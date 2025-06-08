"""Context management commands for scm-cli.

This module provides commands to manage multiple SCM tenant contexts,
allowing users to switch between different authentication profiles.
"""

import typer
from rich.console import Console
from rich.table import Table

from ..utils.context import (
    create_context,
    delete_context,
    get_context_config,
    get_current_context,
    list_contexts,
    set_current_context,
)

app = typer.Typer(help="Manage authentication contexts for multiple SCM tenants")
console = Console()


# ############################################################################
# list command
# ############################################################################
@app.command("list", help="List all available contexts")
def list_command():
    """List all available contexts with the current context highlighted."""
    contexts = list_contexts()
    current = get_current_context()

    if not contexts:
        console.print("[yellow]No contexts found.[/yellow]")
        console.print("\nCreate a context with: [cyan]scm context create <name>[/cyan]")
        return

    table = Table(title="SCM Authentication Contexts")
    table.add_column("Context", style="cyan")
    table.add_column("Current", style="green")
    table.add_column("Client ID", style="dim")

    for context_name in contexts:
        is_current = "✓" if context_name == current else ""
        try:
            config = get_context_config(context_name)
            client_id = config.get("client_id", "")
            # Mask part of client ID for security
            if client_id and "@" in client_id:
                parts = client_id.split("@")
                masked_id = f"{parts[0][:10]}...@{parts[1]}"
            else:
                masked_id = client_id[:20] + "..." if len(client_id) > 20 else client_id
        except Exception:
            masked_id = "[error reading config]"

        table.add_row(context_name, is_current, masked_id)

    console.print(table)

    if not current:
        console.print("\n[yellow]No context currently active.[/yellow]")
        console.print("Set a context with: [cyan]scm context use <name>[/cyan]")


# ############################################################################
# show command
# ############################################################################
@app.command("show", help="Show details of a context")
def show_command(
    context_name: str = typer.Argument(
        None,
        help="Context name to show. If not provided, shows current context.",
    ),
):
    """Show detailed information about a context."""
    try:
        # If no context specified, use current
        if not context_name:
            context_name = get_current_context()
            if not context_name:
                console.print("[red]No current context set.[/red]")
                return

        config = get_context_config(context_name)

        console.print(f"\n[bold cyan]Context: {context_name}[/bold cyan]")
        if context_name == get_current_context():
            console.print("[green]Status: Active[/green]")

        console.print("\n[bold]Configuration:[/bold]")
        console.print(f"  Client ID: {config.get('client_id', 'Not set')}")
        console.print(f"  TSG ID: {config.get('tsg_id', 'Not set')}")
        console.print(f"  Log Level: {config.get('log_level', 'INFO')}")

        # Don't show the secret, just indicate if it's set
        if config.get("client_secret"):
            console.print("  Client Secret: [dim]***** (configured)[/dim]")
        else:
            console.print("  Client Secret: [red]Not set[/red]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


# ############################################################################
# create command
# ############################################################################
@app.command("create", help="Create a new context")
def create_command(
    context_name: str = typer.Argument(..., help="Name for the new context"),
    client_id: str = typer.Option(
        ...,
        "--client-id",
        "-i",
        prompt=True,
        help="SCM client ID",
    ),
    client_secret: str = typer.Option(
        ...,
        "--client-secret",
        "-s",
        prompt=True,
        hide_input=True,
        help="SCM client secret",
    ),
    tsg_id: str = typer.Option(
        ...,
        "--tsg-id",
        "-t",
        prompt=True,
        help="Tenant Service Group ID",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level",
    ),
    set_current: bool = typer.Option(
        True,
        "--set-current/--no-set-current",
        help="Set as current context after creation",
    ),
):
    """Create a new authentication context."""
    try:
        create_context(
            context_name=context_name,
            client_id=client_id,
            client_secret=client_secret,
            tsg_id=tsg_id,
            log_level=log_level,
        )

        console.print(f"[green]✓ Context '{context_name}' created successfully[/green]")

        if set_current:
            set_current_context(context_name)
            console.print(f"[green]✓ Context '{context_name}' set as current[/green]")

    except Exception as e:
        console.print(f"[red]Error creating context: {e}[/red]")
        raise typer.Exit(1) from e


# ############################################################################
# use command
# ############################################################################
@app.command("use", help="Switch to a different context")
def use_command(
    context_name: str = typer.Argument(..., help="Context name to switch to"),
):
    """Switch to a different authentication context."""
    try:
        set_current_context(context_name)
        console.print(f"[green]✓ Switched to context '{context_name}'[/green]")

        # Show a summary of the context
        config = get_context_config(context_name)
        console.print(f"\n[dim]Client ID: {config.get('client_id', 'Not set')}[/dim]")
        console.print(f"[dim]TSG ID: {config.get('tsg_id', 'Not set')}[/dim]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")

        # Show available contexts
        contexts = list_contexts()
        if contexts:
            console.print("\nAvailable contexts:")
            for ctx in contexts:
                console.print(f"  - {ctx}")
        else:
            console.print("\nNo contexts found. Create one with: [cyan]scm context create <name>[/cyan]")

        raise typer.Exit(1) from e


# ############################################################################
# delete command
# ############################################################################
@app.command("delete", help="Delete a context")
def delete_command(
    context_name: str = typer.Argument(..., help="Context name to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
):
    """Delete an authentication context."""
    try:
        # Confirmation prompt
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete context '{context_name}'?")
            if not confirm:
                console.print("[yellow]Deletion cancelled[/yellow]")
                return

        # Check if it's the current context
        if get_current_context() == context_name:
            console.print(f"[yellow]Warning: '{context_name}' is the current context. It will be unset.[/yellow]")

        delete_context(context_name)
        console.print(f"[green]✓ Context '{context_name}' deleted[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


# ############################################################################
# current command
# ############################################################################
@app.command("current", help="Show the current context")
def current_command():
    """Show the current active context."""
    current = get_current_context()

    if current:
        console.print(f"[green]Current context: {current}[/green]")

        # Show basic info
        try:
            config = get_context_config(current)
            console.print(f"\n[dim]Client ID: {config.get('client_id', 'Not set')}[/dim]")
            console.print(f"[dim]TSG ID: {config.get('tsg_id', 'Not set')}[/dim]")
        except Exception:
            console.print("[red]Error reading context configuration[/red]")
    else:
        console.print("[yellow]No current context set[/yellow]")
        console.print("\nSet a context with: [cyan]scm context use <name>[/cyan]")
        console.print("Or create one with: [cyan]scm context create <name>[/cyan]")


# ############################################################################
# test command
# ############################################################################
@app.command("test", help="Test authentication for a context")
def test_command(
    context_name: str = typer.Argument(
        None,
        help="Context name to test. If not provided, tests current context.",
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Test authentication in mock mode without making API calls",
    ),
):
    """Test authentication for a specific context.

    Temporarily switches to the specified context, tests authentication,
    then restores the previous context.
    """
    from oauthlib.oauth2.rfc6749.errors import InvalidClientError
    from scm.client import Scm
    from scm.exceptions import APIError

    # Save current context
    original_context = get_current_context()

    try:
        # Determine which context to test
        if not context_name:
            context_name = original_context
            if not context_name:
                console.print("[red]No context specified and no current context set.[/red]")
                console.print("Specify a context: [cyan]scm context test <name>[/cyan]")
                console.print("Or set a current context: [cyan]scm context use <name>[/cyan]")
                raise typer.Exit(1)

        # Get context configuration
        try:
            config = get_context_config(context_name)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1) from e

        console.print(f"[cyan]Testing authentication for context: {context_name}[/cyan]")

        if mock:
            console.print("[green]✓ Authentication simulation successful (mock mode)[/green]")
            console.print(f"  Client ID: {config.get('client_id', 'Not set')}")
            console.print(f"  TSG ID: {config.get('tsg_id', 'Not set')}")
            return

        # Test with real API
        try:
            # Validate required fields
            if not all(
                [
                    config.get("client_id"),
                    config.get("client_secret"),
                    config.get("tsg_id"),
                ]
            ):
                missing = []
                if not config.get("client_id"):
                    missing.append("client_id")
                if not config.get("client_secret"):
                    missing.append("client_secret")
                if not config.get("tsg_id"):
                    missing.append("tsg_id")
                console.print(f"[red]✗ Missing required fields: {', '.join(missing)}[/red]")
                raise typer.Exit(1)

            # Initialize the SCM client with context credentials
            client = Scm(
                client_id=config.get("client_id"),
                client_secret=config.get("client_secret"),
                tsg_id=config.get("tsg_id"),
                log_level=config.get("log_level", "INFO"),
            )

            console.print("[green]✓ Authentication successful![/green]")
            console.print(f"  Client ID: {config.get('client_id')}")
            console.print(f"  TSG ID: {config.get('tsg_id')}")

            # Try to list address objects as a connectivity test
            try:
                with console.status("[dim]Verifying API connectivity...[/dim]"):
                    address_objects = client.address.list(folder="Shared")

                console.print(f"[green]✓ API connectivity verified[/green] (found {len(address_objects)} address objects in Shared folder)")
            except Exception as conn_error:
                console.print("[yellow]⚠ Authentication successful but could not verify API connectivity:[/yellow]")
                console.print(f"  {str(conn_error)}")

        except (APIError, InvalidClientError) as e:
            error_msg = str(e)
            if "invalid_client" in error_msg or "Client authentication failed" in error_msg:
                console.print("[red]✗ Authentication failed: Invalid client credentials[/red]")
                console.print("\n[yellow]Please verify your credentials:[/yellow]")
                console.print(f"  • Client ID: {config.get('client_id')}")
                console.print(f"  • TSG ID: {config.get('tsg_id')}")
                console.print("  • Client Secret: ******* (hidden)")
                console.print("\n[cyan]To update credentials:[/cyan]")
                console.print(f"  scm context create {context_name} --client-id <id> --client-secret <secret> --tsg-id <tsg>")
            else:
                console.print(f"[red]✗ Authentication failed: {error_msg}[/red]")
            raise typer.Exit(1) from e
        except Exception as e:
            console.print(f"[red]✗ Authentication failed: {str(e)}[/red]")
            raise typer.Exit(1) from e

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error during test: {str(e)}[/red]")
        raise typer.Exit(1) from e
