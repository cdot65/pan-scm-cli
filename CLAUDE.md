# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CLI tool for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations. It provides commands to manage addresses, address groups, security zones, security rules, and bandwidth allocations through a consistent interface.

## Development Commands

### Setup and Build

```bash
make setup              # Install dependencies and pre-commit hooks
make reinstall          # Rebuild and reinstall the package locally
```

### Code Quality

```bash
make lint               # Run flake8 and yamllint
make format             # Format code with ruff
make fix                # Auto-fix linting issues with ruff
make quality            # Run all quality checks (lint, format, mypy, tests)
```

### Testing

```bash
make tests              # Run pytest suite
pytest tests/test_specific.py::test_name  # Run a single test
pytest -v               # Run with verbose output
```

### Documentation

```bash
make docs-serve         # Serve docs locally on port 8000
make docs-build         # Build docs with strict checks
```

## Architecture

### Command Structure

The CLI follows a consistent pattern: `scm-cli <action> <object-type> <object> [options]`

Commands are organized by resource type:

- `commands/objects.py`: Address and address group management
- `commands/network.py`: Security zone management
- `commands/security.py`: Security rule management
- `commands/deployment.py`: Bandwidth allocation management

### Key Components

- `client.py`: Initializes SCM client (real or mock mode)
- `utils/sdk_client.py`: Wrapper around pan-scm-sdk with error handling
- `utils/validators.py`: Pydantic models for input validation
- `utils/config.py`: Dynaconf-based configuration management

### Authentication Flow

1. Check environment variables: `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`
2. Fall back to home config: `~/.scm-cli/config.yaml`
3. Fall back to local config: `.secrets.yaml` (development only)
4. If no credentials found, automatically use mock mode

### Adding New Commands

1. Create/update the appropriate command module in `src/scm_cli/commands/`
2. Add Pydantic validator models in `utils/validators.py` if needed
3. Register the command in `main.py`
4. Add corresponding tests in `tests/`
5. Update documentation in `docs/cli/`

### Testing Patterns

- Tests automatically use mock credentials via `mock_dynaconf_settings` fixture
- Use `mock_scm_client` fixture for API testing without real calls
- Test data fixtures are in `tests/data/`
- Environment-specific tests check auth/config behavior

## Code Style and Standards

**IMPORTANT**: All code in this project must follow the comprehensive style guides located in the `.claude/` directory:

### General Style Guide (`.claude/STYLE_GUIDE.md`)
Covers patterns for command modules and general project standards:
- Module structure and section organization with 192-character separators
- Command architecture patterns for Typer apps
- Documentation standards (Google format docstrings)
- Error handling patterns
- Type annotation conventions (Python 3.10+ syntax)
- Naming conventions for commands, functions, and variables
- Output formatting standards

### SDK Client Style Guide (`.claude/SDK_CLIENT_STYLE_GUIDE.md`)
Specific patterns for `src/scm_cli/utils/sdk_client.py`:
- SDK client class design and initialization
- Method organization by configuration type
- CRUD method patterns (create, get, list, delete)
- Mock mode support with realistic data
- Error handling with `_handle_api_exception`
- Logging standards and levels
- SDK field mapping and data transformation

### Validators Style Guide (`.claude/VALIDATORS_STYLE_GUIDE.md`)
Specific patterns for `src/scm_cli/utils/validators.py`:
- Pydantic model design patterns
- Field definitions with proper constraints
- Model validation patterns
- SDK model conversion with `to_sdk_model()`
- Utility functions for YAML validation
- Type definitions and generic types

Always refer to the appropriate style guide when writing or modifying code to ensure consistency across the codebase.

## Important Notes

- The SDK version is pinned to `pan-scm-sdk==0.3.39` - verify compatibility when updating
- Mock mode allows full testing without API credentials
- Bulk operations use YAML files - see `examples/` for formats
- All commands support `--mock` flag for testing
- Documentation uses MkDocs Material with custom Termynal integration for CLI examples
