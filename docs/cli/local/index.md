# Local Config

Manage local device configuration versions and downloads.

## Commands

### List Config Versions

```bash
scm local list --device 007951000123456
```

Lists available configuration versions for a device, showing version number, timestamp, serial number, and MD5 hash.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device serial number (14-15 digits) |

### Download Config

```bash
# Output to stdout
scm local download --device 007951000123456 --version 42

# Save to file
scm local download --device 007951000123456 --version 42 --output config.xml
```

Downloads a specific configuration version as XML. Outputs to stdout by default; use `--output` to write to a file.

**Options:**

| Option | Required | Description |
|--------|----------|-------------|
| `--device`, `-d` | Yes | Device serial number (14-15 digits) |
| `--version`, `-v` | Yes | Config version number |
| `--output`, `-o` | No | Output file path (default: stdout) |
