# Agent Version

Agent versions display available GlobalProtect agent versions. This is a read-only resource.

## Show Agent Version

```bash
scm show mobile-agent agent-version [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No |
| `--name TEXT` | Name of specific agent version | No |

### Examples

```bash
# List all agent versions
$ scm show mobile-agent agent-version --folder "Mobile Users"

# Show a specific version
$ scm show mobile-agent agent-version --folder "Mobile Users" --name "5.2.0"
```

!!! note
    Agent versions are read-only. They cannot be created, updated, or deleted.
