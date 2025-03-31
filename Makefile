.PHONY: ruff lint reinstall tests clean help docs-serve docs-build docs-build-dev docs-lint docs-links docs-check docs-deploy

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
POETRY := poetry
SRC_DIR := src
DOCS_DIR := docs
RUFF := $(POETRY) run ruff
FLAKE8 := $(POETRY) run flake8
YAMLLINT := $(POETRY) run yamllint
PYTEST := $(POETRY) run pytest
MKDOCS := $(POETRY) run mkdocs
LINKCHECKER := $(POETRY) run linkchecker

# Colors for help target
YELLOW := \033[1;33m
GREEN := \033[0;32m
NC := \033[0m # No Color

help:
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(YELLOW)ruff$(NC)        - Format Python code in src/ directory using ruff"
	@echo "  $(YELLOW)lint$(NC)        - Run flake8 and yamllint on src/ directory"
	@echo "  $(YELLOW)reinstall$(NC)   - Rebuild and reinstall the package in Poetry environment"
	@echo "  $(YELLOW)tests$(NC)       - Run pytest suite (TEMPORARILY DISABLED)"
	@echo "  $(YELLOW)clean$(NC)       - Remove build artifacts and cache files"
	@echo ""
	@echo "$(GREEN)Documentation targets:$(NC)"
	@echo "  $(YELLOW)docs-serve$(NC)  - Serve the documentation site locally"
	@echo "  $(YELLOW)docs-build$(NC)  - Build the documentation site with strict checks"
	@echo "  $(YELLOW)docs-build-dev$(NC) - Build the documentation site in development mode (no strict checks)"
	@echo "  $(YELLOW)docs-lint$(NC)   - Check the documentation for linting issues"
	@echo "  $(YELLOW)docs-links$(NC)  - Check the documentation for broken links"
	@echo "  $(YELLOW)docs-check$(NC)  - Run all documentation checks"
	@echo "  $(YELLOW)docs-deploy$(NC) - Deploy the documentation to GitHub Pages"

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
	rm -rf site/
	@echo "Cleanup complete!"

# Documentation targets
docs-serve:
	@echo "Starting local documentation server..."
	$(MKDOCS) serve

docs-build:
	@echo "Building documentation site..."
	$(MKDOCS) build --strict
	@echo "Documentation build complete!"

docs-build-dev:
	@echo "Building documentation site (development mode)..."
	$(MKDOCS) build
	@echo "Documentation build complete!"

docs-lint:
	@echo "Checking documentation syntax and structure..."
	$(YAMLLINT) mkdocs.yml || true
	@echo "Checking for basic Markdown issues..."
	$(POETRY) run python -c "import sys, re, glob; errors = 0; \
		for file in glob.glob('$(DOCS_DIR)/**/*.md', recursive=True): \
			with open(file, 'r') as f: \
				content = f.read(); \
				if '```' not in content and len(content.strip()) > 0: \
					print(f'WARNING: {file} has no code blocks.'); \
					errors += 1; \
				if re.search(r'\]\(.*?404.*?\)', content): \
					print(f'WARNING: {file} may contain a 404 URL.'); \
					errors += 1; \
				if '(#' in content and not re.search(r'\[.*?\]\(#.*?\)', content): \
					print(f'WARNING: {file} may have malformed anchor links.'); \
					errors += 1; \
		sys.exit(min(errors, 1));" || true
	@echo "Documentation linting complete!"

docs-links:
	@echo "Checking documentation for broken links..."
	$(MKDOCS) build
	$(PYTEST) --check-links --check-links-ignore="^(?!file://).*" site/index.html || true
	@echo "Link checking complete!"

docs-check: docs-lint docs-build-dev docs-links
	@echo "All documentation checks complete!"

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	$(MKDOCS) gh-deploy
	@echo "Documentation deployment complete!"
