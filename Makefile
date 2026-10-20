# Reproduce the audit from a clean checkout. No API keys, no RPC, no spend.
#
#   make           -> clone the upstream release, pin it to 1cb7410, run the audit
#   make red       -> prove the green checks go red on corrupted data
#   make tables    -> re-fetch the arXiv HTML, check its hash, re-extract the tables into data/
#   make clean     -> remove the upstream clone only (never touches data/ or panel/)

UPSTREAM := https://github.com/defai-labs/CyberChainBench.git
COMMIT   := 1cb7410
PAPER    := https://arxiv.org/html/2606.26216v1

.PHONY: all audit red tables clean

all: audit

CyberChainBench:
	git clone $(UPSTREAM) CyberChainBench
	git -C CyberChainBench checkout --quiet $(COMMIT)

audit: CyberChainBench
	python3 verify_cyberchainbench.py --upstream CyberChainBench

red: CyberChainBench
	python3 _test_red_first.py --upstream CyberChainBench

tables:
	curl -sL -o /tmp/paper-arxiv-2606.26216v1.html $(PAPER)
	shasum -a 256 -c data/paper.sha256 --ignore-missing || echo "WARNING: arXiv HTML changed since this audit"
	python3 extract_tables.py /tmp/paper-arxiv-2606.26216v1.html data/

clean:
	rm -rf CyberChainBench
