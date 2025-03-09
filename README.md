# Palo Alto Networks SCM CLI

A network engineer-friendly command-line interface (CLI) for Palo Alto Networks Security Content Management (SCM).

This project provides a familiar Junos-style CLI experience for interacting with the Palo Alto Networks SCM API, making it more accessible for network engineers who are used to traditional CLI interfaces.

## Architecture Overview

The SCM CLI is built with a layered architecture that separates concerns and provides flexibility:

![Architecture Diagram](architecture.png)

1. **CLI Layer (`cli.py`)**: Handles user input, command parsing, and display
2. **SDK Client Layer (`sdk_client.py`)**: Abstracts the Palo Alto Networks SCM SDK
3. **Configuration Layer (`config.py`)**: Manages credentials and settings
4. **Database Layer (`db.py`)**: Stores command history in SQLite
5. **Underlying SDK**: Communicates with the Palo Alto Networks SCM API

## Key Features

- **Familiar CLI Syntax**: Junos-style commands with keyword-based arguments
- **Context-Sensitive Help**: Use `?` anywhere to get context-specific help
- **Tab Completion**: Quickly complete commands, folder names, and object names
- **Command History**: Track and search command history stored in SQLite
- **Partial Updates**: Update specific fields of existing objects without re-specifying everything
- **Rich Terminal Output**: Colorized, formatted output with tables and JSON
- **Authentication**: OAuth2 authentication with the SCM API
- **Typed API Client**: Type-annotated SDK client for better code quality
- **Performance Monitoring**: Built-in performance tracking for operations

## Requirements

- Python 3.12.9 (managed with pyenv)
- Poetry for dependency management

## Installation

```bash
# Install dependencies
poetry install

# Copy the example .env file and modify with your credentials
cp .env.example .env
nano .env  # Edit with your credentials

# Run the CLI
poetry run scm-cli
```

## Authentication

The SCM CLI requires OAuth credentials to authenticate with the SCM API. These credentials must be provided in a `.env` file in the current directory with the following format:

```
SCM_CLIENT_ID=your_client_id_here
SCM_CLIENT_SECRET=your_client_secret_here
SCM_TSG_ID=your_tsg_id_here
```

You can also specify optional settings:

```
SCM_BASE_URL=https://api.strata.paloaltonetworks.com
SCM_VERIFY_SSL=true
```

## Basic Usage

Start the CLI with credentials from the `.env` file:

```bash
poetry run scm-cli
```

### Navigation and Mode Commands

- `configure` - Enter configuration mode
- `edit folder <folder-name>` - Edit a specific folder
- `exit` - Exit current mode or the CLI
- `quit` - Exit the CLI

### Address Object Commands

- `set address-object name <n> type <type> value <value> [description <text>] [tags <tags>]` - Create/update an address object
- `show address-object <n>` - Display address object details
- `show address-object` - List all address objects in current folder
- `show address-objects-filter [--name <n>] [--type <type>] [--value <val>] [--tag <tag>]` - Search and filter address objects
- `delete address-object <n>` - Delete an address object

### History Command

- `history` - Show the last 50 commands (default)
- `history --page <n>` - Navigate between pages of history
- `history --limit <n>` - Change how many commands are shown per page
- `history --folder <folder>` - Filter history by folder
- `history --filter <text>` - Filter history by command content
- `history --id <n>` - Show details of a specific history entry, including command output
- `history --clear` - Clear the command history

### Getting Help

There are several ways to get help in the SCM CLI:

1. **Command help**: Type `help` to see all available commands, or `help <command>` to see detailed help for a specific command.

2. **Question mark at end of command**: Type a command followed by a question mark to show help for that command. 
   ```
   scm> configure?
   ```

3. **Inline question mark**: Type a partial command with a question mark to get context-sensitive help for the current position.
   ```
   scm> set ?
   Available object types:
     address-object - Configure an address object
   ```

4. **Tab completion**: Press TAB to auto-complete commands, arguments, and values.

## Detailed Example Session

```
$ scm-cli
Entering SCM CLI
✅ Client initialized successfully

# ----------------------------------------------------------------------------
# Welcome to the SCM CLI for Strata Cloud Manager
# ----------------------------------------------------------------------------
developer@scm> configure
developer@scm# edit folder Texas
developer(Texas)# set address-object name test123 type ip-netmask value 1.1.1.1/32 description "Test address" tags "Automation,Python"
✅ - created address-object test123
developer(Texas)# show address-object test123
{
  "name": "test123",
  "type": "ip-netmask",
  "value": "1.1.1.1/32",
  "description": "Test address",
  "tags": ["Automation", "Python"]
}
developer(Texas)# set address-object name test123 description "Updated description"
✅ - updated address-object test123
developer(Texas)# show address-objects-filter --type ip-netmask
Address Objects in Texas (filtered by type='ip')
┌─────────┬────────────┬───────────┬─────────────────────┬───────────────────┐
│ Name    │ Type       │ Value     │ Description         │ Tags              │
├─────────┼────────────┼───────────┼─────────────────────┼───────────────────┤
│ test123 │ ip-netmask │ 1.1.1.1/32│ Updated description │ Automation, Python│
└─────────┴────────────┴───────────┴─────────────────────┴───────────────────┘
developer(Texas)# delete address-object test123
✅ - deleted address-object test123
developer(Texas)# exit
developer@scm# exit
```

## Development

This project uses:
- Poetry for dependency management
- Black for code formatting
- isort for import sorting
- mypy for type checking
- pytest for testing
- cmd2 for the interactive shell with tab completion
- rich for terminal formatting
- python-dotenv for loading environment variables

### Development Commands

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy .

# Linting
poetry run flake8 .
```

## Project Structure

```
pan-scm-cli/
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # Project documentation (this file)
├── src/
│   └── scm_cli/           # Main package directory
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # CLI implementation and command handling
│       ├── config.py      # Configuration management
│       ├── db.py          # Database interface for command history
│       ├── mock_sdk.py    # Mock SDK for testing
│       └── sdk_client.py  # SDK client abstraction layer
└── tests/                 # Test directory
    ├── __init__.py
    ├── test_cli.py        # CLI tests
    └── test_config.py     # Configuration tests
```

## Under the Hood

The SCM CLI is built on the following key components:

1. **cmd2**: Extends Python's built-in cmd module with additional features like tab completion, colorization, and more complex command handling.

2. **rich**: Provides rich text and beautiful formatting in the terminal, including tables, panels, and syntax highlighting.

3. **python-dotenv**: Loads environment variables from .env files for configuration.

4. **SQLite**: Stores command history in a local database file.

5. **pan-scm-sdk**: The official Palo Alto Networks SDK for interacting with the SCM API.

## License

[TBD]

## Contributing

[TBD]