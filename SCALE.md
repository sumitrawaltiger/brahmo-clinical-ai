# SCALE.md — where Part 1 strains at 100× data and 100 concurrent users, and what changes first

**Today:** 2,000 products, 83 decision units, 12 events, 15 interaction pairs; SQLite in WAL mode; in-process BM25
and vectors; every rail run resolves brands with per-item SQL and walks all events in Python. A rail run is
≈10 ms, a question ≈20 ms, single process.

**At 100× data (200k products, ~10k units, ~1,200 events, thousands of pairs) and 100 concurrent users, in the
order things break:**

1. **SQLite's single writer.** Every rail run and every answer writes an audit row and may enqueue review items; at
   100 concurrent users writes serialize and `database is locked` appears. *First change:* PostgreSQL for the drug
   master, register and audit (schema is plain SQL, migrations carry over), with the audit log written asynchronously
   (queue → batch insert). Reads stay cheap; writes stop blocking checks.
2. **Candidate loading per item.** The resolver loads ingredients per candidate row (N+1). At 200k products brand
   families like `Kovas 2` have dozens of rows. *Change:* one query per prescription that returns products +
   ingredients for all normalized keys, plus a `current_batch` pointer per dataset so only the serving batch is read.
   Keep the funnel logic identical; it is pure and testable.
3. **Regulatory derivation walks every event.** O(events) per item. *Change:* a materialised view keyed by
   (target key, batch id) of in-force intervals `[effective_from, superseded_at)` so a status is an interval lookup;
   rebuilt on every register batch (no silent upgrades: the view carries the batch id it was built from).
4. **The RAG index is one JSON file in memory per process.** At 10k units it still fits (tens of MB) but rebuilding
   on every version check and holding vectors in Python lists across 100 workers wastes memory and makes
   deployment of a new corpus version a restart. *Change:* units + metadata in Postgres (`tsvector` for lexical,
   `pgvector` for semantic, filters as SQL `WHERE`), index version as a row; the hashed embedder swapped for a real
   embedding model (D-015) computed at ingest, not at query.
5. **Concurrency model.** The CLI is synchronous and single-process. *Change:* a thin ASGI service (FastAPI) with a
   worker pool; the rail and answerer are already pure functions of (input, versions) so they parallelise with no
   shared state; LLM composition (if enabled) is the only I/O-bound step and gets a bounded concurrency + timeout
   that degrades to extractive mode visibly (`notes`), never silently.
6. **Review queue volume.** 730 queued stock rows from 783 is fine to read; 73,000 is a workload. *Change:* alias
   learning from review decisions (D-003/A2) so each family/typo is resolved once per tenant, grouped queue views by
   normalized key, and SLA metrics on queue age — this is a human-throughput problem before it is a database one.
7. **Observability.** Today versions live inside each output; at scale they must also be metrics: resolution rate by
   method, state distribution per check, abstention rate per condition, guard-drop rate, p95 latency — per tenant.

**What I would *not* change:** the eight-state contract, the derive-don't-store rule for regulatory status, the
funnel resolver semantics, the decision-unit chunk schema, or the extractive-first + guard design. They are the
parts that make scale safe rather than merely fast.
