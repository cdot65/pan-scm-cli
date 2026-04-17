# SDK 0.13.0 Upgrade & New Command Modules — Design Spec

**Date:** 2026-04-16
**GitHub Issues:** #212, #213, #214, #215
**SDK Version:** pan-scm-sdk 0.13.0 (April 2026)

---

## Summary

Upgrade pan-scm-sdk from ^0.12.2 to ^0.13.0 and add three new top-level CLI command groups wrapping the SDK's new services: `scm local` (device config versions), `scm operations` (device job dispatch/monitoring), and `scm incidents` (security incident search/detail). The work is structured as four sequential PRs with a shared foundation.

## PR Sequence

| Order | Issue | Branch | Scope |
|-------|-------|--------|-------|
| 1 | #212 | cdot65/sdk-013-foundation | SDK bump, region support, JobTimeoutError |
| 2 | #213 | cdot65/local-config-commands | `scm local` commands |
| 3 | #214 | cdot65/operations-commands | `scm operations` commands |
| 4 | #215 | cdot65/incidents-commands | `scm incidents` commands |

PRs 2-4 depend on PR 1 but are independent of each other.

---

## 1. Foundation (PR 1 — #212)

### SDK Dependency

```toml
# pyproject.toml
pan-scm-sdk = "^0.13.0"
```

### Region Support

**Context YAML schema** gains optional `region` field:

```yaml
# ~/.scm-cli/contexts/production.yaml
client_id: "abc123"
client_secret: "s3cret"
tsg_id: "123456789"
region: "europe"  # optional, defaults to "americas"
```

**Precedence:** global `--region` flag > context's stored region > `"americas"`

**Changes:**
- `commands/context.py`: Add `--region` option to `create` command (default "americas")
- `utils/context.py`: Store and read `region` field; `.get("region", "americas")` for backward compat
- `main.py`: Add global `--region` callback option on main app
- `client.py`: Pass `region=resolved_region` to `Scm()` constructor

### JobTimeoutError Handling

```python
# sdk_client.py — add to _handle_api_exception or as standalone handler
except JobTimeoutError as e:
    logger.error("Job %s timed out in state '%s'", e.job_id, e.last_state)
    typer.echo(
        f"Job {e.job_id} timed out (state: {e.last_state}). "
        f"Check with: scm operations status --job-id {e.job_id}",
        err=True,
    )
    raise typer.Exit(code=1)
```

### Tests

- Region stored in context create
- Region override via global flag
- Old contexts without region field default to "americas"
- JobTimeoutError produces correct error message with job_id and last_state
- All existing tests pass (0 regressions)

---

## 2. Local Config Commands (PR 2 — #213)

### New File: `src/scm_cli/commands/local.py`

**Subcommands:**
- `scm local list --device <name>` — table of config versions
- `scm local download --device <name> --version <id> [--output path]` — XML output

### Table Output (list)

```
Version   Date                 Author       Description
──────────────────────────────────────────────────────────
42        2026-04-15 14:30     admin        Policy update
41        2026-04-14 09:12     auto-commit  Scheduled push
40        2026-04-13 11:45     admin        Initial config
```

### Download Behavior

- No `--output`: decode XML as UTF-8, write to stdout
- With `--output`: write raw bytes to file, print confirmation to stderr

### SDK Client Methods

```python
def list_local_config_versions(self, device: str) -> list[dict]:
    """List configuration versions for a device."""

def download_local_config(self, device: str, version: int) -> bytes:
    """Download a configuration version as raw XML using raw_response=True."""
```

### Mock Mode

Returns 3-5 sample versions with realistic dates; download returns a small XML snippet.

### Registration

```python
# main.py — top-level, alphabetical
app.add_typer(local_app, name="local")
```

---

## 3. Device Operations Commands (PR 3 — #214)

### New File: `src/scm_cli/commands/operations.py`

**Subcommands (7 operation types + status):**

| Command | Operation |
|---------|-----------|
| `scm operations route-table --device <name>` | Retrieve routing table |
| `scm operations fib-table --device <name>` | Retrieve FIB table |
| `scm operations dns-proxy --device <name>` | DNS proxy status |
| `scm operations interfaces --device <name>` | Network interface status |
| `scm operations device-rules --device <name>` | Applied security rules |
| `scm operations bgp-export --device <name>` | BGP policy export |
| `scm operations logging-status --device <name>` | Logging service health |
| `scm operations status --job-id <id>` | Check job status |

**All operation commands share these options:**
- `--device` (required)
- `--async` (flag, default False) — return job ID without polling
- `--timeout` (int, default 300) — sync polling timeout in seconds
- `--mock` (flag)

### Sync Flow (default)

```
$ scm operations route-table --device fw-01
Dispatching route-table job for fw-01... ✓
Polling job abc-123... completed (42s)

Destination       Next Hop        Interface    Metric
──────────────────────────────────────────────────────
0.0.0.0/0         10.0.0.1        ethernet1/1  10
10.1.0.0/16       10.0.0.2        ethernet1/2  20
```

### Async Flow

```
$ scm operations route-table --device fw-01 --async
Job dispatched: abc-123
Check status with: scm operations status --job-id abc-123
```

### SDK Client Methods

```python
def dispatch_device_operation(self, device: str, operation: str, sync: bool = True, timeout: int = 300) -> dict:
    """Dispatch a device operation. Returns results if sync, job_id if async."""

def get_device_operation_status(self, job_id: str) -> dict:
    """Get status of a dispatched device operation job."""
```

The 7 command functions are thin wrappers passing the operation type string to the shared dispatch method. A helper dict maps operation type to table column definitions.

### JobTimeoutError

Caught at the command level — displays job_id and last_state with instructions to check via `scm operations status`.

### Registration

```python
# main.py — top-level, alphabetical
app.add_typer(operations_app, name="operations")
```

---

## 4. Incidents Commands (PR 4 — #215)

### New File: `src/scm_cli/commands/incidents.py`

**Subcommands:**
- `scm incidents list [--status <s>] [--severity <s>] [--product <s>] [--json]`
- `scm incidents show <incident_id> [--json]`

### Table Output (list)

```
ID                  Status   Severity   Product          Summary                          Created
─────────────────────────────────────────────────────────────────────────────────────────────────────
INC-2026-04-001     open     high       Prisma Access    Suspicious lateral movement      2026-04-15
INC-2026-04-002     open     critical   NGFW             C2 callback detected             2026-04-14
```

### Detail Output (show)

```
Incident: INC-2026-04-001
Status:   open
Severity: high
Product:  Prisma Access
Created:  2026-04-15 08:23:00
Updated:  2026-04-16 02:15:00
Summary:  Suspicious lateral movement detected from 10.1.2.50

Alerts (3):
  1. [high] Unusual SMB traffic from 10.1.2.50 to 10.1.2.100   2026-04-15 08:23
  2. [high] Credential dumping tool detected on 10.1.2.50       2026-04-15 08:25
  3. [medium] DNS tunneling attempt from 10.1.2.50              2026-04-15 08:30

Remediation:
  1. Isolate host 10.1.2.50 from network
  2. Reset credentials for affected accounts
  3. Scan 10.1.2.100 for indicators of compromise
```

### JSON Mode

`--json` dumps the full SDK model without formatting. Users pipe to `jq` for filtering.

### Filter Options

- `--status`: open, closed, in_progress
- `--severity`: critical, high, medium, low, informational
- `--product`: free-form string matching SDK's product filter

### SDK Client Methods

```python
def list_incidents(self, status: str | None = None, severity: str | None = None, product: str | None = None) -> list[dict]:
    """Search incidents with optional filters."""

def get_incident(self, incident_id: str) -> dict:
    """Get incident detail including alerts and remediation steps."""
```

### Validators

Pydantic model for list filters with `Literal` types for status/severity if SDK exposes enums.

### Mock Mode

Returns 3-5 incidents with varying status/severity, 2-3 alerts per incident, remediation steps.

### Registration

```python
# main.py — top-level, alphabetical
app.add_typer(incidents_app, name="incidents")
```

---

## 5. Testing Strategy

| PR | Test File | Key Cases |
|----|-----------|-----------|
| Foundation | extend `tests/test_context_commands.py`, `tests/test_client.py` + new region tests | Region context CRUD, override precedence, backward compat, JobTimeoutError |
| Local | `tests/test_local_commands.py` | List (success, empty, error), download stdout, download file, device not found, mock |
| Operations | `tests/test_operations_commands.py` | Sync per op type, async dispatch, timeout recovery, status check, mock |
| Incidents | `tests/test_incidents_commands.py` | List (no filters, each filter, combined, empty), show (found, not found), JSON output, mock |

**Patterns:** `mock_scm_client` fixture, `mock_dynaconf_settings`, Typer `CliRunner`, assert stdout for tables, assert exit codes for errors. Unit tests only — no integration tests in these PRs.

---

## 6. Files Changed Summary

### New Files
- `src/scm_cli/commands/local.py`
- `src/scm_cli/commands/operations.py`
- `src/scm_cli/commands/incidents.py`
- `tests/test_local_commands.py`
- `tests/test_operations_commands.py`
- `tests/test_incidents_commands.py`
- `docs/cli/local/list.md`
- `docs/cli/local/download.md`
- `docs/cli/operations/*.md` (one per operation type + status)
- `docs/cli/incidents/list.md`
- `docs/cli/incidents/show.md`

### Modified Files
- `pyproject.toml` — SDK version bump
- `src/scm_cli/main.py` — 3 new command group registrations + global `--region`
- `src/scm_cli/client.py` — pass region to `Scm()`, handle `raw_response`
- `src/scm_cli/commands/context.py` — `--region` on create
- `src/scm_cli/utils/context.py` — store/read region field
- `src/scm_cli/utils/sdk_client.py` — new methods + JobTimeoutError
- `src/scm_cli/utils/validators.py` — new models for incidents filters
- `mkdocs.yml` — nav entries for 3 new sections

---

## Unresolved Questions

1. SDK 0.13.0 Pydantic model field names for local config versions — need to inspect actual SDK models to confirm table column mapping
2. Device operations result schemas — each of the 7 types returns different data; table columns need to be defined per-type after inspecting SDK response models
3. Incident status/severity enum values — confirm whether SDK exposes these as Literals or free-form strings
4. Does `raw_response` on `Scm.request()` return `bytes` or a `Response` object — affects download implementation
5. Region valid values — is it free-form or an enum in the SDK? Determines whether to validate in CLI
