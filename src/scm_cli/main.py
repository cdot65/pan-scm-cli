"""Main entry point for the scm-cli tool.

This module initializes the Typer CLI application and registers subcommands for the
various SCM configuration actions (set, delete, load) and object types.
"""

import typer

# Import object type modules
from .commands import context, deployment, insights, network, objects, security

# ============================================================================================================================================================================================
# MAIN CLI APPLICATION
# ============================================================================================================================================================================================

app = typer.Typer(
    name="scm",
    help="CLI for Palo Alto Networks Strata Cloud Manager",
)

# ============================================================================================================================================================================================
# ACTION APP GROUPS
# ============================================================================================================================================================================================

# Create app groups for each action
backup_app = typer.Typer(
    help="Backup configurations to YAML files",
    name="backup",
)
delete_app = typer.Typer(
    help="Remove configurations",
    name="delete",
)
load_app = typer.Typer(
    help="Load configurations from YAML files",
    name="load",
)
set_app = typer.Typer(
    help="Create or update configurations",
    name="set",
)
show_app = typer.Typer(
    help="Display configurations",
    name="show",
)

# ============================================================================================================================================================================================
# APP REGISTRATION
# ============================================================================================================================================================================================

# ----------------------------------------------------------------------------------- Register Action Apps -----------------------------------------------------------------------------------

app.add_typer(
    backup_app,
    name="backup",
)
app.add_typer(
    delete_app,
    name="delete",
)
app.add_typer(
    load_app,
    name="load",
)
app.add_typer(
    set_app,
    name="set",
)
app.add_typer(
    show_app,
    name="show",
)

# --------------------------------------------------------------------------------- Register Module Commands ---------------------------------------------------------------------------------

# Backup commands
backup_app.add_typer(
    network.backup_app,
    name="network",
    help="Backup network configurations",
)
backup_app.add_typer(
    objects.backup_app,
    name="object",
    help="Backup object configurations",
)
backup_app.add_typer(
    deployment.backup_app,
    name="sase",
    help="Backup SASE configurations",
)
backup_app.add_typer(
    security.backup_app,
    name="security",
    help="Backup security configurations",
)

# Delete commands
delete_app.add_typer(
    network.delete_app,
    name="network",
    help="Delete network configurations",
)
delete_app.add_typer(
    objects.delete_app,
    name="object",
    help="Delete object configurations",
)
delete_app.add_typer(
    deployment.delete_app,
    name="sase",
    help="Delete SASE configurations",
)
delete_app.add_typer(
    security.delete_app,
    name="security",
    help="Delete security configurations",
)

# Load commands
load_app.add_typer(
    network.load_app,
    name="network",
    help="Load network configurations",
)
load_app.add_typer(
    objects.load_app,
    name="object",
    help="Load object configurations",
)
load_app.add_typer(
    deployment.load_app,
    name="sase",
    help="Load SASE configurations",
)
load_app.add_typer(
    security.load_app,
    name="security",
    help="Load security configurations",
)

# Set commands
set_app.add_typer(
    network.set_app,
    name="network",
    help="Set network configurations",
)
set_app.add_typer(
    objects.set_app,
    name="object",
    help="Set object configurations",
)
set_app.add_typer(
    deployment.set_app,
    name="sase",
    help="Set SASE configurations",
)
set_app.add_typer(
    security.set_app,
    name="security",
    help="Set security configurations",
)

# Show commands
show_app.add_typer(
    network.show_app,
    name="network",
    help="Show network configurations",
)
show_app.add_typer(
    objects.show_app,
    name="object",
    help="Show object configurations",
)
show_app.add_typer(
    deployment.show_app,
    name="sase",
    help="Show SASE configurations",
)
show_app.add_typer(
    security.show_app,
    name="security",
    help="Show security configurations",
)

# ============================================================================================================================================================================================
# CLI COMMANDS
# ============================================================================================================================================================================================

# Register context management as a top-level command
app.add_typer(context.app, name="context")

# Register insights as a top-level command
app.add_typer(insights.app, name="insights")


# Note: test-auth command has been removed in favor of 'scm context test'
# Use 'scm context test' to test the current context
# Use 'scm context test <name>' to test a specific context without switching


@app.callback()
def callback():
    """Manage Palo Alto Networks Strata Cloud Manager (SCM) configurations.

    The CLI follows the pattern: <action> <object-type> <object> [options]

    Examples
    --------
      - scm set object address-group --folder Texas --name test123 --type static
      - scm delete security security-rule --folder Texas --name test123
      - scm load network zone --file config/security_zones.yml
      - scm show object address --folder Texas --list
      - scm show object address --folder Texas --name webserver
      - scm test-auth

    """
    pass


# ============================================================================================================================================================================================
# MAIN ENTRY POINT
# ============================================================================================================================================================================================


if __name__ == "__main__":
    app()
