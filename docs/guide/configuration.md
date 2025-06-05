# Configuration Management with Dynaconf

The pan-scm-cli uses [Dynaconf](https://www.dynaconf.com/) for flexible configuration management, supporting multiple configuration sources with clear precedence rules. The CLI also supports **multi-tenant authentication** through context management, allowing you to easily switch between different SCM environments.

## Multi-Tenant Context Management (Recommended)

The CLI supports managing multiple SCM tenant configurations through contexts. This is the recommended approach for users who work with multiple SCM environments.

### Context Commands

```bash
# List all contexts
scm context list

# Create a new context (interactive)
scm context create production

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
# ~/.scm-cli/contexts/production.yaml
client_id: "prod-app@987654321.iam.panserviceaccount.com"
client_secret: "production-secret-key"
tsg_id: "987654321"
log_level: "WARNING"
```

The current active context is tracked in `~/.scm-cli/current-context`.

### Example: Managing Multiple Tenants

Let me demonstrate a real workflow with multiple tenants:

```bash
# Create context for US production environment
$ scm context create prod-us \
  --client-id "us-prod@111111111.iam.panserviceaccount.com" \
  --client-secret "us-prod-secret" \
  --tsg-id "111111111" \
  --log-level WARNING
✓ Context 'prod-us' created successfully

# Create context for EU production environment
$ scm context create prod-eu \
  --client-id "eu-prod@222222222.iam.panserviceaccount.com" \
  --client-secret "eu-prod-secret" \
  --tsg-id "222222222" \
  --log-level WARNING
✓ Context 'prod-eu' created successfully

# Create development context with debug logging
$ scm context create dev \
  --client-id "dev@333333333.iam.panserviceaccount.com" \
  --client-secret "dev-secret" \
  --tsg-id "333333333" \
  --log-level DEBUG
✓ Context 'dev' created successfully

# List all available contexts
$ scm context list
                           SCM Authentication Contexts                            
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context  ┃ Current ┃ Client ID                                          ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ prod-us  │ ✓       │ us-prod@11...@111111111.iam.panserviceaccount.com │
│ prod-eu  │         │ eu-prod@22...@222222222.iam.panserviceaccount.com │
│ dev      │         │ dev@333333...@333333333.iam.panserviceaccount.com │
└──────────┴─────────┴────────────────────────────────────────────────────┘

# Show details of a specific context
$ scm context show prod-eu
Context: prod-eu

Configuration:
  Client ID: eu-prod@222222222.iam.panserviceaccount.com
  TSG ID: 222222222
  Log Level: WARNING
  Client Secret: ***** (configured)

# Test authentication without switching contexts
$ scm context test prod-eu
Testing authentication for context: prod-eu
✓ Authentication successful!
  Client ID: eu-prod@222222222.iam.panserviceaccount.com
  TSG ID: 222222222
✓ API connectivity verified (found 187 address objects in Shared folder)

# Current context remains unchanged
$ scm context current
Current context: prod-us

Client ID: us-prod@111111111.iam.panserviceaccount.com
TSG ID: 111111111

# Switch to development context
$ scm context use dev
✓ Switched to context 'dev'

Client ID: dev@333333333.iam.panserviceaccount.com
TSG ID: 333333333

# Now all commands use the dev context with DEBUG logging
$ scm show objects address --folder Development
[INFO] Using authentication context: dev
DEBUG:scm_cli.utils.sdk_client:Listing addresses in folder='Development'
Addresses in folder 'Development':
...

# Switch to EU production for operations
$ scm context use prod-eu
✓ Switched to context 'prod-eu'

# Delete a context that's no longer needed
$ scm context delete old-tenant
Are you sure you want to delete context 'old-tenant'? [y/N]: y
✓ Context 'old-tenant' deleted
```

## Configuration Sources

The CLI uses the following configuration sources in order of precedence:

### 1. Current Context (Highest Priority for File-based Config)

When you use `scm context use <name>`, that context's configuration takes precedence:

```yaml
# ~/.scm-cli/contexts/production.yaml
client_id: "prod-app@987654321.iam.panserviceaccount.com"
client_secret: "production-secret-key"
tsg_id: "987654321"
log_level: "WARNING"
```

### 2. Environment Variables (Override Contexts for CI/CD)

Environment variables can override context settings, useful for CI/CD pipelines:

```bash
export SCM_CLIENT_ID="your-client-id@1234567890.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="1234567890"
export SCM_LOG_LEVEL="DEBUG"
```

!!! note "Backward Compatibility"
    The CLI supports both new and legacy environment variable patterns:
    
    - New: `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`
    - Legacy: `SCM_SCM_CLIENT_ID`, `SCM_SCM_CLIENT_SECRET`, `SCM_SCM_TSG_ID`

### 3. Default Settings (Lowest Priority)

The `settings.yaml` file contains default application settings:

```yaml
---
default:
  # Logging configuration
  log_level: "INFO"

production:
  # Production-specific settings
  log_level: "WARNING"
```

!!! warning "Legacy Configuration Files No Longer Supported"
    The following configuration methods are **no longer supported** as of version 0.4.0:
    
    - `~/.scm-cli/config.yaml` - Migrate to contexts using `scm context create`
    - `.secrets.yaml` - Use contexts for development credentials
    
    These files will be ignored if present. Please migrate to the context system for better multi-tenant support.

## Configuration Precedence

When multiple sources define the same setting, the CLI follows this precedence (highest to lowest):

1. Current context configuration (`~/.scm-cli/contexts/<current>.yaml`)
2. Environment variables (when set, they override context values)
3. `settings.yaml` (defaults)

!!! info "Context-First Design"
    The CLI prioritizes contexts to support multi-tenant workflows. Environment variables can still override specific settings when needed for automation or CI/CD.

## Authentication Configuration

The CLI requires three credentials for SCM API authentication:

| Setting         | Environment Variable | Description                   |
|-----------------|----------------------|-------------------------------|
| `client_id`     | `SCM_CLIENT_ID`      | Service account client ID     |
| `client_secret` | `SCM_CLIENT_SECRET`  | Service account client secret |
| `tsg_id`        | `SCM_TSG_ID`         | Tenant Service Group ID       |

### Testing Authentication

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

### Authentication Fallback

If no credentials are configured, the CLI automatically enters **mock mode**:

```bash
$ scm list address
⚠️  No API credentials found. Using mock mode.
```

## Available Settings

### Used Settings

| Setting         | Default  | Environment Variable | Usage                                 |
|-----------------|----------|----------------------|---------------------------------------|
| `log_level`     | `"INFO"` | `SCM_LOG_LEVEL`      | Controls SDK client logging verbosity |
| `client_id`     | None     | `SCM_CLIENT_ID`      | SCM API authentication                |
| `client_secret` | None     | `SCM_CLIENT_SECRET`  | SCM API authentication                |
| `tsg_id`        | None     | `SCM_TSG_ID`         | SCM API tenant identification         |

### Unused Settings

The following settings are defined in `settings.yaml` but not currently used by the CLI:

| Setting       | Default         | Purpose                                          |
|---------------|-----------------|--------------------------------------------------|
| `app_name`    | `"pan-scm-cli"` | Application identifier (reserved for future use) |
| `environment` | `"development"` | Environment mode (reserved for future use)       |
| `debug`       | `true`/`false`  | Debug mode flag (reserved for future use)        |

## Configuration Examples

### Example 1: Multi-Tenant Setup with Contexts

```bash
# Create contexts for different environments
scm context create production \
  --client-id "prod-app@987654321.iam.panserviceaccount.com" \
  --client-secret "production-secret-key" \
  --tsg-id "987654321" \
  --log-level WARNING

scm context create development \
  --client-id "dev-app@123456789.iam.panserviceaccount.com" \
  --client-secret "dev-secret-key" \
  --tsg-id "123456789" \
  --log-level DEBUG

# Switch between environments
scm context use production
scm show objects address --folder Texas

scm context use development
scm show objects address --folder DevFolder
```

### Example 2: CI/CD Setup with Environment Variables

```bash
# Set credentials for automated workflows
export SCM_CLIENT_ID="ci-app@555555555.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="ci-secret-key"
export SCM_TSG_ID="555555555"
export SCM_LOG_LEVEL="WARNING"

# Run commands in CI pipeline
scm context test
scm load objects address --file addresses.yaml --folder Production
```

### Example 3: Context with Environment Variable Override

```bash
# Use a context as base configuration
scm context use staging

# Override specific settings for a one-off command
SCM_LOG_LEVEL=DEBUG scm show objects address --folder Texas
```

## Debugging Configuration

To see which configuration values are being loaded:

```python
# In Python
from scm_cli.utils.config import settings

print(f"Client ID: {settings.get('client_id', 'NOT SET')}")
print(f"Log Level: {settings.get('log_level', 'NOT SET')}")
```

## Technical Implementation

### Context-Aware Dynaconf Initialization

The CLI initializes dynaconf with context awareness in `src/scm_cli/utils/context.py`:

```python
def get_context_aware_settings() -> Dynaconf:
    """Get Dynaconf settings with context awareness."""
    # Start with only the base settings file
    settings_files = ["settings.yaml"]
    
    # Add current context file FIRST so it has priority
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
- `environments=False`: Disables dynaconf's environment switching
- `merge_enabled=True`: Merges configurations from all sources

### Configuration Access Pattern

The CLI uses a centralized `get_auth_config()` function to retrieve credentials:

```python
def get_auth_config():
    """Get authentication configuration from various sources."""
    # Check settings (includes env vars and config files)
    client_id = settings.get("client_id") or settings.get("scm_client_id")
    client_secret = settings.get("client_secret") or settings.get("scm_client_secret")
    tsg_id = settings.get("tsg_id") or settings.get("scm_tsg_id")
    
    return client_id, client_secret, tsg_id
```

## Best Practices

1. **Use contexts** for managing multiple SCM tenants - this is the recommended approach
2. **Use environment variables** only for CI/CD pipelines and automation
3. **Never commit secrets** to version control
4. **Set appropriate log levels** for different environments (INFO for general use, WARNING for production)
5. **Test with mock mode** before using real credentials
6. **Use context test** to verify authentication without switching contexts
7. **Name contexts meaningfully** (e.g., production, staging, dev-tenant1)

## Troubleshooting

### Configuration Not Loading

1. Check environment variable names (must start with `SCM_`)
2. Verify file paths and permissions
3. Ensure YAML syntax is correct
4. Use `settings.reload()` to force reload configuration

### Credential Issues

1. Verify all three credentials are set (client_id, client_secret, tsg_id)
2. Check for typos in environment variable names
3. Ensure credentials have proper SCM permissions
4. Test with mock mode to isolate authentication issues