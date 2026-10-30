# Qualidade de código (full, todos os juízes)

309 runs; 309 com convenções, 309 com métricas estáticas, 836 revisões de juízes (309 runs com 2 ou mais, 218 com 3).

Notas dos juízes: média de TODOS os juízes de cada run, isto é, os dois de famílias distintas da do autor mais o juiz da mesma família (`runs/quality/self-family/`), quando ele existe. É a regra usada no artigo do TCC; `report-<name>.md` sem este sufixo usa só os dois de fora.

## Médias por modelo × nível

### convenções (escore)

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 0.84 (n=14) | 0.88 (n=14) | 0.88 (n=14) | 0.88 (n=14) |
| Haiku 5.5 | 0.88 (n=14) | 0.91 (n=14) | 0.91 (n=14) | 0.91 (n=14) |
| Muse Spark 1.3 | 0.57 (n=14) | 0.72 (n=14) | 0.80 (n=14) | 0.73 (n=14) |
| DeepSeek v4.1 flash | 0.77 (n=14) | 0.86 (n=14) | 0.87 (n=14) | 0.87 (n=14) |
| Beam (free) | 0.60 (n=10) | 0.58 (n=7) | 0.50 (n=5) | 0.66 (n=7) |
| gpt-oss-20b | 0.50 (n=14) | 0.51 (n=14) | 0.55 (n=13) | 0.50 (n=14) |

### Larastan: erros novos

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 6.64 (n=14) | 5.36 (n=14) | 5.50 (n=14) | 5.21 (n=14) |
| Haiku 5.5 | 6.00 (n=14) | 4.71 (n=14) | 5.57 (n=14) | 5.71 (n=14) |
| Muse Spark 1.3 | 4.79 (n=14) | 5.43 (n=14) | 4.43 (n=14) | 4.50 (n=14) |
| DeepSeek v4.1 flash | 5.93 (n=14) | 6.21 (n=14) | 5.86 (n=14) | 5.57 (n=14) |
| Beam (free) | 7.50 (n=10) | 3.00 (n=7) | 6.40 (n=5) | 4.00 (n=7) |
| gpt-oss-20b | 4.60 (n=10) | 3.00 (n=13) | 2.80 (n=10) | 1.25 (n=8) |

### complexidade média

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 2.31 (n=14) | 2.22 (n=14) | 2.19 (n=14) | 2.26 (n=14) |
| Haiku 5.5 | 2.18 (n=14) | 2.14 (n=14) | 2.19 (n=14) | 2.12 (n=14) |
| Muse Spark 1.3 | 2.83 (n=14) | 2.73 (n=14) | 2.61 (n=14) | 2.81 (n=14) |
| DeepSeek v4.1 flash | 2.38 (n=14) | 2.45 (n=14) | 2.39 (n=14) | 2.25 (n=14) |
| Beam (free) | 3.78 (n=10) | 2.62 (n=7) | 3.24 (n=5) | 2.94 (n=7) |
| gpt-oss-20b | 3.12 (n=14) | 2.45 (n=14) | 2.55 (n=13) | 2.60 (n=14) |

### casos de teste novos

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 16.71 (n=14) | 33.86 (n=14) | 34.29 (n=14) | 33.93 (n=14) |
| Haiku 5.5 | 36.79 (n=14) | 45.29 (n=14) | 45.43 (n=14) | 42.00 (n=14) |
| Muse Spark 1.3 | 1.14 (n=14) | 9.71 (n=14) | 8.71 (n=14) | 5.36 (n=14) |
| DeepSeek v4.1 flash | 8.00 (n=14) | 27.79 (n=14) | 28.43 (n=14) | 32.07 (n=14) |
| Beam (free) | 0.00 (n=10) | 0.00 (n=7) | 0.00 (n=5) | 1.14 (n=7) |
| gpt-oss-20b | 0.00 (n=14) | 0.00 (n=14) | 2.93 (n=14) | 0.00 (n=14) |

### Jaccard vs referência

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 0.63 (n=14) | 0.64 (n=14) | 0.63 (n=14) | 0.63 (n=14) |
| Haiku 5.5 | 0.62 (n=14) | 0.60 (n=14) | 0.62 (n=14) | 0.60 (n=14) |
| Muse Spark 1.3 | 0.62 (n=14) | 0.62 (n=14) | 0.63 (n=14) | 0.63 (n=14) |
| DeepSeek v4.1 flash | 0.62 (n=14) | 0.63 (n=14) | 0.63 (n=14) | 0.63 (n=14) |
| Beam (free) | 0.63 (n=10) | 0.51 (n=7) | 0.83 (n=5) | 0.64 (n=7) |
| gpt-oss-20b | 0.59 (n=14) | 0.57 (n=14) | 0.53 (n=14) | 0.56 (n=14) |

### juízes: nota geral

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 3.93 (n=14) | 4.12 (n=14) | 4.11 (n=14) | 4.12 (n=14) |
| Haiku 5.5 | 4.07 (n=14) | 4.29 (n=14) | 4.25 (n=14) | 4.19 (n=14) |
| Muse Spark 1.3 | 2.57 (n=14) | 3.12 (n=14) | 3.36 (n=14) | 3.07 (n=14) |
| DeepSeek v4.1 flash | 3.21 (n=14) | 3.99 (n=14) | 3.89 (n=14) | 3.98 (n=14) |
| Beam (free) | 2.50 (n=10) | 2.36 (n=7) | 2.40 (n=5) | 2.64 (n=7) |
| gpt-oss-20b | 1.61 (n=14) | 1.43 (n=14) | 1.46 (n=14) | 1.61 (n=14) |

### juízes: requirements

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.57 (n=14) | 4.88 (n=14) | 4.71 (n=14) | 4.74 (n=14) |
| Haiku 5.5 | 4.71 (n=14) | 4.71 (n=14) | 4.67 (n=14) | 4.71 (n=14) |
| Muse Spark 1.3 | 4.36 (n=14) | 4.31 (n=14) | 4.45 (n=14) | 4.38 (n=14) |
| DeepSeek v4.1 flash | 4.36 (n=14) | 4.79 (n=14) | 4.52 (n=14) | 4.60 (n=14) |
| Beam (free) | 4.00 (n=10) | 4.29 (n=7) | 3.50 (n=5) | 4.14 (n=7) |
| gpt-oss-20b | 1.89 (n=14) | 1.54 (n=14) | 1.61 (n=14) | 1.71 (n=14) |

### juízes: conventions

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 3.81 (n=14) | 4.36 (n=14) | 4.44 (n=14) | 4.29 (n=14) |
| Haiku 5.5 | 4.12 (n=14) | 4.48 (n=14) | 4.51 (n=14) | 4.50 (n=14) |
| Muse Spark 1.3 | 2.74 (n=14) | 3.45 (n=14) | 3.52 (n=14) | 3.33 (n=14) |
| DeepSeek v4.1 flash | 3.38 (n=14) | 4.24 (n=14) | 4.30 (n=14) | 4.29 (n=14) |
| Beam (free) | 2.35 (n=10) | 2.71 (n=7) | 2.40 (n=5) | 3.07 (n=7) |
| gpt-oss-20b | 2.04 (n=14) | 1.93 (n=14) | 1.89 (n=14) | 1.96 (n=14) |

### juízes: security

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.64 (n=14) | 4.69 (n=14) | 4.73 (n=14) | 4.74 (n=14) |
| Haiku 5.5 | 4.69 (n=14) | 4.86 (n=14) | 4.81 (n=14) | 4.81 (n=14) |
| Muse Spark 1.3 | 4.33 (n=14) | 4.26 (n=14) | 4.45 (n=14) | 4.45 (n=14) |
| DeepSeek v4.1 flash | 4.50 (n=14) | 4.65 (n=14) | 4.65 (n=14) | 4.67 (n=14) |
| Beam (free) | 4.10 (n=10) | 4.21 (n=7) | 4.10 (n=5) | 4.36 (n=7) |
| gpt-oss-20b | 2.50 (n=14) | 2.61 (n=14) | 2.50 (n=14) | 2.36 (n=14) |

### juízes: tests

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.38 (n=14) | 4.71 (n=14) | 4.76 (n=14) | 4.55 (n=14) |
| Haiku 5.5 | 4.52 (n=14) | 4.74 (n=14) | 4.86 (n=14) | 4.79 (n=14) |
| Muse Spark 1.3 | 1.21 (n=14) | 2.48 (n=14) | 2.86 (n=14) | 2.19 (n=14) |
| DeepSeek v4.1 flash | 2.74 (n=14) | 4.46 (n=14) | 4.40 (n=14) | 4.36 (n=14) |
| Beam (free) | 1.05 (n=10) | 1.00 (n=7) | 1.00 (n=5) | 1.50 (n=7) |
| gpt-oss-20b | 1.00 (n=14) | 1.00 (n=14) | 1.32 (n=14) | 1.00 (n=14) |

### juízes: simplicity

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.36 (n=14) | 4.64 (n=14) | 4.50 (n=14) | 4.62 (n=14) |
| Haiku 5.5 | 4.57 (n=14) | 4.55 (n=14) | 4.58 (n=14) | 4.55 (n=14) |
| Muse Spark 1.3 | 4.05 (n=14) | 4.21 (n=14) | 4.26 (n=14) | 4.17 (n=14) |
| DeepSeek v4.1 flash | 4.12 (n=14) | 4.38 (n=14) | 4.21 (n=14) | 4.38 (n=14) |
| Beam (free) | 3.70 (n=10) | 4.07 (n=7) | 3.90 (n=5) | 3.93 (n=7) |
| gpt-oss-20b | 3.18 (n=14) | 3.21 (n=14) | 2.86 (n=14) | 3.00 (n=14) |

### juízes: readability

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.64 (n=14) | 4.81 (n=14) | 4.71 (n=14) | 4.83 (n=14) |
| Haiku 5.5 | 4.86 (n=14) | 4.90 (n=14) | 4.93 (n=14) | 4.86 (n=14) |
| Muse Spark 1.3 | 4.26 (n=14) | 4.43 (n=14) | 4.50 (n=14) | 4.40 (n=14) |
| DeepSeek v4.1 flash | 4.40 (n=14) | 4.68 (n=14) | 4.56 (n=14) | 4.69 (n=14) |
| Beam (free) | 3.80 (n=10) | 4.07 (n=7) | 4.10 (n=5) | 4.00 (n=7) |
| gpt-oss-20b | 2.75 (n=14) | 2.79 (n=14) | 2.50 (n=14) | 2.68 (n=14) |

### juízes: scope

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.76 (n=14) | 4.83 (n=14) | 4.85 (n=14) | 4.88 (n=14) |
| Haiku 5.5 | 4.93 (n=14) | 4.79 (n=14) | 4.93 (n=14) | 4.79 (n=14) |
| Muse Spark 1.3 | 4.79 (n=14) | 4.95 (n=14) | 4.88 (n=14) | 4.83 (n=14) |
| DeepSeek v4.1 flash | 4.74 (n=14) | 4.36 (n=14) | 4.79 (n=14) | 4.60 (n=14) |
| Beam (free) | 4.85 (n=10) | 3.93 (n=7) | 4.20 (n=5) | 4.57 (n=7) |
| gpt-oss-20b | 3.79 (n=14) | 3.89 (n=14) | 3.36 (n=14) | 3.82 (n=14) |

## Efeito de cada nível vs `none` (pareado por tarefa; Wilcoxon exato)

Δ = média(nível − none) nos pares completos; agregado sem modelos incompletos (Beam (free)).

| métrica | nível | pares | Δ médio | p |
|---|---|---|---|---|
| convenções (escore) | agents | 70 | +0.07 | 0.001 |
| convenções (escore) | skills | 69 | +0.10 | 0.000 |
| convenções (escore) | full | 70 | +0.07 | 0.000 |
| Larastan: erros novos | agents | 66 | -0.53 | 0.034 |
| Larastan: erros novos | skills | 65 | -0.57 | 0.057 |
| Larastan: erros novos | full | 63 | -0.63 | 0.015 |
| complexidade média | agents | 70 | -0.17 | 0.001 |
| complexidade média | skills | 69 | -0.19 | 0.025 |
| complexidade média | full | 70 | -0.16 | 0.051 |
| casos de teste novos | agents | 70 | +10.80 | 0.000 |
| casos de teste novos | skills | 70 | +11.43 | 0.000 |
| casos de teste novos | full | 70 | +10.14 | 0.000 |
| Jaccard vs referência | agents | 70 | -0.00 | 0.265 |
| Jaccard vs referência | skills | 70 | -0.01 | 0.245 |
| Jaccard vs referência | full | 70 | -0.01 | 0.169 |
| juízes: nota geral | agents | 70 | +0.31 | 0.000 |
| juízes: nota geral | skills | 70 | +0.34 | 0.000 |
| juízes: nota geral | full | 70 | +0.31 | 0.000 |
| juízes: requirements | agents | 70 | +0.07 | 0.081 |
| juízes: requirements | skills | 70 | +0.01 | 0.447 |
| juízes: requirements | full | 70 | +0.05 | 0.316 |
| juízes: conventions | agents | 70 | +0.47 | 0.000 |
| juízes: conventions | skills | 70 | +0.52 | 0.000 |
| juízes: conventions | full | 70 | +0.46 | 0.000 |
| juízes: security | agents | 70 | +0.08 | 0.177 |
| juízes: security | skills | 70 | +0.10 | 0.114 |
| juízes: security | full | 70 | +0.07 | 0.052 |
| juízes: tests | agents | 70 | +0.71 | 0.000 |
| juízes: tests | skills | 70 | +0.87 | 0.000 |
| juízes: tests | full | 70 | +0.60 | 0.000 |
| juízes: simplicity | agents | 70 | +0.15 | 0.015 |
| juízes: simplicity | skills | 70 | +0.03 | 0.508 |
| juízes: simplicity | full | 70 | +0.09 | 0.075 |
| juízes: readability | agents | 70 | +0.14 | 0.003 |
| juízes: readability | skills | 70 | +0.06 | 0.245 |
| juízes: readability | full | 70 | +0.11 | 0.015 |
| juízes: scope | agents | 70 | -0.04 | 0.857 |
| juízes: scope | skills | 70 | -0.04 | 0.739 |
| juízes: scope | full | 70 | -0.02 | 0.844 |

## Concordância entre juízes (nota geral e por dimensão)

| dupla | n | κ ponderado (geral) | Spearman (geral) | κ médio nas 7 dimensões |
|---|---|---|---|---|
| opus × muse | 250 | 0.78 | 0.81 | 0.63 |
| opus × deepseek | 249 | 0.84 | 0.83 | 0.80 |
| muse × deepseek | 246 | 0.71 | 0.78 | 0.73 |

Viés de cada juiz (média da nota geral que dá − média das notas de todos os juízes do mesmo run):

- opus: -0.13 (n=281)
- muse: +0.21 (n=278)
- deepseek: -0.07 (n=277)

## Validade (Spearman entre medidas, todos os runs)

| A | B | ρ | n |
|---|---|---|---|
| juízes: nota geral | hidden_ok | 0.53 | 309 |
| juízes: requirements | hidden_ok | 0.55 | 309 |
| juízes: conventions | convenções (escore) | 0.73 | 308 |
| juízes: nota geral | Larastan: erros novos | -0.07 | 294 |
| convenções (escore) | hidden_ok | 0.37 | 308 |

## Autopreferência: juiz da mesma família vs os dois de fora

Revisões incluídas nas médias acima: Opus nos diffs de Sonnet/Haiku, Muse nos do Muse e DeepSeek nos do DeepSeek. Δ = nota do juiz da família − média dos dois juízes de outras famílias no mesmo run (Wilcoxon exato pareado).

| juiz | autores | n | Δ geral | p | leniência fora da família | autopreferência | Δ requirements | Δ conventions | Δ security | Δ tests | Δ simplicity | Δ readability | Δ scope |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus | Haiku 5.5, Sonnet 5.5 | 109 | -0.17 | 0.003 | -0.33 | +0.17 | -0.08 | -0.26 | -0.07 | +0.01 | -0.46 | -0.22 | -0.22 |
| muse | Muse Spark 1.3 | 56 | +0.04 | 0.509 | +0.44 | -0.40 | +0.59 | +0.65 | +0.32 | +0.26 | +0.92 | +0.63 | +0.15 |
| deepseek | DeepSeek v4.1 flash | 53 | -0.17 | 0.039 | -0.18 | +0.01 | -0.10 | -0.09 | +0.09 | -0.23 | -0.24 | -0.05 | +0.01 |

Leniência fora da família: média de (nota do juiz − nota do outro juiz) nos runs de outras famílias, ou seja, o quanto ele já é mais generoso em geral. Autopreferência = Δ geral − leniência. Os Δ por dimensão não descontam a leniência.

## Convenções: quantas vezes cada regra se aplicou e foi cumprida

| regra | descrição | aplica | cumpre |
|---|---|---|---|
| C1 | test-first: production code changes ship with a test | 308 | 193 |
| C2 | Livewire validates with #[Validate] (+ $this->validate()) | 106 | 53 |
| C3 | Livewire authorizes every public action server-side | 87 | 36 |
| C4 | domain writes go through app/Actions/* | 148 | 39 |
| C5 | migrations are generated (timestamped name) and reversible (down()) | 171 | 168 |
| C6 | no service/repository layers | 261 | 260 |
| C7 | Blade escapes output ({{ }}, never {!! !!}) | 130 | 130 |
| C8 | new models declare $fillable or $guarded | 151 | 84 |
| C9 | Bulma UI, no utility-CSS classes or JS UI libraries | 130 | 129 |
| C10 | authorization through policies/gates, not manual role checks | 149 | 106 |
