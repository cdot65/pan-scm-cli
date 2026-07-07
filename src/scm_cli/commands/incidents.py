"""Incident management commands for scm-cli.

This module provides commands to search and view security incidents
from the SCM Unified Incident Framework.
"""

import json
import re
from datetime import datetime, timezone

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import OutputFormat, emit, info
from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Search and view security incidents")

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
@handle_command_errors("listing incidents")
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
    incidents = scm_client.list_incidents(status=status, severity=severity, product=product)

    if json_output:
        emit(incidents, OutputFormat.json)
        return

    if not incidents:
        info("No incidents found")
        return

    rows = [
        {
            "incident_id": inc.get("incident_id", ""),
            "status": inc.get("status", ""),
            "severity": inc.get("severity", ""),
            "product": inc.get("product", ""),
            "title": inc.get("title", ""),
            "raised": _format_epoch(inc.get("raised_time")),
        }
        for inc in incidents
    ]
    emit(
        rows,
        OutputFormat.table,
        columns=["incident_id", "status", "severity", "product", "title", "raised"],
        title="Security Incidents",
    )


# ------------------------------------------------------------------------------------- show ------------------------------------------------------------------------------------


@app.command("show")
@handle_command_errors("showing incident")
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
    incident = scm_client.get_incident(incident_id=incident_id)

    if json_output:
        emit(incident, OutputFormat.json)
        return

    summary = {
        "incident_id": incident.get("incident_id", incident_id),
        "status": incident.get("status", ""),
        "severity": incident.get("severity", ""),
        "product": incident.get("product", ""),
        "raised": _format_epoch(incident.get("raised_time")),
        "updated": _format_epoch(incident.get("updated_time")),
        "title": incident.get("title", ""),
    }
    emit(summary, OutputFormat.table, title=f"Incident: {incident.get('incident_id', incident_id)}")

    alerts = incident.get("alerts", [])
    if alerts:
        typer.echo(f"\nAlerts ({len(alerts)}):")
        for i, alert in enumerate(alerts, 1):
            sev = alert.get("severity", "")
            title = alert.get("title", "")
            state = alert.get("state", "")
            typer.echo(f"  {i}. [{sev}] {title}   ({state})")

    remediations_raw = incident.get("remediations", "")
    if remediations_raw:
        typer.echo("\nRemediation:")
        try:
            parsed = json.loads(remediations_raw) if isinstance(remediations_raw, str) else remediations_raw
            steps = parsed.get("remediations", []) if isinstance(parsed, dict) else []
            for rem in steps:
                dc = rem.get("dynamic_content", {})
                for j, step in enumerate(dc.get("steps", []), 1):
                    title = re.sub(r"<[^>]+>", "", step.get("title", "")).strip()
                    typer.echo(f"  {j}. {title}")
                    desc = re.sub(r"<[^>]+>", "", step.get("description", "")).strip()
                    if desc:
                        typer.echo(f"     {desc}")
            if not steps:
                typer.echo(f"  {remediations_raw}")
        except (json.JSONDecodeError, AttributeError):
            typer.echo(f"  {remediations_raw}")

    typer.echo()
