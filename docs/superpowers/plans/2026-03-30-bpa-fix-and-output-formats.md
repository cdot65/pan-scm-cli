# BPA Fix and Output Formats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken BPA upload, rewrite the report parser for the real nested schema, and add JSON/Markdown/CSV output formats to `assess` and `score` commands.

**Architecture:** Minimal fix approach — patch `upload_config_to_presigned_url` in `sdk_client.py` with gzip compression and correct headers, rewrite the parser in `posture.py` to flatten the real nested `best_practices` schema, and add `--format` and updated `--scope` options to both `assess` and `score` commands. All formatting logic lives in `posture.py`.

**Tech Stack:** Python 3.10+, Typer, Pydantic, gzip (stdlib), csv (stdlib)

---

## File Map

- **Modify:** `src/scm_cli/utils/sdk_client.py:15949-15959` — fix upload headers + gzip
- **Modify:** `src/scm_cli/commands/posture.py` — rewrite parser, add format options, update scope
- **Modify:** `tests/test_posture_commands.py` — update all tests for new schema/formats
- **Reference:** `/Users/cdot/development/cdot65/prisma-airs-cli/bpa.json` — real BPA report for schema reference

---

### Task 1: Fix Upload Headers and Gzip Compression

**Files:**
- Modify: `src/scm_cli/utils/sdk_client.py:15949-15959`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing test for gzip + headers**

In `tests/test_posture_commands.py`, update the existing `TestSCMClientPostureMethods` class. Replace `test_upload_config_to_presigned_url`:

```python
def test_upload_config_to_presigned_url(self, monkeypatch):
    """Test config upload sends gzip-compressed data with correct headers."""
    import gzip

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_posture_commands.py::TestSCMClientPostureMethods::test_upload_config_to_presigned_url -v`

Expected: FAIL — current code sends `Content-Type: application/octet-stream` and uncompressed data.

- [ ] **Step 3: Fix `upload_config_to_presigned_url` in sdk_client.py**

In `src/scm_cli/utils/sdk_client.py`, add `import gzip` at the top of the file (near the other stdlib imports), then replace the method body at lines 15949-15959:

```python
def upload_config_to_presigned_url(self, upload_url: str, config_data: bytes) -> None:
    """Upload config file to a presigned GCS URL.

    Args:
        upload_url: Presigned GCS URL from initiate_bpa_upload.
        config_data: Raw config file bytes.

    """
    self.logger.info("Uploading config to presigned URL")
    compressed = gzip.compress(config_data)
    headers = {
        "Content-Type": "plain/text",
        "Content-Encoding": "gzip",
    }
    response = requests.put(upload_url, data=compressed, headers=headers)
    response.raise_for_status()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_posture_commands.py::TestSCMClientPostureMethods::test_upload_config_to_presigned_url -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/utils/sdk_client.py tests/test_posture_commands.py
git commit -m "fix(posture): gzip-compress config upload with correct headers"
```

---

### Task 2: Add BPA Report Parser Function

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for the parser**

Add a new test class in `tests/test_posture_commands.py`. This test data mirrors the real BPA schema structure:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_posture_commands.py::TestBpaReportParser -v`

Expected: FAIL — `flatten_bpa_checks` does not exist yet.

- [ ] **Step 3: Implement `flatten_bpa_checks` in posture.py**

Add this function in `src/scm_cli/commands/posture.py` after the imports, before the Typer app configuration section:

```python
def flatten_bpa_checks(
    report: dict,
    scope: str = "all",
) -> list[dict]:
    """Flatten nested BPA report into a list of checks with category metadata.

    Args:
        report: Raw BPA report dict.
        scope: Category filter — 'all' or a specific category name.

    Returns:
        list[dict]: Flattened checks with category and subcategory attached.

    """
    checks = []
    best_practices = report.get("best_practices", {})

    for category, subcategories in best_practices.items():
        if scope != "all" and category != scope:
            continue
        for subcategory, items in subcategories.items():
            for item in items:
                for warning in item.get("warnings", []):
                    check = {
                        "category": category,
                        "subcategory": subcategory,
                        "check_id": warning.get("check_id"),
                        "check_name": warning.get("check_name"),
                        "check_type": warning.get("check_type"),
                        "check_message": warning.get("check_message"),
                        "check_passed": warning.get("check_passed"),
                        "remediation": warning.get("remediation"),
                    }
                    checks.append(check)

    return checks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_posture_commands.py::TestBpaReportParser -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): add flatten_bpa_checks parser for real BPA schema"
```

---

### Task 3: Add Output Formatting Functions

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for JSON formatting**

Add a new test class in `tests/test_posture_commands.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_posture_commands.py::TestBpaFormatters -v`

Expected: FAIL — `format_bpa_output` does not exist yet.

- [ ] **Step 3: Implement `format_bpa_output` in posture.py**

Add these imports at the top of `src/scm_cli/commands/posture.py`:

```python
import csv
import io
```

Add this function after `flatten_bpa_checks`:

```python
def format_bpa_output(checks: list[dict], fmt: str = "json") -> str:
    """Format flattened BPA checks into the requested output format.

    Args:
        checks: Flattened list of BPA checks from flatten_bpa_checks.
        fmt: Output format — 'json', 'markdown', or 'csv'.

    Returns:
        str: Formatted output string.

    """
    total = len(checks)
    passed = sum(1 for c in checks if c.get("check_passed"))
    failed = total - passed
    score = round((passed / total) * 100, 1) if total > 0 else 0.0

    # Build by_type breakdown
    by_type: dict[str, dict[str, int]] = {}
    for c in checks:
        ct = c.get("check_type", "Unknown")
        if ct not in by_type:
            by_type[ct] = {"total": 0, "passed": 0, "failed": 0}
        by_type[ct]["total"] += 1
        if c.get("check_passed"):
            by_type[ct]["passed"] += 1
        else:
            by_type[ct]["failed"] += 1

    if fmt == "json":
        data = {
            "score": score,
            "total": total,
            "passed": passed,
            "failed": failed,
            "by_type": by_type,
            "checks": checks,
        }
        return json.dumps(data, indent=2)

    if fmt == "markdown":
        lines = [
            f"## BPA Score: {score}% ({passed}/{total})",
            "",
            "### Summary by Severity",
            "| Severity | Passed | Failed | Total |",
            "|---|---|---|---|",
        ]
        for severity in ["Critical", "Warning", "Informational"]:
            if severity in by_type:
                s = by_type[severity]
                lines.append(f"| {severity} | {s['passed']} | {s['failed']} | {s['total']} |")

        failing = [c for c in checks if not c.get("check_passed")]
        passing = [c for c in checks if c.get("check_passed")]

        lines.append("")
        lines.append(f"### Failing Checks ({len(failing)})")
        lines.append("| ID | Name | Severity | Category | Message |")
        lines.append("|---|---|---|---|---|")
        for c in failing:
            msg = c.get("check_message") or ""
            lines.append(f"| {c['check_id']} | {c['check_name']} | {c['check_type']} | {c['category']} | {msg} |")

        lines.append("")
        lines.append(f"### Passing Checks ({len(passing)})")
        lines.append("| ID | Name | Severity | Category |")
        lines.append("|---|---|---|---|")
        for c in passing:
            lines.append(f"| {c['check_id']} | {c['check_name']} | {c['check_type']} | {c['category']} |")

        return "\n".join(lines)

    if fmt == "csv":
        output = io.StringIO()
        fieldnames = [
            "check_id",
            "check_name",
            "check_type",
            "check_passed",
            "category",
            "subcategory",
            "check_message",
            "remediation",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for c in checks:
            writer.writerow(c)
        return output.getvalue()

    raise ValueError(f"Unknown format: {fmt}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_posture_commands.py::TestBpaFormatters -v`

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): add format_bpa_output for json/markdown/csv"
```

---

### Task 4: Update Score Command

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for updated score command**

Replace the entire `TestPostureScoreCommand` class in `tests/test_posture_commands.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_posture_commands.py::TestPostureScoreCommand -v`

Expected: FAIL — the `score_report` function still uses the old flat schema and old `--format` values.

- [ ] **Step 3: Rewrite `score_report` command in posture.py**

Update the `SCOPE_OPTION` and `FORMAT_OPTION` at the module level:

```python
SCOPE_OPTION = typer.Option(
    "all",
    "--scope",
    help="BPA check scope (all, device, service_health, network, policies, objects)",
)
FORMAT_OPTION = typer.Option(
    "json",
    "--format",
    help="Output format (json, markdown, csv)",
)
```

Replace the entire `score_report` function:

```python
@posture_app.command("score")
@handle_command_errors("scoring report")
def score_report(
    report: str = REPORT_OPTION,
    scope: str = SCOPE_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Parse BPA report JSON and output scored results.

    Reads the nested best_practices structure, flattens all checks, and
    outputs scored results in the requested format. Use --scope to filter
    by category and --format to control output.

    Example:
    -------
        scm posture score \
        --report report.json \
        --scope device \
        --format json

    """
    report_path = Path(report)
    if not report_path.exists():
        typer.echo(f"Error: report file not found: {report_path}", err=True)
        raise typer.Exit(code=1)

    report_data = json.loads(report_path.read_text())
    checks = flatten_bpa_checks(report_data, scope=scope)

    if not checks:
        typer.echo("Error: no checks found for the given scope", err=True)
        raise typer.Exit(code=1)

    typer.echo(format_bpa_output(checks, fmt=format))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_posture_commands.py::TestPostureScoreCommand -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): rewrite score command for real BPA schema + formats"
```

---

### Task 5: Update Assess Command

**Files:**
- Modify: `src/scm_cli/commands/posture.py`
- Test: `tests/test_posture_commands.py`

- [ ] **Step 1: Write failing tests for updated assess command**

Replace the `TestPostureAssessCommand` class in `tests/test_posture_commands.py`:

```python
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

    def test_assess_success_json(self, runner, monkeypatch, tmp_path):
        """Test successful BPA assessment with JSON output."""
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

        result = runner.invoke(
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

    def test_assess_success_markdown(self, runner, monkeypatch, tmp_path):
        """Test successful BPA assessment with Markdown output."""
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

        result = runner.invoke(
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_posture_commands.py::TestPostureAssessCommand -v`

Expected: FAIL — `assess_config` doesn't accept `--format` yet.

- [ ] **Step 3: Update `assess_config` command in posture.py**

Replace the `assess_config` function:

```python
@posture_app.command("assess")
@handle_command_errors("assessing config")
def assess_config(
    config: str = CONFIG_OPTION,
    delete_after: bool = DELETE_AFTER_OPTION,
    output: str = typer.Option("report.json", "--output", help="Output file path for report"),
    timeout: int = TIMEOUT_OPTION,
    format: str = FORMAT_OPTION,
):
    r"""Upload config to BPA API, poll for completion, and output scored results.

    Saves the raw BPA report to --output and prints formatted results to stdout.
    Progress messages go to stderr so stdout can be piped cleanly.

    Example:
    -------
        scm posture assess \
        --config config.xml \
        --delete-after \
        --output report.json \
        --format json \
        --timeout 300

    """
    config_path = Path(config)
    if not config_path.exists():
        typer.echo(f"Error: config file not found: {config_path}", err=True)
        raise typer.Exit(code=1)

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

    # Save raw report
    output_path = Path(assess_params.output)
    output_path.write_text(json.dumps(report, indent=2))
    typer.echo(f"BPA report saved to {output_path}", err=True)

    # Output formatted results to stdout
    checks = flatten_bpa_checks(report)
    if checks:
        typer.echo(format_bpa_output(checks, fmt=format))
    else:
        typer.echo("Warning: no checks found in report", err=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_posture_commands.py::TestPostureAssessCommand -v`

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scm_cli/commands/posture.py tests/test_posture_commands.py
git commit -m "feat(posture): update assess command with format output + real schema"
```

---

### Task 6: Run Full Test Suite and Verify

**Files:**
- All modified files

- [ ] **Step 1: Run full posture test suite**

Run: `pytest tests/test_posture_commands.py -v`

Expected: All tests PASS. Old tests that used the flat `checks` schema have been replaced.

- [ ] **Step 2: Run full project test suite**

Run: `make tests`

Expected: All tests PASS. No regressions.

- [ ] **Step 3: Run linting**

Run: `make lint`

Expected: No lint errors.

- [ ] **Step 4: Run formatting**

Run: `make format`

Expected: No changes needed (or auto-fixed).

- [ ] **Step 5: Commit any formatting fixes**

If `make format` changed anything:

```bash
git add -u
git commit -m "style: format posture module"
```
