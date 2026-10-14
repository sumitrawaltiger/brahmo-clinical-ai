# DESIGN.md — Sumit Rawal

## 0. The system in my own words (one paragraph)

BRAHMO is a doctor-facing assistant for Indian outpatient practice whose value is not the language model but the
India-specific layer around it: a drug master that turns the brand names doctors actually write (Dolo, Sinarest,
Telma-H) into salts and strengths; a deterministic rail that checks a draft prescription at the salt level
(duplicates, prohibited or restricted products per gazette events, severe interactions, cumulative exposure) and
reports exactly how far each check could run; and a grounded Q&A slice that answers narrative clinical questions
only from retrieved, versioned Indian sources with claim-level citations, abstaining when the corpus cannot support
an answer. My Part 1 build proves the three load-bearing behaviours on the provided data: nothing ambiguous is
resolved silently (every uncertain brand, target or seed term lands in a review queue with a reason code);
regulatory status is derived from effective-dated events with supersession rather than stored as a flag; and
"missing" is a first-class, visible state everywhere — in the eight-state rail contract, in retrieval abstention,
and in a trace that records every data, rule, index, prompt and config version used so any output can be replayed.

## 0.1 The three riskiest assumptions I see in the provided materials

1. **That a brand name is a usable identity key.** In the CDCI subset, 563 of the ~1,430 distinct brand names map
   to more than one composition (e.g. `Kovas 2` → seven unrelated products across tablet/syrup/capsule), and the
   seed prescriptions and stock file routinely omit strength and form. The SKU key is brand + strength + form; the
   scribe contract upstream must capture strength and form, otherwise the review queue — not the rail — becomes the
   product. My resolver makes this visible (245 of 783 stock rows are `AMBIGUOUS_STRENGTH_MISSING`) instead of
   hiding it behind a "best match".
2. **That regulatory truth can be reconstructed from gazette text alone.** Targets arrive as free text with
   qualifiers that are not machine-resolvable ("specific ratio", "paediatric suspensions only", "Codeine-based cough
   FDCs") and name ingredients the master does not know (Caffeine, Codeine, Ornidazole). Event sourcing is the right
   model, but the *target interpretation* step is a human-curated artefact with its own version and sign-off; the
   materials treat it as parsing. I store the interpretation separately with a confidence and route low-confidence
   ones to review.
3. **That the provided corpus shape generalises.** The STW one-pagers here are clean bullet lists; real ICMR STW
   PDFs are graphical flowcharts with arrows, tables and multi-column layouts, and most Indian specialty guidelines
   are long narrative PDFs. The decision-unit chunker that works perfectly on this pack (83 units, 11/11 questions)
   will need a layout-aware extraction stage and a human unit-review loop before Phase G can scale; Part 2 treats
   this as the critical path, not as an ingestion detail.

A fourth, smaller one: the brief scores a correct refusal as 0, which is right for the held-out set but, if carried
into the product metric, rewards a system that abstains whenever coverage is thin. I kept honest coverage states
(see D-010) and put the tension in the Part 2 quality system rather than tuning it away here.

## Decisions

### D-001 — Stack: Python 3.9 + SQLite + standard library, one PyPI runtime dependency
- **Decision:** Python ≥3.9 syntax, SQLite with numbered SQL migrations, `pypdf` for PDF text; `pytest` for tests.
  No Docker, no DB server, no API key, no model download on the critical path.
- **Why:** G1 (fresh machine < 1 hour) is binary; the measured reproduction is ≈2 minutes. SQLite gives real SQL,
  foreign keys and a single replayable file. Python 3.9 is what ships on the evaluators' likely machines.
- **Rejected:** PostgreSQL + Docker (richer, but reproduction risk and nothing in Part 1 needs it); a Node/TS stack
  (no advantage for a data/rules workload); pandas/numpy (not needed at 2,000 rows and adds install surface).
- **Implication:** `SCALE.md` names SQLite's single-writer model as the first thing to change at 100 concurrent users.

### D-002 — Provenance by `load_batch`; rows are immutable
- **Decision:** Every loader registers a `load_batch` (dataset, declared source version, file sha256, row count,
  loader version, load time) before inserting rows; every row references it; reloading the same file is a no-op;
  a changed file is a new batch. Nothing is updated in place.
- **Why:** Laws 3 and 8. A check result that says `data_versions.cdci = cdci:2026-06-30:8f7cdf39` is replayable
  against exactly that file. Idempotency makes `make reproduce` safe to re-run.
- **Rejected:** A single `source_version` column per row (no file identity, no load time); upserts (destroy history).
- **Implication:** Queries must pick a batch; today the resolver reads all batches (there is one per dataset). A
  `current_batch` pointer per dataset is the Phase P change.

### D-003 — Resolution is a deterministic funnel; fuzzy matching only suggests
- **Decision:** exact normalized brand → strength filter → form filter → group by composition+form. Exactly one
  surviving composition = `RESOLVED` with a method tag and a configured confidence. Otherwise `AMBIGUOUS` or
  `UNRESOLVED` with a reason code and the candidate list queued for review. `difflib` near-misses are returned with
  `note = "fuzzy suggestion only"` and reason `FUZZY_ONLY`; they never resolve.
- **Why:** Law 6 and gate G3. Fuzzy similarity is a search aid; `Kovs-2` → `Kovas 2` is probably a typo, but the
  cost of being wrong is a wrong salt in a safety check.
- **Rejected:** Similarity-threshold auto-accept (a 0.9 ratio still maps `Zqtrixon Forte` to `Zyvin Forte`);
  LLM auto-mapping (implemented as an optional *suggestion* hook, `resolver.llm_assist_enabled=false`, never a
  resolver — see D-024).
- **Implication:** Human review throughput becomes a real dependency (Part 2 §7). The alias table exists so each
  review decision is learned once.

### D-004 — Brand families are an ambiguity, not a near-miss
- **Decision:** `Telma` with no strength returns `AMBIGUOUS_STRENGTH_MISSING` listing Telma 20/40/80/-H 40.
- **Why:** A reviewer (or the scribe UI) can act on "which Telma?" immediately; a fuzzy list looks like a typo.
- **Rejected:** Treating the family as unknown (first version did this and the output was misleading).
- **Implication:** With a strength, the family narrows deterministically (`Telma` + `40 mg` still leaves Telma 40 and
  Telma-H 40 → still ambiguous, correctly).

### D-005 — A unit conflict is a mismatch, never a numeric coincidence
- **Decision:** `Thyronorm 50` written as `50 mcg` against a master row of `Thyroxine 50 mg` is `STRENGTH_MISMATCH`
  with an explicit "possible unit conflict in source" detail; RX10 item 2 is `UNVERIFIED_INPUT`.
- **Why:** mg vs mcg is a thousand-fold difference. The master row is almost certainly wrong (thyroxine is dosed in
  micrograms), but the system must not decide that; it must surface it. Logged in the gaps register and Day-2 Q&A.
- **Rejected:** Matching on the number alone with a warning (that is a silent resolution with a footnote).
- **Implication:** A "clean" seed prescription renders partly unknown. That is the intended behaviour under law 5.

### D-006 — Candidate-added ingredient vocabulary (names only), provenance per row, switchable
- **Decision:** `data/supplements/ingredient_supplement.csv` adds 18 INN names (Caffeine, Codeine, Ornidazole and
  the 15 interaction-seed terms absent from CDCI) and one class→members mapping (Nitrates → ATC C01DA organic
  nitrates). No products are added. Each row records source, version, date added and reason. Loader runs after CDCI
  and before gazette/interactions; `data.supplements_enabled=false` runs on the provided files only.
- **Why:** The e-mail explicitly permits public/synthetic drug-master additions with provenance. Without these
  names, exact-set matching for EV004/EV007/EV010/EV011 could never be evaluated and Sinarest showed
  `PARTIAL_COVERAGE` for a target (EV004) it does not actually match. Names are the least invasive fix.
- **Rejected:** Editing the CDCI file (breaks "exactly as given"); ignoring unmatchable targets (silent); adding
  synthetic products for the missing ingredients (would fabricate SKUs).
- **Implication:** The class mapping `requires_signoff=1`; it is a candidate's reading of a pharmacological class and
  must be clinically signed off before serving. The gaps register lists it.

### D-007 — Regulatory status is derived, never stored
- **Decision:** `derive_status(matching_events, all_events, as_of)`: effective = `effective_date ≤ as_of`;
  superseded = named in `supersedes_event_id` by any effective event (global, not just among matches); in-force =
  effective and not superseded; one in-force action → that status; several disagreeing → `CONFLICT`; none → `NONE`
  with pending (future-effective) events listed. `STAY_GRANTED` yields `STAYED`, which the rail reports as a HIT
  with severity INFO — visible, not enforced.
- **Why:** Law 7. The Nimesulide+Paracetamol chain (prohibited 2018 → stayed 2019 → re-prohibited 2023) is exactly
  the case a boolean destroys: at 2020-01-01 the honest answer is "stayed", at 2026 "prohibited per GSR 411(E)
  effective 2023-06-15", and the output cites both the notification and its effective date.
- **Rejected:** A materialised status table (fine as a cache keyed by batch id + date, wrong as the source of truth);
  treating a stay as "not banned" (hides a live legal dispute from the doctor).
- **Implication:** Every status call walks 12 events; at thousands of events a per-batch materialised view keyed by
  (target, date range) is the obvious cache (`SCALE.md`).

### D-008 — Gazette targets get a structured interpretation with confidence and qualifiers
- **Decision:** `regulatory_target` stores ingredient set, match mode (`exact_set` for FDC/PRODUCT, `ingredient_any`
  for INGREDIENT, `contains_all_fdc_only` for "X-based FDCs"), form/population/ratio qualifiers, parse confidence,
  unresolved terms. A product that exact-matches a target carrying an unresolvable ratio qualifier is reported as
  *uncertain applicability* → `PARTIAL_COVERAGE`, never as a hit or a miss. Form qualifiers exclude explicitly
  (Combiflam tablet vs EV012 paediatric suspensions) and the exclusion is in the evidence.
- **Why:** The text is the law; the interpretation is ours and may be wrong. Separating them with a confidence makes
  the human curation step (and its version) explicit.
- **Rejected:** Keyword matching on the raw description (no qualifiers, no confidence); dropping qualifiers.
- **Implication:** `TARGET_PARSE_UNCERTAIN` review items are the input to a clinical/regulatory curation workflow.

### D-009 — One precedence order for aggregating statuses; missing data never becomes "no hit"
- **Decision:** `SERVICE_UNAVAILABLE > DATA_EXPIRED > SOURCE_CONFLICT > HIT > UNVERIFIED_INPUT > PARTIAL_COVERAGE
  > NOT_CHECKED > CHECKED_NO_HIT`. A check with one unresolved item and no hit is `UNVERIFIED_INPUT`; with a hit
  it is `HIT` and the unresolved items are listed in `unverified_items`. `CheckResult` rejects statuses outside the
  vocabulary and strips severity from non-hits.
- **Why:** An operational failure must not be hidden by a hit; a hit must not be hidden by "unknown"; "unknown" must
  not be hidden by "no hit". Enforcing the vocabulary in the type prevents drift.
- **Rejected:** Per-check ad-hoc aggregation; a numeric score.
- **Implication:** Per-item roll-up for the seed template follows the same order.

### D-010 — Interaction coverage is declared; a clean prescription on uncovered ingredients is PARTIAL_COVERAGE
- **Decision:** `INT-001` is `CHECKED_NO_HIT` only when every ingredient in the prescription appears in at least one
  seed pair (or class member). Otherwise `PARTIAL_COVERAGE` naming the uncovered ingredients. Configurable
  (`rail.interaction_require_ingredient_coverage`).
- **Why:** The seed is 15 pairs. `CHECKED_NO_HIT` for Metformin + Atorvastatin would claim a screening that did not
  happen. "Missing data must never render as safe" applies to missing *coverage*, not only missing rows.
- **Rejected:** `CHECKED_NO_HIT` with a footnote (the footnote is the thing doctors stop reading).
- **Implication:** Most clean prescriptions show `PARTIAL_COVERAGE` on INT-001 until Phase S delivers a verified
  interaction source. This is honest and is the single biggest driver of "unknown" in the held-out set; the Day-2
  Q&A asks whether the evaluators expect it.

### D-011 — Cumulative exposure: totals always, judgement only against cited ceilings, never per patient
- **Decision:** `CUM-001` sums units/day × strength per ingredient across items (frequency parsed from
  `config/frequency_patterns.json`; SOS/PRN and unparseable strings make the total a stated lower bound). The total
  is compared only to `config/reference_ceilings.json`, whose single entry (paracetamol, adult, 3 g/day) cites
  STW-GP-01 and STW-GP-04 verbatim. Without a stated patient population the ceiling is reported as "applicability not
  confirmed" and the check is `PARTIAL_COVERAGE`; exceeding a ceiling is a HIT. DUP-001 carries the same aggregate as
  its evidence (brief A.6(d)).
- **Why:** Law 2 and fence 12. A maximum daily dose from memory is an uncited clinical number; a per-patient dose is
  fenced. Quoting the corpus's own ceiling is both grounded and useful.
- **Rejected:** A hand-typed max-dose table (uncited); omitting ceilings entirely (then RX01's 2,300 mg/day carries
  no context at all).
- **Implication:** RX09 (telmisartan 80 mg/day) reports the total "without judgement" because the corpus has no
  telmisartan ceiling — exactly the honest state.

### D-012 — Severities are configuration
- **Decision:** prohibited/withdrawn → SEVERE, restricted → MODERATE, stayed → INFO, duplicate ingredient →
  MODERATE, cumulative-over-ceiling → MODERATE; seed interactions carry the seed's own severity.
- **Why:** These are clinical-policy choices; they must be changeable without a code change and visible in the
  rule-set version.
- **Rejected:** Hardcoding; deriving severity from the aggregate size (that is dose judgement).

### D-013 — Freshness windows produce `DATA_EXPIRED`
- **Decision:** Each dataset's declared version date (parsed from `source_version`) is compared to the check date;
  older than `freshness.*_max_age_days` → every check depending on it is `DATA_EXPIRED`. Values are placeholders
  (400 days) and documented as the clinical owner's decision. The stock file has no export date, so
  `data.stock_reference_date` is explicit config.
- **Why:** Law 11; a 2031 check against 2026 data must fail visibly (tested).
- **Rejected:** Using load time (says when we loaded, not how old the source is).

### D-014 — Decision-unit chunking: one bullet under one heading
- **Decision:** Each indented line of an STW page under a section heading is one unit; the heading gives section
  and unit type (assessment / red flag / recommendation / contraindication / target / monitoring); the page header
  gives code, version, effective date and supersession; the archive footer marks `superseded_by`; specialty,
  condition and population come from `config/corpus_metadata.json`. The index text is `section: text [title;
  condition]` so questions phrased by section ("red flags", "first-line") reach the right unit.
- **Why:** Brief B.1. A question is answered by a unit, cited by anchor (`p1/first_line_management/2`).
- **Rejected:** Page-level chunks (citation too coarse, mixes contraindications with recommendations); fixed token
  windows (cut units mid-sentence).
- **Implication:** Real ICMR layouts need a layout-aware extractor (assumption 3); the chunk schema will not change.

### D-015 — Hybrid retrieval with a dependency-free semantic leg, pluggable to real embeddings
- **Decision:** BM25 (own implementation) + a deterministic hashed character-n-gram/word/bigram embedding, fused by
  reciprocal rank fusion, with metadata filters (condition, source type, current-only). `sentence-transformers` is a
  config switch; the provider and model are part of the index version.
- **Why:** G1 and law 10: no network, no 100 MB model download on the critical path, and a changed embedder changes
  the index version visibly. On 83 units the difference between hashed n-grams and a transformer is immaterial;
  on 100,000 units it is not, and the switch exists for that.
- **Rejected:** API embeddings as default (key + network on the critical path); BM25 only (brief requires hybrid).
- **Implication:** `SCALE.md` names the embedder and the in-memory index as the first Module B change.

### D-016 — Extractive answering by default; LLM composition is optional and guarded
- **Decision:** The default answer is the set of supporting decision units verbatim, each with its citation and a
  source label. `answering.mode=llm` lets Claude compose a synthesis from the same units, returning JSON claims with
  unit ids; `rag/guard.py` drops any claim whose citation is unknown or whose numbers do not all appear in the cited
  unit text; if nothing survives, the verbatim units are shown and the note says why. A failed API call is a visible
  note, never a silent fallback.
- **Why:** G6 is mechanical with extractive output; the held-out set scores a confident wrong answer at −1. The LLM
  adds readability, not truth; the guard keeps it that way.
- **Rejected:** LLM-first with retrieval as context (unverifiable numbers); no LLM at all (the product needs
  readable synthesis eventually — the guard is the reusable part).
- **Implication:** The prompt sha256 is the `prompt_version` in every run; changing the prompt is a visible version
  change.

### D-017 — Answers come from current editions; superseded editions are shown separately
- **Decision:** Retrieval is current-only. Whenever a cited document has an archived edition in the corpus whose
  recommendations overlap the question, those units are returned under `superseded_editions` with dates and the
  "superseded by" pointer, never merged into claims.
- **Why:** Q3 asks about hypertension and warns that two editions exist. The first implementation let the
  "edition" wording widen retrieval and the 2021 Atenolol recommendation appeared as a claim — the eval caught it.
- **Rejected:** Answering from both editions with dates (the conflict rule is for two *valid* sources; a superseded
  edition is not valid).

### D-018 — Two abstention paths: known-absent conditions before retrieval, no-support after
- **Decision:** `config/condition_synonyms.json` lists the corpus conditions and a set of conditions doctors ask
  about that the corpus does not cover (migraine, tuberculosis, asthma…). A question that names only an absent
  condition abstains before retrieval, stating what is missing and what the corpus does cover. Any other question
  with no unit that lexically overlaps it (after light stemming) or ranks first semantically abstains after retrieval.
- **Why:** A retrieval score threshold alone is brittle (RRF scores are rank-based); naming the missing workflow is
  more useful to the doctor and to the corpus roadmap.
- **Rejected:** Score threshold only; LLM-judged relevance (a model call on the abstention path).
- **Implication:** The absent list is a maintained artefact; unknown-unknowns still fall through to the no-support
  path, which is why both exist.

### D-019 — Local protocol is labelled and compared, and absence is stated
- **Decision:** Units from `SOP-CLIN-014` carry the label "CLINIC PROTOCOL (Sunrise…, v2.1, approved 2026-03-10) —
  organization-level knowledge, not national guidance". When the clinic protocol is in play, a national-only
  retrieval runs for the same condition; if the pack has no such workflow the comparison says so and lists the
  nearest national pages as "different condition, not applicable".
- **Why:** Brief B.3: divergence shown, never hidden. For Q11 the truthful national answer is "the pack says nothing".
- **Rejected:** Treating the dengue page as the national counterpart (different condition).

### D-020 — Structured facts route to Module A, never to retrieval
- **Decision:** Questions matching identity/composition/status intents ("Is NimuPar-P banned?", "what does Sinarest
  contain") try brand n-grams through the resolver; a resolved product answers from the drug master and the
  regulatory register with event citations; an unresolved brand abstains and lists what was tried.
- **Why:** Architecture §2 boundary (b). Retrieval over clinical text is the wrong place for a gazette fact.

### D-021 — Module C is a staple, not a product
- **Decision:** `trace()` calls the rail and the answerer once each and records every version: package, engine,
  rule set and per-rule versions, dataset batches with sha256, freshness, index version, chunker, embedding, answering
  mode/model/prompt sha, config sha, and both run ids.
- **Why:** Brief C: thin integration proof; law 8 replay.

### D-022 — Review queue de-duplication for prescription items
- **Decision:** Re-running the same ambiguous prescription item re-uses the open review item rather than adding one.
- **Why:** Otherwise every rail run inflates the queue; a reviewer resolves an alias once.

### D-023 — Jan Aushadhi / NLEM are signals, not identity sources
- **Decision:** Loaded with plausibility flags (19 implausible Jan Aushadhi rows queued), used for nothing in the
  check path today.
- **Why:** The extracts are visibly synthetic (Losartan 500 mg syrup); using them to "validate" would validate noise.

### D-024 — LLM-assisted mapping is a suggestion hook, not a resolver
- **Decision:** `resolver.llm_assist_enabled` is present and `false`; when enabled, an LLM may propose candidates for
  `UNRESOLVED` items with method `llm_suggestion` (confidence 0.60 < `auto_accept_min` 0.90), so they can only land
  in the review queue with reason `LLM_SUGGESTION_UNVERIFIED`. It was not exercised in this submission (no key).
- **Why:** The brief encourages AI-assisted mapping *with verification built in*; the verification is "a human or a
  deterministic composition match confirms it", never the model's own confidence.

## What the coding agent got wrong, and how it was caught
* Let the word "edition" in Q3 widen retrieval to the superseded 2021 page; Atenolol appeared as a current claim.
  Caught by the mini-eval (`must_not_include`), fixed by D-017.
* Produced a Python 3.12 f-string (nested quotes) in the eval writer; crashed on 3.9. Caught by running it.
* Routed `Telma` to fuzzy suggestions instead of naming the brand family. Caught by reading the resolver output
  for RX04; fixed by D-004.
* The structured-route brand finder matched "Is NimuPar" as one token and found nothing. Caught by a unit test.
* pypdf rendered the bullet glyph as a DEL control character that leaked into unit text. Caught by printing the
  chunk text with `repr`.
* First rail pass showed RX01 as `PARTIAL_COVERAGE` on FDC-001 because EV004's "Caffeine" was unknown to the master;
  correct behaviour for the data as given, but the right engineering answer was D-006.

## Decisions added after the code review (2026-10-14)

An unanchored review of `src/`, `migrations/`, `config/` and `tests/` produced 14 findings; all were applied.
The ones that changed behaviour are recorded here; the rest were hygiene (constants moved to `config/settings.json`
→ `ingest.*`, audit errors no longer swallowed, `--as-of` on the eval, duplicate question field removed).

### D-025 — A resolved line is CHECKED_NO_HIT only when the whole prescription was screened
- **Decision:** In the per-line roll-up, a check that is `UNVERIFIED_INPUT`/`PARTIAL_COVERAGE`/`SOURCE_CONFLICT`/
  `DATA_EXPIRED` because of *another* line limits this line too; a HIT check with unresolved siblings counts as
  `UNVERIFIED_INPUT` for the lines not involved in the hit. RX10's Pan 40 now reads `UNVERIFIED_INPUT`, not clean.
- **Why:** The duplicate and interaction screens are pairwise; Pan 40 was never screened against the unresolved
  Thyronorm line, so "clean" was a claim the system had not earned. The review found it; the original test tolerated it.
- **Rejected:** Keeping line-level cleanliness independent of siblings (reads well, lies).

### D-026 — Condition and marker matching is word-bounded
- **Decision:** `rag/analysis.py` matches synonyms on word boundaries (markers may be word prefixes). `uti` no longer
  fires inside "routine", `ors` not inside "factors"; a malaria or typhoid question now abstains before retrieval.
- **Why:** Verified live by the reviewer: a malaria question had been answered from the UTI-in-pregnancy page — a
  confident wrong answer, the one outcome the held-out scoring punishes.

### D-027 — Every check reads only the serving (latest) batch per dataset
- **Decision:** Resolver, event loading, interaction pairs and class members filter on the latest `load_batch` of
  their dataset; `data_versions` in each output therefore names exactly the rows that were consulted.
- **Why:** Loading a corrected file is the mandated path (new batch, never in-place edits); without the filter the
  second load would have silently mixed with the first. This closes gap A12.

### D-028 — Candidate-added class mappings cannot produce a verdict until signed
- **Decision:** `ingredient_class_member.requires_signoff=1` rows are excluded from matching; a pair that would match
  only through such a mapping is reported as `PARTIAL_COVERAGE` with the pair named (`unsigned_class_matches`).
  `rail.allow_unsigned_class_members=true` is the explicit override for development.
- **Why:** The supplement file says the mapping needs clinical sign-off; the engine was not reading the flag.

### D-029 — REVOKED / LIFTED semantics
- **Decision:** A REVOKED/LIFTED event never governs. If it supersedes a STAY, the instrument the stay suspended is
  restored to force (`restored_by_revocation` in the evidence). If it supersedes a prohibition/restriction, nothing
  is restored. A REVOKED/LIFTED row with no `supersedes_event_id` is queued at load as uninterpretable.
- **Why:** The flat "superseded = gone" model would have cleared a prohibition when its stay was vacated.
- **Rejected:** Refusing REVOKED/LIFTED rows entirely (they are real gazette outcomes; better to model the one
  unambiguous case and queue the rest).

### D-030 — Replay keys instead of random run ids; corpus-file fingerprint in the index
- **Decision:** `run_id` (rail), `run_id` (Q&A) and `trace_id` are sha256 replay keys over input + date + rule/index
  version + data batches; audit rows keep their own uuid (`migration 007`). `load_index` rebuilds when any corpus
  file's sha256 differs from the one recorded in the index, not only when the chunker/embedder version changes.
- **Why:** Checked-in outputs were dirty on every regeneration, hiding real drift; an edited PDF was served stale
  under a comment that promised the opposite. `make outputs` twice now yields no diff.

### What the review caught that the tests had not
Six of the fourteen findings were behavioural (D-025..D-030); the regression tests added for them bring the suite to
63. The common thread: each was a place where the *shape* of the honest state existed but one path did not reach it
(a flag not read, a filter not applied, a key name mismatch). The lesson for `CLAUDE.md`: every "never" in the rules
needs a test that tries to do it.
