"""Bronze transactions -> silver: typed, deduplicated, reversals linked.

Milestone: M3
Inputs:  lakehouse.bronze.bronze_transactions
Outputs: lakehouse.silver.silver_transactions (MERGE on transaction_id).

TODO:
    1. Cast types; parse timestamps; validate enums against reference tables.
    2. Remove the 1,200 exact duplicates; decide which record wins and why.
    3. Link reversals to original_transaction_id.
"""
