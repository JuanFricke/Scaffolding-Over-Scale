"""python -m quality <command>   (run from benchmark/)

  select       list the runs a selection covers
  conventions  layer 2 (runs/<run_id>/quality/conventions.json + runs/quality/conventions.jsonl)
  static       layer 1 (runs/<run_id>/quality/static.json + runs/quality/static.jsonl)
  judge        layer 3 (runs/quality/reviews/, runs/quality/judge-manifest.jsonl)
  analyze      tables (runs/quality/report-<name>.md; --all-judges: report-<name>-all-judges.md)
  status       progress per layer
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from . import conventions, selection, static

PF_REPO = Path(os.environ.get("PF_REPO", Path.home() / "Projetos" / "PegaFilaWeb")).resolve()


def _csv(s: str | None) -> list[str] | None:
    return [x.strip() for x in s.split(",") if x.strip()] if s else None


def _runs(args) -> list[selection.Run]:
    return selection.runs(models=_csv(args.models), tasks=_csv(args.tasks), levels=_csv(args.levels),
                          pilot=args.pilot)


def _jsonl(name: str, rows: list[dict]) -> Path:
    """Merge rows into runs/quality/<name>.jsonl (one line per run_id, latest wins)."""
    path = selection.QUALITY_DIR / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                merged[r["run_id"]] = r
    for r in rows:
        merged[r["run_id"]] = r
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for _, r in sorted(merged.items())))
    return path


def cmd_select(args):
    rs = _runs(args)
    for r in rs:
        print(f"{r.run_id}  hidden_ok={r.hidden_ok}")
    print(f"{len(rs)} runs")


def cmd_conventions(args):
    rows = [conventions.analyse(r) for r in _runs(args)]
    print(f"{len(rows)} runs -> {_jsonl('conventions', rows).relative_to(selection.BENCH_DIR)}")


def cmd_static(args):
    rows = asyncio.run(static.analyse_all(_runs(args), PF_REPO, args.concurrency, args.force))
    bad = [r for r in rows if r.get("error")]
    print(f"{len(rows)} runs ({len(bad)} errors) -> {_jsonl('static', rows).relative_to(selection.BENCH_DIR)}")


def cmd_judge(args):
    from . import judge
    judge.main(args, _runs(args))


def cmd_analyze(args):
    from . import analysis
    print(analysis.build(_runs(args), args.name, args.all_judges))


def cmd_status(args):
    rs = _runs(args)
    have = lambda f: sum(1 for r in rs if (r.out_dir / f).exists())  # noqa: E731
    print(f"{len(rs)} runs; conventions {have('conventions.json')}; static {have('static.json')}")
    try:
        from . import judge
        print(judge.status(rs))
        print(judge.status(rs, self_family=True))
    except ImportError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m quality", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("select", "conventions", "static", "judge", "analyze", "status"):
        p = sub.add_parser(name)
        p.add_argument("--pilot", action="store_true", help="pilot tasks only (T02 + T09)")
        p.add_argument("--models"), p.add_argument("--tasks"), p.add_argument("--levels")
        p.set_defaults(fn=globals()[f"cmd_{name}"])
        if name == "static":
            p.add_argument("--concurrency", type=int, default=3)
            p.add_argument("--force", action="store_true")
        if name == "judge":
            p.add_argument("--concurrency", type=int, default=3, help="per judge pool")
            p.add_argument("--judges", help="only these judges (opus,muse,deepseek)")
            p.add_argument("--tag", help="smoke runs: separate manifest, kept out of the data")
            p.add_argument("--max-reviews", type=int)
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--self-family", action="store_true",
                           help="the excluded same-family judge only (separate manifest, self-preference check)")
        if name == "analyze":
            p.add_argument("--name", default="pilot")
            p.add_argument("--all-judges", action="store_true",
                           help="average the same-family judge too (the article's rule)")
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
