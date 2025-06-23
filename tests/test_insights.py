"""Tests for insights commands."""

import os
import pytest
from typer.testing import CliRunner

from src.scm_cli.main import app


@pytest.fixture
def mock_insights_env(monkeypatch, tmp_path):
    """Set up mock environment for insights tests."""
    # Mock the context file to return None (no context)
    monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))
    monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
    
    # Override all credential env vars to trigger mock mode
    monkeypatch.setenv("SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_TSG_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_ID", "")
    monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "")
    monkeypatch.setenv("SCM_SCM_TSG_ID", "")


class TestInsightsAlerts:
    """Test insights alerts commands."""

    def test_list_alerts_mock(self, runner, mock_insights_env):
        """Test listing alerts in mock mode."""
        result = runner.invoke(app, ["insights", "alerts", "--list"])
        
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "alert-001" in result.output
        assert "Critical CPU Usage" in result.output
        assert "alert-002" in result.output
        assert "Tunnel Down" in result.output

    def test_get_alert_mock(self, runner, mock_insights_env):
        """Test getting a specific alert in mock mode."""
        result = runner.invoke(app, ["insights", "alerts", "--id", "alert-001"])
        assert result.exit_code == 0
        assert "alert-001" in result.output
        assert "Critical CPU Usage" in result.output

    def test_list_alerts_with_filters_mock(self, runner, mock_insights_env):
        """Test listing alerts with filters in mock mode."""
        result = runner.invoke(app, ["insights", "alerts", "--list", "--severity", "critical"])
        assert result.exit_code == 0
        assert "alert-001" in result.output
        assert "Critical CPU Usage" in result.output

    def test_export_alerts_json(self, runner, mock_insights_env, tmp_path):
        """Test exporting alerts to JSON."""
        output_file = tmp_path / "alerts.json"
        result = runner.invoke(app, ["insights", "alerts", "--list", "--export", "json", "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Data exported to" in result.output

    def test_export_alerts_csv(self, runner, mock_insights_env, tmp_path):
        """Test exporting alerts to CSV."""
        output_file = tmp_path / "alerts.csv"
        result = runner.invoke(app, ["insights", "alerts", "--list", "--export", "csv", "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Data exported to" in result.output


class TestInsightsMobileUsers:
    """Test insights mobile users commands."""

    def test_list_mobile_users_mock(self, runner, mock_insights_env):
        """Test listing mobile users in mock mode."""
        result = runner.invoke(app, ["insights", "mobile-users", "--list"])
        assert result.exit_code == 0
        assert "user-001" in result.output
        assert "jsmith@company.com" in result.output

    def test_get_mobile_user_mock(self, runner, mock_insights_env):
        """Test getting a specific mobile user in mock mode."""
        result = runner.invoke(app, ["insights", "mobile-users", "--id", "user-001"])
        assert result.exit_code == 0
        assert "user-001" in result.output
        assert "jsmith@company.com" in result.output


class TestInsightsLocations:
    """Test insights locations commands."""

    def test_list_locations_mock(self, runner, mock_insights_env):
        """Test listing locations in mock mode."""
        result = runner.invoke(app, ["insights", "locations", "--list"])
        assert result.exit_code == 0
        assert "loc-001" in result.output
        assert "New York Office" in result.output

    def test_get_location_mock(self, runner, mock_insights_env):
        """Test getting a specific location in mock mode."""
        result = runner.invoke(app, ["insights", "locations", "--id", "loc-001"])
        assert result.exit_code == 0
        assert "loc-001" in result.output
        assert "New York Office" in result.output


class TestInsightsRemoteNetworks:
    """Test insights remote networks commands."""

    def test_list_remote_networks_mock(self, runner, mock_insights_env):
        """Test listing remote networks in mock mode."""
        result = runner.invoke(app, ["insights", "remote-networks", "--list"])
        assert result.exit_code == 0
        assert "rn-001" in result.output
        assert "Branch Office Network" in result.output

    def test_get_remote_network_mock(self, runner, mock_insights_env):
        """Test getting a specific remote network in mock mode."""
        result = runner.invoke(app, ["insights", "remote-networks", "--id", "rn-001"])
        assert result.exit_code == 0
        assert "rn-001" in result.output
        assert "Branch Office Network" in result.output

    def test_list_remote_networks_with_metrics_mock(self, runner, mock_insights_env):
        """Test listing remote networks with metrics in mock mode."""
        result = runner.invoke(app, ["insights", "remote-networks", "--list", "--metrics"])
        assert result.exit_code == 0
        assert "latency" in result.output
        assert "throughput" in result.output


class TestInsightsServiceConnections:
    """Test insights service connections commands."""

    def test_list_service_connections_mock(self, runner, mock_insights_env):
        """Test listing service connections in mock mode."""
        result = runner.invoke(app, ["insights", "service-connections", "--list"])
        assert result.exit_code == 0
        assert "sc-001" in result.output
        assert "AWS Direct Connect" in result.output

    def test_get_service_connection_mock(self, runner, mock_insights_env):
        """Test getting a specific service connection in mock mode."""
        result = runner.invoke(app, ["insights", "service-connections", "--id", "sc-001"])
        assert result.exit_code == 0
        assert "sc-001" in result.output
        assert "AWS Direct Connect" in result.output


class TestInsightsTunnels:
    """Test insights tunnels commands."""

    def test_list_tunnels_mock(self, runner, mock_insights_env):
        """Test listing tunnels in mock mode."""
        result = runner.invoke(app, ["insights", "tunnels", "--list"])
        assert result.exit_code == 0
        assert "tunnel-001" in result.output
        assert "IPSec-Branch-01" in result.output

    def test_get_tunnel_mock(self, runner, mock_insights_env):
        """Test getting a specific tunnel in mock mode."""
        result = runner.invoke(app, ["insights", "tunnels", "--id", "tunnel-001"])
        assert result.exit_code == 0
        assert "tunnel-001" in result.output
        assert "IPSec-Branch-01" in result.output

    def test_list_tunnels_with_stats_mock(self, runner, mock_insights_env):
        """Test listing tunnels with statistics in mock mode."""
        result = runner.invoke(app, ["insights", "tunnels", "--list", "--stats"])
        assert result.exit_code == 0
        assert "bytes_sent" in result.output
        assert "packets_sent" in result.output
        assert "latency" in result.output