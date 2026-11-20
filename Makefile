# Run `make` or `make help` to see the commands.
# Docker Compose reads .env automatically; every target assumes you are in the repo root.

SHELL := /bin/bash
COMPOSE := docker compose
PY := .venv/bin/python

-include .env
export

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

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
.PHONY: health smoke psql
health: ## Quick health check of every core service
	@echo "--- Iceberg REST catalog (expect JSON) ---"
	@curl -sf http://localhost:$(ICEBERG_REST_HOST_PORT)/v1/config && echo || echo "FAIL: catalog not reachable"
	@echo "--- SeaweedFS S3 API (expect HTTP 403 = up and requiring credentials) ---"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:$(S3_HOST_PORT)/ || echo "FAIL: S3 not reachable"
	@echo "--- Postgres seed (expect 5000 customers, 8000 accounts) ---"
	@$(COMPOSE) exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tA \
	  -c "select 'customers', count(*) from core_banking.customers union all select 'accounts', count(*) from core_banking.accounts;"

smoke: ## End-to-end test of the core stack (needs `make venv` and `make up-core`)
	$(PY) -m pytest tests/integration/test_core_stack.py -v

psql: ## Open a SQL shell on the core-banking DB
	$(COMPOSE) exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# ---------- resets (destructive: local data only) ----------
.PHONY: reset-postgres clean
reset-postgres: ## Drop the Postgres volume and re-seed on next start
	@read -p "Delete the Postgres volume and re-seed? [y/N] " a && [ "$$a" = "y" ]
	$(COMPOSE) --profile core rm -sf postgres
	docker volume rm banking-lakehouse_postgres_data
	$(COMPOSE) --profile core up -d postgres

clean: ## Stop everything AND delete all volumes (all lakehouse data!)
	@read -p "Delete ALL containers and volumes? [y/N] " a && [ "$$a" = "y" ]
	$(COMPOSE) --profile "*" down -v
