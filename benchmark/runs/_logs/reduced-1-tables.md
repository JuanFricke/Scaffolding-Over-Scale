Runs graded (rep 1, prompt pre-218e85fd81c1): 309; contamination suspects excluded: 0; tasks: 14

## pass@1 (hidden tests) por modelo × nível, IC 95% de Wilson

| modelo | none | agents | skills | full | total |
|---|---|---|---|---|---|
| Sonnet 5.5 | 14/14 = 1.00 [0.78, 1.00] | 14/14 = 1.00 [0.78, 1.00] | 14/14 = 1.00 [0.78, 1.00] | 13/14 = 0.93 [0.69, 0.99] | 55/56 = 0.98 |
| Haiku 5.5 | 11/14 = 0.79 [0.52, 0.92] | 11/14 = 0.79 [0.52, 0.92] | 11/14 = 0.79 [0.52, 0.92] | 11/14 = 0.79 [0.52, 0.92] | 44/56 = 0.79 |
| Muse Spark 1.3 | 13/14 = 0.93 [0.69, 0.99] | 13/14 = 0.93 [0.69, 0.99] | 14/14 = 1.00 [0.78, 1.00] | 13/14 = 0.93 [0.69, 0.99] | 53/56 = 0.95 |
| DeepSeek v4.1 flash | 14/14 = 1.00 [0.78, 1.00] | 14/14 = 1.00 [0.78, 1.00] | 14/14 = 1.00 [0.78, 1.00] | 14/14 = 1.00 [0.78, 1.00] | 56/56 = 1.00 |
| Beam (free) | 10/10 = 1.00 [0.72, 1.00] | 7/7 = 1.00 [0.65, 1.00] | 5/5 = 1.00 [0.57, 1.00] | 7/7 = 1.00 [0.65, 1.00] | 29/29 = 1.00 |
| gpt-oss-20b | 2/14 = 0.14 [0.04, 0.40] | 1/14 = 0.07 [0.01, 0.31] | 1/14 = 0.07 [0.01, 0.31] | 2/14 = 0.14 [0.04, 0.40] | 6/56 = 0.11 |

## Fração média de testes ocultos aprovados (métrica contínua, sensível abaixo do teto)

| modelo | none | agents | skills | full |
|---|---|---|---|---|
| Sonnet 5.5 | 1.000 (n=14) | 1.000 (n=14) | 1.000 (n=14) | 0.998 (n=14) |
| Haiku 5.5 | 0.993 (n=14) | 0.993 (n=14) | 0.993 (n=14) | 0.993 (n=14) |
| Muse Spark 1.3 | 0.998 (n=14) | 0.998 (n=14) | 1.000 (n=14) | 0.998 (n=14) |
| DeepSeek v4.1 flash | 1.000 (n=14) | 1.000 (n=14) | 1.000 (n=14) | 1.000 (n=14) |
| Beam (free) | 1.000 (n=10) | 1.000 (n=7) | 1.000 (n=5) | 1.000 (n=7) |
| gpt-oss-20b | 0.250 (n=14) | 0.244 (n=14) | 0.203 (n=14) | 0.203 (n=14) |

## Efeito de cada nível vs `none`, pareado por tarefa (McNemar exato)

`+` = só o nível passou; `−` = só o `none` passou. Δ em pontos percentuais sobre os pares completos.

| modelo | nível | pares | ambos ✓ | + | − | ambos ✗ | Δ pass@1 | p |
|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | agents | 14 | 14 | 0 | 0 | 0 | +0.0 | 1.000 |
| Sonnet 5.5 | skills | 14 | 14 | 0 | 0 | 0 | +0.0 | 1.000 |
| Sonnet 5.5 | full | 14 | 13 | 0 | 1 | 0 | -7.1 | 1.000 |
| Haiku 5.5 | agents | 14 | 11 | 0 | 0 | 3 | +0.0 | 1.000 |
| Haiku 5.5 | skills | 14 | 11 | 0 | 0 | 3 | +0.0 | 1.000 |
| Haiku 5.5 | full | 14 | 11 | 0 | 0 | 3 | +0.0 | 1.000 |
| Muse Spark 1.3 | agents | 14 | 13 | 0 | 0 | 1 | +0.0 | 1.000 |
| Muse Spark 1.3 | skills | 14 | 13 | 1 | 0 | 0 | +7.1 | 1.000 |
| Muse Spark 1.3 | full | 14 | 13 | 0 | 0 | 1 | +0.0 | 1.000 |
| DeepSeek v4.1 flash | agents | 14 | 14 | 0 | 0 | 0 | +0.0 | 1.000 |
| DeepSeek v4.1 flash | skills | 14 | 14 | 0 | 0 | 0 | +0.0 | 1.000 |
| DeepSeek v4.1 flash | full | 14 | 14 | 0 | 0 | 0 | +0.0 | 1.000 |
| Beam (free) | agents | 5 | 5 | 0 | 0 | 0 | +0.0 | 1.000 |
| Beam (free) | skills | 4 | 4 | 0 | 0 | 0 | +0.0 | 1.000 |
| Beam (free) | full | 5 | 5 | 0 | 0 | 0 | +0.0 | 1.000 |
| gpt-oss-20b | agents | 14 | 1 | 0 | 1 | 12 | -7.1 | 1.000 |
| gpt-oss-20b | skills | 14 | 1 | 0 | 1 | 12 | -7.1 | 1.000 |
| gpt-oss-20b | full | 14 | 2 | 0 | 0 | 12 | +0.0 | 1.000 |

Agregado (pares modelo × tarefa; sem os modelos incompletos: Beam (free)):

| nível | pares | ambos ✓ | + | − | ambos ✗ | Δ pass@1 | p |
|---|---|---|---|---|---|---|---|
| agents | 70 | 53 | 0 | 1 | 16 | -1.4 | 1.000 |
| skills | 70 | 53 | 1 | 1 | 15 | +0.0 | 1.000 |
| full | 70 | 53 | 0 | 1 | 16 | -1.4 | 1.000 |

## Custo por modelo × nível (medianas por run)

Tokens de entrada incluem leituras de cache (o Claude Code lê quase tudo do cache).

| modelo | nível | n | turnos | tokens de saída | tokens de entrada | tempo do agente (min) | timeouts |
|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | none | 14 | 18 | 22 502 | 905 810 | 3.1 | 0 |
| Sonnet 5.5 | agents | 14 | 30 | 30 112 | 1 468 970 | 4.1 | 0 |
| Sonnet 5.5 | skills | 14 | 29 | 31 398 | 1 507 708 | 4.5 | 0 |
| Sonnet 5.5 | full | 14 | 26 | 27 909 | 1 363 034 | 4.6 | 0 |
| Haiku 5.5 | none | 14 | 62 | 73 469 | 3 767 150 | 5.9 | 0 |
| Haiku 5.5 | agents | 14 | 70 | 86 608 | 5 397 860 | 8.3 | 0 |
| Haiku 5.5 | skills | 14 | 74 | 85 562 | 6 428 217 | 9.0 | 0 |
| Haiku 5.5 | full | 14 | 71 | 87 200 | 5 525 890 | 8.1 | 0 |
| Muse Spark 1.3 | none | 14 | 62 | 20 360 | 4 125 950 | 4.1 | 0 |
| Muse Spark 1.3 | agents | 14 | 64 | 18 510 | 4 354 079 | 8.6 | 0 |
| Muse Spark 1.3 | skills | 14 | 74 | 18 452 | 4 700 618 | 5.1 | 0 |
| Muse Spark 1.3 | full | 14 | 67 | 19 244 | 4 989 247 | 5.8 | 0 |
| DeepSeek v4.1 flash | none | 14 | 58 | 17 518 | 4 256 746 | 9.3 | 1 |
| DeepSeek v4.1 flash | agents | 14 | 68 | 20 720 | 4 962 629 | 8.7 | 0 |
| DeepSeek v4.1 flash | skills | 14 | 67 | 20 570 | 6 097 903 | 8.3 | 0 |
| DeepSeek v4.1 flash | full | 14 | 76 | 22 686 | 6 913 314 | 8.4 | 0 |
| Beam (free) | none | 10 | 69 | 9 998 | 2 817 642 | 3.4 | 0 |
| Beam (free) | agents | 7 | 83 | 12 100 | 4 206 841 | 4.6 | 0 |
| Beam (free) | skills | 5 | 69 | 12 224 | 4 408 680 | 4.3 | 0 |
| Beam (free) | full | 7 | 89 | 10 684 | 5 116 071 | 4.2 | 0 |
| gpt-oss-20b | none | 14 | 42 | 10 990 | 693 686 | 2.5 | 0 |
| gpt-oss-20b | agents | 14 | 38 | 10 620 | 691 718 | 1.8 | 0 |
| gpt-oss-20b | skills | 14 | 46 | 13 660 | 977 582 | 2.4 | 0 |
| gpt-oss-20b | full | 14 | 46 | 11 222 | 982 754 | 2.3 | 0 |

## Qualidade além do pass@1 (todos os níveis)

Regressões = testes que falham fora dos ocultos, além dos que já falham na árvore intocada (agente nulo, por tarefa: [1, 2] falhas; quase todas do PfControllerTest). Suíte que não rodou conta como regressão.

| modelo | runs com regressão | regressões além da base (média) | pint ok | tocou em testes | tocou no harness | saída sem escape | arquivos alterados (mediana) | linhas + (mediana) |
|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | 3/56 | 0.20 | 43/56 | 11/56 | 0/56 | 0/56 | 17 | 873 |
| Haiku 5.5 | 5/56 | 0.32 | 44/56 | 9/56 | 0/56 | 0/56 | 20 | 1 214 |
| Muse Spark 1.3 | 1/56 | 0.62 | 40/56 | 0/56 | 0/56 | 0/56 | 13 | 594 |
| DeepSeek v4.1 flash | 2/56 | 0.07 | 45/56 | 3/56 | 0/56 | 0/56 | 18 | 930 |
| Beam (free) | 0/29 | 0.00 | 19/29 | 2/29 | 0/29 | 0/29 | 12 | 449 |
| gpt-oss-20b | 35/56 | 5.55 | 3/56 | 0/56 | 0/56 | 0/56 | 11 | 351 |

## pass@1 por tarefa (✓/✗ por nível: none · agents · skills · full)

| tarefa | Sonnet 5.5 | Haiku 5.5 | Muse Spark 1.3 | DeepSeek v4.1 flash | Beam (free) | gpt-oss-20b |
|---|---|---|---|---|---|---|
| T01-discord-ops-alert | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | · · ✓ ✓ | ✗ ✗ ✗ ✗ |
| T02-discord-mention-id | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| T03a-auth-core | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ · ✓ | ✗ ✗ ✗ ✗ |
| T03b-mail-theme | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ · · | ✗ ✗ ✗ ✗ |
| T04a-entity-model | ✓ ✓ ✓ ✓ | ✗ ✗ ✗ ✗ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ · ✓ | ✗ ✗ ✗ ✗ |
| T04b-tenant-onboarding | ✓ ✓ ✓ ✓ | ✗ ✗ ✗ ✗ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | · ✓ · ✓ | ✗ ✗ ✗ ✗ |
| T04c-entity-management | ✓ ✓ ✓ ✓ | ✗ ✗ ✗ ✗ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ · ✓ · | ✗ ✗ ✗ ✗ |
| T05-entity-invites | ✓ ✓ ✓ ✗ | ✓ ✓ ✓ ✓ | ✗ ✗ ✓ ✗ | ✓ ✓ ✓ ✓ | · · · · | ✗ ✗ ✗ ✗ |
| T06-issue-ticket | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ · ✓ · | ✗ ✗ ✗ ✗ |
| T07-call-next-ticket | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ · · · | ✓ ✗ ✗ ✓ |
| T08-queue-management | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ · ✓ | ✗ ✗ ✗ ✗ |
| T09-queue-management-ui | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ · ✓ · | ✗ ✗ ✗ ✗ |
| T10-totem-bff | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | · ✓ · · | ✗ ✗ ✗ ✗ |
| T11-priority-ticket-prefix | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ · · ✓ | ✗ ✗ ✗ ✗ |

## Tentativas de acessar o repositório real pela rede (`fetch_attempts`)

- DeepSeek v4.1 flash, T03a-auth-core, none: 1 tentativa(s); hidden_ok=True
- DeepSeek v4.1 flash, T04b-tenant-onboarding, none: 1 tentativa(s); hidden_ok=True
- DeepSeek v4.1 flash, T09-queue-management-ui, none: 1 tentativa(s); hidden_ok=True

