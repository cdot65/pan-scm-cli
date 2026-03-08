"""Tests for commit command."""

import pytest
from typer.testing import CliRunner

from src.scm_cli.commands import commit
from src.scm_cli.main import app

# Register commit command for testing (main.py registration handled separately)
app.add_typer(commit.app, name="commit")


@pytest.fixture
def mock_commit_env(monkeypatch, tmp_path):
    """Set up mock environment for commit tests."""
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))

    # Override all credential env vars to trigger mock mode
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestCommit:
    """Test commit command."""

    def test_commit_basic_mock(self, runner, mock_commit_env):
        """Test basic commit in mock mode."""
        result = runner.invoke(app, ["commit", "--folder", "Texas", "--description", "Test commit"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "Texas" in result.output
        assert "mock-job-99999" in result.output

    def test_commit_multiple_folders(self, runner, mock_commit_env):
        """Test commit with multiple folders."""
        result = runner.invoke(
            app,
            ["commit", "--folder", "Texas", "--folder", "California", "--description", "Multi-folder commit"],
        )
        assert result.exit_code == 0
        assert "Texas" in result.output
        assert "California" in result.output

    def test_commit_sync_mock(self, runner, mock_commit_env):
        """Test synchronous commit in mock mode."""
        result = runner.invoke(
            app,
            ["commit", "--folder", "Texas", "--description", "Sync commit", "--sync"],
        )
        assert result.exit_code == 0
        assert "successful" in result.output.lower() or "mock-job-99999" in result.output

    def test_commit_sync_with_timeout(self, runner, mock_commit_env):
        """Test synchronous commit with custom timeout."""
        result = runner.invoke(
            app,
            ["commit", "--folder", "Texas", "--description", "Timeout commit", "--sync", "--timeout", "60"],
        )
        assert result.exit_code == 0

    def test_commit_shows_job_follow_up(self, runner, mock_commit_env):
        """Test that async commit shows job follow-up commands."""
        result = runner.invoke(
            app,
            ["commit", "--folder", "Texas", "--description", "Async commit"],
        )
        assert result.exit_code == 0
        # Should show job ID and follow-up instructions
        assert "mock-job-99999" in result.output
