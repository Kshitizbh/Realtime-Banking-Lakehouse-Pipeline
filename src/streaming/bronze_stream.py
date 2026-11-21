"""Spark Structured Streaming: banking.transactions.raw -> validation -> bronze Iceberg.

Milestone: M5
Inputs:  Kafka topic banking.transactions.raw
Outputs: lakehouse.bronze.bronze_transaction_events (+ Kafka partition/offset/timestamp), valid
         events to banking.transactions.validated.

TODO:
    1. Use an explicit schema (common/schemas); never infer.
    2. Route unparseable/invalid records to the DLQ (see dlq.py).
    3. Checkpoint location in s3://checkpoints/...
"""
