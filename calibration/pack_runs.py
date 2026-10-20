#!/usr/bin/env python3
"""Copy raw run evidence into the repo with local paths replaced by $CCB.

usage: pack_runs.py <runs_dir> <dest_dir> <ccb_root>
Keeps: stdout.json (oracle verdict), stderr.log, forge_output.txt of both attack lanes and the
normal-replay lane. Text is copied byte-for-byte except the absolute checkout path.
"""
import shutil
import sys
from pathlib import Path

runs, dest, root = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
keep = ("stdout.json", "stderr.log", "rc.txt")
n = 0
for arm in sorted(p for p in runs.glob("*/*") if p.is_dir()):
    out = dest / arm.parent.name / arm.name
    for f in list(arm.glob("*")) + list(arm.glob("attack_tx_replay*/*/forge_output.txt")) + list(arm.glob("normal_tx_replay/*/forge_output.txt")):
        if not f.is_file() or (f.parent == arm and f.name not in keep):
            continue
        rel = f.relative_to(arm)
        tgt = out / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        text = f.read_text(errors="replace").replace(root, "$CCB").replace(str(Path.home()), "$HOME")
        tgt.write_text(text)
        n += 1
print("files:", n)
