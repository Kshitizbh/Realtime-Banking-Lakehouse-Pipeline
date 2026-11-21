#!/usr/bin/env python3
"""Create the folder structure and placeholder files for Realtime-Banking-Lakehouse-Pipeline.

Run it once from the repo root (it is safe to run again):

    python3 setup_project.py --dry-run   # preview, writes nothing
    python3 setup_project.py             # create folders and files

Rules this script follows:
- Never overwrites an existing file (existing files are reported as "skip").
- Never touches data/ (your bank dataset stays exactly as it is).
- Appends project-specific lines to .gitignore only if they are missing.
- Uses the Python standard library only, so it runs before any venv exists.

Infrastructure files (docker-compose.yml, Dockerfiles, Makefile, pyproject.toml,
dbt_project.yml, shared utilities in src/common) are NOT created here; they come in
the next M0 step, after the version check.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("setup_project")

JOURNAL_DAY0_DATE = "2026-11-21"


# --------------------------------------------------------------------------------------
# Placeholder specs for Python modules
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Placeholder:
    """Describes one placeholder Python module (docstring only, no logic)."""

    milestone: str
    owner: str  # "Kriti" writes the logic; "Claude" writes it as shared infrastructure
    purpose: str
    inputs: str
    outputs: str
    todo: list[str] = field(default_factory=list)


def render_placeholder(path: str, spec: Placeholder) -> str:
    """Return the text of a placeholder module: a docstring and nothing else."""
    todo_lines = "\n".join(f"    {i}. {step}" for i, step in enumerate(spec.todo, start=1))
    return (
        f'"""{Path(path).stem.replace("_", " ").capitalize()}.\n'
        f"\n"
        f"Milestone: {spec.milestone}    Written by: {spec.owner}\n"
        f"\n"
        f"Purpose:\n    {spec.purpose}\n"
        f"\n"
        f"Inputs:\n    {spec.inputs}\n"
        f"\n"
        f"Outputs:\n    {spec.outputs}\n"
        f"\n"
        f"TODO:\n{todo_lines if todo_lines else '    (none yet)'}\n"
        f'"""\n'
    )


PLACEHOLDERS: dict[str, Placeholder] = {
    # ---------------- shared utilities (Claude, next M0 step) ----------------
    "src/common/config.py": Placeholder(
        "M0", "Claude",
        "Load every setting from environment variables / .env into one typed settings object.",
        ".env (local) or container environment.",
        "A settings object imported by every job; no hard-coded hosts, paths or credentials.",
    ),
    "src/common/logging_setup.py": Placeholder(
        "M0", "Claude",
        "One logging format for every job (named logging_setup, not logging, to avoid "
        "shadowing the standard library).",
        "LOG_LEVEL from config.",
        "A configured logger via get_logger(__name__).",
    ),
    "src/common/spark_session.py": Placeholder(
        "M0", "Claude",
        "Spark session factory configured for Iceberg (REST catalog), SeaweedFS (S3, "
        "path-style) and Kafka.",
        "Settings from config.",
        "A SparkSession ready to read/write Iceberg tables and Kafka topics.",
    ),
    "src/common/s3_client.py": Placeholder(
        "M0", "Claude",
        "S3 client for SeaweedFS (path-style addressing).",
        "Settings from config.",
        "A boto3 client used to upload/list landing files.",
    ),
    "src/common/postgres.py": Placeholder(
        "M0", "Claude",
        "Connection helpers for the two Postgres databases: core_banking and analytics.",
        "Settings from config.",
        "Connections/engines for each database.",
    ),
    "src/common/kafka_client.py": Placeholder(
        "M4", "Claude",
        "Producer factory for Redpanda (Kafka API, confluent-kafka client).",
        "Settings from config.",
        "A configured Producer with delivery callbacks logged.",
    ),
    "src/common/audit.py": Placeholder(
        "M1", "Kriti",
        "Record every pipeline run and every ingested file in the analytics database.",
        "Run metadata (job name, start/end, status, row counts), file metadata (path, hash, size).",
        "Rows in analytics: audit.pipeline_runs and audit.file_ingestions.",
        [
            "Decide which columns each audit table needs (look at the Pipeline Health page needs).",
            "Write a function that starts a run and one that finishes it with a status.",
            "Make sure a failed job still records a FAILED run.",
        ],
    ),
    # ---------------- schemas ----------------
    "src/common/schemas/batch_schemas.py": Placeholder(
        "M2", "Kriti",
        "Explicit Spark schemas for every batch file and extract (never infer).",
        "Column lists from data/batch, data/reference and the core_banking extracts.",
        "StructType definitions imported by the Bronze jobs.",
        [
            "Profile each file's header and decide a type per column.",
            "Keep dates as strings in Bronze if their formats differ (account snapshot uses M/D/YYYY).",
        ],
    ),
    "src/common/schemas/event_schema_v1.py": Placeholder(
        "M4", "Kriti",
        "Schema of the v1 transaction event (as found in data/streaming).",
        "A sample of transaction events JSONL.",
        "A schema used by the producer (validation) and Spark streaming (parsing).",
    ),
    "src/common/schemas/event_schema_v2.py": Placeholder(
        "M4", "Kriti",
        "Schema of the v2 event (adds fields such as device_id, ip_country, card_present).",
        "The v1 schema.",
        "A backward-compatible v2 schema for the schema-evolution demo.",
    ),
    # ---------------- ingestion (batch door) ----------------
    "src/ingestion/file_drop.py": Placeholder(
        "M1", "Kriti",
        "Ingest the daily file drops (transactions, balances, settlements) into the landing bucket.",
        "data/batch/{transactions,balances,settlements}/*.csv and data/manifest/source_manifest.csv.",
        "s3://landing/source=<name>/ingestion_date=YYYY-MM-DD/<file> plus audit rows.",
        [
            "For a run date, find the expected files.",
            "Run source checks 1-4 (quality/source_checks.py) before uploading.",
            "Upload only files that pass and were not ingested before (same hash = skip).",
            "Record each file in the audit log.",
        ],
    ),
    "src/ingestion/core_banking_extract.py": Placeholder(
        "M1", "Kriti",
        "Extract from the core_banking Postgres database like a real OLTP source.",
        "core_banking tables: customers, accounts (incremental on updated_at), branches, "
        "transaction_types, merchant_categories (full).",
        "Extract files in s3://landing/source=core_<table>/ or ref_<table>/ plus audit rows.",
        [
            "Read the last watermark for each incremental table.",
            "Extract only rows changed since the watermark; save the new watermark only after a successful upload.",
            "Do full extracts for the reference tables.",
        ],
    ),
    "src/ingestion/watermark.py": Placeholder(
        "M1", "Kriti",
        "Store and read the extraction watermark per source table.",
        "Table name.",
        "Last successful updated_at value (stored in the analytics database).",
    ),
    # ---------------- source-system simulation ----------------
    "src/source_system/core_banking_changes.py": Placeholder(
        "M3", "Kriti",
        "Simulate changes in the core banking system so SCD2 has history to track.",
        "core_banking.customers and core_banking.accounts.",
        "Updated rows (the trigger moves updated_at), e.g. address change, account status change.",
        [
            "Pick a few realistic change types and apply them in a transaction.",
            "Log which IDs changed so you can verify them in silver later.",
        ],
    ),
    # ---------------- producers (streaming door) ----------------
    "src/producers/transaction_replay.py": Placeholder(
        "M4", "Kriti",
        "Replay transaction events to Redpanda as if they were live.",
        "data/streaming/*.jsonl (transaction events + malformed events).",
        "Messages on banking.transactions.raw, key = account_id.",
        [
            "Read events and send them in event_ts order with a speed-up factor from config.",
            "Mix in the malformed events.",
            "Switch from v1 to v2 events at a configurable point.",
            "Flush on exit and log delivery failures.",
        ],
    ),
    "src/producers/fraud_injector.py": Placeholder(
        "M4 (optional)", "Kriti",
        "Send labelled fraud scenarios onto the raw topic and write a ground-truth file.",
        "Scenario definitions (e.g. many failed attempts in minutes).",
        "Messages on banking.transactions.raw and a ground-truth CSV in data/.",
    ),
    # ---------------- batch: bronze ----------------
    "src/batch/bronze/bronze_files.py": Placeholder(
        "M2", "Kriti",
        "Load landed daily files into Bronze Iceberg tables, unchanged, with ingestion metadata.",
        "s3://landing/source=transactions|balances|settlements/...",
        "bronze_transactions, bronze_balances, bronze_settlements.",
        [
            "Read with explicit schemas.",
            "Add ingestion metadata (source file, ingested_at, batch id).",
            "Make re-runs idempotent (the same file must not be appended twice).",
        ],
    ),
    "src/batch/bronze/bronze_core_banking.py": Placeholder(
        "M2", "Kriti",
        "Load core_banking extracts into Bronze Iceberg tables.",
        "s3://landing/source=core_*|ref_*/...",
        "bronze_customers, bronze_accounts, bronze_branches, bronze_transaction_types, "
        "bronze_merchant_categories.",
    ),
    # ---------------- batch: silver ----------------
    "src/batch/silver/silver_transactions.py": Placeholder(
        "M3", "Kriti",
        "Clean, type and deduplicate transactions; link reversals to originals.",
        "bronze_transactions.",
        "silver_transactions (expect 600,000 unique transaction_id).",
    ),
    "src/batch/silver/silver_customers.py": Placeholder(
        "M3", "Kriti",
        "Build customer history as SCD2.",
        "bronze_customers.",
        "silver_customers with valid_from, valid_to, is_current.",
    ),
    "src/batch/silver/silver_accounts.py": Placeholder(
        "M3", "Kriti",
        "Build account history as SCD2 (normalise M/D/YYYY dates).",
        "bronze_accounts.",
        "silver_accounts with valid_from, valid_to, is_current.",
    ),
    "src/batch/silver/silver_daily_balances.py": Placeholder(
        "M3", "Kriti",
        "Typed, validated daily balances per account.",
        "bronze_balances.",
        "silver_daily_balances (one row per account per day).",
    ),
    "src/batch/silver/silver_settlements.py": Placeholder(
        "M3", "Kriti",
        "Typed, validated settlement totals from the clearing house files.",
        "bronze_settlements.",
        "silver_settlements.",
    ),
    # ---------------- streaming ----------------
    "src/streaming/validate_events.py": Placeholder(
        "M5", "Kriti",
        "Streaming Bronze: read the raw topic, validate, route good and bad events.",
        "banking.transactions.raw.",
        "banking.transactions.validated, banking.transactions.dlq, bronze_transaction_events, "
        "bronze_dlq_events (checkpointed).",
    ),
    "src/streaming/silver_events.py": Placeholder(
        "M6", "Kriti",
        "Streaming Silver: watermark, deduplicate on event_id, handle late events.",
        "bronze_transaction_events or banking.transactions.validated.",
        "silver_transaction_events.",
    ),
    "src/streaming/aggregates.py": Placeholder(
        "M6", "Kriti",
        "Near-real-time windowed aggregates for the Operations page.",
        "Validated events.",
        "Aggregate Iceberg table(s) in gold.",
    ),
    "src/streaming/fraud_rules.py": Placeholder(
        "M7", "Kriti",
        "Rule-based fraud alerts over event windows.",
        "Validated events.",
        "banking.fraud.alerts and fact_fraud_alert rows.",
    ),
    # ---------------- quality ----------------
    "src/quality/results.py": Placeholder(
        "M9", "Kriti",
        "Write every check result in one consistent shape.",
        "Check name, category, table, status, observed value, threshold, run id.",
        "Rows in analytics: quality.check_results.",
    ),
    "src/quality/source_checks.py": Placeholder(
        "M1 / M9", "Kriti",
        "Source checks 1-4: file exists, SHA-256 + size match manifest, duplicate file, header matches.",
        "A file path and data/manifest/source_manifest.csv.",
        "Pass/fail results (the account snapshot is expected to fail its hash check).",
    ),
    "src/quality/streaming_checks.py": Placeholder(
        "M5 / M9", "Kriti",
        "Check 5: DLQ count per day; part of check 14: consumer lag on the raw topic.",
        "DLQ topic/table, consumer group offsets.",
        "Check results.",
    ),
    "src/quality/transformation_checks.py": Placeholder(
        "M3 / M9", "Kriti",
        "Checks 6-9: unique transaction_id, non-null keys, allowed status, account FK.",
        "Silver tables.",
        "Check results.",
    ),
    "src/quality/business_checks.py": Placeholder(
        "M8 / M9", "Kriti",
        "Checks 10-13: reversals, balance equation, settlement variance, stream vs batch amounts.",
        "Silver/Gold tables.",
        "Check results.",
    ),
    "src/quality/freshness_checks.py": Placeholder(
        "M9", "Kriti",
        "Check 14: tables updated within SLA.",
        "Iceberg snapshot timestamps / audit runs.",
        "Check results.",
    ),
    "src/quality/run_checks.py": Placeholder(
        "M9", "Kriti",
        "Command-line entry point: run a group of checks and act as a quality gate.",
        "Check group name (source, transformation, business, freshness).",
        "Exit code non-zero when a critical check fails (so Airflow stops downstream tasks).",
    ),
    # ---------------- maintenance ----------------
    "src/maintenance/iceberg_maintenance.py": Placeholder(
        "M11", "Kriti",
        "Iceberg housekeeping: compaction, snapshot expiry, orphan-file cleanup.",
        "List of tables and retention settings from config.",
        "Smaller, fewer files and bounded metadata.",
    ),
    # ---------------- dashboard ----------------
    "src/dashboard/app.py": Placeholder(
        "M10", "Kriti",
        "Streamlit entry page: what the platform is and links to each page.",
        "Gold tables via Trino; audit/quality via Postgres analytics.",
        "The Streamlit app (pages in src/dashboard/pages/).",
    ),
    "src/dashboard/queries.py": Placeholder(
        "M10", "Kriti",
        "Shared query functions (with caching) used by the pages.",
        "Trino and Postgres connections.",
        "DataFrames for each page.",
    ),
    "src/dashboard/pages/1_Transaction_Operations.py": Placeholder(
        "M10 (required)", "Kriti",
        "Operations: count, amount, failure rate, channel mix, balance movement.",
        "fact_transaction, fact_daily_account_balance, dims.", "Streamlit page.",
    ),
    "src/dashboard/pages/2_Pipeline_Health.py": Placeholder(
        "M10 (required)", "Kriti",
        "Data team: failed runs, stale tables, DLQ count, quality failures, consumer lag.",
        "analytics audit and quality tables.", "Streamlit page.",
    ),
    "src/dashboard/pages/3_Branch_Channel.py": Placeholder(
        "M10 (target)", "Kriti",
        "Management: volume and value by branch, region, channel.",
        "fact_transaction, dim_branch, dim_channel.", "Streamlit page.",
    ),
    "src/dashboard/pages/4_Settlement_Reconciliation.py": Placeholder(
        "M10 (target)", "Kriti",
        "Finance: stream vs batch vs settlement totals, variance, unmatched.",
        "fact_settlement_reconciliation.", "Streamlit page.",
    ),
    "src/dashboard/pages/5_Fraud_Risk.py": Placeholder(
        "M10 (target)", "Kriti",
        "Risk: alerts by rule, high-risk merchant categories, high-value activity.",
        "fact_fraud_alert and dims.", "Streamlit page.",
    ),
    # ---------------- Airflow DAGs ----------------
    "src/dags/ingestion_dag.py": Placeholder(
        "M11", "Kriti",
        "Daily: file drops + core_banking extracts to landing, source checks 1-4.",
        "Run date.", "Landing files, audit rows, check results.",
    ),
    "src/dags/processing_dag.py": Placeholder(
        "M11", "Kriti",
        "Daily after ingestion: Spark Bronze and Silver jobs, checks 6-11.",
        "Landing files.", "Bronze and Silver tables, check results.",
    ),
    "src/dags/dbt_quality_dashboard_dag.py": Placeholder(
        "M11", "Kriti",
        "dbt build (Gold + tests), reconciliation, checks 12-14, streaming health and lag.",
        "Silver tables.", "Gold tables, check results.",
    ),
    "src/dags/maintenance_dag.py": Placeholder(
        "M11", "Kriti",
        "Weekly Iceberg maintenance.",
        "Table list.", "Compacted tables, expired snapshots.",
    ),
}

# Packages that need an __init__.py (one-line docstring only).
PACKAGES: list[str] = [
    "src/common",
    "src/common/schemas",
    "src/ingestion",
    "src/source_system",
    "src/producers",
    "src/batch",
    "src/batch/bronze",
    "src/batch/silver",
    "src/streaming",
    "src/quality",
    "src/maintenance",
    "src/dashboard",
]

# Folders that start empty; a .gitkeep lets Git track them.
EMPTY_DIRS: list[str] = [
    "docker/airflow",
    "docker/spark",
    "docker/producers",
    "docker/streamlit",
    "docker/trino/catalog",
    "docker/postgres/init",
    "docker/seaweedfs",
    "scripts",
    "dbt/models/staging",
    "dbt/models/intermediate",
    "dbt/models/marts",
    "dbt/tests",
    "dbt/macros",
    "dbt/snapshots",
    "dbt/seeds",
    "tests/unit",
    "tests/integration",
    "tests/smoke",
    "docs/images",
]


# --------------------------------------------------------------------------------------
# Markdown and config files
# --------------------------------------------------------------------------------------
JOURNAL_TEMPLATE = """\
# Journal — YYYY-MM-DD

**Milestone:** M#   **Hours today:** _

## Goal for this session
-

## What I did
-

## What went wrong (and how I fixed it)
- Link any new troubleshooting entry: [NNNN](../troubleshooting/NNNN-slug.md)

## What I learned
-

## Evidence
(commands + output, row counts, query results, screenshots in docs/images/)

## Next step
-
"""

JOURNAL_DAY0_TEXT = f"""\
# Journal — {JOURNAL_DAY0_DATE} (Day 0: restart)

**Milestone:** M0   **Hours today:** _

## Goal for this session
- Restart the project in a clean repo and agree the structure.

## What I did
- (write in your own words: new repo, .gitignore for data, decisions confirmed, scaffold created)

## What went wrong (and how I fixed it)
- `tree` would not install → see [0001](../troubleshooting/0001-apt-unable-to-locate-package.md)

## What I learned
- Why I restarted, and what I will do differently this time:
- Difference between .gitignore and removing a file from Git history:

## Evidence
- `git log --oneline` after the scaffold commit
- `tree -L 2 -I data`

## Next step
- M0 core profile: SeaweedFS, Iceberg REST catalog, Postgres (core_banking + analytics).
"""

TROUBLESHOOTING_TEMPLATE = """\
# NNNN — Short title of the problem

**Component:** Docker/WSL | SeaweedFS | Iceberg REST | Postgres | Spark | Redpanda | Trino | dbt | Airflow | Streamlit | Python/uv | Git
**Date:** YYYY-MM-DD   **Journal:** [YYYY-MM-DD](../journal/YYYY-MM-DD.md)   **Status:** Solved | Workaround | Open

## Symptom
What I was trying to do and what happened.

## Exact error
```
paste the exact error text
```

## Cause
Why it happened (the root cause, not just the fix).

## Fix
Commands or changes that solved it.

## How I verified it
The command/output that proves it is fixed.

## Prevent it next time
-
"""

TROUBLESHOOTING_INDEX = """\
# Troubleshooting index

One file per issue: `NNNN-short-slug.md` (copy `_template.md`). Add a row here every time.

| # | Component | Problem | Status |
|---|---|---|---|
| [0001](0001-apt-unable-to-locate-package.md) | Docker/WSL | `apt install tree`: Unable to locate package | Solved |

## By component
- **Docker / WSL:** 0001
- **SeaweedFS:**
- **Iceberg REST catalog:**
- **Postgres:**
- **Spark:**
- **Redpanda:**
- **Trino:**
- **dbt:**
- **Airflow:**
- **Streamlit:**
- **Python / uv:**
- **Git:**
"""

TROUBLESHOOTING_0001 = """\
# 0001 — `apt install tree`: Unable to locate package

**Component:** Docker/WSL   **Date:** 2026-11-21   **Journal:** [2026-11-21](../journal/2026-11-21.md)   **Status:** Solved

## Symptom


## Exact error
```

```

## Cause


## Fix


## How I verified it


## Prevent it next time
-
"""

DECISION_TEMPLATE = """\
# NNNN — Decision title

**Status:** Draft | Accepted | Superseded by NNNN   **Date:** YYYY-MM-DD   **Milestone:** M#

## Context
What problem or constraint forced a decision?

## Options considered
| Option | Pros | Cons |
|---|---|---|
| | | |

## Decision
What I chose, in one or two sentences.

## Consequences
What this makes easier, what it makes harder, and how I would undo it.
"""

DECISIONS_INDEX = """\
# Decision records

One file per decision: `NNNN-short-slug.md` (copy `_template.md`).

| # | Decision | Status | Milestone |
|---|---|---|---|
| [0001](0001-seaweedfs-object-storage.md) | SeaweedFS instead of MinIO | Draft | M0 |
| [0002](0002-redpanda-instead-of-kafka.md) | Redpanda instead of Apache Kafka | Draft | M0 |
| [0003](0003-uv-python-environment.md) | uv-managed Python 3.12 environment | Draft | M0 |
"""


def decision_stub(number: str, title: str) -> str:
    """Return a decision record with the title filled in and empty sections."""
    return DECISION_TEMPLATE.replace("NNNN — Decision title", f"{number} — {title}").replace(
        "**Milestone:** M#", "**Milestone:** M0"
    )


DOC_STUBS: dict[str, str] = {
    "docs/architecture.md": (
        "# Architecture\n\n"
        "## Overview (one paragraph a recruiter can read)\n\n"
        "## Batch path\n\n## Streaming path\n\n## Storage: buckets, Iceberg namespaces, catalog\n\n"
        "## Kafka topics\n\n## Postgres: core_banking and analytics\n\n"
        "## Orchestration\n\n## Diagram\n(add docs/images/architecture.png at M12)\n"
    ),
    "docs/dataset.md": (
        "# Dataset\n\n"
        "Local only, in git-ignored `data/` (156 files). Never committed.\n\n"
        "```\n"
        "data/\n"
        "├── batch/\n"
        "│   ├── accounts/       account_snapshot_2026-01-01.csv\n"
        "│   ├── balances/       account_balances_2026-01-DD.csv   (30 days)\n"
        "│   ├── customers/      customer_snapshot_2026-01-01.csv\n"
        "│   ├── settlements/    settlement_2026-01-DD.csv         (30 days)\n"
        "│   └── transactions/   transactions_2026-01-DD.csv       (30 days)\n"
        "├── manifest/           source_manifest.csv\n"
        "├── reference/          branches.csv, merchant_categories.csv, transaction_types.csv\n"
        "└── streaming/          *_2026-01-DD.jsonl (transaction events + malformed events)\n"
        "```\n\n"
        "## Which door each file uses\n\n## Profile (row counts, columns, types)\n\n"
        "## Known data-quality traps\n"
    ),
    "docs/data-dictionary.md": (
        "# Data dictionary\n\nOne section per table (Bronze, Silver, Gold): grain, columns, types, "
        "meaning, source.\n"
    ),
    "docs/runbook.md": (
        "# Runbook\n\n## Start and stop the stack\n\n## Rerun a failed day\n\n"
        "## Recover after Redpanda / Spark / Airflow failure\n\n## Reset local state (careful)\n"
    ),
    "notebooks/README.md": (
        "# Notebooks\n\nExploration only. Pipeline code never lives here; anything reusable moves "
        "to src/.\n"
    ),
}

ENV_EXAMPLE = """\
# Copy to .env (git-ignored) and change every change_me value:  cp .env.example .env
# Hosts below are for running Python from WSL. Inside containers, compose overrides them
# with service names (seaweedfs, iceberg-rest, postgres, redpanda, trino).
# Ports are confirmed in the M0 infrastructure step.

# ---------- Local dataset (git-ignored) ----------
DATA_DIR=./data
DATA_BATCH_DIR=./data/batch
DATA_REFERENCE_DIR=./data/reference
DATA_MANIFEST_FILE=./data/manifest/source_manifest.csv
DATA_STREAMING_DIR=./data/streaming

# ---------- Object storage: SeaweedFS (S3 API, path-style) ----------
S3_ENDPOINT=http://localhost:8333
S3_ACCESS_KEY=change_me
S3_SECRET_KEY=change_me
S3_REGION=us-east-1
S3_PATH_STYLE=true
BUCKET_LANDING=landing
BUCKET_WAREHOUSE=warehouse
BUCKET_CHECKPOINTS=checkpoints

# ---------- Iceberg REST catalog ----------
ICEBERG_REST_URI=http://localhost:8181
ICEBERG_CATALOG_NAME=lakehouse
ICEBERG_WAREHOUSE=s3://warehouse/

# ---------- Postgres: one container, two databases ----------
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SUPERUSER=postgres
POSTGRES_SUPERUSER_PASSWORD=change_me
CORE_BANKING_DB=core_banking
CORE_BANKING_USER=core_banking_app
CORE_BANKING_PASSWORD=change_me
ANALYTICS_DB=analytics
ANALYTICS_USER=analytics_app
ANALYTICS_PASSWORD=change_me

# ---------- Redpanda (Kafka API) ----------
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
TOPIC_TRANSACTIONS_RAW=banking.transactions.raw
TOPIC_TRANSACTIONS_VALIDATED=banking.transactions.validated
TOPIC_TRANSACTIONS_DLQ=banking.transactions.dlq
TOPIC_FRAUD_ALERTS=banking.fraud.alerts
REPLAY_SPEEDUP=60

# ---------- Trino ----------
TRINO_HOST=localhost
TRINO_PORT=8080
TRINO_USER=lakehouse
TRINO_CATALOG=iceberg

# ---------- General ----------
LOG_LEVEL=INFO
"""

GITIGNORE_ADDITIONS: list[str] = [
    "# --- Project-specific (added by setup_project.py) ---",
    ".env",
    ".venv/",
    "spark-warehouse/",
    "metastore_db/",
    "derby.log",
    "dbt/target/",
    "dbt/dbt_packages/",
    "dbt/logs/",
    "logs/",
    "*.log",
    ".ipynb_checkpoints/",
]


# --------------------------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------------------------
class Scaffolder:
    """Create folders and files under a root, never overwriting anything."""

    def __init__(self, root: Path, dry_run: bool) -> None:
        self.root = root
        self.dry_run = dry_run
        self.created: list[str] = []
        self.skipped: list[str] = []

    def write_file(self, rel_path: str, content: str) -> None:
        """Write a file if it does not exist yet."""
        path = self.root / rel_path
        if path.exists():
            self.skipped.append(rel_path)
            logger.debug("skip   %s (exists)", rel_path)
            return
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.created.append(rel_path)
        logger.info("create %s", rel_path)

    def update_gitignore(self) -> None:
        """Append project-specific .gitignore lines that are missing."""
        path = self.root / ".gitignore"
        existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        present = {line.strip() for line in existing}
        missing = [line for line in GITIGNORE_ADDITIONS[1:] if line not in present]
        if not missing:
            logger.info("skip   .gitignore (project lines already present)")
            return
        block = "\n".join([GITIGNORE_ADDITIONS[0], *missing])
        if not self.dry_run:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(("\n" if existing and existing[-1].strip() else "") + "\n" + block + "\n")
        logger.info("update .gitignore (+%d lines: %s)", len(missing), ", ".join(missing))

    def run(self) -> None:
        """Create everything."""
        for package in PACKAGES:
            self.write_file(f"{package}/__init__.py", f'"""{package.replace("/", ".")} package."""\n')
        for rel_path, spec in PLACEHOLDERS.items():
            self.write_file(rel_path, render_placeholder(rel_path, spec))
        for directory in EMPTY_DIRS:
            self.write_file(f"{directory}/.gitkeep", "")

        self.write_file("docs/journal/_template.md", JOURNAL_TEMPLATE)
        self.write_file(f"docs/journal/{JOURNAL_DAY0_DATE}.md", JOURNAL_DAY0_TEXT)
        self.write_file("docs/troubleshooting/_template.md", TROUBLESHOOTING_TEMPLATE)
        self.write_file("docs/troubleshooting/README.md", TROUBLESHOOTING_INDEX)
        self.write_file("docs/troubleshooting/0001-apt-unable-to-locate-package.md", TROUBLESHOOTING_0001)
        self.write_file("docs/decisions/_template.md", DECISION_TEMPLATE)
        self.write_file("docs/decisions/README.md", DECISIONS_INDEX)
        self.write_file("docs/decisions/0001-seaweedfs-object-storage.md",
                        decision_stub("0001", "SeaweedFS instead of MinIO"))
        self.write_file("docs/decisions/0002-redpanda-instead-of-kafka.md",
                        decision_stub("0002", "Redpanda instead of Apache Kafka"))
        self.write_file("docs/decisions/0003-uv-python-environment.md",
                        decision_stub("0003", "uv-managed Python 3.12 environment"))
        for rel_path, content in DOC_STUBS.items():
            self.write_file(rel_path, content)

        self.write_file(".env.example", ENV_EXAMPLE)
        self.update_gitignore()


# --------------------------------------------------------------------------------------
# Safety checks
# --------------------------------------------------------------------------------------
def check_repo_root(root: Path) -> None:
    """Stop unless we are at the root of a Git repo that has a data/ folder."""
    if not (root / ".git").is_dir():
        logger.error("%s is not a Git repo root. cd into the repo and run again.", root)
        sys.exit(1)
    if not (root / "data").is_dir():
        logger.warning("No data/ folder found in %s. Continuing, but check you are in the right repo.", root)


def check_data_not_tracked(root: Path) -> None:
    """Warn loudly if any file under data/ is tracked by Git (the repo is public)."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "data"], cwd=root, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        logger.warning("Could not run git ls-files (%s). Check data/ manually.", exc)
        return
    tracked = [line for line in result.stdout.splitlines() if line and line != "data/.gitkeep"]
    if tracked:
        logger.error(
            "%d file(s) under data/ are TRACKED by Git, e.g. %s. Stop and tell your supervisor "
            "before committing anything.", len(tracked), tracked[0],
        )
    else:
        logger.info("check  data/ is not tracked by Git")


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------
def main() -> None:
    """Parse arguments, run safety checks, create the scaffold and print a summary."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would be created, write nothing")
    parser.add_argument("--verbose", action="store_true", help="also list files that already exist")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-7s %(message)s",
    )
    root = Path.cwd()
    check_repo_root(root)
    check_data_not_tracked(root)

    scaffolder = Scaffolder(root, dry_run=args.dry_run)
    scaffolder.run()

    mode = "DRY RUN — nothing written. " if args.dry_run else ""
    logger.info(
        "%sDone: %d created, %d already existed (never overwritten).",
        mode, len(scaffolder.created), len(scaffolder.skipped),
    )
    if not args.dry_run:
        logger.info("Next: cp .env.example .env  (then change the change_me values)")


if __name__ == "__main__":
    main()
