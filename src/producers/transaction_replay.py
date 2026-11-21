"""Kafka producer: replay streaming/transaction_events_*.jsonl into Redpanda in event_ts order.

Milestone: M4
Inputs:  LOCAL_DATA_DIR/streaming/*.jsonl, speed-up factor, topic name from config.
Outputs: Messages on banking.transactions.raw (key = account_id), malformed events mixed in.

TODO:
    1. Use the confluent-kafka Producer; explain your choice of message key.
    2. Support a speed-up factor (e.g. 1 day of events in 10 minutes).
    3. Emit v1 events, then switch to a v2 schema (e.g. device_id, ip_country) mid-run.
    4. Mix in malformed_events_*.jsonl so the DLQ path is exercised.
    5. Flush and report delivery errors; log counts per topic.
"""
