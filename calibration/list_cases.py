import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
for c in sys.argv[2:]:
    d = json.loads((root / f"data/benchmark/cases/bench-{c}.json").read_text())
    print(c, d["name"], d["chain"], d.get("vulnerable_address"), d.get("proxy_address"), d["file"], d["function"],
          "atk", len(d.get("attack_txs", [])), "norm", len(d.get("normal_txs", [])), d.get("block_number"))
