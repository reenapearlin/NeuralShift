SHELL := /bin/bash
ROOT := $(shell pwd)
DOCKER_BIN := $(shell command -v docker 2>/dev/null || true)
ifeq ($(DOCKER_BIN),)
DOCKER_BIN := /Applications/Docker.app/Contents/Resources/bin/docker
endif

.PHONY: help setup infra-up infra-down infra-logs ollama-pull-models migrate backend frontend dev

help:
	@echo "Available targets:"
	@echo "  make setup              - Install backend/frontend dependencies and prepare .env"
	@echo "  make infra-up           - Start PostgreSQL and Ollama using docker-compose"
	@echo "  make infra-down         - Stop docker-compose infrastructure"
	@echo "  make infra-logs         - Tail docker-compose logs"
	@echo "  make ollama-pull-models - Pull configured Ollama models"
	@echo "  make migrate            - Run Alembic migrations"
	@echo "  make backend            - Start FastAPI backend"
	@echo "  make frontend           - Start Vite frontend"
	@echo "  make dev                - Start backend and frontend (requires 2 terminals/process manager)"

setup:
	@bash scripts/bootstrap.sh
	@chmod +x scripts/*.sh

infra-up:
	@if [ ! -x "$(DOCKER_BIN)" ]; then \
		echo "Docker CLI not found. Install Docker Desktop first."; \
		exit 1; \
	fi
	@$(DOCKER_BIN) compose up -d

infra-down:
	@$(DOCKER_BIN) compose down

infra-logs:
	@$(DOCKER_BIN) compose logs -f

ollama-pull-models:
	@bash scripts/pull_ollama_models.sh

migrate:
	@cd backend && ../.venv/bin/alembic upgrade head

backend:
	@bash scripts/run_backend.sh

frontend:
	@bash scripts/run_frontend.sh

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"
