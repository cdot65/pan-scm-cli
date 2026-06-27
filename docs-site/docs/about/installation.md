# Installation

The `pan-scm-cli` tool installs into any Python environment and provides the `scm` command for managing Strata Cloud Manager configurations.

## Prerequisites

Before you begin, ensure you have the following:

| Requirement | Description |
| --- | --- |
| Python 3.10+ | Python 3.10 or higher must be installed on your system |
| pip | Python package installer should be available |
| SCM Credentials | Valid client ID, client secret, and TSG ID for Strata Cloud Manager |

## Install via pip

### Create a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

**macOS and Linux:**

```bash
python3 -m venv scm-env
source scm-env/bin/activate
```

**Windows:**

```bash
python3 -m venv scm-env
scm-env\Scripts\activate
```

### Install the Package

Within the activated environment, install the package using pip:

```bash
$ pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

### Verify Installation

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

## Set Up Authentication

After installation, create your first context to connect to SCM:

```bash
$ scm context create my-tenant \
    --client-id "your-app@123456789.iam.panserviceaccount.com" \
    --client-secret "your-secret-key" \
    --tsg-id "123456789"
---> 100%
✓ Context 'my-tenant' created successfully
✓ Context 'my-tenant' set as current
```

Test the connection:

```bash
$ scm context test
Testing authentication for context: my-tenant
✓ Authentication successful!
  Client ID: your-app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
✓ API connectivity verified (found 15 address objects in Shared folder)
```

:::warning
Never commit credentials to version control. Use contexts or environment variables
to manage authentication securely.
:::

## Docker Installation

The CLI is also available as a Docker image for containerized environments.

```bash
$ docker pull ghcr.io/cdot65/pan-scm-cli:latest
```

Run with context support by volume-mounting your credentials:

```bash
$ docker run -d \
    --name pan-scm \
    -v ~/.scm-cli:/home/scmuser/.scm-cli \
    ghcr.io/cdot65/pan-scm-cli:latest
```

Use contexts inside the container:

```bash
$ docker exec pan-scm scm context list
$ docker exec pan-scm scm context use production
```

:::info
The Docker image is available at `ghcr.io/cdot65/pan-scm-cli:latest` (AMD64) and
`ghcr.io/cdot65/pan-scm-cli:apple` (ARM64).
:::

## Next Steps

1. [Get started with basic commands](getting-started.md)
2. [Explore the CLI Reference](../cli/index.md)
3. [Read the Troubleshooting guide](troubleshooting.md) if you encounter issues
