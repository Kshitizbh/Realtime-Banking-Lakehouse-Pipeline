"""Spark batch job: landing files -> bronze Iceberg tables (append, unchanged data).

Milestone: M2
Inputs:  s3://landing/<source>/ingest_date=<date>/
Outputs: Iceberg tables lakehouse.bronze.<source> with ingestion metadata columns.

TODO:
    1. Read with an explicit schema (all strings is fine for bronze).
    2. Add source_file, ingested_at, ingest_date, batch_id.
    3. Make re-runs for the same date safe (no duplicate loads).
"""
