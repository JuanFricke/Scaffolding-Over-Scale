# Orchestrator

Runs the benchmark matrix (model × task × level × rep) with safe parallelism,
resume and a reproducible record. Standard library only (Python 3.11+).
Design notes and verified assumptions: [`NOTES.md`](NOTES.md).

```
PREPARE (prepare-task.sh) -> AGENT (pool per provider) -> GRADE (evaluate.sh, grade_slots) -> DONE
```

## Setup (once)

```bash
export PF_REPO=~/Projetos/PegaFilaWeb          # private subject repo, read-only
benchmark/bin/build-image.sh                    # grading image pf-bench:tcc-baseline-v1
benchmark/orchestrator/sandbox/build.sh         # agent sandbox pf-bench-agent:tcc-baseline-v1
opencode auth login                             # OpenCode Go
claude setup-token && export CLAUDE_CODE_OAUTH_TOKEN=...   # or `claude` login / ANTHROPIC_API_KEY
benchmark/orchestrator/llama/serve.sh           # local models (llama/*): llama-server router, keep it running
```

Local models (`llama/<name>`) run through OpenCode against `llama-server` in router mode:
`llama/models.ini` holds the runner parameters (context per model, one slot, `ngram-mod`
speculative decoding, sampling), one model in VRAM at a time (pool `llama`, concurrency 1).
`serve.sh` takes `LLAMA_SERVER`, `MODELS_DIR` (default `~/Modelos`) and `LLAMA_PORT` (8089).

Credentials are never written in the repository: OpenCode's are exported into a
temporary per-run home (outside the repo, deleted after the run); Claude Code
uses `CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_API_KEY`, or a copy of the CLI login.

## Usage (from `benchmark/`)

```bash
python -m orchestrator plan                       # cells per model/level, queue size; touches nothing
python -m orchestrator run --dry-run --reps 1     # what would run
python -m orchestrator pilot --models opencode-go/glm-5.3-flash   # 3 tasks x 4 levels x 1 rep + cost estimate
python -m orchestrator run --reps 1               # first pass; rerun the same command to resume
python -m orchestrator run --models claude-haiku-5-5 --levels none,full --tasks T06-issue-ticket
python -m orchestrator status                     # by state / model / level, partial pass rate, paused pools
python -m orchestrator retry --failed-infra       # requeue infrastructure failures only
python -m orchestrator report                     # runs/report.csv + runs/report.md (pass@1 per runner)
python -m orchestrator env                        # runs/env-<ts>.json: tool versions, image ids, SHAs, seed
python -m orchestrator retry --stale-prompt       # rerun done cells made with another prompt version
python -m orchestrator retry --stale-prompt --no-run   # only requeue them; the next `run` picks them up
python -m orchestrator reparse                    # recompute Claude Code metrics from stored logs
```

`run` writes an `env-*.json` before executing. Cells already `done` (or
`failed_infra`) are skipped, so the same command resumes after a crash or Ctrl-C.
Pilot cells are ordinary rep-1 cells of the matrix: they count as data.

## Prompt

Each agent receives `prompt-preamble.md` (work autonomously, do not ask questions)
followed by the task statement from `tasks/<id>.yaml`, unchanged. The preamble's hash is
recorded per run as `prompt_version`, and the exact text sent goes to `runs/<run_id>/prompt.sent.md`.

## Matrix (`matrix.toml`)

`[run]`: `seed` (shuffles cell order, recorded), `reps`, `agent_timeout_s`,
`grade_slots`, `levels`, `sandbox` (`docker` | `none`), `sandbox_image`,
`max_attempts`, `backoff_base_s`, `work_dir`. `[[model]]`: `id`, `runner`
(`opencode`, `claude-code`, `oracle`, `null`; OpenCode ids `llama/*` use the local server), `pool`, optional `levels`,
`trains_on_data`/`training_ok`, `validation`. `[pool.<name>] max_concurrency`.

Validation runners (`oracle`, `null`) only run when named in `--models`.

## State and outputs

| file | content |
|---|---|
| `runs/manifest.jsonl` | one line per cell transition (tracked; the source of truth for resume) |
| `runs/results.jsonl` | one line per grading, written by `evaluate.sh` (tracked); join on `run_id` |
| `runs/<run_id>/` | agent logs (`agent.stdout.log` = raw runner events, `agent.session.json`), patch, gate logs, `result.json` (ignored) |
| `runs/env-*.json` | environment snapshot per invocation |
| `runs/report.csv`, `report.md` | `report` output |

`run_id = <cell_id>__a<attempt>`, `cell_id = <model>__<task>__<level>__r<rep>`.
`rep`, `cell_id`, runner version and sandbox also go into `agent_metrics` of the
result line. A regrade appends a second line with the same `run_id`; the last one wins.

## Failures

| kind | handling |
|---|---|
| `infra`, rate limit (429, quota, usage window) | not data and **no attempt spent**: the whole pool pauses (60 s, doubling per consecutive 429 up to 30 min, reset by a successful run) and the cell retries until the window reopens |
| `infra`, other (network, 5xx, CLI crash, wrong model used) | not data; backoff with jitter; `max_attempts`, then `failed_infra` |
| `timeout` | data: the tree is graded as it is (`agent_outcome = timeout`) |
| `fail` (context overflow etc.) / normal end | data, graded normally |
| `grade_error` (evaluate.sh / Docker / network failed) | regrade the same tree; the agent is not rerun |

## Isolation

With `sandbox = "docker"` the agent runs in `pf-bench-agent` with **only its tree**
mounted at `/workspace` and full internet access. `bin/pf shell <cmd>` works
through a `docker` shim (it runs `<cmd>` in place); nothing else from the host is
visible (no `PF_REPO`, no `benchmark/tasks`, no other runs). After every run the
tool-call inputs are scanned for paths outside the tree; hits set
`contamination_suspected` in the manifest and those runs are left out of the
report's pass@1 (they are kept on disk).

## Validation (acceptance checks)

```bash
python -m orchestrator run --models oracle,null --levels none --reps 1 --concurrency 1 --tag eqv-c1
python -m orchestrator run --models oracle,null --levels none --reps 1 --concurrency 4 --tag eqv-c4
python -m orchestrator report --tag eqv-c1 --include-validation   # -> runs/_tagged/report-eqv-c1.*
python -m unittest discover -s orchestrator/tests -t .   # 429 pause, resume, level isolation
```

`--tag` keeps validation runs out of the thesis artifacts: manifest, env and report go to
`runs/_tagged/` (git-ignored) and run ids get a `__<tag>` suffix. `evaluate.sh` still appends
their lines to `results.jsonl`; drop lines whose `run_id` ends in a tag before committing it.
