# Schedule

Schedules define time-based policies for security rule enforcement. Supports recurring daily, recurring weekly, and non-recurring schedule types.

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
| `--folder TEXT` | Folder location | No |
| `--snippet TEXT` | Snippet location | No |
| `--device TEXT` | Device location | No |
| `--time-range TEXT` | Time ranges (for daily/non-recurring) | No |
| `--days-monday TEXT` | Monday time ranges (for weekly) | No |
| `--days-tuesday TEXT` | Tuesday time ranges (for weekly) | No |
| `--days-wednesday TEXT` | Wednesday time ranges (for weekly) | No |
| `--days-thursday TEXT` | Thursday time ranges (for weekly) | No |
| `--days-friday TEXT` | Friday time ranges (for weekly) | No |
| `--days-saturday TEXT` | Saturday time ranges (for weekly) | No |
| `--days-sunday TEXT` | Sunday time ranges (for weekly) | No |

### Examples

```bash
# Create a recurring daily schedule
$ scm set object schedule business-hours \
    --schedule-type recurring-daily \
    --folder Texas \
    --time-range "08:00-17:00"

# Create a recurring weekly schedule
$ scm set object schedule weekday-schedule \
    --schedule-type recurring-weekly \
    --folder Texas \
    --days-monday "09:00-17:00" \
    --days-friday "09:00-12:00"
```

## Show Schedule

Display schedule details.

### Syntax

```bash
scm show object schedule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of specific schedule to show | No |
| `--folder TEXT` | Folder location | No |
| `--snippet TEXT` | Snippet location | No |
| `--device TEXT` | Device location | No |

### Example

```bash
$ scm show object schedule --folder Texas
$ scm show object schedule --folder Texas --name business-hours
```

## Delete Schedule

```bash
scm delete object schedule NAME --folder Texas
```

## Load Schedules

```bash
scm load object schedule --file schedules.yaml
```

## Backup Schedules

```bash
scm backup object schedule --folder Texas
```
