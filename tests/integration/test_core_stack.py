"""End-to-end smoke test for the `core` profile.

Run:  make up-core && make smoke
Each test proves one service does its job, not just that the container is "Up".
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
import requests

from common.config import get_settings
from common.s3_client import get_s3_client

pytestmark = pytest.mark.integration
settings = get_settings()


# ---------------------------------------------------------------- object storage
def test_buckets_were_created() -> None:
    names = {b["Name"] for b in get_s3_client().list_buckets()["Buckets"]}
    expected = {settings.bucket_landing, settings.bucket_warehouse, settings.bucket_checkpoints}
    assert expected <= names, f"missing buckets: {expected - names}"


def test_object_round_trip() -> None:
    s3 = get_s3_client()
    key = f"_smoke/{uuid.uuid4()}.txt"
    s3.put_object(Bucket=settings.bucket_landing, Key=key, Body=b"hello lakehouse")
    try:
        body = s3.get_object(Bucket=settings.bucket_landing, Key=key)["Body"].read()
        assert body == b"hello lakehouse"
    finally:
        s3.delete_object(Bucket=settings.bucket_landing, Key=key)


# ---------------------------------------------------------------- Iceberg REST catalog
def _catalog_base() -> str:
    resp = requests.get(f"{settings.iceberg_rest_uri}/v1/config", timeout=10)
    resp.raise_for_status()
    prefix = resp.json().get("overrides", {}).get("prefix")
    return f"{settings.iceberg_rest_uri}/v1/{prefix}" if prefix else f"{settings.iceberg_rest_uri}/v1"


def test_catalog_namespace_lifecycle() -> None:
    base = _catalog_base()
    ns = "smoke_test"
    requests.delete(f"{base}/namespaces/{ns}", timeout=10)  # clean up a previous failed run

    created = requests.post(f"{base}/namespaces", json={"namespace": [ns], "properties": {}}, timeout=10)
    assert created.status_code == 200, created.text

    listed = requests.get(f"{base}/namespaces", timeout=10).json()["namespaces"]
    assert [ns] in listed

    deleted = requests.delete(f"{base}/namespaces/{ns}", timeout=10)
    assert deleted.status_code in (200, 204), deleted.text


# ---------------------------------------------------------------- core_banking (source)
EXPECTED_SEED = {
    "branches": 40,
    "transaction_types": 6,
    "merchant_categories": 8,
    "customers": 5000,
    "accounts": 8000,
}


@pytest.mark.parametrize(("table", "expected"), EXPECTED_SEED.items())
def test_postgres_seed_counts(table: str, expected: int) -> None:
    with psycopg.connect(settings.postgres_dsn) as conn:
        count = conn.execute(f"select count(*) from core_banking.{table}").fetchone()[0]
    assert count == expected


def test_every_account_has_a_valid_branch() -> None:
    """The FK accounts.branch_id -> branches exists, so this proves it is enforced and satisfied."""
    with psycopg.connect(settings.postgres_dsn) as conn:
        orphans = conn.execute(
            "select count(*) from core_banking.accounts a "
            "left join core_banking.branches b using (branch_id) where b.branch_id is null"
        ).fetchone()[0]
        fk = conn.execute(
            "select count(*) from information_schema.table_constraints "
            "where table_schema = 'core_banking' and table_name = 'accounts' "
            "and constraint_type = 'FOREIGN KEY'"
        ).fetchone()[0]
    assert orphans == 0
    assert fk == 2  # -> customers and -> branches


def test_updated_at_trigger_moves_watermark() -> None:
    """An UPDATE must bump updated_at, otherwise incremental extraction would miss it."""
    with psycopg.connect(settings.postgres_dsn) as conn:
        before = conn.execute(
            "select updated_at from core_banking.customers where customer_id = 'CUST00000001'"
        ).fetchone()[0]
        after = conn.execute(
            "update core_banking.customers set risk_band = risk_band "
            "where customer_id = 'CUST00000001' returning updated_at"
        ).fetchone()[0]
        conn.rollback()  # leave the seed data untouched
    assert after > before


# ---------------------------------------------------------------- analytics (platform)
def test_analytics_tables_exist() -> None:
    with psycopg.connect(settings.analytics_dsn) as conn:
        rows = conn.execute(
            "select table_schema || '.' || table_name from information_schema.tables "
            "where table_schema in ('audit', 'quality') order by 1"
        ).fetchall()
    assert [r[0] for r in rows] == [
        "audit.file_ingestions",
        "audit.pipeline_runs",
        "quality.check_results",
    ]


def test_same_file_cannot_be_ingested_twice() -> None:
    """DQ check 3 is enforced by the database: a second INGESTED row with the same hash fails."""
    row = {
        "source_name": "_smoke",
        "file_name": "f.csv",
        "ingestion_date": "2026-01-01",
        "file_sha256": "a" * 64,
        "file_size_bytes": 1,
        "manifest_status": "MATCH",
        "status": "INGESTED",
    }
    insert = (
        "insert into audit.file_ingestions (source_name, file_name, ingestion_date, file_sha256, "
        "file_size_bytes, manifest_status, status) values (%(source_name)s, %(file_name)s, "
        "%(ingestion_date)s, %(file_sha256)s, %(file_size_bytes)s, %(manifest_status)s, %(status)s)"
    )
    with psycopg.connect(settings.analytics_dsn) as conn:
        conn.execute(insert, row)
        with pytest.raises(psycopg.errors.UniqueViolation):
            conn.execute(insert, row)
        conn.rollback()  # leave the audit table empty
