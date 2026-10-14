-- 002: India drug master. brand/SKU -> formulation -> strength -> active ingredient(s).
-- Products are never edited in place; a new source version is a new load_batch with new rows.

CREATE TABLE IF NOT EXISTS ingredient (
    ingredient_id   INTEGER PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,  -- as given by the canonical source (CDCI subset)
    norm_name       TEXT NOT NULL,         -- lower-cased, punctuation-folded key used for matching
    first_seen_batch TEXT NOT NULL REFERENCES load_batch(batch_id)
);
CREATE INDEX IF NOT EXISTS ix_ingredient_norm ON ingredient(norm_name);

CREATE TABLE IF NOT EXISTS product (
    product_id      TEXT NOT NULL,          -- source identifier (CDxxxx)
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    brand_name      TEXT NOT NULL,
    brand_norm      TEXT NOT NULL,          -- matching key
    manufacturer    TEXT,
    dose_form       TEXT,
    strength_text   TEXT,
    source          TEXT NOT NULL,
    source_version  TEXT NOT NULL,
    effective_from  TEXT NOT NULL,
    is_fdc          INTEGER NOT NULL DEFAULT 0,
    ingredient_count INTEGER NOT NULL,
    PRIMARY KEY (product_id, batch_id)
);
CREATE INDEX IF NOT EXISTS ix_product_brand_norm ON product(brand_norm);

-- FDC decomposition: one row per (product, salt). Confidence + method are mandatory (brief A.2 / A.4).
CREATE TABLE IF NOT EXISTS product_ingredient (
    product_id      TEXT NOT NULL,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    position        INTEGER NOT NULL,
    ingredient_id   INTEGER NOT NULL REFERENCES ingredient(ingredient_id),
    strength_value  REAL,
    strength_unit   TEXT,                   -- 'mg' in the provided extract; kept explicit
    confidence      REAL NOT NULL,
    method          TEXT NOT NULL,          -- structured_columns | strength_text_parse | llm_assisted | manual
    PRIMARY KEY (product_id, batch_id, position),
    FOREIGN KEY (product_id, batch_id) REFERENCES product(product_id, batch_id)
);
CREATE INDEX IF NOT EXISTS ix_pi_ingredient ON product_ingredient(ingredient_id);

-- Cross-reference extracts (validation signals, never truth for identity)
CREATE TABLE IF NOT EXISTS nlem_entry (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    medicine        TEXT NOT NULL,
    medicine_norm   TEXT NOT NULL,
    therapeutic_category TEXT,
    care_levels     TEXT,
    nlem_edition    TEXT
);

CREATE TABLE IF NOT EXISTS jan_aushadhi_entry (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    generic_name    TEXT NOT NULL,
    generic_norm    TEXT NOT NULL,
    strength        TEXT,
    pack            TEXT,
    mrp_inr         REAL,
    catalog_version TEXT,
    plausibility_flag TEXT                 -- set by the loader when strength/pack combination is implausible
);
