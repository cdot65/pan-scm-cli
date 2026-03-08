"""Commit command for scm-cli.

This module provides the commit command to push configuration changes
to Strata Cloud Manager.
"""

import typer

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
    try:
        typer.echo(f"Committing changes for folder(s): {', '.join(folders)}")
        typer.echo(f"Description: {description}")

        if sync:
            typer.echo(f"Waiting for commit to complete (timeout: {timeout}s)...")

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

        if result.get("success"):
            typer.echo("\nCommit successful!")
            job_id = result.get("job_id", "unknown")
            typer.echo(f"Job ID: {job_id}")

            if sync:
                status = result.get("status", "unknown")
                typer.echo(f"Status: {status}")
        else:
            typer.echo("\nCommit initiated")
            job_id = result.get("job_id", "unknown")
            typer.echo(f"Job ID: {job_id}")
            if not sync:
                typer.echo(f"\nUse 'scm jobs status --id {job_id}' to check progress")
                typer.echo(f"Or  'scm jobs wait --id {job_id}' to wait for completion")

    except Exception as e:
        typer.echo(f"Error committing configuration: {e!s}", err=True)
        raise typer.Exit(code=1) from e
