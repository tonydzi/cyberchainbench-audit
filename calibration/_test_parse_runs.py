#!/usr/bin/env python3
"""Red-first proof for parse_runs.py: parser must change its answer / raise on damaged logs.

usage: _test_parse_runs.py <runs_dir>   (needs runs/bench-391/{unchanged,revert,emit_only})
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parse_runs as P  # noqa: E402

runs = Path(sys.argv[1])
case = "bench-391"
tmp = Path(tempfile.mkdtemp())
shutil.copytree(runs / case, tmp / case)
fails = 0


def check(name, ok):
    global fails
    print(("ok  " if ok else "FAIL"), name)
    fails += 0 if ok else 1


def atk(arm):
    return next((tmp / case / arm).glob("attack_tx_replay_cli/*/forge_output.txt"))


def nrm(arm):
    return next((tmp / case / arm).glob("normal_tx_replay/*/forge_output.txt"))


# baseline on real logs
b = {a: P.parse_run(tmp / case / a) for a in ("unchanged", "revert", "emit_only")}
check("baseline unchanged not blocked", b["unchanged"]["exploit_blocked"] is False)
check("baseline revert blocked", b["revert"]["exploit_blocked"] is True)
check("baseline emit_only blocked AND profit retained", b["emit_only"]["exploit_blocked"] and b["emit_only"]["profit_retained"])

# 1. remove the BLOCKED marker from emit_only -> PASS without marker must raise
t = atk("emit_only")
t.write_text(t.read_text().replace("ATTACK_TX_BLOCKED", "x"))
try:
    P.parse_run(tmp / case / "emit_only")
    check("missing BLOCKED marker raises", False)
except P.ParseError:
    check("missing BLOCKED marker raises", True)

# 2. truncated log (no verdict) must raise, not be guessed
t.write_text("Compiling 20 files with Solc 0.8.20\n")
try:
    P.parse_run(tmp / case / "emit_only")
    check("truncated log raises", False)
except P.ParseError:
    check("truncated log raises", True)

# 3. flip normal replay to a FAIL -> preserved must go false
n = nrm("revert")
n.write_text(n.read_text().replace("[PASS]", "[FAIL: logs changed]").replace("NORMAL_TX_REPLAY_CHECKED", ""))
r = P.parse_run(tmp / case / "revert")
check("normal FAIL flips preserved to False", r["normal_ops_pass"] is False and r["preserved_count"] == 0)

# 4. inject OOG into a failing normal log -> oracle rule counts it as preserved
n.write_text("[FAIL: EvmError: OutOfGas] testHistoricalNormalTxReplay()\n")
r = P.parse_run(tmp / case / "revert")
check("OOG in failing log counts preserved", r["oog"] and r["normal_ops_pass"])

# 5. the sha moves when a log byte changes
h1 = P.sha([nrm("revert")])
n.write_text(n.read_text() + "x")
check("sha changes with log bytes", P.sha([nrm("revert")]) != h1)

# 6. an RPC error line is flagged; a clean log is not (and hex hashes containing 429 do not trip it)
u = atk("unchanged")
check("clean log not flagged as RPC error", P.parse_run(tmp / case / "unchanged")["rpc_error_in_logs"] is False)
u.write_text(u.read_text() + "\nERROR sharedbackend: Failed to send/recv `storage` 0x429429\n")
check("RPC error line flagged", P.parse_run(tmp / case / "unchanged")["rpc_error_in_logs"] is True)

# 7. score lane that says 'not blocked' while the cli lane says blocked is reported as disagreement
sl = next((tmp / case / "revert").glob("attack_tx_replay/*/forge_output.txt"))
sl.write_text("[FAIL: historical attack tx did not succeed before patch] testHistoricalAttackTxReplay()\n")
check("lane disagreement detected", P.parse_run(tmp / case / "revert")["lanes_disagree"] is True)

shutil.rmtree(tmp)
print("RESULT", "GREEN" if fails == 0 else f"RED({fails})")
sys.exit(1 if fails else 0)
