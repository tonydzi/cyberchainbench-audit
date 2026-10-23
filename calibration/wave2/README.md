# Patch-oracle calibration, wave 2 (2026-10-23)

No model was called and no transaction was sent. The upstream `validate_patch` CLI at `1cb7410` was run unchanged
on forks of historical Ethereum state (free archive `eth.drpc.org`, forge 1.8.5 from the official image, sources from
Sourcify), with the same three inputs as wave 1 (unchanged, `revert()`, emit-only). "Score" below always means the
`score` field of the `validate_patch` CLI. The benchmark's runner or Harbor verifier was not run, so this is not the
full scoring path.

Every number is parsed from the raw forge output in `runs/` by `parse_runs.py` and `wave2_table.py` (one-line
verdict markers, not the oracle's JSON). The oracle's own verdict agrees with the parse in all runs
(`disagree_with_oracle: 0` in `summary.json`).

## Scope and denominator

- Cases: the 55 Ethereum patch cases (`fixable`, `has_public_source`, with `normal_txs`) minus the 8 of wave 1 = 47.
- A case is **usable** only if the `unchanged` and `revert` arms have no compile error and no RPC error line, the
  historical attack reproduces before the patch, and the `revert` arm blocks it (so the blocking check can be satisfied at all).
  The emit-only arm is judged separately (see the `view`/`pure` note). Otherwise the case is excluded with a
  reason: `harness`, `baseline`, `ineligible`, `rpc`.
- **Usable: 23 of 47.** Not usable: 24 = 14 harness, 10 baseline, 0 ineligible, 0 rpc (see `results.md`, column "reason").
- 7 of the 23 usable cases are `view`/`pure` functions: an event cannot be emitted there, so the emit-only arm is
  invalid and these 7 count only in the unchanged and revert columns (emit-only denominator is 16).
- No extrapolation to the 94 patch cases of the paper's evaluation subset. The five wave-1 non-working cases were not
  retried: bench-322 and bench-410 are baseline failures no input can fix; bench-449 is dropped by the CLI; bench-05
  has an unisolated cause; bench-247 (wrong contract etched) may be fixable on our side but was not attempted.

## Result (usable cases, 95% Wilson interval)

| input | validate_patch CLI score 1.0 | usable cases with this arm | interval |
|---|---|---|---|
| unchanged | 3 (bench-239, 534, 567) | 23 | 4.5% to 32.1% |
| revert | 4 (bench-220, 239, 34, 515) | 23 | 7.0% to 37.1% |
| emit_only | 3 (bench-220, 239, 515) | 16 | 6.6% to 43.0% |
| emit_only counted as blocking the exploit | 16 | 16 | 80.6% to 100.0% |
| emit_only with attacker profit exactly unchanged | 8 | 16 | 28.0% to 72.0% |

Wave 1 and wave 2 together (26 usable cases; 19 with a valid emit-only arm): unchanged 4 of 26 (6.2% to 33.5%),
revert 5 of 26 (8.5% to 37.9%), emit_only 4 of 19 (8.5% to 43.3%).

Reading: the strict "any observable change" rule for blocking fired on all 16 emit-only runs, and in 8 of them the
attacker's profit was exactly the same number before and after. In all 13 emit-only runs that scored 0 the normal
replay was not fully preserved (`preserved_count` below `checked_count` in `results.csv`); the forge output names `logs changed`
in 8 of them and `success changed` in 1, the other 4 fail with a message not categorised here. 3 runs scored 1.0. Three cases gave 1.0 to the unmodified source
(bench-239, 534, 567; bench-567 is the case in upstream issue #8).

## Why the other cases are excluded

- 5 harness: our arm builder found no matching Solidity function (bench-121, 157, 257, 465, 483: not a plain
  Solidity function in the staged files).
- 7 harness: the oracle's recompile of the staged sources fails in the `revert` and `emit_only` arms, while the
  `unchanged` arm does run (bench-151, 181, 21, 336, 423, 48, 524; `DeclarationError` on flattened imports; the
  Sourcify layout may be the cause, Etherscan was not available).
- 2 harness: compile error inside forge in an arm (bench-136, 252).
- 7 baseline: the attack replay already fails with `MemoryOOG` or `OutOfGas` on the unchanged recompiled source
  (bench-02, 103, 112, 198, 31, 416, 562). Cause not isolated; one probe that raised forge's memory limit did not
  change it (`FOUNDRY_MEMORY_LIMIT`, bench-02). Zeroed immutables in the recompile are a candidate, not tested.
- 2 baseline: attack does not succeed before patch (bench-433, 434). 1 baseline: attack still passes after
  `revert()` (bench-518).
- bench-72: first run showed an RPC error line; rerun gave a clean result and it is usable. The flaked logs are in
  `runs-flaked-try1/`.

## Hand-written reference fixes (ceiling pilot, 3 cases)

Written by hand from each `fix_description`; sources in `reference-fixes-src/`, raw logs in
`runs-reference-fixes/`.

| case | fix | validate_patch CLI score |
|---|---|---|
| bench-391 | `setRegistry` gets the same `msg.sender` check as `setMaxSupply` | 1.0 |
| bench-76 | `initialize` only callable by the ERC-1967 proxy admin (zero admin = constructor context) | 1.0 |
| bench-559 | constructor `>` becomes `==`, as the description says | 0.0 |
| bench-559 (runtime variant, ours) | `buy` seeds `maxBonusThreshold` from the last tier | 0.0 (exploit still passes, not diagnosed) |

bench-559: the description's fix lives in the constructor, which does not run when the recompiled runtime is etched over
the deployed state, so a constructor-only fix would not change what the oracle replays. That is the likely explanation from reading the
mechanism, not an isolated cause; the runtime variant failing as well does not settle it. Two of three references
passing is a pilot count, not a rate.

## Second pass

bench-220, all three arms from scratch in a fresh clone of upstream at `1cb7410` (`second-pass-bench-220/`):
unchanged 0.0, revert 1.0, emit_only 1.0, the same verdicts as the first pass. A first attempt of this pass failed
for an environment reason (forge-std not present in the fresh clone, compile error, all zeros) and is not counted.
Forge timing lines differ so file checksums differ; verdict markers are identical.

## Files

`results.md`, `results.csv`, `summary.json` (generated by `wave2_table.py`), `runs/` (raw logs), `runs-flaked-try1/`,
`runs-reference-fixes/`, `second-pass-bench-220/`, `reference-fixes-src/`, `stage.log`, `arms.log`, `arms-failed.txt`,
`ids.json`. Reproduce: `stage_sources.py`, `make_arms.py`, `run_wave2.sh <ids>`, then
`wave2_table.py runs ids.json out --arms-failed arms-failed.txt`. Tests: `_test_parse_runs.py`, `_test_wave2_table.py`.
