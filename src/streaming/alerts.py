"""Rule-based fraud alerts with windowed aggregations.

Milestone: M7
Inputs:  lakehouse.silver.silver_transaction_events, silver_accounts (stream-static join).
Outputs: Topic banking.fraud.alerts and the source for gold fact_fraud_alert.

TODO:
    1. Velocity, failed bursts, amount vs baseline, dormant/closed/blocked accounts, high-risk MCC.
"""
