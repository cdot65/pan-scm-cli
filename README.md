# SCM CLI

A proof-of-concept CLI for Palo Alto Networks Strata Cloud Manager (SCM).

This command-line interface provides a network-engineer-friendly way to interact with the SCM API, with familiar command style and patterns.

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

When the CLI starts, it will automatically load these credentials, authenticate with the SCM API, and display a success message if authentication is successful.

## Features

- CLI experience with auto-completion and help syntax
- Tab completion for commands and arguments
- Context-sensitive help with `?` anywhere in the command
- Interactive hints and guidance during command entry
- SDK integration for CRUD operations
- Rich terminal output with colors and formatting
- Address object management
- OAuth authentication

## Usage

Start the CLI with credentials from the `.env` file:

```bash
poetry run scm-cli
```

### Navigation Commands

- `configure` - Enter configuration mode
- `edit folder <folder-name>` - Edit a specific folder
- `exit` - Exit current mode or the CLI
- `quit` - Exit the CLI

### Address Object Commands

- `set address-object <name> <type> <value> [description <text>] [tags <tags>]` - Create/update an address object
- `show address-object <name>` - Display address object details
- `show address-objects` - List all address objects in current folder
- `delete address-object <name>` - Delete an address object

### Address Object Types

The following address object types are supported:

- `ip-netmask` - IP address with netmask (e.g., 192.168.1.0/24)
- `ip-range` - IP address range (e.g., 192.168.1.1-192.168.1.10)
- `ip-wildcard` - IP address with wildcard mask (e.g., 192.168.1.0/0.0.0.255)
- `fqdn` - Fully qualified domain name (e.g., example.com)

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

### Example Session

```
$ scm-cli
Entering SCM CLI
✅ Client initialized successfully

# ----------------------------------------------------------------------------
# Welcome to the SCM CLI for Strata Cloud Manager
# ----------------------------------------------------------------------------
developer@scm> configure
developer@scm# edit folder Texas
developer(Texas)# set ?
Available object types:
  address-object - Configure an address object

developer(Texas)# set address-object ?
Syntax: set address-object <name> <type> <value> [description <text>] [tags <tag1,tag2,...>]

Required arguments:
  <name>      - Name of the address object
  <type>      - Type of address object (ip-netmask, ip-range, ip-wildcard, fqdn)
  <value>     - Value of the address object

Optional arguments:
  description - Description of the address object
  tags        - Comma-separated list of tags

developer(Texas)# set address-object Test123 ip-netmask 1.1.1.1/32 description "Test address" tags "Automation,Python"
Created address object: Test123
developer(Texas)# show address-object Test123
{
  "name": "Test123",
  "type": "ip-netmask",
  "value": "1.1.1.1/32",
  "description": "Test address",
  "tags": ["Automation", "Python"]
}
developer(Texas)# exit
developer@scm# exit
$
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