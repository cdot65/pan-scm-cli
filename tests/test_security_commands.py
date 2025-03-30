"""Tests for the security commands module."""

import typer
from scm_cli.commands.security import (
    delete_app,
    delete_security_rule,
    load_app,
    load_security_rule,
    set_app,
    set_security_rule,
)


class TestSecurityCommands:
    """Test the security commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


class TestSecurityRuleCommands:
    """Test the security rule commands."""

    def test_set_security_rule_command(self, runner, monkeypatch):
        """Test the set security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "sr-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "source_zones": kwargs.get("source_zones", []),
                "destination_zones": kwargs.get("destination_zones", []),
                "source_addresses": kwargs.get("source_addresses", ["any"]),
                "destination_addresses": kwargs.get("destination_addresses", ["any"]),
                "applications": kwargs.get("applications", ["any"]),
                "action": kwargs.get("action", "allow"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
                "enabled": kwargs.get("enabled", True),
            }

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
                "--source-zones",
                "trust",
                "--destination-zones",
                "untrust",
                "--source-addresses",
                "192.168.1.0/24",
                "--destination-addresses",
                "any",
                "--applications",
                "web-browsing",
                "--applications",
                "ssl",
                "--action",
                "allow",
                "--description",
                "Test security rule",
                "--tags",
                "test",
                "--tags",
                "example",
                "--enabled",
            ],
        )

        assert result.exit_code == 0
        assert "Created security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout

    def test_set_security_rule_error(self, runner, monkeypatch):
        """Test the set security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
                "--source-zones",
                "trust",
                "--destination-zones",
                "untrust",
                "--action",
                "allow",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating security rule" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_security_rule_command(self, runner, monkeypatch):
        """Test the delete security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_security_rule_error(self, runner, monkeypatch):
        """Test the delete security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting security rule" in result.stdout
        assert "Test error" in result.stdout

    def test_load_security_rule_command(self, runner, monkeypatch, mock_security_rules_yaml_file):
        """Test the load security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_rules = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"sr-{len(created_rules) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "source_zones": kwargs.get("source_zones", []),
                "destination_zones": kwargs.get("destination_zones", []),
                "source_addresses": kwargs.get("source_addresses", ["any"]),
                "destination_addresses": kwargs.get("destination_addresses", ["any"]),
                "applications": kwargs.get("applications", ["any"]),
                "action": kwargs.get("action", "allow"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
                "enabled": kwargs.get("enabled", True),
            }
            created_rules.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_security_rule)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file)])

        assert result.exit_code == 0
        assert "Applied security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout
        assert len(created_rules) == 1

    def test_load_security_rule_dry_run(self, runner, monkeypatch, mock_security_rules_yaml_file):
        """Test the load security rule command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_security_rule)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called  # Ensure the create method was not called
