#!/usr/bin/env python3
"""Red-first guard: every PASS check in the audit must turn red on corrupted data.

A check that cannot fail proves nothing. This copies the upstream case files
and the parsed paper tables into a temp dir, breaks them in four independent
ways, and asserts that the matching check flips to DISCREPANCY.

Usage:
    python3 _test_red_first.py --upstream CyberChainBench
Exit 0 = every mutation went red. Exit 1 = some check stayed green (or the
baseline was not green to begin with).
рельса: local python, no LLM.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(os.path.realpath(__file__)).parent
AUDIT = HERE / "verify_cyberchainbench.py"


def run(upstream: pathlib.Path, data: pathlib.Path) -> dict[str, str]:
    out = subprocess.run(
        [sys.executable, str(AUDIT), "--upstream", str(upstream), "--data", str(data)],
        capture_output=True, text=True, check=True,
    ).stdout
    status = {}
    for line in out.splitlines():
        if line.startswith("[ok  ] "):
            status[line[7:].strip()] = "PASS"
        elif line.startswith("[DIFF] "):
            status[line[7:].strip()] = "DISCREPANCY"
    return status


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="CyberChainBench")
    args = ap.parse_args()
    upstream = pathlib.Path(args.upstream).resolve()
    data = HERE / "data"
    cases = upstream / "data" / "benchmark" / "cases"
    if not cases.is_dir():
        print(f"no cases under {cases}; clone the upstream first", file=sys.stderr)
        return 1

    baseline = run(upstream, data)
    must_pass = ["dataset size", "patch subset size", "temporal split",
                 "patch subset, pre-filter stage", "Table 4 patch cells are whole-case counts"]
    for name in must_pass:
        if baseline.get(name) != "PASS":
            print(f"baseline is not PASS for {name!r}: {baseline.get(name)}")
            return 1
    print("baseline green on:", ", ".join(must_pass))

    failures = []

    def check(label: str, target: str, mutate_cases=None, mutate_data=None) -> None:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            up = td / "up"
            shutil.copytree(cases, up / "data" / "benchmark" / "cases")
            dd = td / "data"
            shutil.copytree(data, dd)
            if mutate_cases:
                mutate_cases(sorted((up / "data" / "benchmark" / "cases").glob("*.json")))
            if mutate_data:
                mutate_data(dd)
            got = run(up, dd).get(target)
            ok = got == "DISCREPANCY"
            print(f"  {'RED ok      ' if ok else 'STAYED GREEN'}  {label} -> {target!r}: {got}")
            if not ok:
                failures.append((label, target, got))

    def drop_one(files):
        files[0].unlink()

    def unfix(files):
        for f in files:
            d = json.loads(f.read_text())
            if d.get("fixable") is True and d.get("has_public_source") is True and d.get("normal_txs"):
                d["fixable"] = False
                f.write_text(json.dumps(d))
                return
        raise AssertionError("no patch-subset case to mutate")

    def redate(files):
        for f in files:
            d = json.loads(f.read_text())
            if str(d.get("attack_date", "")).startswith("2024"):
                d["attack_date"] = "2025-06-01"
                f.write_text(json.dumps(d))
                return
        raise AssertionError("no 2024 case to mutate")

    def bend_table4(dd: pathlib.Path):
        p = dd / "paper-table-4.csv"
        rows = list(csv.reader(p.open(encoding="utf-8")))
        for r in rows:
            if r[0] == "Codex GPT-5.5":
                r[10] = "21.0"   # patch Easy 19.4 -> 21.0: 31 x 21.0% = 6.51 passes, not a whole case
        with p.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

    print("\nmutations:")
    check("delete one case file", "dataset size", mutate_cases=drop_one)
    check("flip one `fixable` to False", "patch subset size", mutate_cases=unfix)
    check("re-date one 2024 incident to 2025", "temporal split", mutate_cases=redate)
    check("bend one Table 4 patch cell off the k/n grid",
          "Table 4 patch cells are whole-case counts", mutate_data=bend_table4)

    print()
    if failures:
        print("FAILED: these checks could not be made to fail:", failures)
        return 1
    print("every mutation went red: the PASS checks are load-bearing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
