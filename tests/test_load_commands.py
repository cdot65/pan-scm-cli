"""Tests for the load commands of scm-cli.

This module tests the load commands for bulk operations across resource types.
"""

import pytest
import typer

from scm_cli.commands.network import load_security_zone
from scm_cli.commands.security import load_security_rule


def test_load_zone_command(runner, monkeypatch, mock_zones_yaml_file):
    """Test loading zones from a YAML file via the load command."""
    from scm_cli.utils.sdk_client import scm_client

    created = []

    def mock_create(*args, **kwargs):
        result = {
            "id": f"zone-{len(created) + 1}",
            "name": kwargs.get("name"),
            "folder": kwargs.get("folder"),
            "mode": kwargs.get("mode"),
            "interfaces": kwargs.get("interfaces", []),
        }
        created.append(result)
        return result

    monkeypatch.setattr(scm_client, "create_zone", mock_create)

    test_app = typer.Typer()
    test_app.command()(load_security_zone)

    result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file)])

    assert result.exit_code == 0
    assert "Applied zone" in result.stdout
    assert len(created) == 1


def test_load_security_rule_command(runner, monkeypatch, mock_security_rules_yaml_file):
    """Test loading security rules from a YAML file via the load command."""
    from scm_cli.utils.sdk_client import scm_client

    created = []

    def mock_create(*args, **kwargs):
        result = {
            "id": f"sr-{len(created) + 1}",
            "name": kwargs.get("name"),
            "folder": kwargs.get("folder"),
        }
        created.append(result)
        return result

    monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

    test_app = typer.Typer()
    test_app.command()(load_security_rule)

    result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file)])

    assert result.exit_code == 0
    assert "Successfully processed" in result.stdout
    assert len(created) == 1


def test_load_zone_with_nonexistent_file(runner):
    """Test the load zone command with a file that doesn't exist."""
    test_app = typer.Typer()
    test_app.command()(load_security_zone)

    result = runner.invoke(test_app, ["--file", "/path/to/nonexistent/file.yaml"])

    assert result.exit_code != 0


def test_load_zone_dry_run(runner, monkeypatch, mock_zones_yaml_file):
    """Test loading zones with dry-run mode."""
    from scm_cli.utils.sdk_client import scm_client

    mock_called = False

    def mock_create(*args, **kwargs):
        nonlocal mock_called
        mock_called = True
        return {}

    monkeypatch.setattr(scm_client, "create_zone", mock_create)

    test_app = typer.Typer()
    test_app.command()(load_security_zone)

    result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file), "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run mode" in result.stdout
    assert not mock_called


def test_load_security_rule_dry_run(runner, monkeypatch, mock_security_rules_yaml_file):
    """Test loading security rules with dry-run mode."""
    from scm_cli.utils.sdk_client import scm_client

    mock_called = False

    def mock_create(*args, **kwargs):
        nonlocal mock_called
        mock_called = True
        return {}

    monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

    test_app = typer.Typer()
    test_app.command()(load_security_rule)

    result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file), "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run mode" in result.stdout
    assert not mock_called
