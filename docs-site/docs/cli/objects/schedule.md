# Schedule

Schedules define time-based policies for security rule enforcement. The `scm` CLI supports recurring daily, recurring weekly, and non-recurring schedule types.

## Overview

The `schedule` commands allow you to:

- Create recurring daily schedules with time ranges
- Create recurring weekly schedules with per-day time ranges
- Create non-recurring schedules for one-time windows
- Delete schedules that are no longer needed
- Bulk import schedules from YAML files
- Export schedules for backup or migration

## Set Schedule

Create or update a schedule.

### Syntax

```bash
scm set object schedule NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the schedule (positional) | Yes |
| `--schedule-type TEXT` | Schedule type: recurring-daily, recurring-weekly, or non-recurring | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--time-range TEXT` | Time ranges (for daily/non-recurring) | No |
| `--monday TEXT` | Monday time ranges (for weekly) | No |
| `--tuesday TEXT` | Tuesday time ranges (for weekly) | No |
| `--wednesday TEXT` | Wednesday time ranges (for weekly) | No |
| `--thursday TEXT` | Thursday time ranges (for weekly) | No |
| `--friday TEXT` | Friday time ranges (for weekly) | No |
| `--saturday TEXT` | Saturday time ranges (for weekly) | No |
| `--sunday TEXT` | Sunday time ranges (for weekly) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Recurring Daily Schedule

```bash
$ scm set object schedule business-hours \
    --schedule-type recurring-daily \
    --folder Texas \
    --time-range "08:00-17:00"
---> 100%
Created schedule: business-hours in folder Texas
```

#### Create a Recurring Weekly Schedule

```bash
$ scm set object schedule weekday-schedule \
    --schedule-type recurring-weekly \
    --folder Texas \
    --monday "09:00-17:00" \
    --tuesday "09:00-17:00" \
    --wednesday "09:00-17:00" \
    --thursday "09:00-17:00" \
    --friday "09:00-12:00"
---> 100%
Created schedule: weekday-schedule in folder Texas
```

## Delete Schedule

Delete a schedule from SCM.

### Syntax

```bash
scm delete object schedule NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the schedule (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object schedule business-hours --folder Texas --force
---> 100%
Deleted schedule: business-hours from folder Texas
```

## Load Schedules

Load multiple schedules from a YAML file.

### Syntax

```bash
scm load object schedule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing schedule definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
schedules:
  - name: business-hours
    folder: Texas
    schedule_type: recurring-daily
    time_range: "08:00-17:00"

  - name: weekday-schedule
    folder: Texas
    schedule_type: recurring-weekly
    days_monday: "09:00-17:00"
    days_tuesday: "09:00-17:00"
    days_wednesday: "09:00-17:00"
    days_thursday: "09:00-17:00"
    days_friday: "09:00-12:00"
```

### Examples

#### Load with Original Locations

```bash
$ scm load object schedule --file schedules.yaml
---> 100%
✓ Loaded schedule: business-hours
✓ Loaded schedule: weekday-schedule

Successfully loaded 2 out of 2 schedules from 'schedules.yaml'
```

#### Load with Folder Override

```bash
$ scm load object schedule --file schedules.yaml --folder Austin
---> 100%
✓ Loaded schedule: business-hours
✓ Loaded schedule: weekday-schedule

Successfully loaded 2 out of 2 schedules from 'schedules.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all schedules
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Schedule

Display schedule objects.

### Syntax

```bash
scm show object schedule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of specific schedule to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Schedule

```bash
$ scm show object schedule --folder Texas --name business-hours
---> 100%
Schedule: business-hours
  Location: Folder 'Texas'
  Type: recurring-daily
  Time Range: 08:00-17:00
```

#### List All Schedules (Default Behavior)

```bash
$ scm show object schedule --folder Texas
---> 100%
Schedules in folder 'Texas':
------------------------------------------------------------
Name: business-hours
  Type: recurring-daily
  Time Range: 08:00-17:00
------------------------------------------------------------
Name: weekday-schedule
  Type: recurring-weekly
  Monday: 09:00-17:00
  Tuesday: 09:00-17:00
  Wednesday: 09:00-17:00
  Thursday: 09:00-17:00
  Friday: 09:00-12:00
------------------------------------------------------------
```

## Backup Schedules

Backup all schedule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object schedule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup schedules from | No\* |
| `--snippet TEXT` | Snippet to backup schedules from | No\* |
| `--device TEXT` | Device to backup schedules from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object schedule --folder Texas
---> 100%
Successfully backed up 5 schedules to schedule_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object schedule --folder Texas --file texas-schedules.yaml
---> 100%
Successfully backed up 5 schedules to texas-schedules.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name schedules after their purpose (e.g., business-hours, maintenance-window).
2. **Time Format**: Use 24-hour format (HH:MM) for time ranges.
3. **Weekly Schedules**: Only define days that need specific time ranges.
4. **Use YAML for Bulk Operations**: For managing multiple schedules, use YAML files.
5. **Organize by Folder**: Keep schedules organized in logical folders alongside related policies.
