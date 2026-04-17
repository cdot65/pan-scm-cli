# Hardening Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix credential file permissions, standardize error handling, correct documentation mismatches, and normalize style in context module.

**Architecture:** Four independent categories (security, error handling, docs, style) applied as sequential commits on a single branch. All changes are small, isolated edits to existing files with no new modules or dependencies.

**Tech Stack:** Python 3.10+, Typer, PyYAML, MkDocs Material

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/scm_cli/utils/context.py` | Modify | Add chmod on write, permission warning on read |
| `src/scm_cli/utils/sdk_client.py` | Modify | Replace print() with typer.echo() in __init__ error block |
| `src/scm_cli/commands/context.py` | Modify | Narrow exception types, fix separators |
| `tests/test_context_utils.py` | Create | Tests for permission enforcement and warning |
| `docs/cli/deployment/service-connection.md` | Modify | Fix --subnets format, add folder scope note |
| `docs/cli/security/rules.md` | Modify | Add Move Security Rule section |
| `docs/cli/security/app-override-rule.md` | Modify | Add Move App Override Rule section |
| `docs/cli/security/authentication-rule.md` | Modify | Add Move Authentication Rule section |
| `docs/cli/security/decryption-rule.md` | Modify | Add Move Decryption Rule section |
| `docs/cli/objects/schedule.md` | Modify | Fix YAML key names (days_monday -> monday) |

---

### Task 1: Security — Test credential file permissions

**Files:**
- Create: `tests/test_context_utils.py`

- [ ] **Step 1: Write failing tests for permission enforcement**

```python
"""Tests for context utility functions — file permission enforcement."""

import os
import stat
import sys

import pytest
import yaml

from scm_cli.utils.context import (
    create_context,
    ensure_context_dir,
    get_context_config,
)


class TestFilePermissions:
    """Tests for credential file permission enforcement."""

    @pytest.fixture(autouse=True)
    def setup_context_dir(self, tmp_path, monkeypatch):
        """Redirect context paths to tmp_path for isolation."""
        self.ctx_dir = str(tmp_path / "contexts")
        self.current_file = str(tmp_path / "current-context")
        monkeypatch.setattr("scm_cli.utils.context.CONTEXT_DIR", self.ctx_dir)
        monkeypatch.setattr("scm_cli.utils.context.CURRENT_CONTEXT_FILE", self.current_file)

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
    def test_ensure_context_dir_sets_0700(self):
        """Context directory should be created with 0700 permissions."""
        ensure_context_dir()
        mode = stat.S_IMODE(os.stat(self.ctx_dir).st_mode)
        assert mode == 0o700

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
    def test_create_context_sets_0600(self):
        """Created context files should have 0600 permissions."""
        create_context(
            context_name="test-ctx",
            client_id="cid",
            client_secret="csecret",
            tsg_id="tsg",
        )
        ctx_file = os.path.join(self.ctx_dir, "test-ctx.yaml")
        mode = stat.S_IMODE(os.stat(ctx_file).st_mode)
        assert mode == 0o600

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
    def test_get_context_config_warns_on_open_permissions(self, capsys):
        """Reading a context file with overly permissive perms should warn."""
        # Create context then loosen permissions
        create_context(
            context_name="loose-ctx",
            client_id="cid",
            client_secret="csecret",
            tsg_id="tsg",
        )
        ctx_file = os.path.join(self.ctx_dir, "loose-ctx.yaml")
        os.chmod(ctx_file, 0o644)

        get_context_config("loose-ctx")

        captured = capsys.readouterr()
        assert "insecure permissions" in captured.err
        assert "0644" in captured.err

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
    def test_get_context_config_no_warning_on_correct_permissions(self, capsys):
        """Reading a context file with 0600 perms should not warn."""
        create_context(
            context_name="secure-ctx",
            client_id="cid",
            client_secret="csecret",
            tsg_id="tsg",
        )

        get_context_config("secure-ctx")

        captured = capsys.readouterr()
        assert "insecure permissions" not in captured.err

    def test_create_context_writes_valid_yaml(self):
        """Created context file should contain valid YAML with correct fields."""
        create_context(
            context_name="yaml-ctx",
            client_id="cid",
            client_secret="csecret",
            tsg_id="tsg",
            log_level="DEBUG",
        )
        ctx_file = os.path.join(self.ctx_dir, "yaml-ctx.yaml")
        with open(ctx_file) as f:
            data = yaml.safe_load(f)
        assert data["client_id"] == "cid"
        assert data["client_secret"] == "csecret"
        assert data["tsg_id"] == "tsg"
        assert data["log_level"] == "DEBUG"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_context_utils.py -v`
Expected: FAIL — `test_ensure_context_dir_sets_0700` and `test_create_context_sets_0600` fail (default perms), `test_get_context_config_warns_on_open_permissions` fails (no warning printed). `test_create_context_writes_valid_yaml` and `test_get_context_config_no_warning_on_correct_permissions` may pass already.

---

### Task 2: Security — Implement credential file permissions

**Files:**
- Modify: `src/scm_cli/utils/context.py`

- [ ] **Step 1: Add permission enforcement to `ensure_context_dir()`**

In `src/scm_cli/utils/context.py`, replace:

```python
def ensure_context_dir() -> None:
    """Ensure the context directory exists."""
    Path(CONTEXT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CURRENT_CONTEXT_FILE).parent.mkdir(parents=True, exist_ok=True)
```

with:

```python
def ensure_context_dir() -> None:
    """Ensure the context directory exists with restrictive permissions."""
    Path(CONTEXT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CURRENT_CONTEXT_FILE).parent.mkdir(parents=True, exist_ok=True)
    # Restrict directory permissions to owner-only on POSIX systems
    if os.name != "nt":
        os.chmod(CONTEXT_DIR, 0o700)
```

- [ ] **Step 2: Add permission enforcement to `create_context()`**

In `src/scm_cli/utils/context.py`, replace:

```python
    with open(context_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
```

(the one inside `create_context`) with:

```python
    with open(context_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Restrict file permissions to owner-only on POSIX systems
    if os.name != "nt":
        os.chmod(context_file, 0o600)
```

- [ ] **Step 3: Add permission warning to `get_context_config()`**

In `src/scm_cli/utils/context.py`, add `import stat` and `import sys` to the imports at the top:

```python
import os
import stat
import sys
from pathlib import Path
from typing import Any
```

Then replace:

```python
    with open(context_file) as f:
        config = yaml.safe_load(f)

    return config or {}
```

(the block inside `get_context_config`) with:

```python
    # Warn if file permissions are too open on POSIX systems
    if os.name != "nt":
        file_mode = stat.S_IMODE(os.stat(context_file).st_mode)
        if file_mode & 0o077:
            print(
                f"Warning: {context_file} has insecure permissions ({oct(file_mode)[2:]}), expected 0600",
                file=sys.stderr,
            )

    with open(context_file) as f:
        config = yaml.safe_load(f)

    return config or {}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_context_utils.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: No regressions. All previously passing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/utils/context.py tests/test_context_utils.py
git commit -m "fix: enforce 0600 perms on context credential files"
```

---

### Task 3: Error handling — `sdk_client.py` print→typer.echo

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py:127-164`

- [ ] **Step 1: Add typer import**

In `src/scm_cli/utils/sdk_client.py`, add `import typer` to the imports section (after line 16, near the other imports):

```python
import typer
```

- [ ] **Step 2: Replace print() calls with typer.echo()**

Replace the entire `except (APIError, InvalidClientError) as e:` block (lines 127-164) with:

```python
        except (APIError, InvalidClientError) as e:
            # Handle authentication failures gracefully
            error_msg = str(e)
            if "invalid_client" in error_msg or "Client authentication failed" in error_msg:
                typer.echo(
                    "\n❌ Authentication failed: Invalid client credentials",
                    err=True,
                )
                typer.echo(
                    f"\nCurrent context: {current_context or 'None set'}",
                    err=True,
                )
                typer.echo(
                    f"Client ID: {credentials.get('client_id', 'Not set')}",
                    err=True,
                )
                typer.echo(f"TSG ID: {credentials.get('tsg_id', 'Not set')}", err=True)
                typer.echo("\nTo fix this issue:", err=True)
                typer.echo(
                    "  1. Update context: scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>",
                    err=True,
                )
                typer.echo("  2. Switch context: scm context use <name>", err=True)
                typer.echo(
                    "  3. Use environment variables: SCM_CLIENT_ID, SCM_CLIENT_SECRET, SCM_TSG_ID",
                    err=True,
                )
                raise SystemExit(1) from e
            else:
                typer.echo(
                    f"\n❌ Failed to initialize SDK client: {error_msg}",
                    err=True,
                )
                raise SystemExit(1) from e
```

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: No regressions.

- [ ] **Step 4: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py
git commit -m "fix: replace print() with typer.echo() in sdk_client init"
```

---

### Task 4: Error handling — Narrow exception types in context modules

**Files:**
- Modify: `src/scm_cli/utils/context.py:54-58`
- Modify: `src/scm_cli/commands/context.py:54,284`

- [ ] **Step 1: Fix `utils/context.py` `get_current_context()`**

In `src/scm_cli/utils/context.py`, replace:

```python
        except Exception as e:
            print(f"Error reading current context: {e}")
            return None
```

with:

```python
        except OSError as e:
            print(f"Error reading current context: {e}", file=sys.stderr)
            return None
```

- [ ] **Step 2: Fix `commands/context.py` `list_command()`**

In `src/scm_cli/commands/context.py`, replace:

```python
        except Exception:
            masked_id = "[error reading config]"
```

with:

```python
        except (ValueError, OSError):
            masked_id = "[error reading config]"
```

- [ ] **Step 3: Fix `commands/context.py` `current_command()`**

In `src/scm_cli/commands/context.py`, replace:

```python
        except Exception:
            console.print("[red]Error reading context configuration[/red]")
```

with:

```python
        except (ValueError, OSError):
            console.print("[red]Error reading context configuration[/red]")
```

- [ ] **Step 4: Run context tests**

Run: `pytest tests/test_context_commands.py tests/test_context_utils.py -v`
Expected: All PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: No regressions.

- [ ] **Step 6: Commit**

```bash
git add src/scm_cli/utils/context.py src/scm_cli/commands/context.py
git commit -m "fix: narrow bare except clauses to specific exception types"
```

---

### Task 5: Docs — Fix service connection `--subnets` format and folder scope

**Files:**
- Modify: `docs/cli/deployment/service-connection.md`

- [ ] **Step 1: Fix options table**

In `docs/cli/deployment/service-connection.md`, replace:

```
| `--subnets LIST` | Comma-separated list of subnets | No |
```

with:

```
| `--subnets TEXT` | Subnets (repeat flag for multiple) | No |
```

- [ ] **Step 2: Fix CLI example on line 54**

Replace:

```bash
    --subnets "10.1.0.0/24,10.1.1.0/24"
```

with:

```bash
    --subnets 10.1.0.0/24 --subnets 10.1.1.0/24
```

- [ ] **Step 3: Add folder scope note after options table**

After line 44 (`\* One of --folder, --snippet, or --device is required.` — or the end of the options table if that line doesn't exist), add:

```markdown

> **Note:** Service connections are always scoped to the "Service Connections" folder. This is enforced by the CLI to match SCM API requirements. The `--folder`, `--snippet`, and `--device` options are not applicable for this resource type.
```

- [ ] **Step 4: Build docs to verify no rendering errors**

Run: `make docs-build`
Expected: Build succeeds with no errors.

- [ ] **Step 5: Commit**

```bash
git add docs/cli/deployment/service-connection.md
git commit -m "docs: fix --subnets format, add folder scope note for service connections"
```

---

### Task 6: Docs — Add move command documentation to security rule docs

**Files:**
- Modify: `docs/cli/security/rules.md` (append before Best Practices, line 382)
- Modify: `docs/cli/security/app-override-rule.md` (append before Best Practices, line 335)
- Modify: `docs/cli/security/authentication-rule.md` (append before Best Practices, line 340)
- Modify: `docs/cli/security/decryption-rule.md` (append before Best Practices, line 339)

- [ ] **Step 1: Add Move section to `rules.md`**

In `docs/cli/security/rules.md`, insert the following **before** the `## Best Practices` line (line 382):

```markdown
## Move Security Rule

Reposition a security rule within the rulebase.

### Syntax

```bash
scm move security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the rule to move | Yes |
| `--folder TEXT` | Folder containing the rule | Yes\* |
| `--snippet TEXT` | Snippet containing the rule | No\* |
| `--device TEXT` | Device containing the rule | No\* |
| `--destination TEXT` | Where to move: top, bottom, before, after | Yes |
| `--rulebase TEXT` | Rulebase: pre or post (default: pre) | No |
| `--destination-rule TEXT` | UUID of reference rule for before/after | When using before/after |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Move a Rule to the Top

```bash
$ scm move security rule \
    --folder Texas \
    --name "Allow Web" \
    --destination top \
    --rulebase pre
Moved security rule 'Allow Web' to top in folder 'Texas' rulebase 'pre'
```

#### Move a Rule After Another Rule

```bash
$ scm move security rule \
    --folder Texas \
    --name "Allow Web" \
    --destination after \
    --destination-rule 12345678-1234-1234-1234-123456789012
Moved security rule 'Allow Web' to after in folder 'Texas' rulebase 'pre'
```

```

- [ ] **Step 2: Add Move section to `app-override-rule.md`**

In `docs/cli/security/app-override-rule.md`, insert the following **before** the `## Best Practices` line (line 335):

```markdown
## Move App Override Rule

Reposition an app override rule within the rulebase.

### Syntax

```bash
scm move security app-override-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the rule to move | Yes |
| `--folder TEXT` | Folder containing the rule | Yes\* |
| `--snippet TEXT` | Snippet containing the rule | No\* |
| `--device TEXT` | Device containing the rule | No\* |
| `--destination TEXT` | Where to move: top, bottom, before, after | Yes |
| `--rulebase TEXT` | Rulebase: pre or post (default: pre) | No |
| `--destination-rule TEXT` | UUID of reference rule for before/after | When using before/after |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Move a Rule to the Top

```bash
$ scm move security app-override-rule \
    --folder Texas \
    --name override-https \
    --destination top \
    --rulebase pre
Moved app override rule 'override-https' to top in folder 'Texas' rulebase 'pre'
```

```

- [ ] **Step 3: Add Move section to `authentication-rule.md`**

In `docs/cli/security/authentication-rule.md`, insert the following **before** the `## Best Practices` line (line 340):

```markdown
## Move Authentication Rule

Reposition an authentication rule within the rulebase.

### Syntax

```bash
scm move security authentication-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the rule to move | Yes |
| `--folder TEXT` | Folder containing the rule | Yes\* |
| `--snippet TEXT` | Snippet containing the rule | No\* |
| `--device TEXT` | Device containing the rule | No\* |
| `--destination TEXT` | Where to move: top, bottom, before, after | Yes |
| `--rulebase TEXT` | Rulebase: pre or post (default: pre) | No |
| `--destination-rule TEXT` | UUID of reference rule for before/after | When using before/after |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Move a Rule to the Bottom

```bash
$ scm move security authentication-rule \
    --folder Texas \
    --name auth-rule \
    --destination bottom \
    --rulebase pre
Moved authentication rule 'auth-rule' to bottom in folder 'Texas' rulebase 'pre'
```

```

- [ ] **Step 4: Add Move section to `decryption-rule.md`**

In `docs/cli/security/decryption-rule.md`, insert the following **before** the `## Best Practices` line (line 339):

```markdown
## Move Decryption Rule

Reposition a decryption rule within the rulebase.

### Syntax

```bash
scm move security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the rule to move | Yes |
| `--folder TEXT` | Folder containing the rule | Yes\* |
| `--snippet TEXT` | Snippet containing the rule | No\* |
| `--device TEXT` | Device containing the rule | No\* |
| `--destination TEXT` | Where to move: top, bottom, before, after | Yes |
| `--rulebase TEXT` | Rulebase: pre or post (default: pre) | No |
| `--destination-rule TEXT` | UUID of reference rule for before/after | When using before/after |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Move a Rule to the Top

```bash
$ scm move security decryption-rule \
    --folder Texas \
    --name decrypt-rule \
    --destination top \
    --rulebase pre
Moved decryption rule 'decrypt-rule' to top in folder 'Texas' rulebase 'pre'
```

```

- [ ] **Step 5: Build docs to verify no rendering errors**

Run: `make docs-build`
Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add docs/cli/security/rules.md docs/cli/security/app-override-rule.md docs/cli/security/authentication-rule.md docs/cli/security/decryption-rule.md
git commit -m "docs: add move command documentation for all security rule types"
```

---

### Task 7: Docs — Fix schedule YAML key names

**Files:**
- Modify: `docs/cli/objects/schedule.md:137-141`

- [ ] **Step 1: Fix YAML keys**

In `docs/cli/objects/schedule.md`, replace:

```yaml
    days_monday: "09:00-17:00"
    days_tuesday: "09:00-17:00"
    days_wednesday: "09:00-17:00"
    days_thursday: "09:00-17:00"
    days_friday: "09:00-12:00"
```

with:

```yaml
    monday: "09:00-17:00"
    tuesday: "09:00-17:00"
    wednesday: "09:00-17:00"
    thursday: "09:00-17:00"
    friday: "09:00-12:00"
```

- [ ] **Step 2: Build docs to verify**

Run: `make docs-build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add docs/cli/objects/schedule.md
git commit -m "docs: fix schedule YAML keys (days_monday -> monday)"
```

---

### Task 8: Style — Standardize context.py section separators

**Files:**
- Modify: `src/scm_cli/commands/context.py`

- [ ] **Step 1: Replace all section separators**

In `src/scm_cli/commands/context.py`, replace every occurrence of the non-standard separator:

```python
# ############################################################################
```

with the project-standard 191-character separator:

```python
# =============================================================================================================================================================================================
```

There are 14 lines to replace (7 separator blocks, each with 2 identical lines — the top and bottom of each block). The blocks are at approximately lines:
- 24-25 (list command)
- 66-67 (show command)
- 112-113 (create command)
- 202-203 (use command)
- 234-235 (delete command)
- 268-269 (current command)
- 292-293 (test command)

Each 3-line block looks like:

```python
# ############################################################################
# <command name>
# ############################################################################
```

Replace each with:

```python
# =============================================================================================================================================================================================
# <command name>
# =============================================================================================================================================================================================
```

The separator is 191 characters: `# ` followed by 189 `=` characters.

- [ ] **Step 2: Run lint**

Run: `make lint`
Expected: No new lint errors.

- [ ] **Step 3: Commit**

```bash
git add src/scm_cli/commands/context.py
git commit -m "style: standardize context.py section separators to 191-char format"
```

---

### Task 9: Final validation

- [ ] **Step 1: Run full quality checks**

Run: `make quality`
Expected: All checks pass (lint, format, mypy, tests).

- [ ] **Step 2: Verify git log**

Run: `git log --oneline -6`
Expected: 6 new commits in order:
1. `fix: enforce 0600 perms on context credential files`
2. `fix: replace print() with typer.echo() in sdk_client init`
3. `fix: narrow bare except clauses to specific exception types`
4. `docs: fix --subnets format, add folder scope note for service connections`
5. `docs: add move command documentation for all security rule types`
6. `docs: fix schedule YAML keys (days_monday -> monday)`
7. `style: standardize context.py section separators to 191-char format`

---

## Unresolved Questions

None — all design decisions were resolved during brainstorming.
