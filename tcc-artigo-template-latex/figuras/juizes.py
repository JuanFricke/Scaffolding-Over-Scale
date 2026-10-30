"""Carga das revisões dos juízes com TODOS os juízes de cada execução (uso do artigo).

O pacote benchmark/quality carrega, por execução, só o par de juízes de famílias distintas da do
autor (analysis.load). O artigo usa também a revisão do juiz da mesma família, feita como
controle de autopreferência (runs/quality/self-family/), e toma a média de todos os juízes.
Este módulo é compartilhado por gerar-figuras.py e calcular-tabelas.py.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent / "benchmark"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from quality import analysis, judge  # noqa: E402

LEVELS = ["none", "agents", "skills", "full"]
DIMS = analysis.DIMS
PT = {"overall": "Nota geral", "requirements": "Requisitos", "conventions": "Convenções",
      "security": "Segurança", "tests": "Testes", "simplicity": "Simplicidade",
      "readability": "Legibilidade", "scope": "Escopo"}
FULL = [m for m in analysis.selection.ROUND_MODELS if m not in analysis.PARTIAL]


def load_all_judges(runs):
    """Dados do pacote (par de juízes atribuído) mais a revisão do juiz da família, se existir.

    d["cross"] guarda só os dois juízes de fora da família; d["reviews"] tem todos.
    """
    data = analysis.load(runs)
    self_dir = judge.paths(None, self_family=True)["reviews"]
    for rid, d in data.items():
        d["cross"] = dict(d["reviews"])
        j = judge.self_judge(d["run"])
        d["self_judge"] = j
        f = self_dir / f"{rid}__{j}.json" if j else None
        if f and f.exists():
            rv = json.loads(f.read_text())
            d["reviews"][rv["judge"]] = rv["review"]
    return data


def score(review, dim):
    return review["overall"] if dim == "overall" else review["scores"][dim]["score"]


def judge_mean(d, dim="overall", which="reviews"):
    """Média dos juízes da execução na dimensão (None com menos de duas revisões)."""
    rv = list(d[which].values())
    if len(rv) < 2:
        return None
    return statistics.mean(score(x, dim) for x in rv)


def by_cell(data):
    out: dict = {}
    for d in data.values():
        out.setdefault((d["run"].model, d["run"].level), {})[d["run"].task] = d
    return out


def efeitos(data):
    """{(dimensão, nível): (Δ médio, p, pares)} contra `none`, pareado por tarefa, 5 modelos completos."""
    by = by_cell(data)
    out = {}
    for dim in ["overall"] + DIMS:
        for lv in LEVELS[1:]:
            diffs = []
            for m in FULL:
                for task, d in by.get((m, "none"), {}).items():
                    e = by.get((m, lv), {}).get(task)
                    if e and judge_mean(d, dim) is not None and judge_mean(e, dim) is not None:
                        diffs.append(judge_mean(e, dim) - judge_mean(d, dim))
            _, p = analysis.wilcoxon_exact(diffs)
            out[(dim, lv)] = (statistics.mean(diffs), p, len(diffs))
    return out
