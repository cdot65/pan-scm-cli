"""Local configuration management commands for scm-cli.

This module provides commands to list device configuration versions
and download configuration files as XML.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Manage local device configurations")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name or serial number")

# =============================================================================================================================================================================================
# LOCAL CONFIG COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------ list ------------------------------------------------------------------------------------


@app.command("list")
def list_versions(
    device: str = DEVICE_OPTION,
):
    """List configuration versions for a device.

    Examples
    --------
    scm local list --device 007951000123456

    """
    try:
        versions = scm_client.list_local_config_versions(device=device)

        if not versions:
            typer.echo("No config versions found")
            return

        table = Table(title=f"Config Versions — {device}")
        table.add_column("Version", style="cyan")
        table.add_column("Timestamp", style="white")
        table.add_column("Serial", style="green")
        table.add_column("MD5", style="dim")

        for v in versions:
            table.add_row(
                str(v.get("local_version", "")),
                str(v.get("timestamp", "")),
                str(v.get("serial", "")),
                str(v.get("md5", "")),
            )

        console.print(table)

    except Exception as e:
        typer.echo(f"Error listing config versions: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ----------------------------------------------------------------------------------- download -----------------------------------------------------------------------------------


@app.command("download")
def download_config(
    device: str = DEVICE_OPTION,
    version: str = typer.Option(..., "--version", "-v", help="Config version number"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
):
    """Download a device configuration version as XML.

    Examples
    --------
    scm local download --device 007951000123456 --version 42
    scm local download --device 007951000123456 --version 42 --output config.xml

    """
    try:
        xml_data = scm_client.download_local_config(device=device, version=version)

        if output:
            Path(output).write_bytes(xml_data)
            typer.echo(f"Config written to {output}", err=True)
        else:
            sys.stdout.buffer.write(xml_data)
            sys.stdout.buffer.write(b"\n")

    except Exception as e:
        typer.echo(f"Error downloading config: {e!s}", err=True)
        raise typer.Exit(code=1) from e
