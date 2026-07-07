# Global Setting

Global settings are the tenant-wide GlobalProtect configuration singleton in Strata Cloud Manager — the agent version and manual gateway regions. The `scm` CLI provides commands to show and update them.

## Overview

The `global-setting` commands allow you to:

- Show the current GlobalProtect global settings
- Update the agent version and manual gateway configuration

:::note[Singleton semantics]
Global settings always exist for the tenant and are updated in place. There are no `delete`, `backup`, or `load` commands, no `--folder` option, and no `NAME` argument.
:::

## Show Global Setting

Display the current GlobalProtect global settings.

### Syntax

```bash
scm show mobile-agent global-setting
```

### Examples

```bash
$ scm show mobile-agent global-setting

GlobalProtect Global Settings
================================================================================
Agent Version: 6.2.0
Manual Gateway: {region: [{name: americas, locations: [us-east-1]}]}
```

## Set Global Setting

Update the GlobalProtect global settings. At least one option is required.

### Syntax

```bash
scm set mobile-agent global-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--agent-version TEXT` | GlobalProtect agent version | No* |
| `--manual-gateway JSON` | Manual gateway configuration as JSON | No* |

*At least one of the two options must be provided.

### Examples

```bash
$ scm set mobile-agent global-setting --agent-version "6.2.0"
Updated GlobalProtect global settings
```

```bash
$ scm set mobile-agent global-setting \
    --manual-gateway '{"region": [{"name": "americas", "locations": ["us-east-1"]}]}'
Updated GlobalProtect global settings
```
