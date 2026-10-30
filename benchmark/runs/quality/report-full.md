# Qualidade de código (full)

309 runs; 309 com convenções, 309 com métricas estáticas, 615 revisões de juízes (306 runs com as 2).

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
| Sonnet 5.5 | 3.96 (n=14) | 4.14 (n=14) | 4.17 (n=12) | 4.14 (n=14) |
| Haiku 5.5 | 4.18 (n=14) | 4.39 (n=14) | 4.31 (n=13) | 4.25 (n=14) |
| Muse Spark 1.3 | 2.61 (n=14) | 3.04 (n=14) | 3.32 (n=14) | 3.11 (n=14) |
| DeepSeek v4.1 flash | 3.18 (n=14) | 4.11 (n=14) | 3.93 (n=14) | 4.07 (n=14) |
| Beam (free) | 2.50 (n=10) | 2.36 (n=7) | 2.40 (n=5) | 2.64 (n=7) |
| gpt-oss-20b | 1.61 (n=14) | 1.43 (n=14) | 1.46 (n=14) | 1.61 (n=14) |

### juízes: requirements

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.61 (n=14) | 4.86 (n=14) | 4.75 (n=12) | 4.71 (n=14) |
| Haiku 5.5 | 4.86 (n=14) | 4.79 (n=14) | 4.62 (n=13) | 4.75 (n=14) |
| Muse Spark 1.3 | 4.18 (n=14) | 4.11 (n=14) | 4.25 (n=14) | 4.18 (n=14) |
| DeepSeek v4.1 flash | 4.43 (n=14) | 4.79 (n=14) | 4.54 (n=14) | 4.64 (n=14) |
| Beam (free) | 4.00 (n=10) | 4.29 (n=7) | 3.50 (n=5) | 4.14 (n=7) |
| gpt-oss-20b | 1.89 (n=14) | 1.54 (n=14) | 1.61 (n=14) | 1.71 (n=14) |

### juízes: conventions

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 3.93 (n=14) | 4.43 (n=14) | 4.58 (n=12) | 4.39 (n=14) |
| Haiku 5.5 | 4.25 (n=14) | 4.50 (n=14) | 4.54 (n=13) | 4.61 (n=14) |
| Muse Spark 1.3 | 2.50 (n=14) | 3.18 (n=14) | 3.36 (n=14) | 3.14 (n=14) |
| DeepSeek v4.1 flash | 3.39 (n=14) | 4.29 (n=14) | 4.32 (n=14) | 4.32 (n=14) |
| Beam (free) | 2.35 (n=10) | 2.71 (n=7) | 2.40 (n=5) | 3.07 (n=7) |
| gpt-oss-20b | 2.04 (n=14) | 1.93 (n=14) | 1.89 (n=14) | 1.96 (n=14) |

### juízes: security

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.68 (n=14) | 4.68 (n=14) | 4.79 (n=12) | 4.71 (n=14) |
| Haiku 5.5 | 4.71 (n=14) | 4.89 (n=14) | 4.85 (n=13) | 4.89 (n=14) |
| Muse Spark 1.3 | 4.21 (n=14) | 4.14 (n=14) | 4.39 (n=14) | 4.32 (n=14) |
| DeepSeek v4.1 flash | 4.46 (n=14) | 4.64 (n=14) | 4.61 (n=14) | 4.64 (n=14) |
| Beam (free) | 4.10 (n=10) | 4.21 (n=7) | 4.10 (n=5) | 4.36 (n=7) |
| gpt-oss-20b | 2.50 (n=14) | 2.61 (n=14) | 2.50 (n=14) | 2.36 (n=14) |

### juízes: tests

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.46 (n=14) | 4.75 (n=14) | 4.75 (n=12) | 4.54 (n=14) |
| Haiku 5.5 | 4.57 (n=14) | 4.71 (n=14) | 4.77 (n=13) | 4.75 (n=14) |
| Muse Spark 1.3 | 1.21 (n=14) | 2.36 (n=14) | 2.75 (n=14) | 2.07 (n=14) |
| DeepSeek v4.1 flash | 2.79 (n=14) | 4.57 (n=14) | 4.43 (n=14) | 4.46 (n=14) |
| Beam (free) | 1.05 (n=10) | 1.00 (n=7) | 1.00 (n=5) | 1.50 (n=7) |
| gpt-oss-20b | 1.00 (n=14) | 1.00 (n=14) | 1.32 (n=14) | 1.00 (n=14) |

### juízes: simplicity

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.50 (n=14) | 4.75 (n=14) | 4.67 (n=12) | 4.82 (n=14) |
| Haiku 5.5 | 4.71 (n=14) | 4.68 (n=14) | 4.81 (n=13) | 4.68 (n=14) |
| Muse Spark 1.3 | 3.75 (n=14) | 3.89 (n=14) | 3.93 (n=14) | 3.89 (n=14) |
| DeepSeek v4.1 flash | 4.21 (n=14) | 4.46 (n=14) | 4.32 (n=14) | 4.39 (n=14) |
| Beam (free) | 3.70 (n=10) | 4.07 (n=7) | 3.90 (n=5) | 3.93 (n=7) |
| gpt-oss-20b | 3.18 (n=14) | 3.21 (n=14) | 2.86 (n=14) | 3.00 (n=14) |

### juízes: readability

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.79 (n=14) | 4.86 (n=14) | 4.83 (n=12) | 4.96 (n=14) |
| Haiku 5.5 | 4.86 (n=14) | 4.96 (n=14) | 4.96 (n=13) | 4.93 (n=14) |
| Muse Spark 1.3 | 4.04 (n=14) | 4.21 (n=14) | 4.32 (n=14) | 4.18 (n=14) |
| DeepSeek v4.1 flash | 4.43 (n=14) | 4.68 (n=14) | 4.61 (n=14) | 4.68 (n=14) |
| Beam (free) | 3.80 (n=10) | 4.07 (n=7) | 4.10 (n=5) | 4.00 (n=7) |
| gpt-oss-20b | 2.75 (n=14) | 2.79 (n=14) | 2.50 (n=14) | 2.68 (n=14) |

### juízes: scope

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.79 (n=14) | 4.93 (n=14) | 4.92 (n=12) | 4.96 (n=14) |
| Haiku 5.5 | 4.96 (n=14) | 4.89 (n=14) | 5.00 (n=13) | 4.89 (n=14) |
| Muse Spark 1.3 | 4.68 (n=14) | 4.93 (n=14) | 4.86 (n=14) | 4.79 (n=14) |
| DeepSeek v4.1 flash | 4.71 (n=14) | 4.36 (n=14) | 4.79 (n=14) | 4.61 (n=14) |
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
| juízes: nota geral | agents | 70 | +0.31 | 0.001 |
| juízes: nota geral | skills | 67 | +0.34 | 0.001 |
| juízes: nota geral | full | 70 | +0.33 | 0.000 |
| juízes: requirements | agents | 70 | +0.02 | 0.313 |
| juízes: requirements | skills | 67 | -0.04 | 0.732 |
| juízes: requirements | full | 70 | +0.01 | 0.815 |
| juízes: conventions | agents | 70 | +0.44 | 0.000 |
| juízes: conventions | skills | 67 | +0.51 | 0.000 |
| juízes: conventions | full | 70 | +0.46 | 0.000 |
| juízes: security | agents | 70 | +0.08 | 0.230 |
| juízes: security | skills | 67 | +0.12 | 0.056 |
| juízes: security | full | 70 | +0.07 | 0.171 |
| juízes: tests | agents | 70 | +0.67 | 0.000 |
| juízes: tests | skills | 67 | +0.82 | 0.000 |
| juízes: tests | full | 70 | +0.56 | 0.000 |
| juízes: simplicity | agents | 70 | +0.13 | 0.057 |
| juízes: simplicity | skills | 67 | +0.04 | 0.557 |
| juízes: simplicity | full | 70 | +0.09 | 0.101 |
| juízes: readability | agents | 70 | +0.13 | 0.020 |
| juízes: readability | skills | 67 | +0.06 | 0.195 |
| juízes: readability | full | 70 | +0.11 | 0.042 |
| juízes: scope | agents | 70 | +0.01 | 0.659 |
| juízes: scope | skills | 67 | -0.01 | 0.638 |
| juízes: scope | full | 70 | +0.03 | 0.559 |

## Concordância entre juízes (nota geral e por dimensão)

| dupla | n | κ ponderado (geral) | Spearman (geral) | κ médio nas 7 dimensões |
|---|---|---|---|---|
| opus × muse | 82 | 0.85 | 0.91 | 0.73 |
| opus × deepseek | 87 | 0.81 | 0.84 | 0.84 |
| muse × deepseek | 137 | 0.71 | 0.68 | 0.79 |

Viés de cada juiz (média da nota geral que dá − média das duas notas do mesmo run):

- opus: -0.17 (n=169)
- muse: +0.22 (n=219)
- deepseek: -0.09 (n=224)

## Validade (Spearman entre medidas, todos os runs)

| A | B | ρ | n |
|---|---|---|---|
| juízes: nota geral | hidden_ok | 0.52 | 306 |
| juízes: requirements | hidden_ok | 0.54 | 306 |
| juízes: conventions | convenções (escore) | 0.73 | 305 |
| juízes: nota geral | Larastan: erros novos | -0.07 | 291 |
| convenções (escore) | hidden_ok | 0.37 | 308 |

## Autopreferência: juiz da mesma família vs os dois de fora

Revisões extras, fora das médias acima: Opus nos diffs de Sonnet/Haiku, Muse nos do Muse e DeepSeek nos do DeepSeek. Δ = nota do juiz da família − média dos dois juízes de outras famílias no mesmo run (Wilcoxon exato pareado).

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
