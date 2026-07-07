# Configuration Management

The `scm` CLI uses Dynaconf for flexible configuration management, supporting multiple configuration sources with clear precedence rules. The CLI also supports multi-tenant authentication through context management, allowing you to switch between different SCM environments.

## Overview

This guide explains how to configure the CLI for your environment:

- Manage multiple SCM tenants with context-based authentication
- Configure environment variables for CI/CD pipelines
- Understand configuration precedence across sources
- Debug and troubleshoot configuration issues

## Prerequisites

Before configuring the CLI, ensure you have:

- The `scm` CLI installed (see [Getting Started](getting-started.md))
- Service account credentials for at least one SCM tenant
- Access to create files in `~/.scm-cli/` (for context storage)

## Core Concepts

### Configuration Precedence

When multiple sources define the same setting, the CLI follows this precedence (highest to lowest):

1. Environment variables (when set, they override everything)
2. Current context configuration (`~/.scm-cli/contexts/<current>.yaml`)
3. `settings.yaml` defaults

:::info
The CLI prioritizes contexts to support multi-tenant workflows. Environment
variables can still override specific settings when needed for automation or CI/CD.
:::

### Authentication Credentials

The CLI requires three credentials for SCM API authentication:

| Setting | Environment Variable | Description |
| --- | --- | --- |
| `client_id` | `SCM_CLIENT_ID` | Service account client ID |
| `client_secret` | `SCM_CLIENT_SECRET` | Service account client secret |
| `tsg_id` | `SCM_TSG_ID` | Tenant Service Group ID |

### API Endpoint Overrides

By default the SDK talks to the production SCM endpoints. Both can be
overridden per context or via environment variables (env wins over context;
when unset, the SDK defaults apply):

| Setting | Environment Variable | Description |
| --- | --- | --- |
| `api_base_url` | `SCM_API_BASE_URL` | Override the SCM API base URL |
| `token_url` | `SCM_TOKEN_URL` | Override the OAuth2 token URL |

```bash
# Persist per context
$ scm context create fedramp \
    --client-id "fed@333333333.iam.panserviceaccount.com" \
    --client-secret "fed-secret" \
    --tsg-id "333333333" \
    --api-base-url "https://api.example.paloaltonetworks.com" \
    --token-url "https://auth.example.paloaltonetworks.com/am/oauth2/access_token"

# Or override for a one-off command
SCM_API_BASE_URL="https://api.example.paloaltonetworks.com" scm context test
```

### Missing Credentials

If no credentials are configured, commands fail with a clear error (exit code 1)
and remediation steps — the CLI never silently falls back to mock data:

```bash
$ scm show object address --folder Shared

❌ Authentication not configured: Missing required authentication parameters: client_id, client_secret, tsg_id

To fix this issue:
  1. Create a context: scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>
  2. Switch context: scm context use <name>
  3. Or use environment variables: SCM_CLIENT_ID, SCM_CLIENT_SECRET, SCM_TSG_ID
```

### Mock Mode

To test commands without credentials or API calls, opt in explicitly with the
`SCM_MOCK` environment variable (or the `--mock` flag where available):

```bash
$ SCM_MOCK=1 scm show object address --folder Shared
```

## Examples

### Multi-Tenant Setup with Contexts

#### Creating Contexts

```bash
$ scm context create prod-us \
    --client-id "us-prod@111111111.iam.panserviceaccount.com" \
    --client-secret "us-prod-secret" \
    --tsg-id "111111111" \
    --log-level WARNING
---> 100%
✓ Context 'prod-us' created successfully
```

```bash
$ scm context create prod-eu \
    --client-id "eu-prod@222222222.iam.panserviceaccount.com" \
    --client-secret "eu-prod-secret" \
    --tsg-id "222222222" \
    --log-level WARNING
---> 100%
✓ Context 'prod-eu' created successfully
```

```bash
$ scm context create dev \
    --client-id "dev@333333333.iam.panserviceaccount.com" \
    --client-secret "dev-secret" \
    --tsg-id "333333333" \
    --log-level DEBUG
---> 100%
✓ Context 'dev' created successfully
```

#### Listing and Inspecting Contexts

```bash
$ scm context list
                           SCM Authentication Contexts
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context  ┃ Current ┃ Client ID                                          ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ prod-us  │ ✓       │ us-prod@11...@111111111.iam.panserviceaccount.com │
│ prod-eu  │         │ eu-prod@22...@222222222.iam.panserviceaccount.com │
│ dev      │         │ dev@333333...@333333333.iam.panserviceaccount.com │
└──────────┴─────────┴────────────────────────────────────────────────────┘
```

```bash
$ scm context show prod-eu
Context: prod-eu

Configuration:
  Client ID: eu-prod@222222222.iam.panserviceaccount.com
  TSG ID: 222222222
  Log Level: WARNING
  Client Secret: ***** (configured)
```

#### Switching and Testing Contexts

```bash
$ scm context test prod-eu
Testing authentication for context: prod-eu
✓ Authentication successful!
  Client ID: eu-prod@222222222.iam.panserviceaccount.com
  TSG ID: 222222222
✓ API connectivity verified (found 187 address objects in Shared folder)
```

```bash
$ scm context use dev
---> 100%
✓ Switched to context 'dev'

Client ID: dev@333333333.iam.panserviceaccount.com
TSG ID: 333333333
```

#### Using Commands with Active Context

```bash
$ scm show object address --folder Development
[INFO] Using authentication context: dev
DEBUG:scm_cli.utils.sdk_client:Listing addresses in folder='Development'
Addresses in folder 'Development':
...
```

#### Deleting a Context

```bash
$ scm context delete old-tenant
Are you sure you want to delete context 'old-tenant'? [y/N]: y
✓ Context 'old-tenant' deleted
```

### Context Commands Reference

```bash
# List all contexts
scm context list

# Create a new context (non-interactive)
scm context create staging \
    --client-id "staging@123456.iam.panserviceaccount.com" \
    --client-secret "your-secret" \
    --tsg-id "123456" \
    --log-level INFO

# Switch to a different context
scm context use production

# Show current context
scm context current

# Show details of a specific context
scm context show staging

# Delete a context
scm context delete old-tenant

# Test authentication for a specific context
scm context test production
scm context test staging --mock

# Test current context
scm context test
```

### Context Storage

Contexts are stored in `~/.scm-cli/contexts/` as individual YAML files:

```yaml
---
# ~/.scm-cli/contexts/production.yaml
client_id: "prod-app@987654321.iam.panserviceaccount.com"
client_secret: "production-secret-key"
tsg_id: "987654321"
log_level: "WARNING"
```

The current active context is tracked in `~/.scm-cli/current-context`.

### CI/CD Setup with Environment Variables

```bash
# Set credentials for automated workflows
export SCM_CLIENT_ID="ci-app@555555555.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="ci-secret-key"
export SCM_TSG_ID="555555555"
export SCM_LOG_LEVEL="WARNING"

# Run commands in CI pipeline
scm context test
scm load object address --file addresses.yaml --folder Production
```

:::tip
The CLI supports both new and legacy environment variable patterns:
new (`SCM_CLIENT_ID`) and legacy (`SCM_SCM_CLIENT_ID`).
:::

### Context with Environment Variable Override

```bash
# Use a context as base configuration
scm context use staging

# Override specific settings for a one-off command
SCM_LOG_LEVEL=DEBUG scm show object address --folder Texas
```

### Switching Between Environments

```bash
# Switch between environments
scm context use production
scm show object address --folder Texas

scm context use development
scm show object address --folder DevFolder
```

## Configuration Sources

### Current Context

When you use `scm context use <name>`, that context's configuration takes effect:

```yaml
---
# ~/.scm-cli/contexts/production.yaml
client_id: "prod-app@987654321.iam.panserviceaccount.com"
client_secret: "production-secret-key"
tsg_id: "987654321"
log_level: "WARNING"
```

### Environment Variables

Environment variables can override context settings:

```bash
export SCM_CLIENT_ID="your-client-id@1234567890.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="1234567890"
export SCM_LOG_LEVEL="DEBUG"
```

### Default Settings

The `settings.yaml` file contains default application settings:

```yaml
---
default:
  log_level: "WARNING"

production:
  log_level: "WARNING"
```

:::warning
The following legacy configuration methods are no longer supported as of version 0.4.0:
`~/.scm-cli/config.yaml` and `.secrets.yaml`. Migrate to contexts using
`scm context create`.
:::

## Available Settings

### Active Settings

| Setting | Default | Environment Variable | Description |
| --- | --- | --- | --- |
| `log_level` | `"WARNING"` | `SCM_LOG_LEVEL` | Controls logging verbosity (CRITICAL, ERROR, WARNING, INFO, DEBUG) |
| `client_id` | None | `SCM_CLIENT_ID` | SCM API authentication |
| `client_secret` | None | `SCM_CLIENT_SECRET` | SCM API authentication |
| `tsg_id` | None | `SCM_TSG_ID` | SCM API tenant identification |
| `api_base_url` | SDK default | `SCM_API_BASE_URL` | Override the SCM API base URL |
| `token_url` | SDK default | `SCM_TOKEN_URL` | Override the OAuth2 token URL |

### Reserved Settings

| Setting | Default | Description |
| --- | --- | --- |
| `app_name` | `"pan-scm-cli"` | Application identifier (reserved for future use) |
| `environment` | `"development"` | Environment mode (reserved for future use) |
| `debug` | `true`/`false` | Debug mode flag (reserved for future use) |

## Testing Authentication

You can test authentication in several ways:

```bash
# Test using current context
scm context test

# Test a specific context without switching
scm context test production

# Test in mock mode (no API calls)
scm context test --mock
scm context test staging --mock
```

## Debugging

### The --debug Flag

Pass the global `--debug` flag to any command for full diagnostics:

```bash
scm --debug show object address --folder Texas
```

`--debug` enables DEBUG-level logging (including the SDK's OAuth/auth loggers,
which are silenced at every other level) and prints full tracebacks on
unexpected errors instead of one-line messages.

### Log Levels

Logging is configured once at CLI startup with this precedence:

1. `--debug` flag (forces DEBUG)
2. `SCM_LOG_LEVEL` environment variable
3. `log_level` in the active context or `settings.yaml`
4. Default: `WARNING`

Valid levels: `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. An invalid value
produces a warning and falls back to `WARNING`.

### Debugging Configuration

To see which configuration values are being loaded:

```python
from scm_cli.utils.config import settings

print(f"Client ID: {settings.get('client_id', 'NOT SET')}")
print(f"Log Level: {settings.get('log_level', 'NOT SET')}")
```

## Technical Implementation

### Context-Aware Dynaconf Initialization

The CLI initializes Dynaconf with context awareness in `src/scm_cli/utils/context.py`:

```python
def get_context_aware_settings() -> Dynaconf:
    """Get Dynaconf settings with context awareness."""
    settings_files = ["settings.yaml"]

    current_context = get_current_context()
    if current_context:
        context_file = os.path.join(CONTEXT_DIR, f"{current_context}.yaml")
        if os.path.exists(context_file):
            settings_files.insert(0, context_file)

    return Dynaconf(
        envvar_prefix="SCM",
        settings_files=settings_files,
        load_dotenv=True,
        environments=False,
        merge_enabled=True,
    )
```

Key configuration options:

- `envvar_prefix="SCM"`: Environment variables must start with `SCM_`
- Context file loaded first for highest file-based priority
- `load_dotenv=True`: Loads `.env` files if present
- `environments=False`: Disables Dynaconf's environment switching
- `merge_enabled=True`: Merges configurations from all sources

### Configuration Access Pattern

The CLI uses a centralized `get_auth_config()` function to retrieve credentials:

```python
def get_auth_config():
    """Get authentication configuration from various sources."""
    client_id = settings.get("client_id") or settings.get("scm_client_id")
    client_secret = settings.get("client_secret") or settings.get("scm_client_secret")
    tsg_id = settings.get("tsg_id") or settings.get("scm_tsg_id")

    return client_id, client_secret, tsg_id
```

## Best Practices

1. **Use contexts for multi-tenant management**: Contexts are the recommended approach for managing multiple SCM tenants.
2. **Reserve environment variables for CI/CD**: Use environment variables only for automation pipelines.
3. **Never commit secrets to version control**: Keep credentials in contexts or environment variables, never in code.
4. **Set appropriate log levels**: Use `INFO` for general use, `WARNING` for production, `DEBUG` for troubleshooting.
5. **Test with mock mode first**: Use `--mock` to validate commands before using real credentials.
6. **Use `context test` to verify authentication**: Test connectivity without switching contexts by specifying the context name.
7. **Name contexts meaningfully**: Use descriptive names like `production`, `staging`, or `dev-tenant1`.

## Troubleshooting

### Configuration Not Loading

1. Check environment variable names (must start with `SCM_`)
2. Verify file paths and permissions for context files
3. Ensure YAML syntax is correct in context files
4. Use `settings.reload()` to force reload configuration

### Credential Issues

1. Verify all three credentials are set (`client_id`, `client_secret`, `tsg_id`)
2. Check for typos in environment variable names
3. Ensure credentials have proper SCM permissions
4. Test with mock mode to isolate authentication issues

## Next Steps

- Review [Getting Started](getting-started.md) for initial setup instructions
- Explore [Working with Configuration Objects](configuration-objects.md) to manage resources
- Read [Advanced CLI Topics](advanced-topics.md) for scripting and automation
