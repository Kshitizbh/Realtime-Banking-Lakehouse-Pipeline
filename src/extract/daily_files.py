"""File-drop door: land the daily transactions, balances and settlement files (plus the manifest) in
the landing bucket, simulating an SFTP drop from core banking and the clearing house.

Milestone: M1
Inputs:  LOCAL_DATA_DIR/batch/{transactions,balances,settlements}/*, LOCAL_DATA_DIR/manifests/, a
         run date.
Outputs: s3://landing/source=<source_name>/ingestion_date=<YYYY-MM-DD>/<file>, one
         audit.file_ingestions row per file and one audit.pipeline_runs row per run (analytics DB).

TODO:
    1. Read the run date from CLI args (argparse); default = today.
    2. DQ check 1: the expected file for the run date exists.
    3. DQ check 2: SHA-256 and size match manifests/source_manifest.csv (see
       quality/manifest_check.py).
    4. DQ check 3: skip a file whose hash was already INGESTED (the analytics DB enforces this too).
    5. DQ check 4: header matches the expected columns.
    6. Upload with the shared S3 client; deterministic keys so a re-run never duplicates.
    7. Write audit rows (see quality/audit.py); exit non-zero if any file is REJECTED.
"""
