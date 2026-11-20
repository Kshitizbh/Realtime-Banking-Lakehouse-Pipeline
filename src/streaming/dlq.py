"""Dead-letter handling for malformed events.

Milestone: M5
Inputs:  Records that fail parsing or validation.
Outputs: Topic bank.transactions.dlq and table lakehouse.bronze.dlq_events with the error reason.

TODO:
    1. Keep the raw payload and the reason; never drop data silently.
"""
