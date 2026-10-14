# Freshness demo — a new gazette notification arrives

Probe: `Azee 500` in seed prescription RX03; check date 2026-10-14. Demo database `freshness_demo.sqlite` (serving data untouched).

**Added event (synthetic, labelled as such):** DEMO-GSR-000(E) — RESTRICTED Azithromycin (all products), published 2026-09-15, effective 2026-10-01.

| step | register batch | status | governing / pending |
|---|---|---|---|
| before | `gazette:extract-through-2025-11-02:a57b5a9d` | NONE | — |
| after v2 loaded | `gazette:extract-through-2026-09-15:ec5a1fae` | **RESTRICTED** | [('DEMO-GSR-000(E)', '2026-10-01')] |
| after v2, check date 2026-09-20 (published, not yet effective) | `gazette:extract-through-2026-09-15:ec5a1fae` | NONE | pending [('DEMO-GSR-000(E)', '2026-10-01')] |
| replay against v1 after v2 exists | `gazette:extract-through-2025-11-02:a57b5a9d` | NONE | — |

**Rail FDC-001 on RX03:** before `CHECKED_NO_HIT` (data `gazette:extract-through-2025-11-02:a57b5a9d`) → after `HIT` MODERATE — Azee 500: RESTRICTED per DEMO-GSR-000(E) (eff. 2026-10-01) (data `gazette:extract-through-2026-09-15:ec5a1fae`)

What the mechanism guarantees:
- a new register is a new load_batch (sha256 + version); v1 rows are never edited
- every check reads the serving (latest) batch and records its id in data_versions
- an event published before but effective after the check date is reported as pending, not in force
- the v1 batch stays queryable, so any pre-change output can be replayed against exactly what produced it
- in production this load sits behind a re-evaluation gate (seed rail + eval must pass) before the batch is promoted — see PART2_PLAN §1.3
