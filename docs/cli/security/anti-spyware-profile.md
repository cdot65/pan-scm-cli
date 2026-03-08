# Anti-Spyware Profile

Anti-spyware profiles define threat detection and prevention rules for spyware, command-and-control traffic, and other malicious activity.

## Set Anti-Spyware Profile

```bash
scm set security anti-spyware-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--cloud-inline-analysis / --no-cloud-inline-analysis` | Enable cloud inline analysis | No |
| `--block-critical-high` | Add default rule to block critical and high severity threats | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create basic profile
$ scm set security anti-spyware-profile \
    --folder Texas --name strict-security \
    --description "Block critical threats"

# Create profile blocking critical and high severity
$ scm set security anti-spyware-profile \
    --folder Texas --name block-threats \
    --block-critical-high --cloud-inline-analysis

# Create profile in snippet
$ scm set security anti-spyware-profile \
    --snippet Security-Best-Practice --name standard-protection
```

## Show Anti-Spyware Profile

```bash
scm show security anti-spyware-profile --folder Texas
scm show security anti-spyware-profile --folder Texas --name strict-security
```

## Delete Anti-Spyware Profile

```bash
scm delete security anti-spyware-profile --folder Texas --name strict-security
```

## Load / Backup

```bash
scm load security anti-spyware-profile --file anti-spyware.yaml --folder Texas
scm backup security anti-spyware-profile --folder Texas
```
