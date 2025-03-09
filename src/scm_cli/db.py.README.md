# db.py - Database Module for Command History

## Overview

The `db.py` module implements a SQLite-based command history tracking system for the SCM CLI. It provides:

1. Persistent storage of command history between CLI sessions
2. Methods to add, retrieve, and clear command history
3. Advanced filtering and pagination capabilities
4. Detailed record keeping with timestamps and execution context

## Key Components

### CLIHistoryDB Class

The `CLIHistoryDB` class handles all database operations for command history:

```python
class CLIHistoryDB:
    def __init__(self, db_path: str = "scm_cli_history.db") -> None:
        self.db_path = db_path
        self._initialize_db()
```

Main methods:
- `_initialize_db()`: Creates the database and tables if they don't exist
- `add_command()`: Records a new command in the history
- `get_history()`: Retrieves command history with filtering and pagination
- `get_history_entry()`: Retrieves a specific history entry by ID
- `clear_history()`: Removes all history entries

### Database Schema

The module creates a `command_history` table with the following structure:

```sql
CREATE TABLE IF NOT EXISTS command_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    command TEXT NOT NULL,
    response TEXT,
    folder TEXT,
    success INTEGER
)
```

Fields:
- `id`: Unique identifier for the command
- `timestamp`: When the command was executed (ISO format)
- `command`: The command string that was entered by the user
- `response`: (Optional) The command's output
- `folder`: (Optional) The folder context when the command was executed
- `success`: Boolean flag indicating if the command executed successfully

### History Record Addition

The `add_command()` method adds a new command to the history:

```python
def add_command(
    self, 
    command: str, 
    response: Optional[str] = None, 
    folder: Optional[str] = None,
    success: bool = True
) -> int:
    # Implementation
```

It:
1. Creates a timestamp for the command
2. Stores the command and its context in the database
3. Returns the ID of the new record

### History Retrieval with Filtering

The `get_history()` method supports advanced filtering and pagination:

```python
def get_history(
    self, 
    limit: int = 50,
    page: int = 1,
    folder: Optional[str] = None,
    command_filter: Optional[str] = None
) -> Tuple[List[Tuple[int, str, str, str, str, bool]], int]:
    # Implementation
```

It supports:
- Limiting results to a specific number per page
- Pagination through page number specification
- Filtering by folder context
- Text-based filtering of command content
- Returns both results and total count for pagination UI

### Single History Entry Lookup

The `get_history_entry()` method retrieves a specific entry by ID:

```python
def get_history_entry(self, entry_id: int) -> Optional[Tuple[int, str, str, str, str, bool]]:
    # Implementation
```

This is used to display detailed information about a specific command, including its output.

### History Clearing

The `clear_history()` method removes all command history:

```python
def clear_history(self) -> None:
    # Implementation
```

## Data Types

The module uses type hints extensively to ensure correct usage:

- History entries are represented as tuples: `Tuple[int, str, str, str, str, bool]`
- Functions return with explicit types like `Optional[Tuple[...]]`
- Lists and filter parameters have appropriate type annotations

## Integration with CLI

This module is used by the `cli.py` module in several ways:

1. The CLI initializes a history database instance in its state:
   ```python
   history_db: CLIHistoryDB = field(default_factory=lambda: CLIHistoryDB())
   ```

2. Commands are recorded in the `postcmd()` method:
   ```python
   self.state.history_db.add_command(
       command=statement.raw.strip(),
       response="",
       folder=self.state.current_folder,
       success=True
   )
   ```

3. The `do_history()` method fetches and displays history using filters and pagination.

## Performance Considerations

The module includes several performance optimizations:

- Using parameterized queries to prevent SQL injection
- Employing single queries with WHERE clauses rather than filtering in Python
- Limiting result sets through SQL LIMIT and OFFSET
- Reusing database connections appropriately