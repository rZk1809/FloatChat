# FloatChat — developer convenience targets
# Usage: make <target>

.PHONY: help install install-dev dev dev-backend dev-web \
        lint lint-py lint-web typecheck test test-py test-web \
        build docker-up docker-down clean

PYTHON  := python
PIP     := $(PYTHON) -m pip
NPM     := npm
UVICORN := uvicorn

help:
	@echo "FloatChat make targets"
	@echo ""
	@echo "  install        Install all dependencies (Python + Node)"
	@echo "  install-dev    Install with dev/test extras"
	@echo "  dev            Start both web and backend servers (background)"
	@echo "  dev-web        Start Next.js dev server  (localhost:3000)"
	@echo "  dev-backend    Start FastAPI dev server   (localhost:8000)"
	@echo "  lint           Run all linters"
	@echo "  lint-py        Run ruff on Python sources"
	@echo "  lint-web       Run ESLint on web sources"
	@echo "  typecheck      TypeScript type-check (no emit)"
	@echo "  test           Run all test suites"
	@echo "  test-py        Run pytest"
	@echo "  test-web       Run vitest"
	@echo "  build          Build the Next.js production bundle"
	@echo "  docker-up      Start full stack via docker-compose"
	@echo "  docker-down    Stop docker-compose services"
	@echo "  clean          Remove build artefacts and caches"

# ── Dependencies ─────────────────────────────────────────────────────────────

install:
	$(PIP) install -e ".[all]"
	cd web && $(NPM) ci

install-dev:
	$(PIP) install -e ".[dev,test,lint,type]"
	cd web && $(NPM) ci

# ── Dev servers ──────────────────────────────────────────────────────────────

dev-web:
	cd web && $(NPM) run dev

dev-backend:
	$(UVICORN) agentic_workflow.api:app --host 0.0.0.0 --port 8000 --reload

# ── Linting ──────────────────────────────────────────────────────────────────

lint-py:
	$(PYTHON) -m ruff check agentic_workflow tests scripts

lint-web:
	cd web && $(NPM) run lint

lint: lint-py lint-web

# ── Type checking ─────────────────────────────────────────────────────────────

typecheck:
	cd web && $(NPM) run typecheck

# ── Tests ────────────────────────────────────────────────────────────────────

test-py:
	$(PYTHON) -m pytest tests/ -v

test-web:
	cd web && $(NPM) run test

test: test-py test-web

# ── Build ────────────────────────────────────────────────────────────────────

build:
	cd web && $(NPM) run build

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

# ── Clean ────────────────────────────────────────────────────────────────────

clean:
	rm -rf web/.next web/out web/node_modules/.cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
