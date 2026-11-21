"""Build SCD Type 2 history for accounts (status changes matter for fraud rules).

Milestone: M3
Inputs:  lakehouse.bronze.bronze_accounts
Outputs: lakehouse.silver.silver_accounts with valid_from, valid_to, is_current.

TODO:
    1. The Postgres extract already has typed dates; the original snapshot file used M/D/YYYY.
"""
