#!/usr/bin/env python3
"""Recalcula as tabelas da camada 3 (juízes) do artigo com a média de TODOS os juízes.

O relatório runs/quality/report-full.md usa, por execução, a média dos dois juízes de famílias
distintas da do autor e mantém o juiz da mesma família (runs/quality/self-family/) fora das
médias. O artigo, por decisão do autor, usa a média de todas as revisões disponíveis de cada
execução: as duas de fora da família mais a do juiz da família, quando ela existe (Sonnet e
Haiku: Opus; Muse: Muse; DeepSeek: DeepSeek; gpt-oss e Beam não têm juiz da família).

Uso, a partir de tcc-artigo-template-latex/figuras/:
    python3 calcular-tabelas.py

Imprime, em Markdown, as tabelas usadas no texto: revisões por execução, médias por modelo e
nível, efeito de cada nível contra `none` (Wilcoxon exato, 70 pares), concordância entre juízes
(κ ponderado quadrático, Spearman), viés de cada juiz, validade (Spearman com medidas de outras
camadas) e a diferença entre a média de todos os juízes e a média dos dois de fora.
As estatísticas são as funções do pacote benchmark/quality (analysis.py), sem reimplementação.
"""
from __future__ import annotations

import collections
import itertools
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent / "benchmark"
sys.path.insert(0, str(BENCH))

from quality import analysis, judge, selection  # noqa: E402
from juizes import DIMS, LEVELS, PT, FULL, load_all_judges, judge_mean, efeitos as calc_efeitos  # noqa: E402

MODELS = ["claude-sonnet-5-5", "claude-haiku-5-5", "opencode-go/muse-spark-1.3-contributor",
          "opencode-go/deepseek-v4.1-flash", "opencode-go/beam-free", "llama/gpt-oss-20b"]
SHORT = analysis.SHORT


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def main():
    runs = selection.runs()
    data = load_all_judges(runs)
    by = collections.defaultdict(dict)
    for d in data.values():
        by[(d["run"].model, d["run"].level)][d["run"].task] = d

    print("# Camada 3 com a média de todos os juízes\n")
    n_rev = sum(len(d["reviews"]) for d in data.values())
    n_self = sum(1 for d in data.values() if d["self_judge"] and d["self_judge"] in d["reviews"])
    cnt = collections.Counter(len(d["reviews"]) for d in data.values())
    print(f"{len(data)} execuções; {n_rev} revisões ({n_rev - n_self} dos pares de fora da família, "
          f"{n_self} do juiz da família); execuções com 3/2/1 revisões: "
          f"{cnt.get(3, 0)}/{cnt.get(2, 0)}/{cnt.get(1, 0)}")
    missing = [(d["run"].run_id, d["self_judge"]) for d in data.values()
               if d["self_judge"] and d["self_judge"] not in d["reviews"]]
    print(f"sem revisão do juiz da família (judge_error): {len(missing)} -> {[m[0] for m in missing]}\n")

    print("## Médias por modelo × nível (média de todos os juízes)\n")
    for dim in ["overall", "tests", "conventions"]:
        print(f"### {PT[dim]}\n")
        print("| modelo | " + " | ".join(LEVELS) + " |")
        print("|---|" + "---|" * 4)
        for m in MODELS:
            cells = []
            for lv in LEVELS:
                vals = [judge_mean(d, dim) for d in by.get((m, lv), {}).values()]
                vals = [v for v in vals if v is not None]
                cells.append(f"{fmt(statistics.mean(vals))} (n={len(vals)})" if vals else "–")
            print(f"| {SHORT[m]} | " + " | ".join(cells) + " |")
        print()

    print("## Diferença: média de todos os juízes − média dos dois de fora (nota geral, por modelo)\n")
    print("| modelo | juiz da família | n | todos | só de fora | diferença |")
    print("|---|---|---|---|---|---|")
    for m in MODELS:
        ds = [d for (mm, _), cell in by.items() if mm == m for d in cell.values()
              if d["self_judge"] and d["self_judge"] in d["reviews"] and len(d["cross"]) >= 2]
        if not ds:
            continue
        a = statistics.mean(judge_mean(d, "overall") for d in ds)
        b = statistics.mean(judge_mean(d, "overall", "cross") for d in ds)
        print(f"| {SHORT[m]} | {ds[0]['self_judge']} | {len(ds)} | {a:.2f} | {b:.2f} | {a - b:+.2f} |")
    print()

    print("## Efeito de cada nível vs `none` (pareado por tarefa; Wilcoxon exato; 5 modelos completos)\n")
    print("| dimensão | nível | pares | Δ médio | p |")
    print("|---|---|---|---|---|")
    efeitos = calc_efeitos(data)
    for dim in ["overall"] + DIMS:
        for lv in LEVELS[1:]:
            delta, p, n = efeitos[(dim, lv)]
            print(f"| {PT[dim]} | {lv} | {n} | {delta:+.2f} | {p:.3f} |")
    print()
    print("EFEITOS (para gerar-figuras.py):")
    for dim in ["overall"] + DIMS:
        row = ", ".join(f'"{lv}": ({efeitos[(dim, lv)][0]:.2f}, {efeitos[(dim, lv)][1]:.3f})' for lv in LEVELS[1:])
        print(f'    "{PT[dim]}": {{{row}}},')
    print()

    print("## Concordância entre juízes (todas as duplas que avaliaram a mesma mudança)\n")
    print("| dupla | n | κ ponderado (geral) | Spearman (geral) | κ médio (7 dimensões) |")
    print("|---|---|---|---|---|")
    for a, b in itertools.combinations(judge.JUDGES, 2):
        both = [d["reviews"] for d in data.values() if a in d["reviews"] and b in d["reviews"]]
        ka = analysis.kappa_quadratic([r[a]["overall"] for r in both], [r[b]["overall"] for r in both])
        sp = analysis.spearman([r[a]["overall"] for r in both], [r[b]["overall"] for r in both])
        kd = analysis.mean([analysis.kappa_quadratic([r[a]["scores"][dim]["score"] for r in both],
                                                     [r[b]["scores"][dim]["score"] for r in both]) for dim in DIMS])
        print(f"| {a} × {b} | {len(both)} | {fmt(ka)} | {fmt(sp)} | {fmt(kd)} |")
    print()

    print("## Viés de cada juiz (nota geral do juiz − média de todos os juízes da mesma execução)\n")
    for j in judge.JUDGES:
        diffs = [d["reviews"][j]["overall"] - judge_mean(d, "overall")
                 for d in data.values() if j in d["reviews"] and len(d["reviews"]) >= 2]
        print(f"- {j}: {statistics.mean(diffs):+.2f} (n={len(diffs)})")
    print()
    print("Nota geral média por juiz e por modelo avaliado (juiz da família marcado com *):\n")
    print("| modelo | " + " | ".join(judge.JUDGES) + " |")
    print("|---|" + "---|" * len(judge.JUDGES))
    for m in MODELS:
        cells = []
        for j in judge.JUDGES:
            vals = [d["reviews"][j]["overall"] for (mm, _), cell in by.items() if mm == m
                    for d in cell.values() if j in d["reviews"]]
            star = "*" if any(d["self_judge"] == j for cell in by.values() for d in cell.values()
                              if d["run"].model == m) else ""
            cells.append(f"{fmt(statistics.mean(vals))}{star} (n={len(vals)})" if vals else "–")
        print(f"| {SHORT[m]} | " + " | ".join(cells) + " |")
    print()

    print("## Validade (Spearman, todas as execuções; notas = média de todos os juízes)\n")
    fns = analysis.metric_fns()
    ok = lambda d: 1.0 if d["run"].hidden_ok else 0.0  # noqa: E731
    pairs = [("Juízes: nota geral", "Testes ocultos aprovados", lambda d: judge_mean(d, "overall"), ok),
             ("Juízes: requisitos", "Testes ocultos aprovados", lambda d: judge_mean(d, "requirements"), ok),
             ("Juízes: convenções", "Escore de convenções (camada 2)", lambda d: judge_mean(d, "conventions"),
              fns["convenções (escore)"]),
             ("Juízes: nota geral", "Larastan: erros novos", lambda d: judge_mean(d, "overall"),
              fns["Larastan: erros novos"]),
             ("Escore de convenções (camada 2)", "Testes ocultos aprovados", fns["convenções (escore)"], ok)]
    print("| A | B | ρ | n |")
    print("|---|---|---|---|")
    for an, bn, fa, fb in pairs:
        xs = [fa(d) for d in data.values()]
        ys = [fb(d) for d in data.values()]
        n = sum(1 for x, y in zip(xs, ys) if x is not None and y is not None)
        print(f"| {an} | {bn} | {fmt(analysis.spearman(xs, ys))} | {n} |")
    print()

    print("## Exemplo T07 Muse (notas de todos os juízes, none e skills)\n")
    for lv in ("none", "skills"):
        d = by[("opencode-go/muse-spark-1.3-contributor", lv)].get("T07-call-next-ticket")
        if d:
            print(lv, {j: (r["scores"]["tests"]["score"], r["overall"]) for j, r in d["reviews"].items()},
                  "média geral", fmt(judge_mean(d, "overall")))


if __name__ == "__main__":
    main()
