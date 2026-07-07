"""Jobs management commands for scm-cli.

This module provides commands to list, check status, and wait for
SCM configuration jobs.
"""

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Manage SCM configuration jobs")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

JOB_ID_OPTION = typer.Option(..., "--id", help="Job ID to query")
TIMEOUT_OPTION = typer.Option(300, "--timeout", help="Timeout in seconds to wait for job completion")
MAX_RESULTS_OPTION = typer.Option(25, "--max-results", help="Maximum number of jobs to display")


# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def _job_details(job: dict) -> dict:
    """Drop empty fields from a job record for display."""
    return {key: value for key, value in job.items() if value is not None and value != [] and value != ""}


# =============================================================================================================================================================================================
# JOBS COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------ list ------------------------------------------------------------------------------------


@app.command("list")
@handle_command_errors("listing jobs")
def list_jobs(
    max_results: int = MAX_RESULTS_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """List recent SCM configuration jobs.

    Examples
    --------
    scm jobs list
    scm jobs list --max-results 50

    """
    jobs = scm_client.list_jobs(max_results=max_results)

    rows = [
        {
            "id": job.get("id", ""),
            "type": job.get("type_str", job.get("type", "")),
            "status": job.get("status_str", job.get("status", "unknown")),
            "description": job.get("description", ""),
            "start_time": job.get("start_ts", ""),
            "end_time": job.get("end_ts", ""),
        }
        for job in jobs[:max_results]
    ]
    emit(rows, output, title="SCM Jobs")

    if jobs:
        info(f"Showing {min(len(jobs), max_results)} of {len(jobs)} jobs")


# ------------------------------------------------------------------------------------ status ------------------------------------------------------------------------------------


@app.command("status")
@handle_command_errors("getting job status")
def job_status(
    job_id: str = JOB_ID_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """Get the status of a specific job.

    Examples
    --------
    scm jobs status --id 12345

    """
    job = scm_client.get_job_status(job_id=job_id)

    emit(_job_details(job), output, title=f"Job: {job.get('id', job_id)}")


# ------------------------------------------------------------------------------------- wait ------------------------------------------------------------------------------------


@app.command("wait")
@handle_command_errors("waiting for job")
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
    info(f"Waiting for job {job_id} to complete (timeout: {timeout}s)...")
    try:
        result = scm_client.wait_for_job(job_id=job_id, timeout=timeout)
    except TimeoutError as e:
        error(f"Timeout waiting for job {job_id}: {e!s}")
        raise typer.Exit(code=1) from e

    status = result.get("status_str", result.get("status", "unknown"))
    result_str = result.get("result_str", result.get("result", ""))
    success(f"Job {job_id} completed with status: {status} (result: {result_str})")
    emit(_job_details(result), OutputFormat.table, title=f"Job: {job_id}")

    # Exit with error if job did not complete successfully
    if result_str in ("FAIL", "PUSHABORT", "ABORTED"):
        raise typer.Exit(code=1)
