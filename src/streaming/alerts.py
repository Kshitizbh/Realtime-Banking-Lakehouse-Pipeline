"""Real-time fraud rules with windowed aggregations.

Milestone: M7
Inputs:  lakehouse.silver.transaction_events, silver.accounts (stream-static join).
Outputs: lakehouse.gold.fraud_alerts (and optionally an alerts topic).

TODO:
    1. Velocity, failed bursts, amount vs baseline, dormant/closed/blocked accounts.
"""
