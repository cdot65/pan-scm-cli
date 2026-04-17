# Local Config

Manage local device configuration versions and downloads.

## Commands

### List Config Versions

```bash
scm local list --device fw-01
```

Lists available configuration versions for a device, showing version number, date, author, and description.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device name |

### Download Config

```bash
# Output to stdout
scm local download --device fw-01 --version 42

# Save to file
scm local download --device fw-01 --version 42 --output config.xml
```

Downloads a specific configuration version as XML. Outputs to stdout by default; use `--output` to write to a file.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device name |
| `--version`, `-v` | Yes | Config version number |
| `--output`, `-o` | No | Output file path (default: stdout) |
