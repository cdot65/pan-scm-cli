"""Posture module commands for scm.

This module implements commands for PAN-OS firewall Best Practice Assessment (BPA),
including config export, BPA assessment upload, and report scoring.
"""

import json
import os
import time
from pathlib import Path

import typer

from ..utils.decorators import handle_command_errors
from ..utils.sdk_client import scm_client
from ..utils.validators import BpaAssessRequest, BpaStatusResponse, PostureExport

# ===============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ===============================================================================================================================================================================================

posture_app = typer.Typer(help="Firewall posture assessment and BPA scoring")

# ===============================================================================================================================================================================================
# COMMAND OPTIONS
# ===============================================================================================================================================================================================

HOST_OPTION = typer.Option(
    None,
    "--host",
    help="PAN-OS firewall hostname or IP address",
    envvar="PANOS_HOST",
)
USER_OPTION = typer.Option(
    "automation",
    "--user",
    help="Admin username for XML API authentication",
    envvar="PANOS_USER",
)
PASSWORD_OPTION = typer.Option(
    None,
    "--password",
    help="Admin password (or set PANOS_PASSWORD env var)",
    envvar="PANOS_PASSWORD",
)
OUTPUT_OPTION = typer.Option(
    "config.xml",
    "--output",
    help="Output file path",
)
CATEGORY_OPTION = typer.Option(
    "running",
    "--category",
    help="Config category to export (running or candidate)",
)
CONFIG_OPTION = typer.Option(
    ...,
    "--config",
    help="Path to config file to assess",
)
DELETE_AFTER_OPTION = typer.Option(
    True,
    "--delete-after/--keep",
    help="Delete config from cloud after assessment",
)
TIMEOUT_OPTION = typer.Option(
    300,
    "--timeout",
    help="Max seconds to wait for BPA processing",
)
REPORT_OPTION = typer.Option(
    ...,
    "--report",
    help="Path to BPA report JSON file",
)
SCOPE_OPTION = typer.Option(
    "all",
    "--scope",
    help="BPA check scope (all, security, decryption, threat)",
)
FORMAT_OPTION = typer.Option(
    "plain",
    "--format",
    help="Output format (plain or json)",
)

# ===============================================================================================================================================================================================
# EXPORT COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("export")
@handle_command_errors("exporting config")
def export_config(
    host: str = HOST_OPTION,
    user: str = USER_OPTION,
    password: str | None = PASSWORD_OPTION,
    output: str = OUTPUT_OPTION,
    category: str = CATEGORY_OPTION,
):
    r"""Export running or candidate config from a PAN-OS firewall.

    Example:
    -------
        scm posture export \
        --host 10.0.0.1 \
        --user automation \
        --output config.xml \
        --category running

    """
    if not password:
        password = os.environ.get("PANOS_PASSWORD")
    if not password:
        typer.echo("Error: password required via --password or PANOS_PASSWORD env var", err=True)
        raise typer.Exit(code=1)

    if not host:
        typer.echo("Error: --host is required or set PANOS_HOST env var", err=True)
        raise typer.Exit(code=1)

    # Validate inputs
    export_params = PostureExport(
        host=host,
        user=user,
        password=password,
        output=output,
        category=category,
    )

    # Generate API key
    api_key = scm_client.generate_panos_api_key(
        host=export_params.host,
        user=export_params.user,
        password=export_params.password,
    )
    typer.echo(f"Generated API key for {export_params.user}@{export_params.host}", err=True)

    # Export config
    config_xml = scm_client.export_panos_config(
        host=export_params.host,
        api_key=api_key,
        category=export_params.category,
    )

    # Write to file
    output_path = Path(export_params.output)
    output_path.write_text(config_xml)
    typer.echo(f"Exported {export_params.category} config to {output_path}")
