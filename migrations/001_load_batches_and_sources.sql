-- 001: provenance backbone. Every data row in later migrations points at a load_batch.
-- A load_batch records WHICH file (sha256), WHICH declared source version, and WHEN it was loaded.
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id   TEXT PRIMARY KEY,
    applied_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS load_batch (
    batch_id        TEXT PRIMARY KEY,      -- e.g. cdci:2026-06-30:8f7cdf39
    dataset         TEXT NOT NULL,         -- cdci | nlem | jan_aushadhi | gazette | pharmacy_stock | interactions | seed_prescriptions
    source_name     TEXT NOT NULL,         -- declared source label
    source_version  TEXT NOT NULL,         -- declared version/date of the source extract
    file_path       TEXT NOT NULL,
    file_sha256     TEXT NOT NULL,
    row_count       INTEGER NOT NULL,
    loaded_at       TEXT NOT NULL,
    loader_version  TEXT NOT NULL,
    notes           TEXT
);
