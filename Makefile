.PHONY: help install dev api agent mcp web all stop infra db-migrate db-upgrade logs clean format lint fix check

# Default target
help:
	@echo "Pantry Pilot - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install all dependencies with uv"
	@echo "  make infra         - Start infrastructure (postgres, minio, ollama)"
	@echo ""
	@echo "Run Services (local):"
	@echo "  make api           - Run API server (port 8000)"
	@echo "  make agent         - Run Agent server (port 8002)"
	@echo "  make mcp           - Run MCP server (port 8001)"
	@echo "  make web           - Run Web UI (port 8080)"
	@echo "  make all           - Run all services (in background)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    - Create new migration"
	@echo "  make db-upgrade    - Run migrations"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build all Docker images"
	@echo "  make docker-up     - Start all services in Docker"
	@echo "  make docker-down   - Stop all Docker services"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs          - Tail logs from all services"
	@echo "  make stop          - Stop all local services"
	@echo "  make clean         - Clean up temp files and caches"
	@echo "  make test          - Run all tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make fix           - Auto-fix linting issues with ruff"
	@echo "  make check         - Run both format check and lint"

# ============== Setup ==============

install:
	@echo "📦 Installing dependencies..."
	uv sync
	@echo "✅ Dependencies installed"

infra:
	@echo "🚀 Starting infrastructure..."
	docker compose up -d postgres minio
	@echo "⏳ Waiting for services to be ready..."
	@sleep 3
	@echo "✅ Infrastructure ready"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   MinIO: localhost:9000 (console: localhost:9001)"

infra-ollama:
	@echo "🤖 Starting Ollama..."
	docker compose up -d ollama
	@echo "✅ Ollama started at localhost:11434"

# ============== Run Services ==============

api:
	@echo "🚀 Starting API server on port 8000..."
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

agent:
	@echo "🤖 Starting Agent server on port 8002..."
	cd apps/agent && uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

mcp:
	@echo "🔧 Starting MCP server on port 8001..."
	cd apps/mcp && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

web:
	@echo "🌐 Starting Web UI on port 8080..."
	cd apps/web && streamlit run app/main.py

queue:
	@echo "🌐 Starting request queue..."
	export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES && cd apps/queue && rq worker pantry-pilot --url redis://localhost:6379 -v

# Run all services in background
all: infra
	@echo "🚀 Starting all services..."
	@make api &
	@make mcp &
	@make agent &
	@echo "✅ All services started"
	@echo "   API: http://localhost:8000"
	@echo "   MCP: http://localhost:8001"
	@echo "   Agent: http://localhost:8002"

# ============== Database ==============

db-migrate:
	@echo "📝 Creating new migration..."
	@read -p "Migration message: " msg; \
	cd apps/api && alembic revision --autogenerate -m "$$msg"

db-upgrade:
	@echo "⬆️ Running migrations..."
	cd apps/api && alembic upgrade head
	@echo "✅ Migrations applied"

db-downgrade:
	@echo "⬇️ Rolling back migration..."
	cd apps/api && alembic downgrade -1
	@echo "✅ Rolled back one migration"

db-reset:
	@echo "🗑️ Resetting database..."
	cd apps/api && alembic downgrade base
	cd apps/api && alembic upgrade head
	@echo "✅ Database reset complete"

# ============== Docker ==============

docker-build:
	@echo "🔨 Building Docker images..."
	docker compose build
	@echo "✅ Images built"

docker-up:
	@echo "🚀 Starting all services in Docker..."
	docker compose up -d
	@echo "✅ Services started"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker compose down
	@echo "✅ Services stopped"

docker-logs:
	docker compose logs -f

# ============== Testing ==============

test:
	@echo "🧪 Running tests..."
	uv run pytest apps/ -v
	@echo "✅ Tests complete"

test-api:
	@echo "🧪 Running API tests..."
	cd apps/api && uv run pytest tests/ -v

test-agent:
	@echo "🧪 Running Agent tests..."
	cd apps/agent && uv run pytest tests/ -v

test-mcp:
	@echo "🧪 Running MCP tests..."
	cd apps/mcp && uv run pytest tests/ -v

# ============== Utilities ==============

logs:
	@echo "📜 Tailing logs (Ctrl+C to exit)..."
	@tail -f /tmp/pantry-pilot-*.log 2>/dev/null || echo "No log files found"

stop:
	@echo "🛑 Stopping all local services..."
	@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@echo "✅ Services stopped"

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# ============== Code Quality ==============

format:
	@echo "🎨 Formatting code with black..."
	uv run black apps/ packages/ --exclude="venv|env|.venv"
	@echo "✅ Code formatted"

format-check:
	@echo "🔍 Checking code format with black..."
	uv run black apps/ packages/ --check --exclude="venv|env|.venv"
	@echo "✅ Format check complete"

lint:
	@echo "🔍 Linting code with ruff..."
	uv run ruff check apps/ packages/
	@echo "✅ Lint complete"

fix:
	@echo "🔧 Auto-fixing linting issues with ruff..."
	uv run ruff check apps/ packages/ --fix
	@echo "✅ Auto-fix complete"

check: format-check lint
	@echo "✅ All checks passed"

# ============== Quick Start ==============

dev: infra db-upgrade
	@echo ""
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Run services in separate terminals:"
	@echo "  Terminal 1: make api"
	@echo "  Terminal 2: make mcp"
	@echo "  Terminal 3: make agent"
	@echo ""
	@echo "Or run all at once: make all"
