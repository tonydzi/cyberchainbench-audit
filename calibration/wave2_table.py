#!/usr/bin/env python3
"""Wave 2 table: per-case usability with a named reason, plus Wilson 95% intervals over USABLE cases only.

usage: wave2_table.py <runs_dir> <case_ids_file> <outdir> [--arms-failed <file>]
Reads raw forge logs through parse_runs (never the oracle JSON for the verdict markers).

A case is usable ("working") only if, in the three arms, there is no compile error and no RPC error,
the historical attack reproduces before the patch, and the `revert` arm blocks it (so a patch CAN score).
Reasons otherwise: harness | baseline | ineligible | rpc.
"""
import csv
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parse_runs as P  # noqa: E402

ARMS = ("unchanged", "revert", "emit_only")


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def classify(case_dir: Path, arms_built: bool):
    """-> (usable: bool, reason: str, rows: dict[arm,row])"""
    if not arms_built:
        return False, "harness: arm builder found no matching Solidity function/contract", {}
    rows, errs, skipped = {}, [], []
    for a in ARMS:
        d = case_dir / a
        if not d.is_dir():
            errs.append(f"{a}: not run")
            continue
        try:
            rows[a] = P.parse_run(d)
        except P.ParseError as e:
            note = _oracle_note(d)
            if a == "emit_only" and re.search(r"declared as (view|pure)", note):
                skipped.append(a)  # our edit cannot compile inside a view/pure function: arm invalid, case not
            elif "failed to compile fixed bytecode" in note:
                errs.append(f"{a}: oracle recompile of the staged sources fails ({_first_line(note)})")
            else:
                errs.append(f"{a}: {e}")
    if errs:
        txt = "".join(_oracle_note(case_dir / a) for a in ARMS if (case_dir / a).is_dir())
        if "normal_txs field is empty" in txt:
            return False, "ineligible: no replayable normal tx (CLI drops contract-creation txs)", rows
        return False, "harness: " + "; ".join(errs)[:220], rows
    if any(r["attack_compile_errors"] or r["normal_compile_errors"] for r in rows.values()):
        return False, "harness: compile error in an arm", rows
    if any(r["rpc_error_in_logs"] for r in rows.values()):
        return False, "rpc: RPC error line in forge logs", rows
    if not all(r["attack_reproduces"] for r in rows.values()):
        logs = "".join(p.read_text(errors="replace") for p in (case_dir / "unchanged").glob("attack_tx_replay_cli/*/forge_output.txt"))
        if re.search(r"MemoryOOG|OutOfGas", logs):
            return False, "baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated)", rows
        return False, "baseline: historical attack does not reproduce before the patch", rows
    if not rows["revert"]["exploit_blocked"]:
        return False, "baseline: attack still passes after revert() in the vulnerable function", rows
    if skipped:
        return True, "usable (emit_only arm invalid: event cannot be emitted in a view/pure function)", rows
    return True, "usable", rows


def _oracle_note(d: Path) -> str:
    out = ""
    for name in ("stdout.json", "stderr.log"):
        f = d / name
        if f.exists():
            out += f.read_text(errors="replace")
    return out


def _first_line(note: str) -> str:
    m = re.search(r"failed to compile fixed bytecode: ([^\\\n]{0,90})", note)
    return m.group(1) if m else "see stdout.json"


def main():
    runs, ids, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    failed = set()
    if "--arms-failed" in sys.argv:
        failed = set(Path(sys.argv[sys.argv.index("--arms-failed") + 1]).read_text().split())
    out.mkdir(parents=True, exist_ok=True)
    cases = json.loads(ids.read_text())
    table, flat = [], []
    for c in cases:
        ok, reason, rows = classify(runs / c, c not in failed)
        table.append((c, ok, reason, rows))
        for a, r in rows.items():
            flat.append({"usable": ok, "reason": reason, **r})
    with open(out / "results.csv", "w", newline="") as f:
        cols = list(flat[0])
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(flat)
    n_ok = sum(1 for t in table if t[1])
    lines = ["| case | usable? | reason | unchanged | revert | emit_only |", "|---|---|---|---|---|---|"]
    stats = {a: 0 for a in ARMS}
    n_arm = {a: 0 for a in ARMS}
    n_ret = blocked_k = equal_k = disagree = 0
    for c, ok, reason, rows in table:
        cells = []
        for a in ARMS:
            r = rows.get(a)
            s = "n/a" if r is None else str(r["oracle_score"])
            if r is not None and ok:
                n_arm[a] += 1
                disagree += 0 if r["agree_with_oracle"] else 1
                if r["oracle_score"] == 1.0:
                    stats[a] += 1
            cells.append(s)
        if ok and "emit_only" in rows:
            n_ret += 1
            e = rows["emit_only"]
            blocked_k += bool(e["exploit_blocked"])
            equal_k += e["profit_before"] not in (None, 0) and e["profit_before"] == e["profit_after"]
        lines.append(f"| {c} | {'yes' if ok else 'no'} | {reason} | " + " | ".join(cells) + " |")
    lines += ["", f"Usable cases: {n_ok} of {len(table)}. Runs where our parse disagrees with the oracle's own verdict: {disagree}.", ""]
    lines += ["| input | validate_patch CLI score 1.0 | usable cases with this arm | Wilson 95% interval |", "|---|---|---|---|"]
    summary = {"usable": n_ok, "total": len(table), "disagree_with_oracle": disagree, "arms": {}}
    for a in ARMS:
        lo, hi = wilson(stats[a], n_arm[a])
        summary["arms"][a] = {"k": stats[a], "n": n_arm[a], "lo": lo, "hi": hi}
        ci = "n/a" if lo is None else f"{lo*100:.1f}% to {hi*100:.1f}%"
        lines.append(f"| {a} | {stats[a]} | {n_arm[a]} | {ci} |")
    for key, k, label in (
        ("emit_only_counted_blocked", blocked_k, "emit_only counted as blocking the exploit"),
        ("emit_only_profit_exactly_unchanged", equal_k, "emit_only with attacker profit exactly unchanged"),
    ):
        lo, hi = wilson(k, n_ret)
        summary[key] = {"k": k, "n": n_ret, "lo": lo, "hi": hi}
        lines.append(f"| {label} | {k} | {n_ret} | " + ("n/a" if lo is None else f"{lo*100:.1f}% to {hi*100:.1f}%") + " |")
    (out / "results.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
