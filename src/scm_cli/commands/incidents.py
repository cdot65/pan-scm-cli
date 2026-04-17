"""Incident management commands for scm-cli.

This module provides commands to search and view security incidents
from the SCM Unified Incident Framework.
"""

import json
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Search and view security incidents")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

STATUS_OPTION = typer.Option(None, "--status", "-s", help="Filter by status (open, closed, in_progress)")
SEVERITY_OPTION = typer.Option(None, "--severity", help="Filter by severity (critical, high, medium, low, informational)")
PRODUCT_OPTION = typer.Option(None, "--product", "-p", help="Filter by product name")
JSON_OPTION = typer.Option(False, "--json", "-j", help="Output as JSON")


def _format_epoch(epoch: int | str | None) -> str:
    """Convert epoch timestamp (seconds or ms) to human-readable date."""
    if epoch is None:
        return ""
    if isinstance(epoch, str):
        return epoch
    if epoch > 1_000_000_000_000:
        return datetime.fromtimestamp(epoch / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


# =============================================================================================================================================================================================
# INCIDENTS COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------- list ------------------------------------------------------------------------------------


@app.command("list")
def list_incidents(
    status: str | None = STATUS_OPTION,
    severity: str | None = SEVERITY_OPTION,
    product: str | None = PRODUCT_OPTION,
    json_output: bool = JSON_OPTION,
):
    """Search security incidents with optional filters.

    Examples
    --------
    scm incidents list
    scm incidents list --status open --severity high
    scm incidents list --product "Prisma Access"
    scm incidents list --json

    """
    try:
        incidents = scm_client.list_incidents(status=status, severity=severity, product=product)

        if json_output:
            typer.echo(json.dumps(incidents, indent=2))
            return

        if not incidents:
            typer.echo("No incidents found")
            return

        table = Table(title="Security Incidents", show_lines=True)
        table.add_column("ID", style="cyan", no_wrap=True, max_width=12)
        table.add_column("Status", style="white", no_wrap=True)
        table.add_column("Severity", style="white", no_wrap=True)
        table.add_column("Product", style="white", no_wrap=True)
        table.add_column("Title", style="dim", max_width=50)
        table.add_column("Raised", style="white", no_wrap=True)

        severity_styles = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "green", "informational": "dim"}

        for inc in incidents:
            sev = inc.get("severity", "")
            sev_style = severity_styles.get(sev, "white")
            status_val = inc.get("status", "")
            status_style = "green" if status_val == "closed" else ("yellow" if status_val == "in_progress" else "white")
            inc_id = str(inc.get("incident_id", ""))
            short_id = inc_id[:8] + "..." if len(inc_id) > 12 else inc_id
            table.add_row(
                short_id,
                f"[{status_style}]{status_val}[/{status_style}]",
                f"[{sev_style}]{sev}[/{sev_style}]",
                str(inc.get("product", "")),
                str(inc.get("title", "")),
                _format_epoch(inc.get("raised_time")),
            )

        console.print(table)

    except Exception as e:
        typer.echo(f"Error listing incidents: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ------------------------------------------------------------------------------------- show ------------------------------------------------------------------------------------


@app.command("show")
def show_incident(
    incident_id: str = typer.Argument(..., help="Incident ID to show"),
    json_output: bool = JSON_OPTION,
):
    """Show detailed incident information including alerts and remediation.

    Examples
    --------
    scm incidents show INC-2026-04-001
    scm incidents show INC-2026-04-001 --json

    """
    try:
        incident = scm_client.get_incident(incident_id=incident_id)

        if json_output:
            typer.echo(json.dumps(incident, indent=2))
            return

        typer.echo(f"\nIncident: {incident.get('incident_id', incident_id)}")
        typer.echo(f"Status:   {incident.get('status', '')}")
        typer.echo(f"Severity: {incident.get('severity', '')}")
        typer.echo(f"Product:  {incident.get('product', '')}")
        typer.echo(f"Raised:   {_format_epoch(incident.get('raised_time'))}")
        typer.echo(f"Updated:  {_format_epoch(incident.get('updated_time'))}")
        typer.echo(f"Title:    {incident.get('title', '')}")

        alerts = incident.get("alerts", [])
        if alerts:
            typer.echo(f"\nAlerts ({len(alerts)}):")
            for i, alert in enumerate(alerts, 1):
                sev = alert.get("severity", "")
                title = alert.get("title", "")
                state = alert.get("state", "")
                typer.echo(f"  {i}. [{sev}] {title}   ({state})")

        remediations = incident.get("remediations", "")
        if remediations:
            typer.echo(f"\nRemediations:\n  {remediations}")

        typer.echo()

    except Exception as e:
        typer.echo(f"Error showing incident: {e!s}", err=True)
        raise typer.Exit(code=1) from e
