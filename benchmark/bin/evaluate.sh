#!/usr/bin/env bash
# Grade an agent's work on a prepared task tree and append one JSON line to
# benchmark/runs/results.jsonl. Logs and the agent's patch go to benchmark/runs/<run-id>/.
#
# Metrics
#   diff        files / insertions / deletions of the agent's change vs. bench/start
#   violations  harness rules the change breaks (tests deleted or modified,
#               harness files edited, unescaped {!! !!} output introduced)
#   pint        ./vendor/bin/pint --test exit code
#   tests_full  whole suite (pre-existing + hidden) after hidden tests are copied in
#   tests_hidden only the task's hidden tests
#   regressions failures outside the hidden tests (tests_full.failed - tests_hidden.failed)
#   agent       free-form metrics file your runner wrote (tokens, turns, wall time...)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

usage() {
  cat <<'EOF'
Usage: benchmark/bin/evaluate.sh <workdir> [options]

  <workdir>              tree produced by prepare-task.sh (its .meta file must sit beside it)
  --run-id <id>          default: <task>__<level>__<utc-timestamp>
  --image <img>          evaluation image (default: pf-bench:tcc-baseline-v1, see build-image.sh)
  --node-image <img>     image for the asset build (default: node:22-alpine)
  --agent <name>         agent/tool under test, recorded as-is (e.g. opencode, claude-code)
  --model <name>         model id, recorded as-is
  --agent-metrics <json> file with a JSON object your runner produced; embedded verbatim
  --skip-assets          do not run npm install/build (only if the base needs no Vite manifest)
  --timeout <sec>        per-container timeout (default: 1800)

Requires: docker, git, awk, tar. Tests run on SQLite in memory (phpunit.xml), so no
database service is started.
EOF
}

[[ $# -ge 1 ]] || { usage >&2; exit 2; }
WORK="$1"; shift
RUN_ID=""; IMAGE=""; NODE_IMAGE="node:22-alpine"; AGENT=""; MODEL=""; METRICS=""; SKIP_ASSETS=0; TIMEOUT=1800
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --node-image) NODE_IMAGE="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --agent-metrics) METRICS="$2"; shift 2 ;;
    --skip-assets) SKIP_ASSETS=1; shift ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

WORK="$(cd "$WORK" && pwd)"
META="$WORK.meta"
[[ -f "$META" ]] || die "metadata not found: $META (was the tree made by prepare-task.sh?)"
meta() { grep -E "^$1=" "$META" | head -n1 | cut -d= -f2-; }
TASK_ID="$(meta task)"; LEVEL="$(meta level)"; HARNESS="$(meta harness)"; BASE="$(meta base_commit)"
TASK="$(task_file "$TASK_ID")"
SOLUTION="$(yaml_scalar "$TASK" solution_commit)"
[[ -n "$SOLUTION" ]] || die "solution_commit missing in $TASK"
git -C "$PF_REPO" cat-file -e "${SOLUTION}^{commit}" 2>/dev/null || die "solution commit not in repo: $SOLUTION (fetch the branch first)"
command -v docker >/dev/null || die "docker not found"
# the image is built from a PF_REPO ref: the default tag for vendored snapshots, else the --tag ref
IMAGE_TAG="$BENCH_DEFAULT_TAG"; [[ -d "$BENCH_HARNESS/$HARNESS" ]] || IMAGE_TAG="$HARNESS"
[[ -n "$IMAGE" ]] || IMAGE="pf-bench:$IMAGE_TAG"
docker image inspect "$IMAGE" >/dev/null 2>&1 || die "image $IMAGE not found; run benchmark/bin/build-image.sh $IMAGE_TAG"
git -C "$WORK" rev-parse --verify --quiet bench/start >/dev/null || die "tag bench/start missing in $WORK"

[[ -n "$RUN_ID" ]] || RUN_ID="${TASK_ID}__${LEVEL}__$(now_id)"
RUN_DIR="$BENCH_RUNS/$RUN_ID"
mkdir -p "$RUN_DIR" "$BENCH_CACHE/composer" "$BENCH_CACHE/npm"
STARTED="$(now_iso)"

# --- 1. the agent's change -----------------------------------------------------
git -C "$WORK" -c user.name=bench -c user.email=bench@local add -A
git -C "$WORK" diff --cached bench/start > "$RUN_DIR/agent.patch"
git -C "$WORK" diff --cached --numstat bench/start > "$RUN_DIR/agent.numstat"
read -r DIFF_FILES DIFF_INS DIFF_DEL < <(awk '{f++; if ($1!="-") i+=$1; if ($2!="-") d+=$2} END {print f+0, i+0, d+0}' "$RUN_DIR/agent.numstat")

mapfile -t HIDDEN < <(yaml_list "$TASK" hidden_tests)
[[ ${#HIDDEN[@]} -gt 0 ]] || die "no hidden_tests in $TASK"
printf '%s\n' "${HIDDEN[@]}" > "$RUN_DIR/hidden-tests.txt"

# Deleting or editing a pre-existing test is a harness violation, EXCEPT for test files the
# reference solution itself modified (they are in hidden_tests and get overwritten anyway):
# a correct change legitimately breaks those, so touching them is not cheating.
mapfile -t TESTS_TOUCHED < <(git -C "$WORK" diff --cached --name-status bench/start -- tests \
  | awk '$1 ~ /^(D|M)/ {print $1":"$2}' \
  | grep -vxF -f <(for t in "${HIDDEN[@]}"; do printf 'D:%s\nM:%s\n' "$t" "$t"; done) || true)
mapfile -t HARNESS_TOUCHED < <(git -C "$WORK" diff --cached --name-status bench/start -- AGENTS.md CLAUDE.md opencode.json ai .claude .cursor | awk '{print $1":"$NF}')
UNESCAPED="$(grep -cE '^\+.*\{!!' "$RUN_DIR/agent.patch" || true)"
AGENT_COMMITS="$(git -C "$WORK" rev-list --count bench/start..HEAD)"
COMPOSER_CHANGED=0
git -C "$WORK" diff --cached --quiet bench/start -- composer.json || COMPOSER_CHANGED=1

# --- 2. hidden tests from the solution commit ----------------------------------
COLLISIONS=()
for t in "${HIDDEN[@]}"; do
  if git -C "$WORK" diff --cached --name-only bench/start -- "$t" | grep -q .; then COLLISIONS+=("$t"); fi
  mkdir -p "$WORK/$(dirname "$t")"
  git -C "$PF_REPO" show "${SOLUTION}:$t" > "$WORK/$t"
done

# --- 3. containers --------------------------------------------------------------
UIDGID="$(id -u):$(id -g)"
run_in() { # run_in <image> <script>
  timeout "$TIMEOUT" docker run --rm --user "$UIDGID" \
    -e HOME=/tmp -e COMPOSER_HOME=/tmp/composer -e COMPOSER_CACHE_DIR=/cache/composer \
    -e npm_config_cache=/cache/npm -e CI=1 \
    -v "$WORK:/var/www/html" -v "$BENCH_CACHE:/cache" -v "$RUN_DIR:/bench-out" \
    -w /var/www/html "$1" sh -c "$2"
}

ASSETS_EXIT=0
if [[ $SKIP_ASSETS -eq 0 ]]; then
  run_in "$NODE_IMAGE" 'npm install --ignore-scripts --no-audit --no-fund > /bench-out/assets.log 2>&1 && npm run build >> /bench-out/assets.log 2>&1' || ASSETS_EXIT=$?
fi

HIDDEN_ARGS="$(printf '%q ' "${HIDDEN[@]}")"
# If the agent changed composer.json (new dependency) it usually could not refresh composer.lock
# (no PHP on its side); `composer install` would then ignore the new package and every test
# would fail for the wrong reason. Resolve the lock in that case and record which mode ran.
COMPOSER_CMD="composer install --no-interaction --prefer-dist --no-progress --no-ansi"
COMPOSER_MODE="install"
if [[ $COMPOSER_CHANGED -eq 1 ]]; then
  COMPOSER_CMD="composer update --no-interaction --prefer-dist --no-progress --no-ansi"
  COMPOSER_MODE="update"
fi
run_in "$IMAGE" "
  set +e
  $COMPOSER_CMD > /bench-out/composer.log 2>&1; echo \$? > /bench-out/composer.exit
  [ -f .env ] || cp .env.example .env
  php artisan key:generate --force --no-ansi -q >> /bench-out/composer.log 2>&1
  ./vendor/bin/pint --test --no-ansi > /bench-out/pint.log 2>&1; echo \$? > /bench-out/pint.exit
  php artisan test --compact --no-ansi > /bench-out/tests-full.log 2>&1; echo \$? > /bench-out/tests-full.exit
  php artisan test --compact --no-ansi $HIDDEN_ARGS > /bench-out/tests-hidden.log 2>&1; echo \$? > /bench-out/tests-hidden.exit
" || echo "$?" > "$RUN_DIR/container.exit"

exit_of() { [[ -f "$RUN_DIR/$1.exit" ]] && cat "$RUN_DIR/$1.exit" || echo ""; }
# Pest summary: "Tests:    3 failed, 299 passed (1500 assertions)" / "Tests:    302 passed (...)"
count_in() { grep -E '^\s*Tests:' "$RUN_DIR/$1.log" 2>/dev/null | tail -n1 | grep -oE "[0-9]+ $2" | awk '{print $1}'; }
FULL_PASSED="$(count_in tests-full passed)"; FULL_FAILED="$(count_in tests-full failed)"
HID_PASSED="$(count_in tests-hidden passed)"; HID_FAILED="$(count_in tests-hidden failed)"
[[ -n "$FULL_PASSED" && -z "$FULL_FAILED" ]] && FULL_FAILED=0
[[ -n "$HID_PASSED" && -z "$HID_FAILED" ]] && HID_FAILED=0
REGRESSIONS=""
[[ -n "$FULL_FAILED" && -n "$HID_FAILED" ]] && REGRESSIONS=$(( FULL_FAILED - HID_FAILED ))
HIDDEN_OK="false"
[[ "$(exit_of tests-hidden)" == "0" ]] && HIDDEN_OK="true"

AGENT_METRICS="null"
if [[ -n "$METRICS" ]]; then
  [[ -f "$METRICS" ]] || die "agent metrics file not found: $METRICS"
  # one JSON object, collapsed to a single line so results.jsonl stays one record per line
  AGENT_METRICS="$(tr -d '\n\r' < "$METRICS")"
  [[ "$AGENT_METRICS" == \{* ]] || die "agent metrics must be a JSON object: $METRICS"
  cp "$METRICS" "$RUN_DIR/agent-metrics.json"
fi

# --- 4. one JSON line -----------------------------------------------------------
LINE="{\"run_id\":$(json_str "$RUN_ID"),\"task\":$(json_str "$TASK_ID"),\"level\":$(json_str "$LEVEL"),\"harness\":$(json_str "$HARNESS"),\"base_commit\":$(json_str "$BASE"),\"solution_commit\":$(json_str "$SOLUTION"),\"agent\":$(json_str "$AGENT"),\"model\":$(json_str "$MODEL"),\"image\":$(json_str "$IMAGE"),\"started\":$(json_str "$STARTED"),\"finished\":$(json_str "$(now_iso)")"
LINE+=",\"diff\":{\"files\":$DIFF_FILES,\"insertions\":$DIFF_INS,\"deletions\":$DIFF_DEL,\"commits\":$AGENT_COMMITS}"
LINE+=",\"violations\":{\"tests_touched\":$(json_list ${TESTS_TOUCHED[@]+"${TESTS_TOUCHED[@]}"}),\"harness_touched\":$(json_list ${HARNESS_TOUCHED[@]+"${HARNESS_TOUCHED[@]}"}),\"unescaped_output_added\":$UNESCAPED}"
LINE+=",\"hidden_test_collisions\":$(json_list ${COLLISIONS[@]+"${COLLISIONS[@]}"})"
LINE+=",\"assets\":{\"skipped\":$([[ $SKIP_ASSETS -eq 1 ]] && echo true || echo false),\"exit\":$ASSETS_EXIT}"
LINE+=",\"composer\":{\"mode\":$(json_str "$COMPOSER_MODE"),\"json_changed\":$([[ $COMPOSER_CHANGED -eq 1 ]] && echo true || echo false),\"exit\":$(json_num_or_null "$(exit_of composer)")}"
LINE+=",\"pint\":{\"ok\":$([[ "$(exit_of pint)" == "0" ]] && echo true || echo false),\"exit\":$(json_num_or_null "$(exit_of pint)")}"
LINE+=",\"tests_full\":{\"passed\":$(json_num_or_null "$FULL_PASSED"),\"failed\":$(json_num_or_null "$FULL_FAILED"),\"exit\":$(json_num_or_null "$(exit_of tests-full)")}"
LINE+=",\"tests_hidden\":{\"passed\":$(json_num_or_null "$HID_PASSED"),\"failed\":$(json_num_or_null "$HID_FAILED"),\"exit\":$(json_num_or_null "$(exit_of tests-hidden)"),\"ok\":$HIDDEN_OK}"
LINE+=",\"regressions\":$(json_num_or_null "$REGRESSIONS")"
LINE+=",\"agent_metrics\":$AGENT_METRICS}"

printf '%s\n' "$LINE" > "$RUN_DIR/result.json"
printf '%s\n' "$LINE" >> "$BENCH_RUNS/results.jsonl"

cat <<EOF
run       $RUN_ID
task      $TASK_ID  level=$LEVEL  agent=${AGENT:-?}  model=${MODEL:-?}
diff      $DIFF_FILES files, +$DIFF_INS -$DIFF_DEL, $AGENT_COMMITS commits
hidden    ok=$HIDDEN_OK  passed=${HID_PASSED:-?} failed=${HID_FAILED:-?}
full      passed=${FULL_PASSED:-?} failed=${FULL_FAILED:-?}  regressions=${REGRESSIONS:-?}
pint      exit=$(exit_of pint)   composer=$COMPOSER_MODE   violations: tests=${#TESTS_TOUCHED[@]} harness=${#HARNESS_TOUCHED[@]} unescaped=$UNESCAPED
logs      $RUN_DIR
EOF
