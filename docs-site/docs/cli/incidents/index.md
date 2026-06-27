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

Shows full incident detail including alerts and remediations. Use `--json` for the complete structured output.

**Fields:**

- `incident_id` - Unique incident identifier
- `title` - Incident description
- `severity` - critical, high, medium, low, informational
- `status` - open, closed, in_progress
- `raised_time` - Epoch timestamp when incident was raised
- `updated_time` - Epoch timestamp of last update
- `alerts` - Associated alerts with `alert_id`, `title`, `severity`, and `state`
- `remediations` - Remediation guidance (string)

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `incident_id` | Yes | Incident ID to show |

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--json`, `-j` | No | Output as JSON |
