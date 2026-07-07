"""Shared output layer for scm-cli.

Every command renders user-facing output through this module so the CLI
has one consistent voice:

- **Data** (tables, detail views, JSON, YAML) goes to **stdout**.
- **Messages** (success, error, warning, info) go to **stderr**.

This separation keeps stdout pipe-safe: `scm show ... --output json | jq`
receives pure data regardless of any human-oriented messaging.
"""

import json
from enum import Enum
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

# Data console (stdout) and message console (stderr).
console = Console()
err_console = Console(stderr=True)


class OutputFormat(str, Enum):
    """Supported output formats for show/list commands."""

    table = "table"
    json = "json"
    yaml = "yaml"


OUTPUT_OPTION = typer.Option(
    OutputFormat.table,
    "--output",
    "-o",
    help="Output format: table (human), json, or yaml (machine-readable)",
)


# ----------------------------------------------------------------------------- messages (stderr)


def success(message: str) -> None:
    """Print a success message to stderr."""
    err_console.print(f"[green]✓[/green] {message}")


def error(message: str) -> None:
    """Print an error message to stderr."""
    err_console.print(f"[red]✗[/red] {message}")


def warning(message: str) -> None:
    """Print a warning message to stderr."""
    err_console.print(f"[yellow]⚠[/yellow] {message}")


def info(message: str) -> None:
    """Print an informational message to stderr."""
    err_console.print(f"[dim]{message}[/dim]")


# ----------------------------------------------------------------------------- data (stdout)


def _humanize(key: str) -> str:
    """Convert a snake_case field name into a title-cased column label."""
    return key.replace("_", " ").title()


def _cell(value: Any) -> str:
    """Render a single table/detail value compactly."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(_cell(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, default=str)
    return str(value)


def render_table(rows: list[dict[str, Any]], columns: list[str] | None = None, title: str | None = None) -> None:
    """Render a list of dicts as a rich table on stdout.

    Args:
    ----
        rows: List of records to display.
        columns: Keys to display in order; defaults to the union of keys in
            row order of first appearance.
        title: Optional table title.

    """
    if not rows:
        info("No results found." if title is None else f"No results found for {title}.")
        return

    if columns is None:
        columns = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)

    table = Table(title=title, show_lines=False, header_style="bold")
    for column in columns:
        table.add_column(_humanize(column))
    for row in rows:
        table.add_row(*(_cell(row.get(column)) for column in columns))

    console.print(table)


def render_detail(obj: dict[str, Any], title: str | None = None) -> None:
    """Render a single record as a field-per-line detail view on stdout."""
    table = Table(title=title, show_header=False, box=None, pad_edge=False)
    table.add_column(style="bold")
    table.add_column()
    for key, value in obj.items():
        table.add_row(_humanize(key), _cell(value))
    console.print(table)


def emit(
    data: Any,
    output_format: OutputFormat | str = OutputFormat.table,
    columns: list[str] | None = None,
    title: str | None = None,
) -> None:
    """Emit data on stdout in the requested format.

    Table format renders lists as tables and dicts as detail views; json and
    yaml print pure machine-readable documents (no styling, no messages).
    """
    output_format = OutputFormat(output_format)

    # Machine formats bypass rich entirely: rich wraps long lines to the
    # terminal width, which can corrupt JSON/YAML strings.
    if output_format is OutputFormat.json:
        print(json.dumps(data, indent=2, default=str))
    elif output_format is OutputFormat.yaml:
        print(yaml.safe_dump(json.loads(json.dumps(data, default=str)), sort_keys=False), end="")
    elif isinstance(data, dict):
        render_detail(data, title=title)
    else:
        render_table(list(data), columns=columns, title=title)
