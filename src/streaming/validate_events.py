"""Validate events.

Milestone: M5    Written by: Kriti

Purpose:
    Streaming Bronze: read the raw topic, validate, route good and bad events.

Inputs:
    banking.transactions.raw.

Outputs:
    banking.transactions.validated, banking.transactions.dlq, bronze_transaction_events, bronze_dlq_events (checkpointed).

TODO:
    (none yet)
"""
