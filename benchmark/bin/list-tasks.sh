#!/usr/bin/env bash
# List benchmark tasks. By default only the default set (status: ready); --all includes composites.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

ALL=0; IDS_ONLY=0
for a in "$@"; do
  case "$a" in
    --all) ALL=1 ;;
    --ids) IDS_ONLY=1 ;;
    -h|--help) echo "Usage: benchmark/bin/list-tasks.sh [--all] [--ids]"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

[[ $IDS_ONLY -eq 1 ]] || printf '%-28s %-6s %-11s %-9s %-24s %s\n' ID TIER CATEGORY STATUS PARENT HIDDEN
for f in "$BENCH_TASKS"/*.yaml; do
  status="$(yaml_scalar "$f" status)"; status="${status:-ready}"
  [[ $ALL -eq 1 || "$status" == "ready" ]] || continue
  id="$(yaml_scalar "$f" id)"
  if [[ $IDS_ONLY -eq 1 ]]; then echo "$id"; continue; fi
  parent="$(yaml_scalar "$f" parent_task)"
  printf '%-28s %-6s %-11s %-9s %-24s %s\n' "$id" "$(yaml_scalar "$f" tier)" "$(yaml_scalar "$f" category)" \
    "$status" "${parent:-null}" "$(yaml_list "$f" hidden_tests | wc -l | tr -d ' ')"
done
