# Troubleshooting Guide

If you encounter issues while using `pan-scm-cli`, this guide provides solutions to common problems.

## Common Issues and Solutions

### 1. Authentication Failures

**Problem:** Unable to authenticate with the SCM API.

**Solutions:**

- **Check Environment Variables**: Ensure that `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, and `SCM_TSG_ID` are correctly set.
- **Check Local Secrets File**: If using a local configuration, verify that credentials are properly configured in `.secrets.yaml` in the directory where you're running the CLI.
- **File Location**: Make sure you're running the CLI from the same directory where your `.secrets.yaml` file is located, as dynaconf looks for this file in the current working directory.
- **File Format**: Ensure your `.secrets.yaml` follows the correct format with the `default` section.
- **Permissions**: Verify that your credentials have the necessary permissions to access the API.
- **Network Issues**: Ensure there are no network issues blocking access to the SCM authentication endpoint.

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

```bash
export SCM_CLI_LOG_LEVEL=DEBUG
scm <command>
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
