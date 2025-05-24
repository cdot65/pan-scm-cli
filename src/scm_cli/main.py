"""Main entry point for the scm-cli tool.

This module initializes the Typer CLI application and registers subcommands for the
various SCM configuration actions (set, delete, load) and object types.
"""

import typer

# Import object type modules
from .client import get_scm_client
from .commands import deployment, network, objects, security

app = typer.Typer(
    name="scm-cli",
    help="CLI for Palo Alto Networks Strata Cloud Manager",
    add_completion=True,
)

# Create app groups for each action
set_app = typer.Typer(help="Create or update configurations", name="set")
delete_app = typer.Typer(help="Remove configurations", name="delete")
load_app = typer.Typer(help="Load configurations from YAML files", name="load")

# Register the action apps with the main app
app.add_typer(set_app, name="set")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")

# Register object type apps with each action
# Objects module
set_app.add_typer(objects.set_app, name="objects")
delete_app.add_typer(objects.delete_app, name="objects")
load_app.add_typer(objects.load_app, name="objects")

# Network module
set_app.add_typer(network.set_app, name="network")
delete_app.add_typer(network.delete_app, name="network")
load_app.add_typer(network.load_app, name="network")

# Security module
set_app.add_typer(security.set_app, name="security")
delete_app.add_typer(security.delete_app, name="security")
load_app.add_typer(security.load_app, name="security")

# Deployment module
set_app.add_typer(deployment.set_app, name="deployment")
delete_app.add_typer(deployment.delete_app, name="deployment")
load_app.add_typer(deployment.load_app, name="deployment")


@app.command()
def test_auth(
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Test authentication in mock mode without making API calls",
    )
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
      - scm-cli test-auth

    """
    pass


if __name__ == "__main__":
    app()
