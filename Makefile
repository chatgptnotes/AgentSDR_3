.PHONY: help install dev test lint clean seed docker-build docker-run docker-stop celery worker beat redis flower build all

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	./venv/bin/pip install -r requirements.txt

dev: ## Run development server
	FLASK_ENV=development ./venv/bin/python app.py

test: ## Run tests with coverage
	./venv/bin/pytest tests/ -v --cov=agentsdr --cov-report=html --cov-report=term

lint: ## Run linting and formatting
	./venv/bin/black agentsdr/ tests/ --check
	./venv/bin/ruff check agentsdr/ tests/

format: ## Format code
	./venv/bin/black agentsdr/ tests/
	./venv/bin/ruff check --fix agentsdr/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/
	rm -rf .pytest_cache/
	rm -rf celerybeat-schedule

seed: ## Seed database with demo data
	./venv/bin/python scripts/seed.py

# Redis & Celery commands
redis: ## Start Redis server
	@echo "Starting Redis server on port 6379..."
	@redis-server --daemonize yes || echo "Redis already running or not installed. Install with: brew install redis"

redis-stop: ## Stop Redis server
	@redis-cli shutdown || echo "Redis not running"

redis-status: ## Check Redis status
	@redis-cli ping || echo "Redis not running"

worker: ## Start Celery worker
	@echo "Starting Celery worker..."
	./venv/bin/celery -A agentsdr.celery_config.celery_app worker --loglevel=info

beat: ## Start Celery beat scheduler
	@echo "Starting Celery beat scheduler..."
	./venv/bin/celery -A agentsdr.celery_config.celery_app beat --loglevel=info

flower: ## Start Flower monitoring dashboard
	@echo "Starting Flower on http://localhost:5555"
	./venv/bin/celery -A agentsdr.celery_config.celery_app flower --port=5555

celery: ## Start Celery worker and beat together
	@echo "Starting Celery worker and beat..."
	@make redis
	@./venv/bin/celery -A agentsdr.celery_config.celery_app worker --beat --loglevel=info

# Build commands
build: ## Build production assets
	@echo "Building production assets..."
	@mkdir -p logs
	@echo "Build complete!"

all: ## Start all services (Redis, Flask, Celery)
	@echo "Starting all services..."
	@make redis
	@echo "Starting Flask in background..."
	@FLASK_ENV=development ./venv/bin/python app.py &
	@sleep 2
	@echo "Starting Celery worker in background..."
	@./venv/bin/celery -A agentsdr.celery_config.celery_app worker --beat --loglevel=info --detach
	@echo "All services started! Flask: http://localhost:5001"

stop-all: ## Stop all background services
	@echo "Stopping all services..."
	@pkill -f "python app.py" || echo "Flask not running"
	@pkill -f "celery worker" || echo "Celery not running"
	@make redis-stop
	@echo "All services stopped"

# Docker commands
docker-build: ## Build Docker image
	docker-compose build

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

# Setup commands
setup: ## Initial setup
	@echo "Setting up InboxAI..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please update .env with your credentials"; \
	fi
	@echo "Installing dependencies..."
	@make install
	@mkdir -p logs
	@echo "✅ Setup complete! Update .env and run 'make all' to start all services"

deploy-check: ## Check deployment readiness
	@echo "Checking deployment requirements..."
	@./venv/bin/python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
		required = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'FLASK_SECRET_KEY', 'OPENAI_API_KEY', 'REDIS_URL']; \
		missing = [k for k in required if not os.getenv(k)]; \
		print('❌ Missing environment variables:', missing) if missing else print('✅ All required env vars set')"

# Version increment
version-bump: ## Increment version number
	@echo "Current version: $$(grep 'APP_VERSION' .env | cut -d'=' -f2)"
	@read -p "Enter new version: " version; \
	sed -i.bak "s/APP_VERSION=.*/APP_VERSION=$$version/" .env && rm .env.bak
	@echo "Version updated to: $$(grep 'APP_VERSION' .env | cut -d'=' -f2)"
