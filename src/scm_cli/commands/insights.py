"""Insights module commands for scm.

This module implements show and export commands for insights-related
data such as alerts, mobile users, locations, remote networks, service
connections, and tunnels.
"""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml

from ..utils.config import settings
from ..utils.context import get_current_context
from ..utils.sdk_client import scm_client

# ========================================================================================================================================================================================
# HELPER FUNCTIONS
# ========================================================================================================================================================================================


def show_context_info() -> None:
    """Display current context information if log level is INFO."""
    log_level = settings.get("log_level", "INFO").upper()
    if log_level == "INFO":
        current_context = get_current_context()
        if current_context:
            typer.echo(f"[INFO] Using authentication context: {current_context}", err=True)
        else:
            typer.echo(
                "[INFO] No context set, using environment variables or default settings",
                err=True,
            )


def export_data(data: list[dict[str, Any]], export_format: str, output_file: str) -> None:
    """Export data to the specified format.

    Args:
        data: List of dictionaries containing the data to export
        export_format: Format to export to ('json' or 'csv')
        output_file: Path to the output file

    """
    output_path = Path(output_file)

    if export_format == "json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        typer.echo(f"Data exported to {output_path}")

    elif export_format == "csv":
        if not data:
            typer.echo("No data to export", err=True)
            return

        # Get all unique keys from all dictionaries
        all_keys: set[str] = set()
        for item in data:
            all_keys.update(item.keys())

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(data)
        typer.echo(f"Data exported to {output_path}")


# ========================================================================================================================================================================================
# TYPE DEFINITIONS
# ========================================================================================================================================================================================

app = typer.Typer(help="Insights commands for Strata Cloud Manager")

# ========================================================================================================================================================================================
# ALERTS COMMANDS
# ========================================================================================================================================================================================


@app.command("alerts")
def show_alerts(
    list_alerts: bool = typer.Option(False, "--list", "-l", help="List all alerts"),
    alert_id: str | None = typer.Option(None, "--id", help="Get a specific alert by ID"),
    severity: str | None = typer.Option(
        None,
        "--severity",
        help="Filter alerts by severity (Critical, High, Medium, Low - case sensitive)",
    ),
    start_time: Annotated[
        datetime | None,
        typer.Option(
            "--start",
            help="Filter alerts starting from this time (ISO format)",
        ),
    ] = None,
    end_time: Annotated[
        datetime | None,
        typer.Option(
            "--end",
            help="Filter alerts up to this time (ISO format)",
        ),
    ] = None,
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    real_time: bool = typer.Option(
        False,
        "--real-time",
        help="Monitor alerts in real-time (continuous polling)",
    ),
    max_results: int = typer.Option(10, "--max-results", help="Maximum number of results to return (default: 10)"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter alerts by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show alerts from Strata Cloud Manager.

    Examples:
        # List alerts from last 7 days (default)
        scm insights alerts --list

        # List alerts from a specific date
        scm insights alerts --list --start "2025-06-20T00:00:00"

        # List alerts in a date range
        scm insights alerts --list --start "2025-06-20T00:00:00" --end "2025-06-23T23:59:59"

        # Get a specific alert
        scm insights alerts --id alert-123

        # Filter by severity
        scm insights alerts --list --severity critical

        # Export to CSV
        scm insights alerts --list --export csv --output alerts.csv

        # Real-time monitoring
        scm insights alerts --real-time

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if alert_id:
            # Get specific alert
            alert = scm_client.get_alert(alert_id=alert_id, folder=folder)
            typer.echo(yaml.dump(alert, default_flow_style=False))

        elif list_alerts:
            # List alerts with filters
            filters = {}
            if severity:
                filters["severity"] = severity
            
            # Time filtering
            if start_time:
                filters["start_time"] = start_time.isoformat()
                typer.echo(f"Filtering alerts from {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # Default to 7 days ago
                seven_days_ago = datetime.now() - timedelta(days=7)
                filters["start_time"] = seven_days_ago.isoformat()
                typer.echo(f"Note: Showing up to {max_results} most recent alerts from the last 7 days (since {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')})")
                typer.echo("Tip: Use --max-results to change the number of alerts shown.")
                
            if end_time:
                filters["end_time"] = end_time.isoformat()

            alerts = scm_client.list_alerts(folder=folder, max_results=max_results, **filters)

            if export_format and output_file:
                export_data(alerts, export_format, output_file)
            else:
                typer.echo(yaml.dump(alerts, default_flow_style=False))

        elif real_time:
            typer.echo("Starting real-time alert monitoring... (Press Ctrl+C to stop)")
            # TODO: Implement real-time monitoring with websocket or polling
            typer.echo("Real-time monitoring not yet implemented")

        else:
            typer.echo("Please specify --list, --id, or --real-time")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# MOBILE USERS COMMANDS
# ========================================================================================================================================================================================


@app.command("mobile-users")
def show_mobile_users(
    list_users: bool = typer.Option(False, "--list", "-l", help="List all mobile users"),
    user_id: str | None = typer.Option(None, "--id", help="Get a specific mobile user by ID"),
    status: str | None = typer.Option(
        None,
        "--status",
        help="Filter by status (connected, disconnected)",
    ),
    location: str | None = typer.Option(
        None,
        "--location",
        help="Filter by location",
    ),
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results to return"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show mobile users insights from Strata Cloud Manager.

    Examples:
        # List all mobile users
        scm insights mobile-users --list

        # Get a specific user
        scm insights mobile-users --id user-123

        # Filter by status
        scm insights mobile-users --list --status connected

        # Export to JSON
        scm insights mobile-users --list --export json --output users.json

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if user_id:
            # Get specific user
            user = scm_client.get_mobile_user(user_id=user_id, folder=folder)
            typer.echo(yaml.dump(user, default_flow_style=False))

        elif list_users:
            # List users with filters
            filters = {}
            if status:
                filters["status"] = status
            if location:
                filters["location"] = location

            users = scm_client.list_mobile_users(folder=folder, max_results=max_results, **filters)

            if export_format and output_file:
                export_data(users, export_format, output_file)
            else:
                typer.echo(yaml.dump(users, default_flow_style=False))

        else:
            typer.echo("Please specify --list or --id")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# LOCATIONS COMMANDS
# ========================================================================================================================================================================================


@app.command("locations")
def show_locations(
    list_locations: bool = typer.Option(False, "--list", "-l", help="List all locations"),
    location_id: str | None = typer.Option(None, "--id", help="Get a specific location by ID"),
    region: str | None = typer.Option(
        None,
        "--region",
        help="Filter by geographic region",
    ),
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results to return"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show locations insights from Strata Cloud Manager.

    Examples:
        # List all locations
        scm insights locations --list

        # Get a specific location
        scm insights locations --id loc-123

        # Filter by region
        scm insights locations --list --region us-east

        # Export to CSV
        scm insights locations --list --export csv --output locations.csv

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if location_id:
            # Get specific location
            location = scm_client.get_location(location_id=location_id, folder=folder)
            typer.echo(yaml.dump(location, default_flow_style=False))

        elif list_locations:
            # List locations with filters
            filters = {}
            if region:
                filters["region"] = region

            locations = scm_client.list_locations(folder=folder, max_results=max_results, **filters)

            if export_format and output_file:
                export_data(locations, export_format, output_file)
            else:
                typer.echo(yaml.dump(locations, default_flow_style=False))

        else:
            typer.echo("Please specify --list or --id")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# REMOTE NETWORKS COMMANDS
# ========================================================================================================================================================================================


@app.command("remote-networks")
def show_remote_networks(
    list_networks: bool = typer.Option(False, "--list", "-l", help="List all remote networks"),
    network_id: str | None = typer.Option(None, "--id", help="Get a specific remote network by ID"),
    connectivity: str | None = typer.Option(
        None,
        "--connectivity",
        help="Filter by connectivity status (connected, disconnected, degraded)",
    ),
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    show_metrics: bool = typer.Option(
        False,
        "--metrics",
        help="Include performance metrics",
    ),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results to return"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show remote networks insights from Strata Cloud Manager.

    Examples:
        # List all remote networks
        scm insights remote-networks --list

        # Get a specific network with metrics
        scm insights remote-networks --id rn-123 --metrics

        # Filter by connectivity
        scm insights remote-networks --list --connectivity degraded

        # Export to JSON
        scm insights remote-networks --list --export json --output networks.json

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if network_id:
            # Get specific network
            network = scm_client.get_remote_network_insights(network_id=network_id, folder=folder, include_metrics=show_metrics)
            typer.echo(yaml.dump(network, default_flow_style=False))

        elif list_networks:
            # List networks with filters
            filters = {}
            if connectivity:
                filters["connectivity"] = connectivity

            networks = scm_client.list_remote_network_insights(folder=folder, max_results=max_results, include_metrics=show_metrics, **filters)

            if export_format and output_file:
                export_data(networks, export_format, output_file)
            else:
                typer.echo(yaml.dump(networks, default_flow_style=False))

        else:
            typer.echo("Please specify --list or --id")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# SERVICE CONNECTIONS COMMANDS
# ========================================================================================================================================================================================


@app.command("service-connections")
def show_service_connections(
    list_connections: bool = typer.Option(False, "--list", "-l", help="List all service connections"),
    connection_id: str | None = typer.Option(None, "--id", help="Get a specific service connection by ID"),
    health_status: str | None = typer.Option(
        None,
        "--health",
        help="Filter by health status (healthy, unhealthy, degraded)",
    ),
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    show_metrics: bool = typer.Option(
        False,
        "--metrics",
        help="Include performance metrics (latency, throughput)",
    ),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results to return"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show service connections insights from Strata Cloud Manager.

    Examples:
        # List all service connections
        scm insights service-connections --list

        # Get a specific connection with metrics
        scm insights service-connections --id sc-123 --metrics

        # Filter by health status
        scm insights service-connections --list --health unhealthy

        # Export to CSV with metrics
        scm insights service-connections --list --metrics --export csv --output connections.csv

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if connection_id:
            # Get specific connection
            connection = scm_client.get_service_connection_insights(connection_id=connection_id, folder=folder, include_metrics=show_metrics)
            typer.echo(yaml.dump(connection, default_flow_style=False))

        elif list_connections:
            # List connections with filters
            filters = {}
            if health_status:
                filters["health_status"] = health_status

            connections = scm_client.list_service_connection_insights(folder=folder, max_results=max_results, include_metrics=show_metrics, **filters)

            if export_format and output_file:
                export_data(connections, export_format, output_file)
            else:
                typer.echo(yaml.dump(connections, default_flow_style=False))

        else:
            typer.echo("Please specify --list or --id")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# TUNNELS COMMANDS
# ========================================================================================================================================================================================


@app.command("tunnels")
def show_tunnels(
    list_tunnels: bool = typer.Option(False, "--list", "-l", help="List all tunnels"),
    tunnel_id: str | None = typer.Option(None, "--id", help="Get a specific tunnel by ID"),
    status: str | None = typer.Option(
        None,
        "--status",
        help="Filter by tunnel status (up, down)",
    ),
    start_time: Annotated[
        datetime | None,
        typer.Option(
            "--start",
            help="Filter historical data from this time (ISO format)",
        ),
    ] = None,
    end_time: Annotated[
        datetime | None,
        typer.Option(
            "--end",
            help="Filter historical data up to this time (ISO format)",
        ),
    ] = None,
    export_format: str | None = typer.Option(
        None,
        "--export",
        help="Export format (json, csv)",
    ),
    output_file: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for export",
    ),
    show_stats: bool = typer.Option(
        False,
        "--stats",
        help="Include performance statistics",
    ),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results to return"),
    folder: str | None = typer.Option(
        None,
        "--folder",
        help="Filter by folder",
    ),
    mock: bool = typer.Option(False, "--mock", help="Run in mock mode"),
):
    """Show tunnels insights from Strata Cloud Manager.

    Examples:
        # List all tunnels
        scm insights tunnels --list

        # Get a specific tunnel with statistics
        scm insights tunnels --id tunnel-123 --stats

        # Filter by status
        scm insights tunnels --list --status down

        # Get historical data
        scm insights tunnels --list --start 2024-01-01T00:00:00 --end 2024-01-31T23:59:59

        # Export to JSON with statistics
        scm insights tunnels --list --stats --export json --output tunnels.json

    """
    show_context_info()

    # Note: scm_client automatically uses mock mode when no credentials are available

    try:
        if tunnel_id:
            # Get specific tunnel
            tunnel = scm_client.get_tunnel(
                tunnel_id=tunnel_id,
                folder=folder,
                include_stats=show_stats,
                start_time=start_time.isoformat() if start_time else None,
                end_time=end_time.isoformat() if end_time else None,
            )
            typer.echo(yaml.dump(tunnel, default_flow_style=False))

        elif list_tunnels:
            # List tunnels with filters
            filters = {}
            if status:
                filters["status"] = status
            if start_time:
                filters["start_time"] = start_time.isoformat()
            if end_time:
                filters["end_time"] = end_time.isoformat()

            tunnels = scm_client.list_tunnels(folder=folder, max_results=max_results, include_stats=show_stats, **filters)

            if export_format and output_file:
                export_data(tunnels, export_format, output_file)
            else:
                typer.echo(yaml.dump(tunnels, default_flow_style=False))

        else:
            typer.echo("Please specify --list or --id")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
