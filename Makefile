# Fresh-machine reproduction (G1). Requires: Python 3.9+, git. No network needed after `make venv`.
PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: all venv setup test rail eval trace freshness-demo outputs clean reproduce

all: reproduce

venv:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -e ".[dev]"

setup: ## migrate + load every dataset + build the Module B index
	$(BIN)/python -m brahmo setup

test:
	$(BIN)/python -m pytest -q

rail: ## seeded rail demonstration -> outputs/rail/*.json, outputs/seed_prescriptions_completed.csv, outputs/seed_rail_summary.md
	$(BIN)/python -m brahmo rail --seed --as-of 2026-10-14

eval: ## Module B mini-eval + paraphrase robustness set + resolver eval -> outputs/eval/
	$(BIN)/python -m brahmo eval --as-of 2026-10-14
	$(BIN)/python -m brahmo eval --as-of 2026-10-14 --set paraphrase
	$(BIN)/python -m brahmo resolver-eval

freshness-demo: ## stretch: a new gazette notification arrives (throw-away DB) -> outputs/freshness_demo.*
	$(BIN)/python -m brahmo freshness-demo --as-of 2026-10-14

trace: ## Module C sample trace -> outputs/trace_sample.json
	$(BIN)/python -m brahmo trace --rx data/trace_sample_rx.json --question "Which analgesic class must be avoided in suspected dengue, and why?" --as-of 2026-10-14 --out outputs/trace_sample.json > /dev/null
	@echo "wrote outputs/trace_sample.json"

outputs: rail eval trace freshness-demo

reproduce: venv setup test outputs ## everything, from a clean clone
	@echo "Reproduction complete. See outputs/ and SUBMISSION.md"

clean:
	rm -rf build .pytest_cache
