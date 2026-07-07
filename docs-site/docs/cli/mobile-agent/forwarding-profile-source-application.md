# Forwarding Profile Source Application

Forwarding profile source applications define the lists of applications used as source-application match criteria by GlobalProtect forwarding profiles in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load source applications.

## Overview

The `forwarding-profile-source-application` commands allow you to:

- Create source application lists for forwarding profile rules
- Update existing source application configurations
- Delete source applications that are no longer needed
- Bulk import source applications from YAML files
- Export source applications for backup or migration

:::note
Forwarding profile source applications live exclusively in the `Mobile Users` folder. Snippet and device locations are not supported.
:::

## Set Forwarding Profile Source Application

Create or update a forwarding profile source application.

### Syntax

```bash
scm set mobile-agent forwarding-profile-source-application NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the source application | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--application TEXT` | Application name (repeatable) | Yes |
| `--description TEXT` | Description | No |

### Examples

```bash
$ scm set mobile-agent forwarding-profile-source-application "office-apps" \
    --folder "Mobile Users" \
    --application slack \
    --application zoom \
    --description "Collaboration applications"
Created forwarding profile source application: office-apps in folder Mobile Users
```

## Show Forwarding Profile Source Application

Display forwarding profile source applications.

### Syntax

```bash
scm show mobile-agent forwarding-profile-source-application [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the source application to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

### Examples

```bash
# List all source applications in the folder
$ scm show mobile-agent forwarding-profile-source-application --folder "Mobile Users"

# Show a specific source application by name
$ scm show mobile-agent forwarding-profile-source-application "office-apps" --folder "Mobile Users"
```

## Delete Forwarding Profile Source Application

Remove a forwarding profile source application.

### Syntax

```bash
scm delete mobile-agent forwarding-profile-source-application NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the source application | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--force` | Skip confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent forwarding-profile-source-application "office-apps" --folder "Mobile Users" --force
Deleted forwarding profile source application: office-apps from folder Mobile Users
```

## Backup Forwarding Profile Source Application

Export all forwarding profile source applications from a folder to a YAML file.

### Syntax

```bash
scm backup mobile-agent forwarding-profile-source-application [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from (defaults to `Mobile Users`) | No |
| `--file PATH` | Output file path (defaults to `forwarding-profile-source-application-{location}.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent forwarding-profile-source-application --folder "Mobile Users"
Successfully backed up 2 forwarding profile source applications to forwarding-profile-source-application-mobile-users.yaml
```

## Load Forwarding Profile Source Application

Bulk import forwarding profile source applications from a YAML file.

### Syntax

```bash
scm load mobile-agent forwarding-profile-source-application [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |
| `--folder TEXT` | Override folder location for all objects | No |

### YAML Schema

```yaml
forwarding_profile_source_applications:
  - name: office-apps
    folder: "Mobile Users"
    description: Collaboration applications
    applications:
      - slack
      - zoom
  - name: dev-apps
    folder: "Mobile Users"
    applications:
      - github
```

### Examples

```bash
# Preview without applying
$ scm load mobile-agent forwarding-profile-source-application --file source_applications.yml --dry-run

# Apply the configurations
$ scm load mobile-agent forwarding-profile-source-application --file source_applications.yml
Created forwarding profile source application: office-apps
Created forwarding profile source application: dev-apps

Summary: 2 created, 0 updated, 0 unchanged
```
