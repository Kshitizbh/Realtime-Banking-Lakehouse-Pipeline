"""Verify file integrity against manifests/source_manifest.csv (SHA-256 + size) - DQ check 2.

Milestone: M1
Inputs:  A file path and the manifest.
Outputs: MATCH / MISMATCH / NOT_IN_MANIFEST with a reason.

TODO:
    1. Note: manifest paths use Windows backslashes; normalise them.
"""
