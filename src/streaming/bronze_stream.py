"""Spark Structured Streaming: Redpanda -> bronze Iceberg (append).

Milestone: M5
Inputs:  Kafka topic bank.transactions
Outputs: lakehouse.bronze.transaction_events (+ Kafka partition/offset/timestamp metadata).

TODO:
    1. Use an explicit schema (common/schemas); never infer.
    2. Route unparseable records to the DLQ (see dlq.py).
    3. Checkpoint location in s3://checkpoints/...
"""
