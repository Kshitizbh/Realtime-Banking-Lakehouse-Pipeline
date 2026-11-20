"""Extract official daily NPR exchange rates from the Nepal Rastra Bank forex API.

Milestone: M1
Inputs:  NRB forex API (verify endpoint and paging in M1), date range.
Outputs: s3://landing/fx_rates/rate_date=<date>/rates.json

TODO:
    1. Handle HTTP errors, timeouts and retries with backoff.
    2. Keep the raw JSON exactly as received (bronze principle).
    3. Make it idempotent per date.
"""
