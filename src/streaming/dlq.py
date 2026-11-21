"""Dead-letter handling for malformed events (DQ check 5).

Milestone: M5
Inputs:  Records that fail parsing or validation.
Outputs: Topic banking.transactions.dlq and table lakehouse.bronze.bronze_dlq_events with the error
         reason.

TODO:
    1. Keep the raw payload and the reason; never drop data silently.
"""
