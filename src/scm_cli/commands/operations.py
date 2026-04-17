"""Device operations commands for scm-cli.

This module provides commands to dispatch and monitor asynchronous device
jobs for route tables, FIB tables, DNS proxy, network interfaces, device
rules, BGP policy export, and logging service status.
"""

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Dispatch and monitor device operations")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name")
ASYNC_OPTION = typer.Option(False, "--async", help="Return job ID without waiting for completion")
TIMEOUT_OPTION = typer.Option(300, "--timeout", "-t", help="Sync polling timeout in seconds")


# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================

_OPERATION_COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    "route-table": [("destination", "Destination", "cyan"), ("next_hop", "Next Hop", "white"), ("interface", "Interface", "green"), ("metric", "Metric", "dim")],
    "fib-table": [("destination", "Destination", "cyan"), ("interface", "Interface", "green"), ("next_hop", "Next Hop", "white"), ("flags", "Flags", "dim")],
    "dns-proxy": [("domain", "Domain", "cyan"), ("primary", "Primary", "white"), ("secondary", "Secondary", "white"), ("status", "Status", "green")],
    "interfaces": [("name", "Name", "cyan"), ("status", "Status", "green"), ("ip", "IP Address", "white"), ("speed", "Speed", "dim")],
    "device-rules": [("name", "Name", "cyan"), ("action", "Action", "green"), ("from", "From", "white"), ("to", "To", "white")],
    "bgp-export": [("prefix", "Prefix", "cyan"), ("next_hop", "Next Hop", "white"), ("as_path", "AS Path", "dim")],
    "logging-status": [("service", "Service", "cyan"), ("status", "Status", "green"), ("last_log", "Last Log", "dim")],
}


def _run_operation(device: str, operation: str, async_mode: bool, timeout: int) -> None:
    """Dispatch an operation and display results or job ID."""
    try:
        result = scm_client.dispatch_device_operation(
            device=device,
            operation=operation,
            sync=not async_mode,
            timeout=timeout,
        )

        if async_mode:
            job_id = result.get("job_id", "unknown")
            typer.echo(f"Job dispatched: {job_id}")
            typer.echo(f"Check status with: scm operations status --job-id {job_id}")
            return

        results = result.get("results", [])
        if not results:
            typer.echo(f"No results returned for {operation}")
            return

        columns = _OPERATION_COLUMNS.get(operation, [])
        table = Table(title=f"{operation} — {device}")
        for _key, header, style in columns:
            table.add_column(header, style=style)

        for row in results:
            table.add_row(*[str(row.get(key, "")) for key, _, _ in columns])

        console.print(table)

    except Exception as e:
        typer.echo(f"Error running {operation}: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# OPERATION COMMANDS
# =============================================================================================================================================================================================


@app.command("route-table")
def route_table(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Retrieve device routing table.

    Examples
    --------
    scm operations route-table --device fw-01
    scm operations route-table --device fw-01 --async

    """
    _run_operation(device, "route-table", async_mode, timeout)


@app.command("fib-table")
def fib_table(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Retrieve forwarding information base table.

    Examples
    --------
    scm operations fib-table --device fw-01

    """
    _run_operation(device, "fib-table", async_mode, timeout)


@app.command("dns-proxy")
def dns_proxy(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Query DNS proxy configuration and status.

    Examples
    --------
    scm operations dns-proxy --device fw-01

    """
    _run_operation(device, "dns-proxy", async_mode, timeout)


@app.command("interfaces")
def interfaces(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Retrieve network interface status.

    Examples
    --------
    scm operations interfaces --device fw-01

    """
    _run_operation(device, "interfaces", async_mode, timeout)


@app.command("device-rules")
def device_rules(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Retrieve applied security rules from device.

    Examples
    --------
    scm operations device-rules --device fw-01

    """
    _run_operation(device, "device-rules", async_mode, timeout)


@app.command("bgp-export")
def bgp_export(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Export BGP routing policies.

    Examples
    --------
    scm operations bgp-export --device fw-01

    """
    _run_operation(device, "bgp-export", async_mode, timeout)


@app.command("logging-status")
def logging_status(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION):
    """Check logging service health.

    Examples
    --------
    scm operations logging-status --device fw-01

    """
    _run_operation(device, "logging-status", async_mode, timeout)


@app.command("status")
def operation_status(job_id: str = typer.Option(..., "--job-id", "-j", help="Job ID to check")):
    """Check status of a dispatched device operation job.

    Examples
    --------
    scm operations status --job-id abc-123

    """
    try:
        result = scm_client.get_device_operation_status(job_id=job_id)

        typer.echo(f"\nJob Details for ID: {result.get('job_id', job_id)}")
        typer.echo("-" * 50)
        for key, value in result.items():
            if value is not None and value != "" and value != []:
                typer.echo(f"  {key}: {value}")

    except Exception as e:
        typer.echo(f"Error checking job status: {e!s}", err=True)
        raise typer.Exit(code=1) from e
