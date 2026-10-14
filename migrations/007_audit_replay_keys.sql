-- 007: audit rows get their own id; run_id becomes a deterministic REPLAY KEY (same input + date + rule set + data
-- batches => same run_id), so checked-in outputs are stable and any output can be re-derived. Earlier audit tables
-- are kept under *_v1 (never edited, never dropped).

ALTER TABLE rail_run RENAME TO rail_run_v1;
ALTER TABLE qa_run RENAME TO qa_run_v1;

CREATE TABLE IF NOT EXISTS rail_run (
    audit_id        TEXT PRIMARY KEY,       -- uuid per execution
    run_id          TEXT NOT NULL,          -- replay key
    rx_id           TEXT,
    as_of_date      TEXT NOT NULL,
    rule_set_version TEXT NOT NULL,
    data_versions   TEXT NOT NULL,
    input_json      TEXT NOT NULL,
    output_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_rail_run_key ON rail_run(run_id);

CREATE TABLE IF NOT EXISTS qa_run (
    audit_id        TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,          -- replay key
    question        TEXT NOT NULL,
    as_of           TEXT,
    index_version   TEXT NOT NULL,
    prompt_version  TEXT,
    model           TEXT,
    mode            TEXT NOT NULL,
    output_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_qa_run_key ON qa_run(run_id);
