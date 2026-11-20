"""Inject labelled fraud scenarios into the replayed stream (the dataset has no fraud labels).

Milestone: M4
Inputs:  Account and customer IDs, scenario config.
Outputs: Fraud events on bank.transactions plus a ground-truth file s3://landing/fraud_labels/...

TODO:
    1. Scenarios: velocity burst, failed-attempt burst, dormant/closed/blocked account activity,
       amount spike.
    2. Write the ground truth separately; never put the label in the event itself.
"""
