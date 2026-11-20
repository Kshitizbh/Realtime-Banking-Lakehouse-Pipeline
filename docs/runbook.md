# Runbook: running the stack locally

## Memory budget (WSL capped at 16 GB in C:\Users\Admin\.wslconfig)
| Profile | Services | Limit (approx.) | Status |
|---|---|---|---|
| core | SeaweedFS 512 MB, Iceberg REST 768 MB, Postgres 512 MB | ~1.8 GB | ready |
| spark | Spark (local mode) | ~3 GB | next layer |
| streaming | Redpanda + console | ~0.8 GB | next layer |
| serving | Trino + Streamlit | ~2.5 GB | next layer |
| orchestration | Airflow standalone | ~2 GB | next layer |

Keep `make stats` open while you work. Run `make down` when you stop for the day.

## Service URLs (from Ubuntu or a Windows browser)
| Service | URL |
|---|---|
| SeaweedFS S3 API | http://localhost:8333 |
| SeaweedFS admin UI | http://localhost:23646 |
| Iceberg REST catalog | http://localhost:8181/v1/config |
| Postgres | localhost:5432 (db/user from .env) |

## Troubleshooting
| Symptom | Likely cause | Fix |
|---|---|---|
| `Bind for 0.0.0.0:5432 failed: port is already allocated` | Postgres (or another app) already running on Windows | Change `POSTGRES_HOST_PORT=5433` in `.env`, then `make up-core` |
| Same error for 8333/8181/23646 | Port in use | Change the matching `*_PORT` in `.env`; find the user with `netstat -ano \| findstr :8181` in PowerShell |
| `required variable ... is missing` | No `.env` file | `make env`, then edit the passwords |
| `manifest unknown` / `not found` when pulling | Image tag doesn't exist | Check tags on Docker Hub; update the `*_TAG` in `.env` |
| Postgres exits; logs mention `/var/lib/postgresql/data` | Old guides use the pre-18 mount path | Keep the volume at `/var/lib/postgresql` (as in compose) |
| Postgres seed missing / `Expected 5000 customers` | `data/batch` not present when the volume was first created | Check `ls data/batch`, then `make reset-postgres` |
| S3 calls fail with `NoSuchBucket` or DNS errors for `landing.localhost` | Virtual-host addressing | Use `common.s3_client` (path-style); in Spark/Trino set path-style access = true |
| Catalog tables disappear after restart | Catalog not persisted | Check `CATALOG_URI` points at `/home/iceberg/...db` and the `iceberg_catalog` volume exists (`docker volume ls`) |
| `permission denied` writing the catalog DB | Volume created with the wrong owner | `docker compose --profile core down`, `docker volume rm banking-lakehouse_iceberg_catalog`, start again |
| Containers restart in a loop | Out of memory | `make stats`; check `docker inspect <name> --format '{{.State.OOMKilled}}'` |
| Everything is slow | Repo on `/mnt/d/...` instead of `~/projects` | Work only in the Ubuntu copy |
| Shell scripts fail with `bad interpreter` | Windows line endings | `.gitattributes` forces LF; run `git add --renormalize .` once |
| `make: command not found` | Tools missing in Ubuntu | `sudo apt install -y make` |

(Spark jar mismatches and Airflow init issues are added with those layers.)
