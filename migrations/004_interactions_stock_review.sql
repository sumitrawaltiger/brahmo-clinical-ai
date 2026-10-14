-- 004: interaction seed, pharmacy stock ingestion, alias table, and the review queue.

CREATE TABLE IF NOT EXISTS interaction_pair (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    ingredient_a    TEXT NOT NULL,
    ingredient_b    TEXT NOT NULL,
    a_norm          TEXT NOT NULL,
    b_norm          TEXT NOT NULL,
    pair_key        TEXT NOT NULL,          -- sorted "a_norm|b_norm" so lookups are order-independent
    severity        TEXT NOT NULL,
    note            TEXT,
    source_tag      TEXT NOT NULL,
    a_in_master     INTEGER NOT NULL,       -- 1 if a_norm resolves to a drug-master ingredient
    b_in_master     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_interaction_pair_key ON interaction_pair(pair_key);

-- Pharmacy stock: every row is untrusted input. The parsed columns are the loader's reading; resolution is recorded, never assumed.
CREATE TABLE IF NOT EXISTS stock_item (
    id                  INTEGER PRIMARY KEY,
    batch_id            TEXT NOT NULL REFERENCES load_batch(batch_id),
    row_no              INTEGER NOT NULL,
    item_name_as_billed TEXT NOT NULL,
    qty_units           INTEGER,
    mrp_inr             REAL,
    batch_no            TEXT,
    expiry              TEXT,
    parsed_brand_text   TEXT,
    parsed_form         TEXT,
    parsed_pack         TEXT,
    resolution_status   TEXT NOT NULL,      -- RESOLVED | AMBIGUOUS | UNRESOLVED
    resolved_product_id TEXT,
    resolved_batch_id   TEXT,
    confidence          REAL,
    method              TEXT,
    review_item_id      INTEGER,
    expiry_flag         TEXT                -- EXPIRED | EXPIRING_90D | NULL
);

-- Alias table: colloquial / billing spellings -> brand. Populated by review decisions or verified rules; never by fuzzy matching alone.
CREATE TABLE IF NOT EXISTS brand_alias (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    alias_text      TEXT NOT NULL,
    alias_norm      TEXT NOT NULL UNIQUE,
    brand_norm      TEXT NOT NULL,
    product_id      TEXT,                   -- NULL when the alias names a brand family, not one SKU
    kind            TEXT NOT NULL,          -- billing_string | colloquial | typo | manual
    confidence      REAL NOT NULL,
    method          TEXT NOT NULL,
    decided_by      TEXT
);

-- Review queue: the only destination for anything uncertain (brief A.3, gate G3).
CREATE TABLE IF NOT EXISTS review_queue (
    item_id         INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    entity_type     TEXT NOT NULL,          -- stock_item | prescription_item | regulatory_target | product_row | interaction_term
    raw_input       TEXT NOT NULL,
    context         TEXT,                   -- JSON: where it came from (rx_id, row_no, ...)
    reason_code     TEXT NOT NULL,          -- see brahmo.normalize.reasons
    reason_detail   TEXT,
    candidates      TEXT,                   -- JSON array of candidate product ids / interpretations with scores
    status          TEXT NOT NULL DEFAULT 'OPEN',   -- OPEN | RESOLVED | REJECTED
    created_at      TEXT NOT NULL,
    decided_at      TEXT,
    decided_by      TEXT,
    decision        TEXT
);
CREATE INDEX IF NOT EXISTS ix_review_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS ix_review_reason ON review_queue(reason_code);
