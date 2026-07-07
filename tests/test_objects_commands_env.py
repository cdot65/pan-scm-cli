"""Tests for the objects commands of scm-cli across different environments.

This module tests object commands work with the scm_client mock.
"""

from unittest.mock import patch

import pytest

from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestAddressCommands:
    """Test suite for address object commands across environments."""

    def test_set_address(self, runner, env_name, env):
        """Test setting an address object."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            mock_client.create_address.return_value = {
                "id": "addr-123",
                "name": "test-address",
                "folder": "Shared",
                "__action__": "created",
            }

            result = runner.invoke(
                app,
                ["set", "object", "address", "test-address", "--folder", "Shared", "--ip-netmask", "192.168.1.1/32"],
            )

            assert result.exit_code == 0
            assert "test-address" in result.stdout

    def test_set_address_with_mock(self, runner, env_name, env):
        """Test setting an address object with mocked client."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            mock_client.create_address.return_value = {
                "name": "test-address",
                "folder": "Shared",
                "__action__": "created",
            }

            result = runner.invoke(
                app,
                ["set", "object", "address", "test-address", "--folder", "Shared", "--ip-netmask", "192.168.1.1/32"],
            )

            assert result.exit_code == 0
            assert "test-address" in result.stdout

    def test_delete_address(self, runner, env_name, env):
        """Test deleting an address object."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            mock_client.delete_address.return_value = True

            result = runner.invoke(app, ["delete", "object", "address", "test-address", "--folder", "Shared", "--force"])

            assert result.exit_code == 0
            assert "Deleted address" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
class TestAddressGroupCommands:
    """Test suite for address group commands across environments."""

    def test_set_address_group(self, runner, env_name, env):
        """Test setting an address group."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            mock_client.create_address_group.return_value = {
                "id": "ag-123",
                "name": "test-group",
                "folder": "Shared",
                "__action__": "created",
            }

            result = runner.invoke(
                app,
                [
                    "set",
                    "object",
                    "address-group",
                    "test-group",
                    "--folder",
                    "Shared",
                    "--type",
                    "static",
                    "--description",
                    "Test address group",
                    "--members",
                    "192.168.1.0/24,10.0.0.0/8",
                ],
            )

            assert result.exit_code == 0
            assert "test-group" in result.stdout

    def test_load_address_groups(self, runner, env_name, env, mock_address_groups_yaml_file):
        """Test loading address groups from a YAML file."""
        if env != env_name:
            pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

        with patch("scm_cli.commands.objects.scm_client") as mock_client:
            mock_client.create_address_group.return_value = {
                "name": "test-group",
                "folder": "test-folder",
                "created": True,
            }

            result = runner.invoke(app, ["load", "object", "address-group", "--file", str(mock_address_groups_yaml_file)])

            assert result.exit_code == 0
            assert "Successfully processed" in result.stdout
