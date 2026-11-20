# 0001 - Object storage: SeaweedFS instead of MinIO

- Status: accepted
- Date: 2026-11-20

## Context
The lakehouse needs a local S3-compatible object store for landing files, Iceberg
data/metadata and streaming checkpoints. MinIO was the original plan, but the
community edition stopped publishing Docker images and binaries in October 2025,
entered maintenance mode in December 2025, and the remaining images carry
unpatched CVEs. `docker pull minio/minio` no longer works.

## Options considered
| Option | For | Against |
|---|---|---|
| Frozen MinIO image mirror | No code changes | Unmaintained, known CVEs |
| RustFS | Closest MinIO drop-in | Young project, recommended for pilots only |
| Garage | Lightweight | Eventual consistency is a poor fit for Iceberg commits |
| **SeaweedFS** | Mature (since 2015), Apache 2.0, single-process `weed mini`, tested with Iceberg REST | Smaller contributor base; separate admin UI port |

## Decision
Use SeaweedFS (`weed mini`) with path-style S3 addressing on port 8333.

## Consequences
- All code talks to the S3 API through `common.s3_client`, so the store can be swapped again by changing `.env` only.
- Every S3 client (boto3, Spark S3FileIO, Trino) must use path-style access.
- Interview point: storage is a replaceable dependency behind a standard API.
