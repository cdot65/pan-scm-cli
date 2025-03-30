"""Tests for the main CLI application."""

from scm_cli.main import app


def test_app_exists():
    """Test that the application exists."""
    assert app is not None


def test_app_help(runner):
    """Test the help output of the application."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "set" in result.stdout
    assert "delete" in result.stdout
    assert "load" in result.stdout


def test_set_command_help(runner):
    """Test the help output of the set command."""
    result = runner.invoke(app, ["set", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "deployment" in result.stdout
    assert "network" in result.stdout
    assert "objects" in result.stdout
    assert "security" in result.stdout


def test_delete_command_help(runner):
    """Test the help output of the delete command."""
    result = runner.invoke(app, ["delete", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "deployment" in result.stdout
    assert "network" in result.stdout
    assert "objects" in result.stdout
    assert "security" in result.stdout


def test_load_command_help(runner):
    """Test the help output of the load command."""
    result = runner.invoke(app, ["load", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "deployment" in result.stdout
    assert "network" in result.stdout
    assert "objects" in result.stdout
    assert "security" in result.stdout
