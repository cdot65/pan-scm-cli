"""Tests for the security commands of scm-cli across different environments.

This module tests security commands work with the scm_client mock.
"""

from unittest.mock import patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestSecurityRuleCommands:
    """Test suite for security rule commands across environments."""

    def test_set_security_rule(self, runner, env_name, env):
        """Test setting a security rule."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.security.scm_client") as mock_client:
            mock_client.create_security_rule.return_value = {
                "id": "sr-123",
                "name": "test-rule",
                "folder": "Shared",
                "__action__": "created",
            }

            result = runner.invoke(
                app,
                [
                    "set",
                    "security",
                    "rule",
                    "--folder",
                    "Shared",
                    "--name",
                    "test-rule",
                    "--source-zones",
                    "trust",
                    "--destination-zones",
                    "untrust",
                    "--source-addresses",
                    "any",
                    "--destination-addresses",
                    "any",
                    "--applications",
                    "web-browsing",
                    "--action",
                    "allow",
                ],
            )

            assert result.exit_code == 0
            assert "test-rule" in result.stdout

    def test_set_security_rule_with_mock(self, runner, env_name, env):
        """Test setting a security rule with mocked client."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.security.scm_client") as mock_client:
            mock_client.create_security_rule.return_value = {
                "id": "sr-123",
                "name": "test-rule",
                "folder": "Shared",
                "__action__": "created",
            }

            result = runner.invoke(
                app,
                [
                    "set",
                    "security",
                    "rule",
                    "--folder",
                    "Shared",
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

            assert result.exit_code == 0
            assert "test-rule" in result.stdout

    def test_delete_security_rule(self, runner, env_name, env):
        """Test deleting a security rule."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.security.scm_client") as mock_client:
            mock_client.delete_security_rule.return_value = True

            result = runner.invoke(app, ["delete", "security", "rule", "--folder", "Shared", "--name", "test-rule"])

            assert result.exit_code == 0
            assert "Deleted" in result.stdout

    def test_load_security_rules(self, runner, env_name, env, mock_security_rules_yaml_file):
        """Test loading security rules from a YAML file."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.security.scm_client") as mock_client:
            mock_client.create_security_rule.return_value = {
                "name": "test-rule",
                "folder": "test-folder",
                "created": True,
            }

            result = runner.invoke(app, ["load", "security", "rule", "--file", str(mock_security_rules_yaml_file)])

            assert result.exit_code == 0
            assert "Successfully processed" in result.stdout
