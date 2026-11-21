"""Iceberg maintenance.

Milestone: M11    Written by: Kriti

Purpose:
    Iceberg housekeeping: compaction, snapshot expiry, orphan-file cleanup.

Inputs:
    List of tables and retention settings from config.

Outputs:
    Smaller, fewer files and bounded metadata.

TODO:
    (none yet)
"""
