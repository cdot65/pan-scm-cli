# Jobs

Jobs track the status of configuration operations in Strata Cloud Manager. The `scm jobs` commands allow you to list recent jobs, check the status of a specific job, and wait for a job to complete.

## List Jobs

Display recent SCM configuration jobs in a tabular format.

### Syntax

```bash
scm jobs list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--max-results INT` | Maximum number of jobs to display (default: 25) | No |

### Examples

#### List Recent Jobs

```bash
$ scm jobs list
---> 100%
                         SCM Jobs
┌────────┬───────────┬────────┬──────────────────┬────────────┬────────────┐
│ Job ID │ Type      │ Status │ Description      │ Start Time │ End Time   │
├────────┼───────────┼────────┼──────────────────┼────────────┼────────────┤
│ 12345  │ CommitAll │ FIN    │ Deploy changes   │ 2026-03-08 │ 2026-03-08 │
│ 12344  │ CommitAll │ FIN    │ Update objects   │ 2026-03-07 │ 2026-03-07 │
└────────┴───────────┴────────┴──────────────────┴────────────┴────────────┘

Showing 2 of 2 jobs
```

#### List with Custom Result Limit

```bash
$ scm jobs list --max-results 50
---> 100%
                         SCM Jobs
┌────────┬───────────┬────────┬──────────────────┬────────────┬────────────┐
│ Job ID │ Type      │ Status │ Description      │ Start Time │ End Time   │
├────────┼───────────┼────────┼──────────────────┼────────────┼────────────┤
│ 12345  │ CommitAll │ FIN    │ Deploy changes   │ 2026-03-08 │ 2026-03-08 │
│ ...    │ ...       │ ...    │ ...              │ ...        │ ...        │
└────────┴───────────┴────────┴──────────────────┴────────────┴────────────┘

Showing 50 of 120 jobs
```

## Job Status

Get the detailed status of a specific job by its ID.

### Syntax

```bash
scm jobs status [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--id TEXT` | Job ID to query | Yes |

### Examples

#### Check a Completed Job

```bash
$ scm jobs status --id 12345
---> 100%

Job Details for ID: 12345
--------------------------------------------------
  id: 12345
  type_str: CommitAll
  status_str: FIN
  description: Deploy changes
  start_ts: 2026-03-08T10:30:00Z
  end_ts: 2026-03-08T10:31:15Z
```

#### Check a Pending Job

```bash
$ scm jobs status --id 12350
---> 100%

Job Details for ID: 12350
--------------------------------------------------
  id: 12350
  type_str: CommitAll
  status_str: PEND
  description: Update security rules
  start_ts: 2026-03-08T11:00:00Z
```

## Wait for Job

Wait for a job to complete by polling its status until finished or timeout is reached.

### Syntax

```bash
scm jobs wait [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--id TEXT` | Job ID to wait for | Yes |
| `--timeout INT` | Timeout in seconds (default: 300) | No |

### Examples

#### Wait for Job Completion

```bash
$ scm jobs wait --id 12345
Waiting for job 12345 to complete (timeout: 300s)...
---> 100%

Job 12345 completed with status: FIN
--------------------------------------------------
  id: 12345
  type_str: CommitAll
  status_str: FIN
  description: Deploy changes
  start_ts: 2026-03-08T10:30:00Z
  end_ts: 2026-03-08T10:31:15Z
```

#### Wait with Custom Timeout

```bash
$ scm jobs wait --id 12345 --timeout 600
Waiting for job 12345 to complete (timeout: 600s)...
---> 100%

Job 12345 completed with status: FIN
--------------------------------------------------
  id: 12345
  type_str: CommitAll
  status_str: FIN
  description: Deploy changes
```

!!! tip
    Use `scm jobs wait` after an async commit to block until the configuration
    is fully deployed. Combine with `--timeout` for long-running operations.
