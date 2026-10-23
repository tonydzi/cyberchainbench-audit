#!/usr/bin/env python3
"""Red-first proof for wave2_table.py: usability verdict and Wilson interval must change on damaged logs.

usage: _test_wave2_table.py <runs_dir>   (needs runs/bench-391/{unchanged,revert,emit_only})
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wave2_table as T  # noqa: E402

runs = Path(sys.argv[1])
case = "bench-391"
tmp = Path(tempfile.mkdtemp())
fails = 0


def check(name, ok):
    global fails
    print(("ok  " if ok else "FAIL"), name)
    fails += 0 if ok else 1


def fresh():
    shutil.rmtree(tmp / case, ignore_errors=True)
    shutil.copytree(runs / case, tmp / case)


def atk(arm):
    return next((tmp / case / arm).glob("attack_tx_replay_cli/*/forge_output.txt"))


fresh()
ok, reason, _ = T.classify(tmp / case, True)
check("real bench-391 logs classify as usable", ok and reason == "usable")

ok, reason, _ = T.classify(tmp / case, False)
check("arm builder failure is harness", not ok and reason.startswith("harness"))

# revert arm no longer blocks -> baseline
fresh()
a = atk("revert")
a.write_text(a.read_text().replace("ATTACK_TX_BLOCKED", "x").replace("[PASS]", "[FAIL: x]"))
ok, reason, _ = T.classify(tmp / case, True)
check("attack surviving revert is baseline, not usable", not ok and reason.startswith("baseline"))

# attack does not reproduce before the patch -> baseline
fresh()
for arm in ("unchanged", "revert", "emit_only"):
    a = atk(arm)
    a.write_text(a.read_text().replace("ATTACK_TX_BEFORE_OK", "x").replace("[PASS]", "[FAIL: before]"))
ok, reason, _ = T.classify(tmp / case, True)
check("no baseline reproduction is baseline", not ok and reason.startswith("baseline"))

# RPC error line -> rpc
fresh()
a = atk("unchanged")
a.write_text(a.read_text() + "\nERROR sharedbackend: Failed to send/recv `storage`\n")
ok, reason, _ = T.classify(tmp / case, True)
check("RPC error classified as rpc", not ok and reason.startswith("rpc"))

# missing arm output -> harness
fresh()
shutil.rmtree(tmp / case / "emit_only" / "normal_tx_replay")
ok, reason, _ = T.classify(tmp / case, True)
check("missing forge output is harness", not ok and reason.startswith("harness"))

# Wilson known values (n=3: 0/3 -> upper 0.438; 1/3 -> 0.061..0.792; 3/3 -> lower 0.438)
lo, hi = T.wilson(0, 3)
check("wilson 0/3", lo == 0.0 and abs(hi - 0.5615) < 1e-3)
lo, hi = T.wilson(1, 3)
check("wilson 1/3", abs(lo - 0.0615) < 1e-3 and abs(hi - 0.7923) < 1e-3)
check("wilson n=0 is undefined", T.wilson(0, 0) == (None, None))

shutil.rmtree(tmp)
print("RESULT", "GREEN" if fails == 0 else f"RED({fails})")
sys.exit(1 if fails else 0)
