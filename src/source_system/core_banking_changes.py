"""Core banking changes.

Milestone: M3    Written by: Kriti

Purpose:
    Simulate changes in the core banking system so SCD2 has history to track.

Inputs:
    core_banking.customers and core_banking.accounts.

Outputs:
    Updated rows (the trigger moves updated_at), e.g. address change, account status change.

TODO:
    1. Pick a few realistic change types and apply them in a transaction.
    2. Log which IDs changed so you can verify them in silver later.
"""
