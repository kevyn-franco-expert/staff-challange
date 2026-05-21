# Golden Path Platform — Enterprise DevEx Framework
# =================================================
.PHONY: all install test lint build docs clean

all: install test build

# =============================================================================
# Install
# =============================================================================
install: install-cli install-framework

install-cli:
	@echo "Installing Python CLI..."
	cd packages/goldenpath-cli && uv pip install -e ".[dev]"

install-framework:
	@echo "Installing TypeScript Framework..."
	cd packages/goldenpath-framework && pnpm install

# =============================================================================
# Test
# =============================================================================
test: test-cli test-framework

test-cli:
	@echo "Running CLI tests..."
	cd packages/goldenpath-cli && uv run pytest tests/ -v --cov=goldenpath_cli --cov-report=term-missing

test-framework:
	@echo "Running Framework tests..."
	cd packages/goldenpath-framework && pnpm test

# =============================================================================
# Lint
# =============================================================================
lint: lint-cli lint-framework

lint-cli:
	@echo "Linting Python CLI..."
	cd packages/goldenpath-cli && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run mypy src/

lint-framework:
	@echo "Linting TypeScript Framework..."
	cd packages/goldenpath-framework && pnpm lint

# =============================================================================
# Build
# =============================================================================
build: build-cli build-framework

build-cli:
	@echo "Building Python CLI..."
	cd packages/goldenpath-cli && uv build

build-framework:
	@echo "Building TypeScript Framework..."
	cd packages/goldenpath-framework && pnpm build

# =============================================================================
# Documentation
# =============================================================================
docs:
	@echo "Building documentation..."
	cd docs && mkdir -p output && \
	pandoc ADR.md -o output/ADR.pdf --pdf-engine=weasyprint || \
	echo "Install pandoc+weasyprint to generate PDF. Markdown ADR is available at docs/ADR.md"

# =============================================================================
# Clean
# =============================================================================
clean:
	@echo "Cleaning artifacts..."
	cd packages/goldenpath-cli && rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	cd packages/goldenpath-framework && rm -rf dist/ node_modules/ *.tsbuildinfo
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -delete 2>/dev/null || true
