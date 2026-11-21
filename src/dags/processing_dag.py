"""Spark Bronze + Silver batch jobs after ingestion (DQ checks 6-11).

Milestone: M11
Inputs:  landing data for the logical date
Outputs: Airflow DAG

TODO:
    1. Wait for ingestion_dag to succeed for the same date.
"""
