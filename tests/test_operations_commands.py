"""Tests for device operations commands."""

import pytest

from src.scm_cli.main import app
from src.scm_cli.commands import operations as ops_module
from src.scm_cli.utils.sdk_client import SCMClient

app.add_typer(ops_module.app, name="operations")


@pytest.fixture
def mock_ops_env(monkeypatch, tmp_path):
    """Set up mock environment for operations tests."""
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestOperationsSDKClient:
    """Test SDK client methods for device operations."""

    def test_dispatch_operation_mock_sync(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.dispatch_device_operation(device="fw-01", operation="route-table", sync=True)
        assert isinstance(result, dict)
        assert result["status"] == "completed"
        assert "results" in result

    def test_dispatch_operation_mock_async(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.dispatch_device_operation(device="fw-01", operation="route-table", sync=False)
        assert isinstance(result, dict)
        assert "job_id" in result

    def test_get_operation_status_mock(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.get_device_operation_status(job_id="job-abc")
        assert isinstance(result, dict)
        assert "job_id" in result
        assert "state" in result


class TestOperationsRouteTable:
    """Test operations route-table command."""

    def test_route_table_sync(self, runner, mock_ops_env):
        result = runner.invoke(app, ["operations", "route-table", "--device", "fw-01"])
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "0.0.0.0/0" in result.output
        assert "10.0.0.1" in result.output

    def test_route_table_async(self, runner, mock_ops_env):
        result = runner.invoke(app, ["operations", "route-table", "--device", "fw-01", "--async"])
        assert result.exit_code == 0
        assert "mock-job-route-table" in result.output


class TestOperationsInterfaces:
    """Test operations interfaces command."""

    def test_interfaces_sync(self, runner, mock_ops_env):
        result = runner.invoke(app, ["operations", "interfaces", "--device", "fw-01"])
        assert result.exit_code == 0
        assert "ethernet1/1" in result.output


class TestOperationsStatus:
    """Test operations status command."""

    def test_status_check(self, runner, mock_ops_env):
        result = runner.invoke(app, ["operations", "status", "--job-id", "job-abc"])
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "job-abc" in result.output
        assert "completed" in result.output
