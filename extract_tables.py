#!/usr/bin/env python3
"""Extract every <table> in the arXiv HTML of CyberChainBench into CSV files.

Why this exists: the paper's flattened text puts table cells in a misleading
order, and reading numbers off it silently mis-attributes cells. The audit's
transcribed values (TABLE4_* and TABLE5_* in verify_cyberchainbench.py) were
parsed structurally with exactly this routine, so anyone can diff them.

Usage:
    python3 extract_tables.py data/paper-arxiv-2606.26216v1.html data/

Writes data/paper-table-N.csv (N = 1..6, in document order, which matches the
paper's own "Table N" numbering for this arXiv version) and data/paper.txt
(the flattened text, kept only for grep).
"""
from __future__ import annotations

import csv
import html
import os
import re
import sys


def cells(row: str) -> list[str]:
    out = []
    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S):
        c = re.sub(r"<math.*?</math>", "", c, flags=re.S)
        c = html.unescape(re.sub(r"<[^>]+>", " ", c))
        out.append(re.sub(r"\s+", " ", c).strip())
    return out


def main(src: str, out_dir: str) -> int:
    s = open(src, encoding="utf-8", errors="replace").read()
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    tables = re.findall(r"<table.*?</table>", s, flags=re.S)
    if not tables:
        print("no <table> found; is this the arXiv HTML rendering?", file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    for i, tb in enumerate(tables, 1):
        rows = [r for r in (cells(x) for x in re.findall(r"<tr.*?</tr>", tb, flags=re.S)) if r]
        path = os.path.join(out_dir, f"paper-table-{i}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        print(f"{path}: {len(rows)} rows; header: {' | '.join(rows[0])[:80]}")
    text = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    with open(os.path.join(out_dir, "paper.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    caps = re.findall(r"Table (\d+)\s*:", text.replace("\n", " "))
    print(f"captions found in text order: {caps}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
