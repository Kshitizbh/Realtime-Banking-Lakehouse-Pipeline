"""Data-quality checks between layers (14 checks, see INSTRUCTION-adapted section 8).

Milestone: M9
Inputs:  Iceberg tables, Kafka topics, audit tables.
Outputs: Rows in analytics quality.check_results; a pass/fail gate for the pipeline.

TODO:
    1. Start with: unique transaction_id in silver, stream vs batch amount mismatches.
"""
