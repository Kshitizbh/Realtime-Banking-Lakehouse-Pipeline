"""File drop.

Milestone: M1    Written by: Kriti

Purpose:
    Ingest the daily file drops (transactions, balances, settlements) into the landing bucket.

Inputs:
    data/batch/{transactions,balances,settlements}/*.csv and data/manifest/source_manifest.csv.

Outputs:
    s3://landing/source=<name>/ingestion_date=YYYY-MM-DD/<file> plus audit rows.

TODO:
    1. For a run date, find the expected files.
    2. Run source checks 1-4 (quality/source_checks.py) before uploading.
    3. Upload only files that pass and were not ingested before (same hash = skip).
    4. Record each file in the audit log.
"""
