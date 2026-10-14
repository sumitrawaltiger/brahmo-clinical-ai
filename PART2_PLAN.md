# PART 2 — Plan to the finished clinical AI

**Goal, restated as the gate this plan ends on:** 100 doctors use BRAHMO simultaneously for a measured period,
each asking at least 1,000 real clinical questions they would otherwise take to ChatGPT/Claude, with their
satisfaction measured and compared against those assistants under a pre-registered protocol — and the system passes
the release gates in §6 before the first doctor logs in.

**Duration: 5 weeks** (defended in §2). Team: 4 people + AI-first development. Starting point: the Part 1 codebase.

---

## 1. Completion architecture

### 1.1 What exists after Part 1 (and is kept)
| component | state | keep / change |
|---|---|---|
| Drug master schema, `load_batch` provenance, numbered migrations | works on 2k products | keep schema; move to Postgres (SCALE §1) |
| Resolver funnel + review queue + reason codes + alias table | zero silent resolutions | keep semantics; add alias learning from review decisions |
| Event-sourced register + target interpretation with confidence | 12 events | keep; add curation workflow + materialised in-force intervals |
| Rail: 4 checks, 8-state contract, precedence, freshness, audit | all seeds correct | keep contract verbatim; add checks (allergy, pregnancy, renal flags) in Phase S |
| Decision-unit chunker, hybrid retrieval, extractive answers, guard, eval | 11/11, 0 uncited numbers | keep schema + guard; replace extractor and embedder |
| Trace with every version | works | keep; becomes the audit record of every live answer |

### 1.2 What is missing (the honest list)
Corpus at scale (12 pages → thousands of units), a verified interaction/allergy/pregnancy source, patient-context
integration (snapshot contract), orchestration (structured-first routing already exists; needs the composition and
abstention policy for live use), a doctor-facing surface, multi-tenancy, concurrency, freshness watchers,
re-evaluation on any change, and the quality system that makes 100,000 answers reviewable.

### 1.3 Target architecture

```text
 upstream contracts (scribe entities · patient-context snapshot · tenant id)
          │
          ▼
 ┌──────────────── API (ASGI, per-tenant auth, request = {rx?, question?, patient_ctx_ref?, as_of}) ─────────────┐
 │  ROUTER (deterministic): structured fact → DRUG MASTER · narrative → RETRIEVAL · neither → ABSTAIN           │
 │                                                                                                               │
 │  DRUG MASTER (Postgres)         REGISTER (events + curated targets)     SAFETY RAIL (pure; checks DUP/FDC/   │
 │  current_batch per dataset      in-force intervals materialised         INT/CUM + ALG/PRG; 8 states;        │
 │  resolver + alias store         per batch                                patient-aware via snapshot)         │
 │                                                                                                               │
 │  CORPUS SERVICE: ingestion jobs → layout-aware extraction → unit review → units table (tsvector + pgvector)   │
 │  RETRIEVAL: hybrid + filters (specialty, condition, population, source tier, current) → units                 │
 │  COMPOSER: LLM (versioned prompt) → claims with unit ids → GUARD (citation + numeric + fence lexicon)         │
 │           → degrade to extractive on any failure, visibly                                                     │
 │                                                                                                               │
 │  TRACE STORE (every answer: versions, units, checks, guard drops, latency)  ──► QUALITY PIPELINE (§6)         │
 │  FRESHNESS WATCHERS (gazette, STW, corpus sources) → new batch → re-eval gate → promote current_batch         │
 └───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
 doctor surface: answer card (claims + citations + labels), check states as states (never "safe"), one-tap
 "show source", "wrong/unhelpful" feedback bound to the trace id
```

Key completions, each with its binding law:
* **Corpus at scale (law 2, 3):** sources in §3, ingested as jobs; each document version is a batch; a
  layout-aware extractor (PDF → structured blocks) feeds the same decision-unit schema; a *unit review* queue (like
  the drug review queue) where a clinical reviewer accepts/edits units before they serve — units carry
  `review_status` and only `ACCEPTED` units are retrievable in production.
* **Safety coverage (law 4, 5):** interactions from a verified public/licensed source (§3) loaded as versioned
  pairs with coverage metadata, so `INT-001` can say `CHECKED_NO_HIT` honestly; allergy relations (ingredient
  ↔ class) and pregnancy-category rules as new checks `ALG-001`, `PRG-001`, each with provenance and sign-off state;
  a rule serves only after clinical sign-off is recorded against its version.
* **Patient context (law 1, 9; Phase C):** the snapshot is a *reference* (id + version), fetched by the rail at
  check time; allergies/current meds/conditions become inputs to ALG/INT/PRG; nothing is stored in the trace beyond
  the snapshot id and version (DPDP minimisation).
* **Orchestration:** the Part 1 router stays deterministic; composition is LLM-only for narrative answers, with the
  guard extended by a *fence lexicon* (patterns for per-patient dose computation, triage scores, diagnosis ranking)
  that forces abstention when the model drifts into fenced territory.
* **Freshness (law 10, 11):** watchers for the e-Gazette (CDSCO drug notifications), ICMR STW page, and each corpus
  source; a change creates a batch, runs the full eval + seed rail + regression set, and only then promotes
  `current_batch`. A failed re-eval leaves the old batch serving and raises a visible "stale" banner with the date.
* **Audit/replay (law 8):** every live answer = a trace row; `replay(trace_id)` re-runs against the pinned versions.
* **Multi-tenancy:** tenant id on every row that is tenant-owned (local protocols, aliases learned from a clinic's
  stock, review decisions, feedback); national data shared; Postgres row-level security; per-tenant retrieval filter
  so one clinic's protocol never appears to another.
* **Concurrency for 100 users:** stateless workers behind the API; rail and retrieval are CPU-bound and fast;
  LLM calls bounded by a concurrency limit per tenant with p95 latency budget (§6); extractive degrade on timeout.

## 2. Week-by-week plan (5 weeks) with binary gates

**Why 5 weeks, not 3 or 6.** Three weeks cannot absorb the two non-code dependencies that gate everything —
clinical sign-off throughput on rules/units and doctor recruitment/consent (§7); six weeks would spend a week on
polish that the 100-doctor test will tell us about better than we can guess. Five weeks puts the test in week 5
with one full week of buffer inside the schedule (week 4 is deliberately light on new scope).

**Team shape:** 1 tech lead/architect (me), 1 engineer (data + corpus pipelines), 1 clinical lead (part-time
physician who owns sign-offs and the reviewer panel), 1 product/ops (doctor recruitment, consent, study ops,
support). AI-first development means the engineers *specify, review and test*; agents write the code under
`CLAUDE.md`-style rules; every PR carries the prompt used and the eval delta.

| week | deliverables | binary gate (pass/fail) | AI builds | humans must do |
|---|---|---|---|---|
| **1** Foundation at scale | Postgres migration; `current_batch`; alias learning; in-force interval view; corpus ingestion jobs + layout-aware extractor spike on 20 real ICMR STW PDFs; unit review queue; API skeleton with tenant auth; trace store | (a) `make reproduce` + full test suite green on Postgres; (b) ≥ 90 % of units from the 20 real PDFs accepted by the clinical lead *without edit* (else extractor redesign); (c) 100 concurrent synthetic rail requests, p95 < 300 ms | all code | clinical lead reviews units; counsel confirms classification posture for the test (§7) |
| **2** Grounding | Corpus: ICMR STWs (all available), national programme guidelines (§3 tier 1) ingested, reviewed, served; real embedding model; eval set grown to 150 questions (50 from doctors' real questions, 50 edge/abstain, 50 held-back internally); composer + guard + fence lexicon in `llm` mode | (a) eval: 0 wrong on the 150; abstention precision ≥ 95 % (an abstention is "correct" when a reviewer agrees the corpus lacks support); (b) guard drop rate < 5 % of claims (else prompt/unit quality work); (c) every unit served has `review_status=ACCEPTED` | all code, prompt iterations with eval diffs | reviewer panel (3 physicians) accepts units; signs the eval expectations |
| **3** Safety expansion + patient context | Verified interaction source loaded (§3); `ALG-001`, `PRG-001`; snapshot contract + client; rail patient-aware; freshness watchers for gazette + STW; re-eval gate wired to `current_batch` promotion | (a) rule sign-off ledger: 100 % of serving rules have a signed version; (b) seed rail + 60 new adversarial prescriptions: 0 false negatives, 0 unknown-rendered-as-safe; (c) a simulated gazette change flips a status after re-eval and not before | all code | clinical lead signs rules; data rights confirmed for the interaction source |
| **4** Doctor surface + pilot readiness (buffer week) | Answer card + check-state rendering + feedback bound to trace id; per-tenant local-protocol upload with labelling; load test at 100 users × realistic mix; study tooling (randomisation, comparator capture, satisfaction forms); dry run with 10 friendly doctors for 3 days | (a) dry-run doctors complete ≥ 50 questions each with < 2 % "unanswerable for a technical reason"; (b) p95 end-to-end < 4 s with LLM, < 1 s extractive; (c) DPDP checklist signed (purpose, minimisation, retention, deletion test passes) | all code | ops recruits 100 doctors + consent; product runs the dry run; counsel signs the DPDP checklist |
| **5** The 100-doctor test | Freeze versions (all batches, prompts, models pinned); run the study; daily quality pipeline (§6); hot-fix policy = config/data only, no model/prompt changes mid-study | (a) ≥ 100 doctors active, ≥ 100,000 answered or honestly-abstained questions; (b) quality pipeline runs daily with human sample reviewed; (c) pre-registered comparison analysis produced | monitoring, analysis notebooks | study ops, reviewer panel, analysis sign-off |

A gate that fails stops the next week's scope, not the schedule: week 4's buffer absorbs one failed gate; two
failed gates move the test by a week and I say so in week 3, not week 5.

## 3. Sources and data strategy

| tier | source | content | rights / cost | status |
|---|---|---|---|---|
| 1 corpus, free | ICMR Standard Treatment Workflows (stw.icmr.org.in) | one-pagers across specialties | public, attribution; ₹0 | ingest, review units |
| 1 corpus, free | National programme guidelines: NTEP (TB), NVBDCP/NCVBDC (malaria, dengue), RMNCH+A/MoHFW maternal & child, NACO, ICMR AMR treatment guidelines, National Health Mission SOPs | narrative PDFs | public; ₹0 | ingest; chunking is the work |
| 1 corpus, free | NLEM 2022, Jan Aushadhi (PMBJP) catalogue | essential list, generics/prices | public; ₹0 | already loaded as signals |
| 2 corpus, society | Indian specialty society guidelines (API, IAP, FOGSI, RSSDI, CSI, IOA…) | narrative, often behind membership | per-society permission; some ₹0 with attribution, some require agreements; budget ₹5–15 L/yr for the ones that charge | legal to clear per society before ingest; serve nothing without a written permission on file |
| 3 drug master, free/public | CDSCO SUGAM approvals, Gazette of India (egazette.gov.in) notifications, manufacturer package inserts (public), PMBJP, NRCeS/CDCI codes where accessible | brand → composition, regulatory events | public; ₹0; scraping/retrieval effort + pharmacist verification | must be built; this is the FDC decomposition at scale |
| 3 drug master, licensed | CIMS/MIMS India, 1mg/PharmEasy catalogues | brand catalogues | licensed; *not used* unless a licence is signed; the e-mail's rule applies to the product too | fallback if public build is too slow |
| 4 safety, public | FDA/EMA SmPC labels (public), WHO AWaRe/EML, DDInter / TWOSIDES (research licences), ONC high-priority DDI list (the seed's apparent origin) | interactions, pregnancy categories | public/research; check licence per set; ₹0–small | load as versioned pairs with coverage metadata; every pair gets clinical sign-off before serving |
| 4 safety, licensed | Micromedex / Lexicomp / BNF | gold-standard interactions | licensed; ₹20–60 L/yr; API terms restrict derived products | only if the public build fails week-3 gate (b); budget as contingency |
| 5 synthetic/test | adversarial prescriptions, edge questions | eval only | built in-house | growing continuously |

Rights considerations: everything served carries source, version and licence basis in metadata; the corpus
service refuses to promote a batch whose source has no rights record; tenant-uploaded local protocols are the
tenant's data under their consent; no patient data ever enters the corpus or the eval sets.

Rough data cost for 5 weeks: ₹0 for tier 1/3/4 public content; ~₹3–5 L in pharmacist/reviewer time for FDC
verification (≈ 3,000 FDCs at a sustainable 150/day/reviewer); society permissions ₹0–5 L depending on which
societies; licensed contingency not spent unless triggered.

## 4. Gap analysis — concrete weaknesses in the materials I was given

1. **Brand is not an identity key in the provided master, and the upstream contract does not say strength/form are
   mandatory.** 563 brand names carry multiple compositions. *Do:* make `strength` and `form` required fields of the
   scribe → Rx entity contract, with "unknown" as an explicit value that the rail renders as `UNVERIFIED_INPUT`;
   put a resolution-rate SLO (≥ 97 % of items resolved without review) on the scribe team, not the rail.
2. **"Prohibited FDC per event-sourced status" assumes machine-readable targets; gazette text is not.** "Specific
   ratio", "paediatric suspensions only", "codeine-based cough FDCs". *Do:* make target interpretation a curated,
   versioned, signed artefact with its own review queue (built in Part 1 as `regulatory_target`), and plan reviewer
   time for it.
3. **The interaction seed implies a coverage model that does not exist.** 15 pairs, class names ("Nitrates"), terms
   absent from the master. A rail that says `CHECKED_NO_HIT` on this seed is lying. *Do:* coverage as data (which
   ingredients a source covers) and a `CHECKED_NO_HIT` that is only possible inside coverage — and a real source in
   week 3.
4. **The architecture document's conflict rule ("show both") has no tiering.** When a national programme guideline
   and a society guideline disagree, "show both" is right, but doctors need to know which is the regulator's
   position. *Do:* source tiers in metadata (programme/regulator > ICMR STW > society > local), displayed, never used
   to suppress.
5. **The phase skeleton has no corpus-ingestion quality loop.** Real STW PDFs are flowcharts; nothing in the
   materials budgets for unit review. *Do:* week-1 gate (b) and the unit review queue.
6. **The held-out scoring (+1/0/−1) and the product metric could diverge.** A system tuned to it abstains whenever
   coverage is thin; doctors experience that as uselessness. *Do:* the quality system (§6) measures *abstention
   precision* and *answerable-but-abstained rate* separately and sets targets for both.
7. **No definition of "patient-aware" that respects DPDP minimisation.** *Do:* snapshot-by-reference (id + version),
   fetched at check time, never persisted in traces.
8. **The stock file is the only clinic-side data and it is a billing export without an export date.** *Do:* the
   tenant upload contract requires an export timestamp; expiry and stock checks are tenant features, not rail
   features.

## 5. The doctor's reality

| problem | how the plan handles it |
|---|---|
| **Trust** ("why should I believe this over ChatGPT?") | Every claim shows its source, version and section one tap away; abstentions name what is missing; the comparison study publishes the measured correctness of both. Trust is earned by being visibly right about being unsure. |
| **Speed** (a consult is 5–8 minutes) | Extractive answers in < 1 s; LLM composition under a p95 of 4 s with visible degrade; structured facts (is X banned, what is in Y) answered instantly from the master. Rail runs inline on the draft; no modal interruptions. |
| **Alert fatigue** | Severity is config and reviewed against feedback; H1-type restrictions render as INFO after week-4 dry-run data; the same duplicate-ingredient hit on the same patient is shown once per draft; every alert carries a one-line reason, not a wall. The feedback button is on the alert itself and feeds §6. |
| **Unanswerable questions** | The absent-conditions list grows from real questions (week 2: 50 real doctor questions feed it); the answer for an absent condition says which workflows *are* covered and lets the doctor request one; the corpus roadmap is literally the abstention log sorted by frequency. |
| **Language** | Phase 1 is English clinical text (the sources are English); Hindi/regional *questions* are routed through the same analysis with transliteration of brand names (the resolver already folds spelling); answers stay in the source language with citations — translating a dose is a fence until a reviewed translation layer exists. |
| **Workflow interruption** | Rail states appear in the prescription pad where the item is, not in a separate screen; Q&A is a side panel with the patient context already attached; nothing requires the doctor to re-type. |
| **"The system said unknown" (coverage states)** | `PARTIAL_COVERAGE`/`UNVERIFIED_INPUT` render as a short grey state with the exact reason ("Telma — which strength?") and a one-tap fix (pick 40 mg) that resolves the item and re-runs the check. |
| **Local practice vs national guidance** | Clinic protocols upload per tenant, are labelled as the clinic's, and are shown next to (never instead of) the national unit. |
| **Blame and liability** | Every state is a draft; the doctor confirms; the trace is the record. Counsel reviews the surface wording in week 4. |

## 6. The quality system

**"Excellent", operationally, for the 100-doctor test:**

| measure | definition | release gate (must pass before week 5) | study target |
|---|---|---|---|
| Cited correctness | reviewer agrees every consequential claim is supported by its cited unit | 100 % on the 150-question eval; 0 uncited numbers (mechanical) | ≥ 99 % on the sampled set |
| Confident-wrong rate | an answer a reviewer marks as wrong *and* that did not abstain | 0 on eval | < 0.5 % sampled, each one root-caused |
| Abstention precision | share of abstentions where the reviewer agrees the corpus lacks support | ≥ 95 % | ≥ 95 % |
| Answerable-but-abstained | share of abstentions where support existed | ≤ 5 % | ≤ 5 %, trending down weekly |
| Rail false negatives | known-bad adversarial set | 0 | 0 on the weekly adversarial run |
| Unknown-as-safe | any `CHECKED_NO_HIT` outside declared coverage | 0 (mechanical) | 0 |
| Latency | p95 extractive / LLM | < 1 s / < 4 s at 100 concurrent | same |
| Satisfaction | per-answer 1–5 + "would use again"; per-doctor weekly NPS | — | the comparison in §6.2 |

**6.1 QA of 100,000 answers without 100,000 reviews.** Layers, cheapest first:
1. *Mechanical guards on every answer* (citation exists, numbers cited, fence lexicon, state vocabulary) — 100 %.
2. *Automatic risk scoring* per answer: guard drops, low retrieval overlap, dose/pregnancy/paediatric markers,
   new condition, negative feedback → a risk score. Everything above a threshold goes to review — expected 3–5 %.
3. *Stratified random sample* of the rest: 1 % per day stratified by specialty, condition, answer type, tenant.
4. *Calibrated LLM judge* (a different model than the composer, versioned prompt) scores every answer on the same
   rubric the humans use; it is trusted only after agreement with the reviewer panel on 500 double-scored answers
   reaches κ ≥ 0.8, re-checked weekly; disagreements go to humans; the judge never *approves* a flagged answer, it
   only *prioritises*.
5. *Human panel* (3 physicians, ~40 answers/hour each) covers layers 2–4: ~1,500 answers/day capacity vs ~1,000/day
   needed at 20,000 answers/day.
6. *Weekly drift report*: metrics per model/prompt/batch version; any version change inside the study is forbidden
   except data hot-fixes, which re-run the eval before promotion.

**6.2 The satisfaction comparison, designed to be fair.** Within-subject: each doctor's real questions, asked in the
flow of their work, are answered by BRAHMO; a pre-registered random 10 % subset (per doctor, stratified by specialty)
is *also* submitted verbatim to ChatGPT and Claude (current consumer versions, pinned and recorded) at the same time
by the study tool, and the three answers are shown to the doctor in random order with provenance stripped for the
rating step; the doctor rates each on correctness-as-they-judge-it, usefulness and trust (1–5) and picks a
preference. Citations are shown *after* the blind rating so the citation effect is measured separately. Primary
endpoint: pairwise preference rate BRAHMO vs each assistant with 95 % CI; secondary: per-dimension means,
abstention acceptability ("the system declined — was that right?"), and reviewer-scored correctness of all three on
the same subset so satisfaction can be read against truth. Analysis plan is written before the study and committed.

## 7. Dependencies and critical path (the things that are not code)
1. **Clinical sign-off throughput** — units, rules, target interpretations, eval expectations. One part-time physician
   cannot sign 5,000 units; the panel of 3 and the unit-review tooling in week 1 are on the critical path.
2. **Doctor recruitment and consent** — 100 active doctors need ~150 recruited; starts week 1, not week 4.
3. **Data rights** — society permissions and the interaction source; a source without rights on file does not serve.
4. **Regulatory classification counsel** — confirm the test runs as a documentation/reference study with clinical-
   support features behind sign-off; wording of states and disclaimers reviewed (they don't move the line, but they
   must be honest).
5. **DPDP** — consent texts, purpose binding, minimisation (snapshot by reference), retention and deletion test.
6. **Model/API capacity and pinning** — pinned model versions for composer and judge for the study window; rate
   limits sized for 100 concurrent users.
7. **Hospital/clinic IT** — tenant onboarding, SSO or accounts, local protocol uploads.

Critical path: reviewer tooling (W1) → unit/rule sign-off (W2–3) → dry run (W4) → study (W5), with recruitment
running underneath from day 1.

## 8. Fences — deliberately not built in this version
Patient-specific dose calculation (including mg/kg conversion and renal/hepatic adjustment), diagnostic ranking,
triage/severity scoring, auto-generated treatment plans, patient-facing output, translation of clinical numbers,
auto-resolution of any ambiguous drug, auto-acceptance of any rule or unit without sign-off, cross-tenant learning
from one clinic's data, and any check path that calls a model. Each is either a regulatory-classification decision
(device-grade) or a trust decision that the 100-doctor test should inform, not pre-empt.

## 9. Top 10 risks and a rough cost picture

| # | risk | mitigation |
|---|---|---|
| 1 | Real STW/guideline PDFs defeat the extractor; unit quality low | week-1 gate (b) on 20 real PDFs; fall back to semi-manual unit authoring for the launch specialties |
| 2 | Reviewer throughput is the bottleneck | tooling first; prioritise units by expected question volume; batch sign-off with diffs |
| 3 | Abstention rate too high → doctors leave | measure answerable-but-abstained; grow corpus from the abstention log weekly; extractive answers for partial support rather than silence |
| 4 | LLM composition drifts into fenced territory | guard + fence lexicon + judge; degrade to extractive; hard block on fence patterns |
| 5 | Interaction source rights or quality fail | public build in parallel with a licensed contingency; coverage declared either way |
| 6 | Doctor recruitment short | start week 1; over-recruit 1.5×; incentives via study ops |
| 7 | Load/latency under 100 concurrent | week-1 and week-4 load gates; stateless workers; extractive degrade |
| 8 | A gazette change mid-study | watcher → batch → re-eval → promote; stale banner otherwise |
| 9 | Comparison study bias (order, citation halo) | randomised order, blind rating before citations, pre-registered analysis |
| 10 | DPDP/consent gap discovered late | checklist signed in week 4 gate (c); snapshot-by-reference from week 3 |

**Rough cost (5 weeks):** people — 4 FTE-equivalents ≈ ₹25–35 L; reviewer panel (3 physicians part-time) ≈ ₹6–9 L;
infra — managed Postgres + pgvector, 3–6 workers, object storage, observability ≈ ₹1.5–3 L; model usage — ~120k
composed answers + 120k judge calls + eval runs at mid-tier model prices ≈ ₹8–15 L (bounded by the per-tenant
concurrency cap; extractive mode costs nothing); data — ₹3–10 L as in §3; contingency licence not budgeted unless
triggered. Order of magnitude: ₹45–75 L for the five weeks, dominated by people and review time, which is the
correct shape for a system whose safety is a human-signed artefact.
