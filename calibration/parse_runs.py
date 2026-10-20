#!/usr/bin/env python3
"""Derive calibration numbers from raw forge output (not from the oracle's JSON).

usage: parse_runs.py <runs_dir> [--csv out.csv] [--md out.md]
For each runs/<case>/<arm>/ it reads
  attack_tx_replay_cli/<tx>/forge_output.txt   (exploit replay)
  normal_tx_replay/<tx>/forge_output.txt       (benign replay)
and cross-checks against stdout.json (oracle's own verdict); a disagreement is flagged.
A log that is truncated / carries no forge verdict raises ParseError (never guessed).
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


class ParseError(Exception):
    pass


def _verdict(text: str, where: str) -> str:
    # forge prints "[PASS] test..." or "[FAIL...] test..."; compile errors print neither
    if re.search(r"^\[PASS\]", text, re.M):
        return "PASS"
    if re.search(r"^\[FAIL", text, re.M):
        return "FAIL"
    if re.search(r"Compiler run failed|Error:|error\[", text):
        return "COMPILE_ERROR"
    raise ParseError(f"no forge verdict in {where}")


def parse_attack(text: str, where: str) -> dict:
    v = _verdict(text, where)
    if v == "COMPILE_ERROR":
        return {"verdict": v, "checked": False, "blocked": None, "before_ok": None, "before_profit": None, "after_profit": None}
    before_ok = "ATTACK_TX_BEFORE_OK" in text
    blocked = "ATTACK_TX_BLOCKED" in text
    checked = "ATTACK_TX_REPLAY_CHECKED" in text
    bp = re.search(r"BEFORE_PROFIT: (\d+)", text)
    ap = re.findall(r"AFTER_PROFIT: (\d+)", text)
    if v == "PASS" and not (checked and before_ok):
        raise ParseError(f"PASS without CHECKED/BEFORE_OK markers in {where}")
    if v == "PASS" and not blocked:
        raise ParseError(f"PASS implies blocked, marker missing in {where}")
    return {
        "verdict": v, "checked": checked, "blocked": blocked, "before_ok": before_ok,
        "before_profit": int(bp.group(1)) if bp else None,
        "after_profit": int(ap[-1]) if ap else None,
    }


def parse_normal(text: str, where: str) -> dict:
    v = _verdict(text, where)
    oog = bool(re.search(r"MemoryOOG|OutOfGas", text))
    reasons = re.findall(r"(success changed|return data changed|logs changed)", text)
    marker = "NORMAL_TX_REPLAY_CHECKED" in text
    if v == "PASS" and not marker:
        raise ParseError(f"PASS without NORMAL_TX_REPLAY_CHECKED in {where}")
    # oracle rule (validate_patch.py:1608-1612): OOG counts as preserved
    preserved = v == "PASS" or oog
    return {"verdict": v, "checked": marker, "oog": oog, "preserved": preserved, "diff_reasons": sorted(set(reasons))}


def sha(paths) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def parse_run(arm_dir: Path) -> dict:
    case, arm = arm_dir.parent.name, arm_dir.name
    atk_files = sorted(arm_dir.glob("attack_tx_replay_cli/*/forge_output.txt"))
    nrm_files = sorted(arm_dir.glob("normal_tx_replay/*/forge_output.txt"))
    if not atk_files or not nrm_files:
        raise ParseError(f"missing forge_output in {arm_dir}")
    atk = [parse_attack(p.read_text(errors="replace"), str(p)) for p in atk_files]
    nrm = [parse_normal(p.read_text(errors="replace"), str(p)) for p in nrm_files]
    oracle = json.loads((arm_dir / "stdout.json").read_text())
    # the oracle's own score is computed from a second, independent replay lane
    score_files = sorted(arm_dir.glob("attack_tx_replay/*/forge_output.txt"))
    score_lane = [parse_attack(p.read_text(errors="replace"), str(p)) for p in score_files]
    all_files = atk_files + nrm_files + score_files
    rpc_err = any(re.search(r"sharedbackend|Failed to send/recv|rate.?limit|Too Many Requests", p.read_text(errors="replace"), re.I)
                  for p in all_files)
    row = {
        "case": case, "arm": arm,
        "attack_txs": len(atk),
        "exploit_blocked": all(a["blocked"] for a in atk) if all(a["blocked"] is not None for a in atk) else False,
        "attack_compile_errors": sum(a["verdict"] == "COMPILE_ERROR" for a in atk),
        "profit_before": atk[0]["before_profit"], "profit_after": atk[0]["after_profit"],
        "checked_count": len(nrm), "preserved_count": sum(n["preserved"] for n in nrm),
        "normal_compile_errors": sum(n["verdict"] == "COMPILE_ERROR" for n in nrm),
        "oog": any(n["oog"] for n in nrm),
        "normal_ops_pass": all(n["preserved"] for n in nrm),
        "oracle_score": oracle.get("score"),
        "oracle_exploit_blocked": oracle.get("exploit_blocked"),
        "oracle_normal_ops_pass": oracle.get("normal_ops_pass"),
        "forge_sha256_16": sha(atk_files + nrm_files),
        "score_lane_blocked": (all(a["blocked"] for a in score_lane) if score_lane else None),
        "rpc_error_in_logs": rpc_err,
    }
    row["lanes_disagree"] = (
        row["score_lane_blocked"] is not None and bool(row["score_lane_blocked"]) != row["exploit_blocked"]
    )
    row["profit_retained"] = (
        row["profit_after"] is not None and row["profit_before"] not in (None, 0)
        and row["profit_after"] * 100 >= row["profit_before"]
    )
    row["agree_with_oracle"] = (
        row["exploit_blocked"] == bool(oracle.get("exploit_blocked"))
        and (not row["exploit_blocked"] or row["normal_ops_pass"] == bool(oracle.get("normal_ops_pass")))
    )
    return row


def main():
    runs = Path(sys.argv[1])
    rows, errors = [], []
    for arm_dir in sorted(p for p in runs.glob("*/*") if p.is_dir()):
        try:
            rows.append(parse_run(arm_dir))
        except ParseError as e:
            errors.append(f"{arm_dir.parent.name}/{arm_dir.name}: {e}")
    cols = list(rows[0]) if rows else []
    args = sys.argv[2:]
    if "--csv" in args:
        with open(args[args.index("--csv") + 1], "w", newline="") as f:
            w = csv.DictWriter(f, cols)
            w.writeheader()
            w.writerows(rows)
    if "--md" in args:
        show = ["case", "arm", "exploit_blocked", "profit_retained", "normal_ops_pass", "checked_count",
                "preserved_count", "oog", "oracle_score", "agree_with_oracle", "lanes_disagree", "rpc_error_in_logs", "forge_sha256_16"]
        lines = ["| " + " | ".join(show) + " |", "|" + "---|" * len(show)]
        for r in rows:
            lines.append("| " + " | ".join(str(r[c]) for c in show) + " |")
        if errors:
            lines += ["", "Unparseable runs (reported, not guessed):"] + [f"- {e}" for e in errors]
        Path(args[args.index("--md") + 1]).write_text("\n".join(lines) + "\n")
    for r in rows:
        print(json.dumps(r))
    for e in errors:
        print("PARSE_ERROR", e, file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
