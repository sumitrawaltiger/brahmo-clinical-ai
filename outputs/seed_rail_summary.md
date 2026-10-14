# Seeded rail demonstration — summary

as_of: 2026-10-14

| rx | overall | DUP-001 | FDC-001 | INT-001 | CUM-001 | unresolved items |
|---|---|---|---|---|---|---|
| RX01 | HIT | HIT (MODERATE) | CHECKED_NO_HIT | PARTIAL_COVERAGE | PARTIAL_COVERAGE | 0 |
| RX02 | HIT | CHECKED_NO_HIT | HIT (SEVERE) | PARTIAL_COVERAGE | CHECKED_NO_HIT | 0 |
| RX03 | HIT | CHECKED_NO_HIT | CHECKED_NO_HIT | HIT (SEVERE) | CHECKED_NO_HIT | 0 |
| RX04 | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | 1 |
| RX05 | PARTIAL_COVERAGE | CHECKED_NO_HIT | CHECKED_NO_HIT | PARTIAL_COVERAGE | CHECKED_NO_HIT | 0 |
| RX06 | PARTIAL_COVERAGE | CHECKED_NO_HIT | CHECKED_NO_HIT | PARTIAL_COVERAGE | CHECKED_NO_HIT | 0 |
| RX07 | HIT | HIT (MODERATE) | CHECKED_NO_HIT | PARTIAL_COVERAGE | PARTIAL_COVERAGE | 0 |
| RX08 | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | 1 |
| RX09 | HIT | HIT (MODERATE) | CHECKED_NO_HIT | PARTIAL_COVERAGE | PARTIAL_COVERAGE | 0 |
| RX10 | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | UNVERIFIED_INPUT | 1 |

## Per-line states (template columns)

| rx | item | written | state | evidence note |
|---|---|---|---|---|
| RX01 | 1 | Dolo 650 | HIT | DUP-001 MODERATE: Paracetamol in items [1, 2]; aggregate 2300.0 mg/day; aggregate 2300.0 mg/day is within the cited adult ceiling (max 3 g/day adult, STW-GP-01 v2025.1); patient population not supplied, ceiling applicability not confirmed (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX01 | 2 | Sinarest Tablet | HIT | DUP-001 MODERATE: Paracetamol in items [1, 2]; aggregate 2300.0 mg/day; aggregate 2300.0 mg/day is within the cited adult ceiling (max 3 g/day adult, STW-GP-01 v2025.1); patient population not supplied, ceiling applicability not confirmed (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX02 | 1 | NimuPar-P | HIT | FDC-001 SEVERE: PROHIBITED — GSR 411(E) published 2023-06-02 effective 2023-06-15 (DUP-001=CHECKED_NO_HIT, FDC-001=HIT, INT-001=PARTIAL_COVERAGE, CUM-001=CHECKED_NO_HIT) |
| RX03 | 1 | Warf 5 | HIT | INT-001 SEVERE: Warfarin + Azithromycin SEVERE (INR elevation; bleeding; public-high-priority-2026) (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=HIT, CUM-001=CHECKED_NO_HIT) |
| RX03 | 2 | Azee 500 | HIT | INT-001 SEVERE: Warfarin + Azithromycin SEVERE (INR elevation; bleeding; public-high-priority-2026) (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=HIT, CUM-001=CHECKED_NO_HIT) |
| RX04 | 1 | Telma | UNVERIFIED_INPUT | AMBIGUOUS_STRENGTH_MISSING: 'telma' names a brand family with 4 variants (['Telma 20', 'Telma 40', 'Telma 80', 'Telma-H 40']); strength/variant needed to pick one |
| RX05 | 1 | Glycomet 500 | PARTIAL_COVERAGE | resolved, but not fully screened (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=CHECKED_NO_HIT); INT-001: no seed pair matched, but 2 ingredient(s) are not covered by the seed list: Atorvastatin, Metformin |
| RX05 | 2 | Atorva 10 | PARTIAL_COVERAGE | resolved, but not fully screened (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=CHECKED_NO_HIT); INT-001: no seed pair matched, but 2 ingredient(s) are not covered by the seed list: Atorvastatin, Metformin |
| RX06 | 1 | Augmentin 625 Duo | PARTIAL_COVERAGE | resolved, but not fully screened (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=CHECKED_NO_HIT); INT-001: no seed pair matched, but 3 ingredient(s) are not covered by the seed list: Amoxicillin, Cetirizine, Clavulanic Acid |
| RX06 | 2 | Okacet 10 | PARTIAL_COVERAGE | resolved, but not fully screened (DUP-001=CHECKED_NO_HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=CHECKED_NO_HIT); INT-001: no seed pair matched, but 3 ingredient(s) are not covered by the seed list: Amoxicillin, Cetirizine, Clavulanic Acid |
| RX07 | 1 | Calpol 650 | HIT | DUP-001 MODERATE: Paracetamol in items [1, 2]; aggregate ≥1950.0 mg/day; aggregate ≥1950.0 mg/day is within the cited adult ceiling (max 3 g/day adult, STW-GP-01 v2025.1); patient population not supplied, ceiling applicability not confirmed (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX07 | 2 | Crocin 650 | HIT | DUP-001 MODERATE: Paracetamol in items [1, 2]; aggregate ≥1950.0 mg/day; aggregate ≥1950.0 mg/day is within the cited adult ceiling (max 3 g/day adult, STW-GP-01 v2025.1); patient population not supplied, ceiling applicability not confirmed (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX08 | 1 | Zqtrixon Forte | UNVERIFIED_INPUT | FUZZY_ONLY: no drug-master brand equals 'zqtrixon forte'; 5 near-miss candidate(s) listed for human review |
| RX09 | 1 | Telma-H 40 | HIT | DUP-001 MODERATE: Telmisartan in items [1, 2]; aggregate 80.0 mg/day; no cited reference ceiling in the corpus for this ingredient; total reported without judgement (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX09 | 2 | Telma 40 | HIT | DUP-001 MODERATE: Telmisartan in items [1, 2]; aggregate 80.0 mg/day; no cited reference ceiling in the corpus for this ingredient; total reported without judgement (DUP-001=HIT, FDC-001=CHECKED_NO_HIT, INT-001=PARTIAL_COVERAGE, CUM-001=PARTIAL_COVERAGE) |
| RX10 | 1 | Pan 40 | UNVERIFIED_INPUT | resolved, but not fully screened (DUP-001=UNVERIFIED_INPUT, FDC-001=UNVERIFIED_INPUT, INT-001=UNVERIFIED_INPUT, CUM-001=UNVERIFIED_INPUT); DUP-001: 1 item(s) could not be resolved to a product; duplicate check incomplete / FDC-001: 1 item(s) unresolved; regulatory status cannot be checked for them / INT-001: 1 item(s) unresolved; their ingredients could not be screened / CUM-001: 1 item(s) unresolved; totals exclude them |
| RX10 | 2 | Thyronorm 50 | UNVERIFIED_INPUT | STRENGTH_MISMATCH: written strength '50 mcg' matches no master row for brand 'thyronorm 50'; written unit 'mcg' vs master unit(s) ['mg'] — possible unit conflict in source |
