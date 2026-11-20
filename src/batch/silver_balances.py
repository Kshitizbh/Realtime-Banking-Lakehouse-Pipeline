"""Bronze daily balances -> silver, with a balance integrity check.

Milestone: M3
Inputs:  lakehouse.bronze.balances
Outputs: lakehouse.silver.daily_balances

TODO:
    1. Check opening_balance + credit_total - debit_total = closing_balance; quarantine failures.
"""
