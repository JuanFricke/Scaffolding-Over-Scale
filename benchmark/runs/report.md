# pass@1 by model x level (hidden tests; contaminated runs excluded)

Grouped by runner: compare models only within one runner.

## runner `claude-code`

| model | none | agents | skills | full |
|---|---|---|---|---|
| claude-haiku-4-5 | 0.67 (2/3) | 0.67 (2/3) | 0.33 (1/3) | 0.33 (1/3) |
| claude-haiku-5-5 | 0.82 (14/17) | 0.75 (12/16) | 0.81 (13/16) | 0.75 (12/16) |
| claude-sonnet-5-5 | 1.00 (18/18) | 1.00 (16/16) | 1.00 (14/14) | 0.93 (14/15) |

## runner `opencode`

| model | none | agents | skills | full |
|---|---|---|---|---|
| llama/gpt-oss-20b | 0.20 (4/20) | 0.06 (1/17) | 0.06 (1/16) | 0.19 (3/16) |
| llama/qwen3.6-35b-a3b | - | 0.00 (0/1) | 1.00 (2/2) | - |
| opencode-go/beam-free | 1.00 (8/8) | 1.00 (6/6) | 1.00 (4/4) | 1.00 (5/5) |
| opencode-go/deepseek-v4.1-flash | 1.00 (14/14) | 1.00 (14/14) | 1.00 (14/14) | 1.00 (14/14) |
| opencode-go/glm-5.3-flash | 1.00 (1/1) | 1.00 (2/2) | - | - |
| opencode-go/mimo-v2.6-flash | 0.50 (1/2) | 1.00 (1/1) | - | - |
| opencode-go/muse-spark-1.3-contributor | 0.93 (13/14) | 0.93 (13/14) | 1.00 (14/14) | 0.93 (13/14) |

353 graded runs; 0 excluded as contamination suspects. CSV: runs/report.csv
