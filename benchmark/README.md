# Benchmark — repository-level harness evaluation

Experiment infrastructure for the TCC *Scaffolding Over Scale: Evaluating
Repository-Level Harnesses to Maximize Output Quality in Constrained LLMs*
(Juan Paulo Fricke, UNIJUÍ). This directory is the public thesis artifact. It is
**not application code**: nothing here is loaded by the agent under test (task
trees are exported from historical commits of the subject repository).

The subject repository is `PegaFila/PegaFilaWeb` (**private**, a Laravel + Bulma
queue-management web app). Task statements, scripts and a redacted snapshot of
the harness are public here; the task commits themselves are not, so **running
the benchmark requires read access to that private repository** (see
"Requirements"). What was removed from the public copy is described in
[`REDACTIONS.md`](REDACTIONS.md).

## Question

Does a repository-level harness (always-on rules, on-demand skills, LSP and
tool configuration) raise the output quality of a small / constrained coding
agent on real tasks, and which layer of the harness carries the effect?

## Design

- **Tasks** replay real pull requests of the subject repository (`PegaFila/PegaFilaWeb`, private). A task = the
  repository at the PR's base commit + a task statement written from the PR
  and the domain docs. The PR's own test files are the **hidden oracle**: they
  are copied in from the solution commit only at grading time.
- **Conditions** are ablation levels of the harness, applied from one frozen
  snapshot (`harness/v1`, vendored from git tag `tcc-baseline-v1` of the subject
  repository, see [`harness/v1/SOURCE.md`](harness/v1/SOURCE.md)) so every task sees the
  same harness regardless of what its base commit shipped:

  | level | artifacts present in the tree |
  | --- | --- |
  | `none` | nothing (control) |
  | `agents` | `AGENTS.md` + `CLAUDE.md` (always-on rules) |
  | `skills` | `agents` + `ai/` (skills, commands, rules, templates — on-demand reading) |
  | `full` | `skills` + `opencode.json` (instructions + LSP) + `.claude/settings.json` |

- **Metrics** per run (one JSON line in `runs/results.jsonl`): hidden-test
  pass/fail, full-suite pass/fail and regressions, Pint, diff size, harness
  violations (tests deleted or modified, harness files edited, `{!! !!}`
  introduced), plus whatever the agent runner reports (tokens, turns, wall
  time) via `--agent-metrics`.

## Layout

```
benchmark/
  README.md            this file
  REDACTIONS.md        what was redacted from the public copy, by category
  tasks/*.yaml         one task per file (schema below)
  harness/v1/          vendored, redacted harness snapshot under study (+ SOURCE.md)
  bin/
    build-image.sh     build the grading image once from docker/Dockerfile at a ref of PF_REPO
    list-tasks.sh      print the default task set (--all includes composites, --ids for scripting)
    prepare-task.sh    export a task tree, apply a harness level, write the prompt
    apply-harness.sh   strip / apply the harness at a level (used by prepare-task.sh)
    evaluate.sh        copy hidden tests in, run gates in containers, append results
    lib.sh             shared helpers (yaml parsing, json)
  work/                prepared trees (ignored by git)
  runs/                results.jsonl (tracked, starts empty) + per-run logs and patches (ignored)
  .cache/              composer / npm caches shared across runs (ignored)
```

## Protocol (one run)

Requirements on the experiment host: bash, git, tar, docker, awk, sed, grep, and a
**local clone of the private `PegaFila/PegaFilaWeb`** (read access required) that
contains every task's base and solution commits. Fetch everything there
(`git -C ../PegaFilaWeb fetch --all`), including the unmerged `feat/42-*` and
`feat/46-*` branches: the held-out tasks live on them. The scripts never modify
that clone; they only run `git archive|show|cat-file|rev-parse` against it.

Layout assumption: this repository and `PegaFilaWeb` are cloned side by side. If
the clone lives elsewhere, point `PF_REPO` at it:

```bash
export PF_REPO=/path/to/PegaFilaWeb     # default: <this repo>/../PegaFilaWeb
```

```bash
# once
benchmark/bin/build-image.sh                      # -> pf-bench:tcc-baseline-v1
benchmark/bin/list-tasks.sh                       # the default set (status: ready)

# per run (harness defaults to the vendored benchmark/harness/v1;
#          --harness <v> picks another snapshot, --tag <ref> reads it from PF_REPO)
# (loop over `benchmark/bin/list-tasks.sh --ids` x levels x repetitions)
benchmark/bin/prepare-task.sh T06-issue-ticket skills
#   -> benchmark/work/T06-issue-ticket__skills__<ts>/   (tree, tag bench/start)
#   -> benchmark/work/T06-issue-ticket__skills__<ts>.prompt.md
#   -> benchmark/work/T06-issue-ticket__skills__<ts>.meta

# run the agent under test inside the tree with the prompt as its task.
# Example shape (adapt to your agent's CLI; record tokens/turns/time yourself):
#   cd benchmark/work/T06-issue-ticket__skills__<ts>
#   <agent> --model <model> "$(cat ../T06-issue-ticket__skills__<ts>.prompt.md)"
#   echo '{"tokens_in":..,"tokens_out":..,"turns":..,"wall_s":..}' > /tmp/m.json

benchmark/bin/evaluate.sh benchmark/work/T06-issue-ticket__skills__<ts> \
  --agent opencode --model opencode-go/muse-spark-1.3-contributor --agent-metrics /tmp/m.json
```

What `prepare-task.sh` guarantees:

- the task commits are read from `PF_REPO`; tasks, runs and caches live in this
  repository; the harness level comes from `benchmark/harness/<version>`; the
  `.meta` file and the JSON result line record it as `harness` (`v1`, or the ref
  given with `--tag`);
- the tree is a **fresh git repository** holding only the base commit, so the
  agent cannot reach the solution through history, other branches or tags;
  `.github/` is left out (`export-ignore`), `CHANGELOG.md` is put back because
  the rules ask for an entry;
- the harness is **committed separately** and tagged `bench/start`, so the
  agent's diff never includes harness files;
- the prompt and metadata live **beside** the tree, not inside it.

What `evaluate.sh` does, in order: stages everything the agent left (so
untracked files count), records the diff and violations, copies the hidden
tests from the solution commit (overwriting any same-named file the agent
wrote — recorded as `hidden_test_collisions`), builds assets in a Node
container, then in the grading image runs `composer install`, Pint, the full
suite and the hidden tests alone. Tests use SQLite in memory (`phpunit.xml`),
so no database service is needed. Logs, the agent's patch and `result.json`
go to `runs/<run-id>/`.

Should the agent be able to run tests while working? That is part of the
condition. The exported tree still contains `bin/pf` and `docker/`, so an
agent with Docker can run `./bin/pf shell php artisan test` exactly as
`AGENTS.md` instructs. Keep it the same across conditions.

## Task schema (`tasks/<id>.yaml`)

The scripts parse the file with grep/awk, so keep the shape: top-level scalars
on one line, lists as `  - item`, blocks as `key: |` with two-space indent.

```yaml
id: T06-issue-ticket
title: Ticket issuance domain action
tier: small | medium | large          # by non-test files in the solution
category: ops | auth | tenancy | domain | livewire-ui | api
source_pr: 33                          # or null
source_branch: feat/14-issue-ticket-v2
source_issue: 14                       # or null
held_out: false                        # true = solution is an unmerged branch
status: ready | composite              # composite = large parent kept for reference, not in the default set
parent_task: null                      # id of the parent when this is a scoped subtask
base_commit: <sha>                     # tree the agent starts from
solution_commit: <sha>                 # where hidden tests are copied from
solution_stats: 14 files changed, 520 insertions(+), 3 deletions(-)
hidden_tests:                          # tests/ paths added or modified by the solution
  - tests/Feature/IssueTicketTest.php
solution_files:                        # non-test files of the reference solution (informational)
  - app/Actions/IssueTicket.php
statement: |                           # what the agent receives, verbatim
  ...
notes: |                               # for the experimenter: pitfalls, coupling, fairness
  ...
```

The statement must carry the **public contract** the hidden tests depend on
(class names, methods, enums, factories, routes, config keys, lang keys), or
the task measures name-guessing rather than engineering. The `notes` block
records where that coupling is tight.

**Default task set** = every file with `status: ready`
(`benchmark/bin/list-tasks.sh`). Large PRs whose history offers no usable
intermediate commit are kept as `status: composite` and split into
**subtasks** that share the parent's base and solution commits but grade only
a separable subset of its tests, with a statement scoped to that subset
(`parent_task` points back). Run composites only if you want the whole-PR
condition; they are too coupled to markup and literal text to be fair items
on their own.

Subtasks of one parent are **not independent observations**: `T04b` and
`T04c` both include `T04a`'s tests (grading is per test file, so a model
failure fails all three), and `T03a`/`T03b` share the password-reset and
verification routes. Aggregate per parent, or read `tests-hidden.log` per
file, before treating them as separate samples.

### Grading rules worth knowing

- **Tests the reference itself modified are not violations.** Several
  solutions legitimately break pre-existing tests (e.g. a new ticket code
  format). Those files are in `hidden_tests` with status M and are overwritten
  at grading time, so `violations.tests_touched` ignores them; it only counts
  deletions/edits of other pre-existing tests.
- **New dependencies.** If the agent changed `composer.json`, `evaluate.sh`
  runs `composer update` instead of `composer install` (the agent usually has
  no PHP to refresh the lock file) and records `composer.mode = "update"`.
  Grading therefore needs network access to Packagist in both modes.
- **Hidden test collisions.** If the agent wrote a file at a hidden test's
  path, the hidden version replaces it; the path is recorded in
  `hidden_test_collisions` so you can inspect the agent's own test in
  `runs/<run-id>/agent.patch`.

## Adding a task from a PR

1. `M=<merge commit>`; base is `M^1`, solution is `M` (for an unmerged branch:
   base is `git merge-base main <branch>`, solution is the branch tip).
2. `git diff --name-status $M^1 $M` → `hidden_tests` (paths under `tests/`
   with A or M) and `solution_files`.
3. Read the hidden tests at the solution commit and write the statement with
   the contract they require. Never paste the solution.
4. `git diff --shortstat $M^1 $M` → `solution_stats`; pick `tier` by non-test
   file count (≤10 small, 11–25 medium, >25 large).

## Redaction

The public copy is redacted (secrets, infrastructure identifiers, third-party
account ids, personal data, commercial data; see [`REDACTIONS.md`](REDACTIONS.md)).
Redaction never touches a name a hidden test depends on, so task semantics
(`base_commit`, `solution_commit`, `hidden_tests`, `solution_files`, the
"Contract" sections) are unchanged from the private source.

## Threats to validity (record in the thesis)

- **Ground truth is partly AI-authored.** About 15% of the subject repository's
  commits are traceable to Cursor, Codebuff or the OpenCode review bot; the
  hidden tests themselves were sometimes written with AI assistance.
- **Hidden tests couple to names.** A correct implementation with different
  class/method names fails. The statement's contract mitigates this; residual
  coupling is listed per task in `notes`.
- **SQLite vs MariaDB.** The suite runs on SQLite in memory; pessimistic
  locks in `CallNextTicket` are not exercised as in production.
- **Harness drift.** Tasks come from different points in the subject repository's
  history, but all runs use the `v1` harness (`tcc-baseline-v1`). Older bases may
  contain code that the current rules would have written differently.
- **Small N.** Fourteen tasks in the default set (nine whole PRs/branches
  plus five scoped subtasks of the two composites) at four levels is enough
  for effect direction, not for fine-grained significance; repeat runs per
  cell, and remember that subtasks of one parent are correlated.
- **Base tests that a correct change must break.** In T02, T05, T08, T09 and T11
  the reference solution had to edit pre-existing tests. The agent sees them
  fail and may edit them too; those files are hidden tests (status M) and are
  excluded from `violations.tests_touched`, but the agent's time spent on them
  is still part of the condition.
- **Runner effects.** Model, tool version, temperature and the agent's
  ability to run tests must be identical across levels within a comparison;
  record them in `--agent`, `--model` and `--agent-metrics`.
