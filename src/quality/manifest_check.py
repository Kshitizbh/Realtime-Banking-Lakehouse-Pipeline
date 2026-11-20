"""Verify file integrity against manifests/source_manifest.csv (SHA-256 + size).

Milestone: M1
Inputs:  A file path and the manifest.
Outputs: Pass/fail result with reason.

TODO:
    1. Note: manifest paths use Windows backslashes; normalise them.
"""
