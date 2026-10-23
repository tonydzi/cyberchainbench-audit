#!/bin/bash
# run_wave2.sh <case ids without "bench-" prefix...>
# Same three arms as run_all.sh. A case with a null proxy_address gets the key removed through
# --benchmark-dir (cases-fixed/), the workaround first used for bench-559.
ROOT="${CCB_ROOT:-$HOME/ccb}"
for c in "$@"; do
  for arm in unchanged revert emit_only; do
    echo "$(date +%H:%M:%S) bench-$c $arm" >> "$ROOT/runs/_wave2.log"
    extra=()
    [ -f "$ROOT/cases-fixed/bench-$c.json" ] && extra=(--benchmark-dir "$ROOT/cases-fixed")
    "$ROOT/audit/calibration/run_arm.sh" "bench-$c" "$arm" "${extra[@]}" >> "$ROOT/runs/_wave2.log" 2>&1
  done
done
echo "DONE $(date +%H:%M:%S)" >> "$ROOT/runs/_wave2.log"
