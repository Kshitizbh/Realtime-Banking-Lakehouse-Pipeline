"""Silver events.

Milestone: M6    Written by: Kriti

Purpose:
    Streaming Silver: watermark, deduplicate on event_id, handle late events.

Inputs:
    bronze_transaction_events or banking.transactions.validated.

Outputs:
    silver_transaction_events.

TODO:
    (none yet)
"""
