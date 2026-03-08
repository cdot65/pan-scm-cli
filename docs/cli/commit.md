# Commit

Push pending configuration changes to Strata Cloud Manager.

## Syntax

```bash
scm commit [OPTIONS]
```

## Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder(s) to commit (can specify multiple) | Yes |
| `--description TEXT` | Description of the commit | Yes |
| `--sync` | Wait synchronously for the commit to complete | No |
| `--timeout INT` | Timeout in seconds when using --sync (default: 300) | No |

## Examples

```bash
# Basic commit
$ scm commit --folder Texas --description "Update address objects"

# Multi-folder commit
$ scm commit --folder Texas --folder California --description "Multi-folder update"

# Synchronous commit (waits for completion)
$ scm commit --folder Texas --description "Deploy changes" --sync

# Synchronous with custom timeout
$ scm commit --folder Texas --description "Deploy changes" --sync --timeout 600
```

!!! tip
    After an async commit, use `scm jobs status --id <JOB_ID>` to check progress or `scm jobs wait --id <JOB_ID>` to wait for completion.
