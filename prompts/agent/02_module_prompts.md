# Module task prompts, in the order issued

Each block is the instruction the agent executed for that step. Commits in `git log` map 1:1 onto these.

## Step 0 — kit reading and data profiling
> List every file in the kit. Read the index, brief, architecture edition, templates, sample questions, local
> protocol, all CSVs and extract the text of every STW PDF. Profile the CDCI subset (row count, FDC count, distinct
> ingredients, brands with more than one composition, structured-column vs strength_text consistency), the stock
> file (billing-string token patterns, how many resolve exactly, by form, ambiguously, or not at all), the gazette
> events (supersession links, qualifiers in target text, ingredient terms absent from the master), the interaction
> seed (terms absent from the master) and the Jan Aushadhi/NLEM extracts (implausible rows). Report anomalies.

## Step 1 — scaffold, config, migrations, loaders, resolver, review queue
> Create a fresh repo `brahmo-clinical-ai`. Copy the data pack to `data/` and the PDFs to `corpus/`, record input
> checksums. Put all settings in `config/settings.json` with env overrides. Write numbered migrations:
> load_batch provenance; drug master (product, ingredient, product_ingredient with confidence+method); event-sourced
> regulatory register (events + structured target interpretation with confidence, no status column); interaction
> seed with master-coverage flags; stock items; brand aliases; review queue; audit tables. Write idempotent loaders
> that register a batch per file sha256 and queue every uncertainty with a reason code. Write the resolver per the
> standing instructions. Expose `brahmo migrate|ingest|setup|review|resolve|versions`.

## Step 2 — regulatory status and the deterministic rail
> Implement status derivation (effective ≤ as-of, global supersession, in-force set, conflicts, pending, stays,
> form/population/ratio qualifiers, register gaps for targets with unknown terms). Implement the rail with four
> checks (DUP-001 duplicate ingredient with aggregate evidence; FDC-001 regulatory via the register; INT-001 seed
> interactions with declared coverage; CUM-001 per-ingredient daily totals annotated against cited ceilings only)
> under the 8-state contract with precedence, freshness → DATA_EXPIRED, preflight → SERVICE_UNAVAILABLE, audit log.
> Run the 10 seed prescriptions; write per-rx JSON, the completed template CSV and a summary table.

## Step 3 — candidate-added ingredient vocabulary
> Gazette targets name Caffeine/Codeine/Ornidazole and the interaction seed names 16 terms absent from the CDCI
> subset, so exact-set matching could never run for them. Add `data/supplements/ingredient_supplement.csv` with
> names only (no products), provenance per row, a class→members row for 'Nitrates', a migration, a loader that
> runs before gazette/interactions, and a config switch to disable it. Record it in DESIGN.md and the gaps register.

## Step 4 — Module B
> Chunk every STW PDF into decision units (one bullet per unit, section heading as context, unit type from the
> heading, code/version/effective/supersedes from the page header, archive footer → superseded_by, specialty/
> condition/population from `config/corpus_metadata.json`). Chunk the local protocol into numbered steps labelled
> as organization-level. Build BM25 + a dependency-free hashed embedding (pluggable to sentence-transformers) fused
> by RRF with filters (condition, source type, current only). Write the answerer: deterministic question analysis
> (corpus conditions, absent conditions, dose/paediatric/pregnancy/local markers, structured-fact intent), Module A
> routing for structured facts, pre-retrieval abstention for absent conditions, extractive verbatim claims with
> citations, optional LLM composition behind a numeric+citation guard, superseded editions surfaced separately,
> clinic-vs-national comparison that states absence explicitly. Write the mini-eval with expectations taken from the
> corpus text and a mechanical uncited-number check.

## Step 5 — Module C and tests
> One function: prescription + question → one JSON with normalization, all four checks, the grounded answer and
> every version (package, engine, rules, datasets with sha256, freshness, index, chunker, embedding, answering mode/
> model/prompt sha, config sha). Write pytest coverage for provenance, zero silent resolution, regulatory chains,
> rail states incl. DATA_EXPIRED and SERVICE_UNAVAILABLE, Module B behaviours, and the trace. Add a Makefile so a
> fresh clone reproduces everything.

## Step 6 — documents
> Write README, DESIGN (restatement, three riskiest assumptions, decisions with rejected alternatives, what the
> agent got wrong), GAPS_REGISTER (scope cuts + every data anomaly found), SCALE, QA_DAY2, SUBMISSION, CLAUDE.md,
> the prompt library, and the Part 2 plan.
