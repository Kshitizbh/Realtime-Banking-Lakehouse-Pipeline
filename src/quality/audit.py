"""Helpers to write audit rows to the analytics database (settings.analytics_dsn).

Milestone: M1
Inputs:  Pipeline name, run date, counts, status, error.
Outputs: Rows in audit.pipeline_runs and audit.file_ingestions.

TODO:
    1. start_run(...) -> run_id (status RUNNING); finish_run(run_id, status, rows_in, rows_out,
       error).
    2. record_file(run_id, ...) for each file the file-drop door looks at.
    3. Make sure a crash still marks the run FAILED (try/finally or a context manager).
"""
