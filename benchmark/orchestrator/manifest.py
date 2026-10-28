"""Append-only manifest (runs/manifest.jsonl): one line per cell state transition.

Only the orchestrator writes it. Resume reads it back; results.jsonl is never used to
infer state (the join between the two is run_id).
"""
from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .matrix import BENCH_DIR

MANIFEST = BENCH_DIR / "runs" / "manifest.jsonl"


def path_for(tag: str | None) -> Path:
    """Main manifest, or runs/_tagged/manifest-<tag>.jsonl for tagged (validation) runs.

    runs/_tagged/ is git-ignored (runs/*/): validation runs never enter the thesis artifacts."""
    return MANIFEST if not tag else MANIFEST.parent / "_tagged" / f"manifest-{tag}.jsonl"

# Lifecycle. Terminal: done, failed_infra. Everything else is resumable.
PREPARED = "prepared"
AGENT_RUNNING = "agent_running"
AGENT_DONE = "agent_done"          # agent finished (ok / fail / timeout): tree is ready to grade
GRADING = "grading"
DONE = "done"
INFRA_ERROR = "infra_error"        # one attempt failed for infrastructure reasons; will retry
GRADE_ERROR = "grade_error"        # evaluate.sh itself failed; regrade without rerunning the agent
FAILED_INFRA = "failed_infra"      # gave up after max_attempts
TERMINAL = {DONE, FAILED_INFRA}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Manifest:
    def __init__(self, path: Path = MANIFEST):
        self.path = path

    def append(self, cell_id: str, state: str, **fields) -> dict:
        rec = {"ts": now_iso(), "cell_id": cell_id, "state": state, **fields}
        line = json.dumps(rec, ensure_ascii=False, sort_keys=False) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, line.encode())
            os.fsync(fd)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        return rec

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open() as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    # a torn last line from a hard kill: ignore it, the transition is redone
                    continue
        return out

    def latest(self) -> dict[str, dict]:
        """cell_id -> merged view of its records (later fields win; state = last state)."""
        view: dict[str, dict] = {}
        for rec in self.records():
            cur = view.setdefault(rec["cell_id"], {})
            cur.update(rec)
        return view
