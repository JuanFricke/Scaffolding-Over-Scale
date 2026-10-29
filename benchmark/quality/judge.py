"""Layer 3: blind LLM review of each change, run as the `code-review-judge` skill.

Each change gets exactly two judges out of Opus 5.5, Muse Spark 1.3 and DeepSeek v4.1 flash:
never the model that wrote it and never one of its family (Juan's decision, 2026-10-29). The
judge sees only a workspace with the task statement, the change (harness paths removed), the
project conventions and the skill; nothing names the model, level, run or test result.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import time
from pathlib import Path

from orchestrator import adapters, manifest as mf, matrix
from orchestrator.scheduler import Pool

from . import patch as pt, selection

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "code-review-judge"
HARNESS = matrix.BENCH_DIR / "harness" / "v1"
SEED = 20261028
TIMEOUT_S = 600
MAX_DIFF = 150_000           # bytes of change.diff before large files are summarized
MAX_ATTEMPTS = 3             # infra attempts per review (429/stalls do not count)
PROMPT = ("Use the code-review-judge skill to review the change in this directory and write "
          "review.json. The skill's instructions are in .claude/skills/code-review-judge/SKILL.md "
          "(the same file is under .opencode/skills/); read it first and follow it exactly.")

JUDGES = {
    "opus": matrix.Model(id="claude-opus-5-5", runner="claude-code", pool="anthropic", levels=(), effort="medium"),
    "muse": matrix.Model(id="opencode-go/muse-spark-1.3-contributor", runner="opencode", pool="opencode-go", levels=()),
    "deepseek": matrix.Model(id="opencode-go/deepseek-v4.1-flash", runner="opencode", pool="opencode-go", levels=()),
}
JUDGE_FAMILY = {"opus": "anthropic", "muse": "muse", "deepseek": "deepseek"}


def family(model_id: str) -> str:
    if model_id.startswith("claude-"):
        return "anthropic"
    for key in ("muse", "deepseek", "gpt-oss", "beam", "qwen"):
        if key in model_id:
            return key
    return model_id


def assign(runs: list[selection.Run]) -> dict[str, list[str]]:
    """run_id -> two judges. Excluded: the author's family. When all three judges are eligible
    (gpt-oss, Beam) the three pairs rotate, balanced per model x level over the tasks."""
    pairs = [("opus", "muse"), ("opus", "deepseek"), ("muse", "deepseek")]
    out: dict[str, list[str]] = {}
    counter: dict[tuple[str, str], int] = {}
    for r in sorted(runs, key=lambda x: (x.model, x.level, x.task)):
        ok = [j for j in JUDGES if JUDGE_FAMILY[j] != family(r.model)]
        if len(ok) == 2:
            out[r.run_id] = ok
            continue
        k = (r.model, r.level)
        i = counter.get(k, 0)
        counter[k] = i + 1
        offset = int(hashlib.sha256(f"{SEED}:{r.model}:{r.level}".encode()).hexdigest(), 16) % 3
        out[r.run_id] = list(pairs[(i + offset) % 3])
    return out


# --- blind workspace ---------------------------------------------------------------------------

CONVENTION_SECTIONS = ["Write less, correctly", "Test-driven, always", "Laravel conventions",
                       "Bulma / UI conventions", "Livewire (security-first)", "Keep docs in sync"]
REDACT = re.compile(r"\b(AGENTS\.md|CLAUDE\.md|opencode\.json|ai/skills/[\w./-]*|livewire-policy\.md)")


def conventions_md() -> str:
    """The normative sections of harness/v1/AGENTS.md plus the Livewire policy: the same review
    standard for every level (it never reveals whether the agent had it)."""
    text = (HARNESS / "AGENTS.md").read_text()
    parts = re.split(r"(?m)^## ", text)
    keep = [p for p in parts[1:] if any(p.startswith(s) for s in CONVENTION_SECTIONS)]
    policy = (HARNESS / "ai" / "skills" / "livewire" / "livewire-policy.md").read_text()
    body = "\n".join("## " + p.rstrip() + "\n" for p in keep)
    body = REDACT.sub("the project rules", body)
    return ("# Project conventions (PegaFila)\n\nThe review standard. Commands mentioned here are for "
            "implementers; as a reviewer you only read the change.\n\n" + body
            + "\n" + REDACT.sub("the project rules", policy.replace("# Livewire security policy", "## Livewire security policy")))


def change_diff(run: selection.Run) -> tuple[str, dict]:
    files = pt.relevant(pt.parse(run.patch.read_text(errors="replace")))
    meta = {"files": len(files), "summarized": [], "redactions": 0}
    sections = [f.text for f in files]
    while sum(len(s) for s in sections) > MAX_DIFF:
        i = max(range(len(files)), key=lambda k: len(sections[k]))
        if sections[i].startswith("# summarized"):
            break
        f = files[i]
        sections[i] = (f"# summarized (too large to show): {f.path} ({f.status}, +{len(f.added)} -{len(f.removed)})\n")
        meta["summarized"].append(f.path)
    text = "".join(sections)
    text, meta["redactions"] = REDACT.subn("[project rules]", text)
    return text, meta


def workspace_id(run_id: str, judge: str) -> str:
    return hashlib.sha256(f"{SEED}:{run_id}:{judge}".encode()).hexdigest()[:16]


def build_workspace(run: selection.Run, judge: str, root: Path) -> tuple[Path, dict]:
    ws = root / workspace_id(run.run_id, judge)
    shutil.rmtree(ws, ignore_errors=True)
    ws.mkdir(parents=True)
    diff, meta = change_diff(run)
    (ws / "task.md").write_text(run.statement.read_text())
    (ws / "change.diff").write_text(diff)
    (ws / "conventions.md").write_text(conventions_md())
    for f in ("rubric.md", "review.schema.json"):
        shutil.copy(SKILL_DIR / f, ws / f)
    for d in (".claude/skills", ".opencode/skills"):
        shutil.copytree(SKILL_DIR, ws / d / "code-review-judge")
    return ws, meta


def leaks(ws: Path, run: selection.Run) -> list[str]:
    """Anything in the workspace that could tell the judge whose change this is."""
    needles = {run.run_id, run.cell_id, run.model, run.model.split("/")[-1],
               f"__{run.level}__", "hidden_ok", "bench/start"}
    found = []
    for f in ws.rglob("*"):
        if f.is_file():
            text = f.read_text(errors="replace")
            found += [f"{f.relative_to(ws)}: {n}" for n in needles if n in text]
    return found


# --- review.json validation (the subset of JSON Schema review.schema.json uses) ----------------

def validate(doc, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    root = root or schema
    if "$ref" in schema:
        schema = root["$defs"][schema["$ref"].split("/")[-1]]
    errs = []
    if "enum" in schema and doc not in schema["enum"]:
        return [f"{path}: {doc!r} not in {schema['enum']}"]
    t = schema.get("type")
    if t == "object":
        if not isinstance(doc, dict):
            return [f"{path}: expected object"]
        errs += [f"{path}: missing {k}" for k in schema.get("required", []) if k not in doc]
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errs += [f"{path}: unexpected {k}" for k in doc if k not in props]
        for k, v in doc.items():
            if k in props:
                errs += validate(v, props[k], root, f"{path}.{k}")
    elif t == "array":
        if not isinstance(doc, list):
            return [f"{path}: expected array"]
        for i, v in enumerate(doc):
            errs += validate(v, schema.get("items", {}), root, f"{path}[{i}]")
    elif t == "integer":
        if not isinstance(doc, int) or isinstance(doc, bool):
            return [f"{path}: expected integer"]
        if not schema.get("minimum", doc) <= doc <= schema.get("maximum", doc):
            errs.append(f"{path}: {doc} out of range")
    elif t == "string" and not isinstance(doc, str):
        errs.append(f"{path}: expected string")
    return errs


SCHEMA = json.loads((SKILL_DIR / "review.schema.json").read_text())


def read_review(ws: Path) -> tuple[dict | None, list[str]]:
    f = ws / "review.json"
    if not f.exists():
        return None, ["review.json was not written"]
    raw = f.read_text(errors="replace").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, [f"review.json is not valid JSON: {e}"]
    errs = validate(doc, SCHEMA)
    return (doc if not errs else None), errs


# --- runners ------------------------------------------------------------------------------------

class JudgeClaude(adapters.ClaudeCodeAdapter):
    def setup_home(self, home, ctx):
        super().setup_home(home, ctx)
        return []                       # credentials only: no plugins for a reviewer

    def agent_argv(self, ctx):
        return ["claude", "-p", "--model", ctx.cell.model.id, "--effort", ctx.cell.model.effort or "medium",
                "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
                "--strict-mcp-config", "--no-session-persistence", "--dangerously-skip-permissions",
                # `=` form: the flag is variadic and would swallow the prompt as a tool name
                "--disallowedTools=WebFetch,WebSearch,Task", ctx.prompt]


class JudgeOpenCode(adapters.OpenCodeAdapter):
    def agent_argv(self, ctx):
        return ["opencode", "run", "--standalone", "--auto", "--format", "json",
                "-m", ctx.cell.model.id, "--title", "review", ctx.prompt]


RUNNERS = {"claude-code": JudgeClaude, "opencode": JudgeOpenCode}


def paths(tag: str | None) -> dict[str, Path]:
    base = selection.QUALITY_DIR if not tag else matrix.BENCH_DIR / "runs" / "_tagged" / f"quality-{tag}"
    return {"manifest": base / "judge-manifest.jsonl", "reviews": base / "reviews",
            "workspaces": selection.QUALITY_DIR / "workspaces", "logs": selection.QUALITY_DIR / "workspaces" / "_logs"}


async def review_one(run, judge: str, pools: dict, man: mf.Manifest, p: dict, history: dict) -> None:
    key = f"{run.run_id}__{judge}"
    model = JUDGES[judge]
    adapter = RUNNERS[model.runner]()
    infra = history.get("infra", 0)
    attempt = history.get("attempt", 0)
    feedback = ""
    while True:
        attempt += 1
        ws, meta = build_workspace(run, judge, p["workspaces"])
        leak = leaks(ws, run)
        if leak:
            man.append(key, "judge_error", attempt=attempt, reason=f"workspace leak: {leak[:5]}")
            return
        log_dir = p["logs"] / key
        log_dir.mkdir(parents=True, exist_ok=True)
        cell = matrix.Cell(model, run.task, "review", 0)
        ctx = adapters.AgentContext(cell=cell, run_id=f"review-{workspace_id(run.run_id, judge)}", tree=ws,
                                    prompt=PROMPT + feedback, run_dir=log_dir, timeout_s=TIMEOUT_S,
                                    sandbox="docker", sandbox_image=matrix.load().run["sandbox_image"],
                                    pf_repo=Path("/nonexistent"))
        pool = pools[model.pool]
        await pool.acquire()
        started = time.time()
        try:
            man.append(key, "running", attempt=attempt, run_id=run.run_id, judge=judge, judge_model=model.id,
                       workspace=ws.name, diff_meta=meta)
            try:
                res = await adapter.run(ctx)
            except Exception as e:  # noqa: BLE001
                res = adapters.AgentResult("infra", f"adapter error: {e!r}")
        finally:
            pool.release()
        wrong = [m for m in res.models_seen if m.split("/")[-1] != model.id.split("/")[-1]
                 and not m.startswith(model.id)]
        if res.outcome == "infra" or wrong:
            if res.rate_limited:
                pool.rate_limited(started)
                attempt -= 1
                continue
            infra += 1
            man.append(key, "infra_error", attempt=attempt, reason=(f"model mismatch {wrong}" if wrong else res.reason)[:300])
            if infra >= MAX_ATTEMPTS:
                man.append(key, "judge_error", attempt=attempt, reason="infra attempts exhausted")
                return
            await asyncio.sleep(30 * infra)
            continue
        pool.succeeded()
        doc, errs = read_review(ws)
        if doc is None:
            if not feedback:            # one more try, telling the judge what was wrong
                feedback = ("\n\nYour previous review.json was rejected: " + "; ".join(errs[:10])
                            + ". Write a review.json that matches review.schema.json exactly.")
                man.append(key, "invalid", attempt=attempt, reason="; ".join(errs[:10])[:500])
                continue
            man.append(key, "judge_error", attempt=attempt, reason="; ".join(errs[:10])[:500])
            return
        out = {"run_id": run.run_id, "judge": judge, "judge_model": model.id, "models_seen": res.models_seen,
               "attempt": attempt, "workspace": ws.name, "diff_meta": meta, "outcome": res.outcome,
               "metrics": {k: res.metrics.get(k) for k in ("turns", "tokens_in", "tokens_out",
                                                           "tokens_cache_read", "cost_usd", "wall_s")},
               "review": doc}
        p["reviews"].mkdir(parents=True, exist_ok=True)
        (p["reviews"] / f"{key}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        man.append(key, "done", attempt=attempt, overall=doc["overall"], wall_s=res.metrics.get("wall_s"))
        print(f"judge {key}: overall={doc['overall']} ({res.metrics.get('wall_s')}s)", flush=True)
        shutil.rmtree(ws, ignore_errors=True)
        return


def plan(runs, only: list[str] | None, tag: str | None) -> list[tuple[selection.Run, str]]:
    man = mf.Manifest(paths(tag)["manifest"])
    latest = man.latest()
    todo = []
    for run in runs:
        for judge in assign(runs)[run.run_id]:
            if only and judge not in only:
                continue
            if latest.get(f"{run.run_id}__{judge}", {}).get("state") in ("done", "judge_error"):
                continue
            todo.append((run, judge))
    return todo


async def run_all(todo, concurrency: int, tag: str | None) -> None:
    p = paths(tag)
    man = mf.Manifest(p["manifest"])
    p["manifest"].parent.mkdir(parents=True, exist_ok=True)
    pools = {name: Pool(f"judge-{name}", concurrency) for name in {m.pool for m in JUDGES.values()}}
    await asyncio.gather(*(review_one(run, judge, pools, man, p, {}) for run, judge in todo))


def main(args, runs) -> None:
    only = [j.strip() for j in args.judges.split(",")] if args.judges else None
    todo = plan(runs, only, args.tag)
    if args.max_reviews:
        todo = todo[: args.max_reviews]
    by = {}
    for _, j in todo:
        by[j] = by.get(j, 0) + 1
    print(f"{len(todo)} reviews to run: {by}")
    if args.dry_run:
        for run, j in todo:
            print(f"  {j:9} {run.run_id}")
        return
    asyncio.run(run_all(todo, args.concurrency, args.tag))


def status(runs) -> str:
    latest = mf.Manifest(paths(None)["manifest"]).latest()
    want = [(r.run_id, j) for r in runs for j in assign(runs)[r.run_id]]
    states: dict[str, int] = {}
    for rid, j in want:
        s = latest.get(f"{rid}__{j}", {}).get("state", "pending")
        states[s] = states.get(s, 0) + 1
    return f"judge: {len(want)} reviews " + ", ".join(f"{k}={v}" for k, v in sorted(states.items()))
