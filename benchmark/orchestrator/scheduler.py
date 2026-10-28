"""Per-cell pipeline PREPARE -> AGENT -> GRADE with separate concurrency limits.

AGENT is limited per provider pool (max_concurrency, paused as a whole on 429); GRADE by a
global number of Docker slots, each with its own composer/npm cache. All state transitions go
to the manifest, so a killed orchestrator resumes where it stopped.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

from . import adapters, manifest as mf
from .matrix import BENCH_DIR, Cell, Matrix

HARNESS_PATHS = ["AGENTS.md", "CLAUDE.md", "opencode.json", "ai", ".claude", ".cursor"]
LEVEL_FILES = {
    "none": [],
    "agents": ["AGENTS.md", "CLAUDE.md"],
    "skills": ["AGENTS.md", "CLAUDE.md", "ai"],
    "full": ["AGENTS.md", "CLAUDE.md", "ai", "opencode.json", ".claude/settings.json"],
}
POOL_STATE = BENCH_DIR / "runs" / "pools.json"


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


class Pool:
    """Provider pool: a semaphore that can be paused as a whole (e.g. after a 429).

    Usage windows (OpenCode Go: 5 h / week / month) make 429s last for hours, so consecutive
    rate limits double the pause up to `max_pause`, and a successful run resets it. 429s that
    started before the current pause began are the same event and do not escalate it again."""

    def __init__(self, name: str, size: int, base_pause: float = 60, max_pause: float = 1800):
        self.name, self.size = name, size
        self.sem = asyncio.Semaphore(size)
        self.resume_at = 0.0
        self.base_pause, self.max_pause = base_pause, max_pause
        self.strikes = 0
        self.paused_at = 0.0

    async def acquire(self) -> None:
        while True:
            wait = self.resume_at - time.time()
            if wait > 0:
                await asyncio.sleep(wait)
                continue
            await self.sem.acquire()
            if self.resume_at > time.time():   # paused while we were queued
                self.sem.release()
                continue
            return

    def release(self) -> None:
        self.sem.release()

    def pause(self, seconds: float) -> None:
        self.resume_at = max(self.resume_at, time.time() + seconds)
        log(f"pool {self.name}: paused for {seconds:.0f}s")
        _write_pool_state(self)

    def rate_limited(self, run_started_at: float) -> None:
        if run_started_at < self.paused_at:
            return
        self.strikes += 1
        self.paused_at = time.time()
        delay = min(self.base_pause * 2 ** (self.strikes - 1), self.max_pause)
        self.pause(delay + random.uniform(0, delay * 0.2))

    def succeeded(self) -> None:
        self.strikes = 0


def _write_pool_state(pool: Pool) -> None:
    try:
        state = json.loads(POOL_STATE.read_text()) if POOL_STATE.exists() else {}
    except json.JSONDecodeError:
        state = {}
    state[pool.name] = {"resume_at": pool.resume_at}
    POOL_STATE.parent.mkdir(parents=True, exist_ok=True)
    POOL_STATE.write_text(json.dumps(state, indent=2))


@dataclass
class Options:
    concurrency: int | None = None     # overrides every pool and grade_slots (equivalence tests)
    dry_run: bool = False
    max_runs: int | None = None
    pf_repo: Path = Path(os.environ.get("PF_REPO", BENCH_DIR.parent.parent / "PegaFilaWeb")).resolve()
    sandbox: str | None = None
    adapter_override: dict | None = None   # runner -> Adapter instance (tests)
    tag: str | None = None                  # separate manifest + run_id suffix (validation runs)
    cache_tag: str = ""                     # grade cache slots .cache/slot-<cache_tag><n> (a second
                                            # process, e.g. `regrade`, must not share the run's)


class Scheduler:
    def __init__(self, mx: Matrix, opts: Options, man: mf.Manifest | None = None):
        self.mx, self.opts = mx, opts
        self.man = man or mf.Manifest()
        run = mx.run
        self.timeout_s = int(run.get("agent_timeout_s", 1800))
        self.max_attempts = int(run.get("max_attempts", 3))
        self.backoff_base = float(run.get("backoff_base_s", 30))
        self.sandbox = opts.sandbox or run.get("sandbox", "docker")
        self.sandbox_image = run.get("sandbox_image", "pf-bench-agent:tcc-baseline-v1")
        self.work_dir = (BENCH_DIR / run.get("work_dir", "work")).resolve()
        n = opts.concurrency
        self.pools = {name: Pool(name, n or size, float(run.get("rate_limit_base_s", 60)),
                                 float(run.get("rate_limit_max_s", 1800)))
                      for name, size in mx.pools.items()}
        slots = n or int(run.get("grade_slots", 3))
        self.grade_slots: asyncio.Queue[int] = asyncio.Queue()
        for i in range(slots):
            self.grade_slots.put_nowait(i)
        self.adapters: dict[str, adapters.Adapter] = dict(opts.adapter_override or {})
        self.sandbox_image_id = _image_id(self.sandbox_image) if self.sandbox == "docker" else None
        self.preamble, self.prompt_version = load_preamble(run)
        self.versions: dict[str, str] = {}

    def adapter(self, runner: str) -> adapters.Adapter:
        if runner not in self.adapters:
            self.adapters[runner] = adapters.make(runner)
        if runner not in self.versions:
            self.versions[runner] = self.adapters[runner].version()
        return self.adapters[runner]

    # --- selection ---------------------------------------------------------------------

    def pending(self, cells: list[Cell]) -> list[Cell]:
        latest = self.man.latest()
        todo = [c for c in cells if latest.get(c.cell_id, {}).get("state") not in mf.TERMINAL]
        return todo[: self.opts.max_runs] if self.opts.max_runs else todo

    async def run(self, cells: list[Cell]) -> dict:
        todo = self.pending(cells)
        log(f"{len(cells)} cells selected, {len(cells) - len(todo)} already terminal, {len(todo)} to run"
            + (" (dry run)" if self.opts.dry_run else ""))
        if self.opts.dry_run:
            latest = self.man.latest()
            for c in todo:
                st = latest.get(c.cell_id, {}).get("state", "new")
                print(f"  {c.cell_id:80} {st}")
            return {"selected": len(cells), "todo": len(todo)}
        for runner in sorted({c.model.runner for c in todo}):
            self.adapter(runner)
        results = await asyncio.gather(*(self.process(c) for c in todo), return_exceptions=True)
        errors = [(c.cell_id, r) for c, r in zip(todo, results) if isinstance(r, BaseException)]
        for cid, e in errors:
            log(f"{cid}: orchestrator error {e!r}")
            self.man.append(cid, mf.INFRA_ERROR, reason=f"orchestrator: {e!r}")
        return {"selected": len(cells), "ran": len(todo), "errors": len(errors)}

    # --- one cell ------------------------------------------------------------------------

    def _history(self, cell: Cell) -> tuple[dict, int, int]:
        recs = [r for r in self.man.records() if r["cell_id"] == cell.cell_id]
        latest: dict = {}
        for r in recs:
            latest.update(r)
        attempt = max((r.get("attempt", 0) for r in recs), default=0)
        infra = 0
        for r in recs:   # `retry --failed-infra` writes "requeued", which resets the budget
            if r["state"] == "requeued":
                infra = 0
            elif (r["state"] == mf.INFRA_ERROR and r.get("stage") in ("agent", "prepare")
                  and not r.get("rate_limited")):
                infra += 1
        return latest, attempt, infra

    async def process(self, cell: Cell) -> None:
        latest, attempt, infra_fails = self._history(cell)
        state = latest.get("state")
        resumable = state in (mf.AGENT_DONE, mf.GRADING) or (
            state in (mf.GRADE_ERROR, mf.INFRA_ERROR) and latest.get("stage") == "grade")
        if resumable and latest.get("tree") and Path(latest["tree"]).is_dir():
            await self.grade(cell, latest["run_id"], Path(latest["tree"]), latest["attempt"])
            return
        while True:
            attempt += 1
            if infra_fails >= self.max_attempts:
                self.man.append(cell.cell_id, mf.FAILED_INFRA, attempt=attempt - 1,
                                reason=f"{infra_fails} infra failures")
                log(f"{cell.cell_id}: failed_infra")
                return
            run_id = f"{cell.cell_id}__a{attempt}" + (f"__{self.opts.tag}" if self.opts.tag else "")
            tree = self.work_dir / run_id
            ok = await self.prepare(cell, run_id, tree, attempt)
            if not ok:
                infra_fails += 1
                await asyncio.sleep(self._backoff(infra_fails))
                continue
            res = await self.agent(cell, run_id, tree, attempt)
            if res.outcome == "infra":
                if res.rate_limited:
                    # quota, not a fault: the pool is paused (agent()), the cell waits in it and
                    # is retried without spending one of its max_attempts
                    continue
                infra_fails += 1
                await asyncio.sleep(self._backoff(infra_fails))
                continue
            await self.grade(cell, run_id, tree, attempt)
            return

    def _backoff(self, n: int) -> float:
        base = self.backoff_base * 2 ** (n - 1)
        return base + random.uniform(0, base)

    async def prepare(self, cell: Cell, run_id: str, tree: Path, attempt: int) -> bool:
        t0 = time.time()
        env = {**os.environ, "PF_REPO": str(self.opts.pf_repo)}
        self.work_dir.mkdir(parents=True, exist_ok=True)
        r = await adapters._run([str(BENCH_DIR / "bin/prepare-task.sh"), cell.task, cell.level,
                                 "--out", str(tree), "--force"], env=env)
        if r.returncode != 0:
            self.man.append(cell.cell_id, mf.INFRA_ERROR, stage="prepare", run_id=run_id, attempt=attempt,
                            reason=f"prepare-task.sh exit {r.returncode}: {r.stderr.strip()[-500:]}")
            return False
        problems = check_level(tree, cell.level)
        if problems:
            self.man.append(cell.cell_id, mf.INFRA_ERROR, stage="prepare", run_id=run_id, attempt=attempt,
                            reason=f"harness level check failed: {problems}")
            return False
        self.man.append(cell.cell_id, mf.PREPARED, run_id=run_id, tree=str(tree), attempt=attempt,
                        model=cell.model.id, runner=cell.model.runner, task=cell.task, level=cell.level,
                        rep=cell.rep, prepare_s=round(time.time() - t0, 1), reason=None)
        return True

    async def agent(self, cell: Cell, run_id: str, tree: Path, attempt: int) -> adapters.AgentResult:
        pool = self.pools[cell.model.pool]
        adapter = self.adapter(cell.model.runner)
        run_dir = BENCH_DIR / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        # the task statement (tasks/*.yaml, untouched) behind the fixed preamble; what was sent is kept
        prompt = self.preamble + Path(f"{tree}.prompt.md").read_text()
        (run_dir / "prompt.sent.md").write_text(prompt)
        await pool.acquire()
        try:
            self.man.append(cell.cell_id, mf.AGENT_RUNNING, run_id=run_id, attempt=attempt,
                            pool=pool.name, sandbox=self.sandbox, sandbox_image_id=self.sandbox_image_id,
                            prompt_version=self.prompt_version,
                            cli_version=self.versions.get(cell.model.runner))
            log(f"{run_id}: agent start ({cell.model.runner})")
            ctx = adapters.AgentContext(cell=cell, run_id=run_id, tree=tree, prompt=prompt, run_dir=run_dir,
                                        timeout_s=self.timeout_s, sandbox=self.sandbox,
                                        sandbox_image=self.sandbox_image, pf_repo=self.opts.pf_repo)
            started = time.time()
            try:
                res = await adapter.run(ctx)
            except Exception as e:  # noqa: BLE001 - adapter crash = infra
                res = adapters.AgentResult("infra", f"adapter error: {e!r}")
        finally:
            pool.release()
        # validity: the run must have used exactly the model under test
        wrong = [m for m in res.models_seen if not _same_model(m, cell.model.id)]
        if wrong and res.outcome != "infra":
            res.outcome, res.reason = "infra", f"model mismatch: saw {wrong}"
        hits = adapters.contamination(res.tool_inputs, sandbox=self.sandbox)
        if res.rate_limited:
            pool.rate_limited(started)
        elif res.outcome != "infra":
            pool.succeeded()
        if res.outcome == "infra":
            self.man.append(cell.cell_id, mf.INFRA_ERROR, stage="agent", run_id=run_id, attempt=attempt,
                            reason=res.reason, rate_limited=res.rate_limited, agent_s=round(res.wall_s, 1))
            log(f"{run_id}: agent infra error: {res.reason}")
            return res
        self.man.append(cell.cell_id, mf.AGENT_DONE, run_id=run_id, tree=str(tree), attempt=attempt,
                        agent_outcome=res.outcome, agent_reason=res.reason or None, exit_code=res.exit_code,
                        agent_s=round(res.wall_s, 1), metrics=res.metrics, models_seen=res.models_seen,
                        contamination_suspected=bool(hits), contamination_hits=hits[:20],
                        prompt_version=self.prompt_version)
        metrics = {**res.metrics, "cell_id": cell.cell_id, "rep": cell.rep, "attempt": attempt,
                   "runner": cell.model.runner, "cli_version": self.versions.get(cell.model.runner),
                   "effort": cell.model.effort or "cli-default",
                   "prompt_version": self.prompt_version,
                   "sandbox": self.sandbox, "sandbox_image_id": self.sandbox_image_id,
                   "agent_outcome": res.outcome,
                   "contamination_suspected": bool(hits), "matrix_sha256": self.mx.sha256, "seed": self.mx.seed}
        (run_dir / "agent-metrics.input.json").write_text(json.dumps(metrics))
        log(f"{run_id}: agent {res.outcome} in {res.wall_s:.0f}s" + (" CONTAMINATION?" if hits else ""))
        return res

    async def grade(self, cell: Cell, run_id: str, tree: Path, attempt: int) -> None:
        run_dir = BENCH_DIR / "runs" / run_id
        metrics_file = run_dir / "agent-metrics.input.json"
        for n in range(1, self.max_attempts + 1):
            slot = await self.grade_slots.get()
            t0 = time.time()
            try:
                self.man.append(cell.cell_id, mf.GRADING, run_id=run_id, attempt=attempt, grade_try=n, slot=slot)
                env = {**os.environ, "PF_REPO": str(self.opts.pf_repo),
                       "BENCH_CACHE": str(BENCH_DIR / ".cache" / f"slot-{self.opts.cache_tag}{slot}")}
                argv = [str(BENCH_DIR / "bin/evaluate.sh"), str(tree), "--run-id", run_id,
                        "--agent", cell.model.runner, "--model", cell.model.id]
                if metrics_file.exists():
                    argv += ["--agent-metrics", str(metrics_file)]
                r = await adapters._run(argv, env=env)
            finally:
                self.grade_slots.put_nowait(slot)
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / f"evaluate.{n}.log").write_bytes(r.stdout_bytes + r.stderr.encode())
            problem = grade_problem(r.returncode, run_dir)
            if problem is None:
                res = json.loads((run_dir / "result.json").read_text())
                self.man.append(cell.cell_id, mf.DONE, run_id=run_id, attempt=attempt,
                                grade_s=round(time.time() - t0, 1), reason=None,
                                hidden_ok=res["tests_hidden"]["ok"], tests_hidden=res["tests_hidden"],
                                regressions=res["regressions"])
                log(f"{run_id}: done hidden_ok={res['tests_hidden']['ok']}")
                return
            self.man.append(cell.cell_id, mf.GRADE_ERROR, stage="grade", run_id=run_id, attempt=attempt,
                            grade_try=n, reason=problem, grade_s=round(time.time() - t0, 1))
            log(f"{run_id}: grade error ({problem}), try {n}/{self.max_attempts}")
            await asyncio.sleep(self._backoff(n))
        self.man.append(cell.cell_id, mf.FAILED_INFRA, stage="grade", run_id=run_id, attempt=attempt,
                        reason="evaluate.sh kept failing")


PROMPT_V0 = "v0-statement-only"   # runs before the preamble existed (no prompt_version recorded)


def load_preamble(run: dict) -> tuple[str, str]:
    """Fixed text put before every task statement; its hash is the prompt version of each run."""
    name = run.get("prompt_preamble", "prompt-preamble.md")
    if not name:
        return "", PROMPT_V0
    text = (Path(__file__).resolve().parent / name).read_text()
    return text, "pre-" + hashlib.sha256(text.encode()).hexdigest()[:12]


def _image_id(image: str) -> str | None:
    """Pinned at scheduler start: a rebuild mid-matrix shows up as a different id per run."""
    import subprocess
    try:
        r = subprocess.run(["docker", "image", "inspect", "-f", "{{.Id}}", image],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _same_model(seen: str, wanted: str) -> bool:
    # opencode reports provider/model; claude-code may report a dated id (claude-x-1-20260101)
    return seen == wanted or seen.startswith(wanted) or seen.split("/")[-1] == wanted.split("/")[-1]


def check_level(tree: Path, level: str) -> list[str]:
    """The tree carries exactly the harness files of its level (acceptance 4)."""
    want = set(LEVEL_FILES[level])
    problems = [f"missing {p}" for p in want if not (tree / p).exists()]
    for p in HARNESS_PATHS:
        if (tree / p).exists() and not any(w == p or w.startswith(p + "/") for w in want):
            problems.append(f"unexpected {p}")
    return problems


def grade_problem(code: int, run_dir: Path) -> str | None:
    """Failures of the grading itself, as opposed to failures of the agent's code."""
    if code != 0:
        return f"evaluate.sh exit {code}"
    if not (run_dir / "result.json").exists():
        return "result.json missing"
    if (run_dir / "container.exit").exists():
        return f"container exit {(run_dir / 'container.exit').read_text().strip()} (docker/timeout)"
    res = json.loads((run_dir / "result.json").read_text())
    if res["composer"]["exit"] not in (0, None) and not res["composer"]["json_changed"]:
        # the packages installed but the app could not boot for `artisan package:discover`
        # (post-autoload-dump): the agent's code is broken, a valid (failing) result
        log_ = (run_dir / "composer.log").read_text(errors="replace") if (run_dir / "composer.log").exists() else ""
        if not re.search(r"post-autoload-dump|Script @php artisan", log_):
            return "composer install failed with an untouched composer.json (network/cache)"
    if not res["assets"]["skipped"] and res["assets"]["exit"] != 0:
        numstat = (run_dir / "agent.numstat").read_text() if (run_dir / "agent.numstat").exists() else ""
        if not re.search(r"package(-lock)?\.json|vite\.config|resources/(js|css)/", numstat):
            return "asset build failed although the agent did not touch the frontend (network/cache)"
    if res["tests_full"]["exit"] is None:
        return "test suite did not run"
    return None
