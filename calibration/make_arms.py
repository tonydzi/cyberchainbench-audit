#!/usr/bin/env python3
"""Build the three calibration arms for one staged case.

arms: unchanged   - byte-identical copy of the verified target file
      revert      - first statement of the vulnerable function becomes `revert();`
      emit_only   - adds an event and emits it as first statement; vulnerable logic untouched
usage: make_arms.py <upstream_root> <case_id> <target_flat_file> <outdir>
"""
import json
import re
import sys
from pathlib import Path

root, case_id, target, outdir = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
case = json.loads((root / "data/benchmark/cases" / f"{case_id}.json").read_text())
src_dir = root / "data/sources/DeFiHackLabs/verified_source_by_address/ethereum" / case["vulnerable_address"].lower()
fn = case["function"].split("(")[0].strip()
if target == "auto":
    want = Path(case.get("file", "")).name
    fn_re = re.compile(r"function\s+" + re.escape(fn) + r"\s*\(")
    cands = [p for p in sorted(src_dir.glob("*.sol")) if fn_re.search(p.read_text())]
    named = [p for p in cands if want and p.name.endswith(want)]
    pick = (named or cands or [None])[0]
    if pick is None:
        sys.exit(f"auto: no file with function {fn} in {src_dir}")
    target = pick.name
text = (src_dir / target).read_text()

m = list(re.finditer(r"function\s+" + re.escape(fn) + r"\s*\(", text))
if not m:
    sys.exit(f"function {fn} not found in {target}")
if len(m) > 1:
    print(f"WARN {len(m)} matches for {fn}; using first", file=sys.stderr)
brace = text.index("{", m[0].end())
# skip over a possible `{` inside the parameter list is not an issue (no braces in params)
contract_open = None
for cm in re.finditer(r"^[ \t]*(?:abstract\s+)?contract\s+\w+(?:\s+is\s+[^{;]+)?\s*\{", text, re.M):
    if cm.end() < m[0].start():
        contract_open = cm.end()
assert contract_open is not None, "no enclosing contract found"

outdir.mkdir(parents=True, exist_ok=True)
(outdir / "unchanged.sol").write_text(text)

rev = text[: brace + 1] + " revert();" + text[brace + 1 :]
(outdir / "revert.sol").write_text(rev)

emit = text[: brace + 1] + " emit CCBCalibNoop();" + text[brace + 1 :]
emit = emit[:contract_open] + " event CCBCalibNoop();" + emit[contract_open:]
(outdir / "emit_only.sol").write_text(emit)
print(json.dumps({"case": case_id, "function": fn, "target": target, "arms": ["unchanged", "revert", "emit_only"]}))
