# Changelog

## v2.3, 2026-10-23

Second patch-oracle calibration (wave 2), no model, no transaction: [calibration/wave2/README.md](calibration/wave2/README.md). (Numbered v2.3 because v2.2 was already taken by the arXiv comment below.)

- The unmodified upstream `validate_patch` CLI at `1cb7410` on the other 47 Ethereum patch cases, three inputs each (unchanged, `revert()`, emit-only); every score is the CLI's `score` field, not the full benchmark scoring path.
- 23 of 47 cases usable; 24 excluded with a named reason (14 harness, 10 baseline, 0 ineligible, 0 rpc). Seven of the baseline failures are `MemoryOOG`/`OutOfGas` on the unchanged recompile, cause not isolated.
- Usable cases, score 1.0 (95% Wilson): unchanged 3 of 23 (4.5% to 32.1%), `revert()` 4 of 23 (7.0% to 37.1%), emit-only 3 of 16 (6.6% to 43.0%; 7 cases are `view`/`pure`). Emit-only counted as blocking the exploit in 16 of 16. Wave 1 + 2: 26 usable cases. No extrapolation to the 94.
- Three hand-written reference fixes: bench-391 and bench-76 scored 1.0; bench-559 (constructor fix per its description) scored 0, as did our runtime variant.
- One case (bench-220) re-run from scratch in a fresh clone: same verdicts. bench-72 re-run after an RPC error line, flaked logs kept.
- New: `calibration/run_wave2.sh`, `wave2_table.py` (usability reason per case, Wilson intervals), `_test_wave2_table.py` (red-first, 9 checks), `parse_runs.py` gains `attack_reproduces`, `make_arms.py` accepts `library`. Articles (EN, RU) carry a "wave 2" section.
- Not done: retry of the five wave-1 non-working cases, the 24 excluded wave-2 cases, an Etherscan-sourced run, the Harbor verifier.

## v2.2, 2026-10-23

- `paper/`: a 5-page technical comment on arXiv:2606.26216, scoped to the claims `make` reproduces, built and checked with pdfLaTeX; arXiv upload package and metadata in `paper/ARXIV.md`.
- New check (16 in total): the paper's sentence "All models show monotonic degradation from easy to hard cases" fails in 11 of 30 rows of its own Table 4, including GPT-5.5 exploit (39.8 / 50.5 / 33.2) and patch (19.4 / 32.6 / 11.1). Red-first test extended in the reverse direction: making every row monotonic flips the check to PASS.
- Fixed: README linked `calibration/RESULTS.md`; the file is `results.md` (GitHub paths are case-sensitive).

## v2.1.1, 2026-10-22

- Article (EN and RU) now carries the calibration as "Pass four" and no longer says that nothing was measured; "What the numbers can and cannot say" moved after it.
- Every figure in pass four was re-checked by the consolidating session against the raw forge logs, `bytecode_diff.jsonl`, the upstream code at `1cb7410` and Sourcify (bench-76: 999,999 optimizer runs, `london`). New in that check: the hard-coded `optimizer: runs 200` in `compile_dfhl_fixed_bytecode` (`legacy.py:226`) is called by the scoring path too (`evaluator.py:741`), not only by the CLI we ran.
- Wording corrected after an external fact-check (Codex): "could not discriminate any patch" became "gave the same score to all three inputs"; "harmless" became "adds an event, no logic change"; bench-559's `proxy_address: null` workaround is now stated where the case is counted as usable; the provenance of each figure (forge logs vs bytecode diff vs Sourcify) is named.

## v2.1, 2026-10-20

First measurement of the patch oracle, no model involved: [calibration/RESULTS.md](calibration/RESULTS.md).

- 8 Ethereum cases x 3 inputs (unchanged, `revert()`, emit-only) through the upstream `validate_patch` CLI at
  `1cb7410`, forks via the free `eth.drpc.org`, forge 1.8.5 (official image), sources from Sourcify.
- 3 cases usable: a fix-nothing input scored 1.0 once per input (bench-391 revert and emit-only, bench-76
  unchanged). 5 cases could not discriminate (bench-247 compiled the wrong contract; bench-322, 410 and 05 do not
  reproduce the attack before patching; bench-449's only normal tx is a contract creation).
- Observed: an RPC failure inside the oracle's score replay read as "exploit still passes" (score 0.0 instead of
  1.0 for the same patch); `proxy_address: null` crashes the attack replay (`attack_replay.py:259`); the
  recompile step hard-codes optimizer runs 200 (`legacy.py:226`) while real settings differ.
- Second pass in a fresh clone reproduced bench-391 (unchanged 0.0, revert 1.0, emit-only 1.0 after one RPC retry).
- `parse_runs.py` derives every number from raw forge logs; `_test_parse_runs.py` (11 checks) shows it turning red
  on damaged logs.
- Not done: reference fixes, the remaining 47 Ethereum cases, an Etherscan-sourced run, BSC, the Harbor verifier.
  We tried the Docker route first: the daemon was off and was started; the macOS forge release needed `libusb`,
  so the Docker image is used through a shim.
- README: "Scope", "What the patch oracle actually tests" and "The next measurement" updated.

## v2, 2026-10-20

A second review (see [FINDINGS.md](FINDINGS.md)) found errors in v1 of this audit and new
findings in the upstream release. Everything below that touches the upstream code was re-read
by hand at commit `1cb7410` before publishing.

### Corrections to our own v1

| v1 said | What is true |
| --- | --- |
| "They do. This repository reproduces them", "the headline numbers are real", "Yes. Confirmed" | We checked the patch arithmetic and the data construction. 43.7 cannot be checked from the release, and no model or oracle was ever run. |
| The adversarial review was "two independent frontier models" | One adversarial refutation (Gemini 3.1 Pro), whose prompt already named the `revert()` objection, plus one adjudication (GLM-5.3) that saw the rebuttal first. Codex failed with HTTP 400, Grok timed out. Both prompts and responses are now in `panel/`. |
| Scope: "all of it on local forks of historical state" | No fork was run at all. |
| The 94 patch cases are "easy 31 / medium 43 / hard 18" | That is 92. Two more are labelled `unknown` (bench-05, bench-57). With them as their own group all ten Table 4 patch rows are whole-case counts; our "nine of ten reproduce" was an artifact of leaving them out, hidden by a `PASS if len(bad) <= 1` threshold. |
| Difficulty composition accounts for "~2pp" of the gap | 0.17pp for GPT-5.5, 0.01-0.70pp across the ten configurations. |
| "The exploit/patch pair is not a capability ratio" was framed as rebutting a ratio the paper draws | The paper's only explicit ratio is patch 23.4 vs detection type accuracy 56.4. The real point covers all three abstract numbers: three estimands on three case sets presented as one scale. |
| "GPT-5.2 inverts the gradient" | Used the exploit-vs-patch comparison our own section 1 rules out. Dropped as an argument; the GPT-5.2 row now appears only as part of the paper's internal inconsistencies. |
| "One Table 5 cell is wrong" | Three Table 5 cells are not k/94; the GPT-5.2 pair fits k/57. Reported as an inconsistency, not a typo. The paper also gives three different best patch scores (21.3, 23.4, 24.5), not two. |
| "51% of exploit-blocking patches break legitimate callers" | The oracle tests byte equality of success, return data and logs. The gap is an upper bound on caller breakage, not a measurement of it. |
| A model re-run costs "$2.39-$21.86 per case" | $2.39 is the exploit cost. Patch is $0.06-$21.86 per case, $2.31 for GPT-5.5, about $217 on 94 cases. |
| The paper's per-difficulty table is "Table 3" | It is Table 4. Table 3 is a worked example. |
| `_test_red_first.py` | Hardcoded our own `../repo` layout and failed for anyone following the README. Now takes `--upstream`. |
| Footer credited Codex and Grok as reviewers | They produced no review on 2026-10-07. |
| No mention of prior work on the upstream code | shane-moore opened issue #8 and PRs #1-#7 on 2026-10-02. Now credited. |

### New findings

- The authors' own `site/assets/leaderboard.json` differs from Table 4 for 6 of 10 configurations.
- The paper's three Opus 4.7 exploit numbers imply about 85 post-cutoff cases in the 200-case set (corpus has 86; a proportional draw gives ~32).
- The paper prints no post-cutoff patch number, though its text claims a 2-6 point patch gap.
- Patch oracle, read from code: preservation is byte equality; blocking is any observable change; out-of-gas counts as preserved; the patch is `vm.etch`-ed, at different addresses in the two checks, not deployed via proxy upgrade; the agent can see the scoring calls; best-of-history skips the no-op guard; the prompt promises partial credit the scorer never gives; the explorer's verified compiler version is fetched but not used.
- Exploit oracle: an unpriceable profit or a missing reference profit scores full credit.
- Nine curator-flagged cases (disputed/skip) are scored; two are in the patch subset.
- The paper's filter arithmetic 153 − 31 − 29 is 93, not 94; `unknown` difficulty is silently counted as easy on the site.

### Repository

- Pinned upstream to `1cb7410`; `make`, `make red`, `make tables`.
- Tables are parsed from the arXiv HTML into `data/paper-table-N.csv` by `extract_tables.py`; the audit reads the CSVs instead of hand-typed literals. SHA-256 of the HTML in `data/paper.sha256`.
- Audit grew from 10 to 15 checks; red-first test covers 4 mutations.
- Article in `docs/`, English and Russian.

## v1, 2026-10-07

First audit: reproduced the 94-case patch subset, the temporal split and the patch strata;
found `exploit_subset200` unshipped; ran a two-prompt adversarial panel.
