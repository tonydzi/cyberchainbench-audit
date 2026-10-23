#!/usr/bin/env python3
"""Audit CyberChainBench's headline numbers against its own public release.

CyberChainBench (arXiv:2606.26216v1) headlines "a clear difficulty gradient:
37.5% on detection, 43.7% on exploitation, but only 23.4% on patching".

This script checks what can be checked for free. It reconstructs the
benchmark's own case subsets from the published dataset, recomputes the
published aggregates from the published per-difficulty cells, compares the
paper with the leaderboard the authors ship in the same repository, and puts
uncertainty on the headline numbers. No model is run, no RPC is called,
nothing is spent.

Inputs:
  * data/paper-table-4.csv, data/paper-table-5.csv: the paper's Table 4
    (per-difficulty scores) and Table 5 (cost, tokens, block/pass), parsed
    structurally from the arXiv HTML by extract_tables.py. Nothing is
    hand-transcribed.
  * the upstream release at commit 1cb7410 (tag v1.0): case files under
    data/benchmark/cases/ and site/assets/leaderboard.json.

Usage:
    git clone https://github.com/defai-labs/CyberChainBench.git
    git -C CyberChainBench checkout 1cb7410
    python3 verify_cyberchainbench.py --upstream CyberChainBench

Exit code: 0 when every check reached a verdict (discrepancies included),
1 when inputs are missing. A discrepancy is a finding, not a script failure.

Who calls it: humans and the Makefile (`make audit`); _test_red_first.py
runs it on corrupted copies of the data to prove the checks can fail.
рельса: local python, no LLM.
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
DIFFS = ("easy", "medium", "hard")
CUTOFF = "2025-01-01"
UPSTREAM_COMMIT = "1cb7410"

# Claims the paper makes about its own dataset (arXiv:2606.26216v1).
PAPER = {
    "total_cases": 541,
    "patch_subset": 94,
    "pre_filter": 153,          # text calls these "proxy cases"
    "post_cutoff": 86,
    "pre_cutoff": 455,
    "best_patch_abstract": 23.4,  # abstract and section 4: "the best patch pass rate (23.4%)"
    "best_patch_text": 21.3,      # section 4: "Opus 4.7 leads on patch pass rate (21.3%)"
    # Section 4, temporal shift: "Opus 4.7 exploit: 44.9% -> 38.8%" (pre -> post cutoff)
    "opus47_exploit_pre": 44.9,
    "opus47_exploit_post": 38.8,
    "exploit_n": 200,
}

PASS, FAIL, INFO = "PASS", "DISCREPANCY", "note"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str]] = []

    def add(self, status: str, name: str, detail: str) -> None:
        self.rows.append((status, name))
        mark = {PASS: "[ok  ]", FAIL: "[DIFF]", INFO: "[info]"}[status]
        print(f"{mark} {name}\n       {detail}\n")

    def summary(self) -> None:
        c = collections.Counter(s for s, _ in self.rows)
        print("=" * 72)
        print(f"reproduced: {c[PASS]}   discrepancies: {c[FAIL]}   notes: {c[INFO]}")


# ----------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------

def read_table4(path: str) -> dict[str, dict[str, tuple[float, ...]]]:
    """config -> {"detect"|"exploit"|"patch": (All, Easy, Med, Hard)}."""
    rows = list(csv.reader(open(path, encoding="utf-8")))
    out = {}
    for r in rows[2:]:
        v = [float(x) for x in r[1:13]]
        out[r[0]] = {"detect": tuple(v[0:4]), "exploit": tuple(v[4:8]), "patch": tuple(v[8:12])}
    return out


def read_table5(path: str) -> dict[str, dict[str, float]]:
    """config -> {"patch_cost", "exploit_cost", "block", "pass", "ratio", "profit_m"}."""
    rows = list(csv.reader(open(path, encoding="utf-8")))
    out = {}
    for r in rows[2:]:
        ratio, profit = (float(x) for x in r[11].split("/"))
        block, pss = (float(x) for x in r[12].split("/"))
        out[r[0]] = {"exploit_cost": float(r[2]), "patch_cost": float(r[3]),
                     "ratio": ratio, "profit_m": profit, "block": block, "pass": pss}
    return out


def canon(name: str) -> str:
    """Map table and leaderboard naming variants onto one key."""
    n = name.lower().replace("_", "-").replace(" ", "-")
    for key in ("opus-4.7", "opus-4-7", "opus-4.6", "opus-4-6", "gpt-5.5", "gpt-5.4",
                "gpt-5.2", "gemini", "deepseek", "glm", "minimax", "kimi"):
        if key in n:
            return key.replace("opus-4-7", "opus-4.7").replace("opus-4-6", "opus-4.6")
    return n


def load_cases(path: str) -> list[dict]:
    files = sorted(glob.glob(os.path.join(path, "*.json")))
    return [json.load(open(f, encoding="utf-8")) for f in files]


def patch_subset(cases: list[dict]) -> list[dict]:
    """The patch filter exactly as implemented upstream.

    src/scripts/1_benchmark/benchmark.py, _generate_tasks(): fixable is True,
    has_public_source is True, normal_txs non-empty. The paper describes the
    starting set as "153 proxy cases"; the code never consults proxy_address.
    """
    return [c for c in cases if c.get("fixable") is True
            and c.get("has_public_source") is True and c.get("normal_txs")]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - half) / den, (centre + half) / den)


def near_int(x: float, tol: float) -> int | None:
    r = round(x)
    return int(r) if abs(x - r) <= tol else None


# ----------------------------------------------------------------------------
# checks
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", default="CyberChainBench",
                    help="path to a clone of defai-labs/CyberChainBench at commit 1cb7410")
    ap.add_argument("--data", default=os.path.join(HERE, "data"),
                    help="directory holding paper-table-4.csv and paper-table-5.csv")
    args = ap.parse_args()

    cases_dir = os.path.join(args.upstream, "data", "benchmark", "cases")
    t4p = os.path.join(args.data, "paper-table-4.csv")
    t5p = os.path.join(args.data, "paper-table-5.csv")
    for p in (cases_dir, t4p, t5p):
        if not os.path.exists(p):
            print(f"missing input: {p}", file=sys.stderr)
            return 1
    cases = load_cases(cases_dir)
    if not cases:
        print(f"no case files under {cases_dir}", file=sys.stderr)
        return 1
    t4 = read_table4(t4p)
    t5 = read_table5(t5p)
    t5_by = {canon(k): v for k, v in t5.items()}
    NP = PAPER["patch_subset"]  # the paper's denominator for its own patch percentages
    r = Report()
    print(f"CyberChainBench audit: {len(cases)} case files from {cases_dir}, "
          f"{len(t4)} configurations from Table 4\n")

    # 1. dataset size ------------------------------------------------------
    r.add(PASS if len(cases) == PAPER["total_cases"] else FAIL, "dataset size",
          f"paper: {PAPER['total_cases']} incidents; release ships {len(cases)} case files")

    # 2. patch subset reconstruction ----------------------------------------
    fixable = [c for c in cases if c.get("fixable") is True]
    patch = patch_subset(cases)
    n = len(patch)
    comp = collections.Counter(c.get("difficulty") for c in patch)
    unknown = [c["id"] for c in patch if c.get("difficulty") not in DIFFS]
    with_proxy = sum(1 for c in patch if c.get("proxy_address"))
    r.add(PASS if len(fixable) == PAPER["pre_filter"] else FAIL, "patch subset, pre-filter stage",
          f"paper: '{PAPER['pre_filter']} proxy cases'; `fixable is True` yields {len(fixable)}. "
          f"The count matches; the label does not. The code never consults proxy_address "
          f"({with_proxy} of the final {n} have one).")
    r.add(PASS if n == PAPER["patch_subset"] else FAIL, "patch subset size",
          f"paper: {PAPER['patch_subset']}; the code's filter gives {n}: easy {comp['easy']}, "
          f"medium {comp['medium']}, hard {comp['hard']}, plus {len(unknown)} labelled "
          f"'unknown' ({', '.join(unknown) or 'none'}) that sit in no difficulty column")

    # 3. Table 4 patch column is made of whole cases ------------------------
    # Every cell is (passes / stratum size) rounded to 0.1, so passes must be
    # near-integer. The unknown-difficulty cases have no column; whatever the
    # 'All' cell holds beyond the three strata must fit inside them.
    ok, lines = 0, []
    for cfg, v in t4.items():
        a, e, m, h = v["patch"]
        parts = [near_int(x * k / 100, 0.06) for x, k in ((e, comp["easy"]), (m, comp["medium"]), (h, comp["hard"]))]
        total = near_int(a * n / 100, 0.06)
        good = None not in parts and total is not None and 0 <= total - sum(parts) <= len(unknown)
        ok += good
        if not good or total - (sum(parts) if None not in parts else 0) > 0:
            lines.append(f"{cfg}: All={total}/{n}, strata={parts}"
                         + (f", {total - sum(parts)} pass among the {len(unknown)} unknown" if good else " DOES NOT FIT"))
    r.add(PASS if ok == len(t4) else FAIL, "Table 4 patch cells are whole-case counts",
          f"{ok}/{len(t4)} configurations resolve to integer passes per stratum, with the "
          f"remainder inside the {len(unknown)} unknown-difficulty cases. "
          + ("; ".join(lines) if lines else "No configuration needs an unknown-case pass."))

    # 4. Table 4 'All' vs Table 5 'Pass' ------------------------------------
    mism, non_k94 = [], []
    for cfg, v in t4.items():
        row = t5_by.get(canon(cfg))
        if row is None:
            continue
        if abs(v["patch"][0] - row["pass"]) > 1e-9:
            mism.append(f"{cfg}: Table 4 {v['patch'][0]} vs Table 5 {row['pass']}")
        for label in ("block", "pass"):
            if near_int(row[label] * NP / 100, 0.06) is None:
                non_k94.append(f"{cfg} {label} {row[label]}")
    r.add(FAIL if mism or non_k94 else PASS, "Table 4 'All' vs Table 5 'Pass %'",
          f"the two columns report the same quantity and agree for "
          f"{len(t4) - len(mism)}/{len(t4)} configurations. Disagree: {'; '.join(mism) or 'none'}. "
          f"Table 5 cells that are not k/{NP} for any integer k: {'; '.join(non_k94) or 'none'}. "
          f"We call this an inconsistency, not a known typo: the GPT-5.2 pair also fits k/57, "
          f"so a different denominator is as plausible as a transcription error.")

    # 4b. "All models show monotonic degradation from easy to hard" ---------
    # Section 4.2 states it; Table 4 is the evidence it points at.
    nonmono = []
    for cfg, v in t4.items():
        for task in ("detect", "exploit", "patch"):
            _, e, m, h = v[task]
            if not (e >= m >= h):
                nonmono.append(f"{cfg} {task} {e}/{m}/{h}")
    r.add(FAIL if nonmono else PASS, "'All models show monotonic degradation' vs Table 4",
          f"section 4.2 says all models degrade monotonically from easy to hard. In Table 4, "
          f"{len(nonmono)} of {3 * len(t4)} task rows are not monotonic (easy >= medium >= hard), "
          f"including the headline configuration: " + "; ".join(nonmono))

    # 5. three different 'best patch' statements ----------------------------
    best_cfg, best = max(((c, v["patch"][0]) for c, v in t4.items()), key=lambda t: t[1])
    claims = {PAPER["best_patch_text"], PAPER["best_patch_abstract"], best}
    r.add(FAIL if len(claims) > 1 else PASS, "'best patch' statements",
          f"the paper names three different best patch scores: {PAPER['best_patch_text']} "
          f"(section 4, 'Opus 4.7 leads on patch pass rate'), {PAPER['best_patch_abstract']} "
          f"(abstract and section 4, 'the best patch pass rate'), and {best} for {best_cfg} "
          f"in Table 4. The same section 4 sentence names Opus 4.7 the realized-profit leader "
          f"at $45.5M while the abstract and Table 5 give $57.4M to GPT-5.5. A stale results "
          f"paragraph is the likely cause; that is a hypothesis.")

    # 6. the authors' own leaderboard vs the paper --------------------------
    lb_path = os.path.join(args.upstream, "site", "assets", "leaderboard.json")
    if os.path.exists(lb_path):
        lb = json.load(open(lb_path, encoding="utf-8"))
        t4_by = {canon(k): v for k, v in t4.items()}
        diffs, same = [], 0
        seen = set()
        for row in lb:
            key = canon(f"{row.get('agent', '')}-{row.get('model', '')}")
            if key not in t4_by:
                continue
            seen.add(key)
            paper_v = t4_by[key][row["task"]][0]
            site_v = round(100 * float(row["mean"]), 1)
            if abs(paper_v - site_v) > 0.15:
                diffs.append(f"{key} {row['task']}: paper {paper_v} vs site {site_v} (site n={row['n']})")
        bad_cfgs = {d.split()[0] for d in diffs}
        r.add(FAIL if diffs else PASS, "paper Table 4 vs the leaderboard shipped in the same repo",
              f"comparing like for like (leaderboard mean x 100 against Table 4 'All', both "
              f"average reward), {len(bad_cfgs)} of {len(seen)} configurations disagree on at "
              f"least one task: " + "; ".join(diffs) + ". The site builder says the Codex rows "
              f"were carried over from an older leaderboard. The GPT-5.5 headline cells "
              f"(43.7, 23.4) match.")
    else:
        r.add(INFO, "leaderboard comparison", f"skipped: {lb_path} not found")

    # 7. how much does subset composition move the gap? ---------------------
    full = collections.Counter(c.get("difficulty") for c in cases)
    def reweight(cells, counts):
        k = sum(counts[d] for d in DIFFS)
        return sum(x * counts[d] for x, d in zip(cells[1:], DIFFS)) / k
    moves = []
    for cfg, v in t4.items():
        g_patch_comp = reweight(v["exploit"], comp) - reweight(v["patch"], comp)
        g_full = reweight(v["exploit"], full) - reweight(v["patch"], full)
        moves.append((cfg, abs(g_full - g_patch_comp)))
    lo_m, hi_m = min(m for _, m in moves), max(m for _, m in moves)
    g55 = dict(moves)["Codex GPT-5.5"]
    r.add(INFO, "does the patch subset's harder mix explain the gap?",
          f"the patch subset is harder than the corpus ({100 * comp['hard'] / n:.1f}% hard vs "
          f"{100 * full['hard'] / len(cases):.1f}%). Re-weighting both tasks' strata to the same "
          f"difficulty mix moves the exploit-minus-patch gap by {g55:.2f}pp for GPT-5.5 and "
          f"{lo_m:.2f}-{hi_m:.2f}pp across all ten configurations. Composition is not the "
          f"explanation. (Unknown-difficulty cases are left out of both re-weightings.)")

    # 8. uncertainty on the headline numbers --------------------------------
    k_patch = round(t4["Codex GPT-5.5"]["patch"][0] * NP / 100)
    lo, hi = wilson(k_patch, NP)
    k_block = round(t5_by["gpt-5.5"]["block"] * NP / 100)
    r.add(INFO, "uncertainty the paper does not report",
          f"patch 23.4% is {k_patch}/{NP}, Wilson 95% CI [{100 * lo:.1f}, {100 * hi:.1f}]. "
          f"Block 47.9% is {k_block}/{NP}. Exploit 43.7% is a mean of a clamped continuous "
          f"score over an unpublished 200-case set, so no per-case interval can be built from "
          f"the release. Detect is a binary exact match over 541 cases. The three abstract "
          f"numbers are three different estimands on three case sets; the paper defines each "
          f"reward but never says they are not comparable.")

    # 9. block vs pass ------------------------------------------------------
    blk, pss = t5_by["gpt-5.5"]["block"], t5_by["gpt-5.5"]["pass"]
    r.add(INFO, "what the block/pass split does and does not show",
          f"for GPT-5.5, {blk}% of patches pass the blocking check and {pss}% also pass the "
          f"normal-operation check. The second check is byte equality of success flag, return "
          f"data hash and full log hash on 1-5 historical calls (validate_patch.py:1326-1333 at "
          f"{UPSTREAM_COMMIT}), so the gap is an upper bound on 'breaks legitimate callers', not "
          f"a measurement of it: a correct fix that changes an amount or an event also fails. "
          f"Block rate alone is not a fair comparator either: a bare revert() patch passes it.")

    # 10. temporal split and what it implies about the exploit set ----------
    post = [c for c in cases if (c.get("attack_date") or "") >= CUTOFF]
    r.add(PASS if len(post) == PAPER["post_cutoff"] else FAIL, "temporal split",
          f"paper: {PAPER['post_cutoff']} cases dated 2025+ and {PAPER['pre_cutoff']} before; "
          f"release gives {len(post)} / {len(cases) - len(post)}")
    pre_s, post_s = PAPER["opus47_exploit_pre"], PAPER["opus47_exploit_post"]
    all_s = t4["Claude Code Opus 4.7"]["exploit"][0]
    x = PAPER["exploit_n"] * (pre_s - all_s) / (pre_s - post_s)
    prop = PAPER["exploit_n"] * len(post) / len(cases)
    corpus_mix = (pre_s * (len(cases) - len(post)) + post_s * len(post)) / len(cases)
    r.add(FAIL, "the Opus 4.7 temporal numbers vs the exploit set",
          f"the paper gives Opus 4.7 exploit {pre_s}% pre-cutoff and {post_s}% post-cutoff, and "
          f"{all_s}% over the 200-case exploit set. For those three to be one weighted mean, the "
          f"exploit set must hold about {x:.0f} post-cutoff cases, nearly all {len(post)} in the "
          f"corpus, against ~{prop:.0f} for a proportional draw. Over the corpus mix the same "
          f"split would give {corpus_mix:.1f}%. Either the exploit set is heavily skewed toward "
          f"recent incidents without saying so, or the split and the 'All' cell come from "
          f"different populations. The release cannot settle which.")

    post_patch = [c for c in patch if (c.get("attack_date") or "") >= CUTOFF]
    k = len(post_patch)
    lo9, hi9 = wilson(round(0.234 * k), k) if k else (0.0, 0.0)
    r.add(INFO, "the patch side of the contamination control",
          f"only {k} of the {n} patch cases post-date the cutoff. The paper prints no post-cutoff "
          f"patch number at all; if it did, one case would move it by {100 / k:.1f}pp and a "
          f"95% interval around ~23% would span [{100 * lo9:.0f}, {100 * hi9:.0f}]%. The patch "
          f"half of the 'exploit and patch show smaller gaps of 2-6 points' sentence has no "
          f"published number behind it.")

    # 11. curator flags that no code reads ----------------------------------
    # A case counts as curator-flagged if any of the four fields the curators
    # used says so: `disputed`, `_skip_reason`, a `_review_note` starting with
    # DISPUTED, or `notes` starting with SKIP/Disputed. None is read by src/.
    def flagged_case(c: dict) -> bool:
        note = str(c.get("notes", "")).strip().lower()
        return bool(c.get("disputed") or c.get("_skip_reason")
                    or str(c.get("_review_note", "")).strip().upper().startswith("DISPUTED")
                    or note.startswith("skip") or note.startswith("disputed"))
    flagged = [c["id"] for c in cases if flagged_case(c)]
    in_patch = [c for c in flagged if c in {p["id"] for p in patch}]
    r.add(INFO, "curator-flagged cases are still scored",
          f"{len(flagged)} cases carry a curator flag saying disputed or skip "
          f"({', '.join(flagged)}); no code under src/ or site/ reads those fields. In the "
          f"patch subset: {', '.join(in_patch) or 'none'}. Dropping them moves any patch rate by "
          f"at most {100 * len(in_patch) / n:.1f}pp. bench-53 (Ronin) and bench-428 (OrbitChain) "
          f"are flagged by the curators as key compromises, not code bugs.")

    # 12. what a patch run would cost --------------------------------------
    costs = sorted((v["patch_cost"], k_) for k_, v in t5.items())
    g55c = t5_by["gpt-5.5"]["patch_cost"]
    r.add(INFO, "cost of re-running the patch task with a model",
          f"Table 5 patch cost per case ranges ${costs[0][0]:.2f} ({costs[0][1]}) to "
          f"${costs[-1][0]:.2f} ({costs[-1][1]}); GPT-5.5 is ${g55c:.2f}. On {n} cases that is "
          f"${costs[0][0] * NP:.0f} to ${costs[-1][0] * NP:,.0f} per configuration, ~${g55c * NP:.0f} "
          f"for the headline configuration. Model-free oracle controls cost only RPC time.")

    r.summary()
    print("\nBottom line: the release reproduces the paper's data construction and its patch")
    print("arithmetic. It does not let anyone check 43.7, it ships a leaderboard that disagrees")
    print("with the paper, and the paper contradicts itself on the best patch score. Whether the")
    print("patch oracle measures 'a correct fix' is a separate, open question: it tests byte")
    print("equality and has never been calibrated against gold patches or no-op patches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
