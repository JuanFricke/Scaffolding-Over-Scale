#!/usr/bin/env bash
# Materialize one benchmark task as an isolated working tree the agent can work in.
#
#   1. exports the task's base commit (no history, no sibling branches, no benchmark/)
#   2. initializes a fresh git repo there and commits the base
#   3. strips every harness artifact and applies the requested ablation level
#      from the harness snapshot, committed separately and tagged bench/start
#   4. writes the task statement next to the tree (<workdir>.prompt.md) and a
#      metadata file (<workdir>.meta) that evaluate.sh reads back
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

usage() {
  cat <<'EOF'
Usage: benchmark/bin/prepare-task.sh <task-id> <level> [--out <dir>] [--harness <v> | --tag <ref>] [--force]

  <task-id>   file name in benchmark/tasks/ without .yaml (e.g. T06-issue-ticket)
  <level>     none | agents | skills | full   (see apply-harness.sh)
  --out       target directory (default: benchmark/work/<task>__<level>__<utc-timestamp>)
  --harness   vendored harness snapshot benchmark/harness/<v> (default: v1)
  --tag       read the harness from git ref <ref> of PF_REPO instead of the vendored copy
  --force     reuse --out even if it exists (it is wiped first)

Afterwards, run your agent inside the working tree with the prompt file as the
task, then grade with benchmark/bin/evaluate.sh <workdir>.
EOF
}

[[ $# -ge 2 ]] || { usage >&2; exit 2; }
TASK_ID="$1"; LEVEL="$2"; shift 2
OUT=""; HARNESS="$BENCH_DEFAULT_HARNESS"; TAG=""; FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --harness) HARNESS="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

TASK="$(task_file "$TASK_ID")"
BASE="$(yaml_scalar "$TASK" base_commit)"
[[ -n "$BASE" ]] || die "base_commit missing in $TASK"
STATUS="$(yaml_scalar "$TASK" status)"
PARENT="$(yaml_scalar "$TASK" parent_task)"
if [[ "$STATUS" == "composite" ]]; then
  echo "warning: $TASK_ID is a composite (whole-PR) task; the default set uses its subtasks (see benchmark/README.md)" >&2
fi
HARNESS_LABEL="${TAG:-$HARNESS}"
HARNESS_OPT=(--harness "$HARNESS"); [[ -z "$TAG" ]] || HARNESS_OPT=(--tag "$TAG")
git -C "$PF_REPO" cat-file -e "${BASE}^{commit}" 2>/dev/null || die "base commit not in repo: $BASE (fetch first)"

[[ -n "$OUT" ]] || OUT="$BENCH_WORK/${TASK_ID}__${LEVEL}__$(now_id)"
if [[ -e "$OUT" ]]; then
  [[ $FORCE -eq 1 ]] || die "exists: $OUT (use --force to wipe it)"
  rm -rf "$OUT"
fi
mkdir -p "$OUT"

# 1. export the base commit only (git archive never includes other refs or benchmark/ of today).
#    .gitattributes marks CHANGELOG.md and .github/ as export-ignore; the agent rules ask for a
#    changelog entry, so put CHANGELOG.md back. CI workflows stay out on purpose.
git -C "$PF_REPO" archive "$BASE" | tar -x -C "$OUT"
rm -rf "$OUT/benchmark"
if git -C "$PF_REPO" cat-file -e "${BASE}:CHANGELOG.md" 2>/dev/null; then
  git -C "$PF_REPO" show "${BASE}:CHANGELOG.md" > "$OUT/CHANGELOG.md"
fi

# 2. fresh repository so the agent can commit but cannot see the solution
git -C "$OUT" init -q
git -C "$OUT" -c user.name=bench -c user.email=bench@local add -A
git -C "$OUT" -c user.name=bench -c user.email=bench@local commit -q -m "base ${BASE:0:12}"

# 3. harness at the requested level, as its own commit, so the agent's diff excludes it
"$BENCH_DIR/bin/apply-harness.sh" "$OUT" "$LEVEL" "${HARNESS_OPT[@]}" >/dev/null
git -C "$OUT" -c user.name=bench -c user.email=bench@local add -A
git -C "$OUT" -c user.name=bench -c user.email=bench@local commit -q --allow-empty -m "harness: $LEVEL ($HARNESS_LABEL)"
git -C "$OUT" tag bench/start

# 4. prompt + metadata beside the tree (never inside it)
yaml_block "$TASK" statement > "$OUT.prompt.md"
cat > "$OUT.meta" <<EOF
task=$TASK_ID
level=$LEVEL
base_commit=$BASE
harness=$HARNESS_LABEL
status=${STATUS:-ready}
parent_task=${PARENT:-null}
created=$(now_iso)
EOF

cat <<EOF
prepared  $OUT
task      $TASK_ID  ($(yaml_scalar "$TASK" title))  status=${STATUS:-ready} parent=${PARENT:-null}
level     $LEVEL  (harness $HARNESS_LABEL)
base      ${BASE:0:12}
prompt    $OUT.prompt.md

Next: run your agent in '$OUT' with the prompt, then
      benchmark/bin/evaluate.sh "$OUT" --agent <name> --model <model>
EOF
