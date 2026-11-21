"""Streaming silver: dedupe by event_id with a watermark; handle late events; near-real-time
aggregates.

Milestone: M6
Inputs:  lakehouse.bronze.bronze_transaction_events
Outputs: lakehouse.silver.silver_transaction_events + near-real-time aggregate tables.

TODO:
    1. Choose the watermark delay from the data (events arrive up to 2 days late) and justify it.
"""
