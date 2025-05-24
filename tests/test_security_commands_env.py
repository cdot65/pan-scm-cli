"""Tests for the security commands of scm-cli across different environments.

This module tests the security commands for managing security rules
in different environments (dev, test, prod).
"""

from unittest.mock import MagicMock, patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestSecurityRuleCommands:
    """Test suite for security rule commands across environments."""

    def test_set_security_rule(self, runner, env_name, env):
        """Test setting a security rule in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.client.get_scm_client") as mock_get_client:
            # Mock the client to return successfully
            mock_client = MagicMock()
            mock_client.security_rule.create.return_value = {"id": "123", "name": "test-rule"}
            mock_get_client.return_value = mock_client

            # Run the command with the required parameters
            result = runner.invoke(
                app,
                [
                    "set",
                    "security",
                    "security-rule",
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

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "test-rule" in result.stdout

            # Verify the client was called with correct parameters
            mock_client.security_rule.create.assert_called_once()
            args, kwargs = mock_client.security_rule.create.call_args
            assert kwargs.get("folder") == "Shared"
            assert kwargs.get("name") == "test-rule"
            assert "trust" in kwargs.get("source_zones", [])
            assert "untrust" in kwargs.get("destination_zones", [])
            assert "any" in kwargs.get("source_addresses", [])
            assert "any" in kwargs.get("destination_addresses", [])
            assert "web-browsing" in kwargs.get("applications", [])
            assert kwargs.get("action") == "allow"

    def test_set_security_rule_with_mock(self, runner, env_name, env):
        """Test setting a security rule with mock flag in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        # Run the command with the required parameters and mock flag
        result = runner.invoke(
            app,
            [
                "set",
                "security",
                "security-rule",
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
                "--mock",
            ],
        )

        # Check that the command executed successfully with mock message
        assert result.exit_code == 0
        assert "Mock" in result.stdout

    def test_delete_security_rule(self, runner, env_name, env):
        """Test deleting a security rule in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.client.get_scm_client") as mock_get_client:
            # Mock the client to return successfully
            mock_client = MagicMock()
            mock_client.security_rule.delete.return_value = {"status": "success"}
            mock_get_client.return_value = mock_client

            # Run the command with the required parameters
            result = runner.invoke(app, ["delete", "security", "security-rule", "--folder", "Shared", "--name", "test-rule"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "success" in result.stdout.lower()

            # Verify the client was called with correct parameters
            mock_client.security_rule.delete.assert_called_once()
            args, kwargs = mock_client.security_rule.delete.call_args
            assert kwargs.get("folder") == "Shared"
            assert kwargs.get("name") == "test-rule"

    def test_load_security_rules(self, runner, env_name, env, mock_security_rules_yaml_file):
        """Test loading security rules from a YAML file in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
            mock_security_rules_yaml_file: Mock YAML file fixture for security rules
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.client.get_scm_client") as mock_get_client:
            # Mock the client to return successfully
            mock_client = MagicMock()
            mock_client.security_rule.create.return_value = {"status": "success"}
            mock_get_client.return_value = mock_client

            # Run the command with the mock file
            result = runner.invoke(app, ["load", "security", "security-rule", "--file", str(mock_security_rules_yaml_file)])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Loaded configuration" in result.stdout

            # Verify the client was called
            mock_client.security_rule.create.assert_called_once()
