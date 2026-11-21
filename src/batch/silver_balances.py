"""Bronze daily balances -> silver, with a balance integrity check.

Milestone: M3
Inputs:  lakehouse.bronze.bronze_balances
Outputs: lakehouse.silver.silver_daily_balances

TODO:
    1. DQ check 11: opening_balance + credit_total - debit_total = closing_balance; quarantine
       failures.
"""
