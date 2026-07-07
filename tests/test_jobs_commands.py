"""Tests for jobs management commands."""

import json

import pytest
from typer.testing import CliRunner

from src.scm_cli.commands import jobs
from src.scm_cli.main import app

# Register jobs command for testing (main.py registration handled separately)
app.add_typer(jobs.app, name="jobs")


@pytest.fixture
def mock_jobs_env(monkeypatch, tmp_path):
    """Set up mock environment for jobs tests."""
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))

    # Override all credential env vars to trigger mock mode
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestJobsList:
    """Test jobs list command."""

    def test_list_jobs_mock(self, runner, mock_jobs_env):
        """Test listing jobs in mock mode."""
        result = runner.invoke(app, ["jobs", "list"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "11111" in result.output
        assert "22222" in result.output
        assert "33333" in result.output

    def test_list_jobs_with_max_results(self, runner, mock_jobs_env):
        """Test listing jobs with max results."""
        result = runner.invoke(app, ["jobs", "list", "--max-results", "2"])
        assert result.exit_code == 0
        assert "11111" in result.output
        assert "22222" in result.output

    def test_list_jobs_output_json(self, mock_jobs_env):
        """Test jobs list --output json emits machine-readable data on stdout."""
        result = CliRunner(mix_stderr=False).invoke(app, ["jobs", "list", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["id"] == "11111"
        assert data[0]["status"] == "FIN"
        assert data[1]["id"] == "22222"


class TestJobsStatus:
    """Test jobs status command."""

    def test_job_status_mock(self, runner, mock_jobs_env):
        """Test getting job status in mock mode."""
        result = runner.invoke(app, ["jobs", "status", "--id", "12345"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "12345" in result.output
        assert "FIN" in result.output

    def test_job_status_shows_details(self, runner, mock_jobs_env):
        """Test that job status shows detail fields."""
        result = runner.invoke(app, ["jobs", "status", "--id", "99999"])
        assert result.exit_code == 0
        assert "CommitAll" in result.output

    def test_job_status_output_json(self, mock_jobs_env):
        """Test jobs status --output json emits machine-readable data on stdout."""
        result = CliRunner(mix_stderr=False).invoke(app, ["jobs", "status", "--id", "12345", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "12345"
        assert data["status_str"] == "FIN"
        assert data["type_str"] == "CommitAll"


class TestJobsWait:
    """Test jobs wait command."""

    def test_wait_for_job_mock(self, runner, mock_jobs_env):
        """Test waiting for a job in mock mode."""
        result = runner.invoke(app, ["jobs", "wait", "--id", "12345"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "12345" in result.output
        assert "completed" in result.output.lower() or "FIN" in result.output

    def test_wait_for_job_with_timeout(self, runner, mock_jobs_env):
        """Test waiting for a job with custom timeout."""
        result = runner.invoke(app, ["jobs", "wait", "--id", "12345", "--timeout", "60"])
        assert result.exit_code == 0
        assert "12345" in result.output
