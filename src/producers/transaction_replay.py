"""Transaction replay.

Milestone: M4    Written by: Kriti

Purpose:
    Replay transaction events to Redpanda as if they were live.

Inputs:
    data/streaming/*.jsonl (transaction events + malformed events).

Outputs:
    Messages on banking.transactions.raw, key = account_id.

TODO:
    1. Read events and send them in event_ts order with a speed-up factor from config.
    2. Mix in the malformed events.
    3. Switch from v1 to v2 events at a configurable point.
    4. Flush on exit and log delivery failures.
"""
