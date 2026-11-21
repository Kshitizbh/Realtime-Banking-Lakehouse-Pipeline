"""Create the project folder structure and placeholder files.

Run from the repo root:  python3 setup_project.py

Idempotent: existing files are NEVER overwritten, so it is safe to re-run
after you have started writing code. It only adds what is missing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Folders that only need to exist (a .gitkeep keeps them in Git while empty).
EMPTY_DIRS = [
    "data",
    "notebooks",
    "docker/spark",
    "docker/trino/catalog",
    "docker/airflow",
    "docker/producers",
    "docker/streamlit",
    "dbt/models/staging",
    "dbt/models/intermediate",
    "dbt/models/marts",
    "dbt/tests",
    "dbt/macros",
    "tests/unit",
    "tests/integration",
    "docs/decisions",
]

# Python packages (get an empty __init__.py).
PACKAGES = [
    "src/common",
    "src/common/schemas",
    "src/extract",
    "src/producers",
    "src/batch",
    "src/streaming",
    "src/quality",
    "src/ml",
    "src/dashboard",
    "src/dags",
]

# Placeholder modules: path -> (milestone, purpose, inputs, outputs, TODO steps).
# No logic on purpose: Kriti writes these.
PLACEHOLDERS: dict[str, tuple[str, str, str, str, list[str]]] = {
    # ---------------- M1: ingestion to landing ----------------
    "src/extract/daily_files.py": (
        "M1",
        "File-drop door: land the daily transactions, balances and settlement files (plus the manifest) "
        "in the landing bucket, simulating an SFTP drop from core banking and the clearing house.",
        "LOCAL_DATA_DIR/batch/{transactions,balances,settlements}/*, LOCAL_DATA_DIR/manifests/, a run date.",
        "s3://landing/source=<source_name>/ingestion_date=<YYYY-MM-DD>/<file>, one audit.file_ingestions "
        "row per file and one audit.pipeline_runs row per run (analytics DB).",
        [
            "Read the run date from CLI args (argparse); default = today.",
            "DQ check 1: the expected file for the run date exists.",
            "DQ check 2: SHA-256 and size match manifests/source_manifest.csv (see quality/manifest_check.py).",
            "DQ check 3: skip a file whose hash was already INGESTED (the analytics DB enforces this too).",
            "DQ check 4: header matches the expected columns.",
            "Upload with the shared S3 client; deterministic keys so a re-run never duplicates.",
            "Write audit rows (see quality/audit.py); exit non-zero if any file is REJECTED.",
        ],
    ),
    "src/extract/core_banking_db.py": (
        "M1",
        "Database door: extract from the core_banking Postgres source. Customers and accounts "
        "incrementally (watermark on updated_at); branches, transaction_types, merchant_categories in full.",
        "Postgres core_banking.* (settings.postgres_dsn), last watermark per table.",
        "s3://landing/source=core_<table>/ingestion_date=<date>/<extract_ts>.parquet and updated watermarks.",
        [
            "Store watermarks durably (e.g. a small JSON object in the landing bucket, or a table in analytics).",
            "Incremental: WHERE updated_at > watermark - overlap, ORDER BY updated_at.",
            "Full: reference tables are tiny, so extract them completely every run.",
            "Write Parquet with an explicit schema; record extract_ts.",
            "Advance the watermark only after the upload succeeds (why? think about failures).",
            "Write an audit.pipeline_runs row with rows_out.",
        ],
    ),
    # ---------------- M4: Kafka producers ----------------
    "src/producers/transaction_replay.py": (
        "M4",
        "Kafka producer: replay streaming/transaction_events_*.jsonl into Redpanda in event_ts order.",
        "LOCAL_DATA_DIR/streaming/*.jsonl, speed-up factor, topic name from config.",
        "Messages on banking.transactions.raw (key = account_id), malformed events mixed in.",
        [
            "Use the confluent-kafka Producer; explain your choice of message key.",
            "Support a speed-up factor (e.g. 1 day of events in 10 minutes).",
            "Emit v1 events, then switch to a v2 schema (e.g. device_id, ip_country) mid-run.",
            "Mix in malformed_events_*.jsonl so the DLQ path is exercised.",
            "Flush and report delivery errors; log counts per topic.",
        ],
    ),
    "src/producers/fraud_injector.py": (
        "M4 (optional)",
        "Kafka producer: inject labelled fraud scenarios (the dataset has no fraud labels).",
        "Account and customer IDs, scenario config.",
        "Events on banking.transactions.raw plus a ground-truth file s3://landing/source=fraud_labels/...",
        [
            "Scenarios: velocity burst, failed-attempt burst, dormant/closed/blocked account activity, amount spike.",
            "Write the ground truth separately; never put the label in the event itself.",
        ],
    ),
    # ---------------- M2/M3: batch Spark jobs ----------------
    "src/batch/bronze_files.py": (
        "M2",
        "Spark batch job: landing -> bronze Iceberg tables (append, data unchanged).",
        "s3://landing/source=<source>/ingestion_date=<date>/",
        "Iceberg tables lakehouse.bronze.bronze_<source> with ingestion metadata columns.",
        [
            "Read with an explicit schema (all strings is fine for bronze).",
            "Add source_file, ingested_at, ingestion_date, run_id.",
            "Decide and document the partitioning strategy (brief section 13).",
            "Make re-runs for the same date safe (no duplicate loads).",
        ],
    ),
    "src/batch/silver_transactions.py": (
        "M3",
        "Bronze transactions -> silver: typed, deduplicated, reversals linked.",
        "lakehouse.bronze.bronze_transactions",
        "lakehouse.silver.silver_transactions (MERGE on transaction_id).",
        [
            "Cast types; parse timestamps; validate enums against reference tables.",
            "Remove the 1,200 exact duplicates; decide which record wins and why.",
            "Link reversals to original_transaction_id.",
        ],
    ),
    "src/batch/silver_customers_scd2.py": (
        "M3",
        "Build SCD Type 2 history for customers from core-banking extracts.",
        "lakehouse.bronze.bronze_customers",
        "lakehouse.silver.silver_customers with valid_from, valid_to, is_current.",
        ["Detect changed attributes with a hash; close old rows, insert new ones in one MERGE."],
    ),
    "src/batch/silver_accounts_scd2.py": (
        "M3",
        "Build SCD Type 2 history for accounts (status changes matter for fraud rules).",
        "lakehouse.bronze.bronze_accounts",
        "lakehouse.silver.silver_accounts with valid_from, valid_to, is_current.",
        ["The Postgres extract already has typed dates; the original snapshot file used M/D/YYYY."],
    ),
    "src/batch/silver_balances.py": (
        "M3",
        "Bronze daily balances -> silver, with a balance integrity check.",
        "lakehouse.bronze.bronze_balances",
        "lakehouse.silver.silver_daily_balances",
        ["DQ check 11: opening_balance + credit_total - debit_total = closing_balance; quarantine failures."],
    ),
    "src/batch/silver_settlements.py": (
        "M3",
        "Bronze settlement files -> silver settlements (input to reconciliation in gold).",
        "lakehouse.bronze.bronze_settlements",
        "lakehouse.silver.silver_settlements",
        ["Keep settlement data independent of transactions; the comparison happens in gold."],
    ),
    # ---------------- M5-M7: streaming ----------------
    "src/streaming/bronze_stream.py": (
        "M5",
        "Spark Structured Streaming: banking.transactions.raw -> validation -> bronze Iceberg.",
        "Kafka topic banking.transactions.raw",
        "lakehouse.bronze.bronze_transaction_events (+ Kafka partition/offset/timestamp), valid events "
        "to banking.transactions.validated.",
        [
            "Use an explicit schema (common/schemas); never infer.",
            "Route unparseable/invalid records to the DLQ (see dlq.py).",
            "Checkpoint location in s3://checkpoints/...",
        ],
    ),
    "src/streaming/dlq.py": (
        "M5",
        "Dead-letter handling for malformed events (DQ check 5).",
        "Records that fail parsing or validation.",
        "Topic banking.transactions.dlq and table lakehouse.bronze.bronze_dlq_events with the error reason.",
        ["Keep the raw payload and the reason; never drop data silently."],
    ),
    "src/streaming/silver_stream.py": (
        "M6",
        "Streaming silver: dedupe by event_id with a watermark; handle late events; near-real-time aggregates.",
        "lakehouse.bronze.bronze_transaction_events",
        "lakehouse.silver.silver_transaction_events + near-real-time aggregate tables.",
        ["Choose the watermark delay from the data (events arrive up to 2 days late) and justify it."],
    ),
    "src/streaming/alerts.py": (
        "M7",
        "Rule-based fraud alerts with windowed aggregations.",
        "lakehouse.silver.silver_transaction_events, silver_accounts (stream-static join).",
        "Topic banking.fraud.alerts and the source for gold fact_fraud_alert.",
        ["Velocity, failed bursts, amount vs baseline, dormant/closed/blocked accounts, high-risk MCC."],
    ),
    # ---------------- Quality and audit ----------------
    "src/quality/manifest_check.py": (
        "M1",
        "Verify file integrity against manifests/source_manifest.csv (SHA-256 + size) - DQ check 2.",
        "A file path and the manifest.",
        "MATCH / MISMATCH / NOT_IN_MANIFEST with a reason.",
        ["Note: manifest paths use Windows backslashes; normalise them."],
    ),
    "src/quality/audit.py": (
        "M1",
        "Helpers to write audit rows to the analytics database (settings.analytics_dsn).",
        "Pipeline name, run date, counts, status, error.",
        "Rows in audit.pipeline_runs and audit.file_ingestions.",
        [
            "start_run(...) -> run_id (status RUNNING); finish_run(run_id, status, rows_in, rows_out, error).",
            "record_file(run_id, ...) for each file the file-drop door looks at.",
            "Make sure a crash still marks the run FAILED (try/finally or a context manager).",
        ],
    ),
    "src/quality/checks.py": (
        "M9",
        "Data-quality checks between layers (14 checks, see INSTRUCTION-adapted section 8).",
        "Iceberg tables, Kafka topics, audit tables.",
        "Rows in analytics quality.check_results; a pass/fail gate for the pipeline.",
        ["Start with: unique transaction_id in silver, stream vs batch amount mismatches."],
    ),
    # ---------------- ML (stretch) ----------------
    "src/ml/features.py": ("Stretch", "Build fraud features from silver.", "silver tables", "feature DataFrame", ["Why does ML read silver, not gold?"]),
    "src/ml/train.py": ("Stretch", "Train a scikit-learn fraud model.", "features + fraud labels", "model artefact + metrics", ["Handle class imbalance; time-based split."]),
    "src/ml/predict.py": ("Stretch", "Score transactions and write predictions.", "features + model", "lakehouse.gold.fraud_predictions", ["Idempotent per scoring date."]),
    # ---------------- Dashboard ----------------
    "src/dashboard/app.py": (
        "M10",
        "Streamlit dashboard: Transaction Operations and Pipeline Health (required), plus Branch & Channel, "
        "Settlement Reconciliation and Fraud/Risk pages.",
        "gold tables via Trino; analytics audit/quality tables via Postgres",
        "web app on :8501",
        ["Each page answers specific business questions from the brief."],
    ),
    # ---------------- DAGs (brief: at least 3) ----------------
    "src/dags/ingestion_dag.py": (
        "M11",
        "Daily ingestion: reference + customer/account extracts and file drops to landing (DQ checks 1-4).",
        "logical date",
        "Airflow DAG",
        ["Use the run's logical date, not today."],
    ),
    "src/dags/processing_dag.py": (
        "M11",
        "Spark Bronze + Silver batch jobs after ingestion (DQ checks 6-11).",
        "landing data for the logical date",
        "Airflow DAG",
        ["Wait for ingestion_dag to succeed for the same date."],
    ),
    "src/dags/dbt_quality_dashboard_dag.py": (
        "M11",
        "dbt build for Gold (+ tests), reconciliation, DQ checks 12-14, dashboard refresh.",
        "silver tables",
        "Airflow DAG",
        ["Fail the DAG when dbt tests or the quality gate fail."],
    ),
    "src/dags/maintenance_dag.py": ("M11", "Iceberg maintenance: compaction, snapshot expiry, orphan files.", "all tables", "Airflow DAG", []),
    "src/dags/ml_dag.py": ("Stretch", "Train and score the fraud model.", "silver tables", "Airflow DAG", []),
    # ---------------- Shared (written by Claude in later layers) ----------------
    "src/common/spark_session.py": (
        "M0 (Spark layer)",
        "Spark session factory configured for Iceberg REST + SeaweedFS S3 + Kafka. Added with the Spark profile.",
        "Settings from common.config",
        "A configured SparkSession",
        ["Provided by your supervisor in the next M0 layer."],
    ),
    "src/common/schemas/transaction_event.py": (
        "M4",
        "Explicit schemas for stream events (v1 and v2).",
        "-",
        "StructType definitions",
        ["Derive fields from streaming/transaction_events_*.jsonl; add v2 fields as nullable."],
    ),
}

TEXT_FILES = {
    "docs/architecture.md": "# Architecture\n\nTODO (M12): diagram + data flow, as you would present it in an interview.\n",
    "README.md": "# Real-Time Digital Banking Lakehouse\n\nTODO (M12): project summary, architecture diagram, how to run, results.\n",
}


def placeholder(milestone: str, purpose: str, inputs: str, outputs: str, todos: list[str]) -> str:
    def wrap(text: str, first: str, rest: str) -> str:
        return textwrap.fill(text, width=100, initial_indent=first, subsequent_indent=rest)

    todo_lines = "\n".join(wrap(t, f"    {i}. ", "       ") for i, t in enumerate(todos, 1))
    return (
        '"""' + wrap(purpose, "", "") + "\n\n"
        f"Milestone: {milestone}\n"
        + wrap(inputs, "Inputs:  ", "         ") + "\n"
        + wrap(outputs, "Outputs: ", "         ") + "\n\n"
        + "TODO:\n" + (todo_lines or "    (see milestone brief)") + "\n"
        + '"""\n'
    )


def write_if_missing(path: Path, content: str, created: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    created.append(str(path.relative_to(ROOT)))


def main() -> None:
    created: list[str] = []
    for d in EMPTY_DIRS:
        write_if_missing(ROOT / d / ".gitkeep", "", created)
    for pkg in PACKAGES:
        write_if_missing(ROOT / pkg / "__init__.py", "", created)
    for rel, spec in PLACEHOLDERS.items():
        write_if_missing(ROOT / rel, placeholder(*spec), created)
    for rel, text in TEXT_FILES.items():
        write_if_missing(ROOT / rel, text, created)

    print(f"Created {len(created)} file(s); existing files were left untouched.")
    for c in created:
        print(f"  + {c}")


if __name__ == "__main__":
    main()
