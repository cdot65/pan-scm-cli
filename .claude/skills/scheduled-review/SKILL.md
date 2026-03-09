---
name: scheduled-review
description: >
  Comprehensive scheduled review of the pan-scm-cli project. Performs code quality checks, security
  scans, documentation accuracy verification, test coverage analysis, SDK compatibility checks, and
  CLI command validation. Creates GitHub issues and PRs for any findings. Run this on a schedule or
  manually to keep the project healthy.
---

# pan-scm-cli Scheduled Review

You are a senior Python engineer performing a comprehensive review of the pan-scm-cli repository — a CLI tool for managing Palo Alto Networks Strata Cloud Manager configurations. Execute ALL sections below on every run. Be thorough but concise in findings.

## 1. Code Quality & Linting

- Run `poetry run ruff check src/` and `poetry run ruff format --check src/`.
- Run `poetry run mypy src/` (note pre-existing errors vs new ones).
- Run `poetry run flake8 src/`.
- Report any new failures with file paths and line numbers.
- Verify CI workflow (`.github/workflows/ci.yml`) enforces lint/format/tests on PRs.
- If CI enforcement is missing for any check, flag it as a gap.

## 2. Inline Documentation Review

- Scan all `.py` source files in `src/scm_cli/` for docstrings on public classes, methods, and functions.
- Identify exported symbols missing docstrings entirely.
- Identify docstrings that are inaccurate, incomplete, or use incorrect parameter names/types.
- Cross-reference docstrings against the style guides in `.claude/STYLE_GUIDE.md`, `.claude/SDK_CLIENT_STYLE_GUIDE.md`, and `.claude/VALIDATORS_STYLE_GUIDE.md`.

## 3. Code Structure Analysis

- Evaluate the directory layout against the documented structure in `CLAUDE.md`.
- Review command modules (`src/scm_cli/commands/`) for consistency in:
  - Module organization and section separators (191 chars)
  - Typer app patterns and command registration
  - Error handling patterns
  - Output formatting standards
- Review `src/scm_cli/utils/sdk_client.py` for:
  - Method organization by configuration type
  - CRUD method patterns (create, get, list, delete)
  - Mock mode support
  - Error handling with `_handle_api_exception`
- Review `src/scm_cli/utils/validators.py` for:
  - Pydantic model patterns
  - `to_sdk_model()` conversion consistency
  - Field definitions with proper constraints
- Identify duplicated logic, overly large files, or misplaced modules.
- Check `src/scm_cli/main.py` for alphabetical ordering of command registrations.

## 4. Documentation Accuracy

- Read all markdown documentation in `docs/`.
- Cross-reference every CLI command example against actual Typer command registrations in the source.
- Verify option names, types, and required status match the code.
- Flag documentation referencing nonexistent commands, options, or behaviors.
- Check that `docs/cli/` pages follow the style guide in `.claude/skills/docs-style/SKILL.md`.
- Verify `mkdocs.yml` nav structure matches actual file layout in `docs/`.

## 5. Security — Dependencies

- Run `pip audit` or `poetry show --outdated` and report vulnerabilities.
- Check `pyproject.toml` for overly permissive version ranges.
- Verify `pan-scm-sdk` version compatibility (currently requires `>=0.12.0`).
- Check for outdated dependencies with known CVEs.

## 6. Security — Secrets & Environment Variables

- Scan the entire repository for hardcoded secrets, API keys, tokens, or credentials.
- Check that `.secrets.yaml` and any `.env` files are gitignored.
- Verify context credentials are stored safely in `~/.scm-cli/`.
- Check CI workflow files for exposed secrets.
- Verify environment variables documented in `CLAUDE.md` match what the code reads (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`).

## 7. SDK Client Analysis

Analyze `src/scm_cli/utils/sdk_client.py` for correctness:

### CRUD Patterns

| Check | Details |
|-------|---------|
| **Create/Update flow** | Verify all `create_*` methods follow fetch→update or create pattern consistently. |
| **Delete flow** | Verify all `delete_*` methods fetch by name then delete by ID. |
| **List flow** | Verify all `list_*` methods handle pagination and empty results. |
| **Error handling** | Verify all methods use `_handle_api_exception` consistently. |
| **Mock mode** | Verify mock mode returns realistic data for all methods. |

### Field Mapping

| Check | Details |
|-------|---------|
| **SDK service names** | Verify singular form used (e.g., `tag` not `tags`, `service` not `services`). |
| **to_sdk_model()** | Verify validators don't leak `folder`/`snippet`/`device` into SDK create calls. |
| **Boolean fields** | Verify boolean fields are omitted when false (not sent as `false`). |

## 8. CLI Command Validation

For each command category (objects, network, security, sase, identity, mobile-agent, setup):

| Check | Details |
|-------|---------|
| **Option consistency** | Verify `--name`, `--folder`, `--snippet`, `--device` patterns are consistent. |
| **Output messages** | Verify "Created" vs "Updated" messages are correct for set commands. |
| **Comma parsing** | Verify list-type options use `parse_comma_separated_list` where needed. |
| **Force flag** | Verify destructive operations (delete) support `--force` to skip confirmation. |
| **Help text** | Verify all options have descriptive help text. |

## 9. Test Coverage & Health

- Run `poetry run pytest tests/ --ignore=tests/test_dynaconf_config.py --ignore=tests/test_sdk_client_with_dynaconf.py --ignore=tests/test_sdk_client.py -q` and report pass/fail.
- Run with `--cov=src/scm_cli --cov-report=term-missing` to identify uncovered code.
- Identify command modules and SDK client methods with zero test coverage.
- Verify test structure mirrors source structure.
- Flag any tests that are skipped, xfailed, or disabled.

## 10. Upstream Compatibility

- Check current `pan-scm-sdk` version installed vs latest available on PyPI.
- Review open upstream issues (#153 API failures, #154 SDK limitations) for any resolved items.
- Test basic SDK connectivity: `scm context test` (if credentials available).
- Flag any new SDK deprecation warnings in test output.

## 11. Issue Creation & PR Workflow

After completing all analysis, create GitHub issues and PRs for findings.

### Issue Creation Rules

- Use `gh issue create` for each discrete finding requiring a code change.
- Title format: `[CATEGORY] Brief description` where CATEGORY is one of: `docs`, `security`, `structure`, `coverage`, `tests`, `lint`, `sdk-client`, `commands`, `validators`.
- Label issues appropriately (`bug`, `enhancement`, `documentation`, `security`).
- Each issue body must include:
  - **Problem:** What was found.
  - **Location:** File paths and line numbers.
  - **Suggested fix:** Concrete recommendation.
  - **Acceptance criteria:** What "done" looks like.

### PR Creation Rules (TDD — Red/Green)

For each issue, create a PR that follows TDD:

1. **Red phase:** Write failing tests first. Commit: `test: add failing tests for #<issue>`.
2. **Green phase:** Minimum code to pass. Commit: `fix|feat|docs: <desc> (#<issue>)`.
3. **Refactor phase (if needed):** Commit: `refactor: <desc> (#<issue>)`.

- Branch naming: `cdot65/<category>/<short-description>`.
- PR body must reference the issue with `Closes #<issue>`.
- One PR per issue — do not bundle unrelated changes.
- Run lint, format, and tests before marking PR ready.

## 12. Summary Report

At the end of each run, produce a summary:

```
## pan-scm-cli Review Summary — <date>

### Lint/Format: PASS | FAIL
### Type Check: PASS | FAIL (note pre-existing vs new)
### Tests: <passed>/<total> passed

### Documentation Gaps: <count>
### Code Structure Issues: <count>
### Security Vulnerabilities: <count>
### Secrets Exposure: <count>

### SDK Client:
| Component         | Status   | Issues Found |
|-------------------|----------|--------------|
| CRUD Patterns     | OK|ISSUE | <details>    |
| Field Mapping     | OK|ISSUE | <details>    |
| Mock Mode         | OK|ISSUE | <details>    |
| Error Handling    | OK|ISSUE | <details>    |

### CLI Commands:
| Category      | Status   | Issues Found |
|---------------|----------|--------------|
| Objects       | OK|ISSUE | <details>    |
| Network       | OK|ISSUE | <details>    |
| Security      | OK|ISSUE | <details>    |
| SASE          | OK|ISSUE | <details>    |
| Identity      | OK|ISSUE | <details>    |
| Mobile Agent  | OK|ISSUE | <details>    |
| Setup         | OK|ISSUE | <details>    |

### Test Coverage: xx%
### Upstream SDK: <version> (latest: <version>)
### Issues Created: <count> (list issue numbers)
### PRs Created: <count> (list PR numbers)
```
