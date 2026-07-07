"""Main entry point for the scm-cli tool.

This module initializes the Typer CLI application and registers subcommands for the
various SCM configuration actions (set, delete, show, load, backup, move) and the
standalone top-level commands.

Command modules are loaded lazily: help listings render from static metadata, and a
module is only imported when one of its commands is actually dispatched. This keeps
`scm --help` / `scm --version` free of the SDK/validator import cost.
"""

import click
import typer
from typer.core import TyperGroup

# =============================================================================================================================================================================================
# LAZY COMMAND LOADING
# =============================================================================================================================================================================================

# Lazy specs map a subcommand name to (module attribute path, help text). Module
# paths are relative to this package so the module resolves correctly whether the
# package is imported as `scm_cli` or `src.scm_cli` (tests use both).
_PACKAGE = __package__


def _lazy_group(lazy_map: dict[str, tuple[str, str]]) -> type[TyperGroup]:
    """Build a TyperGroup subclass whose subcommands load on dispatch.

    Help listings use the static help text from the spec (no imports); actual
    dispatch (including `<subcommand> --help`) imports the target module.
    """

    class LazyGroup(TyperGroup):
        _lazy = lazy_map

        def list_commands(self, ctx: click.Context) -> list[str]:
            return sorted(set(super().list_commands(ctx)) | set(self._lazy))

        def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
            # Used by help rendering and completion: return a lightweight stub
            # carrying the static help so nothing gets imported.
            if name in self._lazy:
                _, help_text = self._lazy[name]
                return click.Command(name=name, help=help_text, short_help=help_text)
            return super().get_command(ctx, name)

        def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[str | None, click.Command | None, list[str]]:
            # Used only for actual dispatch: import the real subcommand.
            name = args[0] if args else ""
            if name in self._lazy:
                return name, self._load(name), args[1:]
            return super().resolve_command(ctx, args)

        def _load(self, name: str) -> click.Command:
            import importlib

            attr_path, help_text = self._lazy[name]
            module_name, attr = attr_path.split(":")
            module = importlib.import_module(f"{_PACKAGE}.commands.{module_name}")
            command = typer.main.get_command(getattr(module, attr))
            command.name = name
            if help_text and not command.help:
                command.help = help_text
            return command

    return LazyGroup


def _action_spec(action: str, verb: str) -> dict[str, tuple[str, str]]:
    """Lazy spec for one action group: category -> module app."""
    return {
        "identity": (f"identity:{action}_app", f"{verb} identity configurations"),
        "mobile-agent": (f"mobile_agent:{action}_app", f"{verb} mobile agent configurations"),
        "network": (f"network:{action}_app", f"{verb} network configurations"),
        "object": (f"objects:{action}_app", f"{verb} object configurations"),
        "sase": (f"deployment:{action}_app", f"{verb} SASE configurations"),
        "security": (f"security:{action}_app", f"{verb} security configurations"),
        "setup": (f"setup:{action}_app", f"{verb} setup configurations"),
    }


_TOP_LEVEL_SPEC: dict[str, tuple[str, str]] = {
    "commit": ("commit:app", "Commit staged configuration changes"),
    "context": ("context:app", "Manage authentication contexts"),
    "incidents": ("incidents:app", "Search and view security incidents"),
    "insights": ("insights:app", "Query monitoring insights"),
    "jobs": ("jobs:app", "Manage SCM jobs"),
    "local": ("local:app", "Retrieve local device configurations"),
    "operations": ("operations:app", "Run device operations"),
    "posture": ("posture:posture_app", "Firewall posture / BPA assessment"),
}

# =============================================================================================================================================================================================
# MAIN CLI APPLICATION
# =============================================================================================================================================================================================

app = typer.Typer(
    name="scm",
    help="CLI for Palo Alto Networks Strata Cloud Manager",
    cls=_lazy_group(_TOP_LEVEL_SPEC),
)

# =============================================================================================================================================================================================
# ACTION APP GROUPS (categories load lazily per action)
# =============================================================================================================================================================================================

backup_app = typer.Typer(help="Backup configurations to YAML files", cls=_lazy_group(_action_spec("backup", "Backup")))
delete_app = typer.Typer(help="Remove configurations", cls=_lazy_group(_action_spec("delete", "Delete")))
load_app = typer.Typer(help="Load configurations from YAML files", cls=_lazy_group(_action_spec("load", "Load")))
move_app = typer.Typer(help="Move rules to a new position", cls=_lazy_group({"security": ("security:move_app", "Move security rules")}))
set_app = typer.Typer(help="Create or update configurations", cls=_lazy_group(_action_spec("set", "Set")))
show_app = typer.Typer(help="Display configurations", cls=_lazy_group(_action_spec("show", "Show")))

app.add_typer(backup_app, name="backup")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")
app.add_typer(move_app, name="move")
app.add_typer(set_app, name="set")
app.add_typer(show_app, name="show")

# =============================================================================================================================================================================================
# GLOBAL OPTIONS
# =============================================================================================================================================================================================

_region_override: str | None = None

_VALID_LOG_LEVELS = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")


def get_region_override() -> str | None:
    """Get the global --region override value, if set."""
    return _region_override


def _configure_logging(debug: bool) -> None:
    """Configure logging once at CLI entry.

    Precedence: --debug > SCM_LOG_LEVEL env > `log_level` setting > WARNING.
    The SDK auth loggers stay pinned to CRITICAL unless the effective level
    is DEBUG, so OAuth/token traffic is only visible when debugging.
    """
    import logging
    import os

    if debug:
        level = logging.DEBUG
    else:
        from .utils.config import settings
        from .utils.output import warning

        level_name = (os.environ.get("SCM_LOG_LEVEL") or settings.get("log_level", "WARNING") or "WARNING").upper()
        if level_name not in _VALID_LOG_LEVELS:
            warning(f"Invalid SCM_LOG_LEVEL '{level_name}' (valid: {', '.join(_VALID_LOG_LEVELS)}); using WARNING")
            level_name = "WARNING"
        level = getattr(logging, level_name)

    logging.basicConfig(level=level, force=True)

    auth_logger_level = logging.NOTSET if level == logging.DEBUG else logging.CRITICAL
    logging.getLogger("scm.auth").setLevel(auth_logger_level)
    logging.getLogger("oauthlib").setLevel(auth_logger_level)


def _version_callback(value: bool) -> None:
    if value:
        from importlib.metadata import version

        typer.echo(version("pan-scm-cli"))
        raise typer.Exit()


@app.callback()
def callback(
    region: str | None = typer.Option(
        None,
        "--region",
        help="Override SCM API region for this invocation",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging (including SDK auth/HTTP) and full tracebacks",
    ),
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        help="Show the CLI version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
):
    """Manage Palo Alto Networks Strata Cloud Manager (SCM) configurations.

    The CLI follows the pattern: <action> <object-type> <object> [options]

    Examples
    --------
      - scm set object address-group --folder Texas --name test123 --type static
      - scm delete security security-rule --folder Texas --name test123
      - scm load network zone --file config/security_zones.yml
      - scm show object address --folder Texas --list
      - scm show object address --folder Texas --name webserver
      - scm context test

    """
    global _region_override  # noqa: PLW0603
    _region_override = region

    from .utils.decorators import set_debug

    set_debug(debug)
    _configure_logging(debug)


# =============================================================================================================================================================================================
# MAIN ENTRY POINT
# =============================================================================================================================================================================================


if __name__ == "__main__":
    app()
