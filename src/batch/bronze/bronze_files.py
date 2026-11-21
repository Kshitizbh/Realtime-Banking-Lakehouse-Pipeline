"""Bronze files.

Milestone: M2    Written by: Kriti

Purpose:
    Load landed daily files into Bronze Iceberg tables, unchanged, with ingestion metadata.

Inputs:
    s3://landing/source=transactions|balances|settlements/...

Outputs:
    bronze_transactions, bronze_balances, bronze_settlements.

TODO:
    1. Read with explicit schemas.
    2. Add ingestion metadata (source file, ingested_at, batch id).
    3. Make re-runs idempotent (the same file must not be appended twice).
"""
