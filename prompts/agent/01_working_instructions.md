# Standing working instructions the agent followed

These were the rules in force for every file written. They are the brief's binding laws turned into
engineering instructions, and are now also in `CLAUDE.md` for future sessions.

1. Read the entire kit (index → brief → architecture edition → every data file → every PDF) before designing.
   Profile each dataset for anomalies first; design from what the data actually contains.
2. Python 3.9-compatible, standard library + SQLite; one small PyPI dependency allowed for PDF text. A fresh
   machine must reproduce everything in well under an hour with no API key, no Docker, no model download.
3. Every data row must point at a `load_batch` recording file sha256, declared source version and load time.
   Every check result and every answer must carry the rule/data/index/prompt/config versions used.
4. Resolution of brand → product is deterministic: exact normalized brand, then strength filter, then form filter,
   then composition grouping. Exactly one surviving composition = RESOLVED. Otherwise AMBIGUOUS/UNRESOLVED with
   a reason code and candidates in the review queue. Fuzzy matching may only produce suggestions.
5. Regulatory status is derived from events (effective date ≤ as-of, not superseded by an effective event). No
   boolean columns. Stays are a visible state. Conflicts are a visible state.
6. The rail returns exactly one of the eight statuses per check, with severity only on HIT, evidence, rule version,
   data versions. Precedence when aggregating: SERVICE_UNAVAILABLE > DATA_EXPIRED > SOURCE_CONFLICT > HIT >
   UNVERIFIED_INPUT > PARTIAL_COVERAGE > NOT_CHECKED > CHECKED_NO_HIT. Missing data never becomes CHECKED_NO_HIT.
7. No LLM import anywhere under `rail/` or `regulatory/`. Write a test that asserts it.
8. Module B chunks are decision units (one bullet under one section heading) with full metadata; retrieval is
   BM25 + embedding fused by RRF with metadata filters; answers are verbatim units with claim-level citations by
   default; an optional LLM composer must pass a numeric/citation guard. Structured facts route to Module A.
9. Dose text is quoted, never computed. Local protocol is labelled as the clinic's. Superseded editions are shown
   separately, never merged. Conditions outside the corpus abstain before retrieval, naming what is missing.
10. All thresholds, paths, severities and patterns in `config/`. Record every decision with a rejected alternative
    in DESIGN.md; record every data anomaly in GAPS_REGISTER.md; keep outputs regenerated from the code.
