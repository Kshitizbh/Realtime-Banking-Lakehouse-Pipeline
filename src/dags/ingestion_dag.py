"""Daily ingestion: reference + customer/account extracts and file drops to landing (DQ checks 1-4).

Milestone: M11
Inputs:  logical date
Outputs: Airflow DAG

TODO:
    1. Use the run's logical date, not today.
"""
