"""Main entry point for the scm-cli tool.

This module initializes the Typer CLI application and registers subcommands for the
various SCM configuration actions (set, delete, load) and object types.
"""

import typer

# Import object type modules
from .client import get_scm_client
from .commands import deployment, network, objects, security

# ============================================================================================================================================================================================
# MAIN CLI APPLICATION
# ============================================================================================================================================================================================

app = typer.Typer(
    name="scm",
    help="CLI for Palo Alto Networks Strata Cloud Manager",
    add_completion=True,
)

# ============================================================================================================================================================================================
# ACTION APP GROUPS
# ============================================================================================================================================================================================

# Create app groups for each action
backup_app = typer.Typer(help="Backup configurations to YAML files", name="backup")
delete_app = typer.Typer(help="Remove configurations", name="delete")
load_app = typer.Typer(help="Load configurations from YAML files", name="load")
set_app = typer.Typer(help="Create or update configurations", name="set")
show_app = typer.Typer(help="Display configurations", name="show")

# ============================================================================================================================================================================================
# APP REGISTRATION
# ============================================================================================================================================================================================

# ----------------------------------------------------------------------------------- Register Action Apps -----------------------------------------------------------------------------------

app.add_typer(backup_app, name="backup")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")
app.add_typer(set_app, name="set")
app.add_typer(show_app, name="show")

# --------------------------------------------------------------------------------- Register Module Commands ---------------------------------------------------------------------------------

# Backup commands
backup_app.add_typer(deployment.backup_app, name="deployment")
backup_app.add_typer(network.backup_app, name="network")
backup_app.add_typer(objects.backup_app, name="objects")
backup_app.add_typer(security.backup_app, name="security")

# Delete commands
delete_app.add_typer(deployment.delete_app, name="deployment")
delete_app.add_typer(network.delete_app, name="network")
delete_app.add_typer(objects.delete_app, name="objects")
delete_app.add_typer(security.delete_app, name="security")

# Load commands
load_app.add_typer(deployment.load_app, name="deployment")
load_app.add_typer(network.load_app, name="network")
load_app.add_typer(objects.load_app, name="objects")
load_app.add_typer(security.load_app, name="security")

# Set commands
set_app.add_typer(deployment.set_app, name="deployment")
set_app.add_typer(network.set_app, name="network")
set_app.add_typer(objects.set_app, name="objects")
set_app.add_typer(security.set_app, name="security")

# Show commands
show_app.add_typer(deployment.show_app, name="deployment")
show_app.add_typer(network.show_app, name="network")
show_app.add_typer(objects.show_app, name="objects")
show_app.add_typer(security.show_app, name="security")

# ============================================================================================================================================================================================
# CLI COMMANDS
# ============================================================================================================================================================================================


@app.command()
def test_auth(
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Test authentication in mock mode without making API calls",
    ),
):
    """Test authentication configuration.

    Verifies that authentication credentials are properly configured
    either from environment variables or ~/.scm-cli/config.yaml.

    If run with --mock, simulates authentication without API calls.

    Examples
    --------
        scm-cli test-auth
        scm-cli test-auth --mock

    """
    try:
        client = get_scm_client(mock=mock)
        if mock:
            typer.echo(typer.style("Authentication simulation successful (mock mode)", fg="green"))
        else:
            # The Scm client has been successfully initialized at this point
            typer.echo(typer.style("Authentication successful!", fg="green"))
            typer.echo("Successfully initialized SCM client with credentials from environment variables or config file")

            # Try to get network locations as a simple test
            try:
                # Address Objects is a basic endpoint we can use to test connectivity
                address_objects = client.address.list(folder="Shared")
                typer.echo(f"Successfully connected to SCM API. Found {len(address_objects)} address objects in Shared (Prisma Access) folder.")
            except Exception as connection_error:
                # Still consider auth successful, but note the connection issue
                typer.echo(typer.style(f"Note: Could not verify API connectivity: {str(connection_error)}", fg="yellow"))
    except Exception as e:
        typer.echo(typer.style(f"Authentication failed: {str(e)}", fg="red"))
        raise typer.Exit(code=1) from e


@app.callback()
def callback():
    """Manage Palo Alto Networks Strata Cloud Manager (SCM) configurations.

    The CLI follows the pattern: <action> <object-type> <object> [options]

    Examples
    --------
      - scm-cli set objects address-group --folder Texas --name test123 --type static
      - scm-cli delete security security-rule --folder Texas --name test123
      - scm-cli load network zone --file config/security_zones.yml
      - scm-cli show objects address --folder Texas --list
      - scm-cli show objects address --folder Texas --name webserver
      - scm-cli test-auth

    """
    pass


# ============================================================================================================================================================================================
# MAIN ENTRY POINT
# ============================================================================================================================================================================================


if __name__ == "__main__":
    app()
