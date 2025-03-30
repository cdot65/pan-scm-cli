# Configuration Guide

## Overview

The `pan-scm-cli` project uses [Dynaconf](https://dynaconf.com) for configuration management, allowing for:

- Environment-specific settings (development, testing, production)
- Secure credential storage
- Environment variable overrides
- Hierarchical configuration

## Configuration Files

### `settings.yaml`

This file contains non-sensitive configuration parameters:

```yaml
---
default:
  # Application settings
  app_name: "pan-scm-cli"
  log_level: "INFO"

  # Environment settings
  environment: "development"

development:
  # Development-specific settings
  debug: true

testing:
  # Test-specific settings
  debug: true

production:
  # Production-specific settings
  debug: false
  log_level: "WARNING"
```

### `.secrets.yaml` (not committed to Git)

This file contains sensitive credentials and is not committed to version control:

```yaml
---
default:
  # API credentials
  scm_client_id: "your-client-id-here"
  scm_client_secret: "your-client-secret-here"
  scm_tsg_id: "your-tsg-id-here"
```

## Required Credentials

The following credentials are required for interacting with the SCM API:

| Credential | Description | Environment Variable |
|------------|-------------|---------------------|
| `scm_client_id` | SCM API Client ID | `SCM_SCM_CLIENT_ID` |
| `scm_client_secret` | SCM API Client Secret | `SCM_SCM_CLIENT_SECRET` |
| `scm_tsg_id` | Tenant Service Group ID | `SCM_SCM_TSG_ID` |

## Using Environment Variables

You can override any configuration value with environment variables by prefixing with `SCM_`:

```bash
export SCM_SCM_CLIENT_ID="your-client-id"
export SCM_SCM_CLIENT_SECRET="your-client-secret"
export SCM_SCM_TSG_ID="your-tsg-id"
```

## CI/CD Configuration

In CI/CD environments (like GitHub Actions), credentials are stored as repository secrets and used to create the `.secrets.yaml` file at runtime.

Required GitHub Secrets:
- `SCM_CLIENT_ID`
- `SCM_CLIENT_SECRET`
- `SCM_TSG_ID`

## Accessing Configuration in Code

```python
from scm_cli.utils.config import settings, get_credentials

# Access a configuration value
log_level = settings.log_level

# Get all credentials as a dictionary
credentials = get_credentials()
client_id = credentials["client_id"]
```
