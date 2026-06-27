---
title: SCM CLI
slug: /
hide_table_of_contents: false
---

# pan-scm-cli

**Command-line interface for Palo Alto Networks Strata Cloud Manager**

[![PyPI](https://img.shields.io/pypi/v/pan-scm-cli.svg)](https://pypi.org/project/pan-scm-cli/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-%3E%3D3.12-brightgreen.svg)](https://www.python.org/)

Manage your entire Strata Cloud Manager configuration from the terminal. Create,
update, and delete objects, network configs, security policies, and more with a
consistent, scriptable CLI. Context-based authentication supports multiple
tenants, and YAML bulk operations make large deployments easy.

## Highlights

- **Intuitive CLI** — consistent `scm <action> <category> <resource>` structure across 60+ resource types.
- **Bulk operations** — load configurations from YAML files; dry-run mode previews changes before applying.
- **Validated input** — Pydantic models validate every field before sending to the API.
- **Multi-tenant contexts** — named authentication contexts let you switch between SCM tenants instantly, with environment-variable overrides for CI/CD.
- **Full coverage** — objects, network, security, deployment, identity, setup, mobile agent, insights, jobs, and commit operations.
- **Docker ready** — multi-platform images for AMD64 and ARM64.

## How it works

```mermaid
flowchart LR
    A[Create Context] --> B[Authenticate to SCM]
    B --> C[Run CLI Commands]
    C --> D[Validate Input]
    D --> E[Call SCM API]
    E --> F[Display Results]
```

## Get started

- [**Install**](about/installation.md) — prerequisites, installation, and credential setup.
- [**Quick Start**](about/getting-started.md) — create a context and run your first command in minutes.
- [**Configure**](guide/configuration.md) — authentication contexts, environment variables, and Docker setup.
- [**CLI Reference**](cli/index.md) — complete command reference for all 60+ resource types.
