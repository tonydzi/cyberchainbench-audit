#!/usr/bin/env python3
"""Red-first test for rescore_profit_rule.py.

Each check edits a COPY of the real results CSVs and asserts the rescored verdict
changes the way the rule says it must. A rescore that cannot change is not a measurement.
Exit 0 = all checks behaved; exit 1 = some check did not.
рельса: local python, no LLM.
"""
import csv
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import rescore_profit_rule as rp  # noqa: E402

W1 = os.path.join(HERE, "results.csv")
W2 = os.path.join(HERE, "wave2", "results.csv")


def edit(src, dst, case, arm, **kv):
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    hit = 0
    for r in rows:
        if r["case"] == case and r["arm"] == arm:
            r.update({k: str(v) for k, v in kv.items()})
            hit += 1
    assert hit, f"{case}/{arm} not found in {src}"
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def get(rows, case, arm):
    return next(r for r in rows if r["case"] == case and r["arm"] == arm)


def main() -> int:
    fails = []
    base = [rp.rescore(r) for r in rp.load(W1, W2)]

    # 0. baseline cross-check against the published wave numbers
    def count(arm, key):
        return sum(r[key] == 1.0 for r in base if r["arm"] == arm)
    if (count("unchanged", "orig_score"), count("revert", "orig_score"), count("emit_only", "orig_score")) != (4, 5, 4):
        fails.append("original full-credit counts no longer match wave2/README.md (4/26, 5/26, 4/19)")
    r391 = get(base, "bench-391", "emit_only")
    if not (r391["orig_score"] == 1.0 and r391["alt_score"] == 0.0):
        fails.append("bench-391 emit_only should be orig 1.0, alt 0.0 on real data")

    with tempfile.TemporaryDirectory() as td:
        # 1. drop the attacker's profit to zero: the profit rule must now count it blocked and give 1.0
        w1 = os.path.join(td, "w1.csv")
        edit(W1, w1, "bench-391", "emit_only", profit_after=0)
        r = get([rp.rescore(x) for x in rp.load(w1, W2)], "bench-391", "emit_only")
        if not (r["alt_blocked"] and r["alt_score"] == 1.0):
            fails.append("profit 0 after patch did not flip bench-391 emit_only to alt 1.0")

        # 2. mark the normal replay as out-of-gas: the strict rule must refuse preservation
        w1b = os.path.join(td, "w1b.csv")
        edit(W1, w1b, "bench-391", "emit_only", profit_after=0, oog="True")
        r = get([rp.rescore(x) for x in rp.load(w1b, W2)], "bench-391", "emit_only")
        if r["alt_preserved"] or r["alt_score"] != 0.0:
            fails.append("oog=True was still counted as preserved by the strict rule")

        # 2b. the 1% threshold itself: half the profit left is NOT blocked, 0.5% left IS blocked
        before = get(base, "bench-559", "revert")["profit_before"]
        if get(base, "bench-559", "revert")["alt_blocked"]:
            fails.append("bench-559 revert (profit halved) counted as blocked: threshold not applied")
        w1c = os.path.join(td, "w1c.csv")
        edit(W1, w1c, "bench-559", "revert", profit_after=repr(before * 0.005))
        if not get([rp.rescore(x) for x in rp.load(w1c, W2)], "bench-559", "revert")["alt_blocked"]:
            fails.append("0.5% of the profit left was not counted as blocked")
        edit(W1, w1c, "bench-559", "revert", profit_after=repr(before * 0.02))
        if get([rp.rescore(x) for x in rp.load(w1c, W2)], "bench-559", "revert")["alt_blocked"]:
            fails.append("2% of the profit left was counted as blocked")

        # 3. a usable row with a missing profit must raise, not be silently scored
        w2 = os.path.join(td, "w2.csv")
        edit(W2, w2, "bench-220", "emit_only", profit_after="")
        try:
            [rp.rescore(x) for x in rp.load(W1, w2)]
            fails.append("missing profit in a usable row did not raise")
        except ValueError:
            pass

    for f in fails:
        print("FAIL", f)
    print("ok" if not fails else f"{len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
