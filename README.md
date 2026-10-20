# cyberchainbench-audit

An independent audit of **CyberChainBench**
([arXiv:2606.26216v1](https://arxiv.org/abs/2606.26216), Huang, Jiang, Poovendran, Lin, 24 Jun 2026)
against the benchmark's own public release,
[defai-labs/CyberChainBench](https://github.com/defai-labs/CyberChainBench) at commit `1cb7410` (tag `v1.0`).

The paper's abstract:

> Results reveal a clear difficulty gradient: the best configuration scores 37.5% on detection,
> **43.7% on exploitation, but only 23.4% on patching**.

We set out to show that number was wrong. It is not wrong arithmetically. What we found
instead is narrower and, we think, more useful: what the release lets anyone check, what it
does not, where the paper contradicts itself, and what the patch oracle actually tests.

**Read the article:** [docs/article-en.md](docs/article-en.md) · [docs/article-ru.md](docs/article-ru.md)
**Every finding with its verification record:** [FINDINGS.md](FINDINGS.md)
**What changed since v1 of this audit, including our own errors:** [CHANGELOG.md](CHANGELOG.md)

## Run it

No API keys, no RPC, no model, no spend.

```bash
git clone https://github.com/tonydzi/cyberchainbench-audit && cd cyberchainbench-audit
make            # clones upstream at 1cb7410 and runs the audit
make red        # proves the green checks go red on corrupted data
```

Or by hand: `git clone https://github.com/defai-labs/CyberChainBench.git && git -C CyberChainBench checkout 1cb7410 && python3 verify_cyberchainbench.py --upstream CyberChainBench`.

## What reproduces

| Paper says | Release gives |
| --- | --- |
| 541 incidents | 541 case files |
| patch subset of 94 | the code's filter (`fixable` + verified source + ≥1 normal tx) gives exactly 94: easy 31, medium 43, hard 18, and 2 labelled `unknown` (bench-05, bench-57) |
| pre-filter of "153 proxy cases" | `fixable is True` gives 153. The count matches, the label does not: the code never consults `proxy_address` |
| best patch score 23.4% (Codex × GPT-5.5) | Table 4's patch cells are whole-case counts for all 10 configurations once the 2 `unknown` cases are their own group; GPT-5.5 is 22/94 |
| 86 post-cutoff / 455 pre-cutoff | 86 / 455 |

The counts and the patch arithmetic check out.

## What does not

1. **43.7 cannot be checked from the release.** The exploit task runs on `exploit_subset200`
   (`src/scripts/2_eval/eval.py:475-477`), a generated directory that is gitignored, not shipped,
   absent from every fork we checked, and built by no released code. The paper gives no
   sampling rule. A paired exploit-vs-patch measurement is still possible: run exploit on the
   94 patch contracts.
2. **The paper names three different best patch scores.** 21.3 ("Opus 4.7 leads on patch pass
   rate", section 4), 23.4 (abstract and section 4) and 24.5 (Codex × GPT-5.2 in Table 4). The
   same section 4 sentence makes Opus 4.7 the realized-profit leader at $45.5M, while the
   abstract and Table 5 give $57.4M to GPT-5.5.
3. **Table 4 and Table 5 disagree.** They report the same patch quantity and agree for 9 of 10
   configurations. For GPT-5.2 Table 4 says 24.5, Table 5 says 17.5. Three Table 5 cells
   (GPT-5.2 block 56.1 and pass 17.5, DeepSeek block 54.0) are not k/94 for any integer k. The
   GPT-5.2 pair fits k/57, so a different denominator is as plausible as a typo. We call it an
   inconsistency.
4. **The leaderboard the authors ship disagrees with the paper.** `site/assets/leaderboard.json`
   differs from Table 4 for 6 of 10 configurations on at least one task (paper vs site: GLM-5.1
   patch 3.2 vs 9.6, GPT-5.5 detect 37.5 vs 51.4). Its builder says the Codex rows came from an
   older leaderboard. The GPT-5.5 headline cells 43.7 and 23.4 match.
5. **The temporal numbers imply a skewed exploit set.** The paper gives Opus 4.7 exploit 44.9%
   before the cutoff, 38.8% after, and 42.3% over the 200-case set. For those to be one weighted
   mean the set must hold about 85 post-cutoff cases, almost all 86 in the corpus, against ~32
   for a proportional draw. Either the exploit set leans heavily on recent incidents without
   saying so, or the numbers come from different populations.
6. **The patch half of the contamination control has no number.** The paper says exploit and
   patch "show smaller gaps of 2-6 points" pre vs post cutoff, but prints only an exploit figure.
   Only 9 of the 94 patch cases are post-cutoff; one case would move such a number by 11.1pp.
7. **Smaller things.** The paper's filter arithmetic, 153 − 31 − 29, is 93, not 94; the release
   removes 39 and then 20. The 12 `unknown`-difficulty cases are counted as easy by
   `site/build_cases.py:33-35`, which is the only way the paper's "42% easy" reproduces. Nine
   cases carry curator flags saying disputed or skip; no code reads them, and two (bench-53
   Ronin, bench-428 OrbitChain, both key compromises) sit in the patch subset.

## What the patch oracle actually tests

Read from the code at `1cb7410`. Nothing here was measured on a fork.

- **"Normal operation preserved" is byte equality.** For each replayed historical call,
  `src/infra/cli/validate_patch.py:1330-1332` asserts the same success flag, the same return
  data hash and the same hash of the full log stream. The paper says those calls are
  "successful calls to the same entry point" (section 3). So a correct fix that changes an
  amount or an event on that entry point scores 0. For bench-05 (SushiSwap Miso) the
  case file offers two reference fixes, remove `batch` or switch to WETH transfers; if its five
  replayed calls are `batch` calls, as the paper's description implies, the first fails by
  construction and the second very likely fails too. Accounting-error and price-manipulation make up 41 of the 94 cases; how many
  reference fixes fail has not been measured.
- **"Exploit blocked" is any observable change.** `src/eval/tasks/patch/attack_replay.py:227`
  marks the attack blocked if the call fails, the return data changes, or the logs change. The
  "<1% of original profit" test (line 229) only runs when nothing else changed. The paper says
  the attack "must revert".
- **Out-of-gas counts as preserved.** `validate_patch.py:1608-1612` sets `preserved = True` on
  any MemoryOOG/OutOfGas output, and `checked_count` is `len(results)` (line 1638) whether or not
  the replay reached its check. Open PR #1 by shane-moore removes this.
- **`vm.etch`, not a proxy upgrade.** The paper says the patch is "deployed via proxy upgrade".
  The code etches bytecode, and at different addresses in the two checks: the attack check etches
  `proxy_address` when present (`attack_replay.py:260`), the normal check etches the vulnerable
  address (`validate_patch.py:1577`). Storage layout, immutables and upgrade authorization are
  never exercised.
- **The agent can see the test.** The agent-facing `validate_patch` tool replays 3 normal calls by
  default (`src/web3mcp/server.py:368`) and prints their from/to/input and verdicts; scoring
  replays all of them (up to 5). Raising the limit shows every scoring call. Scores are
  best-of-history (`src/eval/runner.py:909-940`), and that path skips the no-op guard at
  `runner.py:896-907`.
- **The prompt promises partial credit the scorer never gives.** `src/prompts/patch.py:71` vs
  `src/eval/tasks/patch/score.py:63-75`. Open PR #3 fixes the wording.
- **Compiler version.** The explorer's verified `CompilerVersion` is fetched
  (`src/infra/chain/metadata.py:838`) but `validate_patch.py:1373-1382` copies only optimizer and
  EVM settings from it; the version comes from verification or source metadata, where flat
  bundles infer it from the pragma (`metadata.py:175`), or from the patch's pragma. Issue #8
  reports one no-model unchanged-source run scoring 1.0; we have not reproduced it.
- **Exploit side.** If the observed profit cannot be priced or the case has no reference profit,
  `src/eval/tasks/exploit/score.py:66-67` returns full credit, 1.0.

These pull in both directions. Byte equality can fail correct fixes; out-of-gas rows can pass
broken ones, any-change blocking lets non-fixes through the first gate, and a visible test makes
overfitting possible. Neither the paper nor the release reports a calibration against reference
fixes or no-op patches, so the error bar on 23.4 as a measure of patching skill is unknown, not
merely wide.

## What the numbers can and cannot say

| Question | Answer from the release |
| --- | --- |
| Do the published patch cells add up? | Yes. |
| Is patching scored lower than detection and exploitation? | In 9 of 10 configurations; GPT-5.2 is the exception (patch 24.5, detect 17.7, exploit 17.5). For GPT-5.5, patch is 22/94, Wilson 95% CI [16.0, 32.9], and below exploit at p ≈ 0.0003 (unpaired; the exploit score is given the maximum variance a [0,1] score can have, so the test is conservative). |
| Is exploitation harder than detection? | Not shown. 6.2pp, z = 1.52, p = 0.13 by the same method, and only 7 of 10 configurations; the two use different metrics on different sets. |
| How much harder is patching? | Not answerable: the three abstract numbers are three different estimands on three case sets. |
| Is the gap explained by the patch set being harder? | No. Matching difficulty mix moves the gap by 0.17pp for GPT-5.5, 0.01-0.70pp across all ten. |
| Does 23.4% measure the ability to write a correct fix? | Unknown until the oracle is calibrated. |

## Our own errors, corrected

Version 1 of this audit (2026-10-07) got things wrong. A second review in October 2026 (six
review lenses run by AI reviewers, every finding checked by two independent refuters, and every
code line we now cite re-read by hand) found them. In short: we wrote that the headline numbers
"are real" though we had checked arithmetic only; we called a one-model refutation "two
independent frontier models"; we said our work ran on local forks, and no fork was ever run; we
said composition explained "~2pp" (it is 0.17pp); we summed the patch set to 92 cases; we
misnumbered the paper's tables; our red-first test only ran in our own directory layout; we
quoted the exploit cost per case as the patch cost; and we did not credit shane-moore, who had
been in this code first. Details: [CHANGELOG.md](CHANGELOG.md).

The refutation that shaped v1 stands, recorded accurately: Gemini 3.1 Pro, asked "where am I
wrong", showed that block rate is degenerate because a bare `revert()` passes it, so our claim
that patching is "not really harder" fell. GLM-5.3 then adjudicated our narrower position after
seeing that rebuttal. Codex failed with HTTP 400 and Grok timed out. Prompts and responses:
[panel/](panel/).

## Credit

shane-moore opened [issue #8](https://github.com/defai-labs/CyberChainBench/issues/8) and PRs
#1-#7 on the upstream on 2026-10-02: replay accounting, null proxy normalization, prompt/score
alignment, native decompiler endpoint, rooted source paths, verified source identities, and
log-buffer copies. We verified in code the points we cite above; we have not reproduced their
measurements.

## The next measurement

The cheapest experiment needs no model: run the patch oracle on the 94 cases with fixed inputs.
A bare `revert()`, the unchanged verified source and an emit-only patch on all 94 give a first
estimate of how often the oracle passes patches that fix nothing; a hand-written reference fix on
a stratified 12 cases is a pilot for how often it fails correct ones. It needs the upstream harness
(Docker, Foundry), an archive RPC at each case's fork block and block-explorer API access. Only after that is a paid model run worth
it: Table 5 puts patch at $0.06-$21.86 per case, about $217 for Codex × GPT-5.5 on 94 cases.

## Files

| Path | What |
| --- | --- |
| `verify_cyberchainbench.py` | the audit, 15 checks |
| `_test_red_first.py` | corrupts data four ways, asserts each green check turns red |
| `extract_tables.py` | parses every table of the arXiv HTML into `data/paper-table-N.csv` |
| `data/` | parsed Tables 1-6, flattened text, SHA-256 of the arXiv HTML we read |
| `panel/` | the two adversarial prompts and both model responses from 2026-10-07 |
| `FINDINGS.md` | every finding of the second review, with both refuters' verdicts |
| `docs/` | the article, English and Russian |

The arXiv HTML itself is not redistributed; `make tables` fetches it and checks the hash.

## Scope

Defensive measurement only. Nothing was run against any chain, live or forked. Only historical,
publicly disclosed incidents of the DeFiHackLabs corpus are involved; no new vulnerability was sought.

## Licence

MIT for this audit code. The benchmark data is AGPL-3.0 via DeFiHackLabs and is not
redistributed here.
