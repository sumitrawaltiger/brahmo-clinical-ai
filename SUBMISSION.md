# SUBMISSION.md — BRAHMO Senior Engineering Assessment · Sumit Rawal

Repository: private, fresh, full commit history preserved. Read access granted to the BRAHMO reviewing account
(see `QA_DAY2.md` Q12 for the account to confirm).

- [x] **How to run:** [`README.md`](README.md) — `make reproduce` from a clean clone: venv, migrations, data loads,
      index, 67 tests, seeded rail outputs, mini-eval, trace. Measured ≈ 16 seconds; no API key, no Docker, no downloads
      beyond `pypdf` and `pytest`.
- [x] **DESIGN.md:** [`DESIGN.md`](DESIGN.md) — opens with the system restatement and the three riskiest assumptions;
      30 decisions, each with why, rejected alternative(s) and implication; a section on what the coding agent got
      wrong and how it was caught, and the six behavioural fixes from the code review.
- [x] **SCALE.md:** [`SCALE.md`](SCALE.md) — where this strains at 100× and 100 concurrent users, in failure order.
- [x] **Gaps register:** [`GAPS_REGISTER.md`](GAPS_REGISTER.md) — 12 scope cuts/limitations, 21 data anomalies with
      what the system does about each.
- [x] **Prompt library + conventions file:** [`prompts/README.md`](prompts/README.md), `prompts/agent/*` (the prompts
      actually used, in order), `prompts/runtime/grounded_answer_v1.md` (the one runtime prompt), [`CLAUDE.md`](CLAUDE.md).
- [x] **Mini-eval results:** [`outputs/eval/mini_eval_results.md`](outputs/eval/mini_eval_results.md) (+ `.json`,
      `answers_full.json`) — 11 questions: 11 correct (9 answered, 2 correctly abstained), 0 wrong, 0 uncited numbers.
      Robustness sets: [`paraphrase_eval_results.md`](outputs/eval/paraphrase_eval_results.md) (35 paraphrased / near-miss /
      absent-topic questions: 35 correct, 0 wrong) and [`resolver_eval_results.md`](outputs/eval/resolver_eval_results.md)
      (45 messy prescription spellings: 45 correct, 0 wrong).
- [x] **Seeded-prescription rail outputs:** [`outputs/seed_rail_summary.md`](outputs/seed_rail_summary.md),
      [`outputs/seed_prescriptions_completed.csv`](outputs/seed_prescriptions_completed.csv) (template columns filled),
      `outputs/rail/RX01..RX10.json` (full evidence, versions). RX01 and RX09 are the FDC-plus-cumulative cases.
- [x] **End-to-end trace:** [`outputs/trace_sample.json`](outputs/trace_sample.json) — 5-item prescription (one
      ambiguous) + one question; normalization, four checks, grounded answer, every version used.
- [x] **Stretch:** colloquial spelling handling (D-031, measured) and a runnable freshness mechanism
      ([`outputs/freshness_demo.md`](outputs/freshness_demo.md), D-033). Not built: doctor-facing rendering, multi-tenant sketch (gaps A5).
- [x] **Part 2 plan:** [`PART2_PLAN.md`](PART2_PLAN.md) — 5-week plan to the 100-doctor test.
- [x] **Day-2 Q&A:** [`QA_DAY2.md`](QA_DAY2.md) — 12 questions.
- [x] **Anything unfinished + prioritisation reasoning:** `GAPS_REGISTER.md` §A. In priority order of what I would do
      next: (1) exercise the guarded LLM composition mode and the LLM mapping-suggestion hook with a key;
      (2) alias learning from review decisions; (3) `current_batch` pointer and a second CDCI version to prove
      replay across versions; (4) layout-aware chunking spike on a real ICMR STW PDF. Core gates were finished
      first because stretch work earns nothing if they fail.
- [ ] Repo access granted to the BRAHMO reviewing team account — pending the account name (Q12).

## Gate self-check

| gate | evidence |
|---|---|
| G1 fresh-machine < 1 h | `make reproduce`; README table |
| G2 decomposition ≥ 95 % | 160 FDCs decomposed from structured columns, cross-checked against `strength_text` (0 disagreements); confidence + method on every row (`product_ingredient`) |
| G3 zero silent resolutions | `tests/test_resolver.py`; 730/783 stock rows and 3/18 seed lines queued with reason codes; fuzzy never resolves |
| G4 rail demonstration | `outputs/seed_rail_summary.md`: RX01/02/03/07/09 HIT; RX04/08/10 UNVERIFIED_INPUT on every line (an unresolved sibling means the line was not fully screened); RX05/06 clean on DUP/FDC/CUM with INT coverage declared; `tests/test_rail.py` |
| G5 100 % provenance | `tests/test_ingest_provenance.py`; every output carries `data_versions` |
| G6 no uncited clinical number | extractive claims are verbatim; `uncited_numbers_total = 0` in the eval; guard enforced in LLM mode |
| G7 decisions with why + rejected alternative | `DESIGN.md` D-001…D-034 |
