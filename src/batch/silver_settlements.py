"""Bronze settlement files -> silver settlements (input to reconciliation in gold).

Milestone: M3
Inputs:  lakehouse.bronze.bronze_settlements
Outputs: lakehouse.silver.silver_settlements

TODO:
    1. Keep settlement data independent of transactions; the comparison happens in gold.
"""
