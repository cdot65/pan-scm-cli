# SCM CLI Package

This package provides the core functionality for the Palo Alto Networks SCM CLI. It's organized into several modules, each handling a specific aspect of the CLI's functionality.

## Module Overview

- **cli.py**: Main CLI interface and command handling based on cmd2
- **config.py**: Configuration and credentials management
- **db.py**: SQLite database for command history tracking
- **sdk_client.py**: Abstraction layer between the CLI and the Palo Alto Networks SCM SDK
- **mock_sdk.py**: Mock implementation of the SCM SDK for testing purposes

## Dependencies

The SCM CLI depends on several external libraries:

- **cmd2**: Provides the base for the interactive command shell
- **rich**: Terminal formatting and pretty-printing
- **python-dotenv**: Loading environment variables from .env files
- **pyyaml**: YAML parsing
- **pan-scm-sdk**: The official Palo Alto Networks SCM SDK

## Package Entry Point

The main entry point for the package is the `main()` function in `cli.py`, which is registered as the `scm-cli` command in the `pyproject.toml` file.