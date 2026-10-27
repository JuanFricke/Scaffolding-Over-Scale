#!/usr/bin/env bash
# Apply (or strip) the PegaFila agent harness in a working tree at one ablation level.
#
# The harness is always taken from ONE snapshot: by default the vendored copy in
# benchmark/harness/<version> (default v1); alternatively --tag <ref> reads it from the
# private subject repository (PF_REPO). Either way every task gets the same harness
# regardless of what its base commit shipped. Running it on a tree is idempotent:
# everything is stripped first, then the requested level is applied.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: benchmark/bin/apply-harness.sh <workdir> <level> [--harness <version> | --tag <ref>]

Levels (cumulative):
  none     strip every harness artifact                       (control condition)
  agents   AGENTS.md + CLAUDE.md                              (always-on rules only)
  skills   agents + ai/  (skills, commands, rules, templates) (on-demand reading)
  full     skills + opencode.json (instructions + LSP) + .claude/settings.json

Options:
  --harness <v> vendored snapshot benchmark/harness/<v> (default: v1)
  --tag <ref>   read the harness from git ref <ref> of PF_REPO instead (e.g. tcc-baseline-v1)
  -h, --help    this text
EOF
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PF_REPO="${PF_REPO:-$HERE/../PegaFilaWeb}"
HARNESS_DIR="$HERE/benchmark/harness"
HARNESS="v1"
TAG=""

[[ $# -ge 2 ]] || { usage >&2; exit 2; }
WORK="$1"; LEVEL="$2"; shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --harness) HARNESS="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$LEVEL" in none|agents|skills|full) ;; *) echo "invalid level: $LEVEL" >&2; usage >&2; exit 2 ;; esac
[[ -d "$WORK" ]] || { echo "workdir not found: $WORK" >&2; exit 2; }
if [[ -n "$TAG" ]]; then
  git -C "$PF_REPO" rev-parse --verify --quiet "${TAG}^{commit}" >/dev/null \
    || { echo "harness ref not found in $PF_REPO: $TAG" >&2; exit 2; }
  SRC="$TAG"
else
  [[ -d "$HARNESS_DIR/$HARNESS" ]] || { echo "harness snapshot not found: $HARNESS_DIR/$HARNESS" >&2; exit 2; }
  SRC="$HARNESS"
fi

# Every artifact an agent could load as instructions. Keep in sync with README.md.
HARNESS_FILES=(AGENTS.md CLAUDE.md opencode.json .claude/settings.json)
HARNESS_DIRS=(ai .claude .cursor)

show() {
  if [[ -n "$TAG" ]]; then git -C "$PF_REPO" show "${TAG}:$1"; else cat "$HARNESS_DIR/$HARNESS/$1"; fi
}

strip_all() {
  local f d
  for f in "${HARNESS_FILES[@]}"; do rm -f "$WORK/$f"; done
  for d in "${HARNESS_DIRS[@]}"; do rm -rf "${WORK:?}/$d"; done
}

apply_agents() {
  show AGENTS.md > "$WORK/AGENTS.md"
  show CLAUDE.md > "$WORK/CLAUDE.md"
}

apply_skills() {
  if [[ -n "$TAG" ]]; then
    git -C "$PF_REPO" archive "$TAG" ai | tar -x -C "$WORK"
  else
    cp -R "$HARNESS_DIR/$HARNESS/ai" "$WORK/ai"
  fi
}

apply_full() {
  show opencode.json > "$WORK/opencode.json"
  mkdir -p "$WORK/.claude"
  show .claude/settings.json > "$WORK/.claude/settings.json"
}

strip_all
case "$LEVEL" in
  none) ;;
  agents) apply_agents ;;
  skills) apply_agents; apply_skills ;;
  full) apply_agents; apply_skills; apply_full ;;
esac

echo "harness level '$LEVEL' applied from $SRC in $WORK"
