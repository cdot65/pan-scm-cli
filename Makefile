.PHONY: ruff lint reinstall tests clean help

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
POETRY := poetry
SRC_DIR := src
RUFF := $(POETRY) run ruff
FLAKE8 := $(POETRY) run flake8
YAMLLINT := $(POETRY) run yamllint
PYTEST := $(POETRY) run pytest

# Colors for help target
YELLOW := \033[1;33m
NC := \033[0m # No Color

help:
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(YELLOW)ruff$(NC)        - Format Python code in src/ directory using ruff"
	@echo "  $(YELLOW)lint$(NC)        - Run flake8 and yamllint on src/ directory"
	@echo "  $(YELLOW)reinstall$(NC)   - Rebuild and reinstall the package in Poetry environment"
	@echo "  $(YELLOW)tests$(NC)       - Run pytest suite (TEMPORARILY DISABLED)"
	@echo "  $(YELLOW)clean$(NC)       - Remove build artifacts and cache files"

ruff:
	@echo "Formatting code with ruff..."
	$(RUFF) format $(SRC_DIR)
	$(RUFF) check --fix $(SRC_DIR)
	@echo "Formatting complete!"

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
	@echo "Tests are temporarily disabled. They will be reimplemented in a future update."
	@echo "Skipping test execution..."
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
	@echo "Cleanup complete!"
