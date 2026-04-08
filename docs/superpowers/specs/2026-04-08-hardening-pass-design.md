# Hardening Pass: Security, Error Handling, Docs, Style

**Date:** 2026-04-08
**Delivery:** Single PR, commits grouped by category

---

## 1. Security — Context Credential File Permissions

### Problem

Context credential files (`~/.scm-cli/contexts/*.yaml`) containing `client_secret` and `access_token` are written with default OS permissions (typically 0644), making them readable by any local user.

### Changes

**File: `src/scm_cli/utils/context.py`**

#### 1a. Restrict directory permissions on creation

In `ensure_context_dir()`: after creating `~/.scm-cli/contexts/`, call `os.chmod(CONTEXT_DIR, 0o700)`.

#### 1b. Restrict file permissions on write

In `create_context()`: after writing the YAML file, call `os.chmod(context_file, 0o600)`.

#### 1c. Warn on read if permissions too open

In `get_context_config()`: before reading, check `os.stat(context_file).st_mode & 0o777`. If more permissive than `0o600`, print a warning to stderr and continue:

```
Warning: /home/user/.scm-cli/contexts/prod.yaml has insecure permissions (0644), expected 0600
```

#### 1d. Platform guard

Skip all permission checks/enforcement on Windows (`os.name == "nt"`) since POSIX permissions don't apply.

---

## 2. Error Handling Cleanup

### 2a. `sdk_client.py` — Replace `print()` with `typer.echo()`

**File: `src/scm_cli/utils/sdk_client.py` lines 130-164**

Replace all `print(..., file=sys.stderr)` calls with `typer.echo(..., err=True)`. Remove the local `import sys` statements inside the two except blocks (lines 131 and 158) — do not remove any top-level `import sys` if one exists. Error messages and structure stay the same.

### 2b. `utils/context.py` — Specific exception types

**File: `src/scm_cli/utils/context.py` line 57**

In `get_current_context()`: replace `except Exception as e` with `except OSError as e` (`PermissionError` is a subclass of `OSError`, so this covers both). Use `print(..., file=sys.stderr)` (utility module, not a command — `typer.echo` not appropriate here).

### 2c. `commands/context.py` — Specific exception types

**File: `src/scm_cli/commands/context.py`**

- Line 54: `except Exception:` in `list_command` → `except (ValueError, OSError):` (since `PermissionError` is a subclass of `OSError`, no need to list it separately)`
- Line 284: `except Exception:` in `current_command` → `except (ValueError, OSError):` (since `PermissionError` is a subclass of `OSError`, no need to list it separately)`

---

## 3. Documentation Fixes

### 3a. Service connection `--subnets` format (GitHub #199)

**File: `docs/cli/deployment/service-connection.md`**

- Options table: change "Comma-separated list of subnets" → "Subnets (repeat flag for multiple)"
- CLI examples: change `--subnets "10.1.0.0/24,10.1.1.0/24"` → `--subnets 10.1.0.0/24 --subnets 10.1.1.0/24`
- Fix any JSON array format examples similarly

### 3b. Service connection folder scope (GitHub #200)

**File: `docs/cli/deployment/service-connection.md`**

Add a note after the options table:

> **Note:** Service connections are always scoped to the "Service Connections" folder. This matches SCM API requirements and is enforced by the CLI.

### 3c. Move command documentation (4 rule types)

Add a "Move" section to each of:

- `docs/cli/security/rules.md`
- `docs/cli/security/app-override-rule.md`
- `docs/cli/security/authentication-rule.md`
- `docs/cli/security/decryption-rule.md`

Each section documents:

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Rule name to move | Yes |
| `--folder` | Folder scope | Yes (one of folder/snippet/device) |
| `--snippet` | Snippet scope | |
| `--device` | Device scope | |
| `--destination` | Position: top, bottom, before, after | Yes |
| `--rulebase` | Rulebase: pre, post | Yes |
| `--destination-rule` | Reference rule for before/after | When destination is before/after |

Include a usage example for each rule type.

### 3d. Schedule command YAML keys

**File: `docs/cli/objects/schedule.md`**

In the YAML format example (lines ~137-141): change `days_monday` → `monday`, `days_tuesday` → `tuesday`, etc. The `days_` prefix is an internal parameter name, not a YAML key.

---

## 4. Style — `commands/context.py` Separators

**File: `src/scm_cli/commands/context.py`**

Replace all `# ############...` section separators with the project-standard 191-character `# ===...===` format. Applies to separators at lines 24-26, 66-68, 112-114, 202-204, 234-236, 268-270, 292-294.

---

## Commit Plan

| Order | Commit | Files |
|-------|--------|-------|
| 1 | `fix: enforce 0600 perms on context credential files` | `utils/context.py` |
| 2 | `fix: replace print() with typer.echo(), use specific exceptions` | `utils/sdk_client.py`, `utils/context.py`, `commands/context.py` |
| 3 | `docs: fix subnets format, add folder scope note, add move cmd docs, fix schedule YAML keys` | 6 docs files |
| 4 | `style: standardize context.py section separators` | `commands/context.py` |

---

## Out of Scope

- Splitting large files (sdk_client.py, objects.py)
- Full error handling sweep of all command modules (decorator rollout already covered)
- Test coverage expansion
- `show_context_info()` deduplication
- Insights API TODO stubs
