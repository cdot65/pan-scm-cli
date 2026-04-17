# SDK 0.13.0 Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade pan-scm-sdk to ^0.13.0 and add three new CLI command groups: `scm local`, `scm operations`, `scm incidents`.

**Architecture:** Four sequential PRs. PR 1 (foundation) bumps the SDK, adds region support to contexts/client, and handles `JobTimeoutError`. PRs 2-4 each add one new command module with SDK client methods, mock mode, tests, and docs. Each PR is independently reviewable and shippable.

**Tech Stack:** Python 3.10+, Typer, Rich, pan-scm-sdk 0.13.0, Pydantic v2, pytest, MkDocs Material

**Design Spec:** `docs/superpowers/specs/2026-04-16-sdk-013-upgrade-design.md`
**GitHub Issues:** #212 (foundation), #213 (local), #214 (operations), #215 (incidents)

---

## PR 1: Foundation — SDK Bump + Region Support (#212)

### Task 1: Bump SDK dependency

**Files:**
- Modify: `pyproject.toml:15`

- [ ] **Step 1: Update pyproject.toml**

Change the SDK version constraint:

```toml
pan-scm-sdk = "^0.13.0"
```

- [ ] **Step 2: Update lock file**

Run: `poetry update pan-scm-sdk`
Expected: Lock file updated, SDK 0.13.x resolved

- [ ] **Step 3: Verify install**

Run: `poetry show pan-scm-sdk`
Expected: Version 0.13.x shown

- [ ] **Step 4: Run existing tests to confirm no regressions**

Run: `poetry run pytest -x -q`
Expected: All existing tests pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "build: bump pan-scm-sdk to ^0.13.0"
```

---

### Task 2: Add region to context storage

**Files:**
- Modify: `src/scm_cli/utils/context.py:90-126`
- Test: `tests/test_context_region.py` (create)

- [ ] **Step 1: Write failing tests for region in context create**

Create `tests/test_context_region.py`:

```python
"""Tests for region support in context management."""

import os

import yaml
import pytest

from src.scm_cli.utils.context import create_context, get_context_config


class TestContextRegion:
    """Test region field in context storage."""

    def test_create_context_with_region(self, tmp_path, monkeypatch):
        """Region is stored in context YAML when provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-region",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            region="europe",
        )

        context_file = tmp_path / "contexts" / "test-region.yaml"
        assert context_file.exists()
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "europe"

    def test_create_context_default_region(self, tmp_path, monkeypatch):
        """Region defaults to 'americas' when not provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-default",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
        )

        context_file = tmp_path / "contexts" / "test-default.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "americas"

    def test_old_context_without_region_defaults(self, tmp_path, monkeypatch):
        """Old context files without region field return 'americas'."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        os.makedirs(tmp_path / "contexts", exist_ok=True)
        old_context = tmp_path / "contexts" / "legacy.yaml"
        old_context.write_text("client_id: cid\nclient_secret: csec\ntsg_id: tsg\n")

        config = get_context_config("legacy")
        assert config.get("region", "americas") == "americas"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_context_region.py -v`
Expected: `test_create_context_with_region` FAILS (create_context doesn't accept `region`)

- [ ] **Step 3: Update create_context to accept and store region**

In `src/scm_cli/utils/context.py`, modify `create_context`:

```python
def create_context(
    context_name: str,
    client_id: str = "",
    client_secret: str = "",
    tsg_id: str = "",
    log_level: str = "INFO",
    access_token: str | None = None,
    region: str = "americas",
) -> None:
    """Create or update a context configuration.

    Args:
    ----
        context_name: Name of the context.
        client_id: SCM client ID.
        client_secret: SCM client secret.
        tsg_id: Tenant Service Group ID.
        log_level: Logging level (default: INFO).
        access_token: Bearer token for direct auth (alternative to OAuth2).
        region: SCM API region (default: americas).

    """
    ensure_context_dir()

    context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yaml")

    config: dict[str, Any] = {
        "log_level": log_level,
        "region": region,
    }

    if access_token:
        config["access_token"] = access_token
    else:
        config["client_id"] = client_id
        config["client_secret"] = client_secret
        config["tsg_id"] = tsg_id

    with open(context_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_context_region.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/context.py tests/test_context_region.py
git commit -m "feat: add region field to context storage"
```

---

### Task 3: Add --region to context create command

**Files:**
- Modify: `src/scm_cli/commands/context.py` (create_command function)
- Test: `tests/test_context_region.py` (extend)

- [ ] **Step 1: Write failing test for --region CLI option**

Add to `tests/test_context_region.py`:

```python
from src.scm_cli.main import app as main_app
from src.scm_cli.commands import context as context_module

main_app.add_typer(context_module.app, name="context")


class TestContextCreateRegionCLI:
    """Test --region flag on context create command."""

    def test_create_with_region_flag(self, runner, tmp_path, monkeypatch):
        """--region flag stores region in context."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(main_app, [
            "context", "create", "eu-prod",
            "--client-id", "cid",
            "--client-secret", "csec",
            "--tsg-id", "tsg",
            "--region", "europe",
            "--no-set-current",
        ])

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "eu-prod.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "europe"

    def test_create_without_region_defaults_americas(self, runner, tmp_path, monkeypatch):
        """Omitting --region stores 'americas' as default."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(main_app, [
            "context", "create", "us-prod",
            "--client-id", "cid",
            "--client-secret", "csec",
            "--tsg-id", "tsg",
            "--no-set-current",
        ])

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "us-prod.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "americas"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_context_region.py::TestContextCreateRegionCLI -v`
Expected: FAIL (no `--region` option exists yet)

- [ ] **Step 3: Add --region option to context create command**

In `src/scm_cli/commands/context.py`, add the `region` parameter to `create_command` (after the `set_current` parameter):

```python
    region: str = typer.Option(
        "americas",
        "--region",
        "-r",
        help="SCM API region (default: americas)",
    ),
```

And pass it through to `create_context`:

```python
        create_context(
            context_name=context_name,
            client_id=client_id or "",
            client_secret=client_secret or "",
            tsg_id=tsg_id or "",
            log_level=log_level,
            access_token=access_token,
            region=region,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_context_region.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/commands/context.py tests/test_context_region.py
git commit -m "feat: add --region option to context create"
```

---

### Task 4: Add global --region flag and pass region to Scm client

**Files:**
- Modify: `src/scm_cli/main.py:293-309` (callback)
- Modify: `src/scm_cli/utils/config.py:58-104` (get_auth_config)
- Test: `tests/test_context_region.py` (extend)

- [ ] **Step 1: Write failing test for region in auth config**

Add to `tests/test_context_region.py`:

```python
from src.scm_cli.utils.config import get_auth_config


class TestRegionInAuthConfig:
    """Test region flows through auth config."""

    def test_auth_config_includes_region_from_context(self, tmp_path, monkeypatch):
        """get_auth_config returns region from active context."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        os.makedirs(tmp_path / "contexts", exist_ok=True)
        (tmp_path / "contexts" / "prod.yaml").write_text(
            "client_id: cid\nclient_secret: csec\ntsg_id: tsg\nregion: europe\n"
        )
        (tmp_path / "current-context").write_text("prod")

        # Re-init settings from patched context
        import scm_cli.utils.config as config_mod
        from scm_cli.utils.context import get_context_aware_settings
        config_mod.settings = get_context_aware_settings()

        auth = get_auth_config()
        assert auth["region"] == "europe"

    def test_auth_config_defaults_region_americas(self, monkeypatch):
        """get_auth_config defaults region to americas when not in context."""
        monkeypatch.setenv("SCM_SCM_CLIENT_ID", "cid")
        monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("SCM_SCM_TSG_ID", "tsg")

        import scm_cli.utils.config as config_mod
        from scm_cli.utils.context import get_context_aware_settings
        config_mod.settings = get_context_aware_settings()

        auth = get_auth_config()
        assert auth.get("region", "americas") == "americas"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_context_region.py::TestRegionInAuthConfig -v`
Expected: FAIL (get_auth_config doesn't return region)

- [ ] **Step 3: Update get_auth_config to include region**

In `src/scm_cli/utils/config.py`, modify `get_auth_config`:

```python
def get_auth_config() -> dict[str, str]:
    """Get SCM API authentication configuration from dynaconf settings.

    Uses the following precedence order:
    1. Current context (set via 'scm context use')
    2. Environment variables (SCM_CLIENT_ID, etc.)
    3. Default settings

    Note: Legacy config file (~/.scm-cli/config.yaml) is no longer supported.
    Use contexts for multi-tenant support.

    Returns
    -------
        Dict containing client_id, client_secret, tsg_id, and region.

    Raises
    ------
        ValueError: If required authentication parameters are missing.

    Examples
    --------
        >>> auth = get_auth_config()
        >>> client = Scm(**auth) #noqa

    """
    # Get authentication from settings (which already includes context awareness)
    auth = {
        "client_id": settings.get("client_id", ""),
        "client_secret": settings.get("client_secret", ""),
        "tsg_id": settings.get("tsg_id", ""),
    }

    # For backward compatibility, also check the scm_ prefixed settings
    # but only if the non-prefixed values are empty
    if not auth["client_id"]:
        auth["client_id"] = settings.get("scm_client_id", "")
    if not auth["client_secret"]:
        auth["client_secret"] = settings.get("scm_client_secret", "")
    if not auth["tsg_id"]:
        auth["tsg_id"] = settings.get("scm_tsg_id", "")

    # Check for missing parameters
    missing = [k for k, v in auth.items() if not v]
    if missing:
        raise ValueError(f"Missing required authentication parameters: {', '.join(missing)}")

    # Add region (not required — defaults to americas)
    auth["region"] = settings.get("region", "americas")

    return auth
```

- [ ] **Step 4: Add global --region flag to main.py callback**

In `src/scm_cli/main.py`, add a module-level variable and update the callback:

```python
# Module-level region override (set by --region flag)
_region_override: str | None = None


@app.callback()
def callback(
    region: str | None = typer.Option(
        None,
        "--region",
        help="Override SCM API region for this invocation",
    ),
):
    """Manage Palo Alto Networks Strata Cloud Manager (SCM) configurations.

    The CLI follows the pattern: <action> <object-type> <object> [options]

    Examples
    --------
      - scm set object address-group --folder Texas --name test123 --type static
      - scm delete security security-rule --folder Texas --name test123
      - scm load network zone --file config/security_zones.yml
      - scm show object address --folder Texas --list
      - scm show object address --folder Texas --name webserver
      - scm context test

    """
    global _region_override  # noqa: PLW0603
    _region_override = region
```

Also add a helper function after the callback:

```python
def get_region_override() -> str | None:
    """Get the global --region override value, if set."""
    return _region_override
```

- [ ] **Step 5: Update sdk_client.py to use region override**

In `src/scm_cli/utils/sdk_client.py`, in the `SCMClient.__init__` OAuth2 branch where `Scm()` is constructed, add region resolution:

```python
            # Resolve region: global flag > context > default
            from scm_cli.main import get_region_override
            region_override = get_region_override()
            resolved_region = region_override or credentials.get("region", "americas")

            self.client = Scm(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tsg_id=self.tsg_id,
                log_level=settings.get("log_level", "INFO"),
                region=resolved_region,
            )
```

Apply the same pattern to the bearer token branch.

- [ ] **Step 6: Run tests to verify they pass**

Run: `poetry run pytest tests/test_context_region.py -v`
Expected: All tests PASS

Run: `poetry run pytest -x -q`
Expected: All existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add src/scm_cli/main.py src/scm_cli/utils/config.py src/scm_cli/utils/sdk_client.py tests/test_context_region.py
git commit -m "feat: add global --region flag with context/override precedence"
```

---

### Task 5: Handle JobTimeoutError in sdk_client

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py:20` (imports), `sdk_client.py:226-258` (_handle_api_exception)
- Test: `tests/test_context_region.py` (extend — or new file `tests/test_job_timeout.py`)

- [ ] **Step 1: Write failing test for JobTimeoutError handling**

Create `tests/test_job_timeout.py`:

```python
"""Tests for JobTimeoutError handling."""

import pytest

from src.scm_cli.utils.sdk_client import SCMClient


class TestJobTimeoutError:
    """Test JobTimeoutError is handled properly."""

    def test_handle_job_timeout_logs_and_reraises(self):
        """_handle_api_exception logs JobTimeoutError with job_id and last_state."""
        from scm.exceptions import JobTimeoutError

        client = SCMClient.__new__(SCMClient)
        client.logger = __import__("logging").getLogger("test")
        client.client = None

        exc = JobTimeoutError(job_id="job-abc", last_state="running")

        with pytest.raises(JobTimeoutError):
            client._handle_api_exception("dispatch", "N/A", "route-table", exc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_job_timeout.py -v`
Expected: FAIL — either `JobTimeoutError` import fails (SDK not yet updated) or it falls through to the generic handler without specific logging

- [ ] **Step 3: Add JobTimeoutError to imports and handler**

In `src/scm_cli/utils/sdk_client.py`, update the import (line 20):

```python
from scm.exceptions import APIError, AuthenticationError, ClientError, JobTimeoutError, NotFoundError
```

In `_handle_api_exception`, add a new branch before the generic `else` (after the `APIError` check):

```python
        elif isinstance(exception, JobTimeoutError):
            self.logger.error(
                f"Job {exception.job_id} timed out in state '{exception.last_state}' "
                f"during {operation} of {resource_name}. "
                f"Check with: scm operations status --job-id {exception.job_id}"
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_job_timeout.py -v`
Expected: PASS

Run: `poetry run pytest -x -q`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_job_timeout.py
git commit -m "feat: handle JobTimeoutError with job_id and recovery message"
```

---

### Task 6: Quality gate and PR for foundation

**Files:** None (verification only)

- [ ] **Step 1: Run full quality checks**

Run: `make quality`
Expected: lint, format, mypy, tests all pass

- [ ] **Step 2: Create PR**

```bash
git push -u origin cdot65/sdk-013-foundation
gh pr create --title "feat: upgrade pan-scm-sdk to 0.13.0 with region support" --body "$(cat <<'EOF'
## Summary
- Bump pan-scm-sdk from ^0.12.2 to ^0.13.0
- Add `--region` option to `scm context create` (stored per-context, defaults to "americas")
- Add global `--region` flag to override region per-invocation
- Handle `JobTimeoutError` with job_id and recovery instructions
- Backward compatible: old contexts without region default to "americas"

Closes #212

## Test plan
- [ ] `poetry show pan-scm-sdk` shows 0.13.x
- [ ] `scm context create test --client-id x --client-secret y --tsg-id z --region europe` stores region
- [ ] `scm context create test2 --client-id x --client-secret y --tsg-id z` defaults to americas
- [ ] All existing tests pass with 0 regressions

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## PR 2: Local Config Commands (#213)

### Task 7: Add SDK client methods for local config

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py` (add methods before LazyClient class)
- Test: `tests/test_local_commands.py` (create)

- [ ] **Step 1: Write failing tests for SDK client methods**

Create `tests/test_local_commands.py`:

```python
"""Tests for local config commands."""

import os

import pytest
import yaml
from typer.testing import CliRunner

from src.scm_cli.main import app
from src.scm_cli.utils.sdk_client import SCMClient


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_local_commands.py::TestLocalConfigSDKClient -v`
Expected: FAIL — `list_local_config_versions` not defined

- [ ] **Step 3: Implement SDK client methods**

Add to `src/scm_cli/utils/sdk_client.py` before the `LazyClient` class (around line 15999):

```python
    # ==========================================================================================================================================================================================
    # LOCAL CONFIG METHODS
    # ==========================================================================================================================================================================================

    def list_local_config_versions(self, device: str) -> list[dict[str, Any]]:
        """List configuration versions for a device.

        Args:
            device: Device name to list versions for.

        Returns:
            list[dict[str, Any]]: List of config version objects.

        """
        self.logger.info(f"Listing local config versions for device: {device}")

        if not self.client:
            return [
                {"version": 42, "date": "2026-04-15 14:30", "author": "admin", "description": "Policy update"},
                {"version": 41, "date": "2026-04-14 09:12", "author": "auto-commit", "description": "Scheduled push"},
                {"version": 40, "date": "2026-04-13 11:45", "author": "admin", "description": "Initial config"},
            ]

        try:
            results = self.client.local_config.list(device=device)
            return [json.loads(r.model_dump_json(exclude_unset=True)) for r in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", f"local config versions for {device}", e)

    def download_local_config(self, device: str, version: int) -> bytes:
        """Download a configuration version as raw XML.

        Args:
            device: Device name.
            version: Config version number to download.

        Returns:
            bytes: Raw XML configuration data.

        """
        self.logger.info(f"Downloading local config version {version} for device: {device}")

        if not self.client:
            return b'<?xml version="1.0"?>\n<config version="42">\n  <devices>\n    <entry name="fw-01">\n      <vsys/>\n    </entry>\n  </devices>\n</config>'

        try:
            return self.client.local_config.download(device=device, version=version)
        except Exception as e:
            self._handle_api_exception("downloading", "N/A", f"local config v{version} for {device}", e)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_local_commands.py::TestLocalConfigSDKClient -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_local_commands.py
git commit -m "feat: add SDK client methods for local config"
```

---

### Task 8: Create local command module

**Files:**
- Create: `src/scm_cli/commands/local.py`
- Modify: `src/scm_cli/main.py` (register)
- Test: `tests/test_local_commands.py` (extend)

- [ ] **Step 1: Write failing tests for CLI commands**

Add to `tests/test_local_commands.py`:

```python
from src.scm_cli.commands import local as local_module

app.add_typer(local_module.app, name="local")


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_local_commands.py::TestLocalList -v`
Expected: FAIL — module `local` does not exist

- [ ] **Step 3: Create the local command module**

Create `src/scm_cli/commands/local.py`:

```python
"""Local configuration management commands for scm-cli.

This module provides commands to list device configuration versions
and download configuration files as XML.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Manage local device configurations")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name")

# =============================================================================================================================================================================================
# LOCAL CONFIG COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------ list ------------------------------------------------------------------------------------


@app.command("list")
def list_versions(
    device: str = DEVICE_OPTION,
):
    """List configuration versions for a device.

    Examples
    --------
    scm local list --device fw-01

    """
    try:
        versions = scm_client.list_local_config_versions(device=device)

        if not versions:
            typer.echo("No config versions found")
            return

        table = Table(title=f"Config Versions — {device}")
        table.add_column("Version", style="cyan")
        table.add_column("Date", style="white")
        table.add_column("Author", style="green")
        table.add_column("Description", style="dim")

        for v in versions:
            table.add_row(
                str(v.get("version", "")),
                str(v.get("date", "")),
                str(v.get("author", "")),
                str(v.get("description", "")),
            )

        console.print(table)

    except Exception as e:
        typer.echo(f"Error listing config versions: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ----------------------------------------------------------------------------------- download -----------------------------------------------------------------------------------


@app.command("download")
def download_config(
    device: str = DEVICE_OPTION,
    version: int = typer.Option(..., "--version", "-v", help="Config version number"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
):
    """Download a device configuration version as XML.

    Examples
    --------
    scm local download --device fw-01 --version 42
    scm local download --device fw-01 --version 42 --output config.xml

    """
    try:
        xml_data = scm_client.download_local_config(device=device, version=version)

        if output:
            Path(output).write_bytes(xml_data)
            typer.echo(f"Config written to {output}", err=True)
        else:
            sys.stdout.buffer.write(xml_data)
            sys.stdout.buffer.write(b"\n")

    except Exception as e:
        typer.echo(f"Error downloading config: {e!s}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 4: Register in main.py**

In `src/scm_cli/main.py`, add to the import line:

```python
from .commands import commit, context, deployment, identity, insights, jobs, local, mobile_agent, network, objects, posture, security, setup
```

Add to the top-level commands section (alphabetical, between `jobs` and `posture`):

```python
app.add_typer(local.app, name="local")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `poetry run pytest tests/test_local_commands.py -v`
Expected: All tests PASS

Run: `poetry run pytest -x -q`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/commands/local.py src/scm_cli/main.py tests/test_local_commands.py
git commit -m "feat: add scm local list and download commands"
```

---

### Task 9: Add local config documentation and PR

**Files:**
- Create: `docs/cli/local/index.md`
- Modify: `mkdocs.yml`

- [ ] **Step 1: Create documentation page**

Create `docs/cli/local/index.md`:

```markdown
# Local Config

Manage local device configuration versions and downloads.

## Commands

### List Config Versions

```bash
scm local list --device fw-01
```

Lists available configuration versions for a device, showing version number, date, author, and description.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device name |

### Download Config

```bash
# Output to stdout
scm local download --device fw-01 --version 42

# Save to file
scm local download --device fw-01 --version 42 --output config.xml
```

Downloads a specific configuration version as XML. Outputs to stdout by default; use `--output` to write to a file.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device name |
| `--version`, `-v` | Yes | Config version number |
| `--output`, `-o` | No | Output file path (default: stdout) |
```

- [ ] **Step 2: Add to mkdocs.yml nav**

In `mkdocs.yml`, add after the "Mobile Agent" section (before "Jobs"):

```yaml
      - Local Config:
          - Overview: cli/local/index.md
```

- [ ] **Step 3: Verify docs build**

Run: `poetry run mkdocs build --strict 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Commit and create PR**

```bash
git add docs/cli/local/index.md mkdocs.yml
git commit -m "docs: add local config command documentation"
git push -u origin cdot65/local-config-commands
gh pr create --title "feat: add scm local commands for config versions" --body "$(cat <<'EOF'
## Summary
- Add `scm local list --device <name>` to show config versions
- Add `scm local download --device <name> --version <id>` for XML download
- Supports stdout (default) and `--output` file modes
- Mock mode support for testing

Closes #213

## Test plan
- [ ] `scm local list --device fw-01` shows version table
- [ ] `scm local download --device fw-01 --version 42` outputs XML
- [ ] `scm local download --output test.xml` writes file
- [ ] All tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## PR 3: Device Operations Commands (#214)

### Task 10: Add SDK client methods for device operations

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py` (add methods)
- Test: `tests/test_operations_commands.py` (create)

- [ ] **Step 1: Write failing tests for SDK client methods**

Create `tests/test_operations_commands.py`:

```python
"""Tests for device operations commands."""

import pytest
from typer.testing import CliRunner

from src.scm_cli.main import app
from src.scm_cli.utils.sdk_client import SCMClient


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
        """dispatch_device_operation returns results in sync mode."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.dispatch_device_operation(device="fw-01", operation="route-table", sync=True)
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "completed"
        assert "results" in result

    def test_dispatch_operation_mock_async(self):
        """dispatch_device_operation returns job_id in async mode."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.dispatch_device_operation(device="fw-01", operation="route-table", sync=False)
        assert isinstance(result, dict)
        assert "job_id" in result

    def test_get_operation_status_mock(self):
        """get_device_operation_status returns mock status."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.get_device_operation_status(job_id="job-abc")
        assert isinstance(result, dict)
        assert "job_id" in result
        assert "state" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_operations_commands.py::TestOperationsSDKClient -v`
Expected: FAIL — methods not defined

- [ ] **Step 3: Implement SDK client methods**

Add to `src/scm_cli/utils/sdk_client.py` before the `LazyClient` class:

```python
    # ==========================================================================================================================================================================================
    # DEVICE OPERATIONS METHODS
    # ==========================================================================================================================================================================================

    _OPERATION_MOCK_RESULTS = {
        "route-table": [
            {"destination": "0.0.0.0/0", "next_hop": "10.0.0.1", "interface": "ethernet1/1", "metric": 10},
            {"destination": "10.1.0.0/16", "next_hop": "10.0.0.2", "interface": "ethernet1/2", "metric": 20},
        ],
        "fib-table": [
            {"destination": "0.0.0.0/0", "interface": "ethernet1/1", "next_hop": "10.0.0.1", "flags": "u"},
        ],
        "dns-proxy": [
            {"domain": "example.com", "primary": "8.8.8.8", "secondary": "8.8.4.4", "status": "active"},
        ],
        "interfaces": [
            {"name": "ethernet1/1", "status": "up", "ip": "10.0.0.1/24", "speed": "1Gbps"},
            {"name": "ethernet1/2", "status": "up", "ip": "10.1.0.1/24", "speed": "1Gbps"},
        ],
        "device-rules": [
            {"name": "allow-web", "action": "allow", "from": "trust", "to": "untrust"},
        ],
        "bgp-export": [
            {"prefix": "10.0.0.0/8", "next_hop": "10.0.0.1", "as_path": "65001 65002"},
        ],
        "logging-status": [
            {"service": "cortex-data-lake", "status": "connected", "last_log": "2026-04-16 10:30:00"},
        ],
    }

    def dispatch_device_operation(
        self,
        device: str,
        operation: str,
        sync: bool = True,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Dispatch a device operation job.

        Args:
            device: Device name to run operation on.
            operation: Operation type (route-table, fib-table, etc.).
            sync: If True, poll until completion. If False, return job_id immediately.
            timeout: Timeout in seconds for sync polling.

        Returns:
            dict: Results if sync, or job_id if async.

        """
        self.logger.info(f"Dispatching {operation} for device {device} (sync={sync})")

        if not self.client:
            if sync:
                return {
                    "status": "completed",
                    "job_id": f"mock-job-{operation}",
                    "device": device,
                    "operation": operation,
                    "results": self._OPERATION_MOCK_RESULTS.get(operation, []),
                }
            return {
                "job_id": f"mock-job-{operation}",
                "device": device,
                "operation": operation,
                "status": "pending",
            }

        try:
            job = self.client.device_operations.dispatch(
                device=device,
                operation=operation,
            )
            if sync:
                result = self.client.device_operations.wait(
                    job_id=job.job_id,
                    timeout=timeout,
                )
                return json.loads(result.model_dump_json(exclude_unset=True))
            return {"job_id": job.job_id, "device": device, "operation": operation, "status": "pending"}
        except Exception as e:
            self._handle_api_exception("dispatching", "N/A", f"{operation} for {device}", e)

    def get_device_operation_status(self, job_id: str) -> dict[str, Any]:
        """Get status of a device operation job.

        Args:
            job_id: The job ID to check.

        Returns:
            dict: Job status information.

        """
        self.logger.info(f"Checking status of job {job_id}")

        if not self.client:
            return {
                "job_id": job_id,
                "state": "completed",
                "device": "fw-01",
                "operation": "route-table",
                "started": "2026-04-16 10:30:00",
                "completed": "2026-04-16 10:30:42",
            }

        try:
            result = self.client.device_operations.status(job_id=job_id)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("checking status", "N/A", f"job {job_id}", e)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_operations_commands.py::TestOperationsSDKClient -v`
Expected: All 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_operations_commands.py
git commit -m "feat: add SDK client methods for device operations"
```

---

### Task 11: Create operations command module

**Files:**
- Create: `src/scm_cli/commands/operations.py`
- Modify: `src/scm_cli/main.py` (register)
- Test: `tests/test_operations_commands.py` (extend)

- [ ] **Step 1: Write failing tests for CLI commands**

Add to `tests/test_operations_commands.py`:

```python
from src.scm_cli.commands import operations as ops_module

app.add_typer(ops_module.app, name="operations")


class TestOperationsRouteTable:
    """Test operations route-table command."""

    def test_route_table_sync(self, runner, mock_ops_env):
        """scm operations route-table shows results in sync mode."""
        result = runner.invoke(app, ["operations", "route-table", "--device", "fw-01"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "0.0.0.0/0" in result.output
        assert "10.0.0.1" in result.output

    def test_route_table_async(self, runner, mock_ops_env):
        """scm operations route-table --async returns job ID."""
        result = runner.invoke(app, ["operations", "route-table", "--device", "fw-01", "--async"])

        assert result.exit_code == 0
        assert "mock-job-route-table" in result.output


class TestOperationsInterfaces:
    """Test operations interfaces command."""

    def test_interfaces_sync(self, runner, mock_ops_env):
        """scm operations interfaces shows interface data."""
        result = runner.invoke(app, ["operations", "interfaces", "--device", "fw-01"])

        assert result.exit_code == 0
        assert "ethernet1/1" in result.output


class TestOperationsStatus:
    """Test operations status command."""

    def test_status_check(self, runner, mock_ops_env):
        """scm operations status shows job details."""
        result = runner.invoke(app, ["operations", "status", "--job-id", "job-abc"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "job-abc" in result.output
        assert "completed" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_operations_commands.py::TestOperationsRouteTable -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Create the operations command module**

Create `src/scm_cli/commands/operations.py`:

```python
"""Device operations commands for scm-cli.

This module provides commands to dispatch and monitor asynchronous device
jobs for route tables, FIB tables, DNS proxy, network interfaces, device
rules, BGP policy export, and logging service status.
"""

import json

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Dispatch and monitor device operations")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

DEVICE_OPTION = typer.Option(..., "--device", "-d", help="Device name")
ASYNC_OPTION = typer.Option(False, "--async", help="Return job ID without waiting for completion")
TIMEOUT_OPTION = typer.Option(300, "--timeout", "-t", help="Sync polling timeout in seconds")


# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================

_OPERATION_COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    "route-table": [("destination", "Destination", "cyan"), ("next_hop", "Next Hop", "white"), ("interface", "Interface", "green"), ("metric", "Metric", "dim")],
    "fib-table": [("destination", "Destination", "cyan"), ("interface", "Interface", "green"), ("next_hop", "Next Hop", "white"), ("flags", "Flags", "dim")],
    "dns-proxy": [("domain", "Domain", "cyan"), ("primary", "Primary", "white"), ("secondary", "Secondary", "white"), ("status", "Status", "green")],
    "interfaces": [("name", "Name", "cyan"), ("status", "Status", "green"), ("ip", "IP Address", "white"), ("speed", "Speed", "dim")],
    "device-rules": [("name", "Name", "cyan"), ("action", "Action", "green"), ("from", "From", "white"), ("to", "To", "white")],
    "bgp-export": [("prefix", "Prefix", "cyan"), ("next_hop", "Next Hop", "white"), ("as_path", "AS Path", "dim")],
    "logging-status": [("service", "Service", "cyan"), ("status", "Status", "green"), ("last_log", "Last Log", "dim")],
}


def _run_operation(
    device: str,
    operation: str,
    async_mode: bool,
    timeout: int,
) -> None:
    """Dispatch an operation and display results or job ID."""
    try:
        result = scm_client.dispatch_device_operation(
            device=device,
            operation=operation,
            sync=not async_mode,
            timeout=timeout,
        )

        if async_mode:
            job_id = result.get("job_id", "unknown")
            typer.echo(f"Job dispatched: {job_id}")
            typer.echo(f"Check status with: scm operations status --job-id {job_id}")
            return

        results = result.get("results", [])
        if not results:
            typer.echo(f"No results returned for {operation}")
            return

        columns = _OPERATION_COLUMNS.get(operation, [])
        table = Table(title=f"{operation} — {device}")
        for key, header, style in columns:
            table.add_column(header, style=style)

        for row in results:
            table.add_row(*[str(row.get(key, "")) for key, _, _ in columns])

        console.print(table)

    except Exception as e:
        typer.echo(f"Error running {operation}: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# OPERATION COMMANDS
# =============================================================================================================================================================================================

# --------------------------------------------------------------------------------- route-table ---------------------------------------------------------------------------------


@app.command("route-table")
def route_table(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Retrieve device routing table.

    Examples
    --------
    scm operations route-table --device fw-01
    scm operations route-table --device fw-01 --async

    """
    _run_operation(device, "route-table", async_mode, timeout)


# ---------------------------------------------------------------------------------- fib-table ----------------------------------------------------------------------------------


@app.command("fib-table")
def fib_table(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Retrieve forwarding information base table.

    Examples
    --------
    scm operations fib-table --device fw-01

    """
    _run_operation(device, "fib-table", async_mode, timeout)


# ---------------------------------------------------------------------------------- dns-proxy ----------------------------------------------------------------------------------


@app.command("dns-proxy")
def dns_proxy(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Query DNS proxy configuration and status.

    Examples
    --------
    scm operations dns-proxy --device fw-01

    """
    _run_operation(device, "dns-proxy", async_mode, timeout)


# --------------------------------------------------------------------------------- interfaces ---------------------------------------------------------------------------------


@app.command("interfaces")
def interfaces(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Retrieve network interface status.

    Examples
    --------
    scm operations interfaces --device fw-01

    """
    _run_operation(device, "interfaces", async_mode, timeout)


# -------------------------------------------------------------------------------- device-rules --------------------------------------------------------------------------------


@app.command("device-rules")
def device_rules(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Retrieve applied security rules from device.

    Examples
    --------
    scm operations device-rules --device fw-01

    """
    _run_operation(device, "device-rules", async_mode, timeout)


# ---------------------------------------------------------------------------------- bgp-export ---------------------------------------------------------------------------------


@app.command("bgp-export")
def bgp_export(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Export BGP routing policies.

    Examples
    --------
    scm operations bgp-export --device fw-01

    """
    _run_operation(device, "bgp-export", async_mode, timeout)


# ------------------------------------------------------------------------------- logging-status -------------------------------------------------------------------------------


@app.command("logging-status")
def logging_status(
    device: str = DEVICE_OPTION,
    async_mode: bool = ASYNC_OPTION,
    timeout: int = TIMEOUT_OPTION,
):
    """Check logging service health.

    Examples
    --------
    scm operations logging-status --device fw-01

    """
    _run_operation(device, "logging-status", async_mode, timeout)


# ------------------------------------------------------------------------------------ status -----------------------------------------------------------------------------------


@app.command("status")
def operation_status(
    job_id: str = typer.Option(..., "--job-id", "-j", help="Job ID to check"),
):
    """Check status of a dispatched device operation job.

    Examples
    --------
    scm operations status --job-id abc-123

    """
    try:
        result = scm_client.get_device_operation_status(job_id=job_id)

        typer.echo(f"\nJob Details for ID: {result.get('job_id', job_id)}")
        typer.echo("-" * 50)
        for key, value in result.items():
            if value is not None and value != "" and value != []:
                typer.echo(f"  {key}: {value}")

    except Exception as e:
        typer.echo(f"Error checking job status: {e!s}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 4: Register in main.py**

In `src/scm_cli/main.py`, update import:

```python
from .commands import commit, context, deployment, identity, insights, jobs, local, mobile_agent, network, objects, operations, posture, security, setup
```

Add to top-level commands (alphabetical, between `local` and `posture`):

```python
app.add_typer(operations.app, name="operations")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `poetry run pytest tests/test_operations_commands.py -v`
Expected: All tests PASS

Run: `poetry run pytest -x -q`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/commands/operations.py src/scm_cli/main.py tests/test_operations_commands.py
git commit -m "feat: add scm operations commands for device jobs"
```

---

### Task 12: Add operations documentation and PR

**Files:**
- Create: `docs/cli/operations/index.md`
- Modify: `mkdocs.yml`

- [ ] **Step 1: Create documentation page**

Create `docs/cli/operations/index.md`:

```markdown
# Device Operations

Dispatch and monitor asynchronous device jobs for network diagnostics and status checks.

## Commands

All operation commands support:

| Option | Default | Description |
|--------|---------|-------------|
| `--device`, `-d` | Required | Device name |
| `--async` | `False` | Return job ID without waiting |
| `--timeout`, `-t` | `300` | Sync polling timeout in seconds |

### Route Table

```bash
scm operations route-table --device fw-01
scm operations route-table --device fw-01 --async
```

### FIB Table

```bash
scm operations fib-table --device fw-01
```

### DNS Proxy

```bash
scm operations dns-proxy --device fw-01
```

### Network Interfaces

```bash
scm operations interfaces --device fw-01
```

### Device Rules

```bash
scm operations device-rules --device fw-01
```

### BGP Export

```bash
scm operations bgp-export --device fw-01
```

### Logging Status

```bash
scm operations logging-status --device fw-01
```

### Job Status

Check on an async job:

```bash
scm operations status --job-id abc-123
```

## Sync vs Async

By default, commands block and poll until the operation completes, then display results as a table. Use `--async` to get the job ID immediately and check later with `scm operations status`.

If sync polling exceeds `--timeout`, the CLI reports the job ID and last known state for manual follow-up.
```

- [ ] **Step 2: Add to mkdocs.yml nav**

Add after "Local Config" in the nav:

```yaml
      - Operations:
          - Overview: cli/operations/index.md
```

- [ ] **Step 3: Verify docs build**

Run: `poetry run mkdocs build --strict 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Commit and create PR**

```bash
git add docs/cli/operations/index.md mkdocs.yml
git commit -m "docs: add device operations command documentation"
git push -u origin cdot65/operations-commands
gh pr create --title "feat: add scm operations commands for device jobs" --body "$(cat <<'EOF'
## Summary
- Add 7 device operation commands: route-table, fib-table, dns-proxy, interfaces, device-rules, bgp-export, logging-status
- Add `scm operations status --job-id <id>` for async job tracking
- Default sync (poll to completion), `--async` for fire-and-forget
- `--timeout` controls sync polling duration
- Mock mode support

Closes #214

## Test plan
- [ ] `scm operations route-table --device fw-01` shows routing table
- [ ] `scm operations route-table --device fw-01 --async` returns job ID
- [ ] `scm operations status --job-id <id>` shows job details
- [ ] All 7 operation types return appropriate mock data
- [ ] All tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## PR 4: Incidents Commands (#215)

### Task 13: Add SDK client methods for incidents

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py` (add methods)
- Test: `tests/test_incidents_commands.py` (create)

- [ ] **Step 1: Write failing tests for SDK client methods**

Create `tests/test_incidents_commands.py`:

```python
"""Tests for incidents commands."""

import json

import pytest
from typer.testing import CliRunner

from src.scm_cli.main import app
from src.scm_cli.utils.sdk_client import SCMClient


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
        """list_incidents returns mock data when no client."""
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
        """list_incidents filters by status in mock mode."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.list_incidents(status="open")
        assert all(i["status"] == "open" for i in result)

    def test_get_incident_mock(self):
        """get_incident returns mock detail with alerts."""
        client = SCMClient.__new__(SCMClient)
        client.client = None
        client.logger = __import__("logging").getLogger("test")

        result = client.get_incident(incident_id="INC-2026-04-001")
        assert isinstance(result, dict)
        assert "id" in result
        assert "alerts" in result
        assert "remediation" in result
        assert len(result["alerts"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_incidents_commands.py::TestIncidentsSDKClient -v`
Expected: FAIL — methods not defined

- [ ] **Step 3: Implement SDK client methods**

Add to `src/scm_cli/utils/sdk_client.py` before the `LazyClient` class:

```python
    # ==========================================================================================================================================================================================
    # INCIDENTS METHODS
    # ==========================================================================================================================================================================================

    _MOCK_INCIDENTS = [
        {
            "id": "INC-2026-04-001",
            "status": "open",
            "severity": "high",
            "product": "Prisma Access",
            "summary": "Suspicious lateral movement detected from 10.1.2.50",
            "created": "2026-04-15 08:23:00",
            "updated": "2026-04-16 02:15:00",
            "alerts": [
                {"severity": "high", "description": "Unusual SMB traffic from 10.1.2.50 to 10.1.2.100", "timestamp": "2026-04-15 08:23"},
                {"severity": "high", "description": "Credential dumping tool detected on 10.1.2.50", "timestamp": "2026-04-15 08:25"},
                {"severity": "medium", "description": "DNS tunneling attempt from 10.1.2.50", "timestamp": "2026-04-15 08:30"},
            ],
            "remediation": [
                "Isolate host 10.1.2.50 from network",
                "Reset credentials for affected accounts",
                "Scan 10.1.2.100 for indicators of compromise",
            ],
        },
        {
            "id": "INC-2026-04-002",
            "status": "open",
            "severity": "critical",
            "product": "NGFW",
            "summary": "C2 callback detected from internal host",
            "created": "2026-04-14 16:45:00",
            "updated": "2026-04-15 09:00:00",
            "alerts": [
                {"severity": "critical", "description": "Known C2 domain contacted by 10.2.1.30", "timestamp": "2026-04-14 16:45"},
                {"severity": "high", "description": "Encrypted payload exfiltration attempt", "timestamp": "2026-04-14 16:50"},
            ],
            "remediation": [
                "Block C2 domain at firewall",
                "Isolate 10.2.1.30",
                "Forensic analysis of affected host",
            ],
        },
        {
            "id": "INC-2026-03-088",
            "status": "closed",
            "severity": "medium",
            "product": "Prisma Access",
            "summary": "Policy violation — data exfiltration attempt",
            "created": "2026-03-28 14:00:00",
            "updated": "2026-03-29 11:30:00",
            "alerts": [
                {"severity": "medium", "description": "Large file upload to unapproved cloud storage", "timestamp": "2026-03-28 14:00"},
            ],
            "remediation": [
                "User counseling completed",
                "DLP policy updated to block unapproved storage",
            ],
        },
    ]

    def list_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        product: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search incidents with optional filters.

        Args:
            status: Filter by incident status (open, closed, in_progress).
            severity: Filter by severity (critical, high, medium, low, informational).
            product: Filter by product name.

        Returns:
            list[dict[str, Any]]: List of incident objects.

        """
        self.logger.info(f"Listing incidents (status={status}, severity={severity}, product={product})")

        if not self.client:
            results = list(self._MOCK_INCIDENTS)
            if status:
                results = [i for i in results if i["status"] == status]
            if severity:
                results = [i for i in results if i["severity"] == severity]
            if product:
                results = [i for i in results if i["product"] == product]
            return results

        try:
            kwargs: dict[str, Any] = {}
            if status:
                kwargs["status"] = status
            if severity:
                kwargs["severity"] = severity
            if product:
                kwargs["product"] = product
            results = self.client.incidents.search(**kwargs)
            return [json.loads(r.model_dump_json(exclude_unset=True)) for r in results]
        except Exception as e:
            self._handle_api_exception("searching", "N/A", "incidents", e)

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        """Get detailed incident information including alerts and remediation.

        Args:
            incident_id: The incident ID to retrieve.

        Returns:
            dict[str, Any]: Full incident detail.

        """
        self.logger.info(f"Getting incident detail: {incident_id}")

        if not self.client:
            for inc in self._MOCK_INCIDENTS:
                if inc["id"] == incident_id:
                    return inc
            return self._MOCK_INCIDENTS[0]

        try:
            result = self.client.incidents.get(incident_id=incident_id)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", "N/A", f"incident {incident_id}", e)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_incidents_commands.py::TestIncidentsSDKClient -v`
Expected: All 4 PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_incidents_commands.py
git commit -m "feat: add SDK client methods for incidents"
```

---

### Task 14: Create incidents command module

**Files:**
- Create: `src/scm_cli/commands/incidents.py`
- Modify: `src/scm_cli/main.py` (register)
- Test: `tests/test_incidents_commands.py` (extend)

- [ ] **Step 1: Write failing tests for CLI commands**

Add to `tests/test_incidents_commands.py`:

```python
from src.scm_cli.commands import incidents as incidents_module

app.add_typer(incidents_module.app, name="incidents")


class TestIncidentsList:
    """Test incidents list command."""

    def test_list_incidents_table(self, runner, mock_incidents_env):
        """scm incidents list shows summary table."""
        result = runner.invoke(app, ["incidents", "list"])

        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "INC-2026-04-001" in result.output
        assert "high" in result.output

    def test_list_incidents_filter_status(self, runner, mock_incidents_env):
        """scm incidents list --status filters results."""
        result = runner.invoke(app, ["incidents", "list", "--status", "closed"])

        assert result.exit_code == 0
        assert "INC-2026-03-088" in result.output
        assert "INC-2026-04-001" not in result.output

    def test_list_incidents_json(self, runner, mock_incidents_env):
        """scm incidents list --json outputs JSON."""
        result = runner.invoke(app, ["incidents", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_incidents_empty(self, runner, mock_incidents_env):
        """scm incidents list shows message for no results."""
        result = runner.invoke(app, ["incidents", "list", "--severity", "informational"])

        assert result.exit_code == 0
        assert "No incidents found" in result.output


class TestIncidentsShow:
    """Test incidents show command."""

    def test_show_incident_detail(self, runner, mock_incidents_env):
        """scm incidents show displays formatted detail."""
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
        """scm incidents show --json outputs full JSON."""
        result = runner.invoke(app, ["incidents", "show", "INC-2026-04-001", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "INC-2026-04-001"
        assert "alerts" in data
        assert "remediation" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_incidents_commands.py::TestIncidentsList -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Create the incidents command module**

Create `src/scm_cli/commands/incidents.py`:

```python
"""Incident management commands for scm-cli.

This module provides commands to search and view security incidents
from the SCM Unified Incident Framework.
"""

import json

import typer
from rich.console import Console
from rich.table import Table

from ..utils.sdk_client import scm_client

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

app = typer.Typer(help="Search and view security incidents")
console = Console()

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

STATUS_OPTION = typer.Option(None, "--status", "-s", help="Filter by status (open, closed, in_progress)")
SEVERITY_OPTION = typer.Option(None, "--severity", help="Filter by severity (critical, high, medium, low, informational)")
PRODUCT_OPTION = typer.Option(None, "--product", "-p", help="Filter by product name")
JSON_OPTION = typer.Option(False, "--json", "-j", help="Output as JSON")


# =============================================================================================================================================================================================
# INCIDENTS COMMANDS
# =============================================================================================================================================================================================

# ------------------------------------------------------------------------------------- list ------------------------------------------------------------------------------------


@app.command("list")
def list_incidents(
    status: str | None = STATUS_OPTION,
    severity: str | None = SEVERITY_OPTION,
    product: str | None = PRODUCT_OPTION,
    json_output: bool = JSON_OPTION,
):
    """Search security incidents with optional filters.

    Examples
    --------
    scm incidents list
    scm incidents list --status open --severity high
    scm incidents list --product "Prisma Access"
    scm incidents list --json

    """
    try:
        incidents = scm_client.list_incidents(
            status=status,
            severity=severity,
            product=product,
        )

        if json_output:
            typer.echo(json.dumps(incidents, indent=2))
            return

        if not incidents:
            typer.echo("No incidents found")
            return

        table = Table(title="Security Incidents")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Severity", style="white")
        table.add_column("Product", style="white")
        table.add_column("Summary", style="dim", max_width=40)
        table.add_column("Created", style="white")

        severity_styles = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "green", "informational": "dim"}

        for inc in incidents:
            sev = inc.get("severity", "")
            sev_style = severity_styles.get(sev, "white")
            status_val = inc.get("status", "")
            status_style = "green" if status_val == "closed" else ("yellow" if status_val == "in_progress" else "white")
            table.add_row(
                str(inc.get("id", "")),
                f"[{status_style}]{status_val}[/{status_style}]",
                f"[{sev_style}]{sev}[/{sev_style}]",
                str(inc.get("product", "")),
                str(inc.get("summary", "")),
                str(inc.get("created", "")),
            )

        console.print(table)

    except Exception as e:
        typer.echo(f"Error listing incidents: {e!s}", err=True)
        raise typer.Exit(code=1) from e


# ------------------------------------------------------------------------------------- show ------------------------------------------------------------------------------------


@app.command("show")
def show_incident(
    incident_id: str = typer.Argument(..., help="Incident ID to show"),
    json_output: bool = JSON_OPTION,
):
    """Show detailed incident information including alerts and remediation.

    Examples
    --------
    scm incidents show INC-2026-04-001
    scm incidents show INC-2026-04-001 --json

    """
    try:
        incident = scm_client.get_incident(incident_id=incident_id)

        if json_output:
            typer.echo(json.dumps(incident, indent=2))
            return

        typer.echo(f"\nIncident: {incident.get('id', incident_id)}")
        typer.echo(f"Status:   {incident.get('status', '')}")
        typer.echo(f"Severity: {incident.get('severity', '')}")
        typer.echo(f"Product:  {incident.get('product', '')}")
        typer.echo(f"Created:  {incident.get('created', '')}")
        typer.echo(f"Updated:  {incident.get('updated', '')}")
        typer.echo(f"Summary:  {incident.get('summary', '')}")

        alerts = incident.get("alerts", [])
        if alerts:
            typer.echo(f"\nAlerts ({len(alerts)}):")
            for i, alert in enumerate(alerts, 1):
                sev = alert.get("severity", "")
                desc = alert.get("description", "")
                ts = alert.get("timestamp", "")
                typer.echo(f"  {i}. [{sev}] {desc}   {ts}")

        remediation = incident.get("remediation", [])
        if remediation:
            typer.echo("\nRemediation:")
            for i, step in enumerate(remediation, 1):
                typer.echo(f"  {i}. {step}")

        typer.echo()

    except Exception as e:
        typer.echo(f"Error showing incident: {e!s}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 4: Register in main.py**

In `src/scm_cli/main.py`, update import:

```python
from .commands import commit, context, deployment, identity, incidents, insights, jobs, local, mobile_agent, network, objects, operations, posture, security, setup
```

Add to top-level commands (alphabetical, between `context` and `insights`):

```python
app.add_typer(incidents.app, name="incidents")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `poetry run pytest tests/test_incidents_commands.py -v`
Expected: All tests PASS

Run: `poetry run pytest -x -q`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/commands/incidents.py src/scm_cli/main.py tests/test_incidents_commands.py
git commit -m "feat: add scm incidents list and show commands"
```

---

### Task 15: Add incidents documentation and PR

**Files:**
- Create: `docs/cli/incidents/index.md`
- Modify: `mkdocs.yml`

- [ ] **Step 1: Create documentation page**

Create `docs/cli/incidents/index.md`:

```markdown
# Incidents

Search and view security incidents from the SCM Unified Incident Framework.

## Commands

### List Incidents

```bash
# List all incidents
scm incidents list

# Filter by status and severity
scm incidents list --status open --severity high

# Filter by product
scm incidents list --product "Prisma Access"

# JSON output for automation
scm incidents list --json
```

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--status`, `-s` | No | Filter: open, closed, in_progress |
| `--severity` | No | Filter: critical, high, medium, low, informational |
| `--product`, `-p` | No | Filter by product name |
| `--json`, `-j` | No | Output as JSON |

### Show Incident Detail

```bash
scm incidents show INC-2026-04-001
scm incidents show INC-2026-04-001 --json
```

Shows full incident detail including alerts and remediation steps. Use `--json` for the complete structured output.

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `incident_id` | Yes | Incident ID to show |

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--json`, `-j` | No | Output as JSON |
```

- [ ] **Step 2: Add to mkdocs.yml nav**

Add after "Operations" in the nav:

```yaml
      - Incidents:
          - Overview: cli/incidents/index.md
```

- [ ] **Step 3: Verify docs build**

Run: `poetry run mkdocs build --strict 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Run full quality gate**

Run: `make quality`
Expected: All checks pass

- [ ] **Step 5: Commit and create PR**

```bash
git add docs/cli/incidents/index.md mkdocs.yml
git commit -m "docs: add incidents command documentation"
git push -u origin cdot65/incidents-commands
gh pr create --title "feat: add scm incidents commands for security incident management" --body "$(cat <<'EOF'
## Summary
- Add `scm incidents list` with filtering by status, severity, product
- Add `scm incidents show <id>` with alerts and remediation detail
- `--json` flag on both commands for automation
- Severity-colored table output
- Mock mode support

Closes #215

## Test plan
- [ ] `scm incidents list` shows incident table
- [ ] `scm incidents list --status open` filters correctly
- [ ] `scm incidents list --json` outputs valid JSON
- [ ] `scm incidents show INC-2026-04-001` shows detail with alerts and remediation
- [ ] `scm incidents show INC-2026-04-001 --json` outputs full JSON
- [ ] All tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Summary

| Task | PR | What |
|------|----|------|
| 1 | 1 | Bump SDK to ^0.13.0 |
| 2 | 1 | Add region to context storage |
| 3 | 1 | Add --region to context create CLI |
| 4 | 1 | Global --region flag + auth config plumbing |
| 5 | 1 | Handle JobTimeoutError |
| 6 | 1 | Quality gate + PR |
| 7 | 2 | SDK client methods for local config |
| 8 | 2 | Local command module + registration |
| 9 | 2 | Docs + PR |
| 10 | 3 | SDK client methods for device operations |
| 11 | 3 | Operations command module + registration |
| 12 | 3 | Docs + PR |
| 13 | 4 | SDK client methods for incidents |
| 14 | 4 | Incidents command module + registration |
| 15 | 4 | Docs + PR |
