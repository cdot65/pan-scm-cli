# cli.py - SCM CLI Interface Module

## Overview

The `cli.py` module is the heart of the SCM CLI application, providing the interactive command-line interface that users interact with. It's responsible for:

1. Command handling and parsing
2. Context-sensitive help and tab completion
3. Command execution and output formatting
4. State management and mode transitions
5. Interactive user experience

## Key Components

### SCMState Dataclass

The `SCMState` dataclass represents the current state of the CLI, including:

- Configuration mode status
- Current folder context
- SDK client instance
- Authentication information
- Known folders and address objects (for autocomplete)
- History database connection

```python
@dataclass
class SCMState:
    config_mode: bool = False
    current_folder: Optional[str] = None
    sdk_client: Optional[SDKClient] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    known_folders: Set[str] = field(default_factory=set)
    known_address_objects: Dict[str, Set[str]] = field(default_factory=dict)
    history_db: CLIHistoryDB = field(default_factory=lambda: CLIHistoryDB())
```

### SCMCLI Class

The main `SCMCLI` class extends the `cmd2.Cmd` class to provide an interactive shell. It:

- Initializes the CLI and establishes the API connection
- Provides command handlers for all operations
- Implements tab completion and context-sensitive help
- Manages state transitions between modes
- Tracks command history in the database

Key methods include:

- `do_set()`: Handle 'set' commands to create/update objects
- `do_show()`: Display objects and their properties
- `do_delete()`: Remove objects
- `do_configure()`: Enter configuration mode
- `do_edit()`: Edit a specific folder
- `do_history()`: Show command history

### Address Object Command Handling

The CLI implements Junos-style keyword-based commands for address objects:

```
set address-object name test1 type ip-netmask value 1.1.1.1/32 description "Test" tags "tag1,tag2"
```

The `parse_set_address_object()` method parses these commands into a structured format, supporting:

- Required fields: name, type, value
- Optional fields: description, tags
- Partial updates: Updating only specific fields without re-specifying everything

### Context-Sensitive Help System

The module implements a robust help system that provides context-specific help:

- Using `?` at any point in a command to get help for that context
- Displaying formatted help tables with command syntax, arguments, and examples
- Custom completion handlers for each command type

The help system is implemented through:
- `_show_contextual_help()`: Display help based on current command context
- Custom completion methods for different argument types
- Overridden readline behavior to handle the `?` character

### Main Function

The `main()` function is the entry point that:
1. Creates the CLI instance
2. Initializes the environment
3. Starts the command loop
4. Handles keyboard interrupts

## Interactions with Other Modules

- **sdk_client.py**: The CLI uses `SDKClient` to communicate with the SCM API
- **config.py**: Credentials are loaded through `load_oauth_credentials()`
- **db.py**: Command history is tracked through `CLIHistoryDB`

## Command Flow Example

When a user types a command like `set address-object name test1 type ip-netmask value 1.1.1.1/32`:

1. The `do_set()` method is called with the command arguments
2. `parse_set_address_object()` parses the arguments into a structured dictionary
3. Validation is performed to ensure required fields are present
4. The SDK client is used to check if the object exists
5. The appropriate create or update operation is called on the SDK client
6. Results are displayed to the user with formatting

## Performance Optimization

The module includes performance optimizations:
- Timing information for SDK operations
- Direct object access methods for efficiency
- Caching of known objects for quicker access and autocompletion