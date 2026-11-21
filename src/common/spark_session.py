"""Spark session.

Milestone: M0    Written by: Claude

Purpose:
    Spark session factory configured for Iceberg (REST catalog), SeaweedFS (S3, path-style) and Kafka.

Inputs:
    Settings from config.

Outputs:
    A SparkSession ready to read/write Iceberg tables and Kafka topics.

TODO:
    (none yet)
"""
