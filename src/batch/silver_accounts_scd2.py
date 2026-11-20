"""Build SCD Type 2 history for accounts (status changes matter for fraud rules).

Milestone: M3
Inputs:  lakehouse.bronze.core_banking_accounts
Outputs: lakehouse.silver.accounts with valid_from, valid_to, is_current.

TODO:
    1. Parse the M/D/YYYY dates from the account snapshot correctly.
"""
