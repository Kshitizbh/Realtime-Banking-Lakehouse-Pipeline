"""Daily batch: extract -> bronze -> silver -> quality.

Milestone: M11
Inputs:  run date
Outputs: Airflow DAG

TODO:
    1. Use the run's logical date, not today.
"""
