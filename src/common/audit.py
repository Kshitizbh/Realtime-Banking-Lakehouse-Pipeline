"""Audit.

Milestone: M1    Written by: Kriti

Purpose:
    Record every pipeline run and every ingested file in the analytics database.

Inputs:
    Run metadata (job name, start/end, status, row counts), file metadata (path, hash, size).

Outputs:
    Rows in analytics: audit.pipeline_runs and audit.file_ingestions.

TODO:
    1. Decide which columns each audit table needs (look at the Pipeline Health page needs).
    2. Write a function that starts a run and one that finishes it with a status.
    3. Make sure a failed job still records a FAILED run.
"""
