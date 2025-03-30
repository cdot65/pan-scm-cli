"""Pytest configuration file for scm-cli.

This file contains fixtures and configuration for testing the scm-cli application.
"""

import os
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))


@pytest.fixture(autouse=True)
def mock_dynaconf_settings(monkeypatch):
    """Mock dynaconf settings for testing.

    This fixture is automatically applied to all tests and sets up
    environment variables that dynaconf will read for credentials.
    """
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "test-tsg-id")
    monkeypatch.setenv("SCM_LOG_LEVEL", "DEBUG")


@pytest.fixture
def runner():
    """Return a CLI runner for testing Typer commands."""
    return CliRunner()


@pytest.fixture
def test_config_path():
    """Return the path to the test configuration files."""
    return Path(os.path.join(os.path.dirname(__file__), "data"))


@pytest.fixture
def mock_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for testing."""
    yaml_content = """
    bandwidth_allocations:
      - name: test-allocation
        folder: test-folder
        bandwidth: 1000
        description: Test allocation
        tags:
          - test
          - example
    """
    test_file = tmp_path / "test_config.yml"
    test_file.write_text(yaml_content)
    return test_file


@pytest.fixture
def mock_zones_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for zones testing."""
    yaml_content = """
    zones:
      - name: test-zone
        folder: test-folder
        mode: L3
        interfaces:
          - ethernet1/1
        description: Test zone
        tags:
          - test
          - example
    """
    test_file = tmp_path / "test_zones.yml"
    test_file.write_text(yaml_content)
    return test_file


@pytest.fixture
def mock_address_groups_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for address groups testing."""
    yaml_content = """
    address_groups:
      - name: test-group
        folder: test-folder
        type: static
        members:
          - 192.168.1.0/24
          - 10.0.0.0/8
        description: Test address group
        tags:
          - test
          - example
    """
    test_file = tmp_path / "test_address_groups.yml"
    test_file.write_text(yaml_content)
    return test_file


@pytest.fixture
def mock_security_rules_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for security rules testing."""
    yaml_content = """
    security_rules:
      - name: test-rule
        folder: test-folder
        source_zones:
          - trust
        destination_zones:
          - untrust
        source_addresses:
          - any
        destination_addresses:
          - any
        applications:
          - web-browsing
        action: allow
        description: Test security rule
        tags:
          - test
          - example
        enabled: true
    """
    test_file = tmp_path / "test_security_rules.yml"
    test_file.write_text(yaml_content)
    return test_file
