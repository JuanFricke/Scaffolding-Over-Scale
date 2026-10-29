"""Layer 1: static metrics of each run's change.

- Larastan (PHPStan level 5): errors in the changed PHP files of the final tree minus errors in the
  same files at the base (`bench/start`); added files count in full. Larastan is installed only in
  a reflink copy of the tree (btrfs copy-on-write), never in work/ or the subject repo.
- Cyclomatic complexity of the functions in the changed PHP files (php/complexity.php).
- Tests written: test files added/changed and new it()/test() cases.
- Distance from the reference solution: Jaccard of the production files touched and ratio of
  added lines (the reference is read from PF_REPO with `git diff`, read-only; judges never see it).
"""
from __future__ import annotations

import asyncio
import functools
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from orchestrator.adapters import ORACLE_EXCLUDE, _run, _yaml_scalar
from orchestrator.matrix import BENCH_DIR

from . import patch as pt

IMAGE = "pf-bench:tcc-baseline-v1"
PHP_DIR = Path(__file__).resolve().parent / "php"
COPIES = BENCH_DIR / ".cache" / "quality-copies"
LEVEL = 5
NEON = f"includes:\n  - vendor/larastan/larastan/extension.neon\nparameters:\n  level: {LEVEL}\n  tmpDir: /tmp/phpstan\n"
TEST_CASE = re.compile(r"^\s*(it|test)\s*\(|^\s*public\s+function\s+test\w*\s*\(")


def python_metrics(files: list[pt.FileDiff], task: str, pf_repo: Path) -> dict:
    files = [f for f in pt.relevant(files) if f.status != "deleted"]
    prod = {f.path for f in files if f.is_production}
    tests = [f for f in files if f.is_test]
    ref = reference(task, str(pf_repo))
    jac = len(prod & ref["files"]) / len(prod | ref["files"]) if prod | ref["files"] else None
    added = sum(len(f.added) for f in files if f.is_production)
    return {
        "prod_files": len(prod),
        "prod_lines_added": added,
        "test_files": len(tests),
        "test_files_added": sum(1 for f in tests if f.status == "added"),
        "test_cases_added": sum(1 for f in tests for l in f.added if TEST_CASE.search(l)),
        "ref_prod_files": len(ref["files"]),
        "ref_files_jaccard": round(jac, 3) if jac is not None else None,
        "ref_lines_ratio": round(added / ref["lines"], 2) if ref["lines"] else None,
    }


@functools.lru_cache(maxsize=None)
def reference(task: str, pf_repo: str) -> dict:
    base, sol = _yaml_scalar(task, "base_commit"), _yaml_scalar(task, "solution_commit")
    excludes = [f":(exclude){p}" for p in ORACLE_EXCLUDE]
    out = subprocess.run(["git", "-C", pf_repo, "diff", base, sol, "--", ".", *excludes],
                         capture_output=True, text=True, check=True).stdout
    files = [f for f in pt.relevant(pt.parse(out)) if f.status != "deleted" and f.is_production]
    return {"files": {f.path for f in files}, "lines": sum(len(f.added) for f in files)}


def _docker(copy: Path, cache: Path, script: str) -> list[str]:
    return ["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "--memory", "6g",
            "--label", "bench.role=quality", "-e", "HOME=/tmp", "-e", "COMPOSER_HOME=/tmp/composer",
            "-e", "COMPOSER_CACHE_DIR=/cache/composer", "-v", f"{copy}:/var/www/html",
            "-v", f"{cache}:/cache", "-v", f"{PHP_DIR}:/q:ro", "-w", "/var/www/html", IMAGE, "sh", "-c", script]


def _phpstan_counts(raw: str) -> dict[str, int] | None:
    """Errors per file, or None when PHPStan did not run (e.g. the app does not boot)."""
    try:
        data = json.loads(raw[raw.index("{"):])
    except ValueError:
        return None
    if "totals" not in data:
        return None
    return {re.sub(r"^/var/www/html/", "", f): v["errors"] for f, v in (data.get("files") or {}).items()}


async def container_metrics(run, files: list[pt.FileDiff], slot: int) -> dict:
    php = [f for f in pt.relevant(files) if f.is_php and f.status != "deleted" and f.path.startswith(("app/", "routes/", "database/", "config/"))]
    if not php:
        return {"php_files": 0}
    paths = " ".join(f.path for f in php)
    modified = [f.path for f in php if f.status != "added"]
    copy = COPIES / run.run_id
    cache = BENCH_DIR / ".cache" / f"slot-q{slot}"
    cache.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(copy, ignore_errors=True)
    COPIES.mkdir(parents=True, exist_ok=True)
    try:
        cp = await _run(["cp", "-a", "--reflink=always", str(run.tree), str(copy)])
        if cp.returncode != 0:
            return {"error": f"copy failed: {cp.stderr[-300:]}"}
        (copy / "phpstan.bench.neon").write_text(NEON)
        analyse = f"vendor/bin/phpstan analyse -c phpstan.bench.neon --error-format=json --no-progress --memory-limit=2G"
        final = await _run(_docker(copy, cache, f"""
            composer require --dev larastan/larastan --no-interaction --no-progress --no-scripts -W >/tmp/req.log 2>&1 \
              || {{ echo REQUIRE_FAILED; tail -5 /tmp/req.log; exit 3; }}
            echo '@@PHPSTAN'; {analyse} {paths} 2>/dev/null
            echo '@@CC'; php /q/complexity.php {paths}"""))
        text = final.stdout_bytes.decode(errors="replace")
        if "REQUIRE_FAILED" in text or "@@PHPSTAN" not in text:
            return {"error": f"larastan setup failed: {text[-400:]} {final.stderr[-300:]}"}
        stan_raw = text.split("@@PHPSTAN", 1)[1].split("@@CC", 1)[0]
        stan_final = _phpstan_counts(stan_raw)
        cc = json.loads(text.split("@@CC", 1)[1].strip() or "{}")
        ccs = [v for per_file in cc.values() if isinstance(per_file, dict) for v in per_file.values()]  # PHP: {} -> []
        common = {
            "php_files": len(php),
            "functions": len(ccs),
            "cc_mean": round(sum(ccs) / len(ccs), 2) if ccs else None,
            "cc_max": max(ccs) if ccs else None,
            "cc_over_10": sum(1 for v in ccs if v > 10),
        }
        if stan_final is None:
            # broken code (syntax error, bad route...): Larastan cannot boot the app; not "0 errors"
            first = next((l.strip() for l in stan_raw.splitlines() if l.strip()), "PHPStan could not bootstrap the application")
            return {**common, "larastan_level": LEVEL, "app_boots": False, "larastan_new_errors": None,
                    "larastan_errors_final": None, "larastan_error": first[:200]}
        stan_base: dict[str, int] = {}
        if modified:
            co = await _run(["git", "-C", str(copy), "checkout", "bench/start", "--", *modified])
            if co.returncode == 0:
                base = await _run(_docker(copy, cache, f"{analyse} {' '.join(modified)} 2>/dev/null"))
                stan_base = _phpstan_counts(base.stdout_bytes.decode(errors="replace")) or {}
        new_errors = {p: max(0, stan_final.get(p, 0) - stan_base.get(p, 0)) for p in (f.path for f in php)}
        return {
            **common,
            "larastan_level": LEVEL,
            "app_boots": True,
            "larastan_new_errors": sum(new_errors.values()),
            "larastan_new_errors_by_file": {k: v for k, v in new_errors.items() if v},
            "larastan_errors_final": sum(stan_final.values()),
        }
    finally:
        shutil.rmtree(copy, ignore_errors=True)


async def analyse(run, pf_repo: Path, slot: int = 0) -> dict:
    files = pt.parse(run.patch.read_text(errors="replace"))
    out = {"run_id": run.run_id, **python_metrics(files, run.task, pf_repo),
           **await container_metrics(run, files, slot)}
    run.out_dir.mkdir(exist_ok=True)
    (run.out_dir / "static.json").write_text(json.dumps(out, indent=1))
    return out


async def analyse_all(runs, pf_repo: Path, concurrency: int = 3, force: bool = False) -> list[dict]:
    slots: asyncio.Queue[int] = asyncio.Queue()
    for i in range(concurrency):
        slots.put_nowait(i)

    async def one(run):
        done = run.out_dir / "static.json"
        if done.exists() and not force and "error" not in json.loads(done.read_text()):
            return json.loads(done.read_text())
        slot = await slots.get()
        try:
            res = await analyse(run, pf_repo, slot)
            print(f"static {run.run_id}: " + (res.get("error") or
                  f"new_errors={res.get('larastan_new_errors')} cc_mean={res.get('cc_mean')}"), flush=True)
            return res
        finally:
            slots.put_nowait(slot)

    return await asyncio.gather(*(one(r) for r in runs))
