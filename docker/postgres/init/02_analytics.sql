-- Platform-side database: audit logs, data-quality results, dashboard serving tables.
-- Kept separate from core_banking because in a real bank the source system and the
-- data platform are different systems owned by different teams.
-- Runs ONCE, after 01_core_banking.sql, on an empty postgres_data volume.

CREATE DATABASE analytics;
\connect analytics

CREATE SCHEMA audit;     -- what ran, when, on which files, with what result
CREATE SCHEMA quality;   -- data-quality check results (the quality gate reads these)
CREATE SCHEMA serving;   -- small tables for the dashboard (filled from M10)

-- ----------------------------------------------------------------------
-- One row per pipeline/job run. Every M1+ job writes a RUNNING row at start
-- and updates it to SUCCESS/FAILED at the end.
-- ----------------------------------------------------------------------
CREATE TABLE audit.pipeline_runs (
    run_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name   TEXT        NOT NULL,                 -- e.g. 'ingest_transactions'
    run_date        DATE        NOT NULL,                 -- business date being processed
    status          TEXT        NOT NULL DEFAULT 'RUNNING'
                    CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    rows_in         BIGINT,
    rows_out        BIGINT,
    error_message   TEXT,
    triggered_by    TEXT        NOT NULL DEFAULT 'manual', -- 'manual' or 'airflow'
    airflow_dag_id  TEXT,
    airflow_run_id  TEXT
);
CREATE INDEX idx_pipeline_runs_name_date ON audit.pipeline_runs (pipeline_name, run_date);

-- ----------------------------------------------------------------------
-- One row per file the file-drop door looked at (DQ checks 1-4 live here).
-- ----------------------------------------------------------------------
CREATE TABLE audit.file_ingestions (
    file_ingestion_id BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id            UUID        REFERENCES audit.pipeline_runs (run_id),
    source_name       TEXT        NOT NULL,               -- e.g. 'transactions'
    file_name         TEXT        NOT NULL,
    landing_key       TEXT,                               -- s3 key, NULL if rejected
    ingestion_date    DATE        NOT NULL,
    file_sha256       CHAR(64)    NOT NULL,
    file_size_bytes   BIGINT      NOT NULL,
    row_count         BIGINT,
    manifest_status   TEXT        NOT NULL
                      CHECK (manifest_status IN ('MATCH', 'MISMATCH', 'NOT_IN_MANIFEST')),
    status            TEXT        NOT NULL
                      CHECK (status IN ('INGESTED', 'SKIPPED_DUPLICATE', 'REJECTED')),
    reason            TEXT,
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- The same file content can only be INGESTED once per source (DQ check 3).
CREATE UNIQUE INDEX uq_file_ingested_once
    ON audit.file_ingestions (source_name, file_sha256)
    WHERE status = 'INGESTED';

-- ----------------------------------------------------------------------
-- One row per data-quality check execution (all 14 checks write here).
-- ----------------------------------------------------------------------
CREATE TABLE quality.check_results (
    check_result_id BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          UUID        REFERENCES audit.pipeline_runs (run_id),
    check_name      TEXT        NOT NULL,                 -- e.g. 'silver_transactions_unique_id'
    check_category  TEXT        NOT NULL
                    CHECK (check_category IN ('SOURCE', 'STREAMING', 'TRANSFORMATION', 'BUSINESS', 'FRESHNESS')),
    layer           TEXT        NOT NULL
                    CHECK (layer IN ('landing', 'kafka', 'bronze', 'silver', 'gold')),
    target          TEXT        NOT NULL,                 -- table, topic or file checked
    status          TEXT        NOT NULL CHECK (status IN ('PASS', 'WARN', 'FAIL')),
    observed_value  NUMERIC,
    threshold       TEXT,
    failed_rows     BIGINT,
    details         JSONB,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_check_results_name_time ON quality.check_results (check_name, checked_at DESC);
