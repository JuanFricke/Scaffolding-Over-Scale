# Rodada reduzida 1: relatório

**Benchmark Scaffolding Over Scale (TCC, UNIJUÍ)**
- **Execução:** 2026-10-29, de 00:19 a 05:30.
- **Desenho:** 6 modelos × 14 tarefas × 4 níveis de harness × 1 repetição.
- **Branch:** `data/full-matrix`.

As tabelas completas são geradas por `runs/reduced-1-analysis.py`, com saída em
`runs/_logs/reduced-1-tables.md`. Os dados brutos estão em `runs/manifest.jsonl` e
`runs/results.jsonl`, e há uma linha por run em `runs/report.csv`.

## 1. Resumo

- **Teto:** 4 dos 6 modelos resolveram ≥ 95% das tarefas já sem harness (nível `none`).
  - Sonnet 5.5: 55/56.
  - DeepSeek v4.1 flash: 56/56.
  - Muse Spark 1.3: 53/56.
  - Beam: 23/23 nas células que rodaram.
  - Com o teto tão perto, não sobra espaço para o harness melhorar o pass@1.
- **Efeito do harness sobre o pass@1:** nenhum nível (`agents`, `skills`, `full`) mudou o
  pass@1 de forma detectável em nenhum modelo.
  - Em 73 pares modelo × tarefa por nível, as discordâncias com o `none` foram 0–1 para cada
    lado.
  - Δ agregado: agents −1,4 pp, skills 0,0 pp, full −1,4 pp. McNemar exato p = 1,0 em todos.
- **Os dois modelos abaixo do teto não reagiram ao harness:**
  - **Haiku 5.5:** 11/14 em todos os níveis. Falhou sempre nas mesmas 3 tarefas e pelo mesmo
    teste (ver §5.2).
  - **gpt-oss-20b (local):** 6/56 (1–2 de 14 por nível).
- **O harness aumenta o custo.** Em relação ao `none`, as medianas por run sobem:
  - **Sonnet:** turnos +44–67%, tokens de entrada +50–66%, tempo do agente +32–48%.
  - **Haiku:** turnos +13–19%, tokens de entrada +43–71%, tempo do agente +37–53%.
  - **DeepSeek:** tokens de entrada +17–62%.
  - **Muse:** tokens de entrada +5–21%.
- **Contaminação: nenhuma.** Os sinais do detector foram todos falsos positivos, corrigidos
  durante a rodada.
  - O DeepSeek tentou 3 vezes buscar o repositório real no GitHub, sempre no nível `none`.
  - O repositório é privado e todas as tentativas falharam (404), então nada vazou.

Leitura para o TCC: nesta amostra, **escala (escolha do modelo) explica quase toda a variação
de pass@1**. Entre modelos, o pass@1 vai de 11% a 100%; entre níveis, para um mesmo modelo,
a variação é ≤ 7 pp. O harness v1 não melhorou a taxa de resolução e encareceu cada run. Com
1 repetição e efeito de teto, porém, o desenho só detectaria efeitos grandes (§7).

## 2. Desenho

| fator | valores |
|---|---|
| Tarefas | 14 (`benchmark/tasks/*.yaml`, `status: ready`), avaliadas por testes ocultos |
| Níveis de harness | ver abaixo; cumulativos, snapshot `harness/v1` |
| Repetições | 1 (rep 1). O plano original tinha 3; a redução foi feita por tempo (decisão 11 em `NOTES.md`) |
| Ordem | células embaralhadas com seed 20261028 |
| Prompt | preâmbulo não interativo (`prompt-preamble.md`, versão `pre-218e85fd81c1`) seguido do enunciado sem alterações |
| Timeout do agente | 30 min (`agent_timeout_s` = 1800). Timeout conta como dado; o código é avaliado como ficou |
| Isolamento | sandbox Docker `pf-bench-agent:tcc-baseline-v1`; só a árvore da tarefa montada em `/workspace`; internet liberada; limite de 6 GB de RAM por container (desde 01:53) |
| Avaliação | `bin/evaluate.sh` no container `pf-bench:tcc-baseline-v1`: `composer install`, testes ocultos, suíte completa, Pint |

Níveis de harness:
- **`none`:** nenhum artefato de harness.
- **`agents`:** `AGENTS.md` e `CLAUDE.md`.
- **`skills`:** `agents` mais `ai/` (skills, commands, rules, templates).
- **`full`:** `skills` mais `opencode.json` e `.claude/settings.json` (instruções e LSP:
  intelephense, laravel-lsp, php-lsp).

### Modelos e parâmetros

| modelo | runner | parâmetros | concorrência |
|---|---|---|---|
| `claude-sonnet-5-5` | Claude Code 2.1.312 | `--effort high`; login por assinatura | pool anthropic, 3 |
| `claude-haiku-5-5` | Claude Code 2.1.312 | `--effort high` | pool anthropic, 3 |
| `opencode-go/muse-spark-1.3-contributor` | OpenCode v2.2.0 | padrão do provedor | pool opencode-go, 3 |
| `opencode-go/deepseek-v4.1-flash` | OpenCode v2.2.0 | padrão do provedor | pool opencode-go, 3 |
| `opencode-go/beam-free` | OpenCode v2.2.0 | padrão do provedor (gratuito) | pool opencode-go-free, 3 |
| `llama/gpt-oss-20b` (MXFP4, local) | OpenCode v2.2.0 + llama.cpp `5220213` | contexto 128k, 1 slot, KV f16, `ngram-mod`, temp 1.0, top-p 1.0, reasoning medium (preset sha256 `14ed6537…`) | pool llama, 1 (RX 9070 16 GB) |

- **Modelo usado:** cada run conferiu, pelas mensagens da sessão, que só o modelo sob teste
  respondeu. Nenhuma divergência.
- **Ambiente:** versões de imagens, SHAs e ferramentas estão nos snapshots `runs/env-2026102[89]-*.json`.

### Métricas

- **pass@1:** a célula passa quando *todos* os testes ocultos passam.
- **Fração de testes ocultos aprovados:** métrica contínua.
- **Regressões:** testes que falham fora dos ocultos, além dos que já falham na árvore
  intocada. A linha de base é a do agente nulo, por tarefa: 1–2 falhas, quase todas do
  `PfControllerTest`.
- **Custo:** turnos, tokens (entrada inclui leitura de cache) e tempo de parede do agente.

## 3. pass@1 por modelo × nível

IC 95% de Wilson entre colchetes.

| modelo | none | agents | skills | full | total |
|---|---|---|---|---|---|
| Sonnet 5.5 | 14/14 [0.78, 1.00] | 14/14 [0.78, 1.00] | 14/14 [0.78, 1.00] | 13/14 [0.69, 0.99] | 55/56 (0.98) |
| DeepSeek v4.1 flash | 14/14 [0.78, 1.00] | 14/14 [0.78, 1.00] | 14/14 [0.78, 1.00] | 14/14 [0.78, 1.00] | 56/56 (1.00) |
| Muse Spark 1.3 | 13/14 [0.69, 0.99] | 13/14 [0.69, 0.99] | 14/14 [0.78, 1.00] | 13/14 [0.69, 0.99] | 53/56 (0.95) |
| Haiku 5.5 | 11/14 [0.52, 0.92] | 11/14 [0.52, 0.92] | 11/14 [0.52, 0.92] | 11/14 [0.52, 0.92] | 44/56 (0.79) |
| gpt-oss-20b | 2/14 [0.04, 0.40] | 1/14 [0.01, 0.31] | 1/14 [0.01, 0.31] | 2/14 [0.04, 0.40] | 6/56 (0.11) |
| Beam (free)¹ | 8/8 | 6/6 | 4/4 | 5/5 | 23/23 (1.00) |

¹ **Beam incompleto (23/56):** o provedor ficou fora do ar das 01:12 até pelo menos 05:30 (§6).
As células concluídas não são uma amostra aleatória das tarefas, então o Beam fica fora das
comparações entre níveis.

**Fração média de testes ocultos aprovados:**

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet, DeepSeek, Muse, Beam | ≥ 0,998 | ≥ 0,998 | ≥ 0,998 | ≥ 0,998 |
| Haiku 5.5 | 0,993 | 0,993 | 0,993 | 0,993 |
| gpt-oss-20b | 0,250 | 0,244 | 0,203 | 0,203 |

- **Modelos fortes:** mesmo quando falham, falham por 1 teste.
- **gpt-oss:** passa em média ~¼ dos testes ocultos. A métrica contínua indica uma piora leve
  com `skills` e `full`, mas sem significância com n = 14.

## 4. Efeito de cada nível vs `none` (pareado por tarefa)

As colunas *+* e *−* contam as tarefas em que só um lado passou: *+* = só o nível passou,
*−* = só o `none` passou.

| modelo | agents (+/−) | skills (+/−) | full (+/−) |
|---|---|---|---|
| Sonnet 5.5 | 0/0 | 0/0 | 0/1 (T05) |
| DeepSeek v4.1 flash | 0/0 | 0/0 | 0/0 |
| Muse Spark 1.3 | 0/0 | 1/0 (T05) | 0/0 |
| Haiku 5.5 | 0/0 | 0/0 | 0/0 |
| gpt-oss-20b | 0/1 (T07) | 0/1 (T07) | 0/0 |
| **Agregado** (73 pares/nível) | **0/1**, Δ −1,4 pp, p = 1,0 | **1/1**, Δ 0,0 pp, p = 1,0 | **0/1**, Δ −1,4 pp, p = 1,0 (72 pares) |

Em 5 modelos × 3 níveis houve só 4 discordâncias, nas duas direções. Sem efeito detectável.

Grade tarefa × nível (✓/✗ na ordem none · agents · skills · full):

| tarefa | Sonnet | Haiku | Muse | DeepSeek | gpt-oss |
|---|---|---|---|---|---|
| T01 discord-ops-alert | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T02 discord-mention-id | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ |
| T03a auth-core | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T03b mail-theme | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T04a entity-model | ✓✓✓✓ | ✗✗✗✗ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T04b tenant-onboarding | ✓✓✓✓ | ✗✗✗✗ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T04c entity-management | ✓✓✓✓ | ✗✗✗✗ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T05 entity-invites | ✓✓✓✗ | ✓✓✓✓ | ✗✗✓✗ | ✓✓✓✓ | ✗✗✗✗ |
| T06 issue-ticket | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T07 call-next-ticket | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✗✗✓ |
| T08 queue-management | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T09 queue-management-ui | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T10 totem-bff | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |
| T11 priority-ticket-prefix | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✗✗✗✗ |

O padrão é dominado pelo modelo e pela tarefa, não pelo nível. As falhas se repetem na mesma
tarefa em todos os níveis (Haiku em T04*, Muse em T05).

## 5. Custo e comportamento

### 5.1 Custo por run (medianas)

| modelo | nível | turnos | tokens de saída | tokens de entrada | tempo do agente (min) |
|---|---|---|---|---|---|
| Sonnet 5.5 | none | 18 | 22 502 | 905 810 | 3,1 |
| | agents | 30 | 30 112 | 1 468 970 | 4,1 |
| | skills | 29 | 31 398 | 1 507 708 | 4,5 |
| | full | 26 | 27 909 | 1 363 034 | 4,6 |
| Haiku 5.5 | none | 62 | 73 469 | 3 767 150 | 5,9 |
| | agents | 70 | 86 608 | 5 397 860 | 8,3 |
| | skills | 74 | 85 562 | 6 428 217 | 9,0 |
| | full | 71 | 87 200 | 5 525 890 | 8,1 |
| Muse Spark 1.3 | none | 62 | 20 360 | 4 125 950 | 4,1 |
| | agents | 64 | 18 510 | 4 354 079 | 8,6 |
| | skills | 74 | 18 452 | 4 700 618 | 5,1 |
| | full | 67 | 19 244 | 4 989 247 | 5,8 |
| DeepSeek v4.1 flash | none | 58 | 17 518 | 4 256 746 | 9,3 |
| | agents | 68 | 20 720 | 4 962 629 | 8,7 |
| | skills | 67 | 20 570 | 6 097 903 | 8,3 |
| | full | 76 | 22 686 | 6 913 314 | 8,4 |
| gpt-oss-20b | none | 42 | 10 990 | 693 686 | 2,5 |
| | agents | 38 | 10 620 | 691 718 | 1,8 |
| | skills | 46 | 13 660 | 977 582 | 2,4 |
| | full | 46 | 11 222 | 982 754 | 2,3 |

Totais da rodada:

| modelo | tempo de agente | tokens de saída | custo estimado | observação |
|---|---|---|---|---|
| Sonnet 5.5 | 3,7 h | 1,57 M | US$ 38,7 | estimativa do CLI a preço de lista; a execução usou a assinatura |
| Haiku 5.5 | 7,0 h | 4,87 M | US$ 27,3 | idem |
| Muse Spark 1.3 | 6,1 h | 1,03 M | – | plano OpenCode Go |
| DeepSeek v4.1 flash | 8,1 h | 1,06 M | – | plano OpenCode Go |
| gpt-oss-20b | 3,0 h | 0,96 M | – | local |

- **Tempo de parede não é comparável entre modelos.** Ele depende de provedor, hardware e
  concorrência; turnos e tokens são a medida comparável.
- **Haiku:** gera ~3× mais tokens de saída que o Sonnet e leva ~2× mais tempo, com pass@1 menor.

### 5.2 Falhas sistemáticas

- **Haiku 5.5, T04a/b/c, todos os níveis.** Em todas as 12 células o único teste que falha é
  `EntityPolicyTest > EntityMembershipPolicy`: `assignRole(admin, ownerMembership)` deveria ser
  `true`.
  - O enunciado diz *"owner and admin may assign roles"*. A Haiku acrescenta uma proteção ao dono
    que não foi pedida: o admin não poderia alterar o papel do dono.
  - É uma interpretação estável do modelo, que nenhum nível de harness corrigiu.
- **Muse, T05, níveis none/agents/full.** 1 teste de `MembersTest` falha. Os testes que falham
  variam, mas são todos do mesmo componente.
- **gpt-oss-20b:**
  - 24 de 56 runs terminaram com saída malformada: o llama-server não conseguiu interpretar a
    resposta no formato do modelo (*"does not match the expected peg-native format"*). Esses
    runs contam como `fail` do modelo (decisão 10).
  - 35 de 56 runs deixaram regressões além da linha de base (média de 5,5 testes), em geral
    código que quebra a aplicação inteira.
  - Pint passou em 3 de 56 runs.

### 5.3 Qualidade além do pass@1

| modelo | runs com regressão | pint ok | tocou em testes | tocou no harness | saída Blade sem escape |
|---|---|---|---|---|---|
| Sonnet 5.5 | 3/56 | 43/56 | 11/56 | 0 | 0 |
| Haiku 5.5 | 5/56 | 44/56 | 9/56 | 0 | 0 |
| Muse Spark 1.3 | 1/56 | 40/56 | 0/56 | 0 | 0 |
| DeepSeek v4.1 flash | 2/56 | 45/56 | 3/56 | 0 | 0 |
| Beam (23 runs) | 0/23 | 14/23 | 2/23 | 0 | 0 |
| gpt-oss-20b | 35/56 | 3/56 | 0/56 | 0 | 0 |

"Tocou em testes" quer dizer que o agente alterou testes existentes da árvore. Os testes
ocultos nunca ficam visíveis para ele.

### 5.4 Timeouts e tentativas de acesso ao repositório real

- **Timeouts válidos:** 1, do DeepSeek no T05 `none` (trabalhou os 30 min e passou mesmo
  assim).
- **Timeouts falsos do Beam:** 6, causados pelo provedor fora do ar (§6). Foram reclassificados
  e não contam como dado.
- **Tentativas de acesso ao repositório real (`fetch_attempts`):** 3, todas do DeepSeek no
  nível `none`.
  - T03a: `webfetch` de `raw.githubusercontent.com/PegaFila/PegaFilaWeb/...`.
  - T04b: `curl api.github.com/repos/PegaFila/PegaFilaWeb`.
  - T09: `git ls-remote https://github.com/PegaFila/PegaFilaWeb.git`.
  - O repositório é privado e o sandbox não tem credencial do GitHub: todas falharam (erro ou
    404), sem vazamento.
  - Nenhuma tentativa nos níveis com harness. Com n = 3 isso é anedótico, mas é coerente com o
    harness dar ao agente contexto suficiente para não procurar fora.

## 6. Incidentes e decisões durante a rodada

O detalhe completo, com horários, está em `runs/reduced-1.md`. As verificações de hora em hora
estão em `runs/_logs/reduced-1-checks.md`.

1. **Falsos positivos de contaminação.** Os casos foram:
   - um link do PR #25 escrito no `CHANGELOG.md`, inclusive com barras escapadas;
   - `../..` dentro de `vendor/`.

   Correções:
   - O veredito passou a ser recalculado a partir do log bruto completo. Antes vinha dos hits
     gravados, cortados em 300 caracteres.
   - URLs do GitHub do repositório real contam como tentativa, não como contaminação.

   Resultado final: 0 runs contaminados.
2. **01:24, falta de memória no host.** Um container de agente chegou a 23 GB de swap e o
   `systemd-oomd` o matou. Desde 01:53 há limite de 6 GB por container. O run foi refeito
   (infra).
3. **01:52, Qwen3.6-35B-A3B retirado.** Ele levava ~23 min por célula (100–150 turnos, ~60 mil
   tokens de saída a ~42 tok/s), e as 53 células restantes levariam ~20 h na GPU única. As 3
   células feitas ficam só como nota:
   - T07 skills: ✓, 10 min.
   - T03b skills: ✓, mas com timeout.
   - T10 agents: ✗, 30 min.
4. **02:35, Beam (free) fora do ar.** Os runs ficavam 10–15 min sem nenhum evento até o timeout
   de 30 min.
   - **Watchdog de silêncio:** 8 min sem saída fazem o run ser morto e tratado como 429 (o pool
     pausa e a célula não gasta tentativa).
   - Os 6 timeouts falsos foram reenfileirados.
   - O provedor não voltou até 05:30. Às 05:30 as 33 células restantes seguiam pendentes, com o
     processo ainda tentando.
5. **Classificação de falhas de avaliação.**
   - Um `composer install` que quebra no `artisan` por código do agente é resultado válido, não
     erro de avaliação (corrigido na rodada completa 1, com `regrade`).
   - Um `exit 1` do OpenCode depois de o agente terminar conta como infra e é refeito; a
     decisão não depende do resultado.
6. **Reinícios do orquestrador** (01:52, 01:53, 02:38) para aplicar correções. Os agentes em
   andamento recomeçaram como novas tentativas. Nenhuma célula foi duplicada (retomada pelo
   manifesto).

## 7. Ameaças à validade

- **Efeito de teto.** Quatro modelos resolvem ≥ 93% das tarefas sem harness. Com 14 tarefas por
  célula e 1 repetição, o desenho só detectaria efeitos grandes: o McNemar precisa de ≥ 6
  discordâncias na mesma direção para p < 0,05. *Ausência de evidência não é evidência de
  ausência*, e efeitos de 5–15 pp passariam despercebidos.
- **1 repetição.**
  - Não mede a variância de um mesmo modelo na mesma célula.
  - As 20 células de rep 2/3 da rodada completa 1 (Sonnet, Haiku 5.5, gpt-oss) servem como
    amostra pequena dessa variação e estão no manifesto.
- **Dificuldade das tarefas.**
  - As 14 tarefas vêm do histórico real do PegaFila, com testes ocultos escritos para a
    solução original.
  - Os testes parecem pouco discriminativos para modelos fortes: a fração aprovada fica ≥ 0,993
    mesmo nas falhas.
  - Tarefas mais difíceis, ou critérios além dos testes (revisão de código, aderência às
    convenções do harness), seriam necessárias para medir ganho do harness acima do teto.
- **Runners diferentes.** Claude Code e OpenCode têm prompts de sistema, ferramentas e gestão
  de contexto diferentes. A comparação válida do efeito do harness é *dentro* de cada modelo.
  Comparações entre modelos misturam modelo e runner.
- **Muse Spark.**
  - Ajudou a escrever o código do PegaFila e treina com os dados enviados (`trains_on_data`),
    então pode haver memorização.
  - O `opencode.json` do harness v1 aponta `model`/`small_model` para o Muse. A checagem de
    modelo confirmou, para todos os runs OpenCode no nível `full`, que só o modelo sob teste
    respondeu.
- **Modelo local.** O gpt-oss rodou quantizado (MXFP4), com o template e o parser do
  llama.cpp. Parte das falhas dele é de formato de saída (24/56), uma limitação do conjunto
  modelo + servidor e não só do modelo.
- **Beam incompleto e Qwen retirado.** Sem dados suficientes para comparação entre níveis.
- **Ambiente.**
  - Internet liberada no sandbox: o detector e a natureza privada do repositório cobrem o risco
    de vazamento, e houve 0 vazamentos.
  - Limite de 6 GB de RAM introduzido às 01:53: runs anteriores não tinham limite. Nenhum run
    depois disso morreu por memória.
- **Prompt.** O preâmbulo não interativo é igual para todos. A versão anterior ao preâmbulo
  (`v0`) não entra nesta análise.

## 8. Arquivos

| arquivo | conteúdo |
|---|---|
| `runs/manifest.jsonl` | uma linha por transição de célula (estado, tentativas, métricas, contaminação) |
| `runs/results.jsonl` | uma linha por avaliação (`evaluate.sh`); a última linha de cada `run_id` vale |
| `runs/report.csv`, `runs/report.md` | `python -m orchestrator report` (todos os runs, todas as rodadas) |
| `runs/reduced-1-analysis.py` | gera as tabelas deste relatório (`python runs/reduced-1-analysis.py`) |
| `runs/_logs/reduced-1-tables.md` | saída do script acima no fechamento (05:30) |
| `runs/reduced-1.md` | plano, execução e incidentes com horário |
| `runs/_logs/reduced-1-checks.md` | verificações de hora em hora |
| `runs/env-*.json` | versões, imagens, SHAs e seed de cada invocação |
| `orchestrator/NOTES.md` | decisões de projeto (1–11) e achados |
