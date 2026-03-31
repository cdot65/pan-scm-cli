# BPA Fix and Output Formats Design

**Date:** 2026-03-30
**Status:** Approved
**Approach:** Minimal Fix + Rewrite Score Parser (Approach A)

## Problem

The posture BPA workflow is broken. The `upload_config_to_presigned_url` method sends wrong headers (`Content-Type: application/octet-stream`) and doesn't gzip-compress the config data. Additionally, the `score` command assumes a flat `checks` array that doesn't match the real BPA report schema, and output formats are limited to plain text and minimal JSON.

## Goals

1. Fix the upload step so the BPA assess pipeline works end-to-end
2. Rewrite the report parser to handle the real nested BPA schema
3. Add agent-friendly output formats: JSON (default), Markdown, CSV
4. Apply formatting to both `assess` and `score` commands

## Non-Goals

- Agentic optimization loop (separate effort, see `2026-03-29-bpa-autoresearch-loop-design.md`)
- Rich terminal tables (Markdown serves console + agent use cases)
- New commands (existing `export`, `assess`, `score` structure stays)
- Mock mode for BPA
- Parsing `adoption` or `adoption_summary` sections
- TSV output (trivially addable later)

---

## Section 1: Upload Fix (`sdk_client.py`)

**Method:** `upload_config_to_presigned_url`

Changes:
- Gzip-compress `config_data` before sending
- Set `Content-Type: plain/text`
- Set `Content-Encoding: gzip`

```python
import gzip

def upload_config_to_presigned_url(self, upload_url: str, config_data: bytes) -> None:
    compressed = gzip.compress(config_data)
    headers = {
        "Content-Type": "plain/text",
        "Content-Encoding": "gzip",
    }
    response = requests.put(upload_url, data=compressed, headers=headers)
    response.raise_for_status()
```

No other SDK client changes needed. The initiate, poll, and fetch methods work correctly.

---

## Section 2: BPA Report Parser

The real BPA report schema is nested:

```
best_practices -> category -> subcategory -> items[] -> warnings[]
```

Categories: `device`, `service_health`, `network`, `policies`, `objects`

Each warning (check) has this schema:

```json
{
    "check_id": 223,
    "check_name": "Client communication with secure custom certificates...",
    "check_type": "Warning",
    "check_message": "It is recommended to configure...",
    "check_passed": false,
    "uuid": null,
    "remediation": null,
    "user_excluded": false,
    "check_excluded": false
}
```

Check types: `Critical`, `Warning`, `Informational`

The parser will:

1. Flatten all checks from the nested structure
2. Attach `category` and `subcategory` to each flattened check
3. Filter by `--scope` using real category names

Flattened check structure:

```python
{
    "category": "device",
    "subcategory": "device_setup_session",
    "check_id": 121,
    "check_name": "Accelerated Aging should be enabled...",
    "check_type": "Critical",
    "check_message": "...",
    "check_passed": True,
    "remediation": None,
}
```

`--scope` values: `all | device | service_health | network | policies | objects`

---

## Section 3: Output Formats

Both `assess` and `score` get a unified `--format` option: `json` (default), `markdown`, `csv`.

### JSON (default)

Agent-friendly structured output:

```json
{
    "score": 71.3,
    "total": 303,
    "passed": 216,
    "failed": 87,
    "by_type": {
        "Critical": {"total": 100, "passed": 82, "failed": 18},
        "Warning": {"total": 94, "passed": 60, "failed": 34},
        "Informational": {"total": 109, "passed": 74, "failed": 35}
    },
    "checks": [
        {
            "check_id": 223,
            "check_name": "Client communication with...",
            "check_type": "Warning",
            "check_passed": false,
            "category": "device",
            "subcategory": "device_setup_secure_communication",
            "check_message": "It is recommended to...",
            "remediation": null
        }
    ]
}
```

### Markdown

Human/console-friendly with tables:

```markdown
## BPA Score: 71.3% (216/303)

### Summary by Severity
| Severity      | Passed | Failed | Total |
|---------------|--------|--------|-------|
| Critical      | 82     | 18     | 100   |
| Warning       | 60     | 34     | 94    |
| Informational | 74     | 35     | 109   |

### Failing Checks (87)
| ID  | Name                          | Severity      | Category | Message     |
|-----|-------------------------------|---------------|----------|-------------|
| 223 | Client communication with...  | Warning       | device   | It is rec...|

### Passing Checks (216)
| ID  | Name                          | Severity      | Category |
|-----|-------------------------------|---------------|----------|
| 121 | Accelerated Aging should...   | Informational | device   |
```

### CSV

Header row + one row per check, all checks included (filterable by scope):

```csv
check_id,check_name,check_type,check_passed,category,subcategory,check_message,remediation
223,"Client communication with...",Warning,false,device,device_setup_secure_communication,"It is recommended...",
121,"Accelerated Aging should...",Informational,true,device,device_setup_session,,
```

---

## Section 4: Command Changes

### `assess` command

- Keeps existing workflow: initiate -> upload (now fixed) -> poll -> fetch
- Still saves raw report JSON to `--output` (default `report.json`)
- Adds `--format` option (`json | markdown | csv`, default `json`)
- After saving raw report, parses and outputs formatted results to stdout
- Progress messages stay on stderr (so agents can pipe stdout cleanly)

### `score` command

- Rewrite parser for real nested schema
- `--scope` changes to `all | device | service_health | network | policies | objects`
- `--format` changes from `plain | json` to `json | markdown | csv`
- Drop `plain` format — JSON default includes score plus full detail

### `export` command

- No changes needed

### Shared option

```python
FORMAT_OPTION = typer.Option(
    "json",
    "--format",
    help="Output format (json, markdown, csv)",
)
```

### Validators

- Update scope validation to match real categories
- No new validator models needed

---

## Real Report Reference

Based on actual BPA output (`bpa.json`, 265KB):

- **Top-level keys:** `information`, `best_practices`, `adoption`, `adoption_summary`
- **Categories:** `device` (38 subcats), `service_health` (29), `network` (9), `policies` (9), `objects` (13)
- **Sample stats:** 303 checks, 216 passed, 87 failed
- **Check types:** Critical (100), Warning (94), Informational (109)
