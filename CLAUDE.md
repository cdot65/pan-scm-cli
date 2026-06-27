# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CLI tool for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations. It provides commands to manage addresses, address groups, security zones, security rules, and bandwidth allocations through a consistent interface.

## Development Commands

### Setup and Build

```bash
make setup              # Install dependencies and pre-commit hooks
make reinstall          # Rebuild and reinstall the package locally
```

### Code Quality

```bash
make lint               # Run flake8 and yamllint
make format             # Format code with ruff
make fix                # Auto-fix linting issues with ruff
make quality            # Run all quality checks (lint, format, mypy, tests)
```

### Testing

```bash
make tests              # Run pytest suite
pytest tests/test_specific.py::test_name  # Run a single test
pytest -v               # Run with verbose output
```

### Documentation

```bash
make docs-serve         # Serve docs locally on port 8000
make docs-build         # Build docs with strict checks
```

## Architecture

### Command Structure

The CLI follows a consistent pattern: `scm <action> <object-type> <object> [options]`

Commands are organized by resource type:

- `commands/objects.py`: Address, address group, application, application group, application filter, dynamic user group, external dynamic list, HIP object, HIP profile, HTTP server profile, log forwarding profile, service, service group, syslog server profile, and tag management
- `commands/network.py`: Security zone management
- `commands/security.py`: Security rule management
- `commands/deployment.py`: Bandwidth allocation management
- `commands/local.py`: Device configuration version listing and XML download
- `commands/operations.py`: Device operations (route-table, fib-table, dns-proxy, interfaces, device-rules, bgp-export, logging-status) with sync/async job support
- `commands/incidents.py`: Security incident search and detail with filtering and JSON output

### Key Components

- `client.py`: Initializes SCM client (real or mock mode)
- `utils/sdk_client.py`: Wrapper around pan-scm-sdk with error handling
- `utils/validators.py`: Pydantic models for input validation
- `utils/config.py`: Dynaconf-based configuration management

### Authentication Flow

The CLI uses a context-based authentication system that supports multiple SCM tenants:

1. **Primary**: Active context (set via `scm context use <name>`)
2. **Override**: Environment variables (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`) for CI/CD
3. **Fallback**: Mock mode if no credentials found

#### Context Management Commands

```bash
# Create a context
scm context create production --client-id <id> --client-secret <secret> --tsg-id <tsg>

# Switch contexts
scm context use production

# Test authentication
scm context test

# List all contexts
scm context list
```

**Note**: Legacy config files (`~/.scm-cli/config.yaml` and `.secrets.yaml`) are no longer supported. Use contexts instead.

### Adding New Commands

1. Create/update the appropriate command module in `src/scm_cli/commands/`
2. Add Pydantic validator models in `utils/validators.py` if needed
3. Register the command in `main.py`
4. Add corresponding tests in `tests/`
5. Update documentation in `docs/cli/`

### Testing Patterns

- Tests automatically use mock credentials via `mock_dynaconf_settings` fixture
- Use `mock_scm_client` fixture for API testing without real calls
- Test data fixtures are in `tests/data/`
- Environment-specific tests check auth/config behavior

### Docker Support

The project includes a Docker build script that supports multi-platform builds:

```bash
# Build locally for Apple Silicon
docker/docker-build.sh --local

# Build AMD64 for testing
docker/docker-build.sh --amd64

# Build both platforms (requires push to registry)
docker/docker-build.sh
```

#### Docker Context Integration

When running in Docker containers, contexts are preserved through volume mounting:

```bash
# Run with context support
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  ghcr.io/cdot65/pan-scm-cli:latest

# Use contexts in container
docker exec pan-scm scm context list
docker exec pan-scm scm context use production
```

The Docker image is available at `ghcr.io/cdot65/pan-scm-cli:latest` (AMD64) and `ghcr.io/cdot65/pan-scm-cli:apple` (ARM64).

## Code Style and Standards

**IMPORTANT**: All code in this project must follow the comprehensive style guides located in the `.claude/` directory:

### General Style Guide (`.claude/STYLE_GUIDE.md`)

Covers patterns for command modules and general project standards:

- Module structure and section organization with 191-character separators
- Command architecture patterns for Typer apps
- Documentation standards (Google format docstrings)
- Error handling patterns
- Type annotation conventions (Python 3.10+ syntax)
- Naming conventions for commands, functions, and variables
- Output formatting standards
- Alphabetical ordering requirements in main.py
- Backup command patterns and implementation

### SDK Client Style Guide (`.claude/SDK_CLIENT_STYLE_GUIDE.md`)

Specific patterns for `src/scm_cli/utils/sdk_client.py`:

- SDK client class design and initialization
- Method organization by configuration type
- CRUD method patterns (create, get, list, delete)
- Mock mode support with realistic data
- Error handling with `_handle_api_exception`
- Logging standards and levels
- SDK field mapping and data transformation
- List methods with `exact_match` parameter support

### Validators Style Guide (`.claude/VALIDATORS_STYLE_GUIDE.md`)

Specific patterns for `src/scm_cli/utils/validators.py`:

- Pydantic model design patterns
- Field definitions with proper constraints
- Model validation patterns
- SDK model conversion with `to_sdk_model()`
- Utility functions for YAML validation
- Type definitions and generic types

Always refer to the appropriate style guide when writing or modifying code to ensure consistency across the codebase.

## Important Notes

- The SDK version requires `pan-scm-sdk>=0.13.0` - verify compatibility when updating
- Mock mode allows full testing without API credentials
- Bulk operations use YAML files - see `examples/` for formats
- All commands support `--mock` flag for testing
- Documentation is a Docusaurus site in `docs-site/` (authored MDX/Markdown under `docs-site/docs/`, sidebar in `docs-site/sidebars.ts`); it builds and deploys to GitHub Pages via `.github/workflows/deploy-docs.yml`. Run locally with `make docs-serve`; build with `make docs-build`.
- SDK service names use singular form (e.g., `application_filter` not `application_filters`, `external_dynamic_list` not `external_dynamic_lists`, `hip_object` not `hip_objects`, `hip_profile` not `hip_profiles`, `http_server_profile` not `http_server_profiles`, `log_forwarding_profile` not `log_forwarding_profiles`, `service` not `services`, `service_group` not `service_groups`, `syslog_server_profile` not `syslog_server_profiles`, `tag` not `tags`)
- Boolean fields in API requests should be omitted when false to avoid validation errors
- Dynamic user group filters use tag-based expressions with specific syntax requirements
- External dynamic lists support various types (predefined_ip, predefined_url, ip, domain, url, imsi, imei) with different configuration requirements
- Predefined EDLs use short names (e.g., "panw-bulletproof-ip-list") not full URLs for the url field
- HIP objects use a flattened field structure in validators for easier CLI usage, which is then converted to nested SDK format
- HIP object criteria types include host info, network info, patch management, disk encryption, mobile device, and certificate validation
- HIP profiles reference HIP objects through match criteria with boolean operators (is/is-not)
- HTTP server profiles require the `http_method` field for all server configurations (discovered through API testing)
- HTTP server profile `server` field is returned as singular from API but we use plural `servers` in YAML for consistency
- Log forwarding profiles require the 'filter' field in match list entries despite SDK documentation showing it as optional
- Log forwarding profile match lists support various log types (traffic, threat, wildfire, url, data, tunnel, auth, decryption, dns-security)
- Services define network protocols (TCP/UDP) with port configurations and optional timeout overrides
- Service tags must reference existing tag objects in SCM (validation error occurs if tag doesn't exist)
- Service port configurations support single ports, port ranges (e.g., 80-443), and comma-separated lists (e.g., 80,443,8080)
- Service groups organize services and other service groups for policy management
- Service group members must be unique and reference existing service or service group objects
- Service groups support nested references (a service group can contain other service groups)
- Syslog server profiles use fetch() method instead of get() in SDK client for retrieval
- Syslog server profiles support UDP and TCP transport (SSL not supported by SDK)
- Syslog server format options include BSD and IETF
- Syslog facilities range from LOG_USER to LOG_LOCAL7
- Tags support 42 predefined colors (Red, Green, Blue, Yellow, Copper, Orange, Purple, Gray, Light Green, Cyan, Light Gray, Blue Gray, Lime, Black, Gold, Brown, Olive, Maroon, Red-Orange, Yellow-Orange, Forest Green, Turquoise Blue, Azure Blue, Cerulean Blue, Midnight Blue, Medium Blue, Cobalt Blue, Violet Blue, Blue Violet, Medium Violet, Medium Rose, Lavender, Orchid, Thistle, Peach, Salmon, Magenta, Red Violet, Mahogany, Burnt Sienna, Chestnut)
- Tag color validation is case-insensitive in validator but API requires exact case
- Tags can have comments for additional metadata
- Decryption profiles support SSL/TLS inspection configurations with three proxy types: SSL Forward Proxy (outbound), SSL Inbound Proxy (inbound), and SSL No Proxy (bypass)
- Decryption profile SSL protocol settings control minimum/maximum TLS versions and allowed cipher suites
- Decryption profiles use JSON input for complex settings in the set command due to nested configuration requirements
- Anti-spyware profiles require at least one rule to be defined (SDK validation requirement)
- Security commands are organized in security.py following the same patterns as object commands
