#!/usr/bin/env python3
"""SCM CLI main module."""

import argparse
import json
import io
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

import cmd2
from cmd2 import (
    Cmd, 
    Cmd2ArgumentParser, 
    CompletionError, 
    CompletionItem, 
    ansi,
    with_argparser,
    with_category
)
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .config import SCMConfig, load_oauth_credentials
from .db import CLIHistoryDB
from .mock_sdk import AddressObjectType, AuthenticationError  # Import from actual panscm when available
from .sdk_client import (
    APIError,
    AddressObject,
    ResourceNotFoundError,
    SDKClient,
    ValidationError,
)


@dataclass
class SCMState:
    """Class representing the current state of the SCM CLI."""

    config_mode: bool = False
    current_folder: Optional[str] = None
    sdk_client: Optional[SDKClient] = None
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


class SCMCLI(cmd2.Cmd):
    """SCM CLI command processor using cmd2."""

    def __init__(self) -> None:
        """Initialize the SCM CLI command processor."""
        super().__init__(
            allow_cli_args=False,
            allow_redirection=False,
            terminators=[],
        )
        
        # Configure cmd2 settings
        self.self_in_help = False
        self.hidden_commands += ['alias', 'macro', 'run_pyscript', 'run_script', 'shell', 'shortcuts', 'py', 'ipy']
        self.default_to_shell = False
        
        # Disable commands if they exist
        for cmd_name in ['alias', 'macro', 'run_pyscript', 'run_script', 'shell', 'shortcuts']:
            if hasattr(self, f'do_{cmd_name}'):
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
        self.continuation_prompt = '> '
        
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
        skip_recording = ['history', 'help', 'exit', 'quit']
        should_record = statement.command and statement.command not in skip_recording
        
        # Record the command to the database
        if should_record:
            self.state.history_db.add_command(
                command=statement.raw.strip(),
                response="",  # We simplify by not capturing output for now
                folder=self.state.current_folder,
                success=True
            )
            
        return super().postcmd(stop, statement)
        
    def _extract_username(self, client_id: str) -> str:
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

    def _initialize_sdk(self) -> None:
        """Initialize SDK client from OAuth credentials."""
        # Load credentials from .env file
        success, config = load_oauth_credentials()
        
        if not success:
            # Error messages already printed by load_oauth_credentials
            sys.exit(1)
        
        try:
            # Create SDK client
            self.state.sdk_client = SDKClient(config)
            self.state.client_id = config.client_id
            
            # Extract username from client_id
            self.state.username = self._extract_username(config.client_id)
            
            # Test connection
            if self.state.sdk_client.test_connection():
                # Show success message
                success_text = Text("✅ Client initialized successfully", style="bold green")
                self.console.print(success_text)
                self.console.print()
                self.console.print("# " + "-" * 76)
                self.console.print("# Welcome to the SCM CLI for Strata Cloud Manager")
                self.console.print("# " + "-" * 76)
            else:
                self.console.print(
                    "[bold red]Error:[/bold red] Failed to connect to SCM API. "
                    "Please check your credentials.", 
                    style="red"
                )
                sys.exit(1)
        except AuthenticationError as e:
            self.console.print(f"[bold red]Authentication Error:[/bold red] {e}", style="red")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}", style="red")
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
        if '?' in statement.raw:
            # Replace ? with space for parsing
            modified_command = statement.raw.replace('?', ' ? ')
            parts = modified_command.split()
            
            # Find the context for the help
            context = []
            for i, part in enumerate(parts):
                if part == '?':
                    # Get the context up to this point
                    context = parts[:i]
                    break
            
            # Show help based on context
            if context:
                self._show_contextual_help(context)
            else:
                self.do_help("")
                
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
            self.do_help("")
            return
            
        # Help for set command
        elif cmd == "set":
            if len(context) == 1:
                self.console.print("Available object types:")
                self.console.print("  address-object - Configure an address object")
            elif len(context) == 2 and context[1] == "address-object":
                self.console.print("Syntax: set address-object <name> <type> <value> [description <text>] [tags <tag1,tag2,...>]")
                self.console.print("\nRequired arguments:")
                self.console.print("  <name>        - Name of the address object")
                self.console.print("  <type>        - Type of address object (ip-netmask, ip-range, ip-wildcard, fqdn)")
                self.console.print("  <value>       - Value of the address object")
                self.console.print("\nOptional arguments:")
                self.console.print("  description   - Description of the address object")
                self.console.print("  tags          - Comma-separated list of tags")
            elif len(context) == 3 and context[1] == "address-object":
                self.console.print("Address object types:")
                self.console.print("  ip-netmask  - IP address with netmask (e.g., 192.168.1.0/24)")
                self.console.print("  ip-range    - IP address range (e.g., 192.168.1.1-192.168.1.10)")
                self.console.print("  ip-wildcard - IP address with wildcard mask (e.g., 192.168.1.0/0.0.0.255)")
                self.console.print("  fqdn        - Fully qualified domain name (e.g., example.com)")
            elif len(context) == 4 and context[1] == "address-object":
                self.console.print("Enter the value for the address object based on its type:")
                self.console.print("  ip-netmask  - e.g., 192.168.1.0/24")
                self.console.print("  ip-range    - e.g., 192.168.1.1-192.168.1.10")
                self.console.print("  ip-wildcard - e.g., 192.168.1.0/0.0.0.255")
                self.console.print("  fqdn        - e.g., example.com")
            elif len(context) >= 5 and context[1] == "address-object":
                if len(context) == 5 or (len(context) > 5 and context[5] not in ["description", "tags"]):
                    self.console.print("Optional arguments:")
                    self.console.print("  description <text>  - Add a description to the address object")
                    self.console.print("  tags <tag1,tag2,..> - Add tags to the address object")
                
        # Help for show command
        elif cmd == "show":
            if len(context) == 1:
                self.console.print("Available objects to show:")
                self.console.print("  address-object         - Show details of a specific address object")
                self.console.print("  address-objects        - Show all address objects in the current folder")
                self.console.print("  address-objects-filter - Search and filter address objects")
            elif len(context) == 2 and context[1] == "address-object":
                self.console.print("Syntax: show address-object <name>")
                self.console.print("\nArguments:")
                self.console.print("  <name> - Name of the address object to show")
            elif len(context) == 2 and context[1] == "address-objects-filter":
                self.console.print("Syntax: show address-objects-filter [--name <substring>] [--type <type>] [--value <substring>] [--tag <substring>]")
                self.console.print("\nFilter options:")
                self.console.print("  --name <substring>  - Filter by name (substring match)")
                self.console.print("  --type <type>       - Filter by type (exact match, one of: ip-netmask, ip-range, ip-wildcard, fqdn)")
                self.console.print("  --value <substring> - Filter by value (substring match)")
                self.console.print("  --tag <substring>   - Filter by tag (substring match)")
                self.console.print("\nExamples:")
                self.console.print("  show address-objects-filter --name web        # Find objects with 'web' in the name")
                self.console.print("  show address-objects-filter --type fqdn       # Show only FQDN objects")
                self.console.print("  show address-objects-filter --value 192.168   # Find objects with value containing '192.168'")
                self.console.print("  show address-objects-filter --tag prod        # Find objects with 'prod' in any tag")
                
        # Help for delete command
        elif cmd == "delete":
            if len(context) == 1:
                self.console.print("Available objects to delete:")
                self.console.print("  address-object - Delete an address object")
            elif len(context) == 2 and context[1] == "address-object":
                self.console.print("Syntax: delete address-object <name>")
                self.console.print("\nArguments:")
                self.console.print("  <name> - Name of the address object to delete")
                
        # Help for edit command
        elif cmd == "edit":
            if len(context) == 1:
                self.console.print("Available objects to edit:")
                self.console.print("  folder - Edit a specific folder")
            elif len(context) == 2 and context[1] == "folder":
                self.console.print("Syntax: edit folder <name>")
                self.console.print("\nArguments:")
                self.console.print("  <name> - Name of the folder to edit")
        
        # Help for history command
        elif cmd == "history":
            self.console.print("Syntax: history [--page <name>] [--limit <name>] [--folder <folder>] [--filter <text>] [--clear] [--id <name>]")
            self.console.print("\nOptions:")
            self.console.print("  --page <name>       - Page number to display, starting from 1 (default: 1)")
            self.console.print("  --limit <name>      - Maximum number of history entries to show per page (default: 50)")
            self.console.print("  --folder <folder> - Filter history by folder")
            self.console.print("  --filter <text>   - Filter history by command content")
            self.console.print("  --clear           - Clear command history")
            self.console.print("  --id <name>         - Show details of a specific history entry")
            self.console.print("\nExamples:")
            self.console.print("  history                     # Show last 50 commands")
            self.console.print("  history --page 2            # Show second page of commands")
            self.console.print("  history --limit 20          # Show only 20 commands per page")
            self.console.print("  history --folder Texas      # Show commands from the Texas folder")
            self.console.print("  history --filter address    # Show commands containing 'address'")
            self.console.print("  history --id 5              # Show details of history entry #5")
            self.console.print("  history --clear             # Clear all command history")
                
        # General help for other commands
        else:
            # Try to get help for the command
            self.do_help(cmd)

    # Help handling for ? suffix
    def postparsing_precmd(self, statement: cmd2.Statement) -> cmd2.Statement:
        """Process commands after parsing but before execution."""
        if '?' in statement.raw:
            # Let default method handle it
            return statement
        
        if statement.raw.strip().endswith('?'):
            # Remove the ? from the command
            command = statement.raw.strip()[:-1].strip()
            
            # Check if it's a valid command or starts with a valid command prefix
            for cmd_name in self.get_all_commands():
                if command == cmd_name or command.startswith(f"{cmd_name} "):
                    # Show help for the command
                    self.do_help(cmd_name)
                    # Return empty statement to not execute the original command
                    return cmd2.Statement("")
            
            # If no matching command is found, show general help
            self.do_help("")
            return cmd2.Statement("")
        
        return statement

    def get_all_commands(self) -> List[str]:
        """Get all available command names."""
        commands = []
        for name in dir(self):
            if name.startswith('do_'):
                commands.append(name[3:])
        return commands

    # Tab completion for folders
    def folder_completer(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Complete folder names."""
        if not self.state.sdk_client:
            raise CompletionError("No SDK client available")
            
        # Add any folders we already know about
        completions = list(self.state.known_folders)
        
        # Add some standard folders
        standard_folders = ["Global", "Shared", "Texas", "California", "New_York"]
        completions.extend(standard_folders)
        
        # Return matching folders
        if text:
            return [f for f in completions if f.startswith(text)]
        else:
            return completions

    # Tab completion for address object names
    def address_completer(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Complete address object names."""
        if not self.state.sdk_client or not self.state.current_folder:
            raise CompletionError("Must be in folder edit mode")
            
        folder = self.state.current_folder
        completions = []
        
        # Use cached address names if available
        if folder in self.state.known_address_objects:
            completions = list(self.state.known_address_objects[folder])
        
        # Try to fetch from SDK if possible
        try:
            addresses = self.state.sdk_client.list_address_objects(folder)
            names = [addr.name for addr in addresses]
            
            # Update cache
            if folder not in self.state.known_address_objects:
                self.state.known_address_objects[folder] = set()
            self.state.known_address_objects[folder].update(names)
            
            completions = names
        except Exception:
            # If we can't fetch, just use what we have
            pass
            
        # Return matching names
        if text:
            return [a for a in completions if a.startswith(text)]
        else:
            return completions

    # Tab completion for address types
    def address_type_completer(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Complete address object types."""
        # Address object types
        types = ["ip-netmask", "ip-range", "ip-wildcard", "fqdn"]
        if text:
            return [t for t in types if t.startswith(text)]
        else:
            return types
    
    # Tab completion for keywords
    def keywords_completer(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Complete keywords like 'description' and 'tags'."""
        keywords = ["description", "tags"]
        if text:
            return [k for k in keywords if k.startswith(text)]
        else:
            return keywords

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
        
    # History command parser
    history_parser = Cmd2ArgumentParser(description="Show command history")
    history_parser.add_argument("--limit", type=int, default=50, help="Maximum number of history entries to show per page")
    history_parser.add_argument("--page", type=int, default=1, help="Page number to display (starting from 1)")
    history_parser.add_argument("--folder", help="Filter history by folder")
    history_parser.add_argument("--filter", help="Filter history by command content")
    history_parser.add_argument("--clear", action="store_true", help="Clear command history")
    history_parser.add_argument("--id", type=int, help="Show details of a specific history entry")
    
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
                self.console.print(f"History entry with ID {args.id} not found", style="red")
                return
                
            id, timestamp, command, response, folder, success = entry
                
            # Format the timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = timestamp
                
            # Display the history entry details
            self.console.print(f"[bold cyan]History Entry #{id}[/bold cyan]")
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
            command_filter=args.filter
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
        for id, timestamp, command, response, folder, success in history_items:
            # Format the timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = timestamp
                
            table.add_row(
                str(id),
                formatted_time,
                folder or "",
                command
            )
            
        self.console.print(table)
        
        # Show pagination help
        pagination_help = []
        if args.page > 1:
            pagination_help.append(f"'history --page {args.page-1}' for previous page")
        if args.page < total_pages:
            pagination_help.append(f"'history --page {args.page+1}' for next page")
            
        if pagination_help:
            self.console.print(f"\nPagination: {' | '.join(pagination_help)}", style="dim")
            
        self.console.print("\nTip: Use 'history --id <n>' to view the full details of a specific entry", style="dim")
    
    @with_category(CATEGORY_CONFIG)
    def do_configure(self, _: cmd2.Statement) -> bool:
        """Enter configuration mode."""
        if not self.state.config_mode:
            self.state.config_mode = True
            self.update_prompt()
        return False

    # Edit command
    edit_parser = Cmd2ArgumentParser(description="Edit a specific folder")
    edit_parser.add_argument("object_type", choices=["folder"], help="Object type to edit")
    edit_parser.add_argument("name", help="Name of the folder to edit").completer = folder_completer
    
    @with_category(CATEGORY_CONFIG)
    @with_argparser(edit_parser)
    def do_edit(self, args: argparse.Namespace) -> None:
        """Edit a specific folder."""
        if not self.state.config_mode:
            self.console.print("Command only available in configuration mode", style="red")
            return

        folder = args.name
        self.state.current_folder = folder
        
        # Add folder to known folders for autocompletion
        self.state.known_folders.add(folder)
            
        self.update_prompt()

    # Custom parser for set address-object that supports positional description and tags
    def parse_set_address_object(self, args: List[str]) -> Tuple[str, str, str, Optional[str], Optional[List[str]]]:
        """Parse the set address-object command with positional keyword arguments.
        
        Args:
            args: List of argument strings
            
        Returns:
            Tuple of (name, type, value, description, tags)
            
        Raises:
            ValueError: If required arguments are missing or format is invalid
        """
        if len(args) < 3:
            raise ValueError("Missing required arguments: name, type, value")
            
        name = args[0]
        addr_type = args[1]
        value = args[2]
        
        # Check if addr_type is valid
        valid_types = ["ip-netmask", "ip-range", "ip-wildcard", "fqdn"]
        if addr_type not in valid_types:
            valid_types_str = ", ".join(valid_types)
            raise ValueError(f"Invalid address type: {addr_type}. Valid types are: {valid_types_str}")
        
        # Process remaining arguments for description and tags
        description = None
        tags = None
        
        i = 3
        while i < len(args):
            if args[i] == "description" and i + 1 < len(args):
                description = args[i + 1]
                i += 2
            elif args[i] == "tags" and i + 1 < len(args):
                # Parse comma-separated tags
                tags = [tag.strip() for tag in args[i + 1].split(",")]
                i += 2
            else:
                # Invalid keyword
                if args[i] in ["description", "tags"]:
                    raise ValueError(f"Missing value for {args[i]}")
                else:
                    raise ValueError(f"Unknown keyword: {args[i]}")
        
        return name, addr_type, value, description, tags
    
    @with_category(CATEGORY_ADDRESS)
    def do_set(self, statement: cmd2.Statement) -> None:
        """Set an object's properties."""
        # Parse command
        args = statement.arg_list
        
        if not args:
            self.console.print("Missing object type", style="red")
            self.console.print("Usage: set address-object <name> <type> <value> [description <text>] [tags <tag1,tag2,...>]")
            return
            
        object_type = args[0]
        
        if not self.state.config_mode or not self.state.current_folder:
            self.console.print("Command only available in folder edit mode", style="red")
            return

        if not self.state.sdk_client:
            self.console.print("No SDK client available.", style="red")
            return

        if object_type == "address-object":
            try:
                # Parse Junos-style arguments
                if len(args) < 2:
                    self.console.print("Missing required arguments", style="red")
                    self.console.print("Usage: set address-object <name> <type> <value> [description <text>] [tags <tag1,tag2,...>]")
                    return
                    
                # Parse the remaining arguments
                name, addr_type, value, description, tags = self.parse_set_address_object(args[1:])
                
                folder = self.state.current_folder
                
                # Convert from CLI types to SDK types
                type_map = {
                    "ip-netmask": "ip",
                    "ip-range": "range",
                    "ip-wildcard": "wildcard",
                    "fqdn": "fqdn"
                }
                sdk_type = type_map.get(addr_type, "ip")
                
                try:
                    # Check if the address object already exists
                    try:
                        self.state.sdk_client.get_address_object(folder, name)
                        # If we get here, the address object exists, so update it
                        address = self.state.sdk_client.update_address_object(
                            folder=folder,
                            name=name,
                            type_val=sdk_type,
                            value=value,
                            description=description,
                            tags=tags,
                        )
                        self.console.print(f"✅ - updated address-object {name}", style="green")
                    except ResourceNotFoundError:
                        # Address object doesn't exist, create it
                        address = self.state.sdk_client.create_address_object(
                            folder=folder,
                            name=name,
                            type_val=sdk_type,
                            value=value,
                            description=description,
                            tags=tags,
                        )
                        self.console.print(f"✅ - created address-object {name}", style="green")
                    
                    # Add to known address objects for autocompletion
                    if folder not in self.state.known_address_objects:
                        self.state.known_address_objects[folder] = set()
                    self.state.known_address_objects[folder].add(name)
                    
                except ValidationError as e:
                    self.console.print(f"Validation error: {e}", style="red")
                except APIError as e:
                    self.console.print(f"API error: {e}", style="red")
            except ValueError as e:
                self.console.print(f"Error: {e}", style="red")
                self.console.print("Usage: set address-object <name> <type> <value> [description <text>] [tags <tag1,tag2,...>]")
        else:
            self.console.print(f"Unknown object type: {object_type}", style="red")

    # Delete address-object command
    delete_parser = Cmd2ArgumentParser(description="Delete an object")
    delete_subparsers = delete_parser.add_subparsers(title="objects", dest="object_type")
    
    # Address object subparser
    addr_del_parser = delete_subparsers.add_parser("address-object", help="Delete an address object")
    addr_del_parser.add_argument("name", help="Name of the address object").completer = address_completer
    
    # Show command
    show_parser = Cmd2ArgumentParser(description="Show object details")
    show_subparsers = show_parser.add_subparsers(title="objects", dest="object_type")
    
    # Address object subparser
    addr_show_parser = show_subparsers.add_parser("address-object", help="Show address object details")
    addr_show_parser.add_argument("name", help="Name of the address object to show").completer = address_completer
    
    # Show all address objects
    addr_all_parser = show_subparsers.add_parser("address-objects", help="Show all address objects")
    
    # Search address objects - new subparser
    addr_search_parser = show_subparsers.add_parser("address-objects-filter", help="Search and filter address objects")
    addr_search_parser.add_argument("--name", help="Filter by name (substring match)")
    addr_search_parser.add_argument("--type", help="Filter by type (exact match)", choices=["ip-netmask", "ip-range", "ip-wildcard", "fqdn"])
    addr_search_parser.add_argument("--value", help="Filter by value (substring match)")
    addr_search_parser.add_argument("--tag", help="Filter by tag (substring match)")
    
    @with_category(CATEGORY_ADDRESS)
    @with_argparser(delete_parser)
    def do_delete(self, args: argparse.Namespace) -> None:
        """Delete an object."""
        if not self.state.config_mode or not self.state.current_folder:
            self.console.print("Command only available in folder edit mode", style="red")
            return

        if not self.state.sdk_client:
            self.console.print("No SDK client available.", style="red")
            return

        if args.object_type == "address-object":
            folder = self.state.current_folder
            
            try:
                self.state.sdk_client.delete_address_object(folder, args.name)
                self.console.print(f"✅ - deleted address-object {args.name}", style="green")
                
                # Remove from known address objects
                if folder in self.state.known_address_objects:
                    if args.name in self.state.known_address_objects[folder]:
                        self.state.known_address_objects[folder].remove(args.name)
                
            except ResourceNotFoundError as e:
                self.console.print(f"Error: {e}", style="red")
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
        else:
            self.console.print(f"Unknown object type: {args.object_type}", style="red")

    # Show command parser definition
    show_parser = Cmd2ArgumentParser(description="Show object details")
    show_subparsers = show_parser.add_subparsers(title="objects", dest="object_type")
    
    # Address object subparser
    addr_show_parser = show_subparsers.add_parser("address-object", help="Show address object details")
    addr_show_parser.add_argument("name", help="Name of the address object to show").completer = address_completer
    
    # Show all address objects
    addr_all_parser = show_subparsers.add_parser("address-objects", help="Show all address objects")
    
    # Search address objects - new subparser
    addr_search_parser = show_subparsers.add_parser("address-objects-filter", help="Search and filter address objects")
    addr_search_parser.add_argument("--name", help="Filter by name (substring match)")
    addr_search_parser.add_argument("--type", help="Filter by type (exact match)", choices=["ip-netmask", "ip-range", "ip-wildcard", "fqdn"])
    addr_search_parser.add_argument("--value", help="Filter by value (substring match)")
    addr_search_parser.add_argument("--tag", help="Filter by tag (substring match)")
    
    @with_category(CATEGORY_ADDRESS)
    @with_argparser(show_parser)
    def do_show(self, args: argparse.Namespace) -> None:
        """Show object details."""
        if not self.state.config_mode:
            self.console.print("Command only available in configuration mode", style="red")
            return

        if not self.state.sdk_client:
            self.console.print("No SDK client available.", style="red")
            return

        folder = self.state.current_folder
        if not folder:
            self.console.print("No folder selected", style="red")
            return

        # Map CLI types to SDK types for filtering
        cli_to_sdk_type = {
            "ip-netmask": "ip",
            "ip-range": "range",
            "ip-wildcard": "wildcard",
            "fqdn": "fqdn"
        }
        
        # Map SDK types to CLI types for display
        sdk_to_cli_type = {
            "ip": "ip-netmask",
            "range": "ip-range",
            "wildcard": "ip-wildcard",
            "fqdn": "fqdn"
        }

        if args.object_type == "address-object":
            try:
                address = self.state.sdk_client.get_address_object(folder, args.name)
                
                # Convert to dictionary for JSON display
                obj_dict = address.to_dict()
                
                # Map SDK type to CLI type for display
                if "type" in obj_dict:
                    obj_dict["type"] = sdk_to_cli_type.get(obj_dict["type"], obj_dict["type"])
                
                # Pretty print as JSON using rich
                json_str = json.dumps(obj_dict, indent=2)
                syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                self.console.print(syntax)
                
                # Add to known address objects for autocompletion
                if folder not in self.state.known_address_objects:
                    self.state.known_address_objects[folder] = set()
                self.state.known_address_objects[folder].add(args.name)
                
            except ResourceNotFoundError as e:
                self.console.print(f"Error: {e}", style="red")
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
        
        elif args.object_type == "address-objects":
            try:
                addresses = self.state.sdk_client.list_address_objects(folder)
                
                if not addresses:
                    self.console.print(f"No address objects found in folder '{folder}'", style="yellow")
                    return
                
                # Create a table for display
                table = Table(title=f"Address Objects in {folder}")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Value", style="blue")
                table.add_column("Description", style="magenta")
                table.add_column("Tags", style="yellow")
                
                for addr in addresses:
                    table.add_row(
                        addr.name,
                        sdk_to_cli_type.get(addr.type.value, addr.type.value),
                        addr.value,
                        addr.description or "",
                        ", ".join(addr.tags) if addr.tags else ""
                    )
                
                self.console.print(table)
                
                # Add to known address objects for autocompletion
                if folder not in self.state.known_address_objects:
                    self.state.known_address_objects[folder] = set()
                self.state.known_address_objects[folder].update(addr.name for addr in addresses)
                
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
                
        elif args.object_type == "address-objects-filter":
            try:
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
                
                # Get filtered addresses
                addresses = self.state.sdk_client.list_address_objects(folder, filter_criteria)
                
                if not addresses:
                    self.console.print(f"No address objects found matching criteria in folder '{folder}'", style="yellow")
                    return
                
                # Create a table for display
                filter_text = ", ".join([f"{k}='{v}'" for k, v in filter_criteria.items()])
                table = Table(title=f"Address Objects in {folder} (filtered by {filter_text})")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Value", style="blue")
                table.add_column("Description", style="magenta")
                table.add_column("Tags", style="yellow")
                
                for addr in addresses:
                    table.add_row(
                        addr.name,
                        sdk_to_cli_type.get(addr.type.value, addr.type.value),
                        addr.value,
                        addr.description or "",
                        ", ".join(addr.tags) if addr.tags else ""
                    )
                
                self.console.print(table)
                
                # Add to known address objects for autocompletion
                if folder not in self.state.known_address_objects:
                    self.state.known_address_objects[folder] = set()
                self.state.known_address_objects[folder].update(addr.name for addr in addresses)
                
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
                
        else:
            self.console.print(f"Unknown object type: {args.object_type}", style="red")


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