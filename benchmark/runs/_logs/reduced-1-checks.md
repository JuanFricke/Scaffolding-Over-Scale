# Verificações da rodada reduzida 1

| hora | done/392 | problemas | ETA |
|---|---|---|---|
| 00:27 | 12 | início 00:19; deepseek validado (T01 ok) | 07:30–08:00 |
| 00:45 | 33 | falso positivo de contaminação (beam T06 skills, link GitHub) + bug em suspected() corrigidos, sem reinício | 07:30–08:00 |
| 01:55 | 130/336 | Qwen retirado (23 min/célula, ~20 h); OOM às 01:24 (container com 23 GB de swap) → limite de 6 GB por agente; 2 reinícios | ~05:00 |
| 02:40 | 173/336 | beam-free fora do ar: 6 timeouts eram travamentos do provedor → watchdog de silêncio (8 min = 429), 6 células reenfileiradas, reinício 02:38 | ~05:15 (beam depende do provedor voltar) |
| 03:35 | 232/336 | beam-free segue fora (12 travamentos, pausas até 518 s); deepseek T09 none exit 1 após terminar → refeito como infra | ~05:30 para os 5 modelos; beam-free (33 células) depende do provedor |
| 04:35 | 282/336 | Claude e gpt-oss completos; Muse+deepseek faltam 21; beam-free segue fora (18 travamentos, 33 células pendentes) | Muse/deepseek ~05:30; beam-free depende do provedor |
| 05:30 | 303/336 | 5 modelos completos; beam-free 23/56 (provedor fora); relatório gerado | fim, exceto beam-free |
