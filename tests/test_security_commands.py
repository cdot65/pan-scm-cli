"""Tests for the security commands module."""

import typer
from scm_cli.commands.security import (
    delete_command,
    delete_security_rule,
    load_command,
    load_security_rule,
    set_command,
    set_security_rule,
)


class TestSecurityCommands:
    """Test the security commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_command is not None
        assert isinstance(set_command, typer.Typer)

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_command is not None
        assert isinstance(delete_command, typer.Typer)

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_command is not None
        assert isinstance(load_command, typer.Typer)


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

        # Invoke the command
        result = runner.invoke(
            set_security_rule,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
                "--source-zone",
                "trust",
                "--destination-zone",
                "untrust",
                "--source-address",
                "192.168.1.0/24",
                "--destination-address",
                "any",
                "--application",
                "web-browsing",
                "--application",
                "ssl",
                "--action",
                "allow",
                "--description",
                "Test security rule",
                "--tag",
                "test",
                "--tag",
                "example",
                "--enabled",
            ],
        )

        assert result.exit_code == 0
        assert "Created security rule" in result.stdout
        assert "ID: sr-12345" in result.stdout
        assert "Name: test-rule" in result.stdout
        assert "Folder: test-folder" in result.stdout
        assert "Source zones: " in result.stdout
        assert "trust" in result.stdout
        assert "Destination zones: " in result.stdout
        assert "untrust" in result.stdout
        assert "Source addresses: " in result.stdout
        assert "192.168.1.0/24" in result.stdout
        assert "Destination addresses: " in result.stdout
        assert "any" in result.stdout
        assert "Applications: " in result.stdout
        assert "web-browsing" in result.stdout
        assert "ssl" in result.stdout
        assert "Action: allow" in result.stdout
        assert "Description: Test security rule" in result.stdout
        assert "Tags: " in result.stdout
        assert "test" in result.stdout
        assert "example" in result.stdout
        assert "Enabled: True" in result.stdout

    def test_set_security_rule_error(self, runner, monkeypatch):
        """Test the set security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create_error)

        # Invoke the command
        result = runner.invoke(
            set_security_rule,
            ["--folder", "test-folder", "--name", "test-rule", "--source-zone", "trust", "--destination-zone", "untrust"],
        )

        assert result.exit_code == 1
        assert "Error creating security rule" in result.stdout
        assert "API Error" in result.stdout

    def test_delete_security_rule_command(self, runner, monkeypatch):
        """Test the delete security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete)

        # Invoke the command
        result = runner.invoke(delete_security_rule, ["--folder", "test-folder", "--name", "test-rule"])

        assert result.exit_code == 0
        assert "Deleted security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_security_rule_error(self, runner, monkeypatch):
        """Test the delete security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete_error)

        # Invoke the command
        result = runner.invoke(delete_security_rule, ["--folder", "test-folder", "--name", "test-rule"])

        assert result.exit_code == 1
        assert "Error deleting security rule" in result.stdout
        assert "API Error" in result.stdout

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

        # Invoke the command
        result = runner.invoke(load_security_rule, ["--file", str(mock_security_rules_yaml_file)])

        assert result.exit_code == 0
        assert "Loaded 1 security rule(s)" in result.stdout
        assert len(created_rules) == 1
        assert created_rules[0]["name"] == "test-rule"
        assert created_rules[0]["folder"] == "test-folder"
        assert "trust" in created_rules[0]["source_zones"]
        assert "untrust" in created_rules[0]["destination_zones"]
        assert created_rules[0]["action"] == "allow"
        assert created_rules[0]["enabled"] is True

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

        # Invoke the command with dry-run
        result = runner.invoke(load_security_rule, ["--file", str(mock_security_rules_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert not mock_called  # Ensure the mock wasn't called due to dry-run

    def test_load_security_rule_error(self, runner, monkeypatch, mock_security_rules_yaml_file):
        """Test the load security rule command with an error."""
        # Mock the config loader to simulate an error
        from scm_cli.utils import config

        def mock_load_error(*args, **kwargs):
            raise ValueError("Invalid file format")

        monkeypatch.setattr(config, "load_from_yaml", mock_load_error)

        # Invoke the command
        result = runner.invoke(load_security_rule, ["--file", str(mock_security_rules_yaml_file)])

        assert result.exit_code == 1
        assert "Error loading security rules" in result.stdout
        assert "Invalid file format" in result.stdout
