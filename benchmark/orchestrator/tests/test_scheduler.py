"""Scheduler tests that need no Docker and no network (grading is stubbed).

Run from benchmark/:  python -m unittest discover -s orchestrator/tests -t .
PREPARE is real (prepare-task.sh against PF_REPO), so PF_REPO must be available.
"""
from __future__ import annotations

import asyncio
import tempfile
import time
import unittest
from pathlib import Path

from orchestrator import adapters, manifest as mf, matrix
from orchestrator.scheduler import Options, Pool, Scheduler, check_level

TASK = "T07-call-next-ticket"


class StubGrade(Scheduler):
    """Grading replaced by an immediate DONE, so tests exercise only the pipeline logic."""

    async def grade(self, cell, run_id, tree, attempt):
        self.man.append(cell.cell_id, mf.DONE, run_id=run_id, attempt=attempt, hidden_ok=False)


class SlowAgent(adapters.Adapter):
    runner = "null"

    def __init__(self, seconds: float):
        self.seconds = seconds

    async def run(self, ctx):
        await asyncio.sleep(self.seconds)
        return adapters.AgentResult("ok", exit_code=0)


def _mx(tmp: Path) -> matrix.Matrix:
    mx = matrix.load()
    mx.run = {**mx.run, "backoff_base_s": 0.2, "rate_limit_base_s": 0.2, "rate_limit_max_s": 1,
              "work_dir": str(tmp / "work"), "max_attempts": 3}
    return mx


def _cells(mx, levels=("none",)):
    return matrix.expand(mx, reps=1, models=["null"], levels=list(levels), tasks=[TASK])


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="orch-test-"))
        self.man = mf.Manifest(self.tmp / "manifest.jsonl")

    def test_rate_limit_pauses_pool_and_keeps_cell(self):
        mx = _mx(self.tmp)
        cells = _cells(mx, levels=("none", "agents"))
        flaky = adapters.FlakyAdapter(fail_times=1)
        sch = StubGrade(mx, Options(tag="unittest", concurrency=1, adapter_override={"null": flaky}), self.man)
        t0 = time.time()
        asyncio.run(sch.run(cells))
        latest = self.man.latest()
        for c in cells:
            self.assertEqual(latest[c.cell_id]["state"], mf.DONE, c.cell_id)
        recs = self.man.records()
        limited = [r for r in recs if r["state"] == mf.INFRA_ERROR and r.get("rate_limited")]
        self.assertEqual(len(limited), 2)                       # one 429 per cell
        self.assertGreater(sch.pools["local"].resume_at, t0)    # the pool itself was paused
        for c in cells:                                         # retried as a new attempt, not lost
            done = [r for r in recs if r["cell_id"] == c.cell_id and r["state"] == mf.DONE]
            self.assertEqual(len(done), 1)
            self.assertEqual(done[0]["attempt"], 2)

    def test_gives_up_after_max_attempts(self):
        mx = _mx(self.tmp)
        cells = _cells(mx)
        flaky = adapters.FlakyAdapter(99, rate_limited=False)
        sch = StubGrade(mx, Options(tag="unittest", concurrency=1, adapter_override={"null": flaky}), self.man)
        asyncio.run(sch.run(cells))
        self.assertEqual(self.man.latest()[cells[0].cell_id]["state"], mf.FAILED_INFRA)

    def test_rate_limits_do_not_spend_attempts(self):
        mx = _mx(self.tmp)
        cells = _cells(mx)
        flaky = adapters.FlakyAdapter(fail_times=5)        # more 429s than max_attempts
        sch = StubGrade(mx, Options(tag="unittest", concurrency=1, adapter_override={"null": flaky}), self.man)
        asyncio.run(sch.run(cells))
        self.assertEqual(self.man.latest()[cells[0].cell_id]["state"], mf.DONE)
        self.assertEqual(sch.pools["local"].strikes, 0)   # reset by the successful run

    def test_concurrent_429s_escalate_once(self):
        pool = Pool("p", 3, base_pause=10, max_pause=100)
        t0 = time.time()
        pool.rate_limited(t0)
        first = pool.resume_at
        pool.rate_limited(t0)            # same event, seen by another run in flight
        self.assertEqual(pool.strikes, 1)
        self.assertEqual(pool.resume_at, first)
        pool.rate_limited(time.time() + 1)   # a later run hits it again
        self.assertEqual(pool.strikes, 2)
        self.assertGreater(pool.resume_at, first)

    def test_resume_after_kill_does_not_duplicate(self):
        mx = _mx(self.tmp)
        cells = _cells(mx, levels=("none", "agents", "skills", "full"))

        async def killed_midway():
            sch = StubGrade(mx, Options(tag="unittest", concurrency=2, adapter_override={"null": SlowAgent(5)}), self.man)
            task = asyncio.ensure_future(sch.run(cells))
            await asyncio.sleep(2.5)    # some cells prepared / agent running
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(killed_midway())
        self.assertFalse(all(r["state"] == mf.DONE for r in self.man.latest().values()))
        sch = StubGrade(mx, Options(tag="unittest", concurrency=2, adapter_override={"null": SlowAgent(0)}), self.man)
        asyncio.run(sch.run(cells))
        recs = self.man.records()
        for c in cells:
            done = [r for r in recs if r["cell_id"] == c.cell_id and r["state"] == mf.DONE]
            self.assertEqual(len(done), 1, c.cell_id)
        # a third invocation has nothing to do
        sch = StubGrade(mx, Options(tag="unittest", concurrency=2), self.man)
        self.assertEqual(sch.pending(cells), [])

    def test_trees_carry_only_their_level(self):
        mx = _mx(self.tmp)
        cells = _cells(mx, levels=matrix.LEVELS)
        sch = StubGrade(mx, Options(tag="unittest", concurrency=4), self.man)
        asyncio.run(sch.run(cells))
        trees = [Path(r["tree"]) for r in self.man.records() if r["state"] == mf.PREPARED]
        self.assertEqual(len(trees), 4)
        self.assertEqual(len(set(trees)), 4)
        for t in trees:
            level = t.name.split("__")[2]
            self.assertEqual(check_level(t, level), [], t)
        none_tree = next(t for t in trees if "__none__" in t.name)
        for p in ("AGENTS.md", "CLAUDE.md", "opencode.json", "ai", ".claude", ".cursor"):
            self.assertFalse((none_tree / p).exists(), p)


class ContaminationTests(unittest.TestCase):
    def test_flags_paths_outside_tree(self):
        hits = adapters.contamination([
            '{"command": "cat ../../tasks/T07-call-next-ticket.yaml"}',
            '{"command": "ls /home/juan/Projetos/PegaFilaWeb"}',
            '{"filePath": "/workspace/app/Models/Ticket.php"}',
            '{"command": "./bin/pf shell php artisan test"}',
            '{"command": "git remote -v  # github.com/PegaFila/PegaFilaWeb.git"}',
            '{"filePath": "/workspace/docs/x.md", "newString": "Domain document for **PegaFilaWeb**"}',
            '{"command": "cat > docs/a.md <<EOF\\nsee ../../PegaFilaWeb\\nEOF"}',
            '{"command": "grep -r foo ../PegaFilaWeb/app"}',
        ])
        self.assertEqual(len(hits), 3)

    def test_sandbox_home_is_not_contamination(self):
        cmd = ['{"command": "ls ~/.composer; cat $HOME/.cache/x"}']
        self.assertEqual(adapters.contamination(cmd, sandbox="docker"), [])
        self.assertEqual(len(adapters.contamination(cmd, sandbox="none")), 1)


if __name__ == "__main__":
    unittest.main()
