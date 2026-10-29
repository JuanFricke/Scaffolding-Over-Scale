"""Tables of the code-quality analysis -> runs/quality/report-<name>.md (standard library only)."""
from __future__ import annotations

import itertools
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from orchestrator.matrix import LEVELS

from . import conventions as cv, judge, selection

DIMS = ["requirements", "conventions", "security", "tests", "simplicity", "readability", "scope"]
SHORT = {"claude-sonnet-5-5": "Sonnet 5.5", "claude-haiku-5-5": "Haiku 5.5",
         "opencode-go/muse-spark-1.3-contributor": "Muse Spark 1.3", "opencode-go/deepseek-v4.1-flash":
         "DeepSeek v4.1 flash", "opencode-go/beam-free": "Beam (free)", "llama/gpt-oss-20b": "gpt-oss-20b"}
PARTIAL = {"opencode-go/beam-free"}       # incomplete in reduced run 1: out of pooled comparisons


# --- statistics ------------------------------------------------------------------------------

def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def wilcoxon_exact(diffs: list[float]) -> tuple[int, float]:
    """Two-sided exact Wilcoxon signed-rank test (zeros dropped, average ranks for ties)."""
    d = [x for x in diffs if x]
    n = len(d)
    if n == 0:
        return 0, 1.0
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    w_plus = sum(r for r, x in zip(ranks, d) if x > 0)
    total = sum(ranks)
    # enumerate all 2^n sign assignments (n is small here: <= 14 tasks per comparison)
    if n > 20:
        mu, sd = total / 2, math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        z = (abs(w_plus - mu) - 0.5) / sd
        return n, min(1.0, math.erfc(z / math.sqrt(2)))
    dev = abs(w_plus - total / 2)
    hits = sum(1 for signs in itertools.product((0, 1), repeat=n)
               if abs(sum(r for r, s in zip(ranks, signs) if s) - total / 2) >= dev - 1e-9)
    return n, hits / 2 ** n


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None

    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else None


def kappa_quadratic(xs, ys, k: int = 5):
    """Quadratic-weighted Cohen's kappa for two raters on a 1..k scale."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None
    obs = [[0] * k for _ in range(k)]
    for x, y in pairs:
        obs[x - 1][y - 1] += 1
    ra = [sum(row) for row in obs]
    rb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    w = lambda i, j: (i - j) ** 2 / (k - 1) ** 2  # noqa: E731
    o = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k)) / n
    e = sum(w(i, j) * ra[i] * rb[j] for i in range(k) for j in range(k)) / n ** 2
    return 1 - o / e if e else None


# --- data --------------------------------------------------------------------------------------

def load(runs) -> dict[str, dict]:
    out = {}
    reviews_dir = judge.paths(None)["reviews"]
    # only the pair assigned on this run set: the pilot's gpt-oss/Beam rotation differs from the full one
    assigned = judge.assign(runs)
    for r in runs:
        d = {"run": r}
        for layer in ("conventions", "static"):
            f = r.out_dir / f"{layer}.json"
            d[layer] = json.loads(f.read_text()) if f.exists() else None
        d["reviews"] = {}
        for f in reviews_dir.glob(f"{r.run_id}__*.json"):
            rv = json.loads(f.read_text())
            if rv["judge"] in assigned[r.run_id]:
                d["reviews"][rv["judge"]] = rv["review"]
        out[r.run_id] = d
    return out


def metric_fns():
    def judge_mean(dim):
        def f(d):
            rv = list(d["reviews"].values())
            if len(rv) < 2:
                return None
            return mean([x["overall"] if dim == "overall" else x["scores"][dim]["score"] for x in rv])
        return f
    fns = {
        "convenções (escore)": lambda d: (d["conventions"] or {}).get("score"),
        "Larastan: erros novos": lambda d: (d["static"] or {}).get("larastan_new_errors"),
        "complexidade média": lambda d: (d["static"] or {}).get("cc_mean"),
        "casos de teste novos": lambda d: (d["static"] or {}).get("test_cases_added"),
        "Jaccard vs referência": lambda d: (d["static"] or {}).get("ref_files_jaccard"),
        "juízes: nota geral": judge_mean("overall"),
    }
    for dim in DIMS:
        fns[f"juízes: {dim}"] = judge_mean(dim)
    return fns


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def build(runs, name: str = "pilot") -> str:
    data = load(runs)
    fns = metric_fns()
    by = defaultdict(dict)
    for d in data.values():
        by[(d["run"].model, d["run"].level)][d["run"].task] = d
    models = [m for m in selection.ROUND_MODELS if any(k[0] == m for k in by)]
    L = []
    out = L.append
    n_rev = sum(len(d["reviews"]) for d in data.values())
    out(f"# Qualidade de código ({name})\n")
    out(f"{len(data)} runs; {sum(1 for d in data.values() if d['conventions'])} com convenções, "
        f"{sum(1 for d in data.values() if d['static'] and 'error' not in d['static'])} com métricas estáticas, "
        f"{n_rev} revisões de juízes ({sum(1 for d in data.values() if len(d['reviews']) >= 2)} runs com as 2).\n")

    out("## Médias por modelo × nível\n")
    for metric, fn in fns.items():
        out(f"### {metric}\n")
        out("| modelo | " + " | ".join(LEVELS) + " |")
        out("|---|" + "---|" * len(LEVELS))
        for m in models:
            cells = []
            for lv in LEVELS:
                vals = [fn(d) for d in by.get((m, lv), {}).values()]
                vals = [v for v in vals if v is not None]
                cells.append(f"{fmt(mean(vals))} (n={len(vals)})" if vals else "–")
            out(f"| {SHORT.get(m, m)} | " + " | ".join(cells) + " |")
        out("")

    out("## Efeito de cada nível vs `none` (pareado por tarefa; Wilcoxon exato)\n")
    out("Δ = média(nível − none) nos pares completos; agregado sem modelos incompletos ("
        + ", ".join(SHORT[m] for m in PARTIAL) + ").\n")
    out("| métrica | nível | pares | Δ médio | p |")
    out("|---|---|---|---|---|")
    for metric, fn in fns.items():
        for lv in LEVELS[1:]:
            diffs = []
            for m in models:
                if m in PARTIAL:
                    continue
                for task, d in by.get((m, "none"), {}).items():
                    e = by.get((m, lv), {}).get(task)
                    if e and fn(d) is not None and fn(e) is not None:
                        diffs.append(fn(e) - fn(d))
            if diffs:
                _, p = wilcoxon_exact(diffs)
                out(f"| {metric} | {lv} | {len(diffs)} | {statistics.mean(diffs):+.2f} | {p:.3f} |")
    out("")

    out("## Concordância entre juízes (nota geral e por dimensão)\n")
    out("| dupla | n | κ ponderado (geral) | Spearman (geral) | κ médio nas 7 dimensões |")
    out("|---|---|---|---|---|")
    for a, b in itertools.combinations(judge.JUDGES, 2):
        both = [d["reviews"] for d in data.values() if a in d["reviews"] and b in d["reviews"]]
        if not both:
            continue
        ka = kappa_quadratic([r[a]["overall"] for r in both], [r[b]["overall"] for r in both])
        sp = spearman([r[a]["overall"] for r in both], [r[b]["overall"] for r in both])
        kd = mean([kappa_quadratic([r[a]["scores"][dim]["score"] for r in both],
                                   [r[b]["scores"][dim]["score"] for r in both]) for dim in DIMS])
        out(f"| {a} × {b} | {len(both)} | {fmt(ka)} | {fmt(sp)} | {fmt(kd)} |")
    out("")
    out("Viés de cada juiz (média da nota geral que dá − média das duas notas do mesmo run):\n")
    for j in judge.JUDGES:
        diffs = [d["reviews"][j]["overall"] - mean([x["overall"] for x in d["reviews"].values()])
                 for d in data.values() if j in d["reviews"] and len(d["reviews"]) >= 2]
        if diffs:
            out(f"- {j}: {statistics.mean(diffs):+.2f} (n={len(diffs)})")
    out("")

    out("## Validade (Spearman entre medidas, todos os runs)\n")
    ok = lambda d: 1.0 if d["run"].hidden_ok else 0.0  # noqa: E731
    pairs = [("juízes: nota geral", "hidden_ok", fns["juízes: nota geral"], ok),
             ("juízes: requirements", "hidden_ok", fns["juízes: requirements"], ok),
             ("juízes: conventions", "convenções (escore)", fns["juízes: conventions"], fns["convenções (escore)"]),
             ("juízes: nota geral", "Larastan: erros novos", fns["juízes: nota geral"], fns["Larastan: erros novos"]),
             ("convenções (escore)", "hidden_ok", fns["convenções (escore)"], ok)]
    out("| A | B | ρ | n |")
    out("|---|---|---|---|")
    for an, bn, fa, fb in pairs:
        xs = [fa(d) for d in data.values()]
        ys = [fb(d) for d in data.values()]
        n = sum(1 for x, y in zip(xs, ys) if x is not None and y is not None)
        out(f"| {an} | {bn} | {fmt(spearman(xs, ys))} | {n} |")
    out("")

    out("## Convenções: quantas vezes cada regra se aplicou e foi cumprida\n")
    out("| regra | descrição | aplica | cumpre |")
    out("|---|---|---|---|")
    for rule, desc in cv.RULES.items():
        app = [x for d in data.values() if d["conventions"] for x in d["conventions"]["rules"]
               if x["rule"] == rule and x["applies"]]
        out(f"| {rule} | {desc} | {len(app)} | {sum(1 for x in app if x['ok'])} |")
    text = "\n".join(L) + "\n"
    path = selection.QUALITY_DIR / f"report-{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return f"written {path.relative_to(selection.BENCH_DIR)}"
