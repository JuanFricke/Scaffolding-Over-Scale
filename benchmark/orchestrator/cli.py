"""python -m orchestrator <command> (run from benchmark/)."""
from __future__ import annotations

import argparse
import asyncio
import collections
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import adapters, manifest as mf, matrix, report
from .scheduler import POOL_STATE, Options, Scheduler

BENCH = matrix.BENCH_DIR


def _csv(s: str | None) -> list[str] | None:
    return [x for x in s.split(",") if x] if s else None


def _selection(args, mx: matrix.Matrix) -> list[matrix.Cell]:
    return matrix.expand(mx, reps=args.reps, models=_csv(args.models), levels=_csv(args.levels),
                         tasks=_csv(args.tasks))


def _guard_training(cells: list[matrix.Cell], allow: bool) -> None:
    blocked = sorted({c.model.id for c in cells if c.model.trains_on_data and not c.model.training_ok})
    if not blocked:
        return
    if not allow:
        sys.exit(f"models that train on submitted data need --allow-training-models: {blocked}")
    answer = input(f"Send the private subject code to {blocked}? Type 'yes' to continue: ")
    if answer.strip() != "yes":
        sys.exit("aborted")


def cmd_plan(args, mx):
    cells = _selection(args, mx)
    latest = mf.Manifest(mf.path_for(args.tag)).latest()
    by = collections.Counter((c.model.id, c.level) for c in cells)
    models = sorted({c.model.id for c in cells})
    levels = [lv for lv in matrix.LEVELS if any(c.level == lv for c in cells)]
    print(f"matrix {mx.path.name} sha256={mx.sha256[:12]} seed={mx.seed} tasks={len(mx.tasks)}")
    print(f"{'model':45} {'runner':12} " + " ".join(f"{lv:>7}" for lv in levels) + "   total")
    for m in models:
        row = [by[(m, lv)] for lv in levels]
        print(f"{m:45} {mx.model(m).runner:12} " + " ".join(f"{n:>7}" for n in row) + f"   {sum(row):>5}")
    done = sum(1 for c in cells if latest.get(c.cell_id, {}).get("state") in mf.TERMINAL)
    print(f"\n{len(cells)} cells, {done} terminal, queue {len(cells) - done}")
    per_pool = collections.Counter(c.model.pool for c in cells)
    for pool, n in sorted(per_pool.items()):
        print(f"  pool {pool:12} {n:5} cells, max_concurrency {mx.pools[pool]}")


def _scheduler(args, mx) -> Scheduler:
    return Scheduler(mx, Options(concurrency=args.concurrency, dry_run=args.dry_run,
                                 max_runs=args.max_runs, sandbox=args.sandbox, tag=args.tag),
                     mf.Manifest(mf.path_for(args.tag)))


def cmd_run(args, mx):
    cells = _selection(args, mx)
    if not args.dry_run:
        _guard_training(cells, args.allow_training_models)
        write_env(mx)
    print(json.dumps(asyncio.run(_scheduler(args, mx).run(cells))))


def cmd_pilot(args, mx):
    model = args.models or next(m.id for m in mx.models if not m.validation)
    tasks = args.tasks or ",".join(mx.tasks[:3])
    args.models, args.tasks, args.reps = model, tasks, 1
    cmd_run(args, mx)
    if args.dry_run:
        return
    cells = _selection(args, mx)
    latest = mf.Manifest(mf.path_for(args.tag)).latest()
    rows = []
    print(f"\n{'run':70} {'turns':>6} {'tok_in':>9} {'tok_out':>8} {'agent_s':>8} {'grade_s':>8}")
    for c in cells:
        r = latest.get(c.cell_id, {})
        m = r.get("metrics") or {}
        rows.append((m.get("turns") or 0, m.get("tokens_in") or 0, m.get("tokens_out") or 0,
                     r.get("agent_s") or 0, r.get("grade_s") or 0))
        print(f"{c.cell_id:70} {rows[-1][0]:>6} {rows[-1][1]:>9} {rows[-1][2]:>8} {rows[-1][3]:>8} {rows[-1][4]:>8}")
    full = matrix.expand(mx)
    if rows:
        avg = [sum(col) / len(rows) for col in zip(*rows)]
        print(f"\nper run (mean): {avg[0]:.0f} requests, {avg[1]:.0f} tokens in, {avg[2]:.0f} out, "
              f"{avg[3]:.0f}s agent, {avg[4]:.0f}s grade")
        print(f"full matrix: {len(full)} runs -> ~{avg[0] * len(full):.0f} requests, "
              f"~{avg[1] * len(full) / 1e6:.1f}M tokens in, ~{avg[2] * len(full) / 1e6:.2f}M out "
              f"(other models will differ; rerun the pilot per model if limits matter)")


def cmd_status(args, mx):
    cells = _selection(args, mx)
    latest = mf.Manifest(mf.path_for(args.tag)).latest()
    states = collections.Counter(latest.get(c.cell_id, {}).get("state", "new") for c in cells)
    print("by state: " + ", ".join(f"{k}={v}" for k, v in sorted(states.items())))
    for key, name in ((lambda c: c.model.id, "model"), (lambda c: c.level, "level")):
        print(f"\nby {name}:")
        groups = collections.defaultdict(list)
        for c in cells:
            groups[key(c)].append(latest.get(c.cell_id, {}))
        for g, recs in sorted(groups.items()):
            done = [r for r in recs if r.get("state") == mf.DONE]
            clean = [r for r in done if not r.get("contamination_suspected")]
            passed = sum(1 for r in clean if r.get("hidden_ok"))
            fi = sum(1 for r in recs if r.get("state") == mf.FAILED_INFRA)
            rate = f"{passed}/{len(clean)} pass" if clean else "-"
            print(f"  {g:45} {len(done):4}/{len(recs):<4} done  {rate:12} failed_infra={fi}"
                  f"  contaminated={len(done) - len(clean)}")
    if POOL_STATE.exists():
        now = time.time()
        for pool, st in json.loads(POOL_STATE.read_text()).items():
            if st.get("resume_at", 0) > now:
                print(f"pool {pool} paused for another {st['resume_at'] - now:.0f}s")


def cmd_retry(args, mx):
    if not args.failed_infra:
        sys.exit("only --failed-infra is supported")
    cells = _selection(args, mx)
    man = mf.Manifest(mf.path_for(args.tag))
    latest = man.latest()
    failed = [c for c in cells if latest.get(c.cell_id, {}).get("state") == mf.FAILED_INFRA]
    for c in failed:
        man.append(c.cell_id, "requeued", reason="retry --failed-infra")
    print(f"requeued {len(failed)} cells")
    if failed and not args.dry_run:
        args.models = ",".join(sorted({c.model.id for c in failed}))
        cmd_run(args, mx)


def cmd_report(args, mx):
    out = report.build(include_validation=args.include_validation, tag=args.tag)
    print(out)


def _cmd(argv: list[str]) -> str:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return f"unavailable ({e})"


def write_env(mx) -> Path:
    pf = Path(os.environ.get("PF_REPO", BENCH.parent.parent / "PegaFilaWeb"))
    sb = mx.run.get("sandbox_image", "")
    env = {
        "created": mf.now_iso(),
        "opencode": _cmd(["opencode", "--version"]),
        "claude": _cmd(["claude", "--version"]),
        "docker": _cmd(["docker", "version", "--format", "{{.Server.Version}}"]),
        "image_pf_bench": _cmd(["docker", "image", "inspect", "-f", "{{.Id}}", "pf-bench:tcc-baseline-v1"]),
        "image_sandbox": _cmd(["docker", "image", "inspect", "-f", "{{.Id}}", sb]) if sb else None,
        "image_node": _cmd(["docker", "image", "inspect", "-f", "{{.Id}}", "node:22-alpine"]),
        "repo_sha": _cmd(["git", "-C", str(BENCH), "rev-parse", "HEAD"]),
        "repo_dirty": bool(_cmd(["git", "-C", str(BENCH), "status", "--porcelain"])),
        "pf_repo_head": _cmd(["git", "-C", str(pf), "rev-parse", "HEAD"]),
        "matrix_sha256": mx.sha256,
        "seed": mx.seed,
        "python": sys.version.split()[0],
    }
    path = BENCH / "runs" / f"env-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}.json"
    path.write_text(json.dumps(env, indent=2) + "\n")
    return path


def cmd_env(args, mx):
    p = write_env(mx)
    print(p.read_text())
    print(f"written {p.relative_to(BENCH)}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m orchestrator", description=__doc__)
    ap.add_argument("--matrix", type=Path, default=matrix.DEFAULT_MATRIX)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def selection(p):
        p.add_argument("--reps", type=int)
        p.add_argument("--models", help="comma-separated model ids (validation runners only when named)")
        p.add_argument("--levels")
        p.add_argument("--tasks")
        p.add_argument("--tag", help="separate manifest runs/manifest-<tag>.jsonl and run_id suffix")

    def execution(p):
        p.add_argument("--max-runs", type=int)
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--concurrency", type=int, help="override every pool and grade_slots")
        p.add_argument("--sandbox", choices=["docker", "none"])
        p.add_argument("--allow-training-models", action="store_true")

    p = sub.add_parser("plan"); selection(p); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("run"); selection(p); execution(p); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("pilot"); selection(p); execution(p); p.set_defaults(fn=cmd_pilot)
    p = sub.add_parser("status"); selection(p); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("retry"); selection(p); execution(p)
    p.add_argument("--failed-infra", action="store_true"); p.set_defaults(fn=cmd_retry)
    p = sub.add_parser("report"); p.add_argument("--include-validation", action="store_true")
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_report)
    p = sub.add_parser("env"); p.set_defaults(fn=cmd_env)

    args = ap.parse_args(argv)
    mx = matrix.load(args.matrix)
    args.fn(args, mx)
