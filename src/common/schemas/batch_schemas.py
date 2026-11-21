"""Batch schemas.

Milestone: M2    Written by: Kriti

Purpose:
    Explicit Spark schemas for every batch file and extract (never infer).

Inputs:
    Column lists from data/batch, data/reference and the core_banking extracts.

Outputs:
    StructType definitions imported by the Bronze jobs.

TODO:
    1. Profile each file's header and decide a type per column.
    2. Keep dates as strings in Bronze if their formats differ (account snapshot uses M/D/YYYY).
"""
