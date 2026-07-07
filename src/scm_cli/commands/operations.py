"""Device operations commands for scm-cli.

This module provides commands to dispatch and monitor asynchronous device
jobs for route tables, FIB tables, DNS proxy, network interfaces, device
rules, BGP policy export, and logging service status.
"""

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Dispatch and monitor device operations")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name or serial number")
ASYNC_OPTION = typer.Option(False, "--async", help="Return job ID without waiting for completion")
TIMEOUT_OPTION = typer.Option(300, "--timeout", "-t", help="Sync polling timeout in seconds")


# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================

_OPERATION_COLUMNS: dict[str, list[str]] = {
    "route-table": ["destination", "next_hop", "interface", "metric"],
    "fib-table": ["destination", "interface", "next_hop", "flags"],
    "dns-proxy": ["domain", "primary", "secondary", "status"],
    "interfaces": ["name", "status", "ip", "speed"],
    "device-rules": ["name", "action", "from", "to"],
    "bgp-export": ["prefix", "next_hop", "as_path"],
    "logging-status": ["service", "status", "last_log"],
}


def _run_operation(device: str, operation: str, async_mode: bool, timeout: int, output: OutputFormat) -> None:
    """Dispatch an operation and display results or job ID."""
    try:
        result = scm_client.dispatch_device_operation(
            device=device,
            operation=operation,
            sync=not async_mode,
            timeout=timeout,
        )
    except ValueError as e:
        if "Invalid error response format" in str(e):
            error(
                f"The Operations API returned 404 for {operation}. "
                "This API may not be available for your SCM tenant or device type. "
                "Contact Palo Alto Networks support to verify Operations API access."
            )
            raise typer.Exit(code=1) from e
        raise

    if async_mode:
        job_id = result.get("job_id", "unknown")
        success(f"Job dispatched: {job_id}")
        info(f"Check status with: scm operations status --job-id {job_id}")
        return

    results = result.get("results", [])
    emit(results, output, columns=_OPERATION_COLUMNS.get(operation), title=f"{operation} — {device}")


# =============================================================================================================================================================================================
# OPERATION COMMANDS
# =============================================================================================================================================================================================


@app.command("route-table")
@handle_command_errors("running route-table")
def route_table(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Retrieve device routing table.

    Examples
    --------
    scm operations route-table --device 007951000123456
    scm operations route-table --device 007951000123456 --async

    """
    _run_operation(device, "route-table", async_mode, timeout, output)


@app.command("fib-table")
@handle_command_errors("running fib-table")
def fib_table(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Retrieve forwarding information base table.

    Examples
    --------
    scm operations fib-table --device 007951000123456

    """
    _run_operation(device, "fib-table", async_mode, timeout, output)


@app.command("dns-proxy")
@handle_command_errors("running dns-proxy")
def dns_proxy(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Query DNS proxy configuration and status.

    Examples
    --------
    scm operations dns-proxy --device 007951000123456

    """
    _run_operation(device, "dns-proxy", async_mode, timeout, output)


@app.command("interfaces")
@handle_command_errors("running interfaces")
def interfaces(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Retrieve network interface status.

    Examples
    --------
    scm operations interfaces --device 007951000123456

    """
    _run_operation(device, "interfaces", async_mode, timeout, output)


@app.command("device-rules")
@handle_command_errors("running device-rules")
def device_rules(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Retrieve applied security rules from device.

    Examples
    --------
    scm operations device-rules --device 007951000123456

    """
    _run_operation(device, "device-rules", async_mode, timeout, output)


@app.command("bgp-export")
@handle_command_errors("running bgp-export")
def bgp_export(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Export BGP routing policies.

    Examples
    --------
    scm operations bgp-export --device 007951000123456

    """
    _run_operation(device, "bgp-export", async_mode, timeout, output)


@app.command("logging-status")
@handle_command_errors("running logging-status")
def logging_status(device: str = DEVICE_OPTION, async_mode: bool = ASYNC_OPTION, timeout: int = TIMEOUT_OPTION, output: OutputFormat = OUTPUT_OPTION):
    """Check logging service health.

    Examples
    --------
    scm operations logging-status --device 007951000123456

    """
    _run_operation(device, "logging-status", async_mode, timeout, output)


@app.command("status")
@handle_command_errors("checking job status")
def operation_status(
    job_id: str = typer.Option(..., "--job-id", "-j", help="Job ID to check"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Check status of a dispatched device operation job.

    Examples
    --------
    scm operations status --job-id abc-123

    """
    result = scm_client.get_device_operation_status(job_id=job_id)

    details = {key: value for key, value in result.items() if value is not None and value != "" and value != []}
    emit(details, output, title=f"Job: {result.get('job_id', job_id)}")
