# Posture

The `scm posture` commands perform Best Practice Assessments (BPA) against PAN-OS firewall configurations. You can export a running config from a firewall, upload it for assessment, and score the results in multiple output formats.

## Overview

The posture workflow has three stages:

1. **Export** — Retrieve a PAN-OS configuration XML from a live firewall
2. **Assess** — Upload the config to the BPA API, poll for completion, and save the report
3. **Score** — Parse a saved BPA report and output scored results

## Export

Export running or candidate configuration from a PAN-OS firewall via the XML API.

### Syntax

```bash
scm posture export [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--host TEXT` | PAN-OS firewall hostname or IP address (env: `PANOS_HOST`) | Yes |
| `--user TEXT` | Admin username (default: `automation`, env: `PANOS_USER`) | No |
| `--password TEXT` | Admin password (env: `PANOS_PASSWORD`) | Yes |
| `--output TEXT` | Output file path (default: `config.xml`) | No |
| `--category TEXT` | Config category: `running` or `candidate` (default: `running`) | No |

### Examples

#### Export Running Config

```bash
$ scm posture export \
    --host 10.0.0.1 \
    --user automation \
    --password $PANOS_PASSWORD \
    --output config.xml
Generated API key for automation@10.0.0.1
Exported running config to config.xml
```

#### Export Candidate Config

```bash
$ scm posture export \
    --host 10.0.0.1 \
    --password $PANOS_PASSWORD \
    --output candidate.xml \
    --category candidate
Generated API key for automation@10.0.0.1
Exported candidate config to candidate.xml
```

## Assess

Upload a PAN-OS configuration to the BPA API, poll for completion, save the raw report, and output formatted results.

The raw BPA report JSON is saved to `--output`. Formatted results are printed to stdout. Progress messages go to stderr so stdout can be piped cleanly by agents.

### Syntax

```bash
scm posture assess [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--config TEXT` | Path to PAN-OS config XML file | Yes |
| `--output TEXT` | Output file path for raw report JSON (default: `report.json`) | No |
| `--format TEXT` | Output format: `json`, `markdown`, or `csv` (default: `json`) | No |
| `--delete-after / --keep` | Delete config from cloud after assessment (default: delete) | No |
| `--timeout INT` | Max seconds to wait for processing (default: 300, range: 30-600) | No |

### Examples

#### Assess with JSON Output

```bash
$ scm posture assess \
    --config config.xml \
    --output report.json \
    --format json
Initiating BPA upload...
Task ID: 1620f87f-99f6-4e10-adf4-38e2f1b71d1a
Uploading config...
Upload complete. Waiting for processing...
  Status: UPLOAD_COMPLETE (processing...)
  Status: IN_PROGRESS (processing...)
Fetching report...
BPA report saved to report.json
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
  "checks": [...]
}
```

#### Assess with Markdown Output

```bash
$ scm posture assess \
    --config config.xml \
    --format markdown
Initiating BPA upload...
...
## BPA Score: 71.3% (216/303)

### Summary by Severity
| Severity | Passed | Failed | Total |
|---|---|---|---|
| Critical | 82 | 18 | 100 |
| Warning | 60 | 34 | 94 |
| Informational | 74 | 35 | 109 |

### Failing Checks (87)
| ID | Name | Severity | Category | Message |
|---|---|---|---|---|
| 223 | Client communication with secure custom certificates | Warning | device | Configure Local or SCEP Certificate Type |
...
```

#### Pipe JSON to an Agent

```bash
$ scm posture assess --config config.xml --format json 2>/dev/null | jq '.score'
71.3
```

## Score

Parse a saved BPA report JSON and output scored results. Use this to re-score a previously saved report in different formats or with different scope filters without re-running the assessment.

### Syntax

```bash
scm posture score [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--report TEXT` | Path to BPA report JSON file | Yes |
| `--scope TEXT` | Category filter: `all`, `device`, `service_health`, `network`, `policies`, `objects` (default: `all`) | No |
| `--format TEXT` | Output format: `json`, `markdown`, or `csv` (default: `json`) | No |

### Examples

#### Score All Checks as JSON

```bash
$ scm posture score --report report.json --format json
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
  "checks": [...]
}
```

#### Score by Category

```bash
$ scm posture score --report report.json --scope policies --format json
{
  "score": 45.5,
  "total": 11,
  "passed": 5,
  "failed": 6,
  ...
}
```

#### Export as CSV

```bash
$ scm posture score --report report.json --format csv > checks.csv
```

CSV output includes a header row and one row per check:

```
check_id,check_name,check_type,check_passed,category,subcategory,check_message,remediation
223,"Client communication with secure custom certificates",Warning,False,device,device_setup_secure_communication,"Configure Local or SCEP Certificate Type","Enable secure communication"
```

## Output Formats

All three formats are available on both `assess` and `score` commands via `--format`.

| Format | Use Case |
| --- | --- |
| `json` | Default. Agent-friendly structured output with score, totals, per-severity breakdown, and all checks |
| `markdown` | Human-readable tables with summary, failing checks, and passing checks sections |
| `csv` | Spreadsheet/pipeline consumption. Header row + one row per check |

## BPA Categories

The `--scope` filter on the `score` command maps to the BPA report's top-level categories:

| Scope | Description |
| --- | --- |
| `all` | All checks across all categories (default) |
| `device` | Device setup, certificates, WildFire, logging, sessions |
| `service_health` | Prisma Access service health checks |
| `network` | IPSec, IKE, GlobalProtect, interface management |
| `policies` | Security rules, decryption rules, NAT, QoS, DoS |
| `objects` | Security profiles, URL filtering, application filters |

## AI Agent Integration

The posture commands are designed for agent consumption:

- **JSON output** provides structured data agents can parse directly
- **Progress on stderr** means agents can pipe stdout without noise: `scm posture assess --config config.xml --format json 2>/dev/null`
- **Separated workflow** allows agents to cache reports and re-score with different scopes without re-uploading
- **CSV output** enables agents to load results into dataframes or spreadsheets
