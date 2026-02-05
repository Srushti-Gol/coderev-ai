.PHONY: dev build test migrate lint clean help

# Default target
help:
	@echo "coderev-ai Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  dev          Start all services in development mode"
	@echo "  build        Build all Docker images"
	@echo "  test         Run all tests"
	@echo "  migrate      Run database migrations"
	@echo "  lint         Run linters"
	@echo "  clean        Remove containers and volumes"
	@echo "  setup        Initial project setup"
	@echo "  logs         Tail all service logs"
	@echo "  shell-be     Open shell in backend container"
	@echo "  shell-db     Open psql in postgres container"

# Development
dev:
	docker-compose up --build

dev-bg:
	docker-compose up --build -d

# Build
build:
	docker-compose build

# Stop
stop:
	docker-compose down

# Clean
clean:
	docker-compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Testing
test:
	docker-compose run --rm backend pytest backend/tests/ -v

test-local:
	cd backend && pytest tests/ -v --asyncio-mode=auto

test-cov:
	docker-compose run --rm backend pytest backend/tests/ -v --cov=app --cov-report=html

# Database migrations
migrate:
	docker-compose run --rm backend alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	docker-compose run --rm backend alembic revision --autogenerate -m "$$name"

migrate-down:
	docker-compose run --rm backend alembic downgrade -1

# Linting
lint:
	cd backend && python -m flake8 app/ --max-line-length=100
	cd frontend && npm run lint

format:
	cd backend && python -m black app/
	cd backend && python -m isort app/

# Setup
setup:
	cp .env.example .env
	@echo "Please edit .env with your configuration"
	docker-compose build
	docker-compose run --rm backend alembic upgrade head
	cd frontend && npm install

setup-local:
	cp .env.example .env
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

# Utility
logs:
	docker-compose logs -f

logs-be:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f celery_worker

shell-be:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U coderev coderev_ai

# Frontend
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# Backend local dev
backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info
