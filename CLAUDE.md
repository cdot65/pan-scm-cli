# PAN SCM CLI - Development Guidelines

## Environment & Setup
- Python: 3.12.9 (managed via pyenv)
- Package Manager: Poetry

## Commands
- Install dependencies: `poetry install`
- Run CLI: `poetry run scm-cli`
- Run tests: `poetry run pytest`
- Run single test: `poetry run pytest tests/test_file.py::test_function -v`
- Lint: `poetry run flake8 .`
- Type check: `poetry run mypy .`
- Format code: `poetry run black .`
- Sort imports: `poetry run isort .`

## Code Style
- Follow PEP 8 and use Black for formatting
- Max line length: 88 characters
- Use type annotations everywhere
- Snake_case for variables/functions, PascalCase for classes
- Group imports: stdlib → third-party → local
- Use f-strings for string formatting
- Prefer explicit error handling with try/except
- Document public functions with docstrings (Google style)
- Prefix private methods with underscore
- Use dataclasses for data containers