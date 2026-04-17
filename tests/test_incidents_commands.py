"""Tests for incidents commands."""

import json

import pytest

from src.scm_cli.main import app
from src.scm_cli.commands import incidents as incidents_module
from src.scm_cli.utils.sdk_client import SCMClient

app.add_typer(incidents_module.app, name="incidents")


@pytest.fixture
def mock_incidents_env(monkeypatch, tmp_path):
    """Set up mock environment for incidents tests."""
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestIncidentsSDKClient:
    """Test SDK client methods for incidents."""

    def test_list_incidents_mock(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.list_incidents()
        assert isinstance(result, list)
        assert len(result) >= 2
        assert "id" in result[0]
        assert "status" in result[0]
        assert "severity" in result[0]

    def test_list_incidents_filter_status(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.list_incidents(status="open")
        assert all(i["status"] == "open" for i in result)

    def test_get_incident_mock(self):
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")
        result = client.get_incident(incident_id="INC-2026-04-001")
        assert isinstance(result, dict)
        assert "id" in result
        assert "alerts" in result
        assert "remediation" in result
        assert len(result["alerts"]) > 0


class TestIncidentsList:
    """Test incidents list command."""

    def test_list_incidents_table(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "list"])
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "INC-2026-04-001" in result.output
        assert "high" in result.output

    def test_list_incidents_filter_status(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "list", "--status", "closed"])
        assert result.exit_code == 0
        assert "INC-2026-03-088" in result.output
        assert "INC-2026-04-001" not in result.output

    def test_list_incidents_json(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_incidents_empty(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "list", "--severity", "informational"])
        assert result.exit_code == 0
        assert "No incidents found" in result.output


class TestIncidentsShow:
    """Test incidents show command."""

    def test_show_incident_detail(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "show", "INC-2026-04-001"])
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "INC-2026-04-001" in result.output
        assert "Suspicious lateral movement" in result.output
        assert "Alerts" in result.output
        assert "Remediation" in result.output

    def test_show_incident_json(self, runner, mock_incidents_env):
        result = runner.invoke(app, ["incidents", "show", "INC-2026-04-001", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "INC-2026-04-001"
        assert "alerts" in data
        assert "remediation" in data
