"""Incrementally extract customers and accounts from the Postgres core-banking DB.

Milestone: M1
Inputs:  Postgres core_banking.customers / core_banking.accounts, last watermark (max updated_at).
Outputs: s3://landing/core_banking/<table>/extract_ts=<ts>/part.parquet and an updated watermark.

TODO:
    1. Store the watermark somewhere durable (e.g. a small JSON object in the landing bucket).
    2. Query rows WHERE updated_at > watermark, ordered by updated_at.
    3. Write Parquet with an explicit schema; record extract_ts.
    4. Advance the watermark only after the upload succeeds (why? think about failures).
"""
