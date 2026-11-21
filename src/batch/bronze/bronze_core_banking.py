"""Bronze core banking.

Milestone: M2    Written by: Kriti

Purpose:
    Load core_banking extracts into Bronze Iceberg tables.

Inputs:
    s3://landing/source=core_*|ref_*/...

Outputs:
    bronze_customers, bronze_accounts, bronze_branches, bronze_transaction_types, bronze_merchant_categories.

TODO:
    (none yet)
"""
