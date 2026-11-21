"""Kafka producer: inject labelled fraud scenarios (the dataset has no fraud labels).

Milestone: M4 (optional)
Inputs:  Account and customer IDs, scenario config.
Outputs: Events on banking.transactions.raw plus a ground-truth file
         s3://landing/source=fraud_labels/...

TODO:
    1. Scenarios: velocity burst, failed-attempt burst, dormant/closed/blocked account activity,
       amount spike.
    2. Write the ground truth separately; never put the label in the event itself.
"""
