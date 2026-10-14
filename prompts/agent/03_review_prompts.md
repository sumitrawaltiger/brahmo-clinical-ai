# Verification prompts used after each step

> Re-run the loaders from a deleted `build/` and confirm every batch id, row count and review-queue tally is
> identical. Re-run with the same files and confirm every loader reports `skipped: true` (idempotency).

> For each seed prescription, read the JSON and check: every check status is in the vocabulary; no non-HIT carries a
> severity; every unresolved item has a review_item_id; every HIT cites a notification id + effective date (FDC-001),
> a seed pair + source tag (INT-001) or an aggregate with contributions (DUP-001).

> Derive the Nimesulide+Paracetamol status at 2018-09-10, 2020-01-01 and 2026-10-14 and confirm NONE/pending,
> STAYED and PROHIBITED with the EV003→EV002→EV001 chain. Derive Ranidom at 2024-12-01 and 2026-10-14 (RESTRICTED
> then PROHIBITED, EV005 superseded). Derive Combiflam (tablet) and confirm EV012 is excluded by the form qualifier.

> Print every chunk with its id, currency flag, unit type and population. Confirm 83 units, the 2021 hypertension
> edition is marked superseded by v2025.2, and no unit text contains control characters or bullet glyphs.

> Run the mini-eval. For every question compare the claims to the expectation. For Q3 confirm only v2025.2 is cited
> and Atenolol appears only under superseded_editions. For Q11 confirm the CLINIC PROTOCOL label and a comparison
> that states the national pack has no such workflow. Confirm uncited_numbers_total is 0.

> Run `pytest`; fix anything red; re-run `make outputs` so checked-in outputs match the code.
