"""Agent adapters: run the agent under test in a prepared tree and report what happened.

Every adapter returns an AgentResult whose `outcome` drives the scheduler:
  ok       agent exited normally (whether it solved the task is decided by grading)
  fail     agent stopped on its own limits (e.g. context overflow): valid data point
  timeout  hit agent_timeout_s: valid data point, the tree is graded as it is
  infra    provider / network / CLI failure: not a data point, retried
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .matrix import BENCH_DIR, Cell

SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"
WORKSPACE = "/workspace"

INFRA_PATTERNS = re.compile(
    r"\b(429|500|502|503|504|529)\b|rate.?limit|too many requests|quota|overloaded|"
    r"insufficient.?(credit|balance)|ECONNRESET|ETIMEDOUT|ENOTFOUND|EAI_AGAIN|socket hang up|"
    r"network error|fetch failed|service unavailable|internal server error|"
    r"unauthorized|authentication|invalid api key|no space left",
    re.I,
)
RATE_LIMIT_PATTERNS = re.compile(r"\b429\b|rate.?limit|too many requests|quota|usage limit", re.I)
AGENT_LIMIT_PATTERNS = re.compile(
    r"context.{0,20}(length|window|limit)|prompt is too long|maximum context|max.?turns", re.I)


@dataclass
class AgentContext:
    cell: Cell
    run_id: str
    tree: Path
    prompt: str
    run_dir: Path           # runs/<run_id>/: agent logs go here, evaluate.sh adds the rest
    timeout_s: int
    sandbox: str            # "docker" | "none"
    sandbox_image: str
    pf_repo: Path


@dataclass
class AgentResult:
    outcome: str
    reason: str = ""
    exit_code: int | None = None
    wall_s: float = 0.0
    metrics: dict = field(default_factory=dict)
    rate_limited: bool = False
    models_seen: list[str] = field(default_factory=list)
    tool_inputs: list[str] = field(default_factory=list)   # for the contamination detector


class Adapter:
    runner = "?"

    def version(self) -> str:
        return ""

    async def run(self, ctx: AgentContext) -> AgentResult:  # pragma: no cover - interface
        raise NotImplementedError


# --- validation agents ---------------------------------------------------------------

# Paths the oracle never applies: tests (hidden at grading time), export-ignored files that are
# absent from the tree, and harness artifacts (so harness_touched stays empty).
ORACLE_EXCLUDE = ["tests", ".github", ".styleci.yml", "benchmark", "AGENTS.md", "CLAUDE.md",
                  "opencode.json", "ai", ".claude", ".cursor"]


def _yaml_scalar(task: str, key: str) -> str:
    for line in (BENCH_DIR / "tasks" / f"{task}.yaml").read_text().splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].split("#")[0].strip()
    return ""


class OracleAdapter(Adapter):
    """Applies the non-test files of the solution commit. Must pass every hidden test."""
    runner = "oracle"

    async def run(self, ctx: AgentContext) -> AgentResult:
        t0 = time.monotonic()
        base = _yaml_scalar(ctx.cell.task, "base_commit")
        sol = _yaml_scalar(ctx.cell.task, "solution_commit")
        excludes = [f":(exclude){p}" for p in ORACLE_EXCLUDE]
        diff = await _run(["git", "-C", str(ctx.pf_repo), "diff", "--binary", base, sol, "--", ".", *excludes])
        if diff.returncode != 0:
            return AgentResult("infra", f"git diff failed: {diff.stderr.strip()}", diff.returncode)
        (ctx.run_dir / "oracle.patch").write_bytes(diff.stdout_bytes)
        apply = await _run(["git", "-C", str(ctx.tree), "apply", "--binary", "--whitespace=nowarn", "-"],
                           input=diff.stdout_bytes)
        if apply.returncode != 0:
            return AgentResult("infra", f"git apply failed: {apply.stderr.strip()}", apply.returncode)
        return AgentResult("ok", exit_code=0, wall_s=time.monotonic() - t0,
                           metrics={"turns": 0, "tokens_in": 0, "tokens_out": 0})


class NullAdapter(Adapter):
    """Does nothing. Every task must fail its hidden tests."""
    runner = "null"

    async def run(self, ctx: AgentContext) -> AgentResult:
        return AgentResult("ok", exit_code=0, metrics={"turns": 0, "tokens_in": 0, "tokens_out": 0})


class FlakyAdapter(Adapter):
    """Test double: answers 429 for the first `fail_times` calls per cell, then behaves like null."""
    runner = "flaky"

    def __init__(self, fail_times: int = 1):
        self.fail_times = fail_times
        self.calls: dict[str, int] = {}

    async def run(self, ctx: AgentContext) -> AgentResult:
        n = self.calls[ctx.cell.cell_id] = self.calls.get(ctx.cell.cell_id, 0) + 1
        if n <= self.fail_times:
            return AgentResult("infra", "simulated HTTP 429 Too Many Requests", 1, rate_limited=True)
        return AgentResult("ok", exit_code=0, metrics={"turns": 0, "tokens_in": 0, "tokens_out": 0})


# --- real runners ------------------------------------------------------------------------

class CLIAdapter(Adapter):
    """Common machinery: per-run HOME, optional Docker sandbox, timeout, log capture."""
    binary = ""

    def host_binary(self) -> Path:
        found = shutil.which(self.binary)
        if not found:
            raise RuntimeError(f"{self.binary} not found on PATH")
        return Path(found).resolve()

    def version(self) -> str:
        try:
            return subprocess.run([str(self.host_binary()), "--version"], capture_output=True,
                                  text=True, timeout=30).stdout.strip()
        except Exception as e:  # noqa: BLE001 - recorded, not fatal
            return f"unknown ({e})"

    # subclasses fill these
    def setup_home(self, home: Path) -> list[str]:
        """Seed credentials into the per-run home; return shell lines to run before the agent."""
        return []

    def agent_argv(self, ctx: AgentContext) -> list[str]:
        raise NotImplementedError

    def extra_mounts(self, home: Path) -> list[str]:
        return []

    def host_prepare(self, home: Path) -> None:
        """Sandbox-less run: last touches to the per-run home."""

    def agent_env(self) -> dict[str, str]:
        return {}

    def parse(self, ctx: AgentContext, res: AgentResult, home: Path, stdout: str, stderr: str) -> None:
        raise NotImplementedError

    async def run(self, ctx: AgentContext) -> AgentResult:
        home = Path(tempfile.mkdtemp(prefix=f"bench-home-{ctx.run_id[:40]}-"))
        try:
            pre = self.setup_home(home)
            argv = self.agent_argv(ctx)
            env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_")}
            env.update(self.agent_env())
            if ctx.sandbox == "docker":
                name = "bench-agent-" + re.sub(r"[^a-zA-Z0-9_.-]", "-", ctx.run_id)[:100]
                cmd = self._docker_argv(ctx, name, home, pre, argv)
                kill = ["docker", "kill", name]
            else:
                env.update({"HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                            "XDG_DATA_HOME": str(home / ".local/share"),
                            "XDG_STATE_HOME": str(home / ".local/state")})
                self.host_prepare(home)
                cmd = ["bash", "-c", "\n".join([*pre, 'exec "$@"']), "agent", *argv]
                kill = None
            out_path, err_path = ctx.run_dir / "agent.stdout.log", ctx.run_dir / "agent.stderr.log"
            (ctx.run_dir / "agent.cmd.json").write_text(json.dumps(
                {"argv": cmd[:-1] + ["<prompt>"] if cmd and cmd[-1] == ctx.prompt else cmd,
                 "sandbox": ctx.sandbox}, indent=2))
            t0 = time.monotonic()
            timed_out = False
            with out_path.open("wb") as out, err_path.open("wb") as err:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, cwd=str(ctx.tree), env=env, stdout=out, stderr=err,
                    stdin=subprocess.DEVNULL, start_new_session=True)
                try:
                    code = await asyncio.wait_for(proc.wait(), ctx.timeout_s)
                except asyncio.TimeoutError:
                    timed_out = True
                    await _terminate(proc, kill)
                    code = proc.returncode
                except asyncio.CancelledError:
                    await _terminate(proc, kill)
                    raise
            wall = time.monotonic() - t0
            stdout, stderr = out_path.read_text(errors="replace"), err_path.read_text(errors="replace")
            res = AgentResult("ok", exit_code=code, wall_s=wall)
            try:
                self.parse(ctx, res, home, stdout, stderr)
            except Exception as e:  # noqa: BLE001 - a parse failure must not lose the run
                res.reason = f"metrics parse error: {e}"
            if timed_out:
                res.outcome, res.reason = "timeout", f"exceeded {ctx.timeout_s}s"
            elif res.outcome == "ok" and code != 0:
                # stderr + error text found by parse(); never the whole stdout, which carries tool
                # output (an auth task prints "authentication" and "500" all the time)
                self._classify_error(res, stderr[-20000:] + "\n" + res.reason)
            res.metrics["wall_s"] = round(wall, 1)
            return res
        finally:
            shutil.rmtree(home, ignore_errors=True)

    @staticmethod
    def _classify_error(res: AgentResult, text: str) -> None:
        res.rate_limited = res.rate_limited or bool(RATE_LIMIT_PATTERNS.search(text))
        if res.rate_limited or INFRA_PATTERNS.search(text):
            res.outcome = "infra"
        elif AGENT_LIMIT_PATTERNS.search(text):
            res.outcome = "fail"
        else:
            # Unknown CLI crash: count as infra (retried, then failed_infra) rather than as a
            # model failure; the log is kept for inspection.
            res.outcome = "infra"
        m = (RATE_LIMIT_PATTERNS.search(text) or INFRA_PATTERNS.search(text)
             or AGENT_LIMIT_PATTERNS.search(text))
        res.reason = (res.reason or f"exit {res.exit_code}") + (f" [{m.group(0)}]" if m else "")

    def _docker_argv(self, ctx: AgentContext, name: str, home: Path, pre: list[str],
                     argv: list[str]) -> list[str]:
        uid, gid = os.getuid(), os.getgid()
        mounts = [
            "-v", f"{ctx.tree}:{WORKSPACE}",
            "-v", f"{home}:/home/agent",
            "-v", f"{self.host_binary()}:/usr/local/bin/{self.binary}:ro",
            *self.extra_mounts(home),
        ]
        envs = []
        for k, v in self.agent_env().items():
            envs += ["-e", f"{k}={v}"]
        script = "\n".join([*pre, 'exec "$@"'])
        return ["docker", "run", "--rm", "--name", name, "--init", "--user", f"{uid}:{gid}",
                "--label", "bench.role=agent", "--label", f"bench.run_id={ctx.run_id}",
                "-e", "HOME=/home/agent", "-e", "CI=1", *envs, *mounts, "-w", WORKSPACE,
                ctx.sandbox_image, "bash", "-c", script, "agent", *argv]


class OpenCodeAdapter(CLIAdapter):
    runner = "opencode"
    binary = "opencode"

    def setup_home(self, home: Path) -> list[str]:
        # Credentials travel as an `auth export` file inside the per-run home (outside the repo,
        # deleted afterwards); the per-run data dir also keeps sessions of parallel runs apart.
        creds = subprocess.run([str(self.host_binary()), "auth", "export"], capture_output=True, timeout=60)
        if creds.returncode != 0:
            raise RuntimeError(f"opencode auth export failed: {creds.stderr.decode()[:300]}")
        f = home / "auth.json"
        f.write_bytes(creds.stdout)
        f.chmod(0o600)
        return ['opencode auth import --standalone "$HOME/auth.json" >/dev/null', 'rm -f "$HOME/auth.json"']

    def agent_argv(self, ctx: AgentContext) -> list[str]:
        return ["opencode", "run", "--standalone", "--auto", "--format", "json",
                "-m", ctx.cell.model.id, "--title", ctx.run_id, ctx.prompt]

    def parse(self, ctx: AgentContext, res: AgentResult, home: Path, stdout: str, stderr: str) -> None:
        session_id = None
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = session_id or ev.get("sessionID")
            part = ev.get("part") or {}
            if ev.get("type") == "tool_use":
                inp = (part.get("state") or {}).get("input")
                if inp:
                    res.tool_inputs.append(json.dumps(inp, ensure_ascii=False))
            if ev.get("type") == "error":
                res.reason = json.dumps(ev.get("error") or ev)[:500]
                self._classify_error(res, json.dumps(ev))
        if not session_id:
            return
        # Totals come from the session export (the event stream can end before the last step_finish).
        env = {**os.environ, "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
               "XDG_DATA_HOME": str(home / ".local/share"), "XDG_STATE_HOME": str(home / ".local/state")}
        exp = subprocess.run([str(self.host_binary()), "session", "export", "--standalone", session_id],
                             capture_output=True, text=True, env=env, timeout=120)
        if exp.returncode != 0:
            res.reason = res.reason or f"session export failed: {exp.stderr[:300]}"
            return
        (ctx.run_dir / "agent.session.json").write_text(exp.stdout)
        data = json.loads(exp.stdout)
        info = data.get("info", {})
        tok = info.get("tokens") or {}
        assistant = [m for m in data.get("messages", []) if m.get("type") == "assistant"]
        models = sorted({f"{m['model'].get('providerID')}/{m['model'].get('id')}"
                         for m in assistant if m.get("model")})
        res.models_seen = models
        res.metrics.update({
            "session_id": session_id,
            "turns": len(assistant),
            "tokens_in": tok.get("input"),
            "tokens_out": tok.get("output"),
            "tokens_reasoning": tok.get("reasoning"),
            "tokens_cache_read": (tok.get("cache") or {}).get("read"),
            "tokens_cache_write": (tok.get("cache") or {}).get("write"),
            "cost_usd": info.get("cost"),
            "outcome": info.get("outcome"),
            "models_seen": models,
        })
        if info.get("outcome") not in (None, "succeeded") and res.outcome == "ok":
            res.reason = res.reason or f"session outcome {info.get('outcome')}"
            self._classify_error(res, stderr[-20000:] + "\n" + res.reason)


class ClaudeCodeAdapter(CLIAdapter):
    runner = "claude-code"
    binary = "claude"

    MARKETPLACE = "claude-plugins-official"
    PLUGINS = ["php-lsp"]   # what harness/v1/.claude/settings.json enables at `full`

    def marketplace_dir(self) -> Path:
        return Path.home() / ".claude" / "plugins" / "marketplaces" / self.MARKETPLACE

    def setup_home(self, home: Path) -> list[str]:
        (home / ".claude" / "plugins").mkdir(parents=True)
        # Prefer a long-lived token (`claude setup-token`) or an API key from the environment;
        # fall back to a copy of the CLI login.
        if not (os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")):
            src = Path.home() / ".claude" / ".credentials.json"
            if not src.exists():
                raise RuntimeError("no Claude credentials: set CLAUDE_CODE_OAUTH_TOKEN or log in with `claude`")
            shutil.copy2(src, home / ".claude" / ".credentials.json")
        if not self.marketplace_dir().is_dir():
            raise RuntimeError(f"marketplace {self.MARKETPLACE} missing on the host; run `claude plugin "
                               f"marketplace add anthropics/{self.MARKETPLACE}` once")
        # The plugins the `full` harness enables are installed at every level, so the environment is
        # identical across levels; they only load where the tree's .claude/settings.json enables them
        # (--setting-sources project ignores the user settings `plugin install` writes, removed anyway).
        self._home = home
        return [f"claude plugin install {p}@{self.MARKETPLACE} >/dev/null 2>&1 || echo 'plugin {p} not installed' >&2"
                for p in self.PLUGINS] + ['rm -f "$HOME/.claude/settings.json"']

    def write_marketplaces(self, home: Path, location: str) -> None:
        (home / ".claude" / "plugins" / "known_marketplaces.json").write_text(json.dumps({
            self.MARKETPLACE: {"source": {"source": "github", "repo": f"anthropics/{self.MARKETPLACE}"},
                               "installLocation": location, "lastUpdated": "2026-10-28T00:00:00.000Z"}}))

    def extra_mounts(self, home: Path) -> list[str]:
        target = f"/home/agent/.claude/plugins/marketplaces/{self.MARKETPLACE}"
        self.write_marketplaces(home, target)
        return ["-v", f"{self.marketplace_dir()}:{target}:ro"]

    def host_prepare(self, home: Path) -> None:
        self.write_marketplaces(home, str(self.marketplace_dir()))

    def agent_env(self) -> dict[str, str]:
        env = {"DISABLE_AUTOUPDATER": "1", "DISABLE_TELEMETRY": "1"}
        for k in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"):
            if os.environ.get(k):
                env[k] = os.environ[k]
        return env

    def agent_argv(self, ctx: AgentContext) -> list[str]:
        # --setting-sources project: only the tree's .claude/settings.json (present at `full`),
        # never the experimenter's user settings; no MCP servers.
        return ["claude", "-p", "--model", ctx.cell.model.id, "--output-format", "stream-json",
                "--verbose", "--setting-sources", "project", "--strict-mcp-config",
                "--no-session-persistence", "--dangerously-skip-permissions", ctx.prompt]

    def parse(self, ctx: AgentContext, res: AgentResult, home: Path, stdout: str, stderr: str) -> None:
        final = None
        models: set[str] = set()
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                # record what the harness actually switched on (plugins / LSP at `full`)
                res.metrics["plugins"] = sorted(p.get("name") for p in ev.get("plugins") or []
                                                if p.get("path") != "builtin")
                res.metrics["lsp_tool"] = "LSP" in (ev.get("tools") or [])
                res.metrics["init_model"] = ev.get("model")
            if ev.get("type") == "assistant":
                msg = ev.get("message") or {}
                if msg.get("model"):
                    models.add(msg["model"])
                for c in msg.get("content") or []:
                    if c.get("type") == "tool_use":
                        res.tool_inputs.append(json.dumps(c.get("input"), ensure_ascii=False))
            elif ev.get("type") == "result":
                final = ev
        if final is None:
            return
        usage = final.get("usage") or {}
        model_usage = final.get("modelUsage") or {}
        res.models_seen = sorted(set(model_usage) | models)
        res.metrics.update({
            "session_id": final.get("session_id"),
            "turns": final.get("num_turns"),
            "tokens_in": usage.get("input_tokens"),
            "tokens_out": usage.get("output_tokens"),
            "tokens_cache_read": usage.get("cache_read_input_tokens"),
            "tokens_cache_write": usage.get("cache_creation_input_tokens"),
            "cost_usd": final.get("total_cost_usd"),
            "duration_api_ms": final.get("duration_api_ms"),
            "outcome": final.get("subtype"),
            "terminal_reason": final.get("terminal_reason"),
            "models_seen": res.models_seen,
        })
        if final.get("is_error") and res.outcome == "ok":
            res.reason = res.reason or str(final.get("result") or final.get("subtype"))[:500]
            self._classify_error(res, stderr[-20000:] + "\n" + res.reason)


ADAPTERS = {"oracle": OracleAdapter, "null": NullAdapter, "flaky": FlakyAdapter,
            "opencode": OpenCodeAdapter, "claude-code": ClaudeCodeAdapter}


def make(runner: str) -> Adapter:
    try:
        return ADAPTERS[runner]()
    except KeyError:
        raise KeyError(f"unknown runner: {runner}") from None


# --- contamination detector --------------------------------------------------------------

# Only where a tool *goes* is checked, never what it writes: file contents legitimately mention the
# project name (README, docs), which would flag every run.
LOCATION_KEYS = {"command", "path", "filePath", "file_path", "notebook_path", "pattern", "url", "cwd",
                 "workdir", "directory", "include", "glob"}


def _locations(tool_input: str) -> list[str]:
    try:
        data = json.loads(tool_input)
    except json.JSONDecodeError:
        return [tool_input]
    if not isinstance(data, dict):
        return [tool_input]
    out = []
    for k, v in data.items():
        if k in LOCATION_KEYS and isinstance(v, str):
            out.append(v.split("<<", 1)[0] if k == "command" else v)   # drop heredoc bodies
    return out


def contamination(tool_inputs: list[str], extra: list[str] | None = None, sandbox: str = "none") -> list[str]:
    """Tool-call inputs that reach outside the tree (subject repo, benchmark files, host home).

    In the Docker sandbox `~` / `$HOME` is the run's own throwaway home, so only host paths count."""
    pats = [r"(^|[/\s\"'])\.\./+PegaFilaWeb|/PegaFilaWeb(\b|/)(?!\.git)", r"Scaffolding-Over-Scale", r"benchmark/(tasks|runs|work)",
            r"\.prompt\.md", r"__(none|agents|skills|full)__", r"\.\./\.\.", r"(^|[\s\"'=])/home/(?!agent)",
            *([] if sandbox == "docker" else [r"(^|[\s\"'=])~/", r"\$HOME(?!/\.)"]), *(extra or [])]
    rx = re.compile("|".join(f"(?:{p})" for p in pats))
    return [t[:300] for t in tool_inputs if any(rx.search(loc) for loc in _locations(t))]


# --- helpers ----------------------------------------------------------------------------

@dataclass
class _Done:
    returncode: int
    stdout_bytes: bytes
    stderr: str


async def _run(argv: list[str], input: bytes | None = None, env: dict | None = None,
               cwd: str | None = None) -> _Done:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=cwd)
    out, err = await proc.communicate(input)
    return _Done(proc.returncode, out, err.decode(errors="replace"))


async def _terminate(proc: asyncio.subprocess.Process, kill_cmd: list[str] | None) -> None:
    if kill_cmd:
        await _run(kill_cmd)
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        await asyncio.wait_for(proc.wait(), 15)
    except asyncio.TimeoutError:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await proc.wait()
