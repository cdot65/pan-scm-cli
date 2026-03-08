# URL Access Profile

URL access profiles define URL filtering policies that control access to websites by category. The `scm` CLI provides commands to create, update, delete, and load URL access profiles.

## Overview

The `url-access-profile` commands allow you to:

- Create URL access profiles with category-based filtering actions
- Update existing profile configurations including safe search and credential enforcement
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set URL Access Profile

Create or update a URL access profile.

### Syntax

```bash
scm set security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Description | No |
| `--block TEXT` | URL categories to block (can specify multiple) | No |
| `--alert TEXT` | URL categories to alert (can specify multiple) | No |
| `--allow TEXT` | URL categories to allow (can specify multiple) | No |
| `--credential-enforcement TEXT` | Credential enforcement as JSON | No |
| `--cloud-inline-cat / --no-cloud-inline-cat` | Enable cloud inline categorization | No |
| `--safe-search / --no-safe-search` | Enable safe search enforcement | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Profile with Blocked Categories

```bash
$ scm set security url-access-profile \
    --folder Texas \
    --name strict-url \
    --block adult \
    --block malware \
    --alert hacking
---> 100%
Created URL access profile: strict-url in folder Texas
```

#### Create Profile with Safe Search

```bash
$ scm set security url-access-profile \
    --folder Texas \
    --name safe-browsing \
    --block adult \
    --block gambling \
    --safe-search \
    --cloud-inline-cat
---> 100%
Created URL access profile: safe-browsing in folder Texas
```

## Delete URL Access Profile

Delete a URL access profile from SCM.

### Syntax

```bash
scm delete security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name to delete | Yes |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security url-access-profile \
    --folder Texas \
    --name strict-url
---> 100%
Deleted URL access profile: strict-url from folder Texas
```

## Load URL Access Profile

Load multiple URL access profiles from a YAML file.

### Syntax

```bash
scm load security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing profile definitions | Yes |
| `--folder TEXT` | Override folder location for all profiles | No |
| `--snippet TEXT` | Override snippet location for all profiles | No |
| `--device TEXT` | Override device location for all profiles | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
url_access_profiles:
  - name: strict-url
    folder: Texas
    description: "Strict URL filtering"
    block:
      - adult
      - malware
    alert:
      - hacking

  - name: safe-browsing
    folder: Texas
    description: "Safe browsing with search enforcement"
    block:
      - adult
      - gambling
    safe_search: true
    cloud_inline_cat: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load security url-access-profile \
    --file url-profiles.yaml
---> 100%
✓ Loaded URL access profile: strict-url
✓ Loaded URL access profile: safe-browsing

Successfully loaded 2 out of 2 URL access profiles from 'url-profiles.yaml'
```

#### Load with Folder Override

```bash
$ scm load security url-access-profile \
    --file url-profiles.yaml \
    --folder Austin
---> 100%
✓ Loaded URL access profile: strict-url
✓ Loaded URL access profile: safe-browsing

Successfully loaded 2 out of 2 URL access profiles from 'url-profiles.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show URL Access Profile

Display URL access profile objects.

### Syntax

```bash
scm show security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name to display | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Profile

```bash
$ scm show security url-access-profile \
    --folder Texas \
    --name strict-url
---> 100%
URL Access Profile: strict-url
  Location: Folder 'Texas'
  Description: Strict URL filtering
  Block: adult, malware
  Alert: hacking
```

#### List All Profiles (Default Behavior)

```bash
$ scm show security url-access-profile --folder Texas
---> 100%
URL Access Profiles in folder 'Texas':
------------------------------------------------------------
Name: strict-url
  Description: Strict URL filtering
  Block: adult, malware
------------------------------------------------------------
Name: safe-browsing
  Description: Safe browsing with search enforcement
  Safe Search: enabled
------------------------------------------------------------
```

## Backup URL Access Profiles

Backup all URL access profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup profiles from | No\* |
| `--snippet TEXT` | Snippet to backup profiles from | No\* |
| `--device TEXT` | Device to backup profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup security url-access-profile --folder Texas
---> 100%
Successfully backed up 4 URL access profiles to url_access_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security url-access-profile \
    --folder Texas \
    --file texas-url-profiles.yaml
---> 100%
Successfully backed up 4 URL access profiles to texas-url-profiles.yaml
```

## Best Practices

1. **Block High-Risk Categories**: Always block categories like malware, phishing, and command-and-control to protect against threats.
2. **Use Alert for Monitoring**: Set categories to alert mode initially to monitor user behavior before enforcing blocks.
3. **Enable Safe Search**: Use `--safe-search` to enforce safe search on search engines for compliance and content filtering.
4. **Enable Cloud Categorization**: Use `--cloud-inline-cat` for real-time URL categorization of newly discovered websites.
5. **Backup Before Changes**: Always backup existing profiles before making bulk modifications via load commands.
