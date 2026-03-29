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
