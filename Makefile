.PHONY: setup mypy flake8 format quality ruff lint reinstall tests clean help docs-install docs-serve docs-build docs-clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
POETRY := poetry
SRC_DIR := src
DOCS_DIR := docs-site
RUFF := $(POETRY) run ruff
FLAKE8 := $(POETRY) run flake8
YAMLLINT := $(POETRY) run yamllint
PYTEST := $(POETRY) run pytest
NPM := npm

# Colors for help target
YELLOW := \033[1;33m
GREEN := \033[0;32m
NC := \033[0m # No Color

setup:
	@echo "Installing dependencies..."
	$(POETRY) install
	@echo "Setup complete!"

mypy:
	@echo "Type checking with mypy..."
	$(POETRY) run mypy $(SRC_DIR)
	@echo "mypy complete!"

flake8:
	@echo "Running flake8..."
	$(POETRY) run flake8 $(SRC_DIR)
	@echo "flake8 complete!"

format:
	@echo "Formatting code with ruff (handles import sorting and formatting)..."
	$(POETRY) run ruff format $(SRC_DIR)
	$(POETRY) run ruff check --fix $(SRC_DIR)
	@echo "Formatting complete!"

quality:
	@echo "Running quality checks (lint, format, mypy, tests)..."
	$(MAKE) lint
	$(MAKE) format
	$(MAKE) mypy
	$(MAKE) tests
	@echo "All quality checks complete!"

help:
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(YELLOW)ruff$(NC)        - Format Python code in src/ directory using ruff"
	@echo "  $(YELLOW)lint$(NC)        - Run flake8 and yamllint on src/ directory"
	@echo "  $(YELLOW)reinstall$(NC)   - Rebuild and reinstall the package in Poetry environment"
	@echo "  $(YELLOW)tests$(NC)       - Run pytest suite"
	@echo "  $(YELLOW)clean$(NC)       - Remove build artifacts and cache files"
	@echo ""
	@echo "$(GREEN)Documentation targets (Docusaurus, in $(DOCS_DIR)/):$(NC)"
	@echo "  $(YELLOW)docs-install$(NC) - Install the Docusaurus site dependencies"
	@echo "  $(YELLOW)docs-serve$(NC)  - Serve the documentation site locally with hot reload"
	@echo "  $(YELLOW)docs-build$(NC)  - Build the documentation site (strict, broken links fail)"
	@echo "  $(YELLOW)docs-clean$(NC)  - Remove the Docusaurus build output"

ruff:
	@echo "Running ruff (formatting and linting with fixes)..."
	$(RUFF) format $(SRC_DIR)
	$(RUFF) check --fix $(SRC_DIR)
	@echo "Ruff complete!"

lint:
	@echo "Running flake8..."
	$(FLAKE8) $(SRC_DIR)
	@echo "Running yamllint..."
	$(YAMLLINT) examples/
	@echo "Linting complete!"

reinstall:
	@echo "Rebuilding and reinstalling package..."
	$(POETRY) build
	$(POETRY) install
	@echo "Reinstallation complete!"

tests:
	@echo "Running tests..."
	$(PYTEST) tests/ --ignore=tests/test_dynaconf_config.py --ignore=tests/test_sdk_client_with_dynaconf.py --ignore=tests/test_sdk_client.py
	@echo "Tests complete!"

clean:
	@echo "Cleaning up build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "htmlcov" -exec rm -rf {} +
	rm -rf docs-site/build docs-site/.docusaurus
	@echo "Cleanup complete!"

# Documentation targets (Docusaurus site in docs-site/)
docs-install:
	@echo "Installing documentation site dependencies..."
	cd $(DOCS_DIR) && $(NPM) install
	@echo "Documentation dependencies installed!"

docs-serve:
	@echo "Starting local documentation server..."
	cd $(DOCS_DIR) && $(NPM) start

docs-build:
	@echo "Building documentation site..."
	cd $(DOCS_DIR) && $(NPM) run build
	@echo "Documentation build complete!"

docs-clean:
	@echo "Cleaning documentation build output..."
	rm -rf $(DOCS_DIR)/build $(DOCS_DIR)/.docusaurus
	@echo "Documentation clean complete!"
