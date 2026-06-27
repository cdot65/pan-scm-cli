# Operations Management

The `scm` CLI provides capabilities beyond managing individual configuration objects, including deployment, job monitoring, health checks, and audit logging. This guide covers operational workflows for managing your SCM environment.

## Overview

This guide covers operational tasks you can perform with the CLI:

- Deploy configuration changes by committing and pushing
- Monitor asynchronous jobs and check their status
- Inspect license status and system health
- Review audit logs to track changes
- Manage scheduled tasks for recurring operations
- Troubleshoot issues with diagnostic tools

## Prerequisites

Before performing operational tasks, ensure you have:

- The `scm` CLI installed and authenticated (see [Getting Started](getting-started.md))
- Appropriate permissions for deployment and operational commands
- Configuration changes staged and ready to deploy (for commit/push operations)

## Core Concepts

### Deployment Workflow

After making changes to your configurations, you must commit and push those changes to make them active. The workflow is:

1. Make configuration changes using `set`, `delete`, or `load` commands
2. Commit the candidate configuration with a description
3. Push the committed configuration to devices

### Asynchronous Jobs

Many SCM operations run asynchronously and generate jobs. Use the job monitoring commands to track their progress and verify completion.

## Examples

### Configuration Deployment

#### Committing Changes

```bash
$ scm set deployment commit \
    --description "Updated address objects and security rules"
---> 100%
Commit initiated successfully
```

#### Pushing Configurations

```bash
$ scm set deployment push
---> 100%
Push initiated successfully
```

```bash
$ scm set deployment push \
    --device-groups "Branch-Firewalls,DataCenter"
---> 100%
Push initiated to device groups: Branch-Firewalls, DataCenter
```

:::tip
After committing or pushing, check job status to confirm the operation
completed successfully.
:::

### Job Monitoring

#### Checking Job Status

```bash
$ scm get operations job --job-id "12345"
---> 100%
Job: 12345
  Status: completed
  Type: commit
  Result: success
```

#### Listing Recent Jobs

```bash
$ scm get operations jobs --limit 10
---> 100%
Recent Jobs:
------------------------------------------------------------
Job ID: 12345
  Type: commit
  Status: completed
------------------------------------------------------------
Job ID: 12344
  Type: push
  Status: in_progress
------------------------------------------------------------
```

### License Management

#### Checking License Status

```bash
$ scm get operations licenses
---> 100%
License Status:
  Type: Enterprise
  Status: Active
  Expiration: 2026-12-31
```

### Health Monitoring

#### System Status

```bash
$ scm get operations status
---> 100%
System Status: Healthy
  API: Connected
  Services: All Running
```

#### Connectivity Tests

```bash
$ scm get operations connectivity-test --target firewalls
---> 100%
Connectivity Test Results:
  Target: firewalls
  Status: All reachable
```

### User Management

#### Listing Users

```bash
$ scm get operations users
---> 100%
Users:
  admin (Administrator)
  readonly (Read-Only)
```

#### User Roles

```bash
$ scm get operations roles
---> 100%
Available Roles:
  Administrator
  Read-Only
  Security Admin
```

### Audit Logs

#### Retrieving Audit Logs

```bash
$ scm get operations audit-logs --limit 20
---> 100%
Audit Logs (last 20 entries):
  2026-03-08 10:30:00 - admin - Created address: web-server
  2026-03-08 10:25:00 - admin - Updated security rule: Allow-Web
```

#### Filtering Audit Logs

```bash
$ scm get operations audit-logs --filter-user "admin"
---> 100%
Audit Logs (filtered by user: admin):
  2026-03-08 10:30:00 - Created address: web-server
  2026-03-08 10:25:00 - Updated security rule: Allow-Web
```

```bash
$ scm get operations audit-logs \
    --start-date "2026-03-01" \
    --end-date "2026-03-08"
---> 100%
Audit Logs (2026-03-01 to 2026-03-08):
  2026-03-08 10:30:00 - admin - Created address: web-server
  2026-03-05 14:00:00 - admin - Committed configuration
```

### Scheduled Tasks

#### Listing Scheduled Tasks

```bash
$ scm get operations scheduled-tasks
---> 100%
Scheduled Tasks:
  Daily-Backup (0 0 * * *) - Active
```

#### Creating Backup Tasks

```bash
$ scm set operations scheduled-task \
    --type backup \
    --name "Daily-Backup" \
    --schedule "0 0 * * *"
---> 100%
Created scheduled task: Daily-Backup
```

### Troubleshooting

#### Diagnostic Tools

```bash
$ scm get operations diagnostics
---> 100%
Diagnostics:
  API Connectivity: OK
  Authentication: Valid
  Configuration Sync: Up to date
```

#### Log Collection

```bash
$ scm get operations collect-logs --output-dir "./support-logs"
---> 100%
Logs collected to ./support-logs/
```

## Best Practices

1. **Use descriptive commit messages**: Document your changes clearly for audit trail purposes.
2. **Check job status after operations**: Verify that commits and pushes complete successfully before proceeding.
3. **Review audit logs periodically**: Track changes made through the CLI and other interfaces to maintain accountability.
4. **Set up scheduled tasks for backups**: Automate recurring operations to ensure consistent configuration backups.
5. **Use verbose mode for troubleshooting**: Add `--verbose` to commands when diagnosing operational issues.

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed information on all available commands
- Learn more about [Advanced Topics](advanced-topics.md) for scripting and automation
- Review [Configuration Objects](configuration-objects.md) to understand the types of resources you can manage
