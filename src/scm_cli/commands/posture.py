"""Posture module commands for scm.

This module implements commands for PAN-OS firewall Best Practice Assessment (BPA),
including config export, BPA assessment upload, and report scoring.
"""

import json
import os
import time
from pathlib import Path

import typer

from ..utils.decorators import handle_command_errors
from ..utils.sdk_client import scm_client
from ..utils.validators import BpaAssessRequest, BpaStatusResponse, PostureExport

# ===============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ===============================================================================================================================================================================================

posture_app = typer.Typer(help="Firewall posture assessment and BPA scoring")

# ===============================================================================================================================================================================================
# COMMAND OPTIONS
# ===============================================================================================================================================================================================

HOST_OPTION = typer.Option(
    None,
    "--host",
    help="PAN-OS firewall hostname or IP address",
    envvar="PANOS_HOST",
)
USER_OPTION = typer.Option(
    "automation",
    "--user",
    help="Admin username for XML API authentication",
    envvar="PANOS_USER",
)
PASSWORD_OPTION = typer.Option(
    None,
    "--password",
    help="Admin password (or set PANOS_PASSWORD env var)",
    envvar="PANOS_PASSWORD",
)
OUTPUT_OPTION = typer.Option(
    "config.xml",
    "--output",
    help="Output file path",
)
CATEGORY_OPTION = typer.Option(
    "running",
    "--category",
    help="Config category to export (running or candidate)",
)
CONFIG_OPTION = typer.Option(
    ...,
    "--config",
    help="Path to config file to assess",
)
DELETE_AFTER_OPTION = typer.Option(
    True,
    "--delete-after/--keep",
    help="Delete config from cloud after assessment",
)
TIMEOUT_OPTION = typer.Option(
    300,
    "--timeout",
    help="Max seconds to wait for BPA processing",
)
REPORT_OPTION = typer.Option(
    ...,
    "--report",
    help="Path to BPA report JSON file",
)
SCOPE_OPTION = typer.Option(
    "all",
    "--scope",
    help="BPA check scope (all, security, decryption, threat)",
)
FORMAT_OPTION = typer.Option(
    "plain",
    "--format",
    help="Output format (plain or json)",
)

# ===============================================================================================================================================================================================
# EXPORT COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("export")
@handle_command_errors("exporting config")
def export_config(
    host: str = HOST_OPTION,
    user: str = USER_OPTION,
    password: str | None = PASSWORD_OPTION,
    output: str = OUTPUT_OPTION,
    category: str = CATEGORY_OPTION,
):
    r"""Export running or candidate config from a PAN-OS firewall.

    Example:
    -------
        scm posture export \
        --host 10.0.0.1 \
        --user automation \
        --output config.xml \
        --category running

    """
    if not password:
        password = os.environ.get("PANOS_PASSWORD")
    if not password:
        typer.echo("Error: password required via --password or PANOS_PASSWORD env var", err=True)
        raise typer.Exit(code=1)

    if not host:
        typer.echo("Error: --host is required or set PANOS_HOST env var", err=True)
        raise typer.Exit(code=1)

    # Validate inputs
    export_params = PostureExport(
        host=host,
        user=user,
        password=password,
        output=output,
        category=category,
    )

    # Generate API key
    api_key = scm_client.generate_panos_api_key(
        host=export_params.host,
        user=export_params.user,
        password=export_params.password,
    )
    typer.echo(f"Generated API key for {export_params.user}@{export_params.host}", err=True)

    # Export config
    config_xml = scm_client.export_panos_config(
        host=export_params.host,
        api_key=api_key,
        category=export_params.category,
    )

    # Write to file
    output_path = Path(export_params.output)
    output_path.write_text(config_xml)
    typer.echo(f"Exported {export_params.category} config to {output_path}")


# ===============================================================================================================================================================================================
# ASSESS COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("assess")
@handle_command_errors("assessing config")
def assess_config(
    config: str = CONFIG_OPTION,
    delete_after: bool = DELETE_AFTER_OPTION,
    output: str = typer.Option("report.json", "--output", help="Output file path for report"),
    timeout: int = TIMEOUT_OPTION,
):
    r"""Upload config to BPA API, poll for completion, and save report.

    Example:
    -------
        scm posture assess \
        --config config.xml \
        --delete-after \
        --output report.json \
        --timeout 300

    """
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: config file not found: {config_path}", err=True)
        raise typer.Exit(code=1)

    assess_params = BpaAssessRequest(
        config=config,
        delete_after_processing=delete_after,
        output=output,
        timeout=timeout,
    )

    # Step 1: Initiate upload
    typer.echo("Initiating BPA upload...", err=True)
    initiate_result = scm_client.initiate_bpa_upload(
        delete_after_processing=assess_params.delete_after_processing,
    )
    task_id = initiate_result["task_id"]
    upload_url = initiate_result["upload_url"]
    typer.echo(f"Task ID: {task_id}", err=True)

    # Step 2: Upload config to presigned URL
    typer.echo("Uploading config...", err=True)
    config_data = config_path.read_bytes()
    scm_client.upload_config_to_presigned_url(
        upload_url=upload_url,
        config_data=config_data,
    )
    typer.echo("Upload complete. Waiting for processing...", err=True)

    # Step 3: Poll for completion
    start_time = time.time()
    poll_interval = 5

    while True:
        elapsed = time.time() - start_time
        if elapsed >= assess_params.timeout:
            typer.echo(f"Error: BPA processing timed out after {assess_params.timeout}s", err=True)
            raise typer.Exit(code=1)

        status_result = scm_client.get_bpa_status(task_id=task_id)
        status = BpaStatusResponse(**status_result)

        if status.status == "COMPLETED":
            break
        elif status.status == "FAILED":
            msg = status.message or "unknown error"
            typer.echo(f"Error: BPA processing failed: {msg}", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"  Status: {status.status} ({status.message or 'processing...'})", err=True)
        time.sleep(poll_interval)

    # Step 4: Fetch report
    report_url = status.result["report_url"]
    typer.echo("Fetching report...", err=True)
    report = scm_client.fetch_bpa_report(report_url=report_url)

    output_path = Path(assess_params.output)
    output_path.write_text(json.dumps(report, indent=2))
    typer.echo(f"BPA report saved to {output_path}")


# ===============================================================================================================================================================================================
# SCORE COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("score")
@handle_command_errors("scoring report")
def score_report(
    report: str = REPORT_OPTION,
    scope: str = SCOPE_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Parse BPA report JSON and return a numeric score.

    The score is the percentage of checks that passed. Use --scope to filter
    by category and --format to control output.

    Note: The report JSON schema is discovered at runtime from the first real
    BPA run. The scoring logic assumes checks have 'name', 'status', and
    'category' fields. Adjust after inspecting a real report.

    Example:
    -------
        scm posture score \
        --report report.json \
        --scope security \
        --format plain

    """
    report_path = Path(report)
    if not report_path.exists():
        typer.echo(f"Error: report file not found: {report_path}", err=True)
        raise typer.Exit(code=1)

    report_data = json.loads(report_path.read_text())

    checks = report_data.get("checks", [])

    if scope != "all":
        checks = [c for c in checks if c.get("category") == scope]

    if not checks:
        typer.echo("Error: no checks found for the given scope", err=True)
        raise typer.Exit(code=1)

    total = len(checks)
    passed = sum(1 for c in checks if c.get("status") == "PASS")
    failed = total - passed
    score = round((passed / total) * 100, 1)

    if format == "json":
        output = json.dumps({"score": score, "passed": passed, "failed": failed, "total": total})
        typer.echo(output)
    else:
        typer.echo(str(score))
