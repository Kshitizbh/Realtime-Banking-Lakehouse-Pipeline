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
    # ---------------- M1: batch extract ----------------
    "src/extract/daily_files.py": (
        "M1",
        "Land the daily batch files (transactions, balances, settlements, snapshots, reference) "
        "into the `landing` bucket, simulating an SFTP drop from core banking.",
        "LOCAL_DATA_DIR/batch/**, LOCAL_DATA_DIR/reference/*, a run date (YYYY-MM-DD).",
        "s3://landing/<source>/ingest_date=<date>/<file> plus a small _SUCCESS/metadata marker.",
        [
            "Read the run date from CLI args (argparse), default = today.",
            "Verify each file's SHA-256 against manifests/source_manifest.csv BEFORE upload (see quality/manifest_check.py).",
            "Upload with the shared S3 client; key layout must be deterministic so re-runs overwrite, not duplicate.",
            "Log counts and skipped/failed files; exit non-zero if any file fails its checksum.",
        ],
    ),
    "src/extract/core_banking_db.py": (
        "M1",
        "Incrementally extract customers and accounts from the Postgres core-banking DB.",
        "Postgres core_banking.customers / core_banking.accounts, last watermark (max updated_at).",
        "s3://landing/core_banking/<table>/extract_ts=<ts>/part.parquet and an updated watermark.",
        [
            "Store the watermark somewhere durable (e.g. a small JSON object in the landing bucket).",
            "Query rows WHERE updated_at > watermark, ordered by updated_at.",
            "Write Parquet with an explicit schema; record extract_ts.",
            "Advance the watermark only after the upload succeeds (why? think about failures).",
        ],
    ),
    "src/extract/fx_rates.py": (
        "M1",
        "Extract official daily NPR exchange rates from the Nepal Rastra Bank forex API.",
        "NRB forex API (verify endpoint and paging in M1), date range.",
        "s3://landing/fx_rates/rate_date=<date>/rates.json",
        [
            "Handle HTTP errors, timeouts and retries with backoff.",
            "Keep the raw JSON exactly as received (bronze principle).",
            "Make it idempotent per date.",
        ],
    ),
    # ---------------- M4: producers ----------------
    "src/producers/transaction_replay.py": (
        "M4",
        "Replay streaming/transaction_events_*.jsonl into Redpanda in event_ts order.",
        "LOCAL_DATA_DIR/streaming/*.jsonl, speed-up factor, topic name.",
        "Messages on topic bank.transactions (key = account_id) and malformed records on the same topic.",
        [
            "Decide the message key and explain why (ordering per account?).",
            "Support a speed-up factor (e.g. 1 day of events in 10 minutes).",
            "Emit v1 events, then switch to a v2 schema (e.g. device_id, ip_country) mid-run.",
            "Mix in malformed_events_*.jsonl so the DLQ path is exercised.",
        ],
    ),
    "src/producers/fraud_injector.py": (
        "M4",
        "Inject labelled fraud scenarios into the replayed stream (the dataset has no fraud labels).",
        "Account and customer IDs, scenario config.",
        "Fraud events on bank.transactions plus a ground-truth file s3://landing/fraud_labels/...",
        [
            "Scenarios: velocity burst, failed-attempt burst, dormant/closed/blocked account activity, amount spike.",
            "Write the ground truth separately; never put the label in the event itself.",
        ],
    ),
    # ---------------- M2/M3: batch Spark jobs ----------------
    "src/batch/bronze_files.py": (
        "M2",
        "Spark batch job: landing files -> bronze Iceberg tables (append, unchanged data).",
        "s3://landing/<source>/ingest_date=<date>/",
        "Iceberg tables lakehouse.bronze.<source> with ingestion metadata columns.",
        [
            "Read with an explicit schema (all strings is fine for bronze).",
            "Add source_file, ingested_at, ingest_date, batch_id.",
            "Make re-runs for the same date safe (no duplicate loads).",
        ],
    ),
    "src/batch/silver_transactions.py": (
        "M3",
        "Bronze transactions -> silver: typed, deduplicated, reversals linked.",
        "lakehouse.bronze.transactions",
        "lakehouse.silver.transactions (MERGE on transaction_id).",
        [
            "Cast types; parse timestamps; validate enums against reference tables.",
            "Remove the 1,200 exact duplicates; decide which record wins and why.",
            "Link reversals to original_transaction_id.",
        ],
    ),
    "src/batch/silver_customers_scd2.py": (
        "M3",
        "Build SCD Type 2 history for customers from core-banking extracts.",
        "lakehouse.bronze.core_banking_customers",
        "lakehouse.silver.customers with valid_from, valid_to, is_current.",
        ["Detect changed attributes with a hash; close old rows, insert new ones in one MERGE."],
    ),
    "src/batch/silver_accounts_scd2.py": (
        "M3",
        "Build SCD Type 2 history for accounts (status changes matter for fraud rules).",
        "lakehouse.bronze.core_banking_accounts",
        "lakehouse.silver.accounts with valid_from, valid_to, is_current.",
        ["Parse the M/D/YYYY dates from the account snapshot correctly."],
    ),
    "src/batch/silver_balances.py": (
        "M3",
        "Bronze daily balances -> silver, with a balance integrity check.",
        "lakehouse.bronze.balances",
        "lakehouse.silver.daily_balances",
        ["Check opening_balance + credit_total - debit_total = closing_balance; quarantine failures."],
    ),
    # ---------------- M5-M7: streaming ----------------
    "src/streaming/bronze_stream.py": (
        "M5",
        "Spark Structured Streaming: Redpanda -> bronze Iceberg (append).",
        "Kafka topic bank.transactions",
        "lakehouse.bronze.transaction_events (+ Kafka partition/offset/timestamp metadata).",
        [
            "Use an explicit schema (common/schemas); never infer.",
            "Route unparseable records to the DLQ (see dlq.py).",
            "Checkpoint location in s3://checkpoints/...",
        ],
    ),
    "src/streaming/dlq.py": (
        "M5",
        "Dead-letter handling for malformed events.",
        "Records that fail parsing or validation.",
        "Topic bank.transactions.dlq and table lakehouse.bronze.dlq_events with the error reason.",
        ["Keep the raw payload and the reason; never drop data silently."],
    ),
    "src/streaming/silver_stream.py": (
        "M6",
        "Streaming silver: dedupe by event_id with a watermark; handle late events.",
        "lakehouse.bronze.transaction_events",
        "lakehouse.silver.transaction_events",
        ["Choose the watermark delay from the data (events arrive up to 2 days late) and justify it."],
    ),
    "src/streaming/alerts.py": (
        "M7",
        "Real-time fraud rules with windowed aggregations.",
        "lakehouse.silver.transaction_events, silver.accounts (stream-static join).",
        "lakehouse.gold.fraud_alerts (and optionally an alerts topic).",
        ["Velocity, failed bursts, amount vs baseline, dormant/closed/blocked accounts."],
    ),
    # ---------------- Quality ----------------
    "src/quality/manifest_check.py": (
        "M1",
        "Verify file integrity against manifests/source_manifest.csv (SHA-256 + size).",
        "A file path and the manifest.",
        "Pass/fail result with reason.",
        ["Note: manifest paths use Windows backslashes; normalise them."],
    ),
    "src/quality/checks.py": (
        "M3/M12",
        "Data quality checks between layers (row counts, nulls, uniqueness, reconciliation).",
        "Iceberg tables.",
        "A results table lakehouse.quality.check_results.",
        ["Start with: unique transaction_id in silver, stream vs batch amount mismatches."],
    ),
    # ---------------- ML ----------------
    "src/ml/features.py": ("M9", "Build fraud features from silver.", "silver tables", "feature DataFrame", ["Why does ML read silver, not gold?"]),
    "src/ml/train.py": ("M9", "Train a scikit-learn fraud model.", "features + fraud labels", "model artefact + metrics", ["Handle class imbalance; time-based split."]),
    "src/ml/predict.py": ("M9", "Score transactions and write predictions.", "features + model", "lakehouse.gold.fraud_predictions", ["Idempotent per scoring date."]),
    # ---------------- Dashboard ----------------
    "src/dashboard/app.py": ("M10", "Streamlit dashboard on gold via Trino.", "gold tables", "web app on :8501", ["KPIs, alerts, reconciliation, predictions."]),
    # ---------------- DAGs ----------------
    "src/dags/batch_daily_dag.py": ("M11", "Daily batch: extract -> bronze -> silver -> quality.", "run date", "Airflow DAG", ["Use the run's logical date, not today."]),
    "src/dags/dbt_dag.py": ("M11", "Run dbt build for gold.", "silver tables", "Airflow DAG", ["Fail the DAG when dbt tests fail."]),
    "src/dags/ml_dag.py": ("M11", "Train and score the fraud model.", "silver tables", "Airflow DAG", []),
    "src/dags/maintenance_dag.py": ("M11", "Iceberg maintenance: compaction, snapshot expiry, orphan files.", "all tables", "Airflow DAG", []),
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
