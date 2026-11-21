"""Build SCD Type 2 history for customers from core-banking extracts.

Milestone: M3
Inputs:  lakehouse.bronze.bronze_customers
Outputs: lakehouse.silver.silver_customers with valid_from, valid_to, is_current.

TODO:
    1. Detect changed attributes with a hash; close old rows, insert new ones in one MERGE.
"""
