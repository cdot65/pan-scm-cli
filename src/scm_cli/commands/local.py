"""Local configuration management commands for scm-cli.

This module provides commands to list device configuration versions
and download configuration files as XML.
"""

import sys
from pathlib import Path

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, success
from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Manage local device configurations")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name or serial number")

# =============================================================================================================================================================================================
# LOCAL CONFIG COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------ list ------------------------------------------------------------------------------------


@app.command("list")
@handle_command_errors("listing config versions")
def list_versions(
    device: str = DEVICE_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """List configuration versions for a device.

    Examples
    --------
    scm local list --device 007951000123456

    """
    try:
        versions = scm_client.list_local_config_versions(device=device)
    except ValueError as e:
        if "Invalid error response format" in str(e):
            error("The Local Config API returned 404. This API may not be available for your SCM tenant or device type. Contact Palo Alto Networks support to verify Local Config API access.")
            raise typer.Exit(code=1) from e
        raise

    emit(
        versions,
        output,
        columns=["local_version", "timestamp", "serial", "md5"],
        title=f"Config Versions — {device}",
    )


# ----------------------------------------------------------------------------------- download -----------------------------------------------------------------------------------


@app.command("download")
@handle_command_errors("downloading config")
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
    xml_data = scm_client.download_local_config(device=device, version=version)

    if output:
        Path(output).write_bytes(xml_data)
        success(f"Config written to {output}")
    else:
        sys.stdout.buffer.write(xml_data)
        sys.stdout.buffer.write(b"\n")
