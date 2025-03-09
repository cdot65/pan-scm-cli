#!/usr/bin/env python3
"""SCM CLI main module."""

import argparse
import json
import io
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
import logging

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

# Configure logging
logger = logging.getLogger("scm_cli.cli")

# Add this for debugging the model issue
try:
    import inspect
    from scm.config.models import AddressModel
    HAS_ADDRESS_MODEL = True
except ImportError:
    HAS_ADDRESS_MODEL = False
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .config import SCMConfig, load_oauth_credentials
from .db import CLIHistoryDB
from scm.exceptions import AuthenticationError  # Import from actual pan-scm-sdk
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
        # Configure readline behavior for handling ? key
        # This makes the '?' character a word-break character, which allows for immediate help
        import readline
        
        # Define delimiters - make ? a delimiter so readline treats it specially
        old_delims = readline.get_completer_delims()
        # Add '?' to the delimiter set but remove it from the end so it's not treated as part of a word
        readline.set_completer_delims(old_delims + '?')
        
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
        self.hidden_commands += ['alias', 'macro', 'run_pyscript', 'run_script', 'shell', 'shortcuts', 'py', 'ipy']
        self.default_to_shell = False
        
        # Configure special characters
        # Override the cmd2 question mark handling to make it immediate
        # In cmd2, this is handled by the postparsing_precmd method
        # We'll modify this to capture ? immediately
        self.question_mark = '?'
        
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
    
    # Special method to handle ? keypress - this is called when ? is typed
    # We need to override the readline handler
    def precmd(self, statement: cmd2.Statement) -> cmd2.Statement:
        """Process the command before execution."""
        # Check if question mark is in the raw input
        if '?' in statement.raw and not statement.raw.strip() == '?':
            # Get the command so far
            input_line = statement.raw.strip()
            # Find where the ? appears in the input
            q_index = input_line.find('?')
            # Get the command parts up to the ? mark
            parts = input_line[:q_index].strip().split()
            
            # Show help for the command parts so far
            self._show_contextual_help(parts)
            
            # Return an empty statement to not execute anything
            return cmd2.Statement("")
        
        return statement
        
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
            self.console.print("Initializing SCM client...", style="yellow")
            
            # Create SDK client
            self.state.sdk_client = SDKClient(config)
            self.state.client_id = config.client_id
            
            # Extract username from client_id
            self.state.username = self._extract_username(config.client_id)
            
            # Test connection
            try:
                self.state.sdk_client.test_connection()
                # Show success message
                success_text = Text("✅ Client initialized successfully", style="bold green")
                self.console.print(success_text)
                self.console.print()
                self.console.print("# " + "-" * 76)
                self.console.print("# Welcome to the SCM CLI for Strata Cloud Manager")
                self.console.print("# " + "-" * 76)
            except Exception as conn_error:
                self.console.print(
                    f"[bold red]Error:[/bold red] Failed to connect to SCM API: {str(conn_error)}", 
                    style="red"
                )
                self.console.print("Please check your credentials in the .env file:", style="yellow")
                self.console.print("  - Ensure SCM_CLIENT_ID is correct", style="yellow")
                self.console.print("  - Ensure SCM_CLIENT_SECRET is correct", style="yellow")
                self.console.print("  - Ensure SCM_TSG_ID is correct", style="yellow")
                self.console.print("  - Ensure you have valid API access to Strata Cloud Manager", style="yellow")
                sys.exit(1)
        except AuthenticationError as e:
            self.console.print(f"[bold red]Authentication Error:[/bold red] {e}", style="red")
            self.console.print("Please check your credentials in the .env file:", style="yellow")
            self.console.print("  - Ensure SCM_CLIENT_ID is correct", style="yellow")
            self.console.print("  - Ensure SCM_CLIENT_SECRET is correct", style="yellow") 
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
                
                required.add_row("name <name>", "Name of the address object (required for all operations)")
                required.add_row("type <type>", "Type of address object (ip-netmask, ip-range, fqdn) (required for new objects)")
                required.add_row("value <value>", "Value of the address object (required for new objects)")
                self.console.print(required)
                
                # Table for optional arguments
                optional = Table(title="Optional Arguments")
                optional.add_column("Argument", style="yellow", width=20)
                optional.add_column("Description", style="blue")
                
                optional.add_row("description <text>", "Description of the address object")
                optional.add_row("tags <tag1,tag2,..>", "Comma-separated list of tags (use Automation or Decryption)")
                self.console.print(optional)
                
                # Add partial update info
                partial = Table(title="Partial Update Support")
                partial.add_column("Feature", style="cyan")
                partial.add_column("Description", style="green")
                
                partial.add_row(
                    "Partial Updates",
                    "For existing objects, you can update only specific fields without specifying all required fields"
                )
                partial.add_row(
                    "Example",
                    "set address-object name test1 description \"Updated description\""
                )
                self.console.print(partial)
                
                # Table for examples
                examples = Table(title="Examples")
                examples.add_column("Command", style="magenta")
                examples.add_column("Description", style="dim")
                
                examples.add_row(
                    "set address-object name test1 type ip-netmask value 1.1.1.1/32", 
                    "Create/update an IP address object"
                )
                examples.add_row(
                    "set address-object name test2 type fqdn value example.com", 
                    "Create/update a domain name address object"
                )
                examples.add_row(
                    "set address-object name test3 type ip-range value 1.1.1.1-1.1.1.10 description \"Test\" tags Automation", 
                    "Create/update an IP range with description and tags"
                )
                self.console.print(examples)
            elif len(context) == 3 and context[1] == "address-object":
                # Show the address object types based on the context
                context_word = context[2]
                if context_word == "type":
                    table = Table(title="Available Address Object Types")
                    table.add_column("Type", style="cyan")
                    table.add_column("Description", style="green")
                    table.add_column("Example", style="yellow")
                    
                    table.add_row("ip-netmask", "IP address with netmask", "192.168.1.0/24")
                    table.add_row("ip-range", "IP address range", "192.168.1.1-192.168.1.10")
                    table.add_row("fqdn", "Fully qualified domain name", "example.com")
                    
                    self.console.print(table)
                else:
                    # General type info
                    table = Table(title="Address Object Types")
                    table.add_column("Type", style="cyan")
                    table.add_column("Description", style="green")
                    table.add_column("Example", style="yellow")
                    
                    table.add_row("ip-netmask", "IP address with netmask", "192.168.1.0/24")
                    table.add_row("ip-range", "IP address range", "192.168.1.1-192.168.1.10")
                    table.add_row("fqdn", "Fully qualified domain name", "example.com")
                    
                    self.console.print(table)
            elif len(context) == 4 and context[1] == "address-object":
                context_word = context[3] if len(context) > 3 else ""
                if context_word == "value":
                    # Value examples based on type
                    type_val = context[3]
                    table = Table(title=f"Value Format for {type_val}")
                    table.add_column("Type", style="cyan")
                    table.add_column("Example", style="green")
                    
                    if type_val == "ip-netmask":
                        table.add_row("ip-netmask", "192.168.1.0/24")
                    elif type_val == "ip-range":
                        table.add_row("ip-range", "192.168.1.1-192.168.1.10")
                    elif type_val == "fqdn":
                        table.add_row("fqdn", "example.com")
                    else:
                        # All examples
                        table.add_row("ip-netmask", "192.168.1.0/24")
                        table.add_row("ip-range", "192.168.1.1-192.168.1.10")
                        table.add_row("fqdn", "example.com")
                    
                    self.console.print(table)
                else:
                    # Generic value info
                    table = Table(title="Enter Value Based on Type")
                    table.add_column("Type", style="cyan")
                    table.add_column("Format", style="green")
                    table.add_column("Example", style="yellow")
                    
                    table.add_row("ip-netmask", "IP/netmask", "192.168.1.0/24")
                    table.add_row("ip-range", "start-end", "192.168.1.1-192.168.1.10")
                    table.add_row("fqdn", "domain name", "example.com")
                    
                    self.console.print(table)
            elif len(context) >= 5 and context[1] == "address-object":
                if len(context) == 5 or (len(context) > 5 and context[5] not in ["description", "tags"]):
                    table = Table(title="Optional Arguments")
                    table.add_column("Argument", style="cyan")
                    table.add_column("Description", style="green")
                    
                    table.add_row("description <text>", "Add a description to the address object")
                    table.add_row("tags <tag1,tag2,..>", "Add tags to the address object (use Automation or Decryption)")
                    
                    self.console.print(table)
                
        # Help for show command
        elif cmd == "show":
            if len(context) == 1:
                table = Table(title="Available Objects to Show")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")
                
                table.add_row("address-object", "Show address objects (specific or all)")
                table.add_row("address-object-filter", "Search and filter address objects")
                
                self.console.print(table)
            elif len(context) == 2 and context[1] == "address-object":
                table = Table(title="Command: show address-object [<name>]")
                table.add_column("Argument", style="cyan", width=20)
                table.add_column("Description", style="green")
                
                table.add_row("<name>", "Name of the address object (optional)")
                self.console.print(table)
                
                examples = Table(title="Examples")
                examples.add_column("Command", style="yellow")
                examples.add_column("Description", style="blue")
                examples.add_row("show address-object", "Show all address objects in current folder")
                examples.add_row("show address-object test123", "Show details of address object 'test123'")
                self.console.print(examples)
            elif len(context) == 2 and context[1] == "address-object-filter":
                table = Table(title="Command: show address-object-filter [options]")
                table.add_column("Option", style="cyan", width=20)
                table.add_column("Description", style="green")
                
                table.add_row("--name <substring>", "Filter by name (substring match)")
                table.add_row("--type <type>", "Filter by type (ip-netmask, ip-range, fqdn)")
                table.add_row("--value <substring>", "Filter by value (substring match)")
                table.add_row("--tag <substring>", "Filter by tag (substring match)")
                self.console.print(table)
                
                examples = Table(title="Examples")
                examples.add_column("Command", style="yellow")
                examples.add_column("Description", style="blue")
                examples.add_row("show address-object-filter --name web", "Find objects with 'web' in the name")
                examples.add_row("show address-object-filter --type fqdn", "Show only FQDN objects")
                examples.add_row("show address-object-filter --value 192.168", "Find objects with value containing '192.168'")
                examples.add_row("show address-object-filter --tag Automation", "Find objects with 'Automation' tag")
                self.console.print(examples)
                
        # Help for delete command
        elif cmd == "delete":
            if len(context) == 1:
                table = Table(title="Available Objects to Delete")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")
                
                table.add_row("address-object", "Delete an address object")
                self.console.print(table)
            elif len(context) == 2 and context[1] == "address-object":
                table = Table(title="Command: delete address-object <name>")
                table.add_column("Argument", style="cyan", width=20)
                table.add_column("Description", style="green")
                
                table.add_row("<name>", "Name of the address object to delete")
                self.console.print(table)
                
                examples = Table(title="Examples")
                examples.add_column("Command", style="yellow")
                examples.add_column("Description", style="blue")
                examples.add_row("delete address-object test123", "Delete the address object named 'test123'")
                self.console.print(examples)
                
        # Help for edit command
        elif cmd == "edit":
            if len(context) == 1:
                table = Table(title="Available Objects to Edit")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="green")
                
                table.add_row("folder", "Edit a specific folder")
                self.console.print(table)
            elif len(context) == 2 and context[1] == "folder":
                table = Table(title="Command: edit folder <name>")
                table.add_column("Argument", style="cyan", width=20)
                table.add_column("Description", style="green")
                
                table.add_row("<name>", "Name of the folder to edit")
                self.console.print(table)
                
                examples = Table(title="Examples")
                examples.add_column("Command", style="yellow")
                examples.add_column("Description", style="blue")
                examples.add_row("edit folder Texas", "Switch to edit mode for the 'Texas' folder")
                self.console.print(examples)
        
        # Help for history command
        elif cmd == "history":
            table = Table(title="Command: history [options]")
            table.add_column("Option", style="cyan", width=20)
            table.add_column("Description", style="green")
            
            table.add_row("--page <name>", "Page number to display, starting from 1 (default: 1)")
            table.add_row("--limit <name>", "Maximum number of history entries per page (default: 50)")
            table.add_row("--folder <folder>", "Filter history by folder")
            table.add_row("--filter <text>", "Filter history by command content")
            table.add_row("--clear", "Clear command history")
            table.add_row("--id <name>", "Show details of a specific history entry")
            self.console.print(table)
            
            examples = Table(title="Examples")
            examples.add_column("Command", style="yellow")
            examples.add_column("Description", style="blue")
            
            examples.add_row("history", "Show last 50 commands")
            examples.add_row("history --page 2", "Show second page of commands")
            examples.add_row("history --limit 20", "Show only 20 commands per page")
            examples.add_row("history --folder Texas", "Show commands from the Texas folder")
            examples.add_row("history --filter address", "Show commands containing 'address'")
            examples.add_row("history --id 5", "Show details of history entry #5")
            examples.add_row("history --clear", "Clear all command history")
            self.console.print(examples)
                
        # General help for other commands
        else:
            # Try to get help for the command
            self.do_help(cmd)

    # Special character handling - this is where we need to implement immediate
    # character by character processing to provide help for ? key
    
    # Override the readline handler to intercept key presses
    def completedefault(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Override the default completer to handle the ? key specially."""
        if text.endswith('?'):
            # Remove the ? and get the command parts
            command_parts = line[:begidx].strip().split()
            if text == '?':
                # Just ? by itself
                # Show help for the current command context
                self._show_contextual_help(command_parts)
                # Return empty list to not display completions
                return []
            else:
                # Something like 'command?'
                # Remove the ? and use as completion text
                completion_text = text[:-1]
                # Show help for this specific command
                self._show_contextual_help(command_parts + [completion_text])
                # Return empty list to not display completions
                return []
        
        # Default behavior for normal completion
        return super().completedefault(text, line, begidx, endidx)
    
    # We still need postparsing_precmd for when ? appears in a command that's fully entered
    def postparsing_precmd(self, statement: cmd2.Statement) -> cmd2.Statement:
        """Process commands after parsing but before execution."""
        if '?' in statement.raw:
            # Split the line into parts and find where the ? is
            parts = []
            current_word = ""
            in_quotes = False
            quote_char = None
            
            # Parse the command line considering quotes
            for char in statement.raw:
                if char in ['"', "'"]:
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                
                if char.isspace() and not in_quotes:
                    if current_word:
                        parts.append(current_word)
                        current_word = ""
                elif char == '?' and not in_quotes:
                    # Found a question mark - process contextual help
                    if current_word:
                        parts.append(current_word)
                    self._show_contextual_help(parts)
                    return cmd2.Statement("")
                else:
                    current_word += char
            
            # Add the last word if there is one
            if current_word and current_word != '?':
                parts.append(current_word)
                
            # Show help for the command parts we've collected
            self._show_contextual_help(parts)
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
        types = ["ip-netmask", "ip-range", "fqdn"]  # Removed ip-wildcard as it's not supported by the SCM SDK
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

    # Updated parser for set address-object that supports keyword arguments
    def parse_set_address_object(self, args: List[str]) -> Dict[str, Any]:
        """Parse the set address-object command with keyword arguments.
        
        This parser is designed to handle Junos-style CLI commands like:
        set address-object name test1 type ip-netmask value 1.1.1.1/32 description "Test desc" tags tag1,tag2
        
        It also supports partial updates (like PATCH) for existing objects:
        set address-object name test1 description "Updated description"
        
        Args:
            args: List of argument strings
            
        Returns:
            Dictionary with parsed arguments and a 'partial_update' flag
            
        Raises:
            ValueError: If required arguments are missing or format is invalid
        """
        if len(args) < 2:  # Need at least "name <value>"
            raise ValueError("Missing required arguments: must at least specify 'name'")
            
        parsed_args = {'partial_update': False}
        i = 0
        
        while i < len(args):
            # Get the keyword and advance
            keyword = args[i].lower()
            i += 1
            
            # Check if we have a value for this keyword
            if i >= len(args):
                raise ValueError(f"Missing value for {keyword}")
                
            # Process based on keyword
            if keyword == "name":
                parsed_args["name"] = args[i]
            elif keyword == "type":
                # Validate type
                valid_types = ["ip-netmask", "ip-range", "fqdn"]
                if args[i] not in valid_types:
                    valid_types_str = ", ".join(valid_types)
                    raise ValueError(f"Invalid address type: {args[i]}. Valid types are: {valid_types_str}")
                parsed_args["type"] = args[i]
            elif keyword == "value":
                parsed_args["value"] = args[i]
            elif keyword == "description":
                # Description might be quoted, so handle special case
                description = args[i]
                # If starts with quote but doesn't end with quote, collect until closing quote
                if description.startswith('"') and not description.endswith('"'):
                    j = i + 1
                    while j < len(args):
                        description += " " + args[j]
                        if args[j].endswith('"'):
                            break
                        j += 1
                    if j < len(args):
                        i = j  # Skip ahead
                # Remove surrounding quotes if present
                if description.startswith('"') and description.endswith('"'):
                    description = description[1:-1]
                parsed_args["description"] = description
            elif keyword == "tags":
                # Parse comma-separated tags
                parsed_args["tags"] = [tag.strip() for tag in args[i].split(",")]
            else:
                raise ValueError(f"Unknown keyword: {keyword}")
                
            # Advance to next keyword
            i += 1
        
        # Check if this is a partial update (missing required fields)
        required_fields = ["name", "type", "value"]
        has_all_required = all(field in parsed_args for field in required_fields)
        
        if not has_all_required:
            # Mark as a partial update - we'll validate if the object exists later
            parsed_args['partial_update'] = True
            
            # Ensure at least name is provided
            if "name" not in parsed_args:
                raise ValueError("For partial updates, at least 'name' must be specified")
                
        return parsed_args
    
    @with_category(CATEGORY_ADDRESS)
    def do_set(self, statement: cmd2.Statement) -> None:
        """Set an object's properties."""
        # Parse command
        args = statement.arg_list
        
        if not args:
            self.console.print("Missing object type", style="red")
            self.console.print("Usage: set address-object name <name> type <type> value <value> [description <text>] [tags <tag1,tag2,...>]")
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
                # Parse Junos-style keyword arguments
                if len(args) < 2:
                    self.console.print("Missing required arguments", style="red")
                    self.console.print("Usage: set address-object name <name> type <type> value <value> [description <text>] [tags <tag1,tag2,...>]")
                    return
                    
                # Parse the remaining arguments using the new keyword-based parser
                parsed_args = self.parse_set_address_object(args[1:])
                
                # Extract values from the parsed arguments
                name = parsed_args["name"]
                folder = self.state.current_folder
                is_partial_update = parsed_args.get('partial_update', False)
                
                # Start timer for overall performance
                start_time = time.time()
                
                # Enable debug mode - shows timing information
                debug_timing = True
                
                # Create timing log function
                def log_timing(operation: str, duration: float) -> None:
                    """Log timing information if debug_timing is enabled."""
                    if debug_timing:
                        self.console.print(f"[dim]DEBUG: {operation} took {duration:.3f} seconds[/dim]", style="dim")
                
                try:
                    # First check if the object exists using fetch (most efficient method)
                    with self.console.status(f"[bold yellow]Checking if address object '{name}' exists...[/bold yellow]"):
                        # Use direct fetch to check existence - fastest way
                        check_start = time.time()
                        existing_object = self.state.sdk_client.direct_fetch_address_object(folder, name)
                        check_end = time.time()
                        log_timing(f"Checking if object exists using fetch", check_end - check_start)
                    
                    # Handle partial update scenario
                    if is_partial_update:
                        if not existing_object:
                            # Can't do a partial update on a non-existent object
                            self.console.print(f"Error: Cannot perform partial update on a non-existent object: '{name}'", style="red")
                            self.console.print("For a new object, you must specify all required fields: name, type, and value", style="yellow")
                            return
                        
                        # For partial update, we need to fill in missing fields from the existing object
                        # We have an existing object, so use its values for fields that weren't provided
                        if "type" not in parsed_args:
                            parsed_args["type"] = AddressObject.sdk_to_cli_type(existing_object.type)
                        if "value" not in parsed_args:
                            parsed_args["value"] = existing_object.value
                        
                        self.console.print(f"Performing partial update on existing object: '{name}'", style="yellow")
                    
                    # Now extract the values after potentially filling in from existing object
                    addr_type = parsed_args.get("type")
                    value = parsed_args.get("value")
                    description = parsed_args.get("description")
                    tags = parsed_args.get("tags")
                    
                    # Use helper method to convert from CLI types to SDK types
                    sdk_type = AddressObject.cli_to_sdk_type(addr_type)
                    
                    # Decision based on existence check
                    if existing_object:
                        # Object exists, update it
                        self.console.print(f"Found existing object: '{name}', will update", style="yellow")
                        with self.console.status(f"[bold yellow]Updating address object '{name}'...[/bold yellow]"):
                            # For partial updates, only include the fields that were provided
                            update_args = {
                                "folder": folder,
                                "name": name,
                                "type_val": sdk_type,
                                "value": value,
                                "object_id": existing_object.id if hasattr(existing_object, 'id') else None
                            }
                            
                            # Only include optional fields if they were provided
                            if description is not None or "description" in parsed_args:
                                update_args["description"] = description
                            if tags is not None or "tags" in parsed_args:
                                update_args["tags"] = tags
                                
                            # Update the object using its ID for efficiency
                            address = self.state.sdk_client.direct_update_address_object(**update_args)
                        update_time = time.time()
                        log_timing(f"Updating object '{name}'", update_time - check_end)
                        
                        # Try to output model dump if available
                        if hasattr(address, 'model_dump') and callable(getattr(address, 'model_dump')):
                            try:
                                # Use the model_dump method to get a clean dictionary representation
                                dump_data = address.model_dump(exclude_unset=True, exclude_none=True)
                                self.console.print(f"✅ Updated address-object '{name}':", style="green")
                                self.console.print(dump_data)
                            except Exception:
                                # Fall back to simple message if model_dump fails
                                self.console.print(f"✅ - updated address-object {name}", style="green")
                        else:
                            # Use the simplified output if model_dump not available
                            self.console.print(f"✅ - updated address-object {name}", style="green")
                    else:
                        # Object doesn't exist, create it
                        if is_partial_update:
                            # This shouldn't happen because we already checked above
                            self.console.print(f"Error: Cannot create object with partial data. Must specify name, type, and value.", style="red")
                            return
                        
                        self.console.print(f"No existing object found: '{name}', will create", style="yellow")
                        with self.console.status(f"[bold yellow]Creating address object '{name}'...[/bold yellow]"):
                            address = self.state.sdk_client.direct_create_address_object(
                                folder=folder,
                                name=name,
                                type_val=sdk_type,
                                value=value,
                                description=description,
                                tags=tags
                            )
                        create_time = time.time()
                        log_timing(f"Creating object '{name}'", create_time - check_end)
                        
                        # Try to output model dump if available
                        if hasattr(address, 'model_dump') and callable(getattr(address, 'model_dump')):
                            try:
                                # Use the model_dump method to get a clean dictionary representation
                                dump_data = address.model_dump(exclude_unset=True, exclude_none=True)
                                self.console.print(f"✅ Created address-object '{name}':", style="green")
                                self.console.print(dump_data)
                            except Exception:
                                # Fall back to simple message if model_dump fails
                                self.console.print(f"✅ - created address-object {name}", style="green")
                        else:
                            # Use the simplified output if model_dump not available
                            self.console.print(f"✅ - created address-object {name}", style="green")
                    
                    # Add to known address objects for autocompletion
                    if folder not in self.state.known_address_objects:
                        self.state.known_address_objects[folder] = set()
                    self.state.known_address_objects[folder].add(name)
                    
                except ValidationError as e:
                    if is_partial_update:
                        self.console.print(f"Validation error during partial update: {e}", style="red")
                        self.console.print("Hint: For partial updates, make sure the object exists and you're providing valid fields", style="yellow")
                    else:
                        self.console.print(f"Validation error: {e}", style="red")
                except APIError as e:
                    error_message = str(e)
                    self.console.print(f"API error: {error_message}", style="red")
                    
                    # Provide helpful feedback for common errors
                    if "does not exist" in error_message.lower() or "not found" in error_message.lower():
                        self.console.print("Hint: Make sure the object exists before attempting a partial update", style="yellow")
                    elif "permission" in error_message.lower() or "access" in error_message.lower():
                        self.console.print("Hint: You may not have permission to modify this object", style="yellow")
            except ValueError as e:
                self.console.print(f"Error: {e}", style="red")
                self.console.print("Usage: set address-object name <name> type <type> value <value> [description <text>] [tags <tag1,tag2,...>]")
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
    addr_show_parser.add_argument("name", nargs="?", default=None, help="Name of the address object to show (optional - if omitted, shows all objects)").completer = address_completer
    
    # Search address objects - subparser
    addr_search_parser = show_subparsers.add_parser("address-object-filter", help="Search and filter address objects")
    addr_search_parser.add_argument("--name", help="Filter by name (substring match)")
    addr_search_parser.add_argument("--type", help="Filter by type (exact match)", choices=["ip-netmask", "ip-range", "fqdn"])
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
    addr_show_parser.add_argument("name", nargs="?", default=None, help="Name of the address object to show (optional - if omitted, shows all objects)").completer = address_completer
    
    # Show all address objects - keeping this for backward compatibility
    addr_all_parser = show_subparsers.add_parser("address-objects", help="Show all address objects")
    
    # Search address objects - new subparser
    addr_search_parser = show_subparsers.add_parser("address-objects-filter", help="Search and filter address objects")
    addr_search_parser.add_argument("--name", help="Filter by name (substring match)")
    addr_search_parser.add_argument("--type", help="Filter by type (exact match)", choices=["ip-netmask", "ip-range", "fqdn"])
    addr_search_parser.add_argument("--value", help="Filter by value (substring match)")
    addr_search_parser.add_argument("--tag", help="Filter by tag (substring match)")
    
    @with_category(CATEGORY_ADDRESS)
    @with_argparser(show_parser)
    def do_show(self, args: argparse.Namespace) -> None:
        """Show object details."""
        # Start timer for overall performance
        start_time = time.time()
        
        # Enable debug mode - shows timing information
        # Set to False in production
        debug_timing = True
        
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
            
        # Create timing log function
        def log_timing(operation: str, duration: float) -> None:
            """Log timing information if debug_timing is enabled."""
            if debug_timing:
                self.console.print(f"[dim]DEBUG: {operation} took {duration:.3f} seconds[/dim]", style="dim")

        # Map CLI types to SDK types for filtering
        cli_to_sdk_type = {
            "ip-netmask": "ip",
            "ip-range": "range",
            "fqdn": "fqdn"
        }
        
        # Map SDK types to CLI types for display
        sdk_to_cli_type = {
            "ip": "ip-netmask",
            "range": "ip-range",
            "fqdn": "fqdn"
        }

        if args.object_type == "address-object":
            try:
                # If no name is provided, show all address objects in the folder
                if args.name is None:
                    # Start timer for API call
                    api_start_time = time.time()
                    
                    # Show a loading message
                    with self.console.status("[bold yellow]Fetching address objects...[/bold yellow]"):
                        addresses = self.state.sdk_client.list_address_objects(folder)
                    
                    api_end_time = time.time()
                    log_timing("API call to list_address_objects", api_end_time - api_start_time)
                    
                    if not addresses:
                        self.console.print(f"No address objects found in folder '{folder}'", style="yellow")
                        return
                    
                    # Start timer for rendering
                    render_start_time = time.time()
                    
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
                            sdk_to_cli_type.get(addr.type, addr.type) if not hasattr(addr.type, 'value') else sdk_to_cli_type.get(addr.type.value, addr.type.value),
                            addr.value,
                            addr.description or "",
                            ", ".join(addr.tags) if addr.tags else ""
                        )
                    
                    self.console.print(table)
                    
                    render_end_time = time.time()
                    log_timing("Rendering table", render_end_time - render_start_time)
                    
                    # Add to known address objects for autocompletion
                    if folder not in self.state.known_address_objects:
                        self.state.known_address_objects[folder] = set()
                    self.state.known_address_objects[folder].update(addr.name for addr in addresses)
                else:
                    # Show a specific address object using direct fetch for best performance
                    api_start_time = time.time()
                    
                    # Show a loading message
                    with self.console.status(f"[bold yellow]Fetching address object '{args.name}'...[/bold yellow]"):
                        address = self.state.sdk_client.direct_fetch_address_object(folder, args.name)
                    
                    api_end_time = time.time()
                    log_timing(f"API call to direct_fetch_address_object for '{args.name}'", api_end_time - api_start_time)
                    
                    # Check if the object was found
                    if not address:
                        self.console.print(f"Address object '{args.name}' not found in folder '{folder}'", style="red")
                        return
                    
                    # Start timer for rendering
                    render_start_time = time.time()
                    
                    # Try to use model_dump if available
                    if hasattr(address, 'model_dump') and callable(getattr(address, 'model_dump')):
                        try:
                            # Use the Pydantic model_dump method for cleaner output
                            logger.debug("Using model_dump method for response")
                            obj_dict = address.model_dump(exclude_unset=True, exclude_none=True)
                            
                            # Map SDK type to CLI type for display if needed
                            if "type" in obj_dict:
                                obj_dict["type"] = sdk_to_cli_type.get(obj_dict["type"], obj_dict["type"])
                            
                            # Pretty print as JSON using rich
                            json_str = json.dumps(obj_dict, indent=2)
                            syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                            self.console.print(syntax)
                        except Exception as e:
                            logger.debug(f"model_dump failed: {str(e)}, falling back to to_dict")
                            # Fall back to to_dict if model_dump fails
                            obj_dict = address.to_dict()
                            
                            # Map SDK type to CLI type for display
                            if "type" in obj_dict:
                                obj_dict["type"] = sdk_to_cli_type.get(obj_dict["type"], obj_dict["type"])
                            
                            # Pretty print as JSON using rich
                            json_str = json.dumps(obj_dict, indent=2)
                            syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                            self.console.print(syntax)
                    else:
                        # Convert to dictionary for JSON display using our adapter
                        obj_dict = address.to_dict()
                        
                        # Map SDK type to CLI type for display
                        if "type" in obj_dict:
                            obj_dict["type"] = sdk_to_cli_type.get(obj_dict["type"], obj_dict["type"])
                        
                        # Pretty print as JSON using rich
                        json_str = json.dumps(obj_dict, indent=2)
                        syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                        self.console.print(syntax)
                    
                    render_end_time = time.time()
                    log_timing("Rendering object details", render_end_time - render_start_time)
                    
                    # Add to known address objects for autocompletion
                    if folder not in self.state.known_address_objects:
                        self.state.known_address_objects[folder] = set()
                    self.state.known_address_objects[folder].add(args.name)
                
            except ResourceNotFoundError as e:
                self.console.print(f"Error: {e}", style="red")
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
        
        # If no name provided, show all objects
        elif args.object_type == "address-object" and not args.name:
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
                        sdk_to_cli_type.get(addr.type, addr.type) if not hasattr(addr.type, 'value') else sdk_to_cli_type.get(addr.type.value, addr.type.value),
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
                
        elif args.object_type == "address-object-filter":
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
                        sdk_to_cli_type.get(addr.type, addr.type) if not hasattr(addr.type, 'value') else sdk_to_cli_type.get(addr.type.value, addr.type.value),
                        addr.value,
                        addr.description or "",
                        ", ".join(addr.tags) if addr.tags else ""
                    )
                
                self.console.print(table)
                
                # Add to known address objects for autocompletion
                if folder not in self.state.known_address_objects:
                    self.state.known_address_objects[folder] = set()
                self.state.known_address_objects[folder].update(addr.name for addr in addresses)
                
            except ResourceNotFoundError as e:
                self.console.print(f"Error: {e}", style="red")
            except APIError as e:
                self.console.print(f"API error: {e}", style="red")
                
        else:
            self.console.print(f"Unknown object type: {args.object_type}", style="red")
        
        # Log overall timing
        end_time = time.time()
        log_timing("Total execution", end_time - start_time)


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