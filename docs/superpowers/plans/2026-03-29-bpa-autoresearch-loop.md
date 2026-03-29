# BPA Autoresearch Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `posture` command group to pan-scm-cli that exports PAN-OS config, uploads to BPA API for scoring, and supports an autoresearch-style agentic hardening loop.

**Architecture:** Three CLI subcommands (`export`, `assess`, `score`) under `scm posture`. `export` uses PAN-OS XML API for config retrieval, `assess` orchestrates the 3-step BPA Config Upload API flow, `score` parses JSON reports into a single numeric metric. A `program.md` at repo root defines the agentic loop instructions.

**Tech Stack:** Python 3.10+, Typer, Pydantic v2, requests (for XML API + presigned URL upload), existing SCM OAuth2 auth

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `src/scm_cli/commands/posture.py` | Create | All three posture subcommands |
| `src/scm_cli/utils/validators.py` | Modify | Add BPA Pydantic models |
| `src/scm_cli/utils/sdk_client.py` | Modify | Add BPA methods (raw HTTP) |
| `src/scm_cli/main.py` | Modify | Register posture command group |
| `tests/test_posture_commands.py` | Create | Unit tests for all posture commands |
| `.gitignore` | Modify | Add config.xml, report.json, results.tsv |
| `posture.yaml` | Move | OpenAPI spec from autoresearch repo |
| `program.md` | Create | Agentic loop instructions |

---

### Task 1: Pydantic Validators for BPA Models

**Files:**
- Modify: `src/scm_cli/utils/validators.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for BPA validators**

Create `tests/test_posture_commands.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py -v`
Expected: FAIL with `ImportError: cannot import name 'BpaAssessRequest'`

- [ ] **Step 3: Add BPA validator models to validators.py**

Append to the end of `src/scm_cli/utils/validators.py`, before any final closing content. Add the following after the last existing validator class, using the same 191-char separator pattern:

```python
# ===============================================================================================================================================================================================
# POSTURE / BPA VALIDATORS
# ===============================================================================================================================================================================================


class PostureExport(BaseModel):
    """Validator for posture export command parameters.

    Attributes:
        host: PAN-OS firewall hostname or IP address.
        user: Admin username for XML API authentication.
        password: Admin password (optional, can come from env).
        output: Output file path for exported config.
        category: Config category to export (running or candidate).

    """

    host: str = Field(..., min_length=1, description="Firewall hostname or IP")
    user: str = Field(..., min_length=1, description="Admin username")
    password: str | None = Field(None, description="Admin password")
    output: str = Field("config.xml", description="Output file path")
    category: str = Field("running", description="Config category")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is running or candidate."""
        allowed = {"running", "candidate"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}, got '{v}'")
        return v


class BpaAssessRequest(BaseModel):
    """Validator for BPA assess command parameters.

    Attributes:
        config: Path to the config file to assess.
        delete_after_processing: Delete config from cloud after assessment.
        output: Output file path for BPA report JSON.
        timeout: Maximum seconds to wait for BPA processing.

    """

    config: str = Field(..., min_length=1, description="Config file path")
    delete_after_processing: bool = Field(True, description="Delete config after processing")
    output: str = Field("report.json", description="Output file path for report")
    timeout: int = Field(300, ge=30, le=600, description="Max wait seconds")


class BpaStatusResponse(BaseModel):
    """Validator for BPA processing status API response.

    Attributes:
        status: Processing status (QUEUED, IN_PROGRESS, COMPLETED, FAILED).
        message: Optional status message.
        result: Result object populated when status is COMPLETED.

    """

    status: str = Field(..., description="Processing status")
    message: str | None = Field(None, description="Status message")
    result: dict | None = Field(None, description="Result when completed")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is a known BPA status."""
        allowed = {"QUEUED", "IN_PROGRESS", "COMPLETED", "FAILED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got '{v}'")
        return v
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/utils/validators.py tests/test_posture_commands.py
git commit -m "feat(posture): add Pydantic validators for BPA models"
```

---

### Task 2: SDK Client BPA Methods

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for SDK client BPA methods**

Append to `tests/test_posture_commands.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestSCMClientPostureMethods -v`
Expected: FAIL with `AttributeError: 'SCMClient' object has no attribute 'generate_panos_api_key'`

- [ ] **Step 3: Add imports and BPA methods to sdk_client.py**

First, add `import requests` and `import xml.etree.ElementTree as ET` to the imports at the top of `src/scm_cli/utils/sdk_client.py` (after the existing imports around line 8-20).

Then add the following methods inside the `SCMClient` class, after the last existing method, using the 191-char separator pattern:

```python
    # ======================================================================================================================================================================================
    # POSTURE / BPA METHODS
    # ======================================================================================================================================================================================

    def generate_panos_api_key(
        self,
        host: str,
        user: str,
        password: str,
    ) -> str:
        """Generate an API key from PAN-OS XML API using username/password.

        Args:
            host: Firewall hostname or IP address.
            user: Admin username.
            password: Admin password.

        Returns:
            str: The generated API key.

        """
        self.logger.info(f"Generating API key for {user}@{host}")
        url = f"https://{host}/api/?type=keygen&user={user}&password={password}"
        response = requests.get(url, verify=False)  # noqa: S501
        response.raise_for_status()

        root = ET.fromstring(response.text)
        key_element = root.find(".//key")
        if key_element is None or key_element.text is None:
            raise ValueError(f"Failed to generate API key: {response.text}")

        return key_element.text

    def export_panos_config(
        self,
        host: str,
        api_key: str,
        category: str = "running",
    ) -> str:
        """Export configuration from PAN-OS firewall via XML API.

        Args:
            host: Firewall hostname or IP address.
            api_key: PAN-OS API key.
            category: Config category ('running' or 'candidate').

        Returns:
            str: The configuration XML as a string.

        """
        self.logger.info(f"Exporting {category} config from {host}")
        url = f"https://{host}/api/?type=export&category=configuration&key={api_key}"
        response = requests.get(url, verify=False)  # noqa: S501
        response.raise_for_status()
        return response.text

    def _get_scm_session(self) -> Any:
        """Get an authenticated requests session for SCM API calls.

        Returns:
            Any: Authenticated session from the SCM SDK client.

        """
        if not self.client:
            raise RuntimeError("SCM client not initialized — check credentials")
        return self.client.session

    def initiate_bpa_upload(
        self,
        delete_after_processing: bool = True,
    ) -> dict[str, Any]:
        """Initiate a BPA config file upload.

        Args:
            delete_after_processing: Delete config from cloud after assessment.

        Returns:
            dict[str, Any]: Response with task_id and upload_url.

        """
        self.logger.info("Initiating BPA config upload")
        session = self._get_scm_session()
        url = "https://api.strata.paloaltonetworks.com/posture/checks/v1/reports/config-file-upload"
        response = session.post(
            url,
            json={"delete_after_processing": delete_after_processing},
        )
        response.raise_for_status()
        return response.json()

    def upload_config_to_presigned_url(
        self,
        upload_url: str,
        config_data: bytes,
    ) -> None:
        """Upload config file to a presigned GCS URL.

        Args:
            upload_url: Presigned GCS URL from initiate_bpa_upload.
            config_data: Raw config file bytes.

        """
        self.logger.info("Uploading config to presigned URL")
        response = requests.put(
            upload_url,
            data=config_data,
            headers={"Content-Type": "application/octet-stream"},
        )
        response.raise_for_status()

    def get_bpa_status(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """Get BPA processing status for a task.

        Args:
            task_id: The task ID from initiate_bpa_upload.

        Returns:
            dict[str, Any]: Status response with status, message, and result fields.

        """
        self.logger.info(f"Checking BPA status for task {task_id}")
        session = self._get_scm_session()
        url = f"https://api.strata.paloaltonetworks.com/posture/checks/v1/reports/{task_id}/bpa-result"
        response = session.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_bpa_report(
        self,
        report_url: str,
    ) -> dict[str, Any]:
        """Fetch the completed BPA report from its URL.

        Args:
            report_url: URL to the completed BPA report.

        Returns:
            dict[str, Any]: The full BPA report as a dict.

        """
        self.logger.info(f"Fetching BPA report from {report_url}")
        session = self._get_scm_session()
        response = session.get(report_url)
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/utils/sdk_client.py tests/test_posture_commands.py
git commit -m "feat(posture): add BPA and PAN-OS XML API methods to SDK client"
```

---

### Task 3: `posture export` Command

**Files:**
- Create: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing test for export command**

Append to `tests/test_posture_commands.py`:

```python
from scm_cli.commands.posture import export_config, posture_app


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureExportCommand -v`
Expected: FAIL with `ImportError: cannot import name 'export_config'`

- [ ] **Step 3: Create posture.py command module**

Create `src/scm_cli/commands/posture.py`:

```python
"""Posture module commands for scm.

This module implements commands for PAN-OS firewall Best Practice Assessment (BPA),
including config export, BPA assessment upload, and report scoring.
"""

import json
import os
import time
from pathlib import Path

import typer

from ..utils.decorators import handle_command_errors
from ..utils.sdk_client import scm_client
from ..utils.validators import BpaAssessRequest, BpaStatusResponse, PostureExport

# ===============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ===============================================================================================================================================================================================

posture_app = typer.Typer(help="Firewall posture assessment and BPA scoring")

# ===============================================================================================================================================================================================
# COMMAND OPTIONS
# ===============================================================================================================================================================================================

HOST_OPTION = typer.Option(
    None,
    "--host",
    help="PAN-OS firewall hostname or IP address",
    envvar="PANOS_HOST",
)
USER_OPTION = typer.Option(
    "automation",
    "--user",
    help="Admin username for XML API authentication",
    envvar="PANOS_USER",
)
PASSWORD_OPTION = typer.Option(
    None,
    "--password",
    help="Admin password (or set PANOS_PASSWORD env var)",
    envvar="PANOS_PASSWORD",
)
OUTPUT_OPTION = typer.Option(
    "config.xml",
    "--output",
    help="Output file path",
)
CATEGORY_OPTION = typer.Option(
    "running",
    "--category",
    help="Config category to export (running or candidate)",
)
CONFIG_OPTION = typer.Option(
    ...,
    "--config",
    help="Path to config file to assess",
)
DELETE_AFTER_OPTION = typer.Option(
    True,
    "--delete-after/--keep",
    help="Delete config from cloud after assessment",
)
TIMEOUT_OPTION = typer.Option(
    300,
    "--timeout",
    help="Max seconds to wait for BPA processing",
)
REPORT_OPTION = typer.Option(
    ...,
    "--report",
    help="Path to BPA report JSON file",
)
SCOPE_OPTION = typer.Option(
    "all",
    "--scope",
    help="BPA check scope (all, security, decryption, threat)",
)
FORMAT_OPTION = typer.Option(
    "plain",
    "--format",
    help="Output format (plain or json)",
)

# ===============================================================================================================================================================================================
# EXPORT COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("export")
@handle_command_errors("exporting config")
def export_config(
    host: str = HOST_OPTION,
    user: str = USER_OPTION,
    password: str | None = PASSWORD_OPTION,
    output: str = OUTPUT_OPTION,
    category: str = CATEGORY_OPTION,
):
    r"""Export running or candidate config from a PAN-OS firewall.

    Example:
    -------
        scm posture export \
        --host 10.0.0.1 \
        --user automation \
        --output config.xml \
        --category running

    """
    if not password:
        password = os.environ.get("PANOS_PASSWORD")
    if not password:
        typer.echo("Error: password required via --password or PANOS_PASSWORD env var", err=True)
        raise typer.Exit(code=1)

    if not host:
        typer.echo("Error: --host is required or set PANOS_HOST env var", err=True)
        raise typer.Exit(code=1)

    # Validate inputs
    export_params = PostureExport(
        host=host,
        user=user,
        password=password,
        output=output,
        category=category,
    )

    # Generate API key
    api_key = scm_client.generate_panos_api_key(
        host=export_params.host,
        user=export_params.user,
        password=export_params.password,
    )
    typer.echo(f"Generated API key for {export_params.user}@{export_params.host}", err=True)

    # Export config
    config_xml = scm_client.export_panos_config(
        host=export_params.host,
        api_key=api_key,
        category=export_params.category,
    )

    # Write to file
    output_path = Path(export_params.output)
    output_path.write_text(config_xml)
    typer.echo(f"Exported {export_params.category} config to {output_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureExportCommand -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): add export command for PAN-OS config retrieval"
```

---

### Task 4: `posture assess` Command

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for assess command**

Append to `tests/test_posture_commands.py`:

```python
from scm_cli.commands.posture import assess_config


class TestPostureAssessCommand:
    """Test the posture assess command."""

    def test_assess_success(self, runner, monkeypatch, tmp_path):
        """Test successful BPA assessment."""
        from scm_cli.utils.sdk_client import scm_client

        # Create a config file
        config_file = tmp_path / "config.xml"
        config_file.write_text("<config><devices></devices></config>")

        report_file = tmp_path / "report.json"
        fake_report = {"checks": [{"name": "test", "status": "PASS"}]}

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
            lambda **kwargs: fake_report,
        )

        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = runner.invoke(
            test_app,
            [
                "--config", str(config_file),
                "--output", str(report_file),
                "--timeout", "60",
                "--delete-after",
            ],
        )

        assert result.exit_code == 0
        assert report_file.exists()
        report_data = json.loads(report_file.read_text())
        assert "checks" in report_data

    def test_assess_config_not_found(self, runner, tmp_path):
        """Test assess with missing config file."""
        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = runner.invoke(
            test_app,
            [
                "--config", str(tmp_path / "nonexistent.xml"),
                "--output", str(tmp_path / "report.json"),
            ],
        )

        assert result.exit_code == 1

    def test_assess_timeout(self, runner, monkeypatch, tmp_path):
        """Test assess times out correctly."""
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
        monkeypatch.setattr(
            scm_client,
            "upload_config_to_presigned_url",
            lambda **kwargs: None,
        )
        # Always return IN_PROGRESS to trigger timeout
        monkeypatch.setattr(
            scm_client,
            "get_bpa_status",
            lambda **kwargs: {"status": "IN_PROGRESS", "message": "Still processing..."},
        )
        # Patch time.time to simulate timeout
        call_count = {"value": 0}
        original_time = time.time

        def mock_time():
            call_count["value"] += 1
            if call_count["value"] == 1:
                return 1000.0  # start time
            return 1400.0  # past timeout

        monkeypatch.setattr(time, "time", mock_time)
        # Also patch time.sleep to avoid real delays
        monkeypatch.setattr(time, "sleep", lambda s: None)

        test_app = typer.Typer()
        test_app.command()(assess_config)

        result = runner.invoke(
            test_app,
            [
                "--config", str(config_file),
                "--output", str(tmp_path / "report.json"),
                "--timeout", "300",
            ],
        )

        assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureAssessCommand -v`
Expected: FAIL with `ImportError: cannot import name 'assess_config'`

- [ ] **Step 3: Add assess command to posture.py**

Append to `src/scm_cli/commands/posture.py`:

```python
# ===============================================================================================================================================================================================
# ASSESS COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("assess")
@handle_command_errors("assessing config")
def assess_config(
    config: str = CONFIG_OPTION,
    delete_after: bool = DELETE_AFTER_OPTION,
    output: str = typer.Option("report.json", "--output", help="Output file path for report"),
    timeout: int = TIMEOUT_OPTION,
):
    r"""Upload config to BPA API, poll for completion, and save report.

    Example:
    -------
        scm posture assess \
        --config config.xml \
        --delete-after \
        --output report.json \
        --timeout 300

    """
    # Validate config file exists
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: config file not found: {config_path}", err=True)
        raise typer.Exit(code=1)

    # Validate inputs
    assess_params = BpaAssessRequest(
        config=config,
        delete_after_processing=delete_after,
        output=output,
        timeout=timeout,
    )

    # Step 1: Initiate upload
    typer.echo("Initiating BPA upload...", err=True)
    initiate_result = scm_client.initiate_bpa_upload(
        delete_after_processing=assess_params.delete_after_processing,
    )
    task_id = initiate_result["task_id"]
    upload_url = initiate_result["upload_url"]
    typer.echo(f"Task ID: {task_id}", err=True)

    # Step 2: Upload config to presigned URL
    typer.echo("Uploading config...", err=True)
    config_data = config_path.read_bytes()
    scm_client.upload_config_to_presigned_url(
        upload_url=upload_url,
        config_data=config_data,
    )
    typer.echo("Upload complete. Waiting for processing...", err=True)

    # Step 3: Poll for completion
    start_time = time.time()
    poll_interval = 5

    while True:
        elapsed = time.time() - start_time
        if elapsed >= assess_params.timeout:
            typer.echo(f"Error: BPA processing timed out after {assess_params.timeout}s", err=True)
            raise typer.Exit(code=1)

        status_result = scm_client.get_bpa_status(task_id=task_id)
        status = BpaStatusResponse(**status_result)

        if status.status == "COMPLETED":
            break
        elif status.status == "FAILED":
            msg = status.message or "unknown error"
            typer.echo(f"Error: BPA processing failed: {msg}", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"  Status: {status.status} ({status.message or 'processing...'})", err=True)
        time.sleep(poll_interval)

    # Step 4: Fetch report
    report_url = status.result["report_url"]
    typer.echo("Fetching report...", err=True)
    report = scm_client.fetch_bpa_report(report_url=report_url)

    # Write report to file
    output_path = Path(assess_params.output)
    output_path.write_text(json.dumps(report, indent=2))
    typer.echo(f"BPA report saved to {output_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureAssessCommand -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): add assess command for BPA config upload and scoring"
```

---

### Task 5: `posture score` Command (Stub)

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for score command**

Append to `tests/test_posture_commands.py`:

```python
from scm_cli.commands.posture import score_report


class TestPostureScoreCommand:
    """Test the posture score command."""

    def test_score_plain_output(self, runner, tmp_path):
        """Test score with plain output format."""
        report_file = tmp_path / "report.json"
        report_data = {
            "checks": [
                {"name": "check-1", "status": "PASS", "category": "security"},
                {"name": "check-2", "status": "FAIL", "category": "security"},
                {"name": "check-3", "status": "PASS", "category": "security"},
                {"name": "check-4", "status": "PASS", "category": "decryption"},
            ]
        }
        report_file.write_text(json.dumps(report_data))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "all", "--format", "plain"],
        )

        assert result.exit_code == 0
        # 3 pass out of 4 = 75.0
        assert "75.0" in result.stdout

    def test_score_json_output(self, runner, tmp_path):
        """Test score with JSON output format."""
        report_file = tmp_path / "report.json"
        report_data = {
            "checks": [
                {"name": "check-1", "status": "PASS", "category": "security"},
                {"name": "check-2", "status": "FAIL", "category": "security"},
            ]
        }
        report_file.write_text(json.dumps(report_data))

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

    def test_score_security_scope(self, runner, tmp_path):
        """Test score filtered to security scope only."""
        report_file = tmp_path / "report.json"
        report_data = {
            "checks": [
                {"name": "check-1", "status": "PASS", "category": "security"},
                {"name": "check-2", "status": "FAIL", "category": "security"},
                {"name": "check-3", "status": "PASS", "category": "decryption"},
            ]
        }
        report_file.write_text(json.dumps(report_data))

        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(report_file), "--scope", "security", "--format", "json"],
        )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Only 2 security checks: 1 pass, 1 fail = 50.0
        assert output["score"] == 50.0
        assert output["total"] == 2

    def test_score_report_not_found(self, runner, tmp_path):
        """Test score with missing report file."""
        test_app = typer.Typer()
        test_app.command()(score_report)

        result = runner.invoke(
            test_app,
            ["--report", str(tmp_path / "nonexistent.json"), "--format", "plain"],
        )

        assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureScoreCommand -v`
Expected: FAIL with `ImportError: cannot import name 'score_report'`

- [ ] **Step 3: Add score command to posture.py**

Append to `src/scm_cli/commands/posture.py`:

```python
# ===============================================================================================================================================================================================
# SCORE COMMAND
# ===============================================================================================================================================================================================


@posture_app.command("score")
@handle_command_errors("scoring report")
def score_report(
    report: str = REPORT_OPTION,
    scope: str = SCOPE_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Parse BPA report JSON and return a numeric score.

    The score is the percentage of checks that passed. Use --scope to filter
    by category and --format to control output.

    Note: The report JSON schema is discovered at runtime from the first real
    BPA run. The scoring logic assumes checks have 'name', 'status', and
    'category' fields. Adjust after inspecting a real report.

    Example:
    -------
        scm posture score \
        --report report.json \
        --scope security \
        --format plain

    """
    report_path = Path(report)
    if not report_path.exists():
        typer.echo(f"Error: report file not found: {report_path}", err=True)
        raise typer.Exit(code=1)

    report_data = json.loads(report_path.read_text())

    # Extract checks — adapt field names after seeing real report schema
    checks = report_data.get("checks", [])

    # Filter by scope
    if scope != "all":
        checks = [c for c in checks if c.get("category") == scope]

    if not checks:
        typer.echo("Error: no checks found for the given scope", err=True)
        raise typer.Exit(code=1)

    # Calculate score
    total = len(checks)
    passed = sum(1 for c in checks if c.get("status") == "PASS")
    failed = total - passed
    score = round((passed / total) * 100, 1)

    # Output
    if format == "json":
        output = json.dumps({"score": score, "passed": passed, "failed": failed, "total": total})
        typer.echo(output)
    else:
        typer.echo(str(score))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureScoreCommand -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): add score command for BPA report parsing (stub schema)"
```

---

### Task 6: Register Posture Commands in main.py and Update .gitignore

**Files:**
- Modify: `src/scm_cli/main.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing test for posture registration**

Append to `tests/test_posture_commands.py`:

```python
class TestPostureRegistration:
    """Test posture command is registered in main app."""

    def test_posture_registered(self):
        """Test that posture is registered as a top-level command."""
        from scm_cli.main import app

        # Typer stores registered commands/groups
        group_names = []
        for group in app.registered_groups:
            if hasattr(group, "typer_instance") and group.typer_instance:
                group_names.append(group.name)
        assert "posture" in group_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/test_posture_commands.py::TestPostureRegistration -v`
Expected: FAIL with `AssertionError: assert 'posture' in [...]`

- [ ] **Step 3: Register posture app in main.py**

In `src/scm_cli/main.py`, add the posture import. At line 10, change:

```python
from .commands import commit, context, deployment, identity, insights, jobs, mobile_agent, network, objects, security, setup
```

to:

```python
from .commands import commit, context, deployment, identity, insights, jobs, mobile_agent, network, objects, posture, security, setup
```

Then after line 284 (`app.add_typer(jobs.app, name="jobs")`), add:

```python
app.add_typer(posture.posture_app, name="posture")
```

- [ ] **Step 4: Update .gitignore**

Append to `.gitignore`:

```
# Posture / BPA autoresearch artifacts
config.xml
report.json
results.tsv
```

- [ ] **Step 5: Run full test suite to verify nothing is broken**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add src/scm_cli/main.py .gitignore
git commit -m "feat(posture): register posture commands and update gitignore"
```

---

### Task 7: Move posture.yaml and Create program.md

**Files:**
- Move: `posture.yaml` from autoresearch repo
- Create: `program.md`

- [ ] **Step 1: Copy posture.yaml to pan-scm-cli repo**

```bash
cp /Users/cdot/development/others/autoresearch/posture.yaml /Users/cdot/development/cdot65/pan-scm-cli/posture.yaml
```

- [ ] **Step 2: Create program.md**

Create `program.md` at `/Users/cdot/development/cdot65/pan-scm-cli/program.md`:

```markdown
# BPA Hardening Loop — Agent Instructions

You are an autonomous agent improving a PAN-OS firewall configuration's Best Practice Assessment (BPA) score. You follow the autoresearch pattern: modify config, score, keep improvements, discard regressions, repeat.

## Setup

1. Branch from main: `git checkout -b autoresearch/bpa-hardening`
2. Export baseline config:
   ```bash
   scm posture export --output config.xml
   ```
3. Establish baseline score:
   ```bash
   scm posture assess --config config.xml --delete-after --output report.json
   scm posture score --report report.json --scope security --format json
   ```
4. Record baseline in results.tsv:
   ```
   timestamp	experiment	score	delta	status	notes
   ```

## Experiment Loop

Repeat indefinitely:

1. **Read** the latest `report.json` to identify failing BPA checks
2. **Choose** one failing check to address (prefer high-impact, low-risk changes)
3. **Edit** `config.xml` to fix the failing check
4. **Commit** the change: `git commit -am "experiment: <short description>"`
5. **Score** the modified config:
   ```bash
   scm posture assess --config config.xml --delete-after --output report.json
   scm posture score --report report.json --scope security --format json
   ```
6. **Decide**:
   - Score improved → log to results.tsv, continue (keep)
   - Score regressed or unchanged → `git reset --hard HEAD~1`, log failure, try different approach
7. **Repeat** — never stop, never ask human, run until interrupted

## What You May Modify (Security Policy Only)

- Add security profiles to rules missing them (antivirus, anti-spyware, vulnerability protection, URL filtering, file blocking, wildfire analysis)
- Attach log forwarding profiles to rules
- Convert port-based rules to application-based (app-id) rules
- Add decryption profiles to decryption rules
- Tighten overly permissive rules (any/any → specific applications)

## What You Must NEVER Modify

- Do not delete any security rules
- Do not modify source/destination zones on any rule
- Do not touch network, routing, interface, or zone configuration
- Do not touch GlobalProtect or certificate configuration
- Do not add new security rules — only harden existing ones
- Do not remove existing allow rules — only add profiles/restrictions to them
- Do not modify the "automation" user account or any admin access settings
- Do not modify anything outside the `<security>`, `<profiles>`, or `<log-settings>` XML sections

## Results Logging

Log every experiment to `results.tsv` (TSV format):

```
timestamp	experiment	score	delta	status	notes
2026-03-29T10:00:00	baseline	72.5	0	keep	initial export
2026-03-29T10:03:00	add-av-profile-to-rule-3	75.0	+2.5	keep	attached antivirus profile
2026-03-29T10:06:00	enable-wildfire-on-ssl	74.2	-0.8	discard	regression on decryption checks
```

## Strategy Tips

- Start with the lowest-hanging fruit: rules missing ANY security profile
- Log forwarding is often a quick win — many rules lack it
- When converting port-based rules, identify the application first from the service port
- Group related changes (e.g., add all missing antivirus profiles in one experiment)
- If a change causes regression, understand WHY before trying a different approach
- The BPA score is deterministic — same config always gives same score
```

- [ ] **Step 3: Commit**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add posture.yaml program.md
git commit -m "feat(posture): add OpenAPI spec and agentic loop instructions"
```

---

### Task 8: Run Full Test Suite and Verify

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m pytest tests/ -v`
Expected: All tests PASS including all new posture tests

- [ ] **Step 2: Run quality checks**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && make quality-basic`
Expected: No lint errors in new files

- [ ] **Step 3: Verify CLI help output**

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m scm_cli --help`
Expected: `posture` appears in the command list

Run: `cd /Users/cdot/development/cdot65/pan-scm-cli && python -m scm_cli posture --help`
Expected: `export`, `assess`, `score` subcommands listed

- [ ] **Step 4: Manual smoke test (first real BPA run)**

This is the schema discovery step. Run against the real firewall and BPA API:

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli

# Export config from firewall
scm posture export --output config.xml

# Upload to BPA and get report
scm posture assess --config config.xml --delete-after --output report.json

# Inspect the report schema
python -c "import json; d=json.load(open('report.json')); print(json.dumps(list(d.keys()), indent=2))"

# Try scoring (may need adjustment based on actual schema)
scm posture score --report report.json --scope all --format json
```

After this step, update `posture.yaml` with the discovered report schema and adjust the `score_report()` function's field names if they differ from the assumed `checks[].name/status/category` structure.

- [ ] **Step 5: Final commit with any schema adjustments**

```bash
cd /Users/cdot/development/cdot65/pan-scm-cli
git add -A
git commit -m "fix(posture): adjust score parsing for real BPA report schema"
```
