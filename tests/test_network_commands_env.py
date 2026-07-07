"""Tests for the network commands of scm-cli across different environments.

This module tests network commands work with the scm_client mock.
"""

from unittest.mock import patch

import pytest

from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestZoneCommands:
    """Test suite for zone commands across environments."""

    def test_set_zone(self, runner, env_name, env):
        """Test setting a zone."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.network.scm_client") as mock_client:
            mock_client.create_zone.return_value = {
                "id": "zone-123",
                "name": "test-zone",
                "folder": "Shared",
                "mode": "layer3",
                "interfaces": ["ethernet1/1"],
            }

            result = runner.invoke(
                app,
                ["set", "network", "zone", "--folder", "Shared", "--name", "test-zone", "--mode", "layer3", "--interfaces", "ethernet1/1"],
            )

            assert result.exit_code == 0
            assert "test-zone" in result.stdout

    def test_set_zone_with_mock(self, runner, env_name, env):
        """Test setting a zone uses mock client (already mocked at conftest level)."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.network.scm_client") as mock_client:
            mock_client.create_zone.return_value = {
                "id": "zone-123",
                "name": "test-zone",
                "folder": "Shared",
                "mode": "layer3",
                "interfaces": [],
            }

            result = runner.invoke(
                app,
                ["set", "network", "zone", "--folder", "Shared", "--name", "test-zone", "--mode", "layer3"],
            )

            assert result.exit_code == 0
            assert "test-zone" in result.stdout

    def test_delete_zone(self, runner, env_name, env):
        """Test deleting a zone."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.network.scm_client") as mock_client:
            mock_client.delete_zone.return_value = True

            result = runner.invoke(app, ["delete", "network", "zone", "--folder", "Shared", "--name", "test-zone", "--force"])

            assert result.exit_code == 0
            assert "Deleted zone" in result.stdout

    def test_load_zones(self, runner, env_name, env, mock_zones_yaml_file):
        """Test loading zones from a YAML file."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.network.scm_client") as mock_client:
            mock_client.create_zone.return_value = {
                "name": "test-zone",
                "folder": "test-folder",
                "mode": "layer3",
                "interfaces": ["ethernet1/1"],
            }

            result = runner.invoke(app, ["load", "network", "zone", "--file", str(mock_zones_yaml_file)])

            assert result.exit_code == 0
            assert "Applied zone" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestNetworkLocationCommands:
    """Test suite for network location commands across environments."""

    def test_set_network_location(self, runner, env_name, env):
        """Test setting a network location."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        # Check if network location command exists
        result = runner.invoke(app, ["set", "network", "--help"])
        if "location" not in result.stdout:
            pytest.skip("Network location command not available")

        with patch("scm_cli.commands.network.scm_client") as mock_client:
            mock_client.create_network_location.return_value = {"id": "123", "name": "test-location"}

            result = runner.invoke(
                app,
                ["set", "network", "location", "--name", "test-location", "--ip-ranges", "192.168.1.0/24,10.0.0.0/8"],
            )

            assert result.exit_code == 0
            assert "test-location" in result.stdout
