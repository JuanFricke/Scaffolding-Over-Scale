# Qualidade de código (pilot)

46 runs; 46 com convenções, 46 com métricas estáticas, 92 revisões de juízes (46 runs com as 2).

## Médias por modelo × nível

### convenções (escore)

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 0.93 (n=2) | 1.00 (n=2) | 0.94 (n=2) | 1.00 (n=2) |
| Haiku 5.5 | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |
| Muse Spark 1.3 | 0.43 (n=2) | 0.93 (n=2) | 1.00 (n=2) | 0.43 (n=2) |
| DeepSeek v4.1 flash | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 0.93 (n=2) |
| Beam (free) | 0.43 (n=2) | 0.00 (n=1) | 0.38 (n=2) | 0.00 (n=1) |
| gpt-oss-20b | 0.36 (n=2) | 0.36 (n=2) | 0.42 (n=2) | 0.43 (n=2) |

### Larastan: erros novos

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 8.00 (n=2) | 7.00 (n=2) | 8.00 (n=2) | 7.00 (n=2) |
| Haiku 5.5 | 6.50 (n=2) | 3.00 (n=2) | 8.00 (n=2) | 7.00 (n=2) |
| Muse Spark 1.3 | 9.00 (n=2) | 8.00 (n=2) | 8.50 (n=2) | 7.50 (n=2) |
| DeepSeek v4.1 flash | 9.00 (n=2) | 8.50 (n=2) | 8.50 (n=2) | 8.00 (n=2) |
| Beam (free) | 8.00 (n=2) | 2.00 (n=1) | 9.50 (n=2) | 0.00 (n=1) |
| gpt-oss-20b | 10.50 (n=2) | 11.50 (n=2) | 2.00 (n=2) | 0.00 (n=1) |

### complexidade média

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 3.70 (n=2) | 3.67 (n=2) | 3.80 (n=2) | 3.69 (n=2) |
| Haiku 5.5 | 3.52 (n=2) | 3.49 (n=2) | 3.44 (n=2) | 3.68 (n=2) |
| Muse Spark 1.3 | 3.75 (n=2) | 3.46 (n=2) | 3.73 (n=2) | 3.95 (n=2) |
| DeepSeek v4.1 flash | 3.73 (n=2) | 3.75 (n=2) | 3.73 (n=2) | 3.71 (n=2) |
| Beam (free) | 4.01 (n=2) | 6.50 (n=1) | 4.28 (n=2) | 5.00 (n=1) |
| gpt-oss-20b | 4.28 (n=2) | 3.96 (n=2) | 3.73 (n=2) | 4.19 (n=2) |

### casos de teste novos

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 12.50 (n=2) | 25.00 (n=2) | 20.50 (n=2) | 24.50 (n=2) |
| Haiku 5.5 | 20.00 (n=2) | 27.00 (n=2) | 24.50 (n=2) | 23.50 (n=2) |
| Muse Spark 1.3 | 0.00 (n=2) | 2.50 (n=2) | 13.50 (n=2) | 0.00 (n=2) |
| DeepSeek v4.1 flash | 2.00 (n=2) | 13.50 (n=2) | 15.00 (n=2) | 18.00 (n=2) |
| Beam (free) | 0.00 (n=2) | 0.00 (n=1) | 0.00 (n=2) | 0.00 (n=1) |
| gpt-oss-20b | 0.00 (n=2) | 0.00 (n=2) | 0.00 (n=2) | 0.00 (n=2) |

### Jaccard vs referência

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |
| Haiku 5.5 | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |
| Muse Spark 1.3 | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |
| DeepSeek v4.1 flash | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |
| Beam (free) | 1.00 (n=2) | 1.00 (n=1) | 1.00 (n=2) | 1.00 (n=1) |
| gpt-oss-20b | 0.94 (n=2) | 0.88 (n=2) | 0.88 (n=2) | 0.80 (n=2) |

### juízes: nota geral

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.25 (n=2) | 4.50 (n=2) | 4.50 (n=2) | 4.00 (n=2) |
| Haiku 5.5 | 4.50 (n=2) | 4.75 (n=2) | 4.75 (n=2) | 4.25 (n=2) |
| Muse Spark 1.3 | 2.75 (n=2) | 3.75 (n=2) | 4.00 (n=2) | 2.75 (n=2) |
| DeepSeek v4.1 flash | 3.00 (n=2) | 3.75 (n=2) | 4.00 (n=2) | 4.25 (n=2) |
| Beam (free) | 2.75 (n=2) | 3.00 (n=1) | 2.50 (n=2) | 3.00 (n=1) |
| gpt-oss-20b | 2.50 (n=2) | 2.50 (n=2) | 1.75 (n=2) | 2.00 (n=2) |

### juízes: requirements

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 5.00 (n=2) | 5.00 (n=2) | 4.75 (n=2) | 4.75 (n=2) |
| Haiku 5.5 | 5.00 (n=2) | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) |
| Muse Spark 1.3 | 4.50 (n=2) | 4.50 (n=2) | 4.50 (n=2) | 4.50 (n=2) |
| DeepSeek v4.1 flash | 4.50 (n=2) | 5.00 (n=2) | 4.50 (n=2) | 4.75 (n=2) |
| Beam (free) | 4.00 (n=2) | 5.00 (n=1) | 3.75 (n=2) | 5.00 (n=1) |
| gpt-oss-20b | 3.00 (n=2) | 3.00 (n=2) | 2.00 (n=2) | 3.00 (n=2) |

### juízes: conventions

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 3.75 (n=2) | 4.50 (n=2) | 4.50 (n=2) | 4.50 (n=2) |
| Haiku 5.5 | 4.50 (n=2) | 4.75 (n=2) | 4.75 (n=2) | 4.75 (n=2) |
| Muse Spark 1.3 | 2.25 (n=2) | 3.75 (n=2) | 4.00 (n=2) | 2.75 (n=2) |
| DeepSeek v4.1 flash | 3.50 (n=2) | 4.75 (n=2) | 4.50 (n=2) | 4.50 (n=2) |
| Beam (free) | 2.25 (n=2) | 3.00 (n=1) | 2.75 (n=2) | 2.50 (n=1) |
| gpt-oss-20b | 2.25 (n=2) | 2.25 (n=2) | 2.00 (n=2) | 2.50 (n=2) |

### juízes: security

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.75 (n=2) | 4.50 (n=2) | 4.75 (n=2) | 4.25 (n=2) |
| Haiku 5.5 | 4.75 (n=2) | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) |
| Muse Spark 1.3 | 4.00 (n=2) | 4.25 (n=2) | 4.00 (n=2) | 4.25 (n=2) |
| DeepSeek v4.1 flash | 4.50 (n=2) | 4.75 (n=2) | 4.50 (n=2) | 4.50 (n=2) |
| Beam (free) | 4.00 (n=2) | 5.00 (n=1) | 4.00 (n=2) | 5.00 (n=1) |
| gpt-oss-20b | 3.50 (n=2) | 3.25 (n=2) | 3.25 (n=2) | 3.25 (n=2) |

### juízes: tests

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) | 4.75 (n=2) |
| Haiku 5.5 | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) | 4.50 (n=2) |
| Muse Spark 1.3 | 1.00 (n=2) | 3.00 (n=2) | 4.25 (n=2) | 1.00 (n=2) |
| DeepSeek v4.1 flash | 2.50 (n=2) | 4.75 (n=2) | 4.50 (n=2) | 4.50 (n=2) |
| Beam (free) | 1.00 (n=2) | 1.00 (n=1) | 1.00 (n=2) | 1.00 (n=1) |
| gpt-oss-20b | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) | 1.00 (n=2) |

### juízes: simplicity

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) | 5.00 (n=2) |
| Haiku 5.5 | 5.00 (n=2) | 4.75 (n=2) | 4.75 (n=2) | 4.75 (n=2) |
| Muse Spark 1.3 | 4.25 (n=2) | 4.00 (n=2) | 4.25 (n=2) | 4.25 (n=2) |
| DeepSeek v4.1 flash | 4.50 (n=2) | 4.50 (n=2) | 4.50 (n=2) | 4.75 (n=2) |
| Beam (free) | 4.00 (n=2) | 4.00 (n=1) | 4.25 (n=2) | 4.50 (n=1) |
| gpt-oss-20b | 3.50 (n=2) | 3.50 (n=2) | 3.25 (n=2) | 3.50 (n=2) |

### juízes: readability

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 4.75 (n=2) | 4.75 (n=2) | 4.75 (n=2) | 5.00 (n=2) |
| Haiku 5.5 | 4.75 (n=2) | 5.00 (n=2) | 4.75 (n=2) | 4.75 (n=2) |
| Muse Spark 1.3 | 4.00 (n=2) | 4.25 (n=2) | 4.50 (n=2) | 4.25 (n=2) |
| DeepSeek v4.1 flash | 4.75 (n=2) | 4.50 (n=2) | 4.75 (n=2) | 4.50 (n=2) |
| Beam (free) | 4.25 (n=2) | 4.00 (n=1) | 4.25 (n=2) | 4.00 (n=1) |
| gpt-oss-20b | 3.00 (n=2) | 3.25 (n=2) | 2.50 (n=2) | 3.50 (n=2) |

### juízes: scope

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 5.00 (n=2) | 5.00 (n=2) | 5.00 (n=2) | 5.00 (n=2) |
| Haiku 5.5 | 5.00 (n=2) | 5.00 (n=2) | 5.00 (n=2) | 5.00 (n=2) |
| Muse Spark 1.3 | 4.50 (n=2) | 5.00 (n=2) | 5.00 (n=2) | 4.75 (n=2) |
| DeepSeek v4.1 flash | 5.00 (n=2) | 4.00 (n=2) | 5.00 (n=2) | 5.00 (n=2) |
| Beam (free) | 5.00 (n=2) | 5.00 (n=1) | 5.00 (n=2) | 4.00 (n=1) |
| gpt-oss-20b | 5.00 (n=2) | 4.50 (n=2) | 2.75 (n=2) | 3.00 (n=2) |

## Efeito de cada nível vs `none` (pareado por tarefa; Wilcoxon exato)

Δ = média(nível − none) nos pares completos; agregado sem modelos incompletos (Beam (free)).

| métrica | nível | pares | Δ médio | p |
|---|---|---|---|---|
| convenções (escore) | agents | 10 | +0.11 | 0.500 |
| convenções (escore) | skills | 10 | +0.13 | 0.125 |
| convenções (escore) | full | 10 | +0.01 | 1.000 |
| Larastan: erros novos | agents | 10 | -1.00 | 0.312 |
| Larastan: erros novos | skills | 10 | -1.60 | 0.625 |
| Larastan: erros novos | full | 9 | -0.67 | 0.250 |
| complexidade média | agents | 10 | -0.13 | 0.156 |
| complexidade média | skills | 10 | -0.11 | 0.406 |
| complexidade média | full | 10 | +0.05 | 0.359 |
| casos de teste novos | agents | 10 | +6.70 | 0.125 |
| casos de teste novos | skills | 10 | +7.80 | 0.031 |
| casos de teste novos | full | 10 | +6.30 | 0.125 |
| Jaccard vs referência | agents | 10 | -0.01 | 1.000 |
| Jaccard vs referência | skills | 10 | -0.01 | 1.000 |
| Jaccard vs referência | full | 10 | -0.03 | 1.000 |
| juízes: nota geral | agents | 10 | +0.45 | 0.062 |
| juízes: nota geral | skills | 10 | +0.40 | 0.266 |
| juízes: nota geral | full | 10 | +0.05 | 0.938 |
| juízes: requirements | agents | 10 | +0.05 | 1.000 |
| juízes: requirements | skills | 10 | -0.25 | 0.500 |
| juízes: requirements | full | 10 | -0.05 | 1.000 |
| juízes: conventions | agents | 10 | +0.75 | 0.016 |
| juízes: conventions | skills | 10 | +0.70 | 0.039 |
| juízes: conventions | full | 10 | +0.55 | 0.027 |
| juízes: security | agents | 10 | +0.00 | 1.000 |
| juízes: security | skills | 10 | +0.00 | 1.000 |
| juízes: security | full | 10 | -0.10 | 0.750 |
| juízes: tests | agents | 10 | +0.95 | 0.062 |
| juízes: tests | skills | 10 | +1.05 | 0.125 |
| juízes: tests | full | 10 | +0.35 | 0.500 |
| juízes: simplicity | agents | 10 | -0.05 | 1.000 |
| juízes: simplicity | skills | 10 | -0.10 | 0.688 |
| juízes: simplicity | full | 10 | +0.05 | 1.000 |
| juízes: readability | agents | 10 | +0.10 | 0.750 |
| juízes: readability | skills | 10 | +0.00 | 1.000 |
| juízes: readability | full | 10 | +0.15 | 0.500 |
| juízes: scope | agents | 10 | -0.20 | 0.750 |
| juízes: scope | skills | 10 | -0.35 | 0.750 |
| juízes: scope | full | 10 | -0.35 | 1.000 |

## Concordância entre juízes (nota geral e por dimensão)

| dupla | n | κ ponderado (geral) | Spearman (geral) | κ médio nas 7 dimensões |
|---|---|---|---|---|
| opus × muse | 10 | 0.85 | 0.85 | 0.80 |
| opus × deepseek | 15 | 0.87 | 0.76 | 0.77 |
| muse × deepseek | 21 | 0.79 | 0.78 | 0.71 |

Viés de cada juiz (média da nota geral que dá − média das duas notas do mesmo run):

- opus: -0.10 (n=25)
- muse: +0.13 (n=31)
- deepseek: -0.04 (n=36)

## Validade (Spearman entre medidas, todos os runs)

| A | B | ρ | n |
|---|---|---|---|
| juízes: nota geral | hidden_ok | 0.48 | 46 |
| juízes: requirements | hidden_ok | 0.54 | 46 |
| juízes: conventions | convenções (escore) | 0.76 | 46 |
| juízes: nota geral | Larastan: erros novos | -0.53 | 45 |
| convenções (escore) | hidden_ok | 0.25 | 46 |

## Convenções: quantas vezes cada regra se aplicou e foi cumprida

| regra | descrição | aplica | cumpre |
|---|---|---|---|
| C1 | test-first: production code changes ship with a test | 46 | 27 |
| C2 | Livewire validates with #[Validate] (+ $this->validate()) | 20 | 18 |
| C3 | Livewire authorizes every public action server-side | 5 | 5 |
| C4 | domain writes go through app/Actions/* | 22 | 22 |
| C5 | migrations are generated (timestamped name) and reversible (down()) | 0 | 0 |
| C6 | no service/repository layers | 22 | 22 |
| C7 | Blade escapes output ({{ }}, never {!! !!}) | 22 | 22 |
| C8 | new models declare $fillable or $guarded | 0 | 0 |
| C9 | Bulma UI, no utility-CSS classes or JS UI libraries | 22 | 22 |
| C10 | authorization through policies/gates, not manual role checks | 22 | 18 |
