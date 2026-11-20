"""Land the daily batch files (transactions, balances, settlements, snapshots, reference) into the
`landing` bucket, simulating an SFTP drop from core banking.

Milestone: M1
Inputs:  LOCAL_DATA_DIR/batch/**, LOCAL_DATA_DIR/reference/*, a run date (YYYY-MM-DD).
Outputs: s3://landing/<source>/ingest_date=<date>/<file> plus a small _SUCCESS/metadata marker.

TODO:
    1. Read the run date from CLI args (argparse), default = today.
    2. Verify each file's SHA-256 against manifests/source_manifest.csv BEFORE upload (see
       quality/manifest_check.py).
    3. Upload with the shared S3 client; key layout must be deterministic so re-runs overwrite, not
       duplicate.
    4. Log counts and skipped/failed files; exit non-zero if any file fails its checksum.
"""
