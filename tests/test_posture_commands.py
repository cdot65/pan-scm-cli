"""Tests for the posture commands module."""

import gzip
import json
from unittest.mock import MagicMock, patch

import pytest
import typer
from pydantic import ValidationError

from scm_cli.commands.posture import assess_config, export_config, posture_app, score_report
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

    def test_upload_config_to_presigned_url(self):
        """Test config upload sends gzip-compressed data with correct headers."""
        from scm_cli.utils.sdk_client import scm_client

        mock_response = MagicMock()
        mock_response.status_code = 200

        captured = {}

        def capture_put(url, data=None, headers=None):
            captured["url"] = url
            captured["data"] = data
            captured["headers"] = headers
            return mock_response

        with patch("scm_cli.utils.sdk_client.requests.put", side_effect=capture_put):
            scm_client.upload_config_to_presigned_url(
                upload_url="https://storage.googleapis.com/presigned-url",
                config_data=b"<config></config>",
            )

        assert captured["headers"]["Content-Type"] == "plain/text"
        assert captured["headers"]["Content-Encoding"] == "gzip"
        # Verify the data is valid gzip
        decompressed = gzip.decompress(captured["data"])
        assert decompressed == b"<config></config>"

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


class TestPostureCommands:
    """Test the posture command app exists."""

    def test_posture_app_exists(self):
        """Test that the posture app exists."""
        assert posture_app


class TestPostureExportCommand:
    """Test the posture export command."""

    def test_export_success(self, runner, monkeypatch, tmp_path):
        """Test successful config export."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(
            scm_client,
            "generate_panos_api_key",
            lambda **kwargs: "LUFRPT1234",
        )
        monkeypatch.setattr(
            scm_client,
            "export_panos_config",
            lambda **kwargs: "<config><devices></devices></config>",
        )
        monkeypatch.setenv("PANOS_PASSWORD", "secret")

        output_file = tmp_path / "config.xml"

        test_app = typer.Typer()
        test_app.command()(export_config)

        result = runner.invoke(
            test_app,
            [
                "--host", "10.0.0.1",
                "--user", "automation",
                "--output", str(output_file),
                "--category", "running",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "<config>" in output_file.read_text()

    def test_export_missing_password(self, runner, monkeypatch, tmp_path):
        """Test export fails without password."""
        monkeypatch.delenv("PANOS_PASSWORD", raising=False)

        test_app = typer.Typer()
        test_app.command()(export_config)

        result = runner.invoke(
            test_app,
            [
                "--host", "10.0.0.1",
                "--user", "automation",
                "--output", str(tmp_path / "config.xml"),
            ],
        )

        assert result.exit_code == 1


class TestPostureAssessCommand:
    """Test the posture assess command."""

    FAKE_REPORT = {
        "information": {"bpa_version": "26.3.6"},
        "best_practices": {
            "device": {
                "device_setup_session": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 121,
                                "check_name": "Accelerated Aging should be enabled",
                                "check_type": "Informational",
                                "check_message": None,
                                "check_passed": True,
                                "uuid": None,
                                "remediation": None,
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
            },
        },
        "adoption": {},
        "adoption_summary": {},
    }

    def test_assess_success_json(self, monkeypatch, tmp_path):
        """Test successful BPA assessment with JSON output."""
        from typer.testing import CliRunner as _CliRunner

        from scm_cli.utils.sdk_client import scm_client

        config_file = tmp_path / "config.xml"
        config_file.write_text("<config><devices></devices></config>")
        report_file = tmp_path / "report.json"

        monkeypatch.setattr(
            scm_client,
            "initiate_bpa_upload",
            lambda **kwargs: {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "upload_url": "https://storage.googleapis.com/presigned-url",
            },
        )
        monkeypatch.setattr(
            scm_client,
            "upload_config_to_presigned_url",
            lambda **kwargs: None,
        )
        monkeypatch.setattr(
            scm_client,
            "get_bpa_status",
            lambda **kwargs: {
                "status": "COMPLETED",
                "result": {"report_url": "https://example.com/report.json"},
            },
        )
        monkeypatch.setattr(
            scm_client,
            "fetch_bpa_report",
            lambda **kwargs: self.FAKE_REPORT,
        )

        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = _CliRunner(mix_stderr=False).invoke(
            test_app,
            [
                "--config", str(config_file),
                "--output", str(report_file),
                "--timeout", "60",
                "--delete-after",
                "--format", "json",
            ],
        )

        assert result.exit_code == 0
        # Raw report saved to file
        assert report_file.exists()
        saved = json.loads(report_file.read_text())
        assert "best_practices" in saved
        # Formatted output on stdout
        stdout_data = json.loads(result.stdout)
        assert "score" in stdout_data
        assert stdout_data["total"] == 1

    def test_assess_success_markdown(self, monkeypatch, tmp_path):
        """Test successful BPA assessment with Markdown output."""
        from typer.testing import CliRunner as _CliRunner

        from scm_cli.utils.sdk_client import scm_client

        config_file = tmp_path / "config.xml"
        config_file.write_text("<config></config>")
        report_file = tmp_path / "report.json"

        monkeypatch.setattr(
            scm_client,
            "initiate_bpa_upload",
            lambda **kwargs: {
                "task_id": "test-id",
                "upload_url": "https://storage.googleapis.com/presigned-url",
            },
        )
        monkeypatch.setattr(scm_client, "upload_config_to_presigned_url", lambda **kwargs: None)
        monkeypatch.setattr(
            scm_client,
            "get_bpa_status",
            lambda **kwargs: {
                "status": "COMPLETED",
                "result": {"report_url": "https://example.com/report.json"},
            },
        )
        monkeypatch.setattr(scm_client, "fetch_bpa_report", lambda **kwargs: self.FAKE_REPORT)

        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = _CliRunner(mix_stderr=False).invoke(
            test_app,
            [
                "--config", str(config_file),
                "--output", str(report_file),
                "--timeout", "60",
                "--delete-after",
                "--format", "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "## BPA Score:" in result.stdout

    def test_assess_config_not_found(self, runner, tmp_path):
        """Test assess with missing config file."""
        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = runner.invoke(
            test_app,
            [
                "--config", str(tmp_path / "nonexistent.xml"),
                "--output", str(tmp_path / "report.json"),
                "--format", "json",
            ],
        )

        assert result.exit_code == 1

    def test_assess_timeout(self, runner, monkeypatch, tmp_path):
        """Test assess times out correctly."""
        import time as time_module

        from scm_cli.utils.sdk_client import scm_client

        config_file = tmp_path / "config.xml"
        config_file.write_text("<config></config>")

        monkeypatch.setattr(
            scm_client,
            "initiate_bpa_upload",
            lambda **kwargs: {
                "task_id": "test-task-id",
                "upload_url": "https://storage.googleapis.com/presigned-url",
            },
        )
        monkeypatch.setattr(scm_client, "upload_config_to_presigned_url", lambda **kwargs: None)
        monkeypatch.setattr(
            scm_client,
            "get_bpa_status",
            lambda **kwargs: {"status": "IN_PROGRESS", "message": "Still processing..."},
        )

        call_count = {"value": 0}

        def mock_time():
            call_count["value"] += 1
            if call_count["value"] == 1:
                return 1000.0
            return 1400.0

        monkeypatch.setattr(time_module, "time", mock_time)
        monkeypatch.setattr(time_module, "sleep", lambda s: None)

        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = runner.invoke(
            test_app,
            [
                "--config", str(config_file),
                "--output", str(tmp_path / "report.json"),
                "--timeout", "300",
                "--format", "json",
            ],
        )

        assert result.exit_code == 1


class TestPostureScoreCommand:
    """Test the posture score command with real BPA schema."""

    SAMPLE_REPORT = {
        "information": {"bpa_version": "26.3.6"},
        "best_practices": {
            "device": {
                "device_setup_session": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 121,
                                "check_name": "Accelerated Aging should be enabled",
                                "check_type": "Informational",
                                "check_message": None,
                                "check_passed": True,
                                "uuid": None,
                                "remediation": None,
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
            },
            "policies": {
                "security_rulebase": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 10,
                                "check_name": "Security rules should use App-ID",
                                "check_type": "Critical",
                                "check_message": "Use application-based rules",
                                "check_passed": False,
                                "uuid": None,
                                "remediation": "Convert to App-ID rules",
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
            },
        },
        "adoption": {},
        "adoption_summary": {},
    }

    def test_score_json_output(self, runner, tmp_path):
        """Test score with JSON output format."""
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(self.SAMPLE_REPORT))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "all", "--format", "json"],
        )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["score"] == 50.0
        assert output["passed"] == 1
        assert output["failed"] == 1
        assert output["total"] == 2

    def test_score_markdown_output(self, runner, tmp_path):
        """Test score with Markdown output format."""
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(self.SAMPLE_REPORT))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "all", "--format", "markdown"],
        )

        assert result.exit_code == 0
        assert "## BPA Score: 50.0% (1/2)" in result.stdout
        assert "### Failing Checks (1)" in result.stdout
        assert "### Passing Checks (1)" in result.stdout

    def test_score_csv_output(self, runner, tmp_path):
        """Test score with CSV output format."""
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(self.SAMPLE_REPORT))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "all", "--format", "csv"],
        )

        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "check_id,check_name,check_type,check_passed,category,subcategory,check_message,remediation"
        assert len(lines) == 3  # header + 2 checks

    def test_score_scope_filter(self, runner, tmp_path):
        """Test score filtered to policies scope only."""
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(self.SAMPLE_REPORT))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "policies", "--format", "json"],
        )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["total"] == 1
        assert output["score"] == 0.0

    def test_score_report_not_found(self, runner, tmp_path):
        """Test score with missing report file."""
        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(tmp_path / "nonexistent.json"), "--format", "json"],
        )

        assert result.exit_code == 1

    def test_score_empty_scope(self, runner, tmp_path):
        """Test score with scope that has no checks."""
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps(self.SAMPLE_REPORT))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "network", "--format", "json"],
        )

        assert result.exit_code == 1


class TestBpaReportParser:
    """Test the BPA report parsing and flattening logic."""

    SAMPLE_REPORT = {
        "information": {
            "bpa_version": "26.3.6",
            "platform": "ngfw",
        },
        "best_practices": {
            "device": {
                "device_setup_session": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 121,
                                "check_name": "Accelerated Aging should be enabled",
                                "check_type": "Informational",
                                "check_message": None,
                                "check_passed": True,
                                "uuid": None,
                                "remediation": None,
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                            {
                                "check_id": 214,
                                "check_name": "TCP out-of-order queue should be disabled",
                                "check_type": "Critical",
                                "check_message": None,
                                "check_passed": True,
                                "uuid": None,
                                "remediation": None,
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
                "device_setup_secure_communication": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 223,
                                "check_name": "Client communication with secure custom certificates",
                                "check_type": "Warning",
                                "check_message": "Configure Local or SCEP Certificate Type",
                                "check_passed": False,
                                "uuid": None,
                                "remediation": "Enable secure communication",
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
            },
            "policies": {
                "security_rulebase": [
                    {
                        "configuration": {},
                        "warnings": [
                            {
                                "check_id": 10,
                                "check_name": "Security rules should use App-ID",
                                "check_type": "Critical",
                                "check_message": "Use application-based rules",
                                "check_passed": False,
                                "uuid": None,
                                "remediation": "Convert to App-ID rules",
                                "user_excluded": False,
                                "check_excluded": False,
                            },
                        ],
                        "notes": [],
                    }
                ],
            },
        },
        "adoption": {},
        "adoption_summary": {},
    }

    def test_flatten_all_checks(self):
        """Test flattening all checks from nested structure."""
        from scm_cli.commands.posture import flatten_bpa_checks

        checks = flatten_bpa_checks(self.SAMPLE_REPORT)
        assert len(checks) == 4

    def test_flatten_preserves_category(self):
        """Test that category and subcategory are attached."""
        from scm_cli.commands.posture import flatten_bpa_checks

        checks = flatten_bpa_checks(self.SAMPLE_REPORT)
        device_checks = [c for c in checks if c["category"] == "device"]
        policy_checks = [c for c in checks if c["category"] == "policies"]
        assert len(device_checks) == 3
        assert len(policy_checks) == 1

    def test_flatten_preserves_fields(self):
        """Test that all check fields are preserved."""
        from scm_cli.commands.posture import flatten_bpa_checks

        checks = flatten_bpa_checks(self.SAMPLE_REPORT)
        check_223 = next(c for c in checks if c["check_id"] == 223)
        assert check_223["check_name"] == "Client communication with secure custom certificates"
        assert check_223["check_type"] == "Warning"
        assert check_223["check_passed"] is False
        assert check_223["category"] == "device"
        assert check_223["subcategory"] == "device_setup_secure_communication"
        assert check_223["check_message"] == "Configure Local or SCEP Certificate Type"
        assert check_223["remediation"] == "Enable secure communication"

    def test_flatten_filter_by_scope(self):
        """Test filtering checks by scope (category)."""
        from scm_cli.commands.posture import flatten_bpa_checks

        checks = flatten_bpa_checks(self.SAMPLE_REPORT, scope="policies")
        assert len(checks) == 1
        assert checks[0]["check_id"] == 10

    def test_flatten_scope_all(self):
        """Test scope=all returns everything."""
        from scm_cli.commands.posture import flatten_bpa_checks

        checks = flatten_bpa_checks(self.SAMPLE_REPORT, scope="all")
        assert len(checks) == 4

    def test_flatten_empty_best_practices(self):
        """Test with empty best_practices."""
        from scm_cli.commands.posture import flatten_bpa_checks

        report = {"best_practices": {}, "information": {}}
        checks = flatten_bpa_checks(report)
        assert checks == []


class TestBpaFormatters:
    """Test BPA output formatting functions."""

    SAMPLE_CHECKS = [
        {
            "category": "device",
            "subcategory": "device_setup_session",
            "check_id": 121,
            "check_name": "Accelerated Aging should be enabled",
            "check_type": "Informational",
            "check_message": None,
            "check_passed": True,
            "remediation": None,
        },
        {
            "category": "device",
            "subcategory": "device_setup_session",
            "check_id": 214,
            "check_name": "TCP out-of-order queue should be disabled",
            "check_type": "Critical",
            "check_message": None,
            "check_passed": True,
            "remediation": None,
        },
        {
            "category": "device",
            "subcategory": "device_setup_secure_communication",
            "check_id": 223,
            "check_name": "Client communication with secure custom certificates",
            "check_type": "Warning",
            "check_message": "Configure Local or SCEP Certificate Type",
            "check_passed": False,
            "remediation": "Enable secure communication",
        },
        {
            "category": "policies",
            "subcategory": "security_rulebase",
            "check_id": 10,
            "check_name": "Security rules should use App-ID",
            "check_type": "Critical",
            "check_message": "Use application-based rules",
            "check_passed": False,
            "remediation": "Convert to App-ID rules",
        },
    ]

    def test_format_json(self):
        """Test JSON output contains score and all checks."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output(self.SAMPLE_CHECKS, fmt="json")
        data = json.loads(output)
        assert data["score"] == 50.0
        assert data["passed"] == 2
        assert data["failed"] == 2
        assert data["total"] == 4
        assert len(data["checks"]) == 4

    def test_format_json_by_type(self):
        """Test JSON output includes by_type breakdown."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output(self.SAMPLE_CHECKS, fmt="json")
        data = json.loads(output)
        assert data["by_type"]["Critical"]["total"] == 2
        assert data["by_type"]["Critical"]["passed"] == 1
        assert data["by_type"]["Critical"]["failed"] == 1
        assert data["by_type"]["Warning"]["total"] == 1
        assert data["by_type"]["Informational"]["total"] == 1

    def test_format_markdown_has_sections(self):
        """Test Markdown output has all required sections."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output(self.SAMPLE_CHECKS, fmt="markdown")
        assert "## BPA Score: 50.0% (2/4)" in output
        assert "### Summary by Severity" in output
        assert "### Failing Checks (2)" in output
        assert "### Passing Checks (2)" in output

    def test_format_markdown_tables(self):
        """Test Markdown output contains table rows."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output(self.SAMPLE_CHECKS, fmt="markdown")
        assert "| Critical" in output
        assert "| Warning" in output
        assert "| Informational" in output
        # Failing check present
        assert "| 223 |" in output
        # Passing check present
        assert "| 121 |" in output

    def test_format_csv(self):
        """Test CSV output has header and data rows."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output(self.SAMPLE_CHECKS, fmt="csv")
        lines = output.strip().split("\n")
        assert lines[0] == "check_id,check_name,check_type,check_passed,category,subcategory,check_message,remediation"
        assert len(lines) == 5  # header + 4 checks

    def test_format_csv_quoting(self):
        """Test CSV properly quotes fields with commas."""
        from scm_cli.commands.posture import format_bpa_output

        checks = [
            {
                "category": "device",
                "subcategory": "test",
                "check_id": 1,
                "check_name": "Check with, comma",
                "check_type": "Warning",
                "check_message": "Message with, comma",
                "check_passed": False,
                "remediation": None,
            },
        ]
        output = format_bpa_output(checks, fmt="csv")
        lines = output.strip().split("\n")
        assert len(lines) == 2
        # csv module handles quoting — just verify it parses back correctly
        import csv
        import io
        reader = csv.DictReader(io.StringIO(output))
        row = next(reader)
        assert row["check_name"] == "Check with, comma"

    def test_format_empty_checks(self):
        """Test formatting with no checks."""
        from scm_cli.commands.posture import format_bpa_output

        output = format_bpa_output([], fmt="json")
        data = json.loads(output)
        assert data["score"] == 0.0
        assert data["total"] == 0


class TestPostureRegistration:
    """Test posture command is registered in main app."""

    def test_posture_registered(self, runner):
        """Test that posture is registered as a top-level command."""
        from scm_cli.main import app

        result = runner.invoke(app, ["posture", "--help"])
        assert result.exit_code == 0
        assert "assess" in result.output
