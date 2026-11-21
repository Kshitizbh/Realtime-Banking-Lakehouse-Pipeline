"""Run checks.

Milestone: M9    Written by: Kriti

Purpose:
    Command-line entry point: run a group of checks and act as a quality gate.

Inputs:
    Check group name (source, transformation, business, freshness).

Outputs:
    Exit code non-zero when a critical check fails (so Airflow stops downstream tasks).

TODO:
    (none yet)
"""
