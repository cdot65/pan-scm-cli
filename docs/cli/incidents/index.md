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

Shows full incident detail including alerts and remediation steps. Use `--json` for the complete structured output.

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `incident_id` | Yes | Incident ID to show |

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--json`, `-j` | No | Output as JSON |
