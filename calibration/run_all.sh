#!/bin/bash
# run_all.sh <case ids...>  - three arms per case, sequential; log to runs/_all.log
ROOT="${CCB_ROOT:-$HOME/ccb}"
for c in "$@"; do
  for arm in unchanged revert emit_only; do
    echo "$(date +%H:%M:%S) bench-$c $arm" >> "$ROOT/runs/_all.log"
    "$ROOT/audit/calibration/run_arm.sh" "bench-$c" "$arm" >> "$ROOT/runs/_all.log" 2>&1
  done
done
echo "DONE $(date +%H:%M:%S)" >> "$ROOT/runs/_all.log"
