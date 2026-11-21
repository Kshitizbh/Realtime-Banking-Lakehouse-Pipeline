"""Spark batch job: landing -> bronze Iceberg tables (append, data unchanged).

Milestone: M2
Inputs:  s3://landing/source=<source>/ingestion_date=<date>/
Outputs: Iceberg tables lakehouse.bronze.bronze_<source> with ingestion metadata columns.

TODO:
    1. Read with an explicit schema (all strings is fine for bronze).
    2. Add source_file, ingested_at, ingestion_date, run_id.
    3. Decide and document the partitioning strategy (brief section 13).
    4. Make re-runs for the same date safe (no duplicate loads).
"""
