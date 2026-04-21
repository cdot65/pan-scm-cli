# Device Label Support (and Writable Fields) — Design

**Date:** 2026-04-21
**Status:** Approved — ready for implementation plan
**Depends on:** `pan-scm-sdk >= 0.14.0` (adds device PUT with writable fields)

## Context

`pan-scm-cli` currently treats devices as read-only (`scm show setup device` only). The SDK v0.14.0 release adds device PUT support with five writable fields: `display_name`, `folder`, `description`, `labels`, `snippets`. Devices cannot be created or deleted via the API — they register themselves through firewall registration — so PUT-with-merge is the only write path.

Folders and snippets already expose labels via `--labels` on their `scm set setup ...` commands (pattern at [commands/setup.py:161-202](../../../src/scm_cli/commands/setup.py)). This spec brings devices to the same surface area, except without create/delete.

## Goals

- Let users attach/detach labels on existing devices via CLI.
- Expose the other four writable fields (`display_name`, `folder`, `description`, `snippets`) in the same command since they share one PUT.
- Provide YAML bulk-load and backup for devices, matching folder/snippet ergonomics.
- Preserve the smart-upsert diff/`__action__` pattern so `no_change` / `updated` feedback is consistent.

## Non-goals

- Device create or delete (SDK does not support).
- Label-application to resources other than folder, snippet, device.
- Renaming a device (name is the lookup key; not in the writable set).
- Changing the existing `scm show setup device` field structure beyond appending writable fields.

## Command surface

| Command                                  | Behavior                                                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| `scm set setup device --name X [...]`    | Update writable fields on an existing device. Errors if device not found.                 |
| `scm show setup device [--name X]`       | Unchanged entry point; detail + list output extended to show writable fields.             |
| `scm load setup device --file devices.yaml` | Apply YAML batch of device updates. `--dry-run` prints without calling SDK.            |
| `scm backup setup device [--file ...]`   | Dump all devices (read-only + writable fields) to YAML, stripping `id`.                   |
| `scm delete setup device`                | **Not implemented** — SDK has no delete path; surfacing the command would mislead users. |

Flags on `scm set setup device`:

- `--name` (required) — device name or serial number (lookup key).
- `--display-name` — new display name.
- `--folder` — move the device into a different folder.
- `--description` — free-text description.
- `--labels` — repeatable; replaces the label set (matches folder/snippet semantics).
- `--snippets` — repeatable; replaces the snippet set.

Omitting a flag preserves the current value on the device.

## Data model

New class in [src/scm_cli/utils/validators.py](../../../src/scm_cli/utils/validators.py), placed near `Folder`/`Label`/`Snippet`:

```python
class Device(BaseModel):
    """Model for device configurations (update-only — devices cannot be created or deleted)."""

    model_config = ConfigDict(extra="ignore")  # tolerate read-only fields in YAML backups

    name: str = Field(..., description="Name or serial number of the device (lookup key)")
    display_name: str | None = Field(None, description="Display name for the device")
    folder: str | None = Field(None, description="Folder to move the device into")
    description: str | None = Field(None, description="Description of the device")
    labels: list[str] | None = Field(None, description="Labels to apply to the device")
    snippets: list[str] | None = Field(None, description="Snippet IDs to associate with the device")

    def to_sdk_model(self) -> dict[str, Any]:
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

**Why `extra="ignore"`**: `scm backup setup device` dumps read-only fields (`serial_number`, `model`, `hostname`, `is_connected`, `uptime`, `software_version`, `family`, `ip_address`, `id`) into the YAML. `scm load setup device` must accept that YAML unchanged without validation errors. Ignored extras never reach `to_sdk_model()`, so read-only fields are not sent to PUT.

**Why `None` = preserve**: matches the `create_folder` smart-upsert pattern at [sdk_client.py:11090-11194](../../../src/scm_cli/utils/sdk_client.py). `None` means "do not touch this field." An explicit empty list means "clear the field."

## SDK client method

New `update_device` method in [src/scm_cli/utils/sdk_client.py](../../../src/scm_cli/utils/sdk_client.py), placed immediately after `list_devices` (~line 11946). Structure mirrors `create_folder` with three key differences: it never creates, it raises a dedicated error on miss, and the "no_change" branch is still reachable.

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

    Returns the device object with a '__action__' key set to
    'updated' or 'no_change'.
    """
    self.logger.info(f"Update device: {name}")

    if not self.client:
        return {
            "id": f"device-{name}",
            "name": name,
            "display_name": display_name or name,
            "folder": folder or "Texas",
            "description": description or "",
            "labels": labels or [],
            "snippets": snippets or [],
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
            current = set(getattr(existing, "labels", []) or [])
            if current != set(labels):
                existing.labels = labels
                update_fields.append("labels")
                needs_update = True

        if snippets is not None:
            current = set(getattr(existing, "snippets", []) or [])
            if current != set(snippets):
                existing.snippets = snippets
                update_fields.append("snippets")
                needs_update = True

        if needs_update:
            self.logger.info(f"Updating device fields: {', '.join(update_fields)}")
            updated = self.client.device.update(existing)
            result = json.loads(updated.model_dump_json(exclude_unset=True))
            result["__action__"] = "updated"
            return result

        result = json.loads(existing.model_dump_json(exclude_unset=True))
        result["__action__"] = "no_change"
        return result

    except Exception as e:
        self._handle_api_exception("update", "N/A", name, e)
```

Also update the mock-mode payloads in `get_device` ([sdk_client.py:11871](../../../src/scm_cli/utils/sdk_client.py)) and `list_devices` ([sdk_client.py:11906](../../../src/scm_cli/utils/sdk_client.py)) to include `display_name`, `description`, `labels`, `snippets`. This lets `scm --mock show/backup setup device` exercise the new fields end-to-end.

## CLI commands

Edits to [src/scm_cli/commands/setup.py](../../../src/scm_cli/commands/setup.py):

1. **Import** `Device` from `..utils.validators` at line 16.
2. **New options** near the existing device section (~line 985):

```python
DISPLAY_NAME_OPTION = typer.Option(None, "--display-name", help="Display name for the device")
DEVICE_FOLDER_OPTION = typer.Option(None, "--folder", help="Folder to move the device into")
```

   `DEVICE_FOLDER_OPTION` is distinct from the existing `FOLDER_OPTION` (variable-scoping). Naming them separately avoids confusing semantics.

3. **`set_device` command** — standard shape matching `set_folder`, but with `update_device` and two output states (`updated`, `no_change`).

4. **`load_device` command** — mirrors `load_folder`: reads YAML, iterates entries, calls `update_device` per device. `--dry-run` prints the parsed YAML without SDK calls.

5. **`backup_device` command** — mirrors `backup_folder`: calls `list_devices`, strips `id`, writes YAML with `devices:` key.

6. **Extend `show_device`** at [setup.py:989-1053](../../../src/scm_cli/commands/setup.py) to print `display_name`, `description`, `labels`, `snippets` when present. List-mode adds a single `Labels:` line per device when labels exist.

(Full code snippets are in the brainstorming transcript; implementation plan will restate them.)

## Error handling

| Scenario                                   | Behavior                                                                                   |
| ------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Device not found on `set`/`load`           | SDK raises `ValueError` with clear message; command prints to stderr and exits 1.          |
| Invalid YAML structure                     | `load_from_yaml` raises; existing catch block prints and exits 1.                          |
| Pydantic validation failure                | `ValidationError` caught, stderr, exit 1 (matches existing pattern).                       |
| YAML contains read-only fields             | `ConfigDict(extra="ignore")` silently drops them. No warning (intentional).                |
| Empty `--labels` (explicit)                | Passes `[]` to SDK → clears labels. Matches folder/snippet behavior.                       |
| Unknown label name                         | Not pre-validated; SDK/API rejects with server error, bubbled through `_handle_api_exception`. |
| Dry-run                                    | `load_device --dry-run` prints parsed YAML, never calls SDK.                               |

## Testing

New tests in [tests/test_setup_commands.py](../../../tests/test_setup_commands.py):

- **`TestDeviceCommands`** class:
  - `test_set_device_with_labels` — asserts `update_device` called with correct labels, stdout contains "Updated device".
  - `test_set_device_no_change` — `__action__="no_change"` path; stdout matches.
  - `test_set_device_not_found` — mocked `ValueError`; typer exits 1; stderr mentions "not found".
  - `test_set_device_all_fields` — passes all five writable fields; asserts full payload.
  - `test_show_device_displays_labels` — `get_device` mock includes labels; stdout shows them.
  - `test_load_device` — YAML fixture with multiple entries; all processed.
  - `test_load_device_dry_run` — no SDK call; stdout shows parsed YAML.
  - `test_backup_device` — writes tmp file; asserts YAML structure and `id` absence.

- **Device validator tests**:
  - `test_device_model_minimal` — `Device(name="X")` → `{"name": "X"}`.
  - `test_device_model_all_fields` — full round-trip.
  - `test_device_model_ignores_extras` — extras in input do not appear in `to_sdk_model()`.

- **SDK client tests** (in [tests/test_sdk_client.py](../../../tests/test_sdk_client.py) or the nearest equivalent):
  - `test_update_device_mock_mode` — no client; returns `__action__="updated"`.
  - `test_update_device_not_found_raises` — `NotFoundError` → `ValueError`.
  - `test_update_device_no_change_when_values_match` — existing fields match args; returns `no_change`.

- **Fixture**: `tests/data/devices.yaml` with 2-3 entries exercising labels, snippets, description.

All tests use the existing `mock_scm_client` fixture. No network calls, no real SDK.

## Documentation

- **New page** `docs/cli/setup/device.md`, following [docs/cli/setup/label.md](../../../docs/cli/setup/label.md) structure. Must reflect the `docs-style` skill conventions.
  - Overview note: "Devices are update-only. Create and delete are not supported."
  - Subsections: `set`, `show`, `load`, `backup`.
  - Writable-fields table: name, display_name, folder, description, labels, snippets.
  - YAML format example for bulk load/backup.
  - Cross-references to label, folder, snippet pages.

- **`docs/cli/setup/label.md`** — add a "Using labels" section with three copyable examples (folder, snippet, device) linking to each page. Closes the doc-asymmetry gap noted in the CLI review.

- **Setup index** — update any TOC at `docs/cli/setup/index.md` (or equivalent) to list device alongside folder/snippet/label/variable.

## Dependency bump

- `pyproject.toml` — `pan-scm-sdk>=0.14.0` (from `>=0.13.0`).
- Verify any pinned versions in `requirements*.txt` or lock files.

## Changeset

New file `.changeset/0000-device-label-support.md`:

```md
---
"pan-scm-cli": minor
---

Add `scm set/show/load/backup setup device` commands for updating device labels, display name, folder, description, and snippets. Devices remain uncreatable — they must be registered via firewall registration.
```

## Version bump

Minor bump: `1.3.5` → `1.4.0`. New user-visible commands justify minor per semver.

## Out of scope / follow-ups

- Label-based filtering on `scm show setup device` (e.g., `--label production`). Deferrable; add if users ask.
- Label application on resources other than folder/snippet/device (e.g., security rules). Awaits SDK support.
- `scm set setup label --color` — labels here are simpler than tags; no color field in SDK.

## Unresolved questions

- None — all design decisions locked in during brainstorming.
