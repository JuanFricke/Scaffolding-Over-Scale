"""Join results.jsonl and the manifest into a per-run CSV and a pass@1 table per runner.

Statistics (paired models, intervals) are out of scope: they start from the CSV.
"""
from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

from . import manifest as mf
from .matrix import BENCH_DIR, LEVELS

RESULTS = BENCH_DIR / "runs" / "results.jsonl"
CSV_OUT = BENCH_DIR / "runs" / "report.csv"
MD_OUT = BENCH_DIR / "runs" / "report.md"
VALIDATION_RUNNERS = {"oracle", "null", "flaky"}

COLUMNS = ["runner", "model", "level", "task", "rep", "cell_id", "run_id", "attempt", "agent_outcome",
           "contamination_suspected", "hidden_ok", "hidden_passed", "hidden_failed", "full_passed",
           "full_failed", "regressions", "pint_ok", "diff_files", "diff_insertions", "diff_deletions",
           "tests_touched", "harness_touched", "unescaped_output_added", "composer_mode", "turns",
           "tokens_in", "tokens_out", "tokens_reasoning", "tokens_cache_read", "cost_usd", "agent_s",
           "grade_s", "cli_version", "sandbox"]


def load_results() -> dict[str, dict]:
    """run_id -> last result line (a regrade appends again; the last line is the valid one)."""
    out: dict[str, dict] = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["run_id"]] = r
    return out


def rows(include_validation: bool = False, tag: str | None = None) -> list[dict]:
    results = load_results()
    man = mf.Manifest(mf.path_for(tag))
    merged: dict[str, dict] = {}
    for rec in man.records():
        merged.setdefault(rec["cell_id"], {}).update(rec)
    out = []
    for cid, m in sorted(merged.items()):
        if m.get("state") != mf.DONE or m.get("run_id") not in results:
            continue
        if m.get("runner") in VALIDATION_RUNNERS and not include_validation:
            continue
        r = results[m["run_id"]]
        met = r.get("agent_metrics") or {}
        v = r["violations"]
        out.append({
            "runner": m.get("runner"), "model": r["model"], "level": r["level"], "task": r["task"],
            "rep": m.get("rep"), "cell_id": cid, "run_id": m["run_id"], "attempt": m.get("attempt"),
            "agent_outcome": m.get("agent_outcome"),
            "contamination_suspected": bool(m.get("contamination_suspected")),
            "hidden_ok": r["tests_hidden"]["ok"], "hidden_passed": r["tests_hidden"]["passed"],
            "hidden_failed": r["tests_hidden"]["failed"], "full_passed": r["tests_full"]["passed"],
            "full_failed": r["tests_full"]["failed"], "regressions": r["regressions"],
            "pint_ok": r["pint"]["ok"], "diff_files": r["diff"]["files"],
            "diff_insertions": r["diff"]["insertions"], "diff_deletions": r["diff"]["deletions"],
            "tests_touched": len(v["tests_touched"]), "harness_touched": len(v["harness_touched"]),
            "unescaped_output_added": v["unescaped_output_added"], "composer_mode": r["composer"]["mode"],
            **{k: met.get(k) for k in ("turns", "tokens_in", "tokens_out", "tokens_reasoning",
                                       "tokens_cache_read", "cost_usd", "cli_version", "sandbox")},
            "agent_s": m.get("agent_s"), "grade_s": m.get("grade_s"),
        })
    return out


def build(include_validation: bool = False, tag: str | None = None) -> str:
    data = rows(include_validation, tag)
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(data)
    lines = ["# pass@1 by model x level (hidden tests; contaminated runs excluded)", "",
             "Grouped by runner: compare models only within one runner.", ""]
    by_runner = collections.defaultdict(list)
    for r in data:
        by_runner[r["runner"]].append(r)
    for runner, rs in sorted(by_runner.items()):
        levels = [lv for lv in LEVELS if any(r["level"] == lv for r in rs)]
        lines += [f"## runner `{runner}`", "",
                  "| model | " + " | ".join(levels) + " |", "|---|" + "---|" * len(levels)]
        for model in sorted({r["model"] for r in rs}):
            cells = []
            for lv in levels:
                sel = [r for r in rs if r["model"] == model and r["level"] == lv
                       and not r["contamination_suspected"]]
                ok = sum(1 for r in sel if r["hidden_ok"])
                cells.append(f"{ok / len(sel):.2f} ({ok}/{len(sel)})" if sel else "-")
            lines.append(f"| {model} | " + " | ".join(cells) + " |")
        lines.append("")
    excluded = sum(1 for r in data if r["contamination_suspected"])
    lines.append(f"{len(data)} graded runs; {excluded} excluded as contamination suspects. CSV: {CSV_OUT.name}")
    MD_OUT.write_text("\n".join(lines) + "\n")
    return "\n".join(lines)
