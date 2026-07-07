"""Commit command for scm-cli.

This module provides the commit command to push configuration changes
to Strata Cloud Manager.
"""

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import info, success
from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Commit configuration changes to SCM")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

FOLDER_OPTION = typer.Option(..., "--folder", help="Folder(s) to commit (can specify multiple)")
DESCRIPTION_OPTION = typer.Option(..., "--description", help="Description of the commit")
SYNC_OPTION = typer.Option(False, "--sync", help="Wait synchronously for the commit to complete")
TIMEOUT_OPTION = typer.Option(300, "--timeout", help="Timeout in seconds when using --sync")


# =============================================================================================================================================================================================
# COMMIT COMMAND
# =============================================================================================================================================================================================


ADMIN_OPTION = typer.Option(None, "--admin", help="Admin user for commit (required for bearer token auth)")


@app.callback(invoke_without_command=True)
@handle_command_errors("committing configuration")
def commit(
    folders: list[str] = FOLDER_OPTION,
    description: str = DESCRIPTION_OPTION,
    sync: bool = SYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
    admin: str | None = ADMIN_OPTION,
):
    """Commit configuration changes to SCM.

    Pushes pending configuration changes for the specified folder(s).
    Use --sync to wait for the commit to complete.
    Use --admin when authenticating with a bearer token.

    Examples
    --------
    scm commit --folder Texas --description "Update address objects"
    scm commit --folder Texas --folder California --description "Multi-folder update"
    scm commit --folder Texas --description "Deploy changes" --sync
    scm commit --folder Texas --description "Deploy changes" --sync --timeout 600
    scm commit --folder Texas --description "Deploy changes" --admin user@domain.com

    """
    info(f"Committing changes for folder(s): {', '.join(folders)}")
    info(f"Description: {description}")

    if sync:
        info(f"Waiting for commit to complete (timeout: {timeout}s)...")

    # Build commit kwargs
    commit_kwargs = {
        "folders": folders,
        "description": description,
        "sync": sync,
        "timeout": timeout,
    }

    # Pass admin parameter if specified (needed for bearer token auth)
    if admin:
        commit_kwargs["admin"] = admin

    result = scm_client.commit_config(**commit_kwargs)

    job_id = result.get("job_id", "unknown")
    if result.get("success"):
        success("Commit successful!")
        success(f"Job ID: {job_id}")

        if sync:
            status = result.get("result_str", result.get("status_str", result.get("status", "unknown")))
            info(f"Status: {status}")
            if result.get("details"):
                info(f"Details: {result.get('details')}")
    else:
        success("Commit initiated")
        success(f"Job ID: {job_id}")
        if not sync:
            info(f"Use 'scm jobs status --id {job_id}' to check progress")
            info(f"Or  'scm jobs wait --id {job_id}' to wait for completion")
