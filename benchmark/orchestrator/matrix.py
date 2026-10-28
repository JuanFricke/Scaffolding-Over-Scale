"""Load matrix.toml and expand it into cells (model, task, level, rep)."""
from __future__ import annotations

import hashlib
import random
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
TASKS_DIR = BENCH_DIR / "tasks"
DEFAULT_MATRIX = Path(__file__).resolve().parent / "matrix.toml"
LEVELS = ("none", "agents", "skills", "full")


@dataclass(frozen=True)
class Model:
    id: str
    runner: str
    pool: str
    levels: tuple[str, ...]
    trains_on_data: bool = False
    training_ok: bool = False
    validation: bool = False


@dataclass(frozen=True)
class Cell:
    model: Model
    task: str
    level: str
    rep: int

    @property
    def cell_id(self) -> str:
        return f"{slug(self.model.id)}__{self.task}__{self.level}__r{self.rep}"


@dataclass
class Matrix:
    path: Path
    sha256: str
    run: dict
    models: list[Model]
    pools: dict[str, int]
    tasks: list[str] = field(default_factory=list)

    @property
    def seed(self) -> int:
        return int(self.run.get("seed", 0))

    def model(self, model_id: str) -> Model:
        for m in self.models:
            if m.id == model_id:
                return m
        raise KeyError(model_id)


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", s).strip("-")


def ready_tasks() -> list[str]:
    """Same rule as bin/list-tasks.sh: status missing or 'ready'."""
    ids = []
    for f in sorted(TASKS_DIR.glob("*.yaml")):
        status, tid = "ready", None
        for line in f.read_text().splitlines():
            if line.startswith("status:"):
                status = line.split(":", 1)[1].split("#")[0].strip() or "ready"
            elif line.startswith("id:"):
                tid = line.split(":", 1)[1].split("#")[0].strip()
        if status == "ready" and tid:
            ids.append(tid)
    return ids


def load(path: Path = DEFAULT_MATRIX) -> Matrix:
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode())
    run = data.get("run", {})
    default_levels = tuple(run.get("levels", LEVELS))
    models = []
    for m in data.get("model", []):
        levels = tuple(m.get("levels", default_levels))
        bad = set(levels) - set(LEVELS)
        if bad:
            raise ValueError(f"{m['id']}: unknown levels {sorted(bad)}")
        models.append(Model(
            id=m["id"], runner=m["runner"], pool=m.get("pool", m["runner"]), levels=levels,
            trains_on_data=bool(m.get("trains_on_data", False)),
            training_ok=bool(m.get("training_ok", False)),
            validation=bool(m.get("validation", False)),
        ))
    pools = {name: int(p.get("max_concurrency", 1)) for name, p in data.get("pool", {}).items()}
    for m in models:
        pools.setdefault(m.pool, 1)
    return Matrix(path=path, sha256=hashlib.sha256(raw).hexdigest(), run=run,
                  models=models, pools=pools, tasks=ready_tasks())


def expand(mx: Matrix, *, reps: int | None = None, models: list[str] | None = None,
           levels: list[str] | None = None, tasks: list[str] | None = None) -> list[Cell]:
    """All selected cells, shuffled with the matrix seed (stable for a given selection)."""
    reps = reps if reps is not None else int(mx.run.get("reps", 1))
    if models:
        unknown = set(models) - {m.id for m in mx.models}
        if unknown:
            raise KeyError(f"unknown models: {sorted(unknown)}")
        chosen = [m for m in mx.models if m.id in models]
    else:
        chosen = [m for m in mx.models if not m.validation]
    task_ids = tasks or mx.tasks
    unknown = set(task_ids) - set(mx.tasks) - {p.stem for p in TASKS_DIR.glob("*.yaml")}
    if unknown:
        raise KeyError(f"unknown tasks: {sorted(unknown)}")
    cells = [
        Cell(m, t, lv, r)
        for m in chosen
        for lv in m.levels if not levels or lv in levels
        for t in task_ids
        for r in range(1, reps + 1)
    ]
    # Sort first so the shuffle depends only on the set of cells, not on file order.
    cells.sort(key=lambda c: c.cell_id)
    random.Random(mx.seed).shuffle(cells)
    return cells
