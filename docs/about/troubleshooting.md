# Troubleshooting Guide

If you encounter issues while using `pan-scm-cli`, this guide provides solutions to common problems.

## Common Issues and Solutions

### 1. Authentication Failures

**Problem:** Unable to authenticate with the SCM API.

**Solutions:**

- **Check Current Context**: Verify which context is active and test it:
  ```bash
  $ scm context current
  Current context: production
  
  $ scm context test
  Testing authentication for context: production
  ✗ Authentication failed: (invalid_client) Client authentication failed
  ```

- **Verify Context Credentials**: Show the context details to check configuration:
  ```bash
  $ scm context show production
  Context: production
  
  Configuration:
    Client ID: prod@123456789.iam.panserviceaccount.com
    TSG ID: 123456789
    Log Level: INFO
    Client Secret: ***** (configured)
  ```

- **Create New Context**: If credentials are incorrect, create a new context:
  ```bash
  $ scm context create production-fixed \
    --client-id "correct-id@123456789.iam.panserviceaccount.com" \
    --client-secret "correct-secret" \
    --tsg-id "123456789"
  ✓ Context 'production-fixed' created successfully
  ```

- **Environment Variable Override**: Check if environment variables are overriding your context:
  ```bash
  # Check for SCM environment variables
  $ env | grep SCM_
  SCM_CLIENT_ID=old-value
  
  # Unset them to use context
  $ unset SCM_CLIENT_ID SCM_CLIENT_SECRET SCM_TSG_ID
  ```

- **Network Issues**: Test connectivity to SCM API endpoints
- **Permissions**: Verify your service account has necessary permissions in SCM

### 2. Command Execution Errors

**Problem:** Commands fail to execute or produce unexpected results.

**Solutions:**

- **Check Command Syntax**: Verify that you're using the correct command syntax (`scm <action> <resource-type> <resource>`).
- **Required Parameters**: Ensure that all required parameters for the command are provided.
- **Validate Input**: Check that parameter values meet the required formats and constraints.
- **Review Output**: Examine command output for specific error messages that may indicate the issue.

### 3. Resource Operation Failures

**Problem:** Unable to create, update, or delete resources.

**Solutions:**

- **Resource Existence**: For updates and deletions, confirm that the referenced resource exists.
- **Resource Conflicts**: Ensure there are no naming conflicts or dependencies preventing the operation.
- **Field Validation**: Check that all field values meet SCM's requirements (e.g., name formats, IP formats).
- **Permissions**: Verify you have the necessary permissions to perform the operation on the resource.

### 4. Bulk Loading Issues

**Problem:** Errors when loading resources from YAML files.

**Solutions:**

- **YAML Syntax**: Ensure your YAML files are properly formatted without syntax errors.
- **Schema Compliance**: Verify that your YAML structure follows the expected schema for the resource type.
- **File Paths**: Check that file paths provided to the `load` command are correct.
- **Use Verbose Mode**: Add `-v` or `--verbose` to get more detailed error information.

## Enabling Debug Logging

For more detailed troubleshooting, you can enable debug logging:

### Method 1: Set log level in context
```bash
# Create or update context with DEBUG logging
$ scm context create debug-env \
  --client-id "your-id@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret" \
  --tsg-id "123456789" \
  --log-level DEBUG
✓ Context 'debug-env' created successfully

$ scm context use debug-env
✓ Switched to context 'debug-env'
```

### Method 2: Use environment variable (overrides context setting)
```bash
export SCM_LOG_LEVEL=DEBUG
scm show object address --folder Texas
```

This will produce verbose output showing each API call, request payloads, and response details.

## Common Error Messages

| Error Message           | Likely Cause                                 | Solution                                               |
| ----------------------- | -------------------------------------------- | ------------------------------------------------------ |
| "Authentication failed" | Invalid credentials                          | Check your client ID, secret, and TSG ID               |
| "Resource not found"    | Attempting to access a non-existent resource | Verify the resource name or create it first            |
| "Validation error"      | Input data doesn't meet requirements         | Check the error details for specific field issues      |
| "Permission denied"     | Insufficient permissions                     | Request necessary permissions for your API credentials |
| "Connection error"      | Network or API endpoint issues               | Check your network connection and SCM service status   |

## Getting Help

If you continue to experience issues:

1. Check for similar issues in the [GitHub repository](https://github.com/cdot65/pan-scm-cli/issues)
2. Submit a new issue with detailed information about your problem
3. Include relevant error messages and steps to reproduce the issue

---

For additional assistance, refer to the [CLI Reference](../cli/index.md) for detailed command documentation.
