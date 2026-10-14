-- 005: audit log for rail runs and Q&A runs so any output is replayable against the exact versions used.

CREATE TABLE IF NOT EXISTS rail_run (
    run_id          TEXT PRIMARY KEY,
    rx_id           TEXT,
    as_of_date      TEXT NOT NULL,
    rule_set_version TEXT NOT NULL,
    data_versions   TEXT NOT NULL,          -- JSON {dataset: batch_id}
    input_json      TEXT NOT NULL,
    output_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_run (
    run_id          TEXT PRIMARY KEY,
    question        TEXT NOT NULL,
    index_version   TEXT NOT NULL,
    prompt_version  TEXT,
    model           TEXT,
    mode            TEXT NOT NULL,
    output_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
