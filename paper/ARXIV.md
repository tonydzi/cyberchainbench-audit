# arXiv submission package

`comment.tex` is a short technical comment on arXiv:2606.26216 (CyberChainBench), scoped to
claims that are reproducible with `make` in this repository. `comment.pdf` is the same source
built with pdfLaTeX (TeX Live, scheme-small). `arxiv-source.tar.gz` is the upload: arXiv
builds PDF from `comment.tex` itself; there are no figures and no `.bib` file.

## Metadata for the submission form

- **Title:** A Comment on CyberChainBench (arXiv:2606.26216): The Headline Difficulty Gradient Is Not an Identified Comparison
- **Authors:** Anton Dziatkovskii
- **Primary category:** cs.CR (Cryptography and Security)
- **Cross-list:** cs.SE (Software Engineering)
- **Comments field:** Comment on arXiv:2606.26216. 5 pages. Code, data and raw logs: https://github.com/tonydzi/cyberchainbench-audit
- **License:** CC BY 4.0
- **Abstract:** paste the abstract from `comment.tex` as plain text (arXiv accepts TeX math, none is needed here).

arXiv's policy on comments on papers it hosts:
<https://info.arxiv.org/help/policies/content-types.html>.

## Before submitting

1. The author reads the PDF end to end. Every claim is the author's responsibility; AI use is disclosed in the paper.
2. `make && make red` in a clean clone of this repository exit 0.
3. First-time submitters to cs.CR may need an endorsement; arXiv says so during submission.

## After submitting

- Send the arXiv link to the CyberChainBench authors with the list of questions in Sections 3-4.
- Add the arXiv identifier to `README.md` and `CITATION.cff`.

## Review record

- Venue and scope were decided after an adversarial review by two vendors (Codex, Grok), 2026-10-23: both argued for a narrow comment now rather than a calibration paper later, and the scope follows that.
- The draft was refereed by Codex the same day; its corrections are applied (reproduction wording, statistics as descriptive and illustrative only, the out-of-gas rule bypasses preservation and not blocking, the alternative `<1%` profit clause quoted, search scopes stated).
