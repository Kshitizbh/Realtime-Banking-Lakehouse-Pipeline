# Run `make` or `make help` to see the commands.
# Docker Compose reads .env automatically; every target assumes you are in the repo root.

SHELL := /bin/bash
COMPOSE := docker compose
PY := .venv/bin/python

-include .env
export

# Fallback so older .env files without ANALYTICS_DB still work.
ANALYTICS_DB_NAME := $(or $(ANALYTICS_DB),analytics)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------- one-time setup ----------
.PHONY: env scaffold venv
env: ## Create .env from .env.example (never overwrites an existing .env)
	@test -f .env && echo ".env already exists - left unchanged" || (cp .env.example .env && echo "Created .env - now edit the passwords")

scaffold: ## Create folders + placeholder files (safe to re-run)
	python3 setup_project.py

venv: ## Create .venv with Python 3.12 (via uv) and install the project + dev tools
	uv venv --python 3.12 .venv
	uv pip install -e ".[dev]"

# ---------- stack: core profile ----------
.PHONY: pull up-core down ps logs stats
pull: ## Download the pinned images for the core profile
	$(COMPOSE) --profile core pull

up-core: ## Start SeaweedFS + Iceberg REST + Postgres (~1.8 GB RAM)
	$(COMPOSE) --profile core up -d
	@echo "Waiting for health checks..." && sleep 15 && $(COMPOSE) --profile core ps

down: ## Stop ALL containers (data in volumes is kept)
	$(COMPOSE) --profile "*" down

ps: ## Show running containers
	$(COMPOSE) --profile "*" ps

logs: ## Follow logs: make logs s=iceberg-rest
	$(COMPOSE) --profile "*" logs -f --tail=100 $(s)

stats: ## Live CPU/memory per container
	docker stats

# ---------- checks ----------
.PHONY: health smoke psql psql-analytics
health: ## Quick health check of every core service
	@echo "--- Iceberg REST catalog (expect JSON) ---"
	@curl -sf http://localhost:$(ICEBERG_REST_HOST_PORT)/v1/config && echo || echo "FAIL: catalog not reachable"
	@echo "--- SeaweedFS S3 API (expect HTTP 403 = up and requiring credentials) ---"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:$(S3_HOST_PORT)/ || echo "FAIL: S3 not reachable"
	@echo "--- core_banking seed (expect branches 40, transaction_types 6, merchant_categories 8, customers 5000, accounts 8000) ---"
	@$(COMPOSE) exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tA -c "\
	  select 'branches', count(*) from core_banking.branches union all \
	  select 'transaction_types', count(*) from core_banking.transaction_types union all \
	  select 'merchant_categories', count(*) from core_banking.merchant_categories union all \
	  select 'customers', count(*) from core_banking.customers union all \
	  select 'accounts', count(*) from core_banking.accounts;"
	@echo "--- analytics database (expect 3 tables: audit.file_ingestions, audit.pipeline_runs, quality.check_results) ---"
	@$(COMPOSE) exec -T postgres psql -U $(POSTGRES_USER) -d $(ANALYTICS_DB_NAME) -tA -c "\
	  select table_schema || '.' || table_name from information_schema.tables \
	  where table_schema in ('audit','quality','serving') order by 1;"

smoke: ## End-to-end test of the core stack (needs `make venv` and `make up-core`)
	$(PY) -m pytest tests/integration/test_core_stack.py -v

psql: ## Open a SQL shell on the core_banking (source) DB
	$(COMPOSE) exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

psql-analytics: ## Open a SQL shell on the analytics (audit/quality) DB
	$(COMPOSE) exec postgres psql -U $(POSTGRES_USER) -d $(ANALYTICS_DB_NAME)

# ---------- resets (destructive: local data only) ----------
.PHONY: reset-postgres clean
reset-postgres: ## Drop the Postgres volume and re-run the init scripts (re-seeds both databases)
	@read -p "Delete the Postgres volume and re-seed? [y/N] " a && [ "$$a" = "y" ]
	$(COMPOSE) --profile core rm -sf postgres
	docker volume rm banking-lakehouse_postgres_data
	$(COMPOSE) --profile core up -d postgres

clean: ## Stop everything AND delete all volumes (all lakehouse data!)
	@read -p "Delete ALL containers and volumes? [y/N] " a && [ "$$a" = "y" ]
	$(COMPOSE) --profile "*" down -v
