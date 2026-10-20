#!/bin/bash
# run_arm.sh <case_id> <arm> [extra validate_patch args]
# Runs upstream validate_patch for one calibration arm. No LLM involved.
# Env: CCB_ROOT (default ~/ccb) holds upstream/ (1cb7410), venv/, bin/forge shim, arms/, runs/.
set -u
ROOT="${CCB_ROOT:-$HOME/ccb}"
CASE="$1"; ARM="$2"; shift 2
export PATH="$ROOT/bin:$PATH" ETH_RPC_URL="${ETH_RPC_URL:-https://eth.drpc.org}" PYTHONPATH=src
OUT="$ROOT/runs/$CASE/$ARM"
rm -rf "$OUT"; mkdir -p "$OUT"
cd "$ROOT/upstream" || exit 2
"$ROOT/venv/bin/python" src/infra/cli/validate_patch.py --case-id "$CASE" \
  --fixed-path "$ROOT/arms/$CASE/$ARM.sol" --artifact-dir "$OUT" --base-dir . \
  "$@" > "$OUT/stdout.json" 2> "$OUT/stderr.log"
echo "rc=$?" > "$OUT/rc.txt"
cat "$OUT/rc.txt"
