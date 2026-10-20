#!/usr/bin/env python3
"""Stage verified sources for a CyberChainBench case from Sourcify (no API key).

Upstream expects data/sources/DeFiHackLabs/verified_source_by_address/<chain>/<addr>/
with flat files ("/" -> "_") plus _metadata.json. That tree is not in the release,
so we rebuild it from Sourcify's verified sources.
usage: stage_sources.py <upstream_root> <case_id>
"""
import json
import sys
import urllib.request
from pathlib import Path

root, case_id = Path(sys.argv[1]), sys.argv[2]
case = json.loads((root / "data/benchmark/cases" / f"{case_id}.json").read_text())
addr = case["vulnerable_address"].lower()
url = f"https://sourcify.dev/server/v2/contract/1/{addr}?fields=sources,compilation"
req = urllib.request.Request(url, headers={"User-Agent": "ccb-calib"})
d = json.load(urllib.request.urlopen(req, timeout=60))
comp = d["compilation"]
settings = comp.get("compilerSettings", {})
out = root / "data/sources/DeFiHackLabs/verified_source_by_address/ethereum" / addr
out.mkdir(parents=True, exist_ok=True)
files = []
for path, v in d["sources"].items():
    if "_" in path:
        print("WARN underscore in path (unflatten will break):", path, file=sys.stderr)
    flat = path.replace("/", "_")
    (out / flat).write_text(v["content"])
    files.append(flat)
meta = {
    "chain": "ethereum",
    "address": addr,
    "files": sorted(files),
    "contract_name": comp.get("name", ""),
    "target_contract_name": comp.get("name", ""),
    "compiler_version": comp["compilerVersion"],
    "optimization_used": settings.get("optimizer", {}).get("enabled", True),
    "optimization_runs": settings.get("optimizer", {}).get("runs", 200),
    "evm_version": settings.get("evmVersion", ""),
    "source": "sourcify",
    "runtimeMatch": d.get("runtimeMatch"),
    "creationMatch": d.get("creationMatch"),
}
(out / "_metadata.json").write_text(json.dumps(meta, indent=1))
keys = ("contract_name", "compiler_version", "optimization_used", "optimization_runs", "runtimeMatch")
print(json.dumps({"dir": str(out), "files": len(files), "meta": {k: meta[k] for k in keys}}))
