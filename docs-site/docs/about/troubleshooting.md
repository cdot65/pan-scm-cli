# Troubleshooting

This guide provides solutions to common issues encountered when using the `pan-scm-cli` tool.

## Authentication Failures

**Problem:** Unable to authenticate with the SCM API.

### Check Current Context

Verify which context is active and test it:

```bash
$ scm context current
Current context: production

$ scm context test
Testing authentication for context: production
✓ Authentication successful!
```

If authentication fails:

```bash
$ scm context test
Testing authentication for context: production
✗ Authentication failed: (invalid_client) Client authentication failed
```

### Verify Context Credentials

Show the context details to check configuration:

```bash
$ scm context show production
Context: production

Configuration:
  Client ID: prod@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
  Log Level: INFO
  Client Secret: ***** (configured)
```

### Create New Context

If credentials are incorrect, create a new context:

```bash
$ scm context create production-fixed \
    --client-id "correct-id@123456789.iam.panserviceaccount.com" \
    --client-secret "correct-secret" \
    --tsg-id "123456789"
---> 100%
✓ Context 'production-fixed' created successfully
```

### Check Environment Variable Override

Environment variables take precedence over contexts. Check for conflicts:

```bash
$ env | grep SCM_
SCM_CLIENT_ID=old-value

$ unset SCM_CLIENT_ID SCM_CLIENT_SECRET SCM_TSG_ID
```

:::warning
Environment variables always override context credentials. Unset them
if you want the CLI to use your active context.
:::

### Network and Permission Issues

- Test connectivity to SCM API endpoints from your network
- Verify your service account has the necessary permissions in SCM

## Command Execution Errors

**Problem:** Commands fail to execute or produce unexpected results.

- **Check Command Syntax**: Verify the correct pattern: `scm <action> <category> <resource>`
- **Required Parameters**: Ensure all required parameters are provided
- **Validate Input**: Check that parameter values meet required formats and constraints
- **Review Output**: Examine command output for specific error messages

## Resource Operation Failures

**Problem:** Unable to create, update, or delete resources.

- **Resource Existence**: For updates and deletions, confirm the resource exists
- **Resource Conflicts**: Ensure there are no naming conflicts or dependencies preventing the operation
- **Field Validation**: Check that all field values meet SCM requirements (name formats, IP formats, etc.)
- **Permissions**: Verify you have the necessary permissions to perform the operation

## Bulk Loading Issues

**Problem:** Errors when loading resources from YAML files.

- **YAML Syntax**: Ensure your YAML files are properly formatted without syntax errors
- **Schema Compliance**: Verify your YAML structure follows the expected schema for the resource type
- **File Paths**: Check that file paths provided to the `load` command are correct
- **Use Verbose Mode**: Add `--verbose` to get more detailed error information

:::tip
Use `--dry-run` with load commands to validate your YAML file before
applying changes.
:::

## Enabling Debug Logging

For detailed troubleshooting, enable debug logging.

### Method 1: Set Log Level in Context

```bash
$ scm context create debug-env \
    --client-id "your-id@123456789.iam.panserviceaccount.com" \
    --client-secret "your-secret" \
    --tsg-id "123456789" \
    --log-level DEBUG
---> 100%
✓ Context 'debug-env' created successfully

$ scm context use debug-env
✓ Switched to context 'debug-env'
```

### Method 2: Use Environment Variable

```bash
export SCM_LOG_LEVEL=DEBUG
scm show object address --folder Texas
```

This produces verbose output showing each API call, request payloads, and response details.

## Error Message Format

All CLI errors follow a consistent format and are written to **stderr**:

```
Error <operation>: <details>
```

For example:

```
Error creating address: Folder Texas doesn't exist
Error deleting zone: Resource not found: my-zone in folder Shared
Error loading services: Empty or invalid YAML file: services.yaml
```

This format is produced by the `@handle_command_errors` decorator used across all command functions. The CLI exits with code 1 on any error.

:::tip
Since errors go to stderr, you can separate them from normal output in scripts:
```bash
scm set object address test --folder Texas --ip-netmask 10.0.0.1/32 2>errors.log
```
:::

## Common Error Messages

| Error Message | Likely Cause | Solution |
| --- | --- | --- |
| `Error ... Authentication failed` | Invalid credentials | Check your client ID, secret, and TSG ID |
| `Error ... Resource not found` | Accessing a non-existent resource | Verify the resource name or create it first |
| `Error ... Validation error` | Input data does not meet requirements | Check error details for specific field issues |
| `Error ... Permission denied` | Insufficient permissions | Request necessary permissions for your API credentials |
| `Error ... Connection error` | Network or API endpoint issues | Check your network connection and SCM service status |

## Getting Help

If you continue to experience issues:

1. **Search existing issues** in the [GitHub repository](https://github.com/cdot65/pan-scm-cli/issues)
2. **Submit a new issue** with detailed information about your problem
3. **Include relevant details**: error messages, command used, and steps to reproduce

For additional assistance, refer to the [CLI Reference](../cli/index.md) for detailed command documentation.
