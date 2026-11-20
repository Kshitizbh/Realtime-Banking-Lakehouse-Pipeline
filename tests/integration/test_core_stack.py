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


# ---------------------------------------------------------------- core-banking Postgres
def test_postgres_seed_counts() -> None:
    with psycopg.connect(settings.postgres_dsn) as conn:
        customers = conn.execute("select count(*) from core_banking.customers").fetchone()[0]
        accounts = conn.execute("select count(*) from core_banking.accounts").fetchone()[0]
    assert (customers, accounts) == (5000, 8000)


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
