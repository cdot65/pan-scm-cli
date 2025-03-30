"""Main entry point for the scm-cli tool.

This module initializes the Typer CLI application and registers subcommands for the
various SCM configuration actions (set, delete, load) and object types.
"""

import typer

# Import object type modules
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


@app.callback()
def callback():
    """Manage Palo Alto Networks Strata Cloud Manager (SCM) configurations.

    The CLI follows the pattern: <action> <object-type> <object> [options]

    Examples
    --------
      - scm-cli set objects address-group --folder Texas --name test123 --type static
      - scm-cli delete security security-rule --folder Texas --name test123
      - scm-cli load network zone --file config/security_zones.yml

    """
    pass


if __name__ == "__main__":
    app()
