"""Database door: extract from the core_banking Postgres source. Customers and accounts incrementally
(watermark on updated_at); branches, transaction_types, merchant_categories in full.

Milestone: M1
Inputs:  Postgres core_banking.* (settings.postgres_dsn), last watermark per table.
Outputs: s3://landing/source=core_<table>/ingestion_date=<date>/<extract_ts>.parquet and updated
         watermarks.

TODO:
    1. Store watermarks durably (e.g. a small JSON object in the landing bucket, or a table in
       analytics).
    2. Incremental: WHERE updated_at > watermark - overlap, ORDER BY updated_at.
    3. Full: reference tables are tiny, so extract them completely every run.
    4. Write Parquet with an explicit schema; record extract_ts.
    5. Advance the watermark only after the upload succeeds (why? think about failures).
    6. Write an audit.pipeline_runs row with rows_out.
"""
