"""Posture module commands for scm.

This module implements commands for PAN-OS firewall Best Practice Assessment (BPA),
including config export, BPA assessment upload, and report scoring.
"""

import csv
import io
import json
import os
import time
from pathlib import Path

import typer

from ..utils.decorators import handle_command_errors
from ..utils.output import error, info, success, warning
from ..utils.sdk_client import scm_client
from ..utils.validators import BpaAssessRequest, BpaStatusResponse, PostureExport

# =============================================================================================================================================================================================
# PARSER FUNCTIONS
# =============================================================================================================================================================================================


def flatten_bpa_checks(
    report: dict,
    scope: str = "all",
) -> list[dict]:
    """Flatten nested BPA report into a list of checks with category metadata.

    Args:
        report: Raw BPA report dict.
        scope: Category filter — 'all' or a specific category name.

    Returns:
        list[dict]: Flattened checks with category and subcategory attached.

    """
    checks = []
    best_practices = report.get("best_practices", {})

    for category, subcategories in best_practices.items():
        if scope != "all" and category != scope:
            continue
        for subcategory, items in subcategories.items():
            for item in items:
                for warn in item.get("warnings", []):
                    check = {
                        "category": category,
                        "subcategory": subcategory,
                        "check_id": warn.get("check_id"),
                        "check_name": warn.get("check_name"),
                        "check_type": warn.get("check_type"),
                        "check_message": warn.get("check_message"),
                        "check_passed": warn.get("check_passed"),
                        "remediation": warn.get("remediation"),
                    }
                    checks.append(check)

    return checks


def format_bpa_output(checks: list[dict], fmt: str = "json") -> str:
    """Format flattened BPA checks into the requested output format.

    Args:
        checks: Flattened list of BPA checks from flatten_bpa_checks.
        fmt: Output format — 'json', 'markdown', or 'csv'.

    Returns:
        str: Formatted output string.

    """
    total = len(checks)
    passed = sum(1 for c in checks if c.get("check_passed"))
    failed = total - passed
    score = round((passed / total) * 100, 1) if total > 0 else 0.0

    # Build by_type breakdown
    by_type: dict[str, dict[str, int]] = {}
    for c in checks:
        ct = c.get("check_type", "Unknown")
        if ct not in by_type:
            by_type[ct] = {"total": 0, "passed": 0, "failed": 0}
        by_type[ct]["total"] += 1
        if c.get("check_passed"):
            by_type[ct]["passed"] += 1
        else:
            by_type[ct]["failed"] += 1

    if fmt == "json":
        data = {
            "score": score,
            "total": total,
            "passed": passed,
            "failed": failed,
            "by_type": by_type,
            "checks": checks,
        }
        return json.dumps(data, indent=2)

    if fmt == "markdown":
        lines = [
            f"## BPA Score: {score}% ({passed}/{total})",
            "",
            "### Summary by Severity",
            "| Severity | Passed | Failed | Total |",
            "|---|---|---|---|",
        ]
        for severity in ["Critical", "Warning", "Informational"]:
            if severity in by_type:
                s = by_type[severity]
                lines.append(f"| {severity} | {s['passed']} | {s['failed']} | {s['total']} |")

        failing = [c for c in checks if not c.get("check_passed")]
        passing = [c for c in checks if c.get("check_passed")]

        lines.append("")
        lines.append(f"### Failing Checks ({len(failing)})")
        lines.append("| ID | Name | Severity | Category | Message |")
        lines.append("|---|---|---|---|---|")
        for c in failing:
            msg = c.get("check_message") or ""
            lines.append(f"| {c['check_id']} | {c['check_name']} | {c['check_type']} | {c['category']} | {msg} |")

        lines.append("")
        lines.append(f"### Passing Checks ({len(passing)})")
        lines.append("| ID | Name | Severity | Category |")
        lines.append("|---|---|---|---|")
        for c in passing:
            lines.append(f"| {c['check_id']} | {c['check_name']} | {c['check_type']} | {c['category']} |")

        return "\n".join(lines)

    if fmt == "csv":
        output = io.StringIO()
        fieldnames = [
            "check_id",
            "check_name",
            "check_type",
            "check_passed",
            "category",
            "subcategory",
            "check_message",
            "remediation",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for c in checks:
            writer.writerow(c)
        return output.getvalue()

    raise ValueError(f"Unknown format: {fmt}")


# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

posture_app = typer.Typer(help="Firewall posture assessment and BPA scoring")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

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
    help="BPA check scope (all, device, service_health, network, policies, objects)",
)
FORMAT_OPTION = typer.Option(
    "json",
    "--format",
    help="Output format (json, markdown, csv)",
)

# =============================================================================================================================================================================================
# EXPORT COMMAND
# =============================================================================================================================================================================================


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
        error("Error: password required via --password or PANOS_PASSWORD env var")
        raise typer.Exit(code=1)

    if not host:
        error("Error: --host is required or set PANOS_HOST env var")
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
    info(f"Generated API key for {export_params.user}@{export_params.host}")

    # Export config
    config_xml = scm_client.export_panos_config(
        host=export_params.host,
        api_key=api_key,
        category=export_params.category,
    )

    # Write to file
    output_path = Path(export_params.output)
    output_path.write_text(config_xml)
    success(f"Exported {export_params.category} config to {output_path}")


# =============================================================================================================================================================================================
# ASSESS COMMAND
# =============================================================================================================================================================================================


@posture_app.command("assess")
@handle_command_errors("assessing config")
def assess_config(
    config: str = CONFIG_OPTION,
    delete_after: bool = DELETE_AFTER_OPTION,
    output: str = typer.Option("report.json", "--output", help="Output file path for report"),
    timeout: int = TIMEOUT_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Upload config to BPA API, poll for completion, and output scored results.

    Saves the raw BPA report to --output and prints formatted results to stdout.
    Progress messages go to stderr so stdout can be piped cleanly.

    Example:
    -------
        scm posture assess \
        --config config.xml \
        --delete-after \
        --output report.json \
        --format json \
        --timeout 300

    """
    config_path = Path(config)
    if not config_path.exists():
        error(f"Error: config file not found: {config_path}")
        raise typer.Exit(code=1)

    assess_params = BpaAssessRequest(
        config=config,
        delete_after_processing=delete_after,
        output=output,
        timeout=timeout,
    )

    # Step 1: Initiate upload
    info("Initiating BPA upload...")
    initiate_result = scm_client.initiate_bpa_upload(
        delete_after_processing=assess_params.delete_after_processing,
    )
    task_id = initiate_result["task_id"]
    upload_url = initiate_result["upload_url"]
    info(f"Task ID: {task_id}")

    # Step 2: Upload config to presigned URL
    info("Uploading config...")
    config_data = config_path.read_bytes()
    scm_client.upload_config_to_presigned_url(
        upload_url=upload_url,
        config_data=config_data,
    )
    info("Upload complete. Waiting for processing...")

    # Step 3: Poll for completion
    start_time = time.time()
    poll_interval = 5

    while True:
        elapsed = time.time() - start_time
        if elapsed >= assess_params.timeout:
            error(f"Error: BPA processing timed out after {assess_params.timeout}s")
            raise typer.Exit(code=1)

        status_result = scm_client.get_bpa_status(task_id=task_id)
        status = BpaStatusResponse(**status_result)

        if status.status == "COMPLETED":
            break
        elif status.status == "FAILED":
            msg = status.message or "unknown error"
            error(f"Error: BPA processing failed: {msg}")
            raise typer.Exit(code=1)

        info(f"  Status: {status.status} ({status.message or 'processing...'})")
        time.sleep(poll_interval)

    # Step 4: Fetch report
    report_url = status.result["report_url"]  # type: ignore[index]
    info("Fetching report...")
    report = scm_client.fetch_bpa_report(report_url=report_url)

    # Save raw report
    output_path = Path(assess_params.output)
    output_path.write_text(json.dumps(report, indent=2))
    info(f"BPA report saved to {output_path}")

    # Output formatted results to stdout
    checks = flatten_bpa_checks(report)
    if checks:
        typer.echo(format_bpa_output(checks, fmt=format))
    else:
        warning("Warning: no checks found in report")


# =============================================================================================================================================================================================
# SCORE COMMAND
# =============================================================================================================================================================================================


@posture_app.command("score")
@handle_command_errors("scoring report")
def score_report(
    report: str = REPORT_OPTION,
    scope: str = SCOPE_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Parse BPA report JSON and output scored results.

    Reads the nested best_practices structure, flattens all checks, and
    outputs scored results in the requested format. Use --scope to filter
    by category and --format to control output.

    Example:
    -------
        scm posture score \
        --report report.json \
        --scope device \
        --format json

    """
    report_path = Path(report)
    if not report_path.exists():
        error(f"Error: report file not found: {report_path}")
        raise typer.Exit(code=1)

    report_data = json.loads(report_path.read_text())
    checks = flatten_bpa_checks(report_data, scope=scope)

    if not checks:
        error("Error: no checks found for the given scope")
        raise typer.Exit(code=1)

    typer.echo(format_bpa_output(checks, fmt=format))
