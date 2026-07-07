# Operations Management

The `scm` CLI provides capabilities beyond managing individual configuration objects, including committing changes, job monitoring, device operations, and local config retrieval. This guide covers operational workflows for managing your SCM environment.

## Overview

This guide covers operational tasks you can perform with the CLI:

- Deploy configuration changes by committing them
- Monitor asynchronous jobs and check their status
- Run diagnostic operations against managed devices
- Retrieve on-device configuration versions
- Troubleshoot issues with debug output

## Prerequisites

Before performing operational tasks, ensure you have:

- The `scm` CLI installed and authenticated (see [Getting Started](getting-started.md))
- Appropriate permissions for deployment and operational commands
- Configuration changes staged and ready to deploy (for commit operations)

## Core Concepts

### Deployment Workflow

After making changes to your configurations, you must commit those changes to make them active. The workflow is:

1. Make configuration changes using `set`, `delete`, or `load` commands
2. Commit the staged configuration with `scm commit`, naming the affected folder(s)
3. Monitor the commit job until it completes

### Asynchronous Jobs

Many SCM operations run asynchronously and generate jobs. Use the `scm jobs` commands to track their progress and verify completion.

## Examples

### Configuration Deployment

#### Committing Changes

```bash
$ scm commit \
    --folder Texas \
    --description "Updated address objects and security rules"
---> 100%
Commit job 12345 started
```

#### Committing Multiple Folders

```bash
$ scm commit \
    --folder Texas \
    --folder California \
    --description "Multi-site update"
---> 100%
Commit job 12346 started
```

#### Waiting for a Commit to Finish

```bash
$ scm commit \
    --folder Texas \
    --description "Update" \
    --sync \
    --timeout 600
---> 100%
Commit job 12347 completed successfully
```

:::tip
After committing, check job status to confirm the operation completed
successfully.
:::

### Job Monitoring

#### Checking Job Status

```bash
$ scm jobs status --id 12345
---> 100%
Job: 12345
  Status: FIN
  Type: CommitAll
  Result: OK
```

#### Listing Recent Jobs

```bash
$ scm jobs list --max-results 10
---> 100%
SCM Jobs
------------------------------------------------------------
Id: 12345
  Type: CommitAll
  Status: FIN
------------------------------------------------------------
Id: 12344
  Type: CommitAll
  Status: PEND
------------------------------------------------------------
```

#### Waiting for a Job

```bash
$ scm jobs wait --id 12344 --timeout 600
---> 100%
Job 12344 completed with status: FIN
```

### Device Operations

Run diagnostics against a managed firewall by serial number. Each command
polls to completion by default; add `--async` to get a job ID immediately.

```bash
$ scm operations route-table --device 007951000123456
$ scm operations interfaces --device 007951000123456
$ scm operations logging-status --device 007951000123456
```

#### Dispatching Asynchronously

```bash
$ scm operations route-table --device 007951000123456 --async
Dispatched job: abc-123

$ scm operations status --id abc-123
Job abc-123: completed
```

See [Device Operations](../cli/operations/index.md) for the full list of
operations.

### Local Device Configurations

List and download configuration versions stored on a device:

```bash
$ scm local list --device 007951000123456
$ scm local download --device 007951000123456 --version 42 --output config.xml
```

### Troubleshooting

#### Debug Output

```bash
$ scm --debug show object address --folder Texas
```

The global `--debug` flag enables debug logging (including SDK auth/HTTP
traffic) and full tracebacks. Alternatively, set `SCM_LOG_LEVEL=DEBUG`.

## Best Practices

1. **Use descriptive commit messages**: Document your changes clearly for audit trail purposes.
2. **Check job status after operations**: Verify that commits complete successfully before proceeding.
3. **Use `--sync` for scripted commits**: Blocking until the commit finishes simplifies automation pipelines.
4. **Prefer `--async` for slow device operations**: Dispatch the job, capture the ID, and poll with `scm operations status --id`.
5. **Use debug mode for troubleshooting**: Add the global `--debug` flag when diagnosing operational issues.

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed information on all available commands
- Learn more about [Advanced Topics](advanced-topics.md) for scripting and automation
- Review [Configuration Objects](configuration-objects.md) to understand the types of resources you can manage
