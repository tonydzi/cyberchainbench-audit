# cyberchainbench-audit

An independent audit of the headline numbers in **CyberChainBench**
([arXiv:2606.26216](https://arxiv.org/abs/2606.26216), Huang, Jiang, Poovendran, Lin, 24 Jun 2026),
checked against the benchmark's own public release at
[defai-labs/CyberChainBench](https://github.com/defai-labs/CyberChainBench).

The paper headlines a *difficulty gradient*:

> Results reveal a clear difficulty gradient: the best configuration scores 37.5% on detection,
> **43.7% on exploitation, but only 23.4% on patching**.

We set out to test whether those two numbers hold. **They do.** This repository
reproduces them, and then documents what the numbers do and do not support.

```bash
git clone --depth 1 https://github.com/defai-labs/CyberChainBench.git
python3 verify_cyberchainbench.py --cases CyberChainBench/data/benchmark/cases
python3 _test_red_first.py     # proves the green checks can actually go red
```

No model is run, no RPC is called, nothing is spent. Every number is either transcribed
from the paper or derived from the 541 published case files.

## What reproduces

| Claim in the paper | Our result |
| --- | --- |
| 541 incidents, 9 EVM chains | 541 case files ✅ |
| patch subset = 94 cases | the code's filter reproduces **exactly 94** (easy 31 / med 43 / hard 18) ✅ |
| pre-filter stage = 153 cases | `fixable is True` yields **exactly 153** ✅ (but see *mislabelled filter* below) |
| temporal split 86 post-cutoff / 455 pre | **86 / 455** ✅ |
| best patch score 23.4% (Codex × GPT-5.5) | recomputing Table 3's own strata over the reconstructed 94-case composition gives **23.44** ✅ |
| exploit 43.7% (Codex × GPT-5.5) | **not reproducible from the release** — see below |

Nine of ten configurations' `Patch All` cells recompute from their own Easy/Med/Hard
cells to within 0.15pp. The arithmetic and the data construction are sound.

**So: the headline numbers are real.** Anyone citing 43.7 / 23.4 is citing them correctly.

## What does not hold up

### 1. The two headline numbers are different estimands

They are printed side by side as if commensurable, and the paper reads a capability
ratio off them ("producing a correct fix is far harder than identifying or reproducing
a vulnerability"). But:

- **exploit** = mean of `min(observed_profit / reference_profit, 1.0)` — a *clamped
  continuous* score with best-of-N retries inside a 30-minute budget, over **200** cases.
- **patch** = mean of `1[exploit blocked] · 1[normal txs pass]` — a *binary conjunction
  of two predicates*, over a different **94** cases.

A mean of a continuous partial-credit score and a mean of a 0/1 conjunction are not the
same quantity. An agent recovering 30% of the reference profit books 0.30 on the exploit
task; an agent producing a patch that blocks the attack but breaks one legitimate caller
books 0.00. You cannot divide one by the other and call the quotient a difficulty ratio.

The paper's own decomposition shows where the patch score actually goes:
**47.9% of GPT-5.5's patches block the exploit, but only 23.4% also preserve normal
operation** — i.e. 51% of exploit-blocking patches break legitimate callers. For Gemini
3.1 Pro it is starker: blocks 98.9%, passes 1.1%.

> **An earlier version of this audit went further** and argued that, compared on the
> single predicate "did the agent neutralise the vulnerability" (the block rate),
> patching is *not* harder than exploiting — and that the paper therefore measured a
> regression property rather than a security one. We ran that claim past two independent
> frontier models as adversarial reviewers and **it did not survive**: block rate is a
> degenerate metric with a zero-cost trivial solution (a patch that simply reverts at the
> function entry scores ~100% on it and requires no security reasoning at all — which is
> exactly what Gemini's 98.9%/1.1% split is). The conjunction is the *minimum viable*
> definition of a patch. We record the refutation rather than quietly dropping it.
> The narrower point above — that the two headline numbers are different estimands —
> is what survived review.

### 2. The "best patch pass rate" sentence contradicts Table 3

The body asserts "the best patch pass rate (23.4%)". But Table 3 prints **24.5%** for
Codex × GPT-5.2, and that cell is self-consistent with its own strata (25.8 / 30.2 / 11.1
over the 94-case composition recomputes to 24.45). So 23.4% is not the best patch score
in the paper's own table.

This matters for the headline framing, because Codex × GPT-5.2 scores **17.5% on exploit
and 24.5% on patch** — for that configuration the "clear difficulty gradient" *inverts*.
One of ten configurations runs the other way.

### 3. One Table 5 cell is wrong

`Table 3 Patch All` and `Table 5 Pass %` are the same quantity, and they agree exactly for
nine of ten configurations. For Codex × GPT-5.2 they disagree: 24.5 vs 17.5. Since Table 3's
value is the one consistent with its own strata, the Table 5 cell looks like the
transcription error — and note that 17.5 is precisely that row's *exploit* score.

### 4. The patch contamination slice rests on 9 cases

The paper reports that post-cutoff cases cost "2–6 points" on exploit and patch, versus
12–16 points on detection, and reads this as evidence that exploitation and patching rely
on reasoning rather than memorised write-ups. That is the paper's main contamination control.

Only **9 of the 94** patch cases post-date the evaluated models' cutoffs. On 9 binary
trials one case moves the score by 11.1pp, and a 95% Wilson interval around ~23% spans
roughly **[6%, 55%]** — about 48pp wide. A 2–6 point difference is not distinguishable
from noise at that sample size. The contamination control for the patch task is
underpowered by construction, not by accident: the filter chain that produces a
patchable case (verified source + recoverable legitimate transactions) selects against
recent incidents, leaving the post-cutoff patch slice at 9.6% of the subset versus 15.9%
of the corpus.

### 5. The mislabelled filter

The paper describes the patch subset as starting from "153 proxy cases". The code
(`src/scripts/1_benchmark/benchmark.py`) filters on `fixable is True` and never consults
`proxy_address`. The count 153 is right; the label is not. Requiring an actual
`proxy_address` yields 87 cases, not 94 — so the described filter and the implemented
filter produce different subsets.

### 6. The exploit headline is not reproducible from the release

`src/scripts/2_eval/eval.py` selects the exploit task from a directory named
`exploit_subset200`. That directory is a generated Harbor artifact under
`data/benchmark/harbor_tasks/`, **which the release does not ship**, and no code in the
release constructs it. Which 200 of the 541 cases make up the exploit set is therefore
unspecified. The patch number can be audited from the public release; the exploit number
cannot.

## Verdict

| | |
| --- | --- |
| Are 43.7 / 23.4 correct as published? | **Yes.** Confirmed, and the patch figure recomputes to 23.44 from their own strata. |
| Is patching the hardest of the three tasks? | **Yes, and this survived adversarial review.** We tried to overturn it and failed. |
| Is "43.7 vs 23.4" a measure of how much harder? | **No.** Different estimands, different subsets, different credit models. |
| Does the subset difference explain the gap? | **No — we tested our own hypothesis and it failed.** Difficulty-matching the two subsets moves the gap from 19.0pp to 19.1pp, about 2pp of a ~20pp gap. |
| Is the contamination analysis sound for patching? | **No.** n=9. |

## What we have not done

This audit is confined to what the public release permits for free. We have **not** run
any model against the benchmark. Doing so costs (by the paper's own Table 5) roughly
$2.39–$21.86 per case, i.e. about $220–$2,000 per configuration for the 94-case patch
set, plus archive RPC access and Docker. Until that is run, we have **no independent
measurement of any model's exploit or patch rate** — only an audit of theirs.

The measurement we would run, informed by the review above:

1. Both tasks on the **same 94 contracts**, so composition is fixed by construction.
2. A **strictness-matched** exploit score — one effectiveness predicate plus one
   legitimacy predicate on each side — rather than a clamped ratio on one side and a
   conjunction on the other. Report the exploit score as a *distribution* of `R` (median
   and quartiles) alongside any binarisation, since thresholding `R ≥ 0.9` imports an
   arbitrary cliff that can move "success" by 20+ points.
3. A **trivial-baseline calibration**: run a one-line `revert()` patch over all 94 cases
   and publish its block/pass rates, so the degenerate floor of the block metric is visible
   in the table rather than inferred.
4. A **powered contamination slice**, which requires extending the patch subset with
   post-cutoff incidents rather than accepting n=9.

## Method notes

Numbers from the paper were parsed structurally out of the arXiv HTML tables, not read
off the flattened text — the flattened column order is misleading and will silently
mis-attribute cells. `_test_red_first.py` corrupts the dataset three ways (delete a case,
flip a `fixable` flag, re-date an incident across the cutoff) and asserts the
corresponding checks go red, so the green results are load-bearing rather than vacuous.

Adversarial review of our own negative claim was run against two independent vendors
(Gemini 3.1 Pro; GLM-5.3) with the prompt "where am I wrong", not "am I right". The
stronger version of our claim was refuted and is retained above as a refutation.

## Scope

Defensive measurement only, on publicly disclosed and long-since-patched incidents, all of
it on local forks of historical state. No transaction was ever submitted to any live
network, no wallet was involved, and no new vulnerability in any live contract was sought
or disclosed. The underlying incidents are the public DeFiHackLabs corpus.

## Licence

MIT for this audit code. The benchmark data it reads is AGPL-3.0 via DeFiHackLabs and is
not redistributed here — the script reads a local clone of the upstream repository.
