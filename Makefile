.PHONY: help install test run build docker-build docker-run docker-stop clean lint format mock-start mock-stop mock-status mock-logs

# Variables
PYTHON := python
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
DOCKER_IMAGE := halcytone-content-generator
DOCKER_TAG := latest

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

test: ## Run tests with coverage
	$(PYTEST) tests/ --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v

run: ## Run the application locally
	$(PYTHON) run_dev.py

run-prod: ## Run the application in production mode
	uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000

lint: ## Run code linting
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m pylint src/
	$(PYTHON) -m mypy src/

format: ## Format code with black
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Run Docker container
	docker-compose -f docker-compose.dev.yml up

docker-run-prod: ## Run production Docker stack
	docker-compose up -d

docker-stop: ## Stop Docker containers
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

docker-logs: ## Show Docker logs
	docker-compose logs -f content-generator

docker-shell: ## Open shell in Docker container
	docker exec -it halcytone-content-gen-dev /bin/bash

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

migrate: ## Run database migrations (if applicable)
	alembic upgrade head

generate-migration: ## Generate a new migration
	alembic revision --autogenerate -m "$(MSG)"

api-docs: ## Generate API documentation
	$(PYTHON) -m mkdocs build

api-docs-serve: ## Serve API documentation locally
	$(PYTHON) -m mkdocs serve

requirements: ## Update requirements.txt
	$(PIP) freeze > requirements.txt

security-check: ## Run security checks
	$(PYTHON) -m bandit -r src/
	$(PYTHON) -m safety check

performance-test: ## Run performance tests
	locust -f tests/performance/locustfile.py --host=http://localhost:8000

monitoring-start: ## Start monitoring stack
	docker-compose up -d prometheus grafana jaeger

monitoring-stop: ## Stop monitoring stack
	docker-compose stop prometheus grafana jaeger

redis-cli: ## Connect to Redis CLI
	docker exec -it halcytone-redis-dev redis-cli

db-shell: ## Connect to database shell
	docker exec -it halcytone-postgres psql -U contentuser -d content_db

backup: ## Backup data and logs
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/ logs/

restore: ## Restore from backup (BACKUP=filename)
	tar -xzf $(BACKUP)

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add staging deployment commands

deploy-production: ## Deploy to production environment
	@echo "Deploying to production..."
	# Add production deployment commands

# Mock Services Management
mock-start: ## Start mock services for development/testing
	@echo "Starting mock services..."
	$(PYTHON) scripts/start_mock_services.py

mock-stop: ## Stop mock services
	@echo "Stopping mock services..."
	docker-compose -f docker-compose.mocks.yml down

mock-status: ## Check mock service status and health
	@echo "Mock service status:"
	@docker-compose -f docker-compose.mocks.yml ps
	@echo "\nHealth checks:"
	@curl -s http://localhost:8001/health >/dev/null && echo "✓ CRM Service (8001) - Healthy" || echo "✗ CRM Service (8001) - Unhealthy"
	@curl -s http://localhost:8002/health >/dev/null && echo "✓ Platform Service (8002) - Healthy" || echo "✗ Platform Service (8002) - Unhealthy"

mock-logs: ## View mock service logs
	@echo "Mock service logs (press Ctrl+C to exit):"
	docker-compose -f docker-compose.mocks.yml logs -f

mock-rebuild: ## Rebuild mock service containers
	@echo "Rebuilding mock services..."
	docker-compose -f docker-compose.mocks.yml build --no-cache
	docker-compose -f docker-compose.mocks.yml up -d

mock-clean: ## Clean mock services (stop + remove containers)
	@echo "Cleaning mock services..."
	docker-compose -f docker-compose.mocks.yml down --rmi all --volumes --remove-orphans

test-contracts: ## Run API contract tests with mock services
	@echo "Running API contract tests..."
	$(MAKE) mock-start
	$(PYTEST) tests/contracts/ -v
	@echo "Contract tests completed"