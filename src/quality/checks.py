"""Data quality checks between layers (row counts, nulls, uniqueness, reconciliation).

Milestone: M3/M12
Inputs:  Iceberg tables.
Outputs: A results table lakehouse.quality.check_results.

TODO:
    1. Start with: unique transaction_id in silver, stream vs batch amount mismatches.
"""
