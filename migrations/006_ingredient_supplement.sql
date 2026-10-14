-- 006: candidate-added ingredient vocabulary and class membership (provenance recorded per row).
-- These rows add NAMES only — no products. They let gazette targets and interaction-seed terms resolve
-- to a canonical ingredient so matching can be evaluated instead of silently skipped.

CREATE TABLE IF NOT EXISTS ingredient_supplement (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    term            TEXT NOT NULL,
    kind            TEXT NOT NULL,          -- ingredient | class
    source          TEXT NOT NULL,
    source_version  TEXT NOT NULL,
    added_on        TEXT NOT NULL,
    reason          TEXT NOT NULL,
    ingredient_id   INTEGER REFERENCES ingredient(ingredient_id)
);

CREATE TABLE IF NOT EXISTS ingredient_class_member (
    id              INTEGER PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES load_batch(batch_id),
    class_norm      TEXT NOT NULL,
    member_name     TEXT NOT NULL,
    member_norm     TEXT NOT NULL,
    source          TEXT NOT NULL,
    requires_signoff INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_class_member ON ingredient_class_member(member_norm);
