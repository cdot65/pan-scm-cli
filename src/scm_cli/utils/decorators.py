"""Shared decorators for scm-cli command modules."""

import functools
import traceback

import typer

_debug_enabled = False


def set_debug(enabled: bool) -> None:
    """Record whether --debug was passed (set once by the main callback)."""
    global _debug_enabled  # noqa: PLW0603
    _debug_enabled = enabled


def is_debug() -> bool:
    """Return True when --debug is active."""
    return _debug_enabled


def handle_command_errors(operation: str):
    """Wrap a command function with standardized error handling.

    Catches all exceptions (except typer.Exit and typer.Abort) and prints
    a formatted error message to stderr before exiting with code 1. With
    --debug active, the full traceback is printed first.

    Args:
    ----
        operation: Human-readable description of the operation, used in error
            messages (e.g., "deleting address", "listing zones").

    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (typer.Exit, typer.Abort, SystemExit):
                raise
            except Exception as e:
                if is_debug():
                    typer.echo(traceback.format_exc(), err=True)
                typer.echo(f"Error {operation}: {str(e)}", err=True)
                raise typer.Exit(code=1) from e

        return wrapper

    return decorator
