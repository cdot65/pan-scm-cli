# Installation Guide for pan-scm-cli

This guide will help you install the `pan-scm-cli` tool in your Python environment.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.10 or higher**: Ensure Python is installed on your system.
- **pip**: Python package installer should be available.
- **Access to SCM**: You need valid credentials for Strata Cloud Manager.

## Installation Steps

### 1. Create a Virtual Environment (Optional but _HIGHLY_ Recommended)

It's good practice to use a virtual environment to manage dependencies.

**On macOS and Linux:**

```bash
python3 -m venv scm-env
source scm-env/bin/activate
```

**On Windows:**

```bash
python3 -m venv scm-env
scm-env\Scripts\activate
```

### 2. Install `pan-scm-cli` via pip

Within the activated environment, install the package using pip:

```bash
pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

### 3. Verify Installation

Verify that the installation was successful by checking the available commands:

```bash
$ scm --help

 Usage: scm [OPTIONS] COMMAND [ARGS]...

 CLI for Palo Alto Networks Strata Cloud Manager

Commands:
  backup   Backup configurations to YAML files
  context  Manage authentication contexts for multiple SCM tenants
  delete   Remove configurations
  load     Load configurations from YAML files
  set      Create or update configurations
  show     Display configurations
```

### 4. Set Up Authentication

After installation, create your first context to connect to SCM:

```bash
# Create a context with your credentials
$ scm context create my-tenant \
  --client-id "your-app@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret-key" \
  --tsg-id "123456789"
✓ Context 'my-tenant' created successfully
✓ Context 'my-tenant' set as current

# Test the connection
$ scm context test
Testing authentication for context: my-tenant
✓ Authentication successful!
  Client ID: your-app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
✓ API connectivity verified (found 15 address objects in Shared folder)
```

## Next Steps

Once you've installed the CLI and set up authentication, you can:

1. [Get started with basic commands](getting-started.md)
2. [Explore configuration objects](../guide/configuration-objects.md)
3. [Learn about advanced operations](../guide/advanced-topics.md)

---

If you encounter any issues during installation, see the [Troubleshooting](troubleshooting.md) guide.
