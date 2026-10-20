# Patch-oracle calibration: first measurement (2026-10-20)

No model was called. The upstream `validate_patch` CLI at `1cb7410` was run unchanged on forks of
historical Ethereum state, with three fixed inputs per case. Every number below is parsed from the raw
forge output in `runs/` by `parse_runs.py` (not from the oracle's own JSON); the oracle's score is
shown next to it and the two are cross-checked.

Arms (built by `make_arms.py` from the verified source of the labelled vulnerable function):

- **unchanged**: the verified source, byte for byte.
- **revert**: the first statement of the vulnerable function becomes `revert();`.
- **emit_only**: an event is declared and emitted as the first statement; the vulnerable logic is untouched.

## Result, 8 cases, 24 runs

| case | usable? | unchanged | revert | emit_only | what the logs show |
| --- | --- | --- | --- | --- | --- |
| bench-391 BBT | yes | 0.0 | **1.0** | **1.0** | revert zeroes the attacker's profit. emit_only keeps the **full** profit (`AFTER_PROFIT == BEFORE_PROFIT`) and is still "blocked", because the extra event changes the log hash. Normal replay 1/1 preserved: that call never touches `setRegistry`. |
| bench-559 ChiSale | yes, after a workaround | 0.0 | 0.0 | 0.0 | unchanged is not blocked and preserved 1/1 (correct). revert: blocked, normal fails (`success changed`). emit_only: blocked via log hash, normal fails (`logs changed`): **a harmless added event fails the normal replay on the function it touches**. Needs `proxy_address: null` removed, see below. |
| bench-76 HYPR | yes | **1.0** | 0.0 | 0.0 | the **unchanged** source is "blocked" (profit 2.57e24 to 0) and normal replay 1/1 preserved, so it scores full marks. The compiled runtime is 8490 bytes against 11380 on chain. revert and emit_only fail the normal replay (`success changed`, `logs changed`). |
| bench-247 Dexible | no (harness) | 0.0 | 0.0 | 0.0 | identical gas in all three arms (576446). The compile step etched a contract named `ERC20` (2130 bytes) over a target that is 18475 bytes on chain; every arm is "blocked" and every normal replay fails (`success changed`). |
| bench-322 Lifiprotocol | no (baseline) | 0.0 | 0.0 | 0.0 | attack replay fails before any patch: `Contract 0x986a... does not exist and is not marked as persistent`. No patch could score. |
| bench-410 FILX | no (baseline) | 0.0 | 0.0 | 0.0 | `historical attack tx did not succeed before patch` in all arms. No patch could score. |
| bench-05 SushiSwap Miso | no (baseline) | 0.0 | 0.0 | 0.0 | the attack still reproduces after `revert()` in `batch` (3/3 normal replays preserved in every arm). Cause not isolated. |
| bench-449 SuperRare | no (ineligible) | n/a | n/a | n/a | the only normal tx is a contract-creation tx (`to: null`); the CLI drops it and returns `case normal_txs field is empty`. |

Counts: a fix-nothing input scored 1.0 in **1 of 3 usable cases per input** (unchanged: bench-76; revert:
bench-391; emit_only: bench-391). Scores above 0 appeared in 2 of the 3 usable cases (bench-391, bench-76).
5 of 8 cases could not discriminate any patch in this setup. This is a pilot of 3 usable cases, not an
estimate of a rate over 94.

Full per-run table: [results.md](results.md) and [results.csv](results.csv).

## What this changes

1. **The two directions of the oracle's strictness are both real.** Blocking is "any observable change"
   (`attack_replay.py:227`), so `emit_only` and `revert` both pass in bench-391. Preservation is byte
   equality of success, return data and the full log stream, so in bench-559 and bench-76 a patch that only
   adds an event, or only reverts, fails the normal replay on the function it touches.
2. **An unchanged source can score 1.0 (bench-76), and a contract-name mix-up can make it score 0
   everywhere (bench-247).** Both come from the same step: the verified source is recompiled and the result
   is `vm.etch`-ed over the target. That step hard-codes `optimizer {enabled: true, runs: 200}` and passes no
   EVM version (`src/infra/solidity/legacy.py:226`, in `compile_dfhl_fixed_bytecode`), while the real settings differ:
   bench-76 999999 runs, bench-247 100 runs, bench-322 1000000 runs, bench-410, bench-449 and bench-559 optimizer
   off (`bytecode_diff.jsonl`, `stage_sources.py` metadata). The cause of the bench-76 mismatch is not isolated;
   hard-coded settings and zeroed immutables are the candidates.
3. **An RPC error becomes a verdict.** In the first clean-clone pass, bench-391 emit_only scored 0.0 instead of
   1.0: the oracle's own score replay hit `sharedbackend: Failed to send/recv storage` on the free RPC, the
   test printed `historical attack tx did not succeed before patch`, and the score read that as "exploit still
   passes". The CLI's second replay of the same patch succeeded. The log is kept in
   `run2-flaked-try1/`; the retry gave 1.0. This is the failure class the upstream replay-accounting PRs (#1-#7) are about; here it is observed rather than read.
4. **`proxy_address: null` crashes the attack replay.** `attack_replay.py:259` does
   `str(raw.get("proxy_address", ""))`, which turns JSON null into the string `"None"`. 4 of the 55 Ethereum
   patch cases have a null proxy (bench-559, 562, 565, 567); bench-559 failed with
   `ValueError: invalid literal for int() with base 16: 'None'`. We re-ran it with the key removed
   (`arms/bench-559/case-without-null-proxy.json`, passed through `--benchmark-dir`). bench-567 is the case in
   upstream issue #8; the null-proxy normalisation is already in PR #1-#7, which we have not reproduced.

## Second pass (different method, clean directory)

A fresh clone of the upstream at `1cb7410`, a fresh `forge-std`, the same scripts, bench-391 with all three
arms from scratch ([results-second-pass.md](results-second-pass.md)): unchanged 0.0, revert 1.0, emit_only 1.0.
Forge outputs differ in timing lines, so the checksums differ; the verdict markers and profits are identical.
The first emit_only try in that pass scored 0.0 because of the RPC error in item 3 and was re-run once
(both runs are kept).

## Parser, red-first

`parse_runs.py` refuses to guess: a log with no forge verdict, or a PASS without its marker, raises.
`_test_parse_runs.py` (11 checks, all green) damages real logs on a copy and asserts the answer changes:
removed BLOCKED marker raises; truncated log raises; a FAIL flips `normal_ops_pass`; an OutOfGas line counts as
preserved (the oracle's rule); an RPC error line is flagged and a hex string containing `429` is not (the first
version of the regex flagged it, found while building the table); a score lane that disagrees with the CLI lane is
reported.

## Limits and deviations

- **Source from Sourcify, not Etherscan.** No Etherscan key was available on this node (a fleet request is open).
  `stage_sources.py` rebuilds the `verified_source_by_address` layout from Sourcify's verified sources
  (`runtimeMatch` is `exact_match` or `match`, recorded in each `_metadata.json`). The upstream explorer path
  (`lookup_verified_source`) was not exercised.
- **Free RPC.** `https://eth.drpc.org`, no key, one transient failure seen across about 30 CLI runs.
- **forge 1.8.5 from the official Docker image.** The macOS release binary needs `libusb`; the shim
  (`forge-docker`) rewrites `--use /Users/.../solc-vX` to a Linux `solc` from `binaries.soliditylang.org`.
  A different forge version could change gas and some verdicts.
- **Only the CLI path.** The Harbor verifier and `/app/workspace/case_data.json` were not run; the crash in item 4
  is on the CLI path (`evaluate_patch`).
- **Arms are mechanical.** `revert` and `emit_only` are inserted into the case's labelled function by regex. For
  bench-05 and bench-322 the labelled function may not be on the attack path, which would make those results
  uninformative about the oracle.
- **No hand-written reference fix was run**, so false rejections of correct patches are only shown by the
  `emit_only`-style cases above, not measured.
- Ethereum only. No BSC case: no free archive RPC found.
