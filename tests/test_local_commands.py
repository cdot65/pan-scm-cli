"""Tests for local config commands."""

import os

import pytest

from src.scm_cli.main import app
from src.scm_cli.commands import local as local_module
from src.scm_cli.utils.sdk_client import SCMClient

app.add_typer(local_module.app, name="local")


@pytest.fixture
def mock_local_env(monkeypatch, tmp_path):
    """Set up mock environment for local config tests."""
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestLocalConfigSDKClient:
    """Test SDK client methods for local config."""

    def test_list_local_config_versions_mock(self):
        """list_local_config_versions returns mock data when no client."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.list_local_config_versions(device="fw-01")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "version" in result[0]
        assert "date" in result[0]

    def test_download_local_config_mock(self):
        """download_local_config returns mock XML bytes when no client."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.download_local_config(device="fw-01", version=42)
        assert isinstance(result, bytes)
        assert b"<config" in result


class TestLocalList:
    """Test local list command."""

    def test_list_versions_mock(self, runner, mock_local_env):
        """scm local list shows config versions in table."""
        result = runner.invoke(app, ["local", "list", "--device", "fw-01"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "42" in result.output
        assert "admin" in result.output

    def test_list_versions_empty(self, runner, mock_local_env, monkeypatch):
        """scm local list shows message when no versions found."""
        monkeypatch.setattr(
            "src.scm_cli.utils.sdk_client.SCMClient.list_local_config_versions",
            lambda self, device: [],
        )
        result = runner.invoke(app, ["local", "list", "--device", "fw-01"])
        assert result.exit_code == 0
        assert "No config versions found" in result.output


class TestLocalDownload:
    """Test local download command."""

    def test_download_to_stdout(self, runner, mock_local_env):
        """scm local download outputs XML to stdout."""
        result = runner.invoke(app, ["local", "download", "--device", "fw-01", "--version", "42"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "<config" in result.output

    def test_download_to_file(self, runner, mock_local_env, tmp_path):
        """scm local download --output writes XML to file."""
        output_file = tmp_path / "config.xml"
        result = runner.invoke(app, [
            "local", "download",
            "--device", "fw-01",
            "--version", "42",
            "--output", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<config" in content
