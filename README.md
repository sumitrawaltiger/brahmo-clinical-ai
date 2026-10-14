# BRAHMO clinical AI — assessment build

[![reproduce](https://github.com/sumitrawaltiger/brahmo-clinical-ai/actions/workflows/reproduce.yml/badge.svg)](https://github.com/sumitrawaltiger/brahmo-clinical-ai/actions/workflows/reproduce.yml)

India drug master + deterministic medication-safety rail (Module A), grounded STW question answering (Module B),
and one end-to-end trace (Module C). Built for the BRAHMO Senior Engineering Assessment.

Start with [`SUBMISSION.md`](SUBMISSION.md) for the map of deliverables. Design reasoning is in [`DESIGN.md`](DESIGN.md).

## Fresh-machine reproduction (target < 1 hour; measured ≈ 16 seconds on a laptop, including venv creation)

Requirements: Python 3.9+ (3.9 is what ships on macOS; 3.10–3.12 also fine), `git`, `make`. One small PyPI
dependency (`pypdf`) plus `pytest`. No Docker, no database server, no API key, no model download.

```bash
git clone <this repo> brahmo-clinical-ai && cd brahmo-clinical-ai
make reproduce
```

`make reproduce` does, in order:

| step | command | what it produces |
|---|---|---|
| venv | `python3 -m venv .venv && pip install -e ".[dev]"` | isolated environment |
| setup | `brahmo setup` | `build/brahmo.sqlite` via numbered migrations (`migrations/00*.sql`), every dataset loaded with a `load_batch` (sha256 + declared version), review queue populated, `build/rag_index.json` built |
| test | `pytest` | 67 tests: provenance, zero-silent-resolution, event-sourced status, rail contract, Module B, trace |
| rail | `brahmo rail --seed --as-of 2026-10-14` | `outputs/rail/RX01..RX10.json`, `outputs/seed_prescriptions_completed.csv`, `outputs/seed_rail_summary.md` |
| eval | `brahmo eval`, `brahmo eval --set paraphrase`, `brahmo resolver-eval` | `outputs/eval/mini_eval_results.*` (11 sample questions), `outputs/eval/paraphrase_eval_results.*` (35 paraphrased/near-miss questions), `outputs/eval/resolver_eval_results.*` (45 messy spellings) |
| trace | `brahmo trace ...` | `outputs/trace_sample.json` |
| freshness-demo | `brahmo freshness-demo` | `outputs/freshness_demo.{json,md}` — a new gazette notification arrives (throw-away DB) |

Without `make`: run the commands in the table from the repo root after activating the venv.

## CLI

```bash
brahmo setup                                  # migrate + ingest + index (idempotent; reruns skip unchanged files)
brahmo versions                               # data versions actually loaded (batch id, sha256, declared version)
brahmo review [--list --reason CODE]          # review queue summary / items
brahmo resolve "Telma" [--strength "40 mg"]   # see exactly why a brand does or does not resolve
brahmo status "NimuPar-P" --as-of 2020-01-01  # event-sourced regulatory status with the supersession chain
brahmo rail --rx my_rx.json --as-of 2026-10-14
brahmo ask "Which analgesic class must be avoided in suspected dengue, and why?"
brahmo ask "Is NimuPar-P banned?"             # structured facts route to Module A, never to retrieval
brahmo eval                                   # mini-eval over the 11 sample questions
brahmo eval --set paraphrase                  # 35 paraphrased / near-miss / absent-topic questions
brahmo resolver-eval                          # 45 messy prescription spellings
brahmo freshness-demo                         # stretch: a new gazette notification arrives
brahmo trace --rx data/trace_sample_rx.json --question "..." --out outputs/trace_sample.json
```

Prescription JSON shape: see `data/trace_sample_rx.json`. `patient_population` is optional ("adult"/"child");
when absent, cited ceilings are reported as not confirmed for the patient.

## Configuration

Everything tunable is in `config/settings.json` (paths, thresholds, freshness windows, retrieval weights,
answering mode) and the files it points at (`rules.json`, `reference_ceilings.json`, `frequency_patterns.json`,
`condition_synonyms.json`, `corpus_metadata.json`). Any key can be overridden with `BRAHMO_<SECTION>__<KEY>`,
e.g. `BRAHMO_ANSWERING__MODE=llm` or `BRAHMO_DATA__SUPPLEMENTS_ENABLED=false` (run on the provided files only).

### Answering modes
* `extractive` (default): decision units are returned verbatim with claim-level citations. No generation, no network.
* `llm`: Claude composes a short synthesis from the retrieved units; every claim is re-verified (citation exists,
  every number appears in the cited text) before it is shown. Needs `pip install -e ".[llm]"` and
  `ANTHROPIC_API_KEY`. If the call fails the answer falls back to extractive units and says so in `notes`.

## Repository layout

```
config/            all settings and rule/threshold files (no constants in code)
migrations/        001..006 numbered SQL migrations
data/              the provided data pack, exactly as given + data/supplements (candidate-added, provenance per row) + data/eval
corpus/            the 13 STW PDFs + the clinic protocol
src/brahmo/        ingest/ normalize/ regulatory/ rail/ rag/ trace/ (see package docstrings)
tests/             pytest suite
prompts/           prompt library actually used (agent session + runtime prompts)
outputs/           checked-in results: rail outputs, mini-eval, trace sample
docs/kit/          the brief and architecture document as received (for traceability)
```

## Documents
`SUBMISSION.md` · `DESIGN.md` · `GAPS_REGISTER.md` · `SCALE.md` · `QA_DAY2.md` · `PART2_PLAN.md` · `CLAUDE.md` · `prompts/README.md`
