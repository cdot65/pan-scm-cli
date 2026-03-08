# Commit

Push pending configuration changes to Strata Cloud Manager. The `scm commit` command initiates a commit job for one or more folders, optionally waiting for completion.

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
| `--admin TEXT` | Admin user for commit (required for bearer token auth) | No |

## Examples

#### Basic Commit

```bash
$ scm commit \
    --folder Texas \
    --description "Update address objects"
---> 100%
Commit successful!
Job ID: 12345
```

#### Multi-Folder Commit

```bash
$ scm commit \
    --folder Texas \
    --folder California \
    --description "Multi-folder update"
---> 100%
Commit successful!
Job ID: 12346
```

#### Synchronous Commit

```bash
$ scm commit \
    --folder Texas \
    --description "Deploy changes" \
    --sync
---> 100%
Commit successful!
Job ID: 12347
Status: FIN
```

#### Synchronous Commit with Custom Timeout

```bash
$ scm commit \
    --folder Texas \
    --description "Deploy changes" \
    --sync \
    --timeout 600
---> 100%
Commit successful!
Job ID: 12348
Status: FIN
```

#### Commit with Bearer Token Auth

```bash
$ scm commit \
    --folder Texas \
    --description "Deploy changes" \
    --admin user@domain.com
---> 100%
Commit successful!
Job ID: 12349
```

!!! tip
    After an async commit, use `scm jobs status --id <JOB_ID>` to check progress
    or `scm jobs wait --id <JOB_ID>` to wait for completion.
