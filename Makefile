# Email Sender CLI - Development Makefile

.PHONY: help install test test-unit test-integration test-cli test-coverage test-fast test-all clean lint format check docs

# Default target
help:
	@echo "Email Sender CLI - Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install dependencies and package in development mode"
	@echo "  install-test     Install test dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run quick tests (unit tests only)"
	@echo "  test-unit        Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-cli         Run CLI tests"
	@echo "  test-fast        Run fast tests (exclude slow tests)"
	@echo "  test-all         Run all tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code"
	@echo "  check            Run all quality checks"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up generated files"
	@echo "  docs             Generate documentation"

# Installation
install:
	uv sync

install-test:
	uv sync --extra test

# Testing
test:
	uv run python run_tests.py --type fast

test-unit:
	uv run pytest -m "unit" tests/ -v

test-integration:
	uv run pytest -m "integration" tests/ -v

test-cli:
	uv run pytest -m "cli" tests/ -v

test-fast:
	uv run pytest -m "not slow" tests/ -v

test-all:
	uv run pytest tests/ -v

test-coverage:
	uv run python run_tests.py --coverage --html-report

# Code Quality
lint:
	uv run ruff check .

format:
	uv run ruff format .

check: lint
	uv run ruff format --check .
	@echo "✅ All quality checks passed!"

# Utilities
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:
	@echo "📚 Documentation available in README.md"
	@echo "🔗 Run 'email-sender --help' for CLI help"

# Development workflow
dev-setup: install-test
	@echo "🚀 Development environment ready!"
	@echo "   Run 'make test' to run tests"
	@echo "   Run 'make check' for code quality"
	@echo "   Run 'email-sender --help' to test CLI"

# CI/CD targets
ci-test: install-test test-coverage check
	@echo "✅ CI pipeline completed successfully!"
