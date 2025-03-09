# SCM CLI Project Documentation

## Overview

The SCM CLI is a command-line interface for Palo Alto Networks Security Content Management (SCM). It provides a network engineer-friendly way to interact with the SCM API, using familiar command-line syntax similar to network device CLIs like Junos.

## Project Structure

The project is organized in a modular structure inspired by Go project organization:

```
scm_cli/
├── cli/                  # Command-line interface modules
│   ├── main.py           # Main CLI module
│   ├── object/           # Object-related commands
│   │   ├── address_object/    # Address object commands
│   │   └── address_group/     # Address group commands
│   └── network/          # Network-related commands
│       └── interface/    # Interface commands
├── utils/                # Utility modules
│   ├── config.py         # Configuration management
│   ├── db.py             # Database handling for command history
│   ├── mock_sdk.py       # Mock SDK for testing
│   └── sdk_client.py     # SDK client abstraction layer
├── models/               # Data models
├── examples/             # Example scripts and usage
└── docs/                 # Documentation
```

## Module Documentation

- [cli.md](cli.md) - Documentation for the main CLI module
- [config.md](config.md) - Documentation for the configuration module
- [db.md](db.md) - Documentation for the database module
- [sdk_client.md](sdk_client.md) - Documentation for the SDK client module
- [mock_sdk.md](mock_sdk.md) - Documentation for the mock SDK module

## Architecture

The SCM CLI is built on a layered architecture that separates concerns:

1. **CLI Layer**: The top-level user interface that handles command parsing and display
2. **Command Modules**: Specific command implementations grouped by function
3. **SDK Client Layer**: Abstracts the Palo Alto Networks SCM SDK
4. **Utility Layer**: Provides supporting functionality like configuration and history tracking

## Command Module Design

Each command module follows a consistent pattern:

1. A core commands class that implements the functionality
2. Clear separation between command parsing and execution
3. Integration with the main CLI via well-defined interfaces

This structure allows for:
- Easy addition of new command modules
- Independent testing of command functionality
- Clear separation of concerns