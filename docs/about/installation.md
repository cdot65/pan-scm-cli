# Installation Guide for pan-scm-cli

This guide will help you install the `pan-scm-cli` tool in your Python environment.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.10 or higher**: Ensure Python is installed on your system.
- **pip**: Python package installer should be available.
- **Access to SCM**: You need valid credentials for Strata Cloud Manager.

## Installation Steps

### 1. Create a Virtual Environment (Optional but *HIGHLY* Recommended)

It's good practice to use a virtual environment to manage dependencies.

**On macOS and Linux:**

<div class="termy">

<!-- termynal -->

```bash
$ python3 -m venv scm-env
$ source scm-env/bin/activate
```

</div>

**On Windows:**

<div class="termy">

<!-- termynal -->

```bash
$ python3 -m venv scm-env
$ scm-env\Scripts\activate
```

</div>

### 2. Install `pan-scm-cli` via pip

Within the activated environment, install the package using pip:

<div class="termy">

<!-- termynal -->

```bash
$ pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

</div>

### 3. Verify Installation

Verify that the installation was successful by checking the available commands:

<div class="termy">

<!-- termynal -->

```bash
$ scm-cli --help
Usage: scm-cli [OPTIONS] COMMAND [ARGS]...

  Command line tool for Palo Alto Networks Strata Cloud Manager.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  delete  Delete resources from SCM.
  load    Load configuration data from files.
  set     Create or update resources in SCM.
```

</div>

## Next Steps

Once you've installed the CLI, proceed to:

1. [Configure authentication](getting-started.md#authentication-setup) with your SCM credentials
2. Set up your SCM environment
3. Start managing your SCM resources

---

If you encounter any issues during installation, see the [Troubleshooting](troubleshooting.md) guide.
