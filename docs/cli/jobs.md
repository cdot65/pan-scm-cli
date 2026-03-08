# Jobs

Jobs track the status of configuration operations in Strata Cloud Manager.

## List Jobs

Display recent SCM configuration jobs.

```bash
scm jobs list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--max-results INT` | Maximum number of jobs to display (default: 25) | No |

### Example

```bash
$ scm jobs list
$ scm jobs list --max-results 50
```

## Job Status

Get the status of a specific job.

```bash
scm jobs status --id JOB_ID
```

### Example

```bash
$ scm jobs status --id 12345
```

## Wait for Job

Wait for a job to complete, polling until finished or timeout.

```bash
scm jobs wait --id JOB_ID [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--id TEXT` | Job ID | Yes |
| `--timeout INT` | Timeout in seconds (default: 300) | No |

### Example

```bash
$ scm jobs wait --id 12345
$ scm jobs wait --id 12345 --timeout 600
```
