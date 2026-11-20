"""Streaming silver: dedupe by event_id with a watermark; handle late events.

Milestone: M6
Inputs:  lakehouse.bronze.transaction_events
Outputs: lakehouse.silver.transaction_events

TODO:
    1. Choose the watermark delay from the data (events arrive up to 2 days late) and justify it.
"""
