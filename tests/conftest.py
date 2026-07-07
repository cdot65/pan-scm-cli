"""Pytest configuration file for scm-cli.

This file contains fixtures and configuration for testing the scm-cli application.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Patch context before any module imports config.py, preventing real credentials
# from ~/.scm-cli/contexts/ from leaking into tests.
_ctx_patcher = patch("scm_cli.utils.context.get_current_context", return_value=None)
_ctx_patcher.start()

# Recreate settings without context file (must happen after context patch, before Scm patch)
import scm_cli.utils.config as _config_module  # noqa: E402
from scm_cli.utils.context import get_context_aware_settings as _get_settings  # noqa: E402

_config_module.settings = _get_settings()

# Patch Scm SDK client before any test modules import it, preventing real HTTP auth calls.
# Must patch where Scm is used (sdk_client module), not where it's defined (scm.client),
# because sdk_client.py does `from scm.client import Scm` creating a local reference.
_scm_patcher = patch("scm_cli.utils.sdk_client.Scm", return_value=MagicMock())
_scm_patcher.start()


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
    # Mock mode must now be requested explicitly (no silent fallback on
    # missing credentials), so opt the whole suite in. Tests that exercise
    # real-client init delete SCM_MOCK and patch Scm/credentials themselves.
    monkeypatch.setenv("SCM_MOCK", "1")


@pytest.fixture(autouse=True)
def reset_scm_client():
    """Reset the LazyClient between tests so each test gets a fresh client."""
    import scm_cli.utils.sdk_client as sdk_module

    if hasattr(sdk_module, "scm_client"):
        sdk_module.scm_client._client = None


@pytest.fixture
def env():
    """Return the current environment name for environment-parametrized tests."""
    return "dev"


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
        bandwidth: 1000
        spn_name_list:
          - spn1
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
    security_zones:
      - name: test-zone
        folder: test-folder
        network:
          layer3:
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
def mock_ipsec_crypto_profiles_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for IPsec crypto profiles testing."""
    yaml_content = """
    ipsec_crypto_profiles:
      - name: test-ipsec-profile
        folder: Texas
        esp_encryption:
          - aes-256-cbc
        esp_authentication:
          - sha256
        dh_group: group14
        lifetime_hours: 1
    """
    test_file = tmp_path / "test_ipsec_crypto_profiles.yml"
    test_file.write_text(yaml_content)
    return test_file


@pytest.fixture
def mock_nat_rules_yaml_file(test_config_path, tmp_path):
    """Create a mock YAML file for NAT rules testing."""
    yaml_content = """
    nat_rules:
      - name: outbound-nat
        folder: Texas
        nat_type: ipv4
        from:
          - trust
        to:
          - untrust
        source:
          - any
        destination:
          - any
        service: any
        source_translation:
          dynamic_ip_and_port:
            type: dynamic_ip_and_port
            translated_address:
              - 10.0.0.1
    """
    test_file = tmp_path / "test_nat_rules.yml"
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
