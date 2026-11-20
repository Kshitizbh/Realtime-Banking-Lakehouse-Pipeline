"""Replay streaming/transaction_events_*.jsonl into Redpanda in event_ts order.

Milestone: M4
Inputs:  LOCAL_DATA_DIR/streaming/*.jsonl, speed-up factor, topic name.
Outputs: Messages on topic bank.transactions (key = account_id) and malformed records on the same
         topic.

TODO:
    1. Decide the message key and explain why (ordering per account?).
    2. Support a speed-up factor (e.g. 1 day of events in 10 minutes).
    3. Emit v1 events, then switch to a v2 schema (e.g. device_id, ip_country) mid-run.
    4. Mix in malformed_events_*.jsonl so the DLQ path is exercised.
"""
