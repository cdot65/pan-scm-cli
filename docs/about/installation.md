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

````bash
$ scm --help
INFO:scm_cli.utils.sdk_client:Initializing SCM client
INFO:scm_cli.utils.sdk_client:Successfully initialized SDK client for TSG ID: 1527824794

 Usage: scm [OPTIONS] COMMAND [ARGS]...

 CLI for Palo Alto Networks Strata Cloud Manager

Commands
test-auth   Test authentication configuration.
backup      Backup configurations to YAML files
load        Load configurations from YAML files
set         Create or update configurations
show        Display configurations
```

## Next Steps

Once you've installed the CLI, proceed to:

1. [Configure authentication](getting-started.md#authentication-setup) with your SCM credentials
2. Set up your SCM environment
3. Start managing your SCM resources

---

If you encounter any issues during installation, see the [Troubleshooting](troubleshooting.md) guide.
````
