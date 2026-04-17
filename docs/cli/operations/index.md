# Device Operations

Dispatch and monitor asynchronous device jobs for network diagnostics and status checks.

## Commands

All operation commands support:

| Option | Default | Description |
|--------|---------|-------------|
| `--device`, `-d` | Required | Device name |
| `--async` | `False` | Return job ID without waiting |
| `--timeout`, `-t` | `300` | Sync polling timeout in seconds |

### Route Table

```bash
scm operations route-table --device fw-01
scm operations route-table --device fw-01 --async
```

### FIB Table

```bash
scm operations fib-table --device fw-01
```

### DNS Proxy

```bash
scm operations dns-proxy --device fw-01
```

### Network Interfaces

```bash
scm operations interfaces --device fw-01
```

### Device Rules

```bash
scm operations device-rules --device fw-01
```

### BGP Export

```bash
scm operations bgp-export --device fw-01
```

### Logging Status

```bash
scm operations logging-status --device fw-01
```

### Job Status

Check on an async job:

```bash
scm operations status --job-id abc-123
```

## Sync vs Async

By default, commands block and poll until the operation completes, then display results as a table. Use `--async` to get the job ID immediately and check later with `scm operations status`.

If sync polling exceeds `--timeout`, the CLI reports the job ID and last known state for manual follow-up.
