# Code-quality analysis

Pass@1 sat at the ceiling for most models in reduced run 1, so this package asks a different
question: does the harness change **how** the code is written? It works on what the runs left
behind (`runs/<run_id>/agent.patch`, the final trees in `work/`) and never reruns an agent.
Standard library only.

| layer | what | where |
|---|---|---|
| 1, static | Larastan level 5 (new errors vs the base), cyclomatic complexity, tests written, distance from the reference solution | `static.py`, `php/complexity.php` |
| 2, conventions | 10 heuristic rules from `harness/v1/AGENTS.md`, each applying only when the change touches its subject | `conventions.py` |
| 3, judges | blind review by two LLM judges out of Opus 5.5, Muse Spark 1.3 and DeepSeek v4.1 flash, never the author's family, run as the `code-review-judge` skill | `judge.py`, `skills/code-review-judge/` |

## Usage (from `benchmark/`)

```bash
python -m quality select --pilot                 # which runs (pilot: T02 + T09, 46 runs)
python -m quality conventions --pilot            # layer 2, seconds
python -m quality static --pilot                 # layer 1, ~8 s per run (Docker, pf-bench image)
python -m quality judge --pilot --dry-run        # layer 3 plan: reviews per judge
python -m quality judge --pilot                  # run it; rerun the same command to resume
python -m quality judge --tasks T02-discord-mention-id --judges opus --max-reviews 1 --tag smoke
python -m quality analyze --pilot --name pilot   # -> runs/quality/report-pilot.md
python -m quality status --pilot
python -m unittest discover -s quality/tests -t .
```

Without `--pilot` every graded run of reduced run 1 is selected (309 runs).

## Outputs

| file | content |
|---|---|
| `runs/quality/conventions.jsonl`, `static.jsonl` | one line per run (layers 2 and 1); per-run copies in `runs/<run_id>/quality/` |
| `runs/quality/reviews/<run_id>__<judge>.json` | one review: the judge's `review.json` plus judge model, tokens, time, diff metadata |
| `runs/quality/judge-manifest.jsonl` | state of every (run, judge) review: running / invalid / infra_error / done / judge_error |
| `runs/quality/report-<name>.md` | tables from `analyze` |
| `runs/quality/workspaces/` | judge workspaces and logs (git-ignored; a workspace is deleted after a valid review) |

## Judges

**Pairs.**
- **Sonnet and Haiku:** Muse + DeepSeek.
- **Muse:** Opus + DeepSeek.
- **DeepSeek:** Opus + Muse.
- **gpt-oss and Beam:** the three pairs rotate, balanced per model × level with seed 20261028.

**Blind workspace.** Each review runs in a workspace that holds:
- `task.md`: the statement the agent got.
- `change.diff`: the patch, without harness paths or lock files. Harness file names are redacted
  inside it, and very large files are summarized.
- `conventions.md`: the normative sections of `AGENTS.md` plus the Livewire policy, the same
  standard for every level.
- The rubric, the schema and the skill, under both `.claude/skills/` and `.opencode/skills/`.

A leak check refuses any workspace that contains the run id, model, level or test result.

**Validation.** The judge writes `review.json`, which is validated against
`review.schema.json`. An invalid file gets one retry with the errors fed back; after that the
review becomes `judge_error`.

**Sandbox and limits.** Reviews use the agent sandbox (Docker, workspace only), with a 6 GB
cap, the 8-minute silence watchdog and per-provider pools. A 429 pauses the pool and does not
spend an attempt.

## Validating layer 2

The rules are heuristics. Every violation keeps its evidence in `conventions.json`.
- **Pilot, by hand:** all 25 violations were read against the code; all were real (C1 19/19,
  C2 2/2, C10 4/4).
- **Not counted:** rules that never applied in the pilot (C5 migrations, C8 models) are
  untested on real data.
