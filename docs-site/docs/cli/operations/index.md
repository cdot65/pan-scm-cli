# Device Operations

Dispatch and monitor asynchronous device jobs for network diagnostics and status checks.

## Commands

All operation commands support:

| Option | Default | Description |
|--------|---------|-------------|
| `--device`, `-d` | Required | Device serial number (14-15 digits) |
| `--async` | `False` | Return job ID without waiting |
| `--timeout`, `-t` | `300` | Sync polling timeout in seconds |

### Route Table

```bash
scm operations route-table --device 007951000123456
scm operations route-table --device 007951000123456 --async
```

### FIB Table

```bash
scm operations fib-table --device 007951000123456
```

### DNS Proxy

```bash
scm operations dns-proxy --device 007951000123456
```

### Network Interfaces

```bash
scm operations interfaces --device 007951000123456
```

### Device Rules

```bash
scm operations device-rules --device 007951000123456
```

### BGP Export

```bash
scm operations bgp-export --device 007951000123456
```

### Logging Status

```bash
scm operations logging-status --device 007951000123456
```

### Job Status

Check on an async job:

```bash
scm operations status --job-id abc-123
```

## Sync vs Async

By default, commands block and poll until the operation completes, then display results as a table. Use `--async` to get the job ID immediately and check later with `scm operations status`.

If sync polling exceeds `--timeout`, the CLI reports the job ID and last known state for manual follow-up.
