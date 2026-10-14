-- 003: event-sourced regulatory register. There is deliberately NO boolean status column anywhere.
-- Status is DERIVED at query time from the chain of effective-dated events (see brahmo.regulatory.status).

CREATE TABLE IF NOT EXISTS regulatory_event (
    event_id            TEXT NOT NULL,
    batch_id            TEXT NOT NULL REFERENCES load_batch(batch_id),
    notification_id     TEXT NOT NULL,
    date_published      TEXT NOT NULL,
    effective_date      TEXT NOT NULL,
    action              TEXT NOT NULL,      -- PROHIBITED | RESTRICTED | WITHDRAWN | STAY_GRANTED | (future: REVOKED, LIFTED)
    target_type         TEXT NOT NULL,      -- FDC | INGREDIENT | PRODUCT
    target_description  TEXT NOT NULL,      -- verbatim from the gazette extract
    supersedes_event_id TEXT,
    note                TEXT,
    source              TEXT NOT NULL,
    PRIMARY KEY (event_id, batch_id)
);

-- Structured interpretation of target_description, produced by the loader with a confidence + method.
-- A target whose text could not be parsed with confidence lands in the review queue and is NOT matched silently.
CREATE TABLE IF NOT EXISTS regulatory_target (
    event_id            TEXT NOT NULL,
    batch_id            TEXT NOT NULL REFERENCES load_batch(batch_id),
    ingredient_set      TEXT NOT NULL,      -- JSON array of normalized ingredient keys, sorted
    match_mode          TEXT NOT NULL,      -- exact_set | contains_all | ingredient_any
    form_qualifier      TEXT,               -- e.g. 'Suspension', 'Syrup' or NULL (all forms)
    population_qualifier TEXT,              -- e.g. 'paediatric' or NULL
    ratio_qualifier     TEXT,               -- e.g. 'specific ratio' (unresolvable from the extract) or NULL
    parse_confidence    REAL NOT NULL,
    parse_method        TEXT NOT NULL,
    unresolved_terms    TEXT,               -- JSON array of ingredient terms not present in the drug master
    PRIMARY KEY (event_id, batch_id)
);
