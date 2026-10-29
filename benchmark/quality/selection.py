"""Which runs are analysed: graded runs of a round, rep 1, current prompt version."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestrator import manifest as mf, matrix, report
from orchestrator.scheduler import load_preamble

BENCH_DIR = matrix.BENCH_DIR
QUALITY_DIR = BENCH_DIR / "runs" / "quality"

# reduced run 1 (runs/reduced-1.md): the six models of the round
ROUND_MODELS = ["claude-sonnet-5-5", "claude-haiku-5-5", "opencode-go/muse-spark-1.3-contributor",
                "opencode-go/deepseek-v4.1-flash", "opencode-go/beam-free", "llama/gpt-oss-20b"]
PILOT_TASKS = ["T02-discord-mention-id", "T09-queue-management-ui"]   # small + large (Livewire/UI)


@dataclass(frozen=True)
class Run:
    run_id: str
    cell_id: str
    model: str
    level: str
    task: str
    tree: Path
    hidden_ok: bool
    runs_root: Path = BENCH_DIR / "runs"      # tests point this at a temporary directory

    @property
    def run_dir(self) -> Path:
        return self.runs_root / self.run_id

    @property
    def patch(self) -> Path:
        return self.run_dir / "agent.patch"

    @property
    def statement(self) -> Path:
        """The task statement as the agent got it (without the preamble), next to the tree."""
        return Path(f"{self.tree}.prompt.md")

    @property
    def out_dir(self) -> Path:
        return self.run_dir / "quality"


def runs(models: list[str] | None = None, tasks: list[str] | None = None,
         levels: list[str] | None = None, pilot: bool = False) -> list[Run]:
    _, current = load_preamble(matrix.load().run)
    latest = mf.Manifest(mf.path_for(None)).latest()
    models = models or ROUND_MODELS
    tasks = tasks or (PILOT_TASKS if pilot else None)
    out = []
    for r in report.rows():
        if (r["model"] not in models or r["rep"] != 1 or r["prompt_version"] != current
                or (tasks and r["task"] not in tasks) or (levels and r["level"] not in levels)
                or r["contamination_suspected"]):
            continue
        tree = Path(latest[r["cell_id"]]["tree"])
        out.append(Run(r["run_id"], r["cell_id"], r["model"], r["level"], r["task"], tree,
                       bool(r["hidden_ok"])))
    return sorted(out, key=lambda x: (x.model, x.task, matrix.LEVELS.index(x.level)))
