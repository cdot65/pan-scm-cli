"""Tests for the authentication functionality of scm-cli.

This module tests the auth command for verifying authentication credentials
across different environments (dev, test, prod).
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from scm_cli.main import app


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
def test_auth_command_with_mock(runner, env_name, env, monkeypatch):
    """Test the 'test auth' command with mock flag in different environments.

    Args:
        runner: CLI runner fixture
        env_name: Name of the environment being tested
        env: Current environment fixture
        monkeypatch: pytest monkeypatch fixture
    """
    # Only run the test for the current environment
    if env != env_name:
        pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

    # Run the command with mock flag
    result = runner.invoke(app, ["test", "auth", "--mock"])

    # Check that the command executed successfully
    assert result.exit_code == 0
    assert "Authentication simulation successful (mock mode)" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
def test_auth_command_with_env_vars(runner, env_name, env, monkeypatch):
    """Test the 'test auth' command using environment variables in different environments.

    Args:
        runner: CLI runner fixture
        env_name: Name of the environment being tested
        env: Current environment fixture
        monkeypatch: pytest monkeypatch fixture
    """
    # Only run the test for the current environment
    if env != env_name:
        pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

    with patch("scm_cli.client.scm.client.Scm") as mock_scm:
        # Mock the client to return successfully
        mock_client = MagicMock()
        mock_client.address.list.return_value = [{"name": "test-address"}]
        mock_scm.return_value = mock_client

        # Run the command
        result = runner.invoke(app, ["test", "auth"])

        # Check that the command executed successfully
        assert result.exit_code == 0
        assert "Authentication successful!" in result.stdout
        assert "Successfully connected to SCM API" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
def test_auth_command_with_config_file(runner, env_name, env, mock_config_file):
    """Test the 'test auth' command using config file in different environments.

    Args:
        runner: CLI runner fixture
        env_name: Name of the environment being tested
        env: Current environment fixture
        mock_config_file: Mock config file fixture
    """
    # Only run the test for the current environment
    if env != env_name:
        pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

    with patch("scm_cli.client.scm.client.Scm") as mock_scm:
        # Mock the client to return successfully
        mock_client = MagicMock()
        mock_client.address.list.return_value = [{"name": "test-address"}]
        mock_scm.return_value = mock_client

        # Clear environment variables to force config file usage
        with patch.dict(os.environ, {"SCM_CLIENT_ID": "", "SCM_CLIENT_SECRET": "", "SCM_TSG_ID": ""}, clear=True):
            # Run the command
            result = runner.invoke(app, ["test", "auth"])

            # Check that the command executed successfully
            assert result.exit_code == 0
            assert "Authentication successful!" in result.stdout
            assert "Successfully connected to SCM API" in result.stdout


@pytest.mark.parametrize("env_name", ["dev", "test", "prod"])
def test_auth_command_api_error(runner, env_name, env):
    """Test the 'test auth' command with API connectivity error in different environments.

    Args:
        runner: CLI runner fixture
        env_name: Name of the environment being tested
        env: Current environment fixture
    """
    # Only run the test for the current environment
    if env != env_name:
        pytest.skip(f"Skipping test for {env_name} environment (current: {env})")

    with patch("scm_cli.client.scm.client.Scm") as mock_scm:
        # Mock the client but have address.list raise an exception
        mock_client = MagicMock()
        mock_client.address.list.side_effect = Exception("API connection error")
        mock_scm.return_value = mock_client

        # Run the command
        result = runner.invoke(app, ["test", "auth"])

        # Check that authentication is still successful but connectivity error is reported
        assert result.exit_code == 0
        assert "Authentication successful!" in result.stdout
        assert "Could not verify API connectivity: API connection error" in result.stdout


def test_legacy_auth_command_deprecated(runner):
    """Test that the legacy 'test-auth' command shows a deprecation warning."""
    with patch("scm_cli.client.get_scm_client") as mock_get_client:
        # Mock the client to avoid actual API calls
        mock_get_client.return_value = MagicMock()

        # Run the legacy command
        result = runner.invoke(app, ["test-auth", "--mock"])

        # Check for deprecation warning
        assert result.exit_code == 0
        assert "deprecated" in result.stdout.lower()
        assert "please use 'test auth' instead" in result.stdout.lower()
