# Device Label Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `scm set/show/load/backup setup device` commands that expose the five writable device fields (display_name, folder, description, labels, snippets) landed in pan-scm-sdk 0.14.0.

**Architecture:** Follow the existing folder/snippet/label pattern: a Pydantic validator (`Device`), an SDK client wrapper method (`update_device`) with smart-upsert-style change tracking, Typer commands registered on `set_app`/`show_app`/`load_app`/`backup_app`, plus documentation and a changeset. No create/delete surface — devices are update-only.

**Tech Stack:** Python 3.10+, Pydantic 2.x, Typer, pytest, Poetry, pan-scm-sdk 0.14.0, MkDocs Material.

**Spec reference:** [docs/superpowers/specs/2026-04-21-device-label-support-design.md](../specs/2026-04-21-device-label-support-design.md)

---

## Task 1: Bump SDK dependency to 0.14.0

**Files:**
- Modify: `pyproject.toml:14` (dependency pin)
- Regenerate: `poetry.lock`

- [ ] **Step 1: Update the version constraint**

Edit [pyproject.toml](../../../pyproject.toml) line 14:

```toml
pan-scm-sdk = "^0.14.0"
```

(Was `"^0.13.0"`.)

- [ ] **Step 2: Update the lock file and install**

Run:

```bash
poetry lock --no-update
poetry install
```

Expected: lock file refreshes, `pan-scm-sdk 0.14.x` is installed. If `poetry lock --no-update` fails because of dependency resolution, fall back to `poetry lock`.

- [ ] **Step 3: Verify the installed version**

Run:

```bash
poetry run python -c "import scm; print(scm.__version__ if hasattr(scm, '__version__') else 'no __version__'); from scm.client import ScmClient; print('device.update attr:', hasattr(ScmClient, 'device'))"
```

Expected: no import errors. If `scm` exposes `__version__`, it reads 0.14.x.

- [ ] **Step 4: Run the existing test suite to confirm nothing regressed**

Run:

```bash
poetry run pytest -x --ignore=tests/test_sdk_client_with_dynaconf.py 2>&1 | tail -40
```

Expected: all tests pass (or same pre-existing failures — note any and proceed).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "chore: bump pan-scm-sdk to ^0.14.0 for device label support"
```

---

## Task 2: Add `Device` Pydantic validator

**Files:**
- Modify: `src/scm_cli/utils/validators.py` (add class near Folder/Label/Snippet, ~line 4265)
- Modify: `tests/test_setup_commands.py` (add tests inside `TestSetupValidators` class, ~line 373)

- [ ] **Step 1: Write failing validator tests**

Append to the `TestSetupValidators` class in [tests/test_setup_commands.py](../../../tests/test_setup_commands.py) (place after the existing `test_snippet_with_enable_prefix` test at the same indentation level):

```python
    def test_device_minimal(self):
        from scm_cli.utils.validators import Device
        device = Device(name="PA-VM-01")
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01"}

    def test_device_all_fields(self):
        from scm_cli.utils.validators import Device
        device = Device(
            name="PA-VM-01",
            display_name="Edge-FW",
            folder="Austin",
            description="Edge firewall",
            labels=["production", "west"],
            snippets=["DNS-Best-Practice"],
        )
        sdk = device.to_sdk_model()
        assert sdk["name"] == "PA-VM-01"
        assert sdk["display_name"] == "Edge-FW"
        assert sdk["folder"] == "Austin"
        assert sdk["description"] == "Edge firewall"
        assert sdk["labels"] == ["production", "west"]
        assert sdk["snippets"] == ["DNS-Best-Practice"]

    def test_device_ignores_read_only_extras(self):
        from scm_cli.utils.validators import Device
        device = Device(
            name="PA-VM-01",
            labels=["prod"],
            serial_number="0123456789",
            model="PA-VM",
            hostname="pa-vm-01",
            is_connected=True,
            id="device-uuid",
        )
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01", "labels": ["prod"]}

    def test_device_empty_labels_list_passes_through(self):
        from scm_cli.utils.validators import Device
        device = Device(name="PA-VM-01", labels=[])
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01", "labels": []}

    def test_device_requires_name(self):
        from scm_cli.utils.validators import Device
        with pytest.raises(ValidationError):
            Device()
```

- [ ] **Step 2: Run the new tests — they must fail**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestSetupValidators -v 2>&1 | tail -20
```

Expected: 5 failures with `ImportError: cannot import name 'Device' from 'scm_cli.utils.validators'` (or equivalent AttributeError).

- [ ] **Step 3: Add the `Device` class**

Insert at [src/scm_cli/utils/validators.py](../../../src/scm_cli/utils/validators.py), immediately after the `Label` class (locate via `grep -n "^class Label" src/scm_cli/utils/validators.py` — place the new class between `Label` and `Snippet`):

```python
class Device(BaseModel):
    """Model for device configurations (update-only — devices cannot be created or deleted)."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Name or serial number of the device (lookup key)")
    display_name: str | None = Field(None, description="Display name for the device")
    folder: str | None = Field(None, description="Folder to move the device into")
    description: str | None = Field(None, description="Description of the device")
    labels: list[str] | None = Field(None, description="Labels to apply to the device")
    snippets: list[str] | None = Field(None, description="Snippet IDs to associate with the device")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format.

        Only includes fields whose value is not None. `None` means "preserve the
        existing value on the device"; an explicit empty list clears the field.
        """
        data: dict[str, Any] = {"name": self.name}
        if self.display_name is not None:
            data["display_name"] = self.display_name
        if self.folder is not None:
            data["folder"] = self.folder
        if self.description is not None:
            data["description"] = self.description
        if self.labels is not None:
            data["labels"] = self.labels
        if self.snippets is not None:
            data["snippets"] = self.snippets
        return data
```

(The `BaseModel`, `ConfigDict`, `Field`, and `Any` imports already exist at the top of the file.)

- [ ] **Step 4: Run the validator tests — they must pass**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestSetupValidators -v 2>&1 | tail -20
```

Expected: all existing + 5 new tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/validators.py tests/test_setup_commands.py
git commit -m "feat(validators): add Device pydantic model for update-only flow"
```

---

## Task 3: Add `update_device` SDK client method

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py` (new method after `list_devices`, ~line 11946)
- Modify: `tests/test_sdk_client.py` (new tests)

- [ ] **Step 1: Add tests for mock mode and not-found behavior**

Append to [tests/test_sdk_client.py](../../../tests/test_sdk_client.py) (place at the bottom of the file — review the file first to match import style; the existing file imports `scm_client` from `scm_cli.utils.sdk_client`):

```python
class TestUpdateDevice:
    """Tests for scm_client.update_device."""

    def test_update_device_mock_mode_returns_updated(self):
        from scm_cli.utils.sdk_client import SDKClient

        client = SDKClient()
        client.client = None  # force mock mode

        result = client.update_device(
            name="PA-VM-01",
            display_name="Edge-FW",
            labels=["prod"],
        )

        assert result["name"] == "PA-VM-01"
        assert result["display_name"] == "Edge-FW"
        assert result["labels"] == ["prod"]
        assert result["__action__"] == "updated"

    def test_update_device_not_found_raises_value_error(self, monkeypatch):
        from scm.exceptions import NotFoundError

        from scm_cli.utils.sdk_client import SDKClient

        client = SDKClient()

        class FakeDevice:
            @staticmethod
            def fetch(name):
                raise NotFoundError("not found")

            @staticmethod
            def update(*args, **kwargs):
                raise AssertionError("update must not be called on missing device")

        class FakeClient:
            device = FakeDevice()

        client.client = FakeClient()

        with pytest.raises(ValueError, match="cannot be created"):
            client.update_device(name="missing", labels=["prod"])

    def test_update_device_no_change_when_values_match(self, monkeypatch):
        from scm_cli.utils.sdk_client import SDKClient

        client = SDKClient()

        class FakeExisting:
            display_name = "Edge-FW"
            folder = "Austin"
            description = "edge"
            labels = ["prod"]
            snippets = []

            def model_dump_json(self, **_kw):
                return '{"name": "PA-VM-01", "display_name": "Edge-FW", "labels": ["prod"]}'

        class FakeDevice:
            @staticmethod
            def fetch(name):
                return FakeExisting()

            @staticmethod
            def update(*args, **kwargs):
                raise AssertionError("update must not be called when no change")

        class FakeClient:
            device = FakeDevice()

        client.client = FakeClient()

        result = client.update_device(
            name="PA-VM-01",
            display_name="Edge-FW",
            folder="Austin",
            description="edge",
            labels=["prod"],
        )
        assert result["__action__"] == "no_change"
```

Ensure `import pytest` is at the top of the test file (the existing file already has it — confirm before appending).

- [ ] **Step 2: Run the new tests — they must fail**

Run:

```bash
poetry run pytest tests/test_sdk_client.py::TestUpdateDevice -v 2>&1 | tail -25
```

Expected: 3 failures (`AttributeError: 'SDKClient' object has no attribute 'update_device'`).

- [ ] **Step 3: Add the `update_device` method**

Insert into [src/scm_cli/utils/sdk_client.py](../../../src/scm_cli/utils/sdk_client.py) immediately after `list_devices` (locate via `grep -n "def list_devices" src/scm_cli/utils/sdk_client.py` — insert after the final `return` of that method; preserve the `# Device (read-only)` comment block but you may rename the comment to `# Device`).

```python
    def update_device(
        self,
        name: str,
        display_name: str | None = None,
        folder: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        snippets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a device (smart update — devices cannot be created).

        Args:
            name: Name or serial number of the device (lookup key).
            display_name: New display name (None = preserve).
            folder: New folder (None = preserve).
            description: New description (None = preserve).
            labels: New label set — replaces existing (None = preserve, [] = clear).
            snippets: New snippet set — replaces existing (None = preserve, [] = clear).

        Returns:
            dict[str, Any]: Device payload with '__action__' = 'updated' | 'no_change'.

        Raises:
            ValueError: If the device is not found (devices cannot be created).

        """
        self.logger.info(f"Update device: {name}")

        if not self.client:
            return {
                "id": f"device-{name}",
                "name": name,
                "display_name": display_name if display_name is not None else name,
                "folder": folder if folder is not None else "Texas",
                "description": description if description is not None else "",
                "labels": labels if labels is not None else [],
                "snippets": snippets if snippets is not None else [],
                "__action__": "updated",
            }

        try:
            try:
                existing = self.client.device.fetch(name=name)
            except NotFoundError as e:
                raise ValueError(
                    f"Device '{name}' not found. Devices cannot be created via the CLI — "
                    "they must be registered by the firewall itself."
                ) from e

            needs_update = False
            update_fields: list[str] = []

            if display_name is not None and getattr(existing, "display_name", None) != display_name:
                existing.display_name = display_name
                update_fields.append("display_name")
                needs_update = True

            if folder is not None and getattr(existing, "folder", None) != folder:
                existing.folder = folder
                update_fields.append("folder")
                needs_update = True

            if description is not None and getattr(existing, "description", None) != description:
                existing.description = description
                update_fields.append("description")
                needs_update = True

            if labels is not None:
                current_labels = set(getattr(existing, "labels", []) or [])
                if current_labels != set(labels):
                    existing.labels = labels
                    update_fields.append("labels")
                    needs_update = True

            if snippets is not None:
                current_snippets = set(getattr(existing, "snippets", []) or [])
                if current_snippets != set(snippets):
                    existing.snippets = snippets
                    update_fields.append("snippets")
                    needs_update = True

            if needs_update:
                self.logger.info(f"Updating device fields: {', '.join(update_fields)}")
                updated = self.client.device.update(existing)
                result = json.loads(updated.model_dump_json(exclude_unset=True))
                result["__action__"] = "updated"
                return result

            self.logger.info(f"No changes detected for device '{name}', skipping update")
            result = json.loads(existing.model_dump_json(exclude_unset=True))
            result["__action__"] = "no_change"
            return result

        except ValueError:
            raise
        except Exception as e:
            self._handle_api_exception("update", "N/A", name, e)
```

Note: `ValueError` is re-raised unchanged so the "not found" message surfaces cleanly; all other exceptions flow through the standard `_handle_api_exception`.

- [ ] **Step 4: Run the tests — they must pass**

Run:

```bash
poetry run pytest tests/test_sdk_client.py::TestUpdateDevice -v 2>&1 | tail -20
```

Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_sdk_client.py
git commit -m "feat(sdk-client): add update_device with smart diff and not-found guard"
```

---

## Task 4: Update mock payloads for `get_device` and `list_devices`

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py` (`get_device` ~line 11871, `list_devices` ~line 11906)

These methods already exist but their mock responses do not include the new writable fields. We extend them so that `scm --mock show setup device` and `scm --mock backup setup device` surface the new data end-to-end.

- [ ] **Step 1: Update the `get_device` mock payload**

Locate the `if not self.client:` block inside `get_device` (grep: `grep -n "def get_device" src/scm_cli/utils/sdk_client.py`). Replace the returned dict with:

```python
            return {
                "id": f"device-{name}",
                "name": name,
                "display_name": f"{name} (display)",
                "hostname": name,
                "serial_number": "0123456789",
                "model": "PA-VM",
                "family": "vm",
                "folder": "Texas",
                "description": f"Mock device {name}",
                "labels": ["production"],
                "snippets": ["DNS-Best-Practice"],
                "software_version": "11.1.0",
                "is_connected": True,
                "uptime": "30 days",
            }
```

- [ ] **Step 2: Update the `list_devices` mock payload**

Locate the `if not self.client:` block inside `list_devices`. Replace both device entries with:

```python
            return [
                {
                    "id": "device-fw1",
                    "name": "PA-VM-01",
                    "display_name": "Edge-FW-01",
                    "hostname": "pa-vm-01",
                    "serial_number": "0123456789",
                    "model": "PA-VM",
                    "family": "vm",
                    "folder": folder or "Texas",
                    "description": "Edge firewall 1",
                    "labels": ["production", "west"],
                    "snippets": ["DNS-Best-Practice"],
                    "software_version": "11.1.0",
                    "is_connected": True,
                },
                {
                    "id": "device-fw2",
                    "name": "PA-VM-02",
                    "display_name": "Edge-FW-02",
                    "hostname": "pa-vm-02",
                    "serial_number": "9876543210",
                    "model": "PA-VM",
                    "family": "vm",
                    "folder": folder or "Texas",
                    "description": "Edge firewall 2",
                    "labels": ["staging"],
                    "software_version": "11.1.0",
                    "is_connected": False,
                },
            ]
```

- [ ] **Step 3: Smoke-test mock mode**

Run:

```bash
poetry run scm --mock show setup device --name PA-VM-01 2>&1 | tail -20
```

Expected: output shows the device (fields like Serial Number, Model, etc. print; the new fields — display_name, description, labels, snippets — will not appear until Task 6 extends `show_device`). No tracebacks.

- [ ] **Step 4: Run the existing device tests to confirm nothing broke**

Run:

```bash
poetry run pytest tests/test_setup_commands.py -k "device" -v 2>&1 | tail -20
```

Expected: any existing device tests still pass (likely none currently beyond `show_device`).

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py
git commit -m "feat(sdk-client): enrich device mock payloads with writable fields"
```

---

## Task 5: Add `set_device` CLI command

**Files:**
- Modify: `src/scm_cli/commands/setup.py` (import, new options, new command near line 985)
- Modify: `tests/test_setup_commands.py` (new `TestDeviceCommands` class)

- [ ] **Step 1: Write failing tests for `set_device`**

Append a new class to [tests/test_setup_commands.py](../../../tests/test_setup_commands.py). Also update the import line at the top to include `set_device` and `Device`:

Top of file — change the existing `from scm_cli.commands.setup import (...)` block to also import `set_device`, and add `Device` to the validator import:

```python
from scm_cli.commands.setup import (
    backup_app,
    delete_app,
    delete_folder,
    delete_label,
    delete_snippet,
    delete_variable,
    load_app,
    set_app,
    set_device,
    set_folder,
    set_label,
    set_snippet,
    set_variable,
    show_app,
    show_device,
    show_folder,
    show_label,
    show_snippet,
    show_variable,
)
from scm_cli.utils.validators import Device, Folder, Label, Snippet, Variable
```

Append this class at the bottom of the file (outside any other class):

```python
class TestDeviceCommands:
    """Test device commands."""

    def test_set_device_updates_labels(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_update(**kwargs):
            captured.update(kwargs)
            return {
                "id": "device-PA-VM-01",
                "name": kwargs.get("name"),
                "labels": kwargs.get("labels", []),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(
            test_app,
            ["--name", "PA-VM-01", "--labels", "production", "--labels", "west"],
        )

        assert result.exit_code == 0, result.stdout
        assert "Updated device" in result.stdout
        assert captured["name"] == "PA-VM-01"
        assert captured["labels"] == ["production", "west"]

    def test_set_device_all_fields(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_update(**kwargs):
            captured.update(kwargs)
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(
            test_app,
            [
                "--name", "PA-VM-01",
                "--display-name", "Edge-FW",
                "--folder", "Austin",
                "--description", "Edge firewall",
                "--labels", "production",
                "--snippets", "DNS-Best-Practice",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert captured["display_name"] == "Edge-FW"
        assert captured["folder"] == "Austin"
        assert captured["description"] == "Edge firewall"
        assert captured["labels"] == ["production"]
        assert captured["snippets"] == ["DNS-Best-Practice"]

    def test_set_device_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(**kwargs):
            return {"name": kwargs["name"], "__action__": "no_change"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(test_app, ["--name", "PA-VM-01", "--labels", "production"])

        assert result.exit_code == 0, result.stdout
        assert "No changes detected" in result.stdout

    def test_set_device_not_found_exits_nonzero(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(**kwargs):
            raise ValueError("Device 'missing' not found. Devices cannot be created via the CLI.")

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(test_app, ["--name", "missing", "--labels", "x"])

        assert result.exit_code != 0
        # stderr + stdout merged in CliRunner by default
        combined = (result.stdout or "") + (result.stderr or "")
        assert "not found" in combined
```

- [ ] **Step 2: Run the new tests — they must fail**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v 2>&1 | tail -20
```

Expected: `ImportError: cannot import name 'set_device' from 'scm_cli.commands.setup'`.

- [ ] **Step 3: Add the options and command**

In [src/scm_cli/commands/setup.py](../../../src/scm_cli/commands/setup.py):

**(a) Extend the validator import** on line 16:

```python
from ..utils.validators import Device, Folder, Label, Snippet, Variable
```

**(b) Add two new options.** Locate the existing `# DEVICE COMMANDS (READ-ONLY)` section (around line 985) and rename the banner comment to `# DEVICE COMMANDS`. Immediately under the banner (before `@show_app.command("device")`), add:

```python
DISPLAY_NAME_OPTION = typer.Option(
    None,
    "--display-name",
    help="Display name for the device",
)
DEVICE_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder to move the device into",
)
```

**(c) Add `set_device`.** Place it immediately after `show_device` (at the end of the current device section):

```python
@set_app.command("device")
def set_device(
    name: str = NAME_OPTION,
    display_name: str | None = DISPLAY_NAME_OPTION,
    folder: str | None = DEVICE_FOLDER_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    snippets: list[str] | None = SNIPPETS_OPTION,
):
    """Update a device's writable fields (device must already exist).

    Devices cannot be created or deleted via the CLI — they are registered by
    the firewall itself. Use this command to update display_name, folder,
    description, labels, and/or snippets on an existing device.

    Examples
    --------
        scm set setup device --name PA-VM-01 --labels production --labels west
        scm set setup device --name 0123456789 --folder Austin
        scm set setup device --name PA-VM-01 --description "Edge firewall"

    """
    try:
        device_model = Device(
            name=name,
            display_name=display_name,
            folder=folder,
            description=description,
            labels=labels,
            snippets=snippets,
        )
        result = scm_client.update_device(**device_model.to_sdk_model())

        action = result.get("__action__", "updated")
        if action == "no_change":
            typer.echo(f"No changes detected for device: {name}")
        else:
            typer.echo(f"Updated device: {name}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error updating device: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 4: Run the tests — they must pass**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v 2>&1 | tail -20
```

Expected: 4 tests pass.

- [ ] **Step 5: Smoke-test in mock mode**

Run:

```bash
poetry run scm --mock set setup device --name PA-VM-01 --labels production --labels west 2>&1 | tail -5
```

Expected: `Updated device: PA-VM-01`.

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/commands/setup.py tests/test_setup_commands.py
git commit -m "feat(setup): add 'scm set setup device' for writable device fields"
```

---

## Task 6: Extend `show_device` to display writable fields

**Files:**
- Modify: `src/scm_cli/commands/setup.py` (within existing `show_device` at ~line 989)
- Modify: `tests/test_setup_commands.py` (add tests to `TestDeviceCommands`)

- [ ] **Step 1: Write failing show tests**

Append to the `TestDeviceCommands` class you created in Task 5:

```python
    def test_show_device_detail_includes_writable_fields(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(name):
            return {
                "id": "device-PA-VM-01",
                "name": name,
                "display_name": "Edge-FW",
                "hostname": "pa-vm-01",
                "serial_number": "0123456789",
                "model": "PA-VM",
                "folder": "Austin",
                "description": "Edge firewall",
                "labels": ["production", "west"],
                "snippets": ["DNS-Best-Practice"],
                "is_connected": True,
            }

        monkeypatch.setattr(scm_client, "get_device", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, ["--name", "PA-VM-01"])

        assert result.exit_code == 0, result.stdout
        assert "Display Name: Edge-FW" in result.stdout
        assert "Description: Edge firewall" in result.stdout
        assert "Labels: production, west" in result.stdout
        assert "Snippets: DNS-Best-Practice" in result.stdout

    def test_show_device_list_shows_labels(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(folder=None):
            return [
                {
                    "id": "d1",
                    "name": "PA-VM-01",
                    "labels": ["production"],
                    "is_connected": True,
                },
            ]

        monkeypatch.setattr(scm_client, "list_devices", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0, result.stdout
        assert "PA-VM-01" in result.stdout
        assert "Labels: production" in result.stdout
```

- [ ] **Step 2: Run the new tests — they must fail**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v -k "show_device" 2>&1 | tail -20
```

Expected: 2 failures — assertion messages will indicate missing `Display Name:`, `Description:`, `Labels:`, or `Snippets:` strings.

- [ ] **Step 3: Extend the detail view in `show_device`**

In [src/scm_cli/commands/setup.py](../../../src/scm_cli/commands/setup.py), inside `show_device` (~line 1005), the block currently looks like:

```python
            device = scm_client.get_device(name=name)

            typer.echo(f"\nDevice: {device.get('name', device.get('hostname', 'N/A'))}")
            typer.echo("=" * 80)
            if device.get("serial_number"):
                typer.echo(f"Serial Number: {device['serial_number']}")
            if device.get("model"):
                typer.echo(f"Model: {device['model']}")
            ...
```

Add four new field prints. Place them right after the existing `if device.get("hostname"):` block, so the new info comes before IP / folder:

```python
            if device.get("display_name"):
                typer.echo(f"Display Name: {device['display_name']}")
            if device.get("description"):
                typer.echo(f"Description: {device['description']}")
            if device.get("labels"):
                typer.echo(f"Labels: {', '.join(device['labels'])}")
            if device.get("snippets"):
                typer.echo(f"Snippets: {', '.join(device['snippets'])}")
```

- [ ] **Step 4: Extend the list view**

In the same `show_device` function, locate the `for d in devices:` loop (~line 1038). After the existing `if d.get("folder"):` line, add:

```python
                if d.get("labels"):
                    typer.echo(f"  Labels: {', '.join(d['labels'])}")
```

- [ ] **Step 5: Run the tests — they must pass**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v 2>&1 | tail -20
```

Expected: all 6 TestDeviceCommands tests pass.

- [ ] **Step 6: Smoke-test**

Run:

```bash
poetry run scm --mock show setup device --name PA-VM-01 2>&1 | tail -20
```

Expected: output now includes `Display Name: ...`, `Description: ...`, `Labels: production, west`, `Snippets: DNS-Best-Practice`.

- [ ] **Step 7: Commit**

```bash
git add src/scm_cli/commands/setup.py tests/test_setup_commands.py
git commit -m "feat(setup): show display_name, description, labels, snippets in show_device"
```

---

## Task 7: Add `load_device` CLI command

**Files:**
- Create: `tests/data/devices.yaml`
- Modify: `src/scm_cli/commands/setup.py` (new command at end of device section)
- Modify: `tests/test_setup_commands.py` (new tests in `TestDeviceCommands`)

- [ ] **Step 1: Create the test fixture**

Create [tests/data/devices.yaml](../../../tests/data/devices.yaml):

```yaml
devices:
  - name: PA-VM-01
    display_name: Edge-FW-01
    folder: Austin
    description: Edge firewall 1
    labels:
      - production
      - west
    snippets:
      - DNS-Best-Practice
  - name: PA-VM-02
    labels:
      - staging
    # Read-only fields below should be ignored by the Device validator:
    serial_number: "9876543210"
    model: PA-VM
    is_connected: false
```

- [ ] **Step 2: Write failing load tests**

Append to the `TestDeviceCommands` class:

```python
    def test_load_device_processes_all_entries(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import load_app
        from scm_cli.utils.sdk_client import scm_client

        captured_calls = []

        def mock_update(**kwargs):
            captured_calls.append(kwargs)
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        # Copy fixture into tmp_path for hermeticity
        import shutil
        from pathlib import Path
        fixture = Path(__file__).parent / "data" / "devices.yaml"
        target = tmp_path / "devices.yaml"
        shutil.copy(fixture, target)

        result = runner.invoke(load_app, ["device", "--file", str(target)])

        assert result.exit_code == 0, result.stdout
        assert len(captured_calls) == 2
        assert captured_calls[0]["name"] == "PA-VM-01"
        assert captured_calls[0]["labels"] == ["production", "west"]
        assert captured_calls[1]["name"] == "PA-VM-02"
        # Read-only fields must not reach the SDK call
        assert "serial_number" not in captured_calls[1]
        assert "is_connected" not in captured_calls[1]
        assert "Processed 2 devices" in result.stdout

    def test_load_device_dry_run_skips_sdk(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import load_app
        from scm_cli.utils.sdk_client import scm_client

        called = {"n": 0}

        def mock_update(**kwargs):
            called["n"] += 1
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        import shutil
        from pathlib import Path
        fixture = Path(__file__).parent / "data" / "devices.yaml"
        target = tmp_path / "devices.yaml"
        shutil.copy(fixture, target)

        result = runner.invoke(load_app, ["device", "--file", str(target), "--dry-run"])

        assert result.exit_code == 0, result.stdout
        assert called["n"] == 0
        assert "Dry run" in result.stdout
```

- [ ] **Step 3: Run the tests — they must fail**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v -k "load_device" 2>&1 | tail -20
```

Expected: command not registered on `load_app` — either "No such command" or an import/attribute error.

- [ ] **Step 4: Add `load_device`**

In [src/scm_cli/commands/setup.py](../../../src/scm_cli/commands/setup.py), append to the DEVICE COMMANDS section (after `set_device` from Task 5):

```python
@load_app.command("device")
def load_device(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load device updates from a YAML file.

    Devices must already exist — loading will error on any unknown device
    rather than creating one. Read-only fields in the YAML (serial_number,
    model, hostname, is_connected, etc.) are silently ignored.

    Example: scm load setup device --file devices.yaml
    """
    try:
        config = load_from_yaml(str(file), "devices")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["devices"]))
            return None

        results = []
        for device_data in config["devices"]:
            device_model = Device(**device_data)
            result = scm_client.update_device(**device_model.to_sdk_model())
            results.append(result)

            action = result.get("__action__", "updated")
            if action == "no_change":
                typer.echo(f"No changes for device: {device_model.name}")
            else:
                typer.echo(f"Updated device: {device_model.name}")

        typer.echo(f"\nProcessed {len(results)} devices from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading devices: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 5: Run the tests — they must pass**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v 2>&1 | tail -20
```

Expected: all 8 TestDeviceCommands tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/commands/setup.py tests/test_setup_commands.py tests/data/devices.yaml
git commit -m "feat(setup): add 'scm load setup device' for YAML batch updates"
```

---

## Task 8: Add `backup_device` CLI command

**Files:**
- Modify: `src/scm_cli/commands/setup.py` (new command at end of device section)
- Modify: `tests/test_setup_commands.py` (new tests in `TestDeviceCommands`)

- [ ] **Step 1: Write failing backup tests**

Append to the `TestDeviceCommands` class:

```python
    def test_backup_device_writes_yaml(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import backup_app
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(folder=None):
            return [
                {
                    "id": "device-PA-VM-01",
                    "name": "PA-VM-01",
                    "display_name": "Edge-FW",
                    "serial_number": "0123456789",
                    "labels": ["production"],
                },
                {
                    "id": "device-PA-VM-02",
                    "name": "PA-VM-02",
                    "labels": ["staging"],
                },
            ]

        monkeypatch.setattr(scm_client, "list_devices", mock_list)

        out_file = tmp_path / "device-backup.yaml"
        result = runner.invoke(backup_app, ["device", "--file", str(out_file)])

        assert result.exit_code == 0, result.stdout
        assert out_file.exists()

        import yaml
        data = yaml.safe_load(out_file.read_text())
        assert "devices" in data
        assert len(data["devices"]) == 2
        assert data["devices"][0]["name"] == "PA-VM-01"
        # id must be stripped
        assert "id" not in data["devices"][0]
        assert "id" not in data["devices"][1]
        # labels must round-trip
        assert data["devices"][0]["labels"] == ["production"]

    def test_backup_device_empty_returns_message(self, runner, monkeypatch):
        from scm_cli.commands.setup import backup_app
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_devices", lambda folder=None: [])

        result = runner.invoke(backup_app, ["device"])

        assert result.exit_code == 0
        assert "No devices found" in result.stdout
```

- [ ] **Step 2: Run the tests — they must fail**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v -k "backup_device" 2>&1 | tail -20
```

Expected: `Usage: ... No such command 'device'.` or equivalent.

- [ ] **Step 3: Add `backup_device`**

Append to [src/scm_cli/commands/setup.py](../../../src/scm_cli/commands/setup.py), after `load_device`:

```python
@backup_app.command("device")
def backup_device(
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all devices to a YAML file.

    Includes read-only fields (serial_number, model, hostname, etc.) for
    reference. Those fields are ignored on `scm load setup device`.

    Examples
    --------
        scm backup setup device
        scm backup setup device --file my-devices.yaml

    """
    if not file:
        file = get_default_backup_filename("devices")

    try:
        devices = scm_client.list_devices()

        if not devices:
            typer.echo("No devices found")
            return None

        backup_data = []
        for d in devices:
            d_dict = d.copy()
            d_dict.pop("id", None)
            backup_data.append(d_dict)

        yaml_data = {"devices": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} devices to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up devices: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

- [ ] **Step 4: Run the tests — they must pass**

Run:

```bash
poetry run pytest tests/test_setup_commands.py::TestDeviceCommands -v 2>&1 | tail -25
```

Expected: all 10 TestDeviceCommands tests pass.

- [ ] **Step 5: Run the full setup test file**

Run:

```bash
poetry run pytest tests/test_setup_commands.py -v 2>&1 | tail -20
```

Expected: all tests in the file pass.

- [ ] **Step 6: Smoke-test round-trip**

Run:

```bash
poetry run scm --mock backup setup device --file /tmp/device-backup.yaml && cat /tmp/device-backup.yaml && poetry run scm --mock load setup device --file /tmp/device-backup.yaml --dry-run
```

Expected: the YAML round-trips without validation errors; dry-run prints the parsed config.

- [ ] **Step 7: Commit**

```bash
git add src/scm_cli/commands/setup.py tests/test_setup_commands.py
git commit -m "feat(setup): add 'scm backup setup device' for YAML export"
```

---

## Task 9: Write device documentation page

**Files:**
- Create: `docs/cli/setup/device.md`

- [ ] **Step 1: Read the docs-style skill conventions**

Before writing, skim [.claude/STYLE_GUIDE.md](../../../.claude/STYLE_GUIDE.md) and the existing [docs/cli/setup/label.md](../../../docs/cli/setup/label.md). The docs-style skill requires: clear section ordering, admonitions for warnings, tables for fields, fenced code blocks with language hints, no emojis.

- [ ] **Step 2: Create the page**

Create [docs/cli/setup/device.md](../../../docs/cli/setup/device.md):

````markdown
# Device

Devices represent firewalls registered to Strata Cloud Manager. The CLI supports
**read and update** operations on devices; it does **not** support create or
delete. Devices enroll themselves through firewall-side registration — the CLI
cannot add or remove them.

!!! note "Update-only surface"
    `scm set setup device` updates existing devices. It errors if the named
    device does not exist. There is no `scm delete setup device`.

## Writable fields

| Field          | Flag              | Description                                      |
| -------------- | ----------------- | ------------------------------------------------ |
| `name`         | `--name`          | Lookup key (name or serial number). Required.    |
| `display_name` | `--display-name`  | Human-friendly display name.                     |
| `folder`       | `--folder`        | Folder to move the device into.                  |
| `description`  | `--description`   | Free-text description.                           |
| `labels`       | `--labels`        | Labels to apply. Repeatable; replaces current set. |
| `snippets`     | `--snippets`      | Snippet IDs to associate. Repeatable; replaces current set. |

Omitting a flag preserves the current value on the device. Passing an empty
value (e.g. `--labels ""`) is not supported; to clear a list field, use YAML
load with an empty list.

## Commands

### Update a device (`set`)

```bash
# Attach labels
scm set setup device --name PA-VM-01 --labels production --labels west

# Move into a folder
scm set setup device --name 0123456789 --folder Austin

# Set multiple fields at once
scm set setup device \
  --name PA-VM-01 \
  --display-name "Edge-FW" \
  --description "Edge firewall" \
  --labels production
```

If the named device does not exist, the command errors with a message
explaining that devices cannot be created via the CLI.

### Display devices (`show`)

```bash
# List all devices
scm show setup device

# Show a single device (by name or serial number)
scm show setup device --name PA-VM-01
scm show setup device --name 0123456789

# Filter by folder
scm show setup device --folder Texas
```

The detail view prints the writable fields (`display_name`, `description`,
`labels`, `snippets`) alongside read-only info (`serial_number`, `model`,
`hostname`, `software_version`, `is_connected`, `uptime`).

### Bulk-load updates (`load`)

```bash
scm load setup device --file devices.yaml
scm load setup device --file devices.yaml --dry-run
```

YAML format:

```yaml
devices:
  - name: PA-VM-01
    display_name: Edge-FW-01
    folder: Austin
    description: Edge firewall
    labels:
      - production
      - west
    snippets:
      - DNS-Best-Practice
  - name: PA-VM-02
    labels:
      - staging
```

Read-only fields present in the YAML (e.g. `serial_number`, `model`,
`is_connected`) are ignored — they are safe to leave in backups you edit and
reload.

### Back up devices (`backup`)

```bash
# Default filename: devices_YYYYMMDD_HHMMSS.yaml
scm backup setup device

# Custom filename
scm backup setup device --file my-devices.yaml
```

Backup dumps all devices (read-only and writable fields) except the SCM
identifier (`id`). The output is consumable by `scm load setup device`.

## Related

- [Labels](label.md) — create the labels you apply to devices.
- [Folders](folder.md) — folders that devices can be moved into.
- [Snippets](snippet.md) — snippets that can be attached to devices.
````

- [ ] **Step 3: Build the docs locally to check for broken links**

Run:

```bash
poetry run mkdocs build --strict 2>&1 | tail -20
```

Expected: build succeeds. If strict build fails because the new page isn't in the nav, edit `mkdocs.yml` to add it (see Task 10).

- [ ] **Step 4: Commit**

```bash
git add docs/cli/setup/device.md
git commit -m "docs(cli): add setup/device reference page"
```

---

## Task 10: Cross-reference label docs and update nav

**Files:**
- Modify: `docs/cli/setup/label.md` (add "Using labels on resources" section)
- Modify: `mkdocs.yml` (nav entry for device page)

- [ ] **Step 1: Locate the setup nav section in `mkdocs.yml`**

Run:

```bash
grep -n "setup/" /Users/cdot/development/cdot65/pan-scm-cli/mkdocs.yml | head -20
```

Expected: a list of `setup/<resource>.md` entries under a nav heading.

- [ ] **Step 2: Add device to the nav**

Open [mkdocs.yml](../../../mkdocs.yml), locate the `setup/` nav group, and add `- Device: cli/setup/device.md` in alphabetical position (after Configs or Devices-adjacent — match the existing ordering; the existing entries are likely sorted alphabetically).

- [ ] **Step 3: Add a "Using labels" section to `label.md`**

Open [docs/cli/setup/label.md](../../../docs/cli/setup/label.md). Append (before any final "Related" section, or at the bottom):

```markdown
## Using labels on resources

Labels can be applied to folders, snippets, and devices. Create the labels
first with `scm set setup label`, then attach them via each resource's
`--labels` flag:

```bash
# Folder
scm set setup folder --name Austin --parent Texas --labels production

# Snippet
scm set setup snippet --name Web-Security --labels production

# Device (must already exist)
scm set setup device --name PA-VM-01 --labels production --labels west
```

See [folder](folder.md), [snippet](snippet.md), and [device](device.md) for
full details on each command.
```

- [ ] **Step 4: Build docs in strict mode**

Run:

```bash
poetry run mkdocs build --strict 2>&1 | tail -20
```

Expected: success, no broken references.

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml docs/cli/setup/label.md
git commit -m "docs(cli): cross-reference label usage on folder/snippet/device"
```

---

## Task 11: Changeset and version bump

**Files:**
- Create: `.changeset/0001-device-label-support.md` (use next unused number — run `ls .changeset/` to check)
- Modify: `pyproject.toml` (version line)
- Modify: `src/scm_cli/__init__.py` if it contains a `__version__` (grep first)

- [ ] **Step 1: Confirm the changeset filename**

Run:

```bash
ls /Users/cdot/development/cdot65/pan-scm-cli/.changeset/ 2>/dev/null
```

Expected: a listing. Pick the next unused numeric prefix (e.g., `0001-`, `0002-`, …). If the directory doesn't exist, create it: `mkdir -p .changeset`.

- [ ] **Step 2: Create the changeset**

Create `.changeset/<NNNN>-device-label-support.md` (replace `<NNNN>` with the number chosen above):

```md
---
"pan-scm-cli": minor
---

Add device commands to manage writable fields landed in pan-scm-sdk 0.14.0: `scm set setup device`, `scm load setup device`, and `scm backup setup device`. Display writable fields (display_name, description, labels, snippets) in `scm show setup device`. Devices remain uncreatable and undeletable — they register through the firewall itself.
```

- [ ] **Step 3: Bump the version in pyproject.toml**

Edit [pyproject.toml](../../../pyproject.toml) line 3:

```toml
version = "1.4.0"
```

(Was `"1.3.5"`.)

- [ ] **Step 4: Check for a module-level `__version__`**

Run:

```bash
grep -rn "__version__" /Users/cdot/development/cdot65/pan-scm-cli/src/scm_cli/ | head -5
```

If any file defines `__version__ = "1.3.5"`, update it to `"1.4.0"`.

- [ ] **Step 5: Run the full quality gate**

Run:

```bash
make quality 2>&1 | tail -40
```

Expected: lint, format, mypy (if configured), and tests all pass. If anything fails, fix before committing.

- [ ] **Step 6: Run the full test suite end-to-end**

Run:

```bash
poetry run pytest -x 2>&1 | tail -20
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add .changeset/ pyproject.toml src/scm_cli/__init__.py 2>/dev/null
git commit -m "release: bump version to 1.4.0 for device label support"
```

(The `src/scm_cli/__init__.py` entry in `git add` is a no-op if the file has no `__version__`.)

---

## Task 12: Final verification & PR

**Files:** none (verification only)

- [ ] **Step 1: Verify git log**

Run:

```bash
git log --oneline main..HEAD
```

Expected: 10-11 commits for this feature, in order from Task 1 through Task 11.

- [ ] **Step 2: Run the full test suite**

Run:

```bash
poetry run pytest 2>&1 | tail -5
```

Expected: all tests pass, no skips introduced by this work.

- [ ] **Step 3: Docs build**

Run:

```bash
poetry run mkdocs build --strict 2>&1 | tail -10
```

Expected: success.

- [ ] **Step 4: Manual smoke-test in mock mode**

Run each of these and confirm output:

```bash
poetry run scm --mock show setup device
poetry run scm --mock show setup device --name PA-VM-01
poetry run scm --mock set setup device --name PA-VM-01 --labels production --labels west
poetry run scm --mock backup setup device --file /tmp/devices.yaml
cat /tmp/devices.yaml
poetry run scm --mock load setup device --file /tmp/devices.yaml --dry-run
poetry run scm --mock load setup device --file /tmp/devices.yaml
```

Expected: every command exits 0; `Labels: production, west` appears in the detail view; backup YAML contains both devices with labels; load processes both.

- [ ] **Step 5: Push branch and open PR**

```bash
git push -u origin HEAD
gh pr create --title "feat: device label support (pan-scm-sdk 0.14.0)" --body "$(cat <<'EOF'
## Summary
- Add `scm set/load/backup setup device` to expose the five writable device fields (display_name, folder, description, labels, snippets) landed in pan-scm-sdk 0.14.0.
- Extend `scm show setup device` to display the new fields in detail and list views.
- Devices remain uncreatable/undeletable via CLI — they register through firewall registration.
- Docs: new `docs/cli/setup/device.md`, label.md cross-references.

## Test plan
- [x] Unit tests for Device validator (5 cases)
- [x] Unit tests for update_device SDK method (3 cases)
- [x] Unit tests for set/show/load/backup device CLI commands (10+ cases)
- [x] Manual smoke-test in `--mock` mode round-trips (show → set → backup → load)
- [x] `make quality` passes
- [x] `mkdocs build --strict` passes

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR created. Print the URL.

---

## Self-review summary

Cross-checked plan against the spec:

| Spec section            | Task(s) that cover it     |
| ----------------------- | ------------------------- |
| Dependency on SDK 0.14.0 | Task 1                    |
| Data model (`Device`)    | Task 2                    |
| SDK client (`update_device`) | Task 3                |
| Mock payloads            | Task 4                    |
| `scm set setup device`   | Task 5                    |
| Extended `show_device`   | Task 6                    |
| `scm load setup device`  | Task 7                    |
| `scm backup setup device` | Task 8                   |
| Error handling           | Tasks 3, 5 (not-found, ValidationError paths tested) |
| Testing (validator, SDK, commands) | Tasks 2, 3, 5-8 |
| `docs/cli/setup/device.md` | Task 9                  |
| Label cross-references + nav | Task 10              |
| Changeset + version bump | Task 11                   |
| Final verification       | Task 12                   |

No placeholders. Names consistent across tasks (`update_device`, `set_device`, `load_device`, `backup_device`, `Device` class). All types and signatures defined before first use.
