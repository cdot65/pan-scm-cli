# CLI Operations Management

The `scm` CLI provides capabilities beyond just managing individual configuration objects, allowing you to handle operations like deployment, status checking, and more.

## Configuration Deployment

After making changes to your configurations using the CLI, you need to deploy those changes to make them active in your environment.

### Committing Changes

To commit your configuration changes:

```bash
# Commit changes with a description
scm set deployment commit --description "Updated address objects and security rules"
```

### Pushing Configurations

To push configurations to devices:

```bash
# Push configurations to all devices
scm set deployment push

# Push to specific device groups
scm set deployment push --device-groups "Branch-Firewalls,DataCenter"
```

## Job Monitoring

Many operations in Strata Cloud Manager generate jobs that run asynchronously. The CLI provides commands to monitor these jobs.

### Checking Job Status

To check the status of a job:

```bash
# Check job status by ID
scm get operations job --job-id "12345"
```

### Listing Recent Jobs

To view recent jobs:

```bash
# List the 10 most recent jobs
scm get operations jobs --limit 10
```

## License Management

Manage licenses for your deployment using the CLI.

### Checking License Status

```bash
# Check current license status
scm get operations licenses
```

## Health Monitoring

Monitor the health of your Strata Cloud Manager deployment.

### System Status

Check the current system status:

```bash
# Get overall system status
scm get operations status
```

### Connectivity Tests

Test connectivity to various services:

```bash
# Test connectivity to firewalls
scm get operations connectivity-test --target firewalls
```

## User Management

The CLI includes commands for managing users and roles.

### Listing Users

```bash
# List all users
scm get operations users
```

### User Roles

```bash
# List available roles
scm get operations roles
```

## Audit Logs

Access audit logs to track changes made through the CLI and other interfaces.

### Retrieving Audit Logs

```bash
# Get recent audit logs
scm get operations audit-logs --limit 20
```

### Filtering Audit Logs

```bash
# Filter audit logs by user
scm get operations audit-logs --filter-user "admin"

# Filter audit logs by date range
scm get operations audit-logs --start-date "2025-03-01" --end-date "2025-03-30"
```

## Scheduled Tasks

Manage scheduled tasks for recurring operations.

### Listing Scheduled Tasks

```bash
# List all scheduled tasks
scm get operations scheduled-tasks
```

### Creating Backup Tasks

```bash
# Create a scheduled backup
scm set operations scheduled-task --type backup --name "Daily-Backup" --schedule "0 0 * * *"
```

## Troubleshooting

The CLI provides tools to help with troubleshooting.

### Diagnostic Tools

```bash
# Run diagnostic checks
scm get operations diagnostics
```

### Log Collection

```bash
# Collect logs for support
scm get operations collect-logs --output-dir "./support-logs"
```

## Best Practices

When using the CLI for operations management:

1. **Use descriptive commit messages** to document your changes
2. **Check job status** after initiating operations that generate jobs
3. **Review audit logs** periodically to track changes
4. **Set up scheduled tasks** for recurring operations
5. **Use the `--verbose` flag** when troubleshooting operations

## Next Steps

- Explore the [Command Reference](../cli/index.md) for detailed information on all available commands
- Learn more about [Advanced Topics](advanced-topics.md) for scripting and automation
- Review [Configuration Objects](configuration-objects.md) to understand the types of resources you can manage
