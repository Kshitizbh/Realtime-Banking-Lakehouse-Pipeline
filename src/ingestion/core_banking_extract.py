"""Core banking extract.

Milestone: M1    Written by: Kriti

Purpose:
    Extract from the core_banking Postgres database like a real OLTP source.

Inputs:
    core_banking tables: customers, accounts (incremental on updated_at), branches, transaction_types, merchant_categories (full).

Outputs:
    Extract files in s3://landing/source=core_<table>/ or ref_<table>/ plus audit rows.

TODO:
    1. Read the last watermark for each incremental table.
    2. Extract only rows changed since the watermark; save the new watermark only after a successful upload.
    3. Do full extracts for the reference tables.
"""
