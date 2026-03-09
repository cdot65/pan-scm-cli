"""Jobs management commands for scm-cli.

This module provides commands to list, check status, and wait for
SCM configuration jobs.
"""

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Manage SCM configuration jobs")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

JOB_ID_OPTION = typer.Option(..., "--id", help="Job ID to query")
TIMEOUT_OPTION = typer.Option(300, "--timeout", help="Timeout in seconds to wait for job completion")
MAX_RESULTS_OPTION = typer.Option(25, "--max-results", help="Maximum number of jobs to display")


# =============================================================================================================================================================================================
# JOBS COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------ list ------------------------------------------------------------------------------------


@app.command("list")
def list_jobs(
    max_results: int = MAX_RESULTS_OPTION,
):
    """List recent SCM configuration jobs.

    Examples
    --------
    scm jobs list
    scm jobs list --max-results 50

    """
    try:
        jobs = scm_client.list_jobs(max_results=max_results)

        if not jobs:
            typer.echo("No jobs found")
            return

        table = Table(title="SCM Jobs")
        table.add_column("Job ID", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Status", style="green")
        table.add_column("Description", style="dim")
        table.add_column("Start Time", style="white")
        table.add_column("End Time", style="white")

        for job in jobs[:max_results]:
            status = job.get("status_str", job.get("status", "unknown"))
            style = "green" if status == "FIN" else ("yellow" if status == "PEND" else "red")
            table.add_row(
                str(job.get("id", "")),
                str(job.get("type_str", job.get("type", ""))),
                f"[{style}]{status}[/{style}]",
                str(job.get("description", "")),
                str(job.get("start_ts", "")),
                str(job.get("end_ts", "")),
            )

        console.print(table)
        typer.echo(f"\nShowing {min(len(jobs), max_results)} of {len(jobs)} jobs")

    except Exception as e:
        typer.echo(f"Error listing jobs: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ------------------------------------------------------------------------------------ status ------------------------------------------------------------------------------------


@app.command("status")
def job_status(
    job_id: str = JOB_ID_OPTION,
):
    """Get the status of a specific job.

    Examples
    --------
    scm jobs status --id 12345

    """
    try:
        job = scm_client.get_job_status(job_id=job_id)

        typer.echo(f"\nJob Details for ID: {job.get('id', job_id)}")
        typer.echo("-" * 50)
        for key, value in job.items():
            if value is not None and value != [] and value != "":
                typer.echo(f"  {key}: {value}")

    except Exception as e:
        typer.echo(f"Error getting job status: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ------------------------------------------------------------------------------------- wait ------------------------------------------------------------------------------------


@app.command("wait")
def wait_for_job(
    job_id: str = JOB_ID_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Wait for a job to complete.

    Polls the job status until it completes or the timeout is reached.

    Examples
    --------
    scm jobs wait --id 12345
    scm jobs wait --id 12345 --timeout 600

    """
    try:
        typer.echo(f"Waiting for job {job_id} to complete (timeout: {timeout}s)...")
        result = scm_client.wait_for_job(job_id=job_id, timeout=timeout)

        status = result.get("status_str", result.get("status", "unknown"))
        result_str = result.get("result_str", result.get("result", ""))
        typer.echo(f"\nJob {job_id} completed with status: {status} (result: {result_str})")
        typer.echo("-" * 50)
        for key, value in result.items():
            if value is not None and value != [] and value != "":
                typer.echo(f"  {key}: {value}")

        # Exit with error if job did not complete successfully
        if result_str in ("FAIL", "PUSHABORT", "ABORTED"):
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except TimeoutError as e:
        typer.echo(f"Timeout waiting for job {job_id}: {e!s}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error waiting for job: {e!s}", err=True)
        raise typer.Exit(code=1) from e
