"""One logging format for every script and job.

Named logging_setup.py (not logging.py) so it can never shadow Python's own
`logging` module.

Usage:
    from common.logging_setup import get_logger
    log = get_logger(__name__)
    log.info("Uploaded %s files", n)
"""

from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once (idempotent)."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # Quieten very chatty libraries.
    for noisy in ("botocore", "boto3", "urllib3", "s3transfer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, configuring logging from LOG_LEVEL on first use."""
    if not _configured:
        from common.config import get_settings

        configure_logging(get_settings().log_level)
    return logging.getLogger(name)
