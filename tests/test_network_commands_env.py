"""Tests for the network commands of scm-cli across different environments.

This module tests the network commands for managing zones and other network
objects in different environments (dev, test, prod).
"""

from unittest.mock import MagicMock, patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestZoneCommands:
    """Test suite for zone commands across environments."""

    def test_set_zone(self, runner, env_name, env):
        """Test setting a zone in different environments.

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
            mock_client.zone.create.return_value = {"id": "123", "name": "test-zone"}
            mock_get_client.return_value = mock_client

            # Run the command with the required parameters
            result = runner.invoke(app, ["set", "network", "zone", "--folder", "Shared", "--name", "test-zone", "--mode", "layer3", "--interfaces", "ethernet1/1,ethernet1/2"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "test-zone" in result.stdout

            # Verify the client was called with correct parameters
            mock_client.zone.create.assert_called_once()
            args, kwargs = mock_client.zone.create.call_args
            assert kwargs.get("folder") == "Shared"
            assert kwargs.get("name") == "test-zone"
            assert kwargs.get("mode") == "layer3"

    def test_set_zone_with_mock(self, runner, env_name, env):
        """Test setting a zone with mock flag in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        # Run the command with the required parameters and mock flag
        result = runner.invoke(app, ["set", "network", "zone", "--folder", "Shared", "--name", "test-zone", "--mode", "layer3", "--interfaces", "ethernet1/1,ethernet1/2", "--mock"])

        # Check that the command executed successfully with mock message
        assert result.exit_code == 0
        assert "Mock" in result.stdout

    def test_delete_zone(self, runner, env_name, env):
        """Test deleting a zone in different environments.

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
            mock_client.zone.delete.return_value = {"status": "success"}
            mock_get_client.return_value = mock_client

            # Run the command with the required parameters
            result = runner.invoke(app, ["delete", "network", "zone", "--folder", "Shared", "--name", "test-zone"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "success" in result.stdout.lower()

            # Verify the client was called with correct parameters
            mock_client.zone.delete.assert_called_once()
            args, kwargs = mock_client.zone.delete.call_args
            assert kwargs.get("folder") == "Shared"
            assert kwargs.get("name") == "test-zone"

    def test_load_zones(self, runner, env_name, env, mock_zones_yaml_file):
        """Test loading zones from a YAML file in different environments.

        Args:
            runner: CLI runner fixture
            env_name: Name of the environment being tested
            env: Current environment fixture
            mock_zones_yaml_file: Mock YAML file fixture for zones
        """
        # Only run the test for the current environment
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.client.get_scm_client") as mock_get_client:
            # Mock the client to return successfully
            mock_client = MagicMock()
            mock_client.zone.create.return_value = {"status": "success"}
            mock_get_client.return_value = mock_client

            # Run the command with the mock file
            result = runner.invoke(app, ["load", "network", "zone", "--file", str(mock_zones_yaml_file)])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Loaded configuration" in result.stdout

            # Verify the client was called
            mock_client.zone.create.assert_called_once()


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestNetworkLocationCommands:
    """Test suite for network location commands across environments."""

    def test_set_network_location(self, runner, env_name, env):
        """Test setting a network location in different environments.

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
            mock_client.network_location.create.return_value = {"id": "123", "name": "test-location"}
            mock_get_client.return_value = mock_client

            # Run the command with the required parameters
            result = runner.invoke(app, ["set", "network", "location", "--name", "test-location", "--ip-ranges", "192.168.1.0/24,10.0.0.0/8"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "test-location" in result.stdout

            # Verify the client was called with correct parameters
            mock_client.network_location.create.assert_called_once()
            args, kwargs = mock_client.network_location.create.call_args
            assert kwargs.get("name") == "test-location"
            assert "192.168.1.0/24" in kwargs.get("ip_ranges", [])
            assert "10.0.0.0/8" in kwargs.get("ip_ranges", [])
