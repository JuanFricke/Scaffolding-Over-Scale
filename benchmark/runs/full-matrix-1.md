# Rodada completa 1: 5 modelos × 14 tarefas × 4 níveis × 3 reps

Registro do início da primeira rodada completa do benchmark (TCC, Scaffolding Over Scale).

## Início

- **Data/hora:** 2026-10-28, 18:51:54 (horário local; `env` em UTC: 21:51:53Z)
- **Branch:** `data/full-matrix`, rebaseada no `main` após o merge do PR #4 (modelos locais)
- **Commit do código:** `8b6b685` (`feat(orchestrator): retry --no-run only requeues`)
- **Snapshot do ambiente:** `runs/env-20261028-215154.json`
  - `repo_dirty: true` vem só de `runs/manifest.jsonl`, que já tinha os registros
    `requeued` (ver "Preparação"); o código rodado é o do commit acima.
- **Log de execução:** `runs/_logs/full-matrix-1.log` (fora do git)

### Comando

```bash
cd benchmark
M=claude-sonnet-5-5,claude-haiku-5-5,opencode-go/glm-5.3-flash,opencode-go/mimo-v2.6-flash,llama/gpt-oss-20b
python -m orchestrator retry --stale-prompt --no-run --models $M   # 12 células do piloto do GLM
PF_REPO=~/Projetos/PegaFilaWeb python -m orchestrator run --models $M
```

## Preparação

- **Rebase:** a branch foi rebaseada no `main` (com o PR #4 mergeado) e a branch
  `data/full-matrix` foi criada para os dados desta rodada.
- **Opção nova `retry --no-run`:** ela só reenfileira as células. Assim as 12 células do
  piloto do GLM (T02, T06 e T10 × 4 níveis, rep 1) entram nesta mesma rodada com o
  preâmbulo atual.
  - Essas células tinham sido feitas sem o preâmbulo (`v0-statement-only`).
  - As execuções antigas continuam no disco e em `results.jsonl`, apontadas por
    `superseded_run_id`.
  - Com isso, toda a rodada usa o mesmo prompt.

## Matriz da rodada

840 células: 5 modelos × 14 tarefas × 4 níveis (none, agents, skills, full) × 3 reps,
em ordem embaralhada com seed 20261028.

| pool | modelos | runner | agentes simultâneos |
|---|---|---|---|
| anthropic | `claude-sonnet-5-5` e `claude-haiku-5-5` (effort high) | Claude Code 2.1.312 | 3 |
| opencode-go | `glm-5.3-flash` e `mimo-v2.6-flash` | OpenCode v2.2.0 | 3 |
| llama | `gpt-oss-20b` (local) | OpenCode v2.2.0 + llama-server | 1 |

- **Avaliação:** 3 slots de Docker em paralelo.
- **Ambiente dos agentes:**
  - **Sandbox:** imagem `pf-bench-agent:tcc-baseline-v1` com acesso à internet; o agente
    só vê a própria árvore de trabalho.
  - **Prompt:** um preâmbulo não interativo antes de todo enunciado.
- **Modelo local:**
  - llama.cpp build `5220213`, preset `llama/models.ini` (sha256 `14ed6537…`).
  - Configuração: contexto de 128k, 1 slot, `ngram-mod`.
  - GPU: RX 9070 16 GB.
- **Identificação da matriz:** `matrix.toml` sha256 `84cccd5b…`, seed 20261028.

## Cuidados durante a rodada

- **Duração:** dias. Os gargalos são o gpt-oss (uma célula por vez na GPU) e a lentidão do GLM.
- **Cotas:**
  - Se o OpenCode Go (plano de US$10) ou o plano do Claude bater limite, o pool pausa
    sozinho: 60 s, dobrando até 30 min. O 429 não gasta tentativa nem gera dado; a
    célula espera a janela reabrir.
- **Ambiente:**
  - O `llama-server` (`orchestrator/llama/serve.sh`) precisa continuar no ar.
  - A regra do `ufw` para docker0:8089 precisa continuar ativa.
  - O PC não pode suspender.
- **Disco:**
  - A rodada deve gerar ~60 GB de árvores em `benchmark/work`.
  - Em 2026-10-28 havia 356 GB livres e 20 GB já usados pelas rodadas anteriores.
- **Retomada:**
  - Se o processo cair, rodar de novo o mesmo `run --models ...`: ele retoma sem duplicar células.
  - Falhas de infraestrutura que esgotarem as tentativas: `retry --failed-infra --models $M`.
- **Acompanhamento:** `python -m orchestrator status --models $M`.

## Incidentes

- **18:56, falso positivo de contaminação** (`claude-sonnet-5-5__T03a-auth-core__full__r3`): o
  agente usou `../../laravel/framework` dentro de `vendor/`. O detector foi corrigido (`0b5a1ea`):
  no Docker, `../..` não conta. `status` e `report` recalculam o veredito a partir dos hits
  gravados, então o run voltou para os dados.
- **18:53 e 18:57, saída malformada do gpt-oss** (erro 500 do llama-server, *"does not match the
  expected peg-native format"*): decisão de tratar como `fail` do modelo (`5606783`).
  - O processo foi parado às ~19:00. Os 7 agentes em andamento foram mortos e recomeçaram como
    nova tentativa.
  - As 2 tentativas afetadas (T01 e T04b, none, r3, a1) foram registradas como `fail`, com o
    campo `reclassified`, e avaliadas: T01 passou, T04b não.
  - Reinício às 19:01; log em `runs/_logs/full-matrix-2.log`.
- **19:10, falha de avaliação mal classificada** (`llama-gpt-oss-20b__T03b-mail-theme__none__r3__a2`):
  o código do agente quebrava o `artisan` no fim do `composer install`.
  - A regra foi corrigida e a célula foi reavaliada na mesma árvore com `regrade` (`hidden_ok=False`).
  - O processo em andamento ainda usa a regra antiga: rodar `regrade --models $M` ao final.

## Ao terminar

1. `python -m orchestrator regrade --models $M` (falhas de avaliação da regra antiga), depois
   `python -m orchestrator status --models $M`: nenhuma célula pendente ou `failed_infra`.
2. `python -m orchestrator report`: gera `runs/report.csv` e `runs/report.md`.
3. Commit de `runs/manifest.jsonl`, `runs/results.jsonl`, `runs/env-*.json` e do relatório
   na branch `data/full-matrix`.
4. Registrar aqui a data de término e qualquer incidente (pausas longas, `failed_infra`,
   contaminação).
