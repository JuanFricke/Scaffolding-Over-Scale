"""Layer 3 plumbing that needs no model: pairs, blind workspace, review.json validation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from quality import judge, selection


def fake_run(tmp: Path, model: str, level: str, task: str = "T02-discord-mention-id", patch: str = "") -> selection.Run:
    rid = f"{model.replace('/', '-')}__{task}__{level}__r1__a1"
    tree = tmp / "work" / rid
    tree.mkdir(parents=True, exist_ok=True)
    Path(f"{tree}.prompt.md").write_text("# Task\nDo the thing.\n")
    run = selection.Run(rid, rid.rsplit("__", 1)[0], model, level, task, tree, True, runs_root=tmp / "runs")
    run.run_dir.mkdir(parents=True, exist_ok=True)
    run.patch.write_text(patch)
    return run


class JudgeTests(unittest.TestCase):
    def setUp(self):
        # everything (trees, run dirs, workspaces) lives under this temporary directory
        self.tmp = Path(tempfile.mkdtemp(prefix="quality-test-"))

    def run_(self, *a, **k):
        return fake_run(self.tmp, *a, **k)

    def test_pairs_never_self_or_family(self):
        runs = [self.run_(m, lv, task=t) for m in selection.ROUND_MODELS for lv in ("none", "full")
                for t in ("T02-discord-mention-id", "T09-queue-management-ui")]
        a = judge.assign(runs)
        for r in runs:
            js = a[r.run_id]
            self.assertEqual(len(set(js)), 2, r.run_id)
            self.assertFalse(any(judge.JUDGE_FAMILY[j] == judge.family(r.model) for j in js), r.run_id)
        self.assertEqual(a[next(r.run_id for r in runs if r.model == "claude-sonnet-5-5")], ["muse", "deepseek"])
        self.assertEqual(judge.assign(runs), a)            # deterministic

    def test_workspace_is_blind_and_drops_harness(self):
        patch = ("diff --git a/AGENTS.md b/AGENTS.md\n--- a/AGENTS.md\n+++ b/AGENTS.md\n@@ -1 +1 @@\n+x\n"
                 "diff --git a/app/A.php b/app/A.php\n--- a/app/A.php\n+++ b/app/A.php\n@@ -1 +1 @@\n"
                 "+// as AGENTS.md says\n")
        r = self.run_("claude-sonnet-5-5", "full", patch=patch)
        ws, meta = judge.build_workspace(r, "muse", self.tmp / "ws")
        diff = (ws / "change.diff").read_text()
        self.assertNotIn("a/AGENTS.md", diff)
        self.assertNotIn("AGENTS.md", diff)
        self.assertEqual(meta["redactions"], 1)
        self.assertEqual(judge.leaks(ws, r), [])
        self.assertTrue((ws / ".claude/skills/code-review-judge/SKILL.md").exists())
        self.assertTrue((ws / ".opencode/skills/code-review-judge/SKILL.md").exists())
        self.assertNotIn("AGENTS.md", (ws / "conventions.md").read_text())

    def test_validate_review(self):
        dims = ["requirements", "conventions", "security", "tests", "simplicity", "readability", "scope"]
        good = {"scores": {d: {"score": 4, "evidence": "app/A.php:3"} for d in dims}, "overall": 4,
                "confidence": "high", "summary": "ok",
                "issues": [{"severity": "minor", "dimension": "tests", "location": "x", "explanation": "y"}]}
        self.assertEqual(judge.validate(good, judge.SCHEMA), [])
        bad = json.loads(json.dumps(good))
        bad["scores"]["tests"]["score"] = 7
        bad["overall"] = "4"
        bad["extra"] = 1
        del bad["scores"]["scope"]
        errs = judge.validate(bad, judge.SCHEMA)
        self.assertTrue(any("out of range" in e for e in errs))
        self.assertTrue(any("overall: expected integer" in e for e in errs))
        self.assertTrue(any("unexpected extra" in e for e in errs))
        self.assertTrue(any("missing scope" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
