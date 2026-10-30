#!/usr/bin/env python3
"""Gera as figuras do artigo (PDF vetorial) a partir dos dados do benchmark.

Uso, a partir de tcc-artigo-template-latex/figuras/:
    python3 gerar-figuras.py

Fontes de dados (somente leitura):
  - benchmark/runs/report.csv                  pass@1, turnos e tokens por run
  - benchmark/quality (pacote Python)           seleção dos runs, par de juízes atribuído,
                                                revisões, static.jsonl e conventions.jsonl
  - benchmark/runs/quality/self-family/         revisão do juiz da mesma família (juizes.py)

As notas dos juízes (F5, F6, F8) usam a média de TODOS os juízes de cada execução, incluindo o
da mesma família do autor, como no artigo (ver calcular-tabelas.py); report-full.md usa só os
dois juízes de fora da família.

Os agregados usados em cada figura são impressos no terminal para conferência com
runs/reduced-1-report.md e runs/quality/report-full.md.
"""
from __future__ import annotations

import collections
import csv
import json
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BENCH = ROOT / "benchmark"
OUT = HERE / "04-desenvolvimento"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))

from quality import analysis, selection  # noqa: E402
import juizes  # noqa: E402

# --- paleta (dataviz: categórica em ordem fixa; status; sequencial azul) -----------------------
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GOOD, CRITICAL = "#0ca30c", "#d03b3b"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8984"
GRID = "#e6e5e1"

LEVELS = ["none", "agents", "skills", "full"]
MODELS = [  # ordem fixa: a cor segue o modelo em todas as figuras
    ("claude-sonnet-5-5", "Sonnet 5.5"),
    ("claude-haiku-5-5", "Haiku 5.5"),
    ("opencode-go/muse-spark-1.3-contributor", "Muse Spark 1.3"),
    ("opencode-go/deepseek-v4.1-flash", "DeepSeek v4.1 flash"),
    ("opencode-go/beam-free", "Beam (free)"),
    ("llama/gpt-oss-20b", "gpt-oss-20b"),
]
COLOR = {m: CAT[i] for i, (m, _) in enumerate(MODELS)}
LABEL = dict(MODELS)
FULL = [m for m, _ in MODELS if m != "opencode-go/beam-free"]   # matriz completa (56 células)
TASKS = ["T01", "T02", "T03a", "T03b", "T04a", "T04b", "T04c", "T05", "T06", "T07", "T08", "T09",
         "T10", "T11"]

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.edgecolor": INK3, "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2,
    "axes.labelcolor": INK, "text.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
    "axes.axisbelow": True, "legend.frameon": False, "pdf.fonttype": 42,
})


def smean(xs):
    return statistics.mean(xs) if xs else float("nan")


def despine(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def save(fig, name):
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"-> {path.relative_to(ROOT)}")


# --- dados -------------------------------------------------------------------------------------
def report_rows():
    with open(BENCH / "runs" / "report.csv", newline="") as f:
        return list(csv.DictReader(f))


def round_rows():
    """Linhas de report.csv que entram na rodada reduzida (mesmo critério de quality.selection)."""
    runs = {r.run_id: r for r in selection.runs()}
    return [row for row in report_rows() if row["run_id"] in runs], runs


def static_by_run():
    """static.jsonl (camada 1), uma linha por run; a cópia por run em runs/<id>/quality não é versionada."""
    out = {}
    with open(BENCH / "runs" / "quality" / "static.jsonl") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                out[d["run_id"]] = d
    return out


def task_short(task):
    return task.split("-")[0]


# --- F4: mosaico tarefa x nível x modelo -------------------------------------------------------
def fig_mosaico(rows):
    ok = {}
    for r in rows:
        if r["model"] in FULL:
            ok[(r["model"], task_short(r["task"]), r["level"])] = r["hidden_ok"] == "True"
    fig, axes = plt.subplots(1, len(FULL), figsize=(6.3, 4.2), sharey=True,
                             gridspec_kw={"wspace": 0.12})
    for ax, m in zip(axes, FULL):
        ax.set_title(LABEL[m], pad=6)
        ax.grid(False)
        for i, t in enumerate(TASKS):
            for j, lv in enumerate(LEVELS):
                v = ok.get((m, t, lv))
                color = GOOD if v else CRITICAL
                ax.add_patch(plt.Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, color=color, lw=0))
                ax.text(j + 0.5, i + 0.5, "✓" if v else "✗", ha="center", va="center",
                        color="white", fontsize=7.5, fontfamily="DejaVu Sans")
        ax.set_xlim(0, 4); ax.set_ylim(len(TASKS), 0)
        ax.set_xticks([k + 0.5 for k in range(4)]); ax.set_xticklabels(LEVELS, rotation=60, ha="right")
        ax.set_yticks([k + 0.5 for k in range(len(TASKS))]); ax.set_yticklabels(TASKS)
        ax.tick_params(length=0)
        despine(ax, keep=())
    counts = collections.Counter(v for v in ok.values())
    print("F4 células:", dict(counts), "total", sum(counts.values()))
    fig.legend(handles=[Patch(color=GOOD, label="✓ todos os testes ocultos passam"),
                        Patch(color=CRITICAL, label="✗ ao menos um teste oculto falha")],
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04),
               prop={"family": "DejaVu Sans", "size": 8})
    save(fig, "fig-mosaico-pass1.pdf")


# --- F5: nota geral dos juízes e casos de teste por modelo x nível -----------------------------
def fig_qualidade_modelo(data):
    static = static_by_run()
    nota = collections.defaultdict(list); testes = collections.defaultdict(list)
    for rid, d in data.items():
        m, lv = d["run"].model, d["run"].level
        v = juizes.judge_mean(d, "overall")
        if v is not None: nota[(m, lv)].append(v)
        t = static.get(rid, {}).get("test_cases_added")
        if t is not None: testes[(m, lv)].append(t)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.3, 3.0), gridspec_kw={"wspace": 0.35})
    x = range(4)
    for m, lab in MODELS:
        ys = [smean(nota[(m, lv)]) for lv in LEVELS]
        ts = [smean(testes[(m, lv)]) for lv in LEVELS]
        print(f"F5 {lab:20s} nota geral", [round(v, 2) for v in ys], " casos de teste", [round(v, 1) for v in ts])
        for ax, vals in ((a1, ys), (a2, ts)):
            ax.plot(x, vals, color=COLOR[m], lw=1.6, marker="o", ms=4.5,
                    markeredgecolor="white", markeredgewidth=1.2, label=lab)
    a1.set_ylim(1, 5); a1.set_yticks([1, 2, 3, 4, 5]); a1.set_title("Nota geral dos juízes (1 a 5)")
    a2.set_ylim(0, 50); a2.set_title("Casos de teste novos por execução")
    for ax in (a1, a2):
        ax.set_xticks(list(x)); ax.set_xticklabels(LEVELS); ax.set_xlim(-0.3, 3.3)
        ax.grid(axis="x", visible=False); despine(ax)
    a1.set_xlim(-0.3, 3.3)
    fig.legend(handles=[Line2D([], [], color=COLOR[m], lw=1.6, marker="o", ms=4, label=lab) for m, lab in MODELS],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.16))
    save(fig, "fig-qualidade-modelo.pdf")


# --- F6: Δ por dimensão dos juízes vs none (Wilcoxon exato, 70 pares; média de todos os juízes) --
def fig_efeito_dimensoes(data):
    ef = juizes.efeitos(data)
    EFEITOS = {juizes.PT[dim]: {lv: ef[(dim, lv)][:2] for lv in ("agents", "skills", "full")}
               for dim in ["overall"] + juizes.DIMS}
    dims = list(EFEITOS)
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    offs = {"agents": -0.22, "skills": 0.0, "full": 0.22}
    marks = {"agents": "o", "skills": "s", "full": "D"}
    for i, dim in enumerate(dims):
        for k, lv in enumerate(("agents", "skills", "full")):
            d, p = EFEITOS[dim][lv]
            y = i + offs[lv]
            filled = p < 0.05
            ax.plot([0, d], [y, y], color=GRID, lw=1.2, zorder=1)
            ax.plot(d, y, marker=marks[lv], ms=6, color=CAT[k], markerfacecolor=CAT[k] if filled else "white",
                    markeredgewidth=1.3, zorder=3)
    ax.axvline(0, color=INK3, lw=0.8)
    ax.set_yticks(range(len(dims))); ax.set_yticklabels(dims); ax.invert_yaxis()
    ax.set_xlabel("Δ médio contra o nível none (pontos na escala de 1 a 5; 70 pares por nível)")
    ax.grid(axis="y", visible=False); despine(ax)
    handles = [Line2D([], [], marker=marks[lv], color=CAT[k], ms=6, lw=0, label=lv)
               for k, lv in enumerate(("agents", "skills", "full"))]
    handles += [Line2D([], [], marker="o", color=INK2, ms=6, lw=0, label="p < 0,05"),
                Line2D([], [], marker="o", color=INK2, markerfacecolor="white", ms=6, lw=0, label="p ≥ 0,05")]
    ax.legend(handles=handles, loc="lower right", ncol=2)
    for dim in dims:
        print(f"F6 {dim:13s}", {lv: (round(d, 2), round(p, 3)) for lv, (d, p) in EFEITOS[dim].items()})
    save(fig, "fig-efeito-dimensoes.pdf")


# --- F7: custo relativo ao none (medianas de report.csv) ---------------------------------------
def fig_custo(rows):
    med = {}
    for m in FULL:
        for lv in LEVELS:
            cell = [r for r in rows if r["model"] == m and r["level"] == lv]
            med[(m, lv, "turns")] = statistics.median(float(r["turns"]) for r in cell)
            med[(m, lv, "tokens_in")] = statistics.median(
                float(r["tokens_in"] or 0) + float(r["tokens_cache_read"] or 0) for r in cell)
            med[(m, lv, "agent_s")] = statistics.median(float(r["agent_s"]) for r in cell)
        print(f"F7 {LABEL[m]:20s}", [(lv, med[(m, lv, 'turns')], int(med[(m, lv, 'tokens_in')]),
                                     round(med[(m, lv, 'agent_s')] / 60, 1)) for lv in LEVELS])
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.9), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, (metric, title) in zip(axes, (("turns", "Turnos"), ("tokens_in", "Tokens de entrada"))):
        for k, lv in enumerate(("agents", "skills", "full")):
            ys = [100 * (med[(m, lv, metric)] / med[(m, "none", metric)] - 1) for m in FULL]
            ax.barh([i + (k - 1) * 0.26 for i in range(len(FULL))], ys, height=0.24, color=CAT[k], label=lv)
        ax.axvline(0, color=INK3, lw=0.8)
        ax.set_title(title)
        ax.set_xlabel("variação da mediana contra none (%)")
        ax.set_yticks(range(len(FULL))); ax.set_yticklabels([LABEL[m] for m in FULL]); ax.invert_yaxis()
        ax.grid(axis="y", visible=False); despine(ax)
    fig.legend(handles=[Patch(color=CAT[k], label=lv) for k, lv in enumerate(("agents", "skills", "full"))],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.1))
    save(fig, "fig-custo-relativo.pdf")


# --- F8: concordância entre juízes (nota geral) -----------------------------------------------
def fig_concordancia(data):
    pairs = [("opus", "muse"), ("opus", "deepseek"), ("muse", "deepseek")]
    names = {"opus": "Opus 5.5", "muse": "Muse Spark 1.3", "deepseek": "DeepSeek v4.1 flash"}
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.5), gridspec_kw={"wspace": 0.3})
    for ax, (a, b) in zip(axes, pairs):
        xs, ys = [], []
        for d in data.values():
            rv = d["reviews"]
            if a in rv and b in rv:
                xs.append(rv[a]["overall"]); ys.append(rv[b]["overall"])
        k = analysis.kappa_quadratic(xs, ys)
        cnt = collections.Counter(zip(xs, ys))
        print(f"F8 {a}×{b}: n={len(xs)} κ={k:.2f}")
        ax.plot([0.5, 5.5], [0.5, 5.5], color=GRID, lw=1)
        for (x, y), c in cnt.items():
            ax.scatter(x, y, s=12 + 9 * c, color=CAT[0], alpha=0.85, edgecolors="white", linewidths=0.8, zorder=3)
            if c >= 10:
                ax.text(x, y, str(c), ha="center", va="center", fontsize=6.5, color="white", zorder=4)
        ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
        ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
        ax.set_xlabel(names[a]); ax.set_ylabel(names[b])
        ax.set_title(f"κ ponderado = {k:.2f}  (n = {len(xs)})")
        ax.set_aspect("equal"); despine(ax)
    save(fig, "fig-concordancia-juizes.pdf")


if __name__ == "__main__":
    rows, runs = round_rows()
    print("runs da rodada:", len(rows))
    data = juizes.load_all_judges(list(runs.values()))
    print("revisões de juízes:", sum(len(d["reviews"]) for d in data.values()))
    fig_mosaico(rows)
    fig_qualidade_modelo(data)
    fig_efeito_dimensoes(data)
    fig_custo(rows)
    fig_concordancia(data)
