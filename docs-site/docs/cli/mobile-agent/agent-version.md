# Agent Version

Agent versions display available GlobalProtect agent versions in Strata Cloud Manager. Agent version management is read-only through the CLI.

## Show Agent Version

Display agent version objects.

### Syntax

```bash
scm show mobile-agent agent-version [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Name of a specific agent version | No |

:::note
When no `--name` is specified, all agent versions are listed by default.
:::

### Examples

#### Show Specific Agent Version

```bash
$ scm show mobile-agent agent-version \
    --folder "Mobile Users" \
    --name "5.2.0"
---> 100%
Agent Version: 5.2.0
  Location: Folder 'Mobile Users'
  Version: 5.2.0
  Platform: Windows
  Release Date: 2024-01-15
```

#### List All Agent Versions (Default Behavior)

```bash
$ scm show mobile-agent agent-version --folder "Mobile Users"
---> 100%
Agent Versions in folder 'Mobile Users':
------------------------------------------------------------
Name: 5.2.0
  Version: 5.2.0
  Platform: Windows
  Release Date: 2024-01-15
------------------------------------------------------------
Name: 5.1.4
  Version: 5.1.4
  Platform: macOS
  Release Date: 2023-11-20
------------------------------------------------------------
```

:::note
Agent version management is read-only. Agent versions cannot be created, updated, or deleted
through the CLI.
:::
