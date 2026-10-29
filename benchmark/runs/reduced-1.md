# Rodada reduzida 1: 6 modelos × 14 tarefas × 4 níveis × 1 rep (Qwen retirado às 01:52)

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

## Execução

- **Início:** 2026-10-29 00:19. Log em `runs/_logs/reduced-1-20261029-001939.log`; verificações
  de hora em hora em `runs/_logs/reduced-1-checks.md`.
- **00:23, deepseek-v4.1-flash validado:** 1ª célula (T01 skills) em 183 s, 25 turnos, modelo
  certo, `hidden_ok=True`.

## Incidentes

- **00:37, falso positivo de contaminação** (`opencode-go-beam-free__T06-issue-ticket__skills__r1`):
  o agente editou o `CHANGELOG.md` via `php -r`, e o texto tinha o link
  `https://github.com/PegaFila/PegaFilaWeb/pull/25`.
  - **Detector:** links `github.com/PegaFila/PegaFilaWeb` deixaram de contar.
  - **Bug em `suspected()`:** o veredito recalculado usava os hits gravados no manifesto, que
    são cortados em 300 caracteres. Agora ele lê o log bruto completo do agente e só usa os
    hits gravados se o log não existir.
  - **Resultado:** os 2 runs marcados até aqui são falsos positivos e voltaram para os dados.
    Nenhum run passou a ser marcado com a checagem completa.
  - **Sem reinício:** o processo em andamento ainda marca com o detector antigo, mas `status` e
    `report` usam o novo.

- **00:56, mesmo link do `CHANGELOG`, com barras escapadas** (`github.com\/PegaFila\/PegaFilaWeb`,
  beam-free T02 agents). Agora os locais são normalizados (`\/` → `/`) antes de comparar.
- **00:44, tentativa de buscar o repositório real** (`opencode-go-deepseek-v4.1-flash__T03a-auth-core__none__r1`):
  o agente usou `webfetch` em
  `https://raw.githubusercontent.com/PegaFila/PegaFilaWeb/main/app/Livewire/Auth/Login.php`.
  - **Sem vazamento:** a ferramenta retornou erro. O repositório é privado (`private: true` na
    API do GitHub), a URL responde 404 sem autenticação e o sandbox não tem credencial do GitHub.
  - **Decisão:** URLs do GitHub do PegaFilaWeb não contam como contaminação, porque não podem
    vazar nada.
  - **Contagem à parte:** as tentativas entram como `fetch_attempts` (`adapters.fetch_attempts`)
    e aparecem no relatório final como comportamento observado.

- **02:54, 2ª tentativa de acessar o repositório real** (`opencode-go-deepseek-v4.1-flash__T04b-tenant-onboarding__none__r1`):
  - O agente rodou `curl -s -I https://api.github.com/repos/PegaFila/PegaFilaWeb` e recebeu
    HTTP 404: sem vazamento.
  - O padrão não cobria `api.github.com/repos/`. Agora qualquer URL do GitHub do repositório
    (`SUBJECT_URL`) é removida antes da checagem de caminhos e contada em `fetch_attempts`.
  - Até aqui: 2 tentativas, ambas do deepseek, ambas no nível `none`.
- **01:24, container morto por falta de memória** (`claude-sonnet-5-5__T08-queue-management__none__r1__a3`,
  `exit 137`):
  - O `systemd-oomd` do host matou o container, que tinha chegado a 23 GB de swap, com o
    host acima de 90% de RAM e swap.
  - O run virou `infra` e foi refeito (a5).
  - **Correção:** limite de memória por container de agente (`--memory 6g --memory-swap 6g`,
    `BENCH_AGENT_MEMORY`). Um processo descontrolado morre dentro do próprio sandbox, sem
    derrubar o host nem os outros runs.
- **01:52, Qwen fora da rodada:**
  - Medido: ~23 min por célula. O Qwen é verboso (100–150 turnos e ~60 mil tokens de saída por
    tarefa, contra 6–9 mil do gpt-oss) e gera a ~42 tok/s.
  - Com a GPU rodando uma célula por vez, as 53 células restantes levariam ~20 h, contra 1,5–3 h
    dos outros pools.
  - Fica para uma rodada própria. As 3 células dele já feitas ficam no manifesto (T10 agents
    ok, T03b skills timeout, T07 skills ok).
  - O processo foi reiniciado às 01:52 sem o Qwen e de novo às 01:53 para aplicar o limite de
    memória. Os agentes em andamento recomeçaram nas duas vezes.
  - Logs: `runs/_logs/reduced-1-20261029-015234.log` e `...-015335.log`.
- **02:35, beam-free fora do ar** (provedor, não modelo):
  - Os 6 timeouts do beam-free eram travamentos do endpoint.
    - 3 runs pararam de receber eventos no mesmo minuto (01:12).
    - 3 nunca receberam resposta (02:08).
    - Todos ficaram 10–15 min mudos até o timeout de 30 min.
  - **Confirmação:** às 02:35 um "pong" ao beam-free ficou 90 s sem resposta; o Muse respondeu
    em 4 s.
  - Contados como timeout do modelo, esses runs puxariam o beam-free para baixo: sem eles, ele
    estava 23/23.
  - **Correção:** watchdog de silêncio (`STALL_S` = 480 s, `BENCH_STALL_S`). Um agente sem
    nenhum evento por 8 min é morto e tratado como 429: o pool pausa (60 s → 30 min), a célula
    é refeita sem gastar tentativa e nunca vira dado.
  - Os 6 timeouts foram reenfileirados com `retry --cells` e a razão gravada no manifesto.
  - O processo foi reiniciado às 02:38 (log `...-023852.log`); os agentes em andamento recomeçaram.
  - O timeout do deepseek no T05 none (02:26) é legítimo: o agente trabalhou até o fim.
- **03:22, OpenCode saiu com `exit 1` depois de o agente terminar**
  (`opencode-go-deepseek-v4.1-flash__T09-queue-management-ui__none__r1__a4`):
  - O último evento é o resumo final do agente e o stderr está vazio, então é uma falha do CLI
    no encerramento.
  - Pela regra, crash desconhecido do CLI conta como `infra`, e a célula foi refeita (a5).
  - A decisão de descartar não dependeu do resultado (o run não foi avaliado), então não
    enviesa o pass@1.
- **03:35, beam-free ainda fora:**
  - 12 travamentos detectados pelo watchdog desde 02:38, todos do beam-free; nenhum de outro
    modelo.
  - Pausas do pool: 68 s → 120 s → 261 s → 518 s.
  - Um "pong" direto ficou 60 s sem resposta.
- **04:17, erro passageiro do provedor no Muse** (`provider.rate-limit`, "The model failed to
  generate a response"): o pool `opencode-go` pausou 70 s e a célula foi refeita sem gastar
  tentativa. Às 04:20, Muse e deepseek respondiam normalmente.
- **04:35, estado dos pools:**
  - Concluídos: Claude (Sonnet 56/56, Haiku 56/56) e gpt-oss (56/56).
  - Faltam 21 células do Muse e do deepseek.
  - beam-free ainda fora: segue no catálogo (`opencode models`), mas um "pong" não responde em
    60 s; 18 travamentos detectados desde 02:38; 33 células pendentes.
- **Desenho final desta rodada:** 6 modelos, 336 células.

## Ao terminar

1. Rodar `python -m orchestrator regrade --models $M --reps 1` e depois
   `python -m orchestrator status --models $M --reps 1`: nenhuma célula pendente ou `failed_infra`.
2. `python -m orchestrator report`.
3. Commit de `runs/manifest.jsonl`, `runs/results.jsonl`, `runs/env-*.json`, do relatório e da
   data de término e incidentes neste arquivo.
