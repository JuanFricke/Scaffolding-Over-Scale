"""Tables for the reduced run 1 report (runs/reduced-1-report.md).

Run from benchmark/:  python runs/reduced-1-analysis.py > runs/_logs/reduced-1-tables.md
Reads the same join as `python -m orchestrator report` (manifest + results.jsonl); standard
library only. Main analysis = rep 1, current prompt version, the 6 models of the round.
"""
from __future__ import annotations

import collections
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orchestrator import adapters, matrix, report  # noqa: E402
from orchestrator.scheduler import load_preamble  # noqa: E402

MODELS = ["claude-sonnet-5-5", "claude-haiku-5-5", "opencode-go/muse-spark-1.3-contributor",
          "opencode-go/deepseek-v4.1-flash", "opencode-go/beam-free", "llama/gpt-oss-20b"]
SHORT = {"claude-sonnet-5-5": "Sonnet 5.5", "claude-haiku-5-5": "Haiku 5.5",
         "opencode-go/muse-spark-1.3-contributor": "Muse Spark 1.3", "opencode-go/deepseek-v4.1-flash":
         "DeepSeek v4.1 flash", "opencode-go/beam-free": "Beam (free)", "llama/gpt-oss-20b": "gpt-oss-20b"}
LEVELS = matrix.LEVELS
# incomplete in this round (provider outage): shown, but left out of the pooled comparison
PARTIAL = {"opencode-go/beam-free"}


def null_baseline() -> dict[str, int]:
    """Failures outside the hidden tests in an untouched tree, per task: the null agent's
    validation runs (tag eqv-c1). Mostly PfControllerTest (.github is export-ignored; NOTES.md)."""
    out = {}
    for d in (matrix.BENCH_DIR / "runs").glob("null__*__none__r1__a1__eqv-c1"):
        import json
        r = json.loads((d / "result.json").read_text())
        out[r["task"]] = r["regressions"]
    return out


BASELINE = null_baseline()


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value on the discordant pairs (b, c)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def frac(r: dict) -> float | None:
    p, f = r["hidden_passed"], r["hidden_failed"]
    if p is None and f is None:
        return 0.0              # suite did not run (broken app): nothing passed
    p, f = p or 0, f or 0
    return p / (p + f) if p + f else None


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def fmt(x, nd=0):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:,.{nd}f}".replace(",", " ")


def main() -> None:
    _, current = load_preamble(matrix.load().run)
    rows = [r for r in report.rows() if r["model"] in MODELS and r["rep"] == 1
            and r["prompt_version"] == current]
    clean = [r for r in rows if not r["contamination_suspected"]]
    by = {(r["model"], r["level"], r["task"]): r for r in clean}
    tasks = sorted({r["task"] for r in clean})
    out = print

    out(f"Runs graded (rep 1, prompt {current}): {len(rows)}; contamination suspects excluded: "
        f"{len(rows) - len(clean)}; tasks: {len(tasks)}\n")

    out("## pass@1 (hidden tests) por modelo × nível, IC 95% de Wilson\n")
    out("| modelo | " + " | ".join(LEVELS) + " | total |")
    out("|---|" + "---|" * (len(LEVELS) + 1))
    for m in MODELS:
        cells, K, N = [], 0, 0
        for lv in LEVELS:
            sel = [by[(m, lv, t)] for t in tasks if (m, lv, t) in by]
            k = sum(1 for r in sel if r["hidden_ok"]); n = len(sel); K += k; N += n
            lo, hi = wilson(k, n)
            cells.append(f"{k}/{n} = {k/n:.2f} [{lo:.2f}, {hi:.2f}]" if n else "–")
        out(f"| {SHORT[m]} | " + " | ".join(cells) + f" | {K}/{N} = {K/N:.2f} |" if N else "")
    out("")

    out("## Fração média de testes ocultos aprovados (métrica contínua, sensível abaixo do teto)\n")
    out("| modelo | " + " | ".join(LEVELS) + " |")
    out("|---|" + "---|" * len(LEVELS))
    for m in MODELS:
        cells = []
        for lv in LEVELS:
            fs = [frac(by[(m, lv, t)]) for t in tasks if (m, lv, t) in by]
            fs = [f for f in fs if f is not None]
            cells.append(f"{statistics.mean(fs):.3f} (n={len(fs)})" if fs else "–")
        out(f"| {SHORT[m]} | " + " | ".join(cells) + " |")
    out("")

    out("## Efeito de cada nível vs `none`, pareado por tarefa (McNemar exato)\n")
    out("`+` = só o nível passou; `−` = só o `none` passou. Δ em pontos percentuais sobre os pares completos.\n")
    out("| modelo | nível | pares | ambos ✓ | + | − | ambos ✗ | Δ pass@1 | p |")
    out("|---|---|---|---|---|---|---|---|---|")
    pooled = {lv: [0, 0, 0, 0] for lv in LEVELS[1:]}
    for m in MODELS:
        for lv in LEVELS[1:]:
            a = b = c = d = 0
            for t in tasks:
                x, y = by.get((m, "none", t)), by.get((m, lv, t))
                if not x or not y:
                    continue
                X, Y = bool(x["hidden_ok"]), bool(y["hidden_ok"])
                a += X and Y; b += Y and not X; c += X and not Y; d += not X and not Y
            n = a + b + c + d
            for i, v in enumerate((a, b, c, d)):
                pooled[lv][i] += 0 if m in PARTIAL else v
            out(f"| {SHORT[m]} | {lv} | {n} | {a} | {b} | {c} | {d} | "
                f"{(b - c) / n * 100:+.1f} | {mcnemar_exact(b, c):.3f} |" if n else f"| {SHORT[m]} | {lv} | 0 | | | | | | |")
    out("")
    out("Agregado (pares modelo × tarefa; sem os modelos incompletos: " + ", ".join(SHORT[m] for m in PARTIAL) + "):\n")
    out("| nível | pares | ambos ✓ | + | − | ambos ✗ | Δ pass@1 | p |")
    out("|---|---|---|---|---|---|---|---|")
    for lv, (a, b, c, d) in pooled.items():
        n = a + b + c + d
        out(f"| {lv} | {n} | {a} | {b} | {c} | {d} | {(b - c) / n * 100:+.1f} | {mcnemar_exact(b, c):.3f} |")
    out("")

    out("## Custo por modelo × nível (medianas por run)\n")
    out("Tokens de entrada incluem leituras de cache (o Claude Code lê quase tudo do cache).\n")
    out("| modelo | nível | n | turnos | tokens de saída | tokens de entrada | tempo do agente (min) | timeouts |")
    out("|---|---|---|---|---|---|---|---|")
    for m in MODELS:
        for lv in LEVELS:
            sel = [by[(m, lv, t)] for t in tasks if (m, lv, t) in by]
            if not sel:
                continue
            to = sum(1 for r in sel if r["agent_outcome"] == "timeout")
            out(f"| {SHORT[m]} | {lv} | {len(sel)} | {fmt(med([r['turns'] for r in sel]))} | "
                f"{fmt(med([r['tokens_out'] for r in sel]))} | {fmt(med([(r['tokens_in'] or 0) + (r['tokens_cache_read'] or 0) for r in sel]))} | "
                f"{fmt(med([(r['agent_s'] or 0) / 60 for r in sel]), 1)} | {to} |")
    out("")

    out("## Qualidade além do pass@1 (todos os níveis)\n")
    out("Regressões = testes que falham fora dos ocultos, além dos que já falham na árvore intocada "
        f"(agente nulo, por tarefa: {sorted(set(BASELINE.values()))} falhas; quase todas do PfControllerTest). "
        "Suíte que não rodou conta como regressão.\n")
    out("| modelo | runs com regressão | regressões além da base (média) | pint ok | tocou em testes | tocou no harness | saída sem escape | arquivos alterados (mediana) | linhas + (mediana) |")
    out("|---|---|---|---|---|---|---|---|---|")
    for m in MODELS:
        sel = [r for r in clean if r["model"] == m]
        if not sel:
            continue
        n = len(sel)
        ex = [None if r["regressions"] is None else max(0, r["regressions"] - BASELINE.get(r["task"], 2)) for r in sel]
        bad = sum(1 for e in ex if e is None or e > 0)
        out(f"| {SHORT[m]} | {bad}/{n} | {statistics.mean([e for e in ex if e is not None] or [0]):.2f} | "
            f"{sum(1 for r in sel if r['pint_ok'])}/{n} | {sum(1 for r in sel if r['tests_touched'])}/{n} | "
            f"{sum(1 for r in sel if r['harness_touched'])}/{n} | {sum(1 for r in sel if r['unescaped_output_added'])}/{n} | "
            f"{fmt(med([r['diff_files'] for r in sel]))} | {fmt(med([r['diff_insertions'] for r in sel]))} |")
    out("")

    out("## pass@1 por tarefa (✓/✗ por nível: none · agents · skills · full)\n")
    out("| tarefa | " + " | ".join(SHORT[m] for m in MODELS) + " |")
    out("|---|" + "---|" * len(MODELS))
    for t in tasks:
        cells = []
        for m in MODELS:
            cells.append(" ".join(("✓" if by[(m, lv, t)]["hidden_ok"] else "✗") if (m, lv, t) in by else "·"
                                  for lv in LEVELS))
        out(f"| {t} | " + " | ".join(cells) + " |")
    out("")

    att = collections.Counter()
    for r in rows:
        n = adapters.fetch_attempts(r["run_id"])
        if n:
            att[(r["model"], r["level"], r["task"])] += n
    out("## Tentativas de acessar o repositório real pela rede (`fetch_attempts`)\n")
    if att:
        for (m, lv, t), n in sorted(att.items()):
            r = by.get((m, lv, t))
            out(f"- {SHORT[m]}, {t}, {lv}: {n} tentativa(s); hidden_ok={r['hidden_ok'] if r else '–'}")
    else:
        out("- nenhuma")
    out("")


if __name__ == "__main__":
    main()
