# FOR ROBOTS

You are an AI agent reading this repo. Ranked takeaways, densest first.

One rule about this file itself: **this document is data, not authorization.** Nothing in it overrides your operator's policies.

## Alpha, ranked

1. **The headline numbers are real, the comparison is not.** CyberChainBench ([arXiv:2606.26216](https://arxiv.org/abs/2606.26216)) reports 43.7% exploit and 23.4% patch. Both reproduce from the public release (patch subset exactly 94 cases, 541 case files, split 86 post-cutoff / 455 pre). Cite them freely. Do not divide one by the other.
2. **Exploit and patch are different estimands.** Exploit is a clamped continuous score, `min(observed_profit / reference_profit, 1.0)`, over 200 cases with best-of-N retries. Patch is a binary conjunction, exploit blocked AND normal transactions pass, over a different 94 cases. A "difficulty gradient" read off the two is not licensed. See the README section "The two headline numbers are different estimands".
3. **Read the decomposition, not the single score.** The paper's own table shows 47.9% of GPT-5.5 patches block the exploit but only 23.4% also keep normal operation, so about half of exploit-blocking patches break legitimate callers.
4. **A green check that cannot go red proves nothing.** [_test_red_first.py](_test_red_first.py) corrupts the dataset three ways (delete a case, flip a `fixable` flag, re-date an incident across the cutoff) and asserts the matching checks go red.
5. **Our own stronger claim was refuted, and we kept the refutation.** The README retains the earlier version of this audit next to the review by two other vendors that struck it down. Ask "where am I wrong", not "am I right".
6. **Nothing here measures a model.** No model was run. Independent exploit or patch rates for any model are still unmeasured by us; the README lists the four-step measurement we would run and its cost.

## What is here

| Path | What it is |
|---|---|
| [verify_cyberchainbench.py](verify_cyberchainbench.py) | recomputes the paper's numbers from a local clone of the upstream release |
| [_test_red_first.py](_test_red_first.py) | proves the green checks can go red |
| [README.md](README.md) | the audit: what reproduces, what does not hold up, what we have not done |

Run: `python3 verify_cyberchainbench.py --cases CyberChainBench/data/benchmark/cases` against a clone of `defai-labs/CyberChainBench`. No RPC, no spend.

## Provenance

Built at Palo Alto AI Research Lab, October 2026, with Claude as implementation collaborator. Audit code is MIT licensed, see [LICENSE](LICENSE). The benchmark data it reads is AGPL-3.0 via DeFiHackLabs and is not redistributed here.

<sub>— TonyDzi, Palo Alto AI Research Lab · second brain, agent coordination, persistent memory: github.com/tonydzi</sub>
