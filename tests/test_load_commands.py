"""Tests for the load commands of scm-cli.

This module tests the load commands for bulk operations across all resource types.
"""

from unittest.mock import MagicMock, patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize(
    "resource_type,fixture_name",
    [("address", "mock_yaml_file"), ("address-group", "mock_address_groups_yaml_file"), ("zone", "mock_zones_yaml_file"), ("security-rule", "mock_security_rules_yaml_file")],
)
def test_load_command(runner, resource_type, fixture_name, request):
    """Test the load command with different resource types.

    Args:
        runner: CLI runner fixture
        resource_type: Type of resource to load
        fixture_name: Name of the fixture containing mock YAML data
        request: pytest request fixture for accessing other fixtures
    """
    # Get the fixture value
    mock_file = request.getfixturevalue(fixture_name)

    # Determine the correct command category based on resource type
    if resource_type in ["address", "address-group"]:
        category = "objects"
    elif resource_type in ["zone"]:
        category = "network"
    elif resource_type in ["security-rule"]:
        category = "security"
    else:
        category = "objects"  # Default

    # Mock the client to return successfully
    with patch("scm_cli.client.get_scm_client") as mock_get_client:
        mock_client = MagicMock()

        # Set up the appropriate mock method based on resource type
        if resource_type == "address":
            mock_client.address.create.return_value = {"status": "success"}
        elif resource_type == "address-group":
            mock_client.address_group.create.return_value = {"status": "success"}
        elif resource_type == "zone":
            mock_client.zone.create.return_value = {"status": "success"}
        elif resource_type == "security-rule":
            mock_client.security_rule.create.return_value = {"status": "success"}

        mock_get_client.return_value = mock_client

        # Run the command with the mock file
        result = runner.invoke(app, ["load", category, resource_type, "--file", str(mock_file)])

        # Check that the command executed successfully
        assert result.exit_code == 0
        assert "Loaded configuration" in result.stdout


def test_load_command_with_invalid_yaml(runner, tmp_path):
    """Test the load command with invalid YAML file.

    Args:
        runner: CLI runner fixture
        tmp_path: pytest fixture for temporary directory
    """
    # Create an invalid YAML file
    invalid_yaml_file = tmp_path / "invalid.yaml"
    invalid_yaml_file.write_text("""
    addresses:
      - name: test
        invalid yaml content
    """)

    # Run the command with the invalid file
    result = runner.invoke(app, ["load", "objects", "address", "--file", str(invalid_yaml_file)])

    # Check that the command failed with appropriate error
    assert result.exit_code != 0
    assert "Error parsing YAML" in result.stdout


def test_load_command_with_nonexistent_file(runner):
    """Test the load command with a file that doesn't exist.

    Args:
        runner: CLI runner fixture
    """
    # Run the command with a nonexistent file
    result = runner.invoke(app, ["load", "objects", "address", "--file", "/path/to/nonexistent/file.yaml"])

    # Check that the command failed with appropriate error
    assert result.exit_code != 0
    assert "File not found" in result.stdout


def test_load_command_with_mock_flag(runner, mock_yaml_file):
    """Test the load command with mock flag.

    Args:
        runner: CLI runner fixture
        mock_yaml_file: Mock YAML file fixture
    """
    # Run the command with mock flag
    result = runner.invoke(app, ["load", "objects", "address", "--file", str(mock_yaml_file), "--mock"])

    # Check that the command executed successfully with mock message
    assert result.exit_code == 0
    assert "Mock" in result.stdout
