#!/usr/bin/env bash
# Shared helpers for the benchmark scripts. Source it; do not run it.

# BENCH_ROOT: this (public) thesis repository. PF_REPO: local clone of the private subject
# repository (PegaFila/PegaFilaWeb) that holds the task commits.
BENCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PF_REPO="${PF_REPO:-$BENCH_ROOT/../PegaFilaWeb}"
BENCH_DIR="$BENCH_ROOT/benchmark"
BENCH_HARNESS="$BENCH_DIR/harness"
BENCH_TASKS="$BENCH_DIR/tasks"
BENCH_WORK="$BENCH_DIR/work"
BENCH_RUNS="$BENCH_DIR/runs"
BENCH_CACHE="${BENCH_CACHE:-$BENCH_DIR/.cache}"   # overridable: one cache per parallel grader
BENCH_DEFAULT_TAG="tcc-baseline-v1"
BENCH_DEFAULT_HARNESS="v1"

die() { echo "error: $*" >&2; exit 1; }

git -C "$PF_REPO" rev-parse --git-dir >/dev/null 2>&1 \
  || die "PF_REPO is not a git repository: $PF_REPO (clone PegaFila/PegaFilaWeb next to this repo or set PF_REPO)"

task_file() {
  local id="$1"
  local f="$BENCH_TASKS/$id.yaml"
  [[ -f "$f" ]] || die "task not found: $f"
  echo "$f"
}

# yaml_scalar <file> <key>  -> single-line top-level scalar
yaml_scalar() {
  grep -E "^$2:" "$1" | head -n1 | sed -E 's/^[^:]+:[[:space:]]*//' | sed -E 's/[[:space:]]+#.*$//'
}

# yaml_list <file> <key>  -> items of a top-level "  - item" list, one per line
yaml_list() {
  awk -v key="$2" '
    $0 ~ "^"key":" { inlist=1; next }
    inlist && /^  - / { sub(/^  - /, ""); print; next }
    inlist && !/^  / { inlist=0 }
  ' "$1"
}

# yaml_block <file> <key>  -> contents of a top-level "key: |" block, dedented
yaml_block() {
  awk -v key="$2" '
    $0 ~ "^"key": \\|" { inblock=1; next }
    inblock && /^  / { sub(/^  /, ""); print; next }
    inblock && /^$/ { print ""; next }
    inblock { inblock=0 }
  ' "$1"
}

# json_str <string> -> JSON string literal (escapes backslash, quote, newline, tab)
json_str() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '"%s"' "$s"
}

# json_num_or_null <value> -> number literal or null
json_num_or_null() {
  if [[ "${1:-}" =~ ^-?[0-9]+$ ]]; then printf '%s' "$1"; else printf 'null'; fi
}

# json_list <item...> -> JSON array of strings
json_list() {
  local out="[" first=1 item
  for item in "$@"; do
    [[ $first -eq 1 ]] || out+=","
    out+="$(json_str "$item")"; first=0
  done
  printf '%s]' "$out"
}

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
now_id() { date -u +%Y%m%d-%H%M%S; }
