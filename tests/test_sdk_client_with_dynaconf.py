"""Tests for the SDK client with dynaconf integration."""

from scm_cli.utils.config import settings
from scm_cli.utils.sdk_client import SCMClient


def test_sdk_client_init_with_credentials(monkeypatch):
    """Test that SCMClient initializes correctly with dynaconf credentials."""
    # Set environment variables directly with monkeypatch
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "test-tsg-id")

    # Force settings reload
    settings.reload()

    # Mock the Scm class initialization to prevent real API calls
    monkeypatch.setattr("scm_cli.utils.sdk_client.Scm", lambda **kwargs: None)

    # Create a new client instance
    client = SCMClient()

    # Check if credentials were loaded correctly
    assert client.client_id == "test-client-id"
    assert client.client_secret == "test-client-secret"
    assert client.tsg_id == "test-tsg-id"


def test_sdk_client_fallback_to_mock_credentials(monkeypatch):
    """Test that SCMClient falls back to mock credentials when none are available."""
    # Unset environment variables
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")

    # Force settings reload
    settings.reload()

    # Create a new client instance
    client = SCMClient()

    # Check if mock credentials are used
    assert client.client_id == "mock-client-id"
    assert client.client_secret == "mock-client-secret"
    assert client.tsg_id == "mock-tsg-id"
    assert client.client is None  # No real client should be created
