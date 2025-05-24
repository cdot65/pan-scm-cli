"""Tests for the objects commands of scm-cli across different environments.

This module tests the objects commands for managing address objects and address groups
in different environments (dev, test, prod).
"""

from unittest.mock import patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestAddressCommands:
    """Test suite for address object commands across environments."""

    def test_set_address(self, runner, env_name, env):
        """Test setting an address object in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            # Mock the client to return successfully
            mock_client.create_address.return_value = {"id": "123", "name": "test-address", "folder": "Shared"}

            # Run the command with the required parameters
            result = runner.invoke(app, ["set", "objects", "address", "--folder", "Shared", "--name", "test-address", "--ip-netmask", "192.168.1.1/32"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "test-address" in result.stdout
            assert "Created address" in result.stdout

    def test_set_address_with_mock(self, runner, env_name, env):
        """Test setting an address object with mock flag in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            # Mock the client to simulate a mock response
            mock_client.create_address.return_value = {"name": "test-address", "folder": "Shared", "mock": True}

            # Run the command with the required parameters
            result = runner.invoke(app, ["set", "objects", "address", "--folder", "Shared", "--name", "test-address", "--ip-netmask", "192.168.1.1/32"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "test-address" in result.stdout

    def test_delete_address(self, runner, env_name, env):
        """Test deleting an address object in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            # Mock the client to return successfully
            mock_client.delete_address.return_value = {"status": "success"}

            # Run the command with the required parameters
            result = runner.invoke(app, ["delete", "objects", "address", "--folder", "Shared", "--name", "test-address"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Deleted address" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestAddressGroupCommands:
    """Test suite for address group commands across environments."""

    def test_set_address_group(self, runner, env_name, env):
        """Test setting an address group in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            # Mock the client to return successfully
            mock_client.create_address_group.return_value = {"id": "123", "name": "test-group", "folder": "Shared"}

            # Run the command with the required parameters
            result = runner.invoke(
                app,
                [
                    "set",
                    "objects",
                    "address-group",
                    "--folder",
                    "Shared",
                    "--name",
                    "test-group",
                    "--type",
                    "static",  # Use --type static as required
                    "--description",
                    "Test address group",
                    "--members",
                    "192.168.1.0/24,10.0.0.0/8",
                ],
            )

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Created address group" in result.stdout

    def test_load_address_groups(self, runner, env_name, env, mock_address_groups_yaml_file):
        """Test loading address groups from a YAML file in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
            mock_address_groups_yaml_file: Mock YAML file fixture for address groups
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            # Mock the client to return successfully
            mock_client.create_address_group.return_value = {"name": "test-group", "folder": "test-folder"}

            # Run the command with the mock file
            result = runner.invoke(app, ["load", "objects", "address-group", "--file", str(mock_address_groups_yaml_file)])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Applied address group" in result.stdout
