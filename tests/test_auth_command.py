"""Tests for the context test (authentication) functionality of scm-cli.

This module tests the context test command for verifying authentication credentials.
"""

from unittest.mock import patch

from scm_cli.main import app


def test_context_test_no_context(runner, monkeypatch, tmp_path):
    """Test 'context test' when no context is set."""
    # Ensure no current context exists
    monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

    result = runner.invoke(app, ["context", "test"])

    assert result.exit_code == 1
    assert "No context specified" in result.output or "no current context" in result.output.lower()


def test_context_test_nonexistent_context(runner, monkeypatch):
    """Test 'context test' with a context that doesn't exist."""
    monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

    def mock_get_config(name):
        raise ValueError(f"Context '{name}' not found")

    monkeypatch.setattr("scm_cli.commands.context.get_context_config", mock_get_config)

    result = runner.invoke(app, ["context", "test", "nonexistent"])

    assert result.exit_code == 1


def test_context_test_mock_mode(runner, monkeypatch):
    """Test 'context test --mock' with a valid context."""
    monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "test-ctx")
    monkeypatch.setattr(
        "scm_cli.commands.context.get_context_config",
        lambda name: {"client_id": "test-id", "client_secret": "test-secret", "tsg_id": "test-tsg"},
    )

    result = runner.invoke(app, ["context", "test", "test-ctx", "--mock"])

    assert result.exit_code == 0
    assert "mock mode" in result.output.lower()
