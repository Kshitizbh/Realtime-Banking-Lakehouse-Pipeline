"""S3 client factory for SeaweedFS (any S3-compatible store works the same way).

Usage:
    from common.s3_client import get_s3_client
    s3 = get_s3_client()
    s3.upload_file(local_path, settings.bucket_landing, key)
"""

from __future__ import annotations

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from common.config import Settings, get_settings


def get_s3_client(settings: Settings | None = None) -> BaseClient:
    """Return a boto3 S3 client configured for the local object store.

    Path-style addressing is required: SeaweedFS serves http://host:8333/<bucket>/<key>
    and does not create per-bucket DNS names like <bucket>.host.
    """
    s = settings or get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        region_name=s.s3_region,
        config=Config(
            s3={"addressing_style": "path"},
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=5,
            read_timeout=60,
        ),
    )
