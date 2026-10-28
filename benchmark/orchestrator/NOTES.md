# Orchestrator — notas de verificação (seção 3 do plano)

Verificado em 2026-10-28 lendo `bin/*.sh`, `harness/v1/`, `PF_REPO` (`bin/pf`,
`docker/compose.dev.yml`) e o `--help` local dos CLIs. Host: CachyOS, Python 3.14,
OpenCode v2.2.0, Claude Code 2.1.312. **Docker não estava instalado** no momento.

## prepare-task.sh

- stdout é texto livre; a primeira linha é `prepared  <OUT>`. Não é preciso
  analisá-la: o script aceita `--out <dir>`, então **o orquestrador escolhe o
  caminho** (`work/<cell_id>__a<tentativa>`), o que já garante unicidade mesmo no
  mesmo segundo. Prompt = `<OUT>.prompt.md`, meta = `<OUT>.meta` (formato `k=v`:
  task, level, base_commit, harness, status, parent_task, created).
- A árvore é um repo git novo com 2 commits (`base …`, `harness: <level>`) e a tag
  `bench/start`. Contém `bin/pf`, `docker/`, `.env.example`, sem `vendor/` nem
  `node_modules/`.
- Não usa Docker nem rede; só `git archive|show` no `PF_REPO`. Seguro em paralelo
  (cada chamada escreve só no próprio `--out`).

## evaluate.sh

- `--run-id <id>` é aceito; default `<task>__<level>__<ts>` (colide no mesmo
  segundo). **O orquestrador sempre passa `--run-id`** (= `cell_id` + tentativa).
- Campos gravados: run_id, task, level, harness, base_commit, solution_commit,
  agent, model, image, started, finished, diff{files,insertions,deletions,commits},
  violations{tests_touched,harness_touched,unescaped_output_added},
  hidden_test_collisions, assets, composer{mode,json_changed,exit}, pint,
  tests_full, tests_hidden{passed,failed,exit,ok}, regressions, agent_metrics.
  **Não grava `rep` nem `cell_id`**: o manifesto guarda; além disso o
  orquestrador os coloca dentro do JSON de `--agent-metrics`, que é embutido verbatim.
- A linha vai para `runs/<run-id>/result.json` e é anexada com
  `printf '%s\n' "$LINE" >> results.jsonl`. É um `printf` builtin em modo append;
  com linhas de alguns KB não há garantia de um único `write(2)`. **Patch mínimo
  proposto:** envolver esse append em `flock` (o `flock(1)` existe no host).
- Docker: `docker run --rm` sem `--name`, sem portas publicadas, rede bridge
  padrão → sem colisão de nomes/portas entre avaliações paralelas. Ressalva:
  `timeout` mata o cliente `docker`, não o contêiner; num timeout o contêiner pode
  ficar vivo. O orquestrador pode limpar por label/nome se necessário (patch
  adicional, só se aparecer na prática).
- Cache: `BENCH_CACHE` é fixo em `lib.sh` (`benchmark/.cache`), montado em `/cache`
  e usado por composer e npm. O cache do npm (cacache) é feito para concorrência;
  o do composer não garante escrita concorrente segura. **Patch mínimo proposto:**
  `BENCH_CACHE="${BENCH_CACHE:-$BENCH_DIR/.cache}"` em `lib.sh`, e o orquestrador
  usa `.cache/slot-<n>` por slot de GRADE.
- Avaliar exige a imagem `pf-bench:tcc-baseline-v1` (`build-image.sh`) e acesso
  à rede (Packagist/npm).
- Efeito colateral: `git add -A` na árvore (o stage muda). Reavaliar a mesma árvore
  é seguro (os testes ocultos sobrescrevem os mesmos caminhos), o que permite o
  retry de `grade_error` sem rodar o agente de novo.

## bin/pf e docker/ na árvore

- `compose_dev` chama `docker compose -f docker/compose.dev.yml` **sem `-p`** →
  o nome do projeto vira `docker` (nome da pasta) em **todas** as árvores, e o
  compose publica portas fixas `8080` e `5173`, mais mariadb. Dois agentes
  rodando `./bin/pf up` ao mesmo tempo colidem (mesmo projeto e mesmas portas).
  `COMPOSE_PROJECT_NAME` por run resolve o nome, mas **não as portas**.
- `bin/pf` também tem `deploy`/`smoke`/`doctor` com API da Hostinger; sem `.env`
  com token, falha. Mesmo assim, é mais um motivo para o agente não ter Docker
  do host.

## CLIs dos runners (do `--help` local)

- **OpenCode** `opencode run [msg]`: `-m provider/model`, `--format json`
  (eventos), `--auto` (auto-aprova permissões não negadas), `--agent`,
  `--title`, `--standalone` (servidor privado em vez do serviço de fundo
  compartilhado — **necessário em paralelo**). Sem flag de temperatura.
  Os 4 modelos da matriz existem em `opencode models` hoje, e
  `opencode-go/claude-haiku-5-5` também.
- **Claude Code** `claude -p`: `--model`, `--output-format json|stream-json`
  (+ `--verbose` para stream), `--permission-mode`, `--dangerously-skip-permissions`,
  `--allowed-tools`, `--setting-sources`, `--settings`, `--no-session-persistence`,
  `--strict-mcp-config`, `--bare`. Sem flag de temperatura.
- **Armadilha do nível `full`:** `harness/v1/opencode.json` define
  `"model": "opencode-go/muse-spark-1.3-contributor"` (e `small_model`). Se o
  `-m` não sobrescrever os dois (o `small_model` é usado em títulos/resumos), o
  código privado vai para um modelo que treina com os dados. O adaptador vai
  verificar nos eventos JSON que só o modelo pedido aparece; se aparecer outro,
  o run é abortado como `infra` e marcado.
- Isolamento de config de usuário: para o Claude Code, usar
  `--setting-sources project` (só `.claude/settings.json` da árvore, que só
  existe no `full`) e `--strict-mcp-config` para não carregar MCPs do usuário.
  O OpenCode lê `~/.config/opencode` (hoje só `service.json`) e guarda estado em
  `~/.local/share/opencode`; com sandbox, usar um `XDG_*` por run.

## Métricas

- OpenCode `--format json`: eventos por mensagem com `tokens{input,output,reasoning,cache}`
  e custo → somar; turnos = número de mensagens do assistente. A verificar no
  piloto (o formato exato muda entre versões, registrar a versão).
- Claude Code `--output-format json`: objeto final com `usage`, `num_turns`,
  `duration_ms`, `total_cost_usd`.
- Tempo de parede medido pelo próprio orquestrador nos dois casos.

## Isolamento de sistema de arquivos — **o risco existe, e é maior que o previsto**

Testado: a partir de `benchmark/work/<run>/`, `../../../../PegaFilaWeb` é legível.
Pior ainda, a árvore fica **dentro** do repositório do benchmark, então o agente
alcança com `../../`:

- `benchmark/tasks/*.yaml` → `solution_files`, `notes` e `solution_commit`;
- `benchmark/runs/*/agent.patch` → patches de outros runs (inclusive do oráculo);
- `benchmark/work/*` → árvores de outros runs em andamento;
- `<tree>.meta` ao lado.

Com shell e permissões auto-aprovadas (`--auto` / `--dangerously-skip-permissions`),
nada impede a leitura. Conclusão: **o sandbox Docker com só a árvore montada é
necessário**, não opcional. Até ele existir, no mínimo: árvores fora do repo
(`--out` num diretório irmão sem nada mais), e o detector de contaminação
procurando `PegaFilaWeb`, `benchmark/tasks`, `benchmark/runs`, `.meta`, `..`.

## Decisões (respostas do Juan, 2026-10-28)

1. **Testes no sandbox:** sim. Imagem derivada de `pf-bench` com PHP + composer;
   um shim fora da árvore faz `bin/pf shell <cmd>` → `<cmd>`.
2. **Rede no sandbox:** acesso completo à internet.
3. **Modelos Anthropic só no Claude Code** (nunca via `opencode-go/claude-*`).
4. Commits com `Juan Paulo Fricke <juanpfricke@hotmail.com>`.
5. `results.jsonl` e `manifest.jsonl` versionados (artefato do TCC).
6. Vazamento para o Muse Spark é irrelevante (o código-sujeito foi escrito com
   ele). `trains_on_data` fica no `matrix.toml` como informação, e o Muse é
   liberado sem `--allow-training-models`. A checagem de "modelo usado == modelo
   pedido" continua, mas por **validade** do dado, não por privacidade.

## Achados durante a implementação

- **Bug em `evaluate.sh` (corrigido):** `count_in` roda sob `set -euo pipefail`; quando o
  resumo do Pest não tinha "N failed" (tudo verde) ou "N passed" (tudo vermelho), o `grep`
  sem match abortava o script sem mensagem, antes de gravar a linha. Isso acontecia em
  **todo** run do oráculo e do agente nulo. Patch: `|| true` na função.
- **Linha de base da suíte completa:** em todas as tarefas testadas, `PfControllerTest`
  falha 2 testes porque `.github/` é `export-ignore` e não vai para a árvore. Logo
  `regressions` tem piso 2 (não é culpa do agente). Para a análise, usar
  `regressions - regressions(null)` por tarefa, ou olhar só `tests_hidden`.
  Quando nada passa, `tests_hidden.passed` vem `null` (não 0); o CSV mantém como está.
- **Claude Code no nível `full`:** `.claude/settings.json` habilita
  `php-lsp@claude-plugins-official`, mas o plugin só carrega se estiver instalado no HOME.
  O adaptador registra o marketplace (montado só-leitura do host) e instala o plugin no
  HOME de **todo** run (ambiente idêntico entre níveis); só carrega onde a árvore o
  habilita, porque `--setting-sources project` ignora as configurações de usuário.
  Verificado: `full` → ferramenta `LSP` presente; árvore sem settings → ausente. As
  métricas gravam `plugins` e `lsp_tool` por run.
- **OpenCode no nível `full`:** `opencode.json` pede `intelephense` (instalado no sandbox,
  1.18.5) e `laravel-lsp` (**não existe** no sandbox nem no host; o harness original usa
  um wrapper + `.phar` local). Esse LSP falha silenciosamente nos runs do OpenCode.
  O `small_model` (Muse) não aparece no export da sessão, então não dá para verificar
  pelo log; ver decisão 6.
- **Credenciais do OpenCode:** não ficam em arquivo no host (`auth list` mostra "stored");
  o adaptador usa `opencode auth export` → arquivo no HOME temporário do run →
  `auth import` dentro do sandbox → arquivo apagado. O HOME temporário fica em `/tmp`,
  nunca no repositório, e é removido ao fim do run.
- **Métricas do OpenCode:** o stream `--format json` pode terminar antes do último
  `step_finish`; os totais vêm de `opencode session export <id>` (tokens, custo, modelo de
  cada mensagem do assistente), salvo em `runs/<run_id>/agent.session.json`.
- O orquestrador remove variáveis `CLAUDE_CODE_*` do ambiente do runner (se ele for
  disparado de dentro de uma sessão do Claude Code, o filho herdaria a sessão).

## laravel-lsp (decisão 7, 2026-10-28)

Instalado no sandbox: `laravel/lsp` v0.0.31 (a versão do commit `c8dd1b7` do repo-sujeito),
PHAR de `builds/laravel-lsp` com sha256 fixado, extraído e rodado com o PHP 8.4 local (o
wrapper original usava o contêiner `php:8.4-cli`). Responde a `initialize` por stdio.
Os runs do piloto `T02 full` e `T06 full` começaram antes do rebuild (sem laravel-lsp) e
foram reenfileirados com `retry --cells`; o run antigo fica referenciado como
`superseded_run_id`. Desde então cada run grava `sandbox_image_id`.

## Preâmbulo "trabalhe sem perguntar" (decisão 8, 2026-10-28)

No mini piloto, o Haiku 4.5 respondeu ao T10 `agents` pedindo esclarecimento e parou
(1 turno): no modo headless ninguém responde. O enunciado (`tasks/*.yaml`) não pode mudar,
então o orquestrador põe o texto fixo de `orchestrator/prompt-preamble.md` antes de todo
enunciado, em **todos** os runs (todos os modelos e níveis; aplicar só a alguns modelos
criaria diferença de condição entre eles). O texto não fala de testes, harness nem
ferramentas. Cada run grava `prompt_version` (hash do preâmbulo) e `runs/<run_id>/prompt.sent.md`.
Runs anteriores aparecem como `v0-statement-only`; `retry --stale-prompt` os refaz.

## Estado em 2026-10-28 (fim da sessão)

**Pronto e validado**
- Orquestrador (`plan`/`run`/`pilot`/`status`/`retry`/`report`/`env`/`reparse`), sandbox do
  agente (só a árvore montada, `bin/pf` via shim, intelephense + laravel-lsp), adaptadores
  OpenCode e Claude Code, 429 sem gastar tentativas, preâmbulo não interativo.
- Aceites: oráculo 14/14, nulo 0/14, sequencial = paralelo, retomada sem duplicar, 429 pausa
  o pool, `plan`/`--dry-run` sem Docker/rede; 8 testes em `orchestrator/tests/`.
- Matriz: 9 modelos, 1428 células (5 OpenCode Go incl. beam-free; Claude Code: haiku-5-5 e
  sonnet-5-5 em effort high, haiku-4-5, opus-5-5 medium só none/full).

**Dados (rep 1, prompt `v0-statement-only`, sem preâmbulo)**
- Muse Spark 1.3: 12/12 (teto). GLM 5.3 flash: 11/12. Haiku 4.5: 6/12 (o único abaixo do
  teto; falha em T06 skills/full e T10 em todos os níveis). Tarefas: T02, T06, T10.
- n = 1 por célula: nenhuma conclusão sobre o efeito do harness ainda.

**Próximos passos**
1. `retry --stale-prompt` nas 36 células dos pilotos (refazer com o preâmbulo).
2. Antes de rodar a matriz, conferir no painel do opencode.ai o consumo da cota do Go
   (estimativa: matriz ≈ 50% da cota mensal; GLM ≈ 2/3 disso) e considerar
   `CLAUDE_CODE_OAUTH_TOKEN` dedicado (`claude setup-token`) para runs longos.
3. 1ª passada: `run --reps 1`, depois reps 2 e 3.
4. `benchmark/work/` guarda todas as árvores (≈20 GB após ~300 runs; ignorado pelo git):
   limpar árvores de células `done` ou mover `work_dir` para um disco maior antes da matriz.
