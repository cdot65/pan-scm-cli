"""Tests for shared command decorators."""

import typer
from typer.testing import CliRunner

from scm_cli.utils.decorators import handle_command_errors

runner = CliRunner()


def test_success_passthrough():
    """Decorator passes through return value on success."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("testing")
    def cmd():
        typer.echo("ok")

    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_exception_caught_and_formatted():
    """Decorator catches exceptions and prints formatted error to stderr."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("creating widget")
    def cmd():
        raise RuntimeError("connection refused")

    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "Error creating widget: connection refused" in result.output


def test_typer_exit_passthrough():
    """Decorator does not catch typer.Exit."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("testing")
    def cmd():
        raise typer.Exit(code=42)

    result = runner.invoke(app, [])
    assert result.exit_code == 42


def test_typer_abort_passthrough():
    """Decorator does not catch typer.Abort."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("testing")
    def cmd():
        raise typer.Abort()

    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_preserves_function_name():
    """Decorator preserves the wrapped function's name."""

    @handle_command_errors("testing")
    def my_fancy_command():
        pass

    assert my_fancy_command.__name__ == "my_fancy_command"


def test_with_arguments():
    """Decorator works with commands that have arguments."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("greeting")
    def cmd(name: str = typer.Argument(...)):
        typer.echo(f"hello {name}")

    result = runner.invoke(app, ["world"])
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_with_options():
    """Decorator works with commands that have options."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("greeting")
    def cmd(name: str = typer.Option("default", "--name")):
        typer.echo(f"hello {name}")

    result = runner.invoke(app, ["--name", "test"])
    assert result.exit_code == 0
    assert "hello test" in result.output


def _make_raising_app(exc_class):
    """Helper to create a Typer app that raises a specific exception."""
    app = typer.Typer()

    @app.command()
    @handle_command_errors("processing")
    def cmd():
        raise exc_class("specific error")

    return app


def test_various_exception_types():
    """Decorator handles different exception types consistently."""
    for exc_class in [ValueError, TypeError, KeyError, IOError]:
        app = _make_raising_app(exc_class)
        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "Error processing" in result.output
