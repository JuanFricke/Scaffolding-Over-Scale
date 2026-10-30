"""Linhas inseridas por execução, separadas em produção, testes e outros (uso do artigo).

Lê o `agent.patch` de cada execução com `quality.patch` (a mesma classificação da camada 1:
`is_production` = app/, routes/, resources/, database/, config/ em .php/.js/.css/.scss;
`is_test` = tests/; `relevant` remove arquivos do harness e ruído gerado). "Outros" é o que
sobra: documentação, traduções, CHANGELOG, configuração do projeto. Conta linhas inseridas
(`+` no diff); remoções ficam de fora. A soma de produção bate com `prod_lines_added` do
`runs/quality/static.jsonl`.
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent / "benchmark"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from quality import patch as pt  # noqa: E402

CATS = ["prod", "test", "other"]
PT = {"prod": "Produção", "test": "Testes", "other": "Outros"}


def lines_by_run(runs) -> dict[str, dict]:
    """{run_id: {"prod": n, "test": n, "other": n, "total": n, "test_share": frac|None, "run": run}}"""
    out = {}
    for r in runs:
        files = [f for f in pt.relevant(pt.parse(Path(r.patch).read_text(errors="replace")))
                 if f.status != "deleted"]
        d = {"prod": 0, "test": 0, "other": 0}
        for f in files:
            cat = "test" if f.is_test else "prod" if f.is_production else "other"
            d[cat] += len(f.added)
        d["total"] = sum(d[c] for c in CATS)
        code = d["prod"] + d["test"]
        d["test_share"] = d["test"] / code if code else None
        d["run"] = r
        out[r.run_id] = d
    return out


def cell_means(lines, models, levels):
    """{(model, level): {"prod": média, "test": média, "other": média, "test_share": média, "n": n}}"""
    out = {}
    for m in models:
        for lv in levels:
            cell = [d for d in lines.values() if d["run"].model == m and d["run"].level == lv]
            if not cell:
                continue
            agg = {c: statistics.mean(d[c] for d in cell) for c in CATS + ["total"]}
            shares = [d["test_share"] for d in cell if d["test_share"] is not None]
            agg["test_share"] = statistics.mean(shares) if shares else None
            agg["n"] = len(cell)
            out[(m, lv)] = agg
    return out
