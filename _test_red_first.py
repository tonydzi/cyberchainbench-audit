#!/usr/bin/env python3
"""Red-first guard: the audit's PASS checks must turn red on corrupted data.

A check that cannot fail proves nothing. This deliberately breaks the dataset in
three independent ways and asserts the corresponding check flips to DISCREPANCY.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE / "verify_cyberchainbench.py"
CASES = (HERE / ".." / "repo" / "data" / "benchmark" / "cases").resolve()


def run(cases_dir):
    out = subprocess.run(
        [sys.executable, str(AUDIT), "--cases", str(cases_dir)],
        capture_output=True, text=True, check=True,
    ).stdout
    status = {}
    for line in out.splitlines():
        if line.startswith("[ok  ] "):
            status[line[7:].strip()] = "PASS"
        elif line.startswith("[DIFF] "):
            status[line[7:].strip()] = "DISCREPANCY"
    return status


def corrupt(dst, mutate):
    shutil.copytree(CASES, dst)
    files = sorted(dst.glob("*.json"))
    mutate(files)


def main():
    baseline = run(CASES)
    print("baseline:", {k: v for k, v in baseline.items()})
    expected_pass = [
        "dataset size",
        "patch subset size",
        "temporal split",
        "patch subset, pre-filter stage",
    ]
    for name in expected_pass:
        assert baseline.get(name) == "PASS", f"baseline should be PASS for {name!r}"

    failures = []

    def check(label, target, mutate):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "cases"
            corrupt(dst, mutate)
            got = run(dst)
            ok = got.get(target) == "DISCREPANCY"
            print(f"  {'RED ok ' if ok else 'STAYED GREEN'}  {label} -> {target!r}: {got.get(target)}")
            if not ok:
                failures.append((label, target, got.get(target)))

    print("\nred-first mutations:")

    # 1. drop a case file -> dataset size must go red
    check("delete one case file", "dataset size",
          lambda files: files[0].unlink())

    # 2. flip a `fixable` flag -> patch subset size must go red
    def unfix(files):
        for f in files:
            d = json.loads(f.read_text())
            if d.get("fixable") is True and d.get("has_public_source") is True and d.get("normal_txs"):
                d["fixable"] = False
                f.write_text(json.dumps(d))
                return
        raise AssertionError("no patch-subset case found to mutate")
    check("flip one `fixable` to False", "patch subset size", unfix)

    # 3. move a 2024 incident into 2025 -> temporal split must go red
    def redate(files):
        for f in files:
            d = json.loads(f.read_text())
            if (d.get("attack_date") or "").startswith("2024"):
                d["attack_date"] = "2025-06-01"
                f.write_text(json.dumps(d))
                return
        raise AssertionError("no 2024 case found to mutate")
    check("re-date one 2024 incident to 2025", "temporal split", redate)

    print()
    if failures:
        print("FAILED -- these checks could not be made to fail:", failures)
        return 1
    print("all mutations produced red: the PASS checks are load-bearing, not vacuous.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
