#!/usr/bin/env python3
"""SCM CLI main module."""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set

import cmd2
from cmd2 import (
    Cmd2ArgumentParser,
    with_argparser,
    with_category, )

# Use child logger from the root logger
logger = logging.getLogger("scm_cli.cli")

from rich.console import Console
from rich.table import Table
from rich.text import Text

# Import modules from the utils package with absolute imports
from scm.client import ScmClient
from scm.exceptions import AuthenticationError
from src.scm_cli.utils.config import load_oauth_credentials
from src.scm_cli.utils.db import CLIHistoryDB
from src.scm_cli.utils.logging import set_log_level, get_log_levels
from src.scm_cli.utils.sdk_client import create_client, test_connection

# Import command modules
from .object.address_object.commands import AddressObjectCommands


@dataclass
class SCMState:
    """Class representing the current state of the SCM CLI."""

    config_mode: bool = False
    current_folder: Optional[str] = None
    scm_client: Optional[ScmClient] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    # Track folders we've seen for autocompletion
    known_folders: Set[str] = field(default_factory=set)
    # Track address objects we've seen for autocompletion
    known_address_objects: Dict[str, Set[str]] = field(default_factory=dict)
    # History database
    history_db: CLIHistoryDB = field(default_factory=lambda: CLIHistoryDB())


# Command categories
CATEGORY_CONFIG = "Configuration Commands"
CATEGORY_ADDRESS = "Address Object Commands"
CATEGORY_GENERAL = "General Commands"
CATEGORY_HISTORY = "History Commands"
CATEGORY_SYSTEM = "System Commands"


def _extract_username(client_id: str) -> str:
    """Extract username from client_id.

    Args:
        client_id: The full client_id which may contain email format

    Returns:
        Just the username part (before the @ symbol)
    """
    if not client_id:
        return "user"

    # Extract everything before the first @ symbol
    match = re.match(r"^([^@]+)@?.*$", client_id)
    if match:
        return match.group(1)

    return client_id


class SCMCLI(cmd2.Cmd):
    """SCM CLI command processor using cmd2."""

    def __init__(self) -> None:
        """Initialize the SCM CLI command processor."""
        # Configure readline behavior for handling ? key
        # This makes the '?' character a word-break character, which allows for immediate help
        import readline

        # Define delimiters - make ? a delimiter so readline treats it specially
        old_delims = readline.get_completer_delims()
        # Add '?' to the delimiter set but remove it from the end so it's not treated as part of a word
        readline.set_completer_delims(old_delims + "?")

        # Define a custom key event handler for ? to show help without executing the command
        # This requires overriding some readline behavior

        # Initialize the cmd2 shell
        super().__init__(
            allow_cli_args=False,
            allow_redirection=False,
            terminators=[],
        )

        # Configure cmd2 settings
        self.self_in_help = False
        self.hidden_commands += [
            "alias",
            "macro",
            "run_pyscript",
            "run_script",
            "shell",
            "shortcuts",
            "py",
            "ipy",
        ]
        self.default_to_shell = False

        # Configure special characters
        # Override the cmd2 question mark handling to make it immediate
        # In cmd2, this is handled by the postparsing_precmd method
        # We'll modify this to capture ? immediately
        self.question_mark = "?"

        # Disable commands if they exist
        for cmd_name in [
            "alias",
            "macro",
            "run_pyscript",
            "run_script",
            "shell",
            "shortcuts",
        ]:
            if hasattr(self, f"do_{cmd_name}"):
                self.disable_command(cmd_name, "Command not available")

        # Initialize state
        self.state = SCMState()

        # Rich console
        self.console = Console()

        # Initialize SDK client
        self._initialize_sdk()

        # Set prompt
        self.update_prompt()

        # Configure cmd2 to use ? to display help
        self.continuation_prompt = "> "

        # Initialize command modules
        self._initialize_command_modules()

    def _initialize_command_modules(self) -> None:
        """Initialize the command modules."""
        # Initialize all command modules with the SCM client
        self.address_object_commands = AddressObjectCommands(
            console=self.console, client=self.state.scm_client
        )

    # Use cmd2's built-in history mechanism but also store in our database
    def postcmd(self, stop: bool, statement: cmd2.Statement) -> bool:
        """Executed after the command is processed.

        Args:
            stop: True if the command loop should terminate
            statement: The command statement that was executed

        Returns:
            True if the command loop should terminate, False otherwise
        """
        # Skip recording certain commands
        skip_recording = ["history", "help", "exit", "quit"]
        should_record = statement.command and statement.command not in skip_recording

        # Record the command to the database
        if should_record:
            self.state.history_db.add_command(
                command=statement.raw.strip(),
                response="",  # We simplify by not capturing output for now
                folder=self.state.current_folder,
                success=True,
            )

        return super().postcmd(stop, statement)

    # Special method to handle ? keypress - this is called when ? is typed
    # We need to override the readline handler
    def precmd(self, statement: cmd2.Statement) -> cmd2.Statement:
        """Process the command before execution."""
        # Check if question mark is in the raw input
        if "?" in statement.raw and not statement.raw.strip() == "?":
            # Get the command so far
            input_line = statement.raw.strip()
            # Find where the ? appears in the input
            q_index = input_line.find("?")
            # Get the command parts up to the ? mark
            parts = input_line[:q_index].strip().split()

            # Show help for the command parts so far
            self._show_contextual_help(parts)

            # Return an empty statement to not execute anything
            return cmd2.Statement("")

        return statement

    def _initialize_sdk(self) -> None:
        """Initialize SCM client from OAuth credentials."""
        # Load credentials from .env file
        success, config = load_oauth_credentials()

        if not success:
            # Error messages already printed by load_oauth_credentials
            sys.exit(1)

        try:
            self.console.print("Initializing SCM client...", style="yellow")

            # Create SDK client
            self.state.scm_client = create_client(config)
            self.state.client_id = config.client_id

            # Extract username from client_id
            self.state.username = _extract_username(config.client_id)

            # Test connection
            try:
                test_connection(self.state.scm_client)
                # Show success message
                success_text = Text(
                    "✅ Client initialized successfully", style="bold green"
                )
                self.console.print(success_text)
                self.console.print()
                self.console.print("# " + "-" * 76)
                self.console.print("# Welcome to the SCM CLI for Strata Cloud Manager")
                self.console.print("# " + "-" * 76)
            except Exception as conn_error:
                self.console.print(
                    f"[bold red]Error:[/bold red] Failed to connect to SCM API: {str(conn_error)}",
                    style="red",
                )
                self.console.print(
                    "Please check your credentials in the .env file:", style="yellow"
                )
                self.console.print(
                    "  - Ensure SCM_CLIENT_ID is correct", style="yellow"
                )
                self.console.print(
                    "  - Ensure SCM_CLIENT_SECRET is correct", style="yellow"
                )
                self.console.print("  - Ensure SCM_TSG_ID is correct", style="yellow")
                self.console.print(
                    "  - Ensure you have valid API access to Strata Cloud Manager",
                    style="yellow",
                )
                sys.exit(1)
        except AuthenticationError as e:
            self.console.print(
                f"[bold red]Authentication Error:[/bold red] {e}", style="red"
            )
            self.console.print(
                "Please check your credentials in the .env file:", style="yellow"
            )
            self.console.print("  - Ensure SCM_CLIENT_ID is correct", style="yellow")
            self.console.print(
                "  - Ensure SCM_CLIENT_SECRET is correct", style="yellow"
            )
            self.console.print("  - Ensure SCM_TSG_ID is correct", style="yellow")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}", style="red")
            self.console.print("Stack trace:", style="dim")
            import traceback

            self.console.print(traceback.format_exc(), style="dim")
            sys.exit(1)

    def update_prompt(self) -> None:
        """Update the prompt based on the current state."""
        username = self.state.username or "user"

        if self.state.config_mode:
            if self.state.current_folder:
                self.prompt = f"{username}({self.state.current_folder})# "
            else:
                self.prompt = f"{username}@scm# "
        else:
            self.prompt = f"{username}@scm> "

    def emptyline(self) -> bool:
        """Do nothing on empty line."""
        return False

    def default(self, statement: cmd2.Statement) -> bool:
        """Handle unknown commands."""
        # Check if command contains ? for help
        if "?" in statement.raw:
            # Replace ? with space for parsing
            modified_command = statement.raw.replace("?", " ? ")
            parts = modified_command.split()

            # Find the context for the help
            context = []
            for i, part in enumerate(parts):
                if part == "?":
                    # Get the context up to this point
                    context = parts[:i]
                    break

            # Show help based on context
            if context:
                self._show_contextual_help(context)
            else:
                self.do_help(self, "")

            return False

        self.console.print(f"Unknown command: {statement.raw}", style="red")
        return False

    def _show_contextual_help(self, context: List[str]) -> None:
        """Show contextual help based on command context.

        Args:
            context: The command parts entered so far
        """
        cmd = context[0] if context else ""

        # Help for main commands
        if not context or cmd == "":
            self.do_help(self, "")
            return

        # Help for set command
        elif cmd == "set":
            if len(context) == 1:
                table = Table(title="Available Object Types")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")

                table.add_row("address-object", "Configure an address object")
                self.console.print(table)
            elif len(context) == 2 and context[1] == "address-object":
                # Table for required arguments
                required = Table(title="Command: set address-object")
                required.add_column("Required Arguments", style="cyan", width=20)
                required.add_column("Description", style="green")

                required.add_row(
                    "name <n>",
                    "Name of the address object (required for all operations)",
                )
                required.add_row(
                    "type <type>",
                    "Type of address object (ip-netmask, ip-range, fqdn) (required for new objects)",
                )
                required.add_row(
                    "value <value>",
                    "Value of the address object (required for new objects)",
                )
                self.console.print(required)

                # Table for optional arguments
                optional = Table(title="Optional Arguments")
                optional.add_column("Argument", style="yellow", width=20)
                optional.add_column("Description", style="blue")

                optional.add_row(
                    "description <text>", "Description of the address object"
                )
                optional.add_row(
                    "tags <tag1,tag2,..>",
                    "Comma-separated list of tags (use Automation or Decryption)",
                )
                self.console.print(optional)

                # Add partial update info
                partial = Table(title="Partial Update Support")
                partial.add_column("Feature", style="cyan")
                partial.add_column("Description", style="green")

                partial.add_row(
                    "Partial Updates",
                    "For existing objects, you can update only specific fields without specifying all required fields",
                )
                partial.add_row(
                    "Example",
                    'set address-object name test1 description "Updated description"',
                )
                self.console.print(partial)

                # Table for examples
                examples = Table(title="Examples")
                examples.add_column("Command", style="magenta")
                examples.add_column("Description", style="dim")

                examples.add_row(
                    "set address-object name test1 type ip-netmask value 1.1.1.1/32",
                    "Create/update an IP address object",
                )
                examples.add_row(
                    "set address-object name test2 type fqdn value example.com",
                    "Create/update a domain name address object",
                )
                examples.add_row(
                    'set address-object name test3 type ip-range value 1.1.1.1-1.1.1.10 description "Test" tags Automation',
                    "Create/update an IP range with description and tags",
                )
                self.console.print(examples)

            # Add more contextual help for address object arguments here
            # ...

        # Help for show command
        elif cmd == "show":
            if len(context) == 1:
                table = Table(title="Available Objects to Show")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")

                table.add_row(
                    "address-object", "Show address objects (specific or all)"
                )
                table.add_row(
                    "address-objects-filter", "Search and filter address objects"
                )

                self.console.print(table)

            # Add more contextual help for show command arguments here
            # ...

        # Help for delete command
        elif cmd == "delete":
            if len(context) == 1:
                table = Table(title="Available Objects to Delete")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")

                table.add_row("address-object", "Delete an address object")
                self.console.print(table)

            # Add more contextual help for delete command arguments here
            # ...

        # Help for edit command
        elif cmd == "edit":
            if len(context) == 1:
                table = Table(title="Available Objects to Edit")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")

                table.add_row("folder", "Edit a specific folder")
                self.console.print(table)

            # Add more contextual help for edit command arguments here
            # ...

        # Help for history command
        elif cmd == "history":
            table = Table(title="Command: history [options]")
            table.add_column("Option", style="cyan", width=20)
            table.add_column("Description", style="green")

            table.add_row(
                "--page <n>", "Page number to display, starting from 1 (default: 1)"
            )
            table.add_row(
                "--limit <n>",
                "Maximum number of history entries per page (default: 50)",
            )
            table.add_row("--folder <folder>", "Filter history by folder")
            table.add_row("--filter <text>", "Filter history by command content")
            table.add_row("--clear", "Clear command history")
            table.add_row("--id <n>", "Show details of a specific history entry")
            self.console.print(table)

            examples = Table(title="Examples")
            examples.add_column("Command", style="yellow")
            examples.add_column("Description", style="blue")

            examples.add_row("history", "Show last 50 commands")
            examples.add_row("history --page 2", "Show second page of commands")
            examples.add_row("history --limit 20", "Show only 20 commands per page")
            examples.add_row(
                "history --folder Texas", "Show commands from the Texas folder"
            )
            examples.add_row(
                "history --filter address", "Show commands containing 'address'"
            )
            examples.add_row("history --id 5", "Show details of history entry #5")
            examples.add_row("history --clear", "Clear all command history")
            self.console.print(examples)

        # General help for other commands
        else:
            # Try to get help for the command
            self.do_help(self, cmd)

    # Tab completion helpers for folder names, object names, etc.
    # ... (implement as needed)

    # Core commands
    @with_category(CATEGORY_GENERAL)
    def do_exit(self, _: cmd2.Statement) -> bool:
        """Exit the current mode or the CLI."""
        if self.state.current_folder:
            self.state.current_folder = None
            self.update_prompt()
            return False
        elif self.state.config_mode:
            self.state.config_mode = False
            self.update_prompt()
            return False
        else:
            return True

    @with_category(CATEGORY_GENERAL)
    def do_quit(self, _: cmd2.Statement) -> bool:
        """Exit the CLI."""
        return True

    # History command
    history_parser = Cmd2ArgumentParser(description="Show command history")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of history entries to show per page",
    )
    history_parser.add_argument(
        "--page", type=int, default=1, help="Page number to display (starting from 1)"
    )
    history_parser.add_argument("--folder", help="Filter history by folder")
    history_parser.add_argument("--filter", help="Filter history by command content")
    history_parser.add_argument(
        "--clear", action="store_true", help="Clear command history"
    )
    history_parser.add_argument(
        "--id", type=int, help="Show details of a specific history entry"
    )

    @with_category(CATEGORY_HISTORY)
    @with_argparser(history_parser)
    def do_history(self, args: argparse.Namespace) -> None:
        """Show command history."""
        if args.clear:
            self.state.history_db.clear_history()
            self.console.print("Command history cleared", style="green")
            return

        # If an ID is specified, show details for that specific entry
        if args.id is not None:
            entry = self.state.history_db.get_history_entry(args.id)
            if not entry:
                self.console.print(
                    f"History entry with ID {args.id} not found", style="red"
                )
                return

            object_id, timestamp, command, response, folder, success = entry

            # Format the timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = timestamp

            # Display the history entry details
            self.console.print(f"[bold cyan]History Entry #{object_id}[/bold cyan]")
            self.console.print(f"[bold]Timestamp:[/bold] {formatted_time}")
            self.console.print(f"[bold]Folder:[/bold] {folder or 'None'}")
            self.console.print(f"[bold]Command:[/bold] {command}")
            self.console.print("\n[bold]Response:[/bold]")
            self.console.print(response)
            return

        # Validate page number
        if args.page < 1:
            self.console.print("Page number must be 1 or greater", style="red")
            return

        # Get history from database with pagination
        history_items, total_count = self.state.history_db.get_history(
            limit=args.limit,
            page=args.page,
            folder=args.folder,
            command_filter=args.filter,
        )

        if not history_items:
            self.console.print("No command history found", style="yellow")
            return

        # Calculate pagination info
        total_pages = (total_count + args.limit - 1) // args.limit  # Ceiling division

        # Create table for display
        title = f"Command History (Page {args.page} of {total_pages})"
        if args.folder or args.filter:
            filters = []
            if args.folder:
                filters.append(f"folder='{args.folder}'")
            if args.filter:
                filters.append(f"filter='{args.filter}'")
            title += f" [Filtered by: {', '.join(filters)}]"

        table = Table(title=title)
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Timestamp", style="magenta")
        table.add_column("Folder", style="green")
        table.add_column("Command", style="blue")

        # Add history items to table
        for object_id, timestamp, command, response, folder, success in history_items:
            # Format the timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = timestamp

            table.add_row(str(object_id), formatted_time, folder or "", command)

        self.console.print(table)

        # Show pagination help
        pagination_help = []
        if args.page > 1:
            pagination_help.append(f"'history --page {args.page-1}' for previous page")
        if args.page < total_pages:
            pagination_help.append(f"'history --page {args.page+1}' for next page")

        if pagination_help:
            self.console.print(
                f"\nPagination: {' | '.join(pagination_help)}", style="dim"
            )

        self.console.print(
            "\nTip: Use 'history --object_id <n>' to view the full details of a specific entry",
            style="dim",
        )

    @with_category(CATEGORY_CONFIG)
    def do_configure(self, _: cmd2.Statement) -> bool:
        """Enter configuration mode."""
        if not self.state.config_mode:
            self.state.config_mode = True
            self.update_prompt()
        return False

    # Edit command
    edit_parser = Cmd2ArgumentParser(description="Edit a specific folder")
    edit_parser.add_argument(
        "object_type", choices=["folder"], help="Object type to edit"
    )
    edit_parser.add_argument("name", help="Name of the folder to edit")

    @with_category(CATEGORY_CONFIG)
    @with_argparser(edit_parser)
    def do_edit(self, args: argparse.Namespace) -> None:
        """Edit a specific folder."""
        if not self.state.config_mode:
            self.console.print(
                "Command only available in configuration mode", style="red"
            )
            return

        folder = args.name
        self.state.current_folder = folder

        # Add folder to known folders for autocompletion
        self.state.known_folders.add(folder)

        self.update_prompt()

    @with_category(CATEGORY_ADDRESS)
    def do_set(self, statement: cmd2.Statement) -> None:
        """Set an object's properties."""
        # Parse command
        args = statement.arg_list

        if not args:
            self.console.print("Missing object type", style="red")
            self.console.print(
                "Usage: set address-object name <n> type <type> value <value> [description <text>] [tags <tag1,tag2,...>]"
            )
            return

        object_type = args[0]

        if not self.state.config_mode or not self.state.current_folder:
            self.console.print(
                "Command only available in folder edit mode", style="red"
            )
            return

        if not self.state.scm_client:
            self.console.print("No SCM client available.", style="red")
            return

        # Delegate to appropriate command handler
        if object_type == "address-object":
            self.address_object_commands.set_address_object(
                self.state.current_folder, args
            )
        else:
            self.console.print(f"Unknown object type: {object_type}", style="red")

    # Delete command
    delete_parser = Cmd2ArgumentParser(description="Delete an object")
    delete_subparsers = delete_parser.add_subparsers(
        title="objects", dest="object_type"
    )

    # Address object subparser
    addr_del_parser = delete_subparsers.add_parser(
        "address-object", help="Delete an address object"
    )
    addr_del_parser.add_argument("name", help="Name of the address object")

    # Logger command
    logger_parser = Cmd2ArgumentParser(description="Control logging levels")
    logger_subparsers = logger_parser.add_subparsers(
        title="logger-commands", dest="subcommand"
    )
    
    # Show logger levels
    logger_show_parser = logger_subparsers.add_parser(
        "show", help="Show current log levels"
    )
    
    # Set logger level
    logger_set_parser = logger_subparsers.add_parser(
        "set", help="Set log level for a module"
    )
    logger_set_parser.add_argument(
        "level", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level to set"
    )
    logger_set_parser.add_argument(
        "--module", 
        help="Optional module name (default: scm_cli for root logger)"
    )

    @with_category(CATEGORY_ADDRESS)
    @with_argparser(delete_parser)
    def do_delete(self, args: argparse.Namespace) -> None:
        """Delete an object."""
        if not self.state.config_mode or not self.state.current_folder:
            self.console.print(
                "Command only available in folder edit mode", style="red"
            )
            return

        if not self.state.scm_client:
            self.console.print("No SCM client available.", style="red")
            return

        # Delegate to appropriate command handler
        if args.object_type == "address-object":
            self.address_object_commands.delete_address_object(
                self.state.current_folder, args.name
            )
        else:
            self.console.print(f"Unknown object type: {args.object_type}", style="red")

    # Show command
    show_parser = Cmd2ArgumentParser(description="Show object details")
    show_subparsers = show_parser.add_subparsers(title="objects", dest="object_type")

    # Address object subparser
    addr_show_parser = show_subparsers.add_parser(
        "address-object", help="Show address object details"
    )
    addr_show_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name of the address object to show (optional - if omitted, shows all objects)",
    )

    # Address objects filter subparser
    addr_filter_parser = show_subparsers.add_parser(
        "address-objects-filter", help="Search and filter address objects"
    )
    addr_filter_parser.add_argument("--name", help="Filter by name (substring match)")
    addr_filter_parser.add_argument(
        "--type",
        help="Filter by type (exact match)",
        choices=["ip-netmask", "ip-range", "fqdn"],
    )
    addr_filter_parser.add_argument("--value", help="Filter by value (substring match)")
    addr_filter_parser.add_argument("--tag", help="Filter by tag (substring match)")

    @with_category(CATEGORY_ADDRESS)
    @with_argparser(show_parser)
    def do_show(self, args: argparse.Namespace) -> None:
        """Show object details."""
        if not self.state.config_mode:
            self.console.print(
                "Command only available in configuration mode", style="red"
            )
            return

        if not self.state.scm_client:
            self.console.print("No SCM client available.", style="red")
            return

        folder = self.state.current_folder
        if not folder:
            self.console.print("No folder selected", style="red")
            return

        # Map CLI types to SDK types for filtering
        cli_to_sdk_type = {"ip-netmask": "ip", "ip-range": "range", "fqdn": "fqdn"}

        # Delegate to appropriate command handler
        if args.object_type == "address-object":
            self.address_object_commands.show_address_object(folder, args.name)
        elif args.object_type == "address-objects-filter":
            # Build filter criteria from arguments
            filter_criteria = {}

            if args.name:
                filter_criteria["name"] = args.name

            if args.type:
                filter_criteria["type"] = cli_to_sdk_type.get(args.type, args.type)

            if args.value:
                filter_criteria["value"] = args.value

            if args.tag:
                filter_criteria["tag"] = args.tag

            self.address_object_commands.show_address_object(
                folder, None, filter_criteria=filter_criteria
            )
        else:
            self.console.print(f"Unknown object type: {args.object_type}", style="red")
    
    @with_category(CATEGORY_SYSTEM)
    @with_argparser(logger_parser)
    def do_logger(self, args: argparse.Namespace) -> None:
        """Control logging levels."""
        if args.subcommand == "show":
            # Get the current log levels
            log_levels = get_log_levels()
            
            # Create a table for display
            table = Table(title="Logging Levels")
            table.add_column("Logger", style="cyan")
            table.add_column("Level", style="green")
            
            # Add each logger to the table
            for log in log_levels:
                table.add_row(log["name"], log["level"].upper())
            
            self.console.print(table)
            
        elif args.subcommand == "set":
            # Set the log level
            module = args.module or "scm_cli"
            if set_log_level(args.level, module):
                self.console.print(
                    f"✅ Log level for '{module}' set to {args.level.upper()}", 
                    style="green"
                )
            else:
                self.console.print(
                    f"❌ Failed to set log level for '{module}'", 
                    style="red"
                )


def main() -> None:
    """Run the SCM CLI."""
    console = Console()
    console.print("Entering SCM CLI", style="bold green")
    try:
        cli = SCMCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        console.print("\nExiting SCM CLI", style="bold yellow")
    print("$")


if __name__ == "__main__":
    main()
