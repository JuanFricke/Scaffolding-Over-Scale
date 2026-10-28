# Rodada reduzida 1: 7 modelos × 14 tarefas × 4 níveis × 1 rep

Substitui a rodada completa 1 (`full-matrix-1.md`), cancelada em 2026-10-28 às 19:40 porque
levaria ~30 h ou mais. O objetivo desta é terminar em ≤ 12 h.

## Desenho

- **Repetições: 1** (eram 3).
  - Cada modelo ainda compara os 4 níveis nas mesmas 14 tarefas: 14 pares por comparação
    entre níveis.
  - A variação entre tarefas tende a ser maior que entre execuções da mesma tarefa, então as
    tarefas funcionam como repetição.
  - O que se perde é a estimativa da variação de um mesmo modelo na mesma célula.
  - Reps 2 e 3 podem ser acrescentadas depois como células novas, sem refazer nada.
- **Modelos: 7, 392 células** (56 por modelo):

  | pool | modelos | concorrência |
  |---|---|---|
  | anthropic | `claude-sonnet-5-5`, `claude-haiku-5-5` (effort high) | 3 |
  | opencode-go | `muse-spark-1.3-contributor`, `deepseek-v4.1-flash` | 3 |
  | opencode-go-free | `beam-free` | 3 |
  | llama | `gpt-oss-20b`, `qwen3.6-35b-a3b` (locais) | 1 |

- **Por que estes do OpenCode Go:** são os 3 com mais tokens por segundo, medidos em
  2026-10-28. O GLM e o mimo saíram por lentidão: eram o gargalo da rodada completa.

  | modelo | isolado (tok/s) | agentic, mediana (tok/s) |
  |---|---|---|
  | muse-spark-1.3-contributor | 376 | 102 |
  | beam-free | 339 | 197 |
  | deepseek-v4.1-flash | 280 | – (sem runs) |
  | glm-5.3-flash | 93 | 75 |
  | mimo-v2.6-flash | 75 | 45 |

  - **Isolado:** o mesmo prompt de ~1k tokens de código, sem ferramentas.
  - **Agentic:** respostas ≥ 300 tokens de todos os runs gravados.
  - Os dois valores incluem o tempo até o primeiro token.

## Estimativa

~7–8 h. Os pools rodam em paralelo; os gargalos são o anthropic (~11 min/célula × 112 ÷ 3)
e o llama (gpt-oss ~2,5 min + Qwen ~5 min por célula, uma de cada vez).

## Como rodar

```bash
~/Projetos/Scaffolding-Over-Scale/benchmark/runs/reduced-1.sh
```

O script:
- sobe o `llama-server` se ele não estiver no ar;
- reenfileira as 12 células do piloto do Muse, feitas sem o preâmbulo;
- dispara o `run` desacoplado do terminal, com log em `runs/_logs/reduced-1-*.log`.

Rodar de novo retoma de onde parou.

## O que veio da rodada completa 1

- **Reaproveitadas:** as células de rep 1 já `done` desses modelos (Sonnet 2, Haiku 5.5 3,
  gpt-oss 4) continuam valendo.
- **Fora da análise principal:**
  - As células de rep 2 e 3 já feitas (Sonnet, Haiku 5.5, gpt-oss) ficam no manifesto como
    amostra extra de variação entre execuções.
  - As células de GLM e mimo também ficam no manifesto, sem uso.
- **Reavaliações:** 3 `failed_infra` do gpt-oss, causados pela regra antiga do composer, foram
  reavaliados com `regrade` antes do cancelamento: os 3 deram `hidden_ok=False`.

## Ao terminar

1. Rodar `python -m orchestrator regrade --models $M --reps 1` e depois
   `python -m orchestrator status --models $M --reps 1`: nenhuma célula pendente ou `failed_infra`.
2. `python -m orchestrator report`.
3. Commit de `runs/manifest.jsonl`, `runs/results.jsonl`, `runs/env-*.json`, do relatório e da
   data de término e incidentes neste arquivo.
