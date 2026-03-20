"""Shared decorators for scm-cli command modules."""

import functools

import typer


def handle_command_errors(operation: str):
    """Wrap a command function with standardized error handling.

    Catches all exceptions (except typer.Exit and typer.Abort) and prints
    a formatted error message to stderr before exiting with code 1.

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
                typer.echo(f"Error {operation}: {str(e)}", err=True)
                raise typer.Exit(code=1) from e

        return wrapper

    return decorator
