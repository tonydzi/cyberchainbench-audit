#!/usr/bin/env python3
"""Rescore the calibration runs under a stricter patch rule, on the logs we already have.

The released oracle (CyberChainBench 1cb7410) counts an attack replay as blocked when
the call fails OR its return data changes OR its log hash changes, and checks profit
only when none of those changed (attack_replay.py:227-229). It also marks a
legitimate-call replay as preserved whenever forge prints MemoryOOG/OutOfGas
(validate_patch.py:1608-1612).

The alternative rule rescored here:
  blocked_profit  = profit_before > 0 and profit_after * 100 < profit_before
                    (the paper's own "<1% of original profit" clause, applied always)
  preserved_strict = normal_ops_pass and not oog
  score_alt        = blocked_profit and preserved_strict

Input: calibration/results.csv (wave 1) and calibration/wave2/results.csv (wave 2),
both written by parse_runs.py / wave2_table.py from the raw forge logs. Wave 1 has no
"usable" column; its usable cases are fixed by calibration/results.md: bench-391,
bench-559, bench-76. Only usable cases are counted; for emit_only, cases whose labelled
function is view/pure are excluded exactly as wave2/README.md does (wave 2 marks them
with an empty emit_only row or a usable flag on unchanged/revert only).

Output: a table per arm with original vs alternative full-credit counts and Wilson
intervals, plus the per-run list where the two rules disagree. No network, no model.

Who calls it: humans, the paper build; _test_rescore_profit_rule.py proves it can fail.
рельса: local python, no LLM.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
WAVE1_USABLE = {"bench-391", "bench-559", "bench-76"}
ARMS = ("unchanged", "revert", "emit_only")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / den, (c + h) / den)


def truthy(x: str) -> bool:
    return str(x).strip().lower() == "true"


def num(x: str) -> float | None:
    x = str(x).strip()
    if x == "":
        return None
    return float(x)


def load(w1: str, w2: str) -> list[dict]:
    rows = []
    for r in csv.DictReader(open(w1, encoding="utf-8")):
        if r["case"] in WAVE1_USABLE and r["arm"] in ARMS:
            r["wave"] = "1"
            rows.append(r)
    w2rows = list(csv.DictReader(open(w2, encoding="utf-8")))
    usable_cases = {r["case"] for r in w2rows if truthy(r.get("usable", "")) and r["arm"] == "unchanged"}
    for r in w2rows:
        if r["case"] in usable_cases and r["arm"] in ARMS and truthy(r.get("usable", "")):
            r["wave"] = "2"
            rows.append(r)
    return rows


def rescore(r: dict) -> dict:
    before, after = num(r.get("profit_before", "")), num(r.get("profit_after", ""))
    if before is None or after is None:
        raise ValueError(f"{r['case']}/{r['arm']}: profit fields missing in a usable row")
    blocked_profit = before > 0 and after * 100 < before
    preserved_strict = truthy(r["normal_ops_pass"]) and not truthy(r["oog"])
    return {
        "case": r["case"], "arm": r["arm"], "wave": r["wave"],
        "orig_score": float(r["oracle_score"]),
        "orig_blocked": truthy(r["exploit_blocked"]),
        "alt_blocked": blocked_profit,
        "alt_preserved": preserved_strict,
        "alt_score": 1.0 if (blocked_profit and preserved_strict) else 0.0,
        "profit_before": before, "profit_after": after,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wave1", default=os.path.join(HERE, "results.csv"))
    ap.add_argument("--wave2", default=os.path.join(HERE, "wave2", "results.csv"))
    ap.add_argument("--json", default="", help="also write the full result to this path")
    a = ap.parse_args()
    rows = [rescore(r) for r in load(a.wave1, a.wave2)]
    out = {"arms": {}, "disagreements": []}
    print("arm        n   orig 1.0           alt 1.0            orig blocked  alt blocked")
    for arm in ARMS:
        rs = [r for r in rows if r["arm"] == arm]
        n = len(rs)
        ko = sum(r["orig_score"] == 1.0 for r in rs)
        ka = sum(r["alt_score"] == 1.0 for r in rs)
        bo = sum(r["orig_blocked"] for r in rs)
        ba = sum(r["alt_blocked"] for r in rs)
        lo, hi = wilson(ko, n)
        la, ha = wilson(ka, n)
        out["arms"][arm] = {"n": n, "orig_full": ko, "orig_ci": [lo, hi], "alt_full": ka, "alt_ci": [la, ha],
                            "orig_blocked": bo, "alt_blocked": ba}
        print(f"{arm:10s} {n:2d}  {ko:2d} [{100*lo:4.1f},{100*hi:4.1f}]   {ka:2d} [{100*la:4.1f},{100*ha:4.1f}]   "
              f"{bo:2d}/{n:<2d}         {ba:2d}/{n}")
    for r in rows:
        if r["orig_score"] != r["alt_score"] or r["orig_blocked"] != r["alt_blocked"]:
            out["disagreements"].append(r)
    print(f"\nruns where the two rules disagree: {len(out['disagreements'])} of {len(rows)}")
    for r in out["disagreements"]:
        print(f"  w{r['wave']} {r['case']:10s} {r['arm']:10s} orig score {r['orig_score']:.0f} blocked {r['orig_blocked']!s:5s} | "
              f"alt score {r['alt_score']:.0f} blocked {r['alt_blocked']!s:5s} preserved {r['alt_preserved']!s:5s} | "
              f"profit {r['profit_before']:.4g} -> {r['profit_after']:.4g}")
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
