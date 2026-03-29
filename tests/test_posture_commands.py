"""Tests for the posture commands module."""

import pytest
from pydantic import ValidationError

from scm_cli.utils.validators import BpaAssessRequest, BpaStatusResponse, PostureExport


class TestPostureExportValidator:
    """Test the PostureExport validator."""

    def test_valid_export(self):
        """Test valid export parameters."""
        export = PostureExport(
            host="10.0.0.1",
            user="automation",
            output="config.xml",
            category="running",
        )
        assert export.host == "10.0.0.1"
        assert export.user == "automation"
        assert export.category == "running"

    def test_invalid_category(self):
        """Test that invalid category is rejected."""
        with pytest.raises(ValidationError):
            PostureExport(
                host="10.0.0.1",
                user="automation",
                output="config.xml",
                category="invalid",
            )

    def test_default_category(self):
        """Test default category is running."""
        export = PostureExport(
            host="10.0.0.1",
            user="automation",
            output="config.xml",
        )
        assert export.category == "running"


class TestBpaAssessRequestValidator:
    """Test the BpaAssessRequest validator."""

    def test_valid_assess(self):
        """Test valid assess parameters."""
        assess = BpaAssessRequest(
            config="config.xml",
            delete_after_processing=True,
            output="report.json",
            timeout=300,
        )
        assert assess.config == "config.xml"
        assert assess.delete_after_processing is True
        assert assess.timeout == 300

    def test_default_timeout(self):
        """Test default timeout is 300."""
        assess = BpaAssessRequest(
            config="config.xml",
            output="report.json",
        )
        assert assess.timeout == 300

    def test_default_delete_after(self):
        """Test default delete_after_processing is True."""
        assess = BpaAssessRequest(
            config="config.xml",
            output="report.json",
        )
        assert assess.delete_after_processing is True


class TestBpaStatusResponseValidator:
    """Test the BpaStatusResponse validator."""

    def test_completed_status(self):
        """Test completed status with report_url."""
        response = BpaStatusResponse(
            status="COMPLETED",
            result={"report_url": "https://example.com/report.json"},
        )
        assert response.status == "COMPLETED"
        assert response.result["report_url"] == "https://example.com/report.json"

    def test_in_progress_status(self):
        """Test in-progress status without result."""
        response = BpaStatusResponse(
            status="IN_PROGRESS",
            message="Analyzing security rules...",
        )
        assert response.status == "IN_PROGRESS"
        assert response.result is None

    def test_invalid_status(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError):
            BpaStatusResponse(status="UNKNOWN")


from unittest.mock import MagicMock, patch


class TestSCMClientPostureMethods:
    """Test posture-related methods on SCMClient."""

    def test_generate_api_key(self, monkeypatch):
        """Test XML API key generation from username/password."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<response><result><key>LUFRPT1234</key></result></response>"

        with patch("scm_cli.utils.sdk_client.requests.get", return_value=mock_response) as mock_get:
            key = scm_client.generate_panos_api_key(
                host="10.0.0.1",
                user="automation",
                password="secret",
            )
            assert key == "LUFRPT1234"
            mock_get.assert_called_once()

    def test_export_config(self, monkeypatch):
        """Test config export via XML API."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<config><devices></devices></config>"

        with patch("scm_cli.utils.sdk_client.requests.get", return_value=mock_response):
            config_xml = scm_client.export_panos_config(
                host="10.0.0.1",
                api_key="LUFRPT1234",
                category="running",
            )
            assert "<config>" in config_xml

    def test_initiate_bpa_upload(self, monkeypatch):
        """Test BPA upload initiation."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "upload_url": "https://storage.googleapis.com/presigned-url",
        }

        with patch.object(scm_client, "_get_scm_session", return_value=MagicMock()) as mock_session:
            mock_session.return_value.post.return_value = mock_response
            result = scm_client.initiate_bpa_upload(delete_after_processing=True)
            assert result["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
            assert "upload_url" in result

    def test_upload_config_to_presigned_url(self, monkeypatch):
        """Test config upload to presigned GCS URL."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("scm_cli.utils.sdk_client.requests.put", return_value=mock_response):
            scm_client.upload_config_to_presigned_url(
                upload_url="https://storage.googleapis.com/presigned-url",
                config_data=b"<config></config>",
            )

    def test_get_bpa_status_completed(self, monkeypatch):
        """Test BPA status check when completed."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "COMPLETED",
            "result": {"report_url": "https://example.com/report.json"},
        }

        with patch.object(scm_client, "_get_scm_session", return_value=MagicMock()) as mock_session:
            mock_session.return_value.get.return_value = mock_response
            result = scm_client.get_bpa_status(
                task_id="550e8400-e29b-41d4-a716-446655440000",
            )
            assert result["status"] == "COMPLETED"
            assert "report_url" in result["result"]
