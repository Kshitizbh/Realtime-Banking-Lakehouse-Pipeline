"""Central configuration loaded from environment variables (and .env for local runs).

Usage:
    from common.config import get_settings
    settings = get_settings()
    settings.s3_endpoint_url

Rule for the whole project: no hard-coded hosts, paths or credentials anywhere else.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name} (see .env.example)")
    return value


def _optional(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    """Typed, read-only view of the environment."""

    # Object storage (SeaweedFS S3 API)
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str
    bucket_landing: str
    bucket_warehouse: str
    bucket_checkpoints: str

    # Iceberg REST catalog
    iceberg_rest_uri: str

    # Core-banking Postgres
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Local
    local_data_dir: Path
    log_level: str

    @property
    def postgres_dsn(self) -> str:
        """Connection string for psycopg (never log this: it contains the password)."""
        return (
            f"host={self.postgres_host} port={self.postgres_port} dbname={self.postgres_db} "
            f"user={self.postgres_user} password={self.postgres_password}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process. Real environment variables win over .env."""
    load_dotenv(override=False)
    return Settings(
        s3_endpoint_url=_required("S3_ENDPOINT_URL"),
        s3_access_key=_required("S3_ACCESS_KEY"),
        s3_secret_key=_required("S3_SECRET_KEY"),
        s3_region=_optional("S3_REGION", "us-east-1"),
        bucket_landing=_optional("BUCKET_LANDING", "landing"),
        bucket_warehouse=_optional("BUCKET_WAREHOUSE", "warehouse"),
        bucket_checkpoints=_optional("BUCKET_CHECKPOINTS", "checkpoints"),
        iceberg_rest_uri=_required("ICEBERG_REST_URI"),
        postgres_host=_optional("POSTGRES_HOST", "localhost"),
        postgres_port=int(_optional("POSTGRES_HOST_PORT", "5432")),
        postgres_db=_required("POSTGRES_DB"),
        postgres_user=_required("POSTGRES_USER"),
        postgres_password=_required("POSTGRES_PASSWORD"),
        local_data_dir=Path(_optional("LOCAL_DATA_DIR", "./data")).resolve(),
        log_level=_optional("LOG_LEVEL", "INFO").upper(),
    )
