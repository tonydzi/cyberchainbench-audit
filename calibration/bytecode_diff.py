#!/usr/bin/env python3
"""Why does an UNCHANGED source sometimes count as 'blocked'?

Compile the unchanged verified source exactly as upstream does (compile_dfhl_fixed_bytecode),
fetch the on-chain runtime code of the vulnerable address at the fork block, and report
where they differ (immutable slots / metadata hash tail / real code differences).
usage: bytecode_diff.py <upstream_root> <case_id>   (run with PYTHONPATH=<upstream_root>/src)
"""
import json
import sys
from pathlib import Path

root, case_id = Path(sys.argv[1]).resolve(), sys.argv[2]
from benchmark.loader import BenchmarkLoader  # noqa: E402
from infra.chain.metadata import lookup_runtime_code, resolve_case_source_metadata  # noqa: E402
from infra.solidity.legacy import compile_dfhl_fixed_bytecode  # noqa: E402
from infra.cli.validate_patch import _resolve_case, _pick_case_contract_address  # noqa: E402

case = _resolve_case(root, case_id)
addr = _pick_case_contract_address(case)
meta = resolve_case_source_metadata(case.id, root, chain="ethereum", address=addr,
                                    file_hint=case.raw.get("file", ""), explicit_metadata=case.raw)
src_dir = root / meta["source_dir"]
target = Path(sys.argv[3]) if len(sys.argv) > 3 else None
fixed = (target or next(Path(root.parent / "arms" / case_id).glob("unchanged.sol"))).read_text()
bc, ver, name = compile_dfhl_fixed_bytecode(base_dir=root, case_id=case.id, fixed_code=fixed,
                                            contract_name_hint=meta.get("target_contract_name", ""),
                                            source_metadata=meta)
block = int(case.raw["block_number"]) - 1
chain_code = lookup_runtime_code("ethereum", addr, block)
chain_hex = chain_code[2:] if chain_code.startswith("0x") else chain_code
n = min(len(bc), len(chain_hex))
diff = [i for i in range(0, n, 2) if bc[i:i + 2] != chain_hex[i:i + 2]]
# group differing byte offsets into runs
runs, start, prev = [], None, None
for i in diff:
    if start is None:
        start = prev = i
    elif i - prev <= 2:
        prev = i
    else:
        runs.append((start // 2, (prev - start) // 2 + 1)); start = prev = i
if start is not None:
    runs.append((start // 2, (prev - start) // 2 + 1))
print(json.dumps({"case": case_id, "compiled_contract": name, "solc": ver, "compiled_bytes": len(bc) // 2,
                  "onchain_bytes": len(chain_hex) // 2, "differing_bytes": len(diff),
                  "diff_runs_offset_len": runs[:40], "n_runs": len(runs)}))
