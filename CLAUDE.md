# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. The body below mirrors `AGENTS.md`.

<!-- SYNC: The body below (from "## Project Overview" onward) is kept identical between AGENTS.md and CLAUDE.md. Only the header above differs per file. -->

## Project Overview

`pan-scm-cli` is a CLI tool for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations. It manages objects, network configs, security policy, identity profiles, mobile agent settings, setup containers, and SASE/deployment resources through a consistent verb-based interface, plus monitoring (insights, incidents), device operations, local config retrieval, jobs, and firewall posture (BPA) assessment.

- **Package:** `pan-scm-cli` (version `2.0.0`), console script `scm`.
- **Runtime:** Python `>=3.10,<3.14`, built with Typer + Click, validated with Pydantic v2.
- **SDK dependency:** `pan-scm-sdk ^0.15.0` (i.e. `>=0.15.0,<0.16.0`) — verify compatibility when bumping.
- **Packaging/build:** Poetry (`pyproject.toml`).

---

## Development

### Setup and Build

```bash
make setup              # Install dependencies via poetry
make reinstall          # Rebuild and reinstall the package locally (poetry build)
```

### Code Quality

```bash
make lint               # Run flake8
make format             # Format code with ruff (ruff format)
make ruff               # Run ruff formatting + lint with fixes
make mypy               # Type-check with mypy
make quality            # Run all quality checks (lint, format, mypy, tests)
```

> Note: there is no `make fix` target. Use `make ruff` for autofix.

### Testing

```bash
make tests              # Run pytest suite
pytest tests/test_specific.py::test_name  # Run a single test
pytest -v               # Run with verbose output
```

### Documentation (Docusaurus)

Documentation is a Docusaurus site in `docs-site/` (authored Markdown/MDX under `docs-site/docs/`, sidebar in `docs-site/sidebars.ts`). It builds and deploys to GitHub Pages via `.github/workflows/deploy-docs.yml`.

```bash
make docs-install       # Install the docs-site toolchain
make docs-serve         # Serve docs locally
make docs-build         # Build docs with strict checks
```

The command reference under `docs-site/docs/cli/` is the source of truth for the documented CLI surface; the live `scm --help` output is the source of truth for actual behavior. Keep both in sync with the code.

---

## Architecture

### Command Structure

For configuration verbs the CLI follows:

```
scm <action> <category> <object-type> [NAME] [options]
```

**Actions:** `set`, `delete`, `show`, `load`, `backup`, `move`
**Categories:** `object`, `network`, `security`, `identity`, `mobile-agent`, `setup`, `sase`
**Standalone top-level commands:** `commit`, `context`, `jobs`, `insights`, `incidents`, `local`, `operations`, `posture`

The object name is a positional `NAME` argument (required for `set`/`delete`/`move`, optional for `show` — omit it to list all). Exceptions: quarantined-device uses `--host-id`, network-location uses `--value`, and singletons (sase bgp-routing, mobile-agent global-setting) take no name.

### Command Modules (`src/scm_cli/commands/`)

- `objects.py` — object category: address, address group, application, application group, application filter, auto-tag-action, dynamic user group, external dynamic list, HIP object, HIP profile, HTTP server profile, log forwarding profile, quarantined-device, region, schedule, service, service group, syslog server profile, tag
- `network.py` — network category: security zones, interfaces (aggregate/ethernet/loopback/tunnel/vlan/layer2-sub/layer3-sub), BGP profiles & route maps, DHCP/DNS-proxy, IKE/IPSec crypto, IKE gateway, NAT/PBF/QoS rules, route access/prefix lists, OSPF auth
- `security.py` — security category: security rules + profiles (anti-spyware, app-override, authentication, decryption profile/rule, dns-security, url-access, url-category, vulnerability-protection, wildfire-antivirus)
- `identity.py` — identity category: authentication/kerberos/ldap/radius/saml/tacacs server profiles
- `mobile_agent.py` — mobile-agent category: agent-version (read-only), auth-setting, profiles
- `setup.py` — setup category: folder, label, snippet, variable, device
- `deployment.py` — sase category: bandwidth-allocation, bgp-routing, internal-dns-server, remote-network, service-connection
- `commit.py` — commit staged changes
- `context.py` — authentication context management
- `jobs.py` — SCM job management
- `insights.py` — monitoring insights
- `incidents.py` — security incident search/detail
- `local.py` — local device config version listing & XML download
- `operations.py` — device operations with sync/async job support
- `posture.py` — firewall posture / BPA scoring

### Key Components

- `client.py` — initializes SCM client (real or mock mode)
- `utils/sdk_client.py` — wrapper around `pan-scm-sdk` with error handling
- `utils/validators.py` — Pydantic models for input validation
- `utils/config.py` — Dynaconf-based configuration management
- `utils/context.py` — authentication context storage/resolution
- `utils/decorators.py` — shared command decorators

### Adding New Commands

1. Create/update the appropriate command module in `src/scm_cli/commands/`
2. Add Pydantic validator models in `utils/validators.py` if needed
3. Register the command in `main.py` (alphabetical ordering)
4. Add corresponding tests in `tests/`
5. Update documentation under `docs-site/docs/cli/`

### Testing Patterns

- Tests automatically use mock credentials via the `mock_dynaconf_settings` fixture
- Use the `mock_scm_client` fixture for API testing without real calls
- Test data fixtures live in `tests/data/`
- Environment-specific tests check auth/config behavior

### Docker Support

The image is built from local source (multi-stage, `python:3.12-alpine`, non-root `scmuser`). Run the helper script from the repo root:

```bash
./docker/docker-build.sh --local-only   # ARM64 image for local use (tags :local, :apple)
./docker/docker-build.sh                 # Build ARM64 (local) + AMD64 (:latest), no push
./docker/docker-build.sh --push          # Build and push :latest + :apple to GHCR
# --no-cache forces a clean rebuild
```

Pushing requires `docker login ghcr.io -u <user>`. See `docker/README.md` for full details.

Contexts persist in containers via volume mounting:

```bash
docker run -d --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  ghcr.io/cdot65/pan-scm-cli:latest

docker exec pan-scm scm context list
docker exec pan-scm scm context use production
```

Images: `ghcr.io/cdot65/pan-scm-cli:latest` (AMD64), `ghcr.io/cdot65/pan-scm-cli:apple` (ARM64).

---

## Code Style and Standards

All code must follow the style guides in the `.claude/` directory:

- **`.claude/STYLE_GUIDE.md`** — command module patterns: section organization with 192-char separators, Typer app architecture, Google-format docstrings, error handling, Python 3.10+ type annotations, naming conventions, output formatting, alphabetical ordering in `main.py`, backup command patterns.
- **`.claude/SDK_CLIENT_STYLE_GUIDE.md`** — patterns for `utils/sdk_client.py`: client class design/init, method organization by config type, CRUD patterns, mock-mode data, `_handle_api_exception`, logging, SDK field mapping, `exact_match` on list methods.
- **`.claude/VALIDATORS_STYLE_GUIDE.md`** — patterns for `utils/validators.py`: Pydantic model design, field constraints, validation, `to_sdk_model()` conversion, YAML validation utilities, type definitions.

Lint config: ruff `line-length = 192`, `target-version = py310`, rules `E,F,I,B,C4,SIM,UP,W,N,D`.

---

# Operating the CLI

## Quick Reference

```
scm <action> <category> <object-type> [NAME] [options]
```

**Actions:** `set`, `delete`, `show`, `load`, `backup`, `move`
**Categories:** `object`, `network`, `security`, `identity`, `mobile-agent`, `setup`, `sase`
**Standalone:** `scm commit`, `scm context`, `scm jobs`, `scm insights`, `scm incidents`, `scm local`, `scm operations`, `scm posture`

The object name is a positional `NAME` argument: required for `set`/`delete`/`move`, optional for `show` (omit it to list all — there is no `--list` flag). Every `show` supports `--output table|json|yaml` and `--max-results N`; every `load` supports `--dry-run`; every `backup` supports `--file`. Multi-value flags are repeatable (e.g. `--tags a --tags b`, `--members m1 --members m2`), not comma-separated.

Global options: `--version`/`-V`, `--region <region>` (override SCM API region for the invocation), `--debug`.

---

## Authentication

### Context Setup (required before any API calls)

```bash
# Create a context with OAuth2 credentials
scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>

# Create a context with bearer token
scm context create <name> --access-token <token>

# Switch active context
scm context use <name>

# Verify auth works
scm context test

# List / show / delete / current contexts
scm context list
scm context show [name]
scm context delete <name> [--force]
scm context current
```

**Environment variable overrides:** `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID` (useful for CI/CD).

**Mock mode:** Set `SCM_MOCK=1` to test without API credentials (`scm context test` also accepts `--mock`; other commands have no `--mock` flag). Missing credentials without explicit mock mode fail with exit code 1 — there is no silent fallback.

**Note:** Legacy config files (`~/.scm-cli/config.yaml`, `.secrets.yaml`) are no longer supported — use contexts.

---

## Container Locations

`set`/`delete`/`show` for object, network, security, and identity types require exactly ONE container location:

| Flag | Description |
|------|-------------|
| `--folder <name>` | Folder in the hierarchy (most common) |
| `--snippet <name>` | Shared configuration snippet |
| `--device <name>` | Device-level configuration |

Exceptions: `sase` types, `setup` folder/label/snippet/device, and quarantined-device take no container; `mobile-agent` is folder-only (SDK limitation).

---

## Object Management (`scm ... object ...`)

### Addresses

```bash
# IP netmask
scm set object address webserver --folder Texas --ip-netmask 10.1.1.10/32 --description "Web server" --tags web --tags prod
# IP range
scm set object address dhcp-pool --folder Texas --ip-range 10.1.3.1-10.1.3.10
# FQDN
scm set object address google-dns --folder Texas --fqdn dns.google.com
# IP wildcard
scm set object address wildcard --folder Texas --ip-wildcard 10.20.0.0/0.0.255.255
```

```bash
scm show object address --folder Texas             # list all
scm show object address webserver --folder Texas   # show one
scm delete object address webserver --folder Texas [--force]
```

**Constraints:** Name 1-63 chars. Exactly ONE address type required.

### Address Groups

```bash
scm set object address-group web-servers --folder Texas --type static --members webserver1 --members webserver2
scm set object address-group tagged-web --folder Texas --type dynamic --filter "'web' and 'prod'"
```

**Constraints:** Static requires `--members` (min 1). Dynamic uses tag-based filter expressions.

### Applications

```bash
scm set object application custom-app --folder Texas \
  --category business-systems --subcategory erp --technology client-server --risk 3 \
  --ports tcp/8080 --ports tcp/8443 --transfers-files --has-known-vulnerabilities
```

**Risk levels:** 1-5. Boolean flags: `--evasive`, `--pervasive`, `--excessive-bandwidth-use`, `--used-by-malware`, `--transfers-files`, `--has-known-vulnerabilities`, `--tunnels-other-apps`, `--prone-to-misuse`, `--no-certifications`.

### Application Groups

```bash
scm set object application-group web-apps --folder Texas --members web-browsing --members ssl --members http
```

### Application Filters

```bash
scm set object application-filter high-risk --folder Texas \
  --category business-systems --subcategory erp --technology client-server --risk 4 --risk 5
```

### Tags

```bash
scm set object tag production --folder Texas --color Red --comments "Production environment"
```

**42 valid colors:** Red, Green, Blue, Yellow, Copper, Orange, Purple, Gray, Light Green, Cyan, Light Gray, Blue Gray, Lime, Black, Gold, Brown, Olive, Maroon, Red-Orange, Yellow-Orange, Forest Green, Turquoise Blue, Azure Blue, Cerulean Blue, Midnight Blue, Medium Blue, Cobalt Blue, Violet Blue, Blue Violet, Medium Violet, Medium Rose, Lavender, Orchid, Thistle, Peach, Salmon, Magenta, Red Violet, Mahogany, Burnt Sienna, Chestnut. Color names are case-insensitive in the CLI validator but case-sensitive in the API.

### Services

```bash
scm set object service web-http --folder Texas --protocol tcp --port 80
scm set object service web-https --folder Texas --protocol tcp --port 443 --timeout 3600
scm set object service multi-port --folder Texas --protocol tcp --port 80,443,8080
scm set object service port-range --folder Texas --protocol tcp --port 8000-8999
```

**Constraints:** Protocol `tcp` or `udp`. Port: single, range (80-443), or comma-separated (80,443,8080). Service tags must reference existing tag objects.

### Service Groups

```bash
scm set object service-group web-services --folder Texas --members web-http --members web-https
```

**Constraints:** Members must be unique; can reference services or other service groups (nested allowed).

### Dynamic User Groups

```bash
scm set object dynamic-user-group risky-users --folder Texas \
  --filter "'high-risk' and 'external'" --description "High risk external users"
```

**Constraints:** Filter max 2047 chars. Tag-based expressions with single quotes.

### External Dynamic Lists

```bash
scm set object external-dynamic-list bulletproof-ips --folder Texas \
  --type predefined_ip --url panw-bulletproof-ip-list
scm set object external-dynamic-list threat-ips --folder Texas \
  --type ip --url https://example.com/threats.txt --recurring daily --hour 03
scm set object external-dynamic-list blocked-domains --folder Texas \
  --type domain --url https://example.com/domains.txt --recurring hourly \
  --username api_user --password secret --expand-domain
```

**Types:** `predefined_ip`, `predefined_url`, `ip`, `domain`, `url`, `imsi`, `imei`.
**Recurring:** `five_minute`, `hourly`, `daily`, `weekly`, `monthly`.
Predefined EDLs use short names (e.g. `panw-bulletproof-ip-list`) not full URLs.

### HIP Objects

```bash
scm set object hip-object corporate-host --folder Texas \
  --host-info-os Microsoft --host-info-os-value All --host-info-managed \
  --disk-encryption-enabled
```

Criteria types: host info, network info, patch management, disk encryption, mobile device, certificate. HIP objects use a flattened field structure in validators (converted to nested SDK format). See `examples/hip-objects.yml`.

### HIP Profiles

```bash
scm set object hip-profile corp-compliance --folder Texas --match "corporate-host is"
```

Reference HIP objects through match criteria with boolean operators (is/is-not).

### HTTP Server Profiles

```bash
scm set object http-server-profile webhook-profile --folder Texas \
  --servers '[{"name": "srv1", "address": "192.168.1.1", "protocol": "HTTP", "port": 8080, "http_method": "POST"}]'
```

**Important:** `http_method` is required for all server configs. The `server` field is singular from the API but YAML uses plural `servers` for consistency.

### Log Forwarding Profiles

```bash
scm set object log-forwarding-profile forward-all --folder Texas --enhanced-application-logging
```

**Important:** the `filter` field is required in match list entries despite SDK docs showing it optional. Match lists support traffic, threat, wildfire, url, data, tunnel, auth, decryption, dns-security log types.

### Syslog Server Profiles

```bash
scm set object syslog-server-profile syslog-central --folder Texas \
  --server-name syslog1 --server-address 192.168.1.100 \
  --transport UDP --port 514 --format BSD --facility LOG_USER
```

**Transport:** UDP, TCP (SSL not supported by SDK). **Format:** BSD, IETF. **Facilities:** LOG_USER, LOG_LOCAL0–LOG_LOCAL7. Uses `fetch()` (not `get()`) in the SDK client for retrieval.

### Schedules

```bash
scm set object schedule maintenance-window --folder Texas \
  --schedule-type recurring-weekly --saturday 02:00-06:00 --sunday 02:00-06:00
```

### Regions

```bash
scm set object region us-east --folder Texas --address 10.0.0.0/8 --address 172.16.0.0/12
```

### Auto Tag Actions

```bash
scm set object auto-tag-action auto-tag-threats --folder Texas
```

### Quarantined Devices

```bash
scm show object quarantined-device [--host-id <id>] [--serial-number <sn>]
```

Manage quarantined devices (list/set/delete) — identified by `--host-id`, no positional name and no container flags. See `docs-site/docs/cli/objects/quarantined-device.md`.

---

## Network Management (`scm ... network ...`)

### Security Zones

```bash
scm set network zone trust --folder Texas --mode layer3 --interfaces ethernet1/1 --interfaces ethernet1/2
scm show network zone --folder Texas
scm delete network zone trust --folder Texas [--force]
```

### Other Network Objects

All follow `scm <action> network <type>`:

| Object Type | Description |
|-------------|-------------|
| `aggregate-interface` | Aggregate (LAG) interfaces |
| `bgp-address-family-profile` | BGP address family profiles |
| `bgp-auth-profile` | BGP authentication profiles |
| `bgp-filtering-profile` | BGP filtering profiles |
| `bgp-redistribution-profile` | BGP redistribution profiles |
| `bgp-route-map` | BGP route maps |
| `bgp-route-map-redistribution` | BGP route map redistribution |
| `dhcp-interface` | DHCP interface configs |
| `dns-proxy` | DNS proxy configs |
| `ethernet-interface` | Ethernet interfaces |
| `ike-crypto-profile` | IKE crypto profiles |
| `ike-gateway` | IKE gateways |
| `ipsec-crypto-profile` | IPSec crypto profiles |
| `layer2-subinterface` | Layer 2 subinterfaces |
| `layer3-subinterface` | Layer 3 subinterfaces |
| `loopback-interface` | Loopback interfaces |
| `nat-rule` | NAT rules |
| `ospf-auth-profile` | OSPF auth profiles |
| `pbf-rule` | Policy-based forwarding rules |
| `qos-profile` | QoS profiles |
| `qos-rule` | QoS rules |
| `route-access-list` | Route access lists |
| `route-prefix-list` | Route prefix lists |
| `tunnel-interface` | Tunnel interfaces |
| `vlan-interface` | VLAN interfaces |
| `zone` | Security zones |

---

## Security Management (`scm ... security ...`)

### Security Rules

```bash
scm set security rule allow-web --folder Texas \
  --source-zones trust --destination-zones untrust \
  --source-addresses any --destination-addresses web-servers \
  --applications web-browsing --applications ssl --services application-default \
  --action allow --log-end --description "Allow web traffic" --rulebase pre

scm show security rule --folder Texas
scm show security rule allow-web --folder Texas
scm delete security rule allow-web --folder Texas [--force]

# Move (reorder)
scm move security rule allow-web --folder Texas --destination top --rulebase pre
scm move security rule allow-web --folder Texas --destination before --destination-rule <rule-uuid> --rulebase pre
scm move security rule allow-web --folder Texas --destination after --destination-rule <rule-uuid> --rulebase pre
```

**Options:** `--source-zones`/`--destination-zones` (names or `any`); `--source-addresses`/`--destination-addresses`; `--applications`; `--services` (names, `application-default`, or `any`); `--action` (`allow`/`deny`/`drop`); `--enabled`/`--disabled`; `--log-start`/`--log-end`; `--log-setting`; `--rulebase` (`pre` default, `post`, `default`); `--tags`.

### Security Profiles

| Object Type | Description |
|-------------|-------------|
| `anti-spyware-profile` | Anti-spyware profiles (min 1 rule required) |
| `app-override-rule` | Application override rules |
| `authentication-rule` | Authentication rules |
| `decryption-profile` | SSL/TLS decryption profiles (SSL Forward Proxy, SSL Inbound Proxy, SSL No Proxy; uses JSON input for nested settings in `set`) |
| `decryption-rule` | Decryption rules |
| `dns-security-profile` | DNS security profiles |
| `url-access-profile` | URL filtering profiles |
| `url-category` | Custom URL categories |
| `vulnerability-protection-profile` | Vulnerability protection profiles |
| `wildfire-antivirus-profile` | WildFire antivirus profiles |

---

## Identity Management (`scm ... identity ...`)

| Object Type | Description |
|-------------|-------------|
| `authentication-profile` | Authentication profiles |
| `kerberos-server-profile` | Kerberos server profiles |
| `ldap-server-profile` | LDAP server profiles |
| `radius-server-profile` | RADIUS server profiles |
| `saml-server-profile` | SAML server profiles |
| `tacacs-server-profile` | TACACS+ server profiles |

---

## Mobile Agent (`scm ... mobile-agent ...`)

| Object Type | Description |
|-------------|-------------|
| `agent-version` | Agent versions (show only, read-only) |
| `auth-setting` | GlobalProtect auth settings |

Also includes agent/forwarding/tunnel profiles and global/infrastructure settings — see `docs-site/docs/cli/mobile-agent/`. Mobile-agent commands are folder-only (no `--snippet`/`--device`, SDK limitation); global-setting is a singleton and takes no name.

```bash
scm set mobile-agent auth-setting gp-auth --folder "Mobile Users" \
  --authentication-profile corp-auth --os Any
```

---

## Setup (`scm ... setup ...`)

### Folders

```bash
scm set setup folder "Branch Office" --parent "All Firewalls" --description "Branch config"
scm show setup folder
scm delete setup folder "Branch Office" [--force]
```

### Labels

```bash
scm set setup label production --description "Production environment"
```

### Snippets

```bash
scm set setup snippet shared-config --description "Shared configuration"
```

### Variables

```bash
scm set setup variable '$dns-server' --folder Texas --type ip-netmask --value 8.8.8.8/32
```

**Variable types:** `percent`, `count`, `ip-netmask`, `zone`, `ip-range`, `ip-wildcard`, `fqdn`, `port`, `egress-max`, and more.

### Devices

```bash
scm show setup device
```

Manage device records — see `docs-site/docs/cli/setup/device.md`.

---

## SASE / Deployment (`scm ... sase ...`)

| Object Type | Description |
|-------------|-------------|
| `bandwidth-allocation` | Bandwidth allocations |
| `bgp-routing` | BGP routing configs |
| `internal-dns-server` | Internal DNS servers |
| `remote-network` | Remote network configs |
| `service-connection` | Service connections |

```bash
scm set sase bandwidth-allocation site-bw --bandwidth 1000 --spn-name-list spn1,spn2
scm show sase bandwidth-allocation
```

SASE resources are global — no `--folder`/`--snippet`/`--device` flags. `bgp-routing` is a singleton and takes no name.

---

## Bulk Operations via YAML (`load` / `backup`)

### Loading from YAML

```bash
scm load object address --file addresses.yml [--dry-run]
scm load object address --file addresses.yml --folder Override-Folder
scm load security rule --file rules.yml [--dry-run]
```

- `--file` (required): path to YAML file
- `--dry-run`: preview changes without applying
- `--folder` / `--snippet` / `--device`: override container location in the YAML

### Backing Up to YAML

```bash
scm backup object address --folder Texas [--file custom-output.yaml]
scm backup security rule --folder Texas --file rules-backup.yaml
```

Defaults output file to `{object-type}-{location}.yaml`.

### YAML File Formats

**Addresses:**
```yaml
addresses:
  - name: webserver
    folder: Texas
    ip_netmask: 10.1.1.10/32
    description: Web server
    tags: [web, prod]
  - name: dns-server
    folder: Texas
    fqdn: dns.google.com
```

**Address Groups:**
```yaml
address_groups:
  - name: web-servers
    folder: Texas
    type: static
    members: [webserver1, webserver2]
    tags: [web]
  - name: tagged-servers
    folder: Texas
    type: dynamic
    filter: "'web' and 'prod'"
```

**Services:**
```yaml
services:
  - name: web-http
    folder: Texas
    protocol:
      tcp:
        port: "80"
    tag: [web]
```

**Security Rules:**
```yaml
security_rules:
  - name: allow-web
    folder: Texas
    rulebase: pre
    source_zones: [trust]
    destination_zones: [untrust]
    source_addresses: [any]
    destination_addresses: [web-servers]
    applications: [web-browsing, ssl]
    service: [application-default]
    action: allow
    enabled: true
    log_end: true
```

**Tags:**
```yaml
tags:
  - name: production
    folder: Texas
    color: Red
    comments: Production environment
```

**Security Zones:**
```yaml
security_zones:
  - name: trust
    folder: Texas
    network:
      layer3: [ethernet1/1, ethernet1/2]
```

**External Dynamic Lists:**
```yaml
external_dynamic_lists:
  - name: threat-ips
    folder: Texas
    type: ip
    url: https://example.com/threats.txt
    recurring: daily
    hour: "03"
```

**Syslog Server Profiles:**
```yaml
syslog_server_profiles:
  - name: central-syslog
    folder: Texas
    server:
      - name: syslog1
        server: 192.168.1.100
        transport: UDP
        port: 514
        format: BSD
        facility: LOG_USER
```

See `examples/` for complete YAML templates for all object types.

---

## Committing Changes

Changes from `set`, `delete`, or `load` are staged and must be committed:

```bash
scm commit --folder Texas --description "Updated address objects"
scm commit --folder Texas --folder California --description "Multi-site update"
scm commit --folder Texas --description "Update" --sync --timeout 600
```

---

## Job Management

```bash
scm jobs list [--max-results 50]
scm jobs status --id 12345
scm jobs wait --id 12345 [--timeout 600]
```

---

## Insights (Monitoring)

```bash
scm insights alerts --list [--severity Critical] [--max-results 20]
scm insights alerts --id <alert-id>
scm insights alerts --list --export json --output alerts.json

scm insights mobile-users --list [--status connected] [--location "US West"]
scm insights locations --list [--region "Americas"]
scm insights remote-networks --list [--connectivity connected] [--metrics]
scm insights service-connections --list [--health healthy] [--metrics]
scm insights tunnels --list [--status up] [--stats]
```

All insights commands support: `--export json|csv`, `--output <file>`, `--max-results <n>`, `--folder <name>`. There is no `--mock` flag on insights commands — set `SCM_MOCK=1` to test without credentials.

---

## Incidents (`scm incidents ...`)

Search and view security incidents.

```bash
scm incidents list                                   # list all
scm incidents list --status open --severity high     # filter
scm incidents list --product "Prisma Access"
scm incidents list --json                            # JSON for automation
scm incidents show INC-2026-04-001 [--json]          # detail w/ alerts & remediation
```

---

## Local Device Config (`scm local ...`)

Retrieve on-device configuration versions.

```bash
scm local list --device 007951000123456                              # list config versions
scm local download --device 007951000123456 --version 42             # XML to stdout
scm local download --device 007951000123456 --version 42 --output config.xml
```

---

## Device Operations (`scm operations ...`)

Dispatch and monitor device operations (support sync and `--async` job dispatch).

```bash
scm operations route-table --device 007951000123456 [--async]
scm operations fib-table --device 007951000123456
scm operations dns-proxy --device 007951000123456
scm operations interfaces --device 007951000123456
scm operations device-rules --device 007951000123456
scm operations bgp-export --device 007951000123456
scm operations logging-status --device 007951000123456
scm operations status --id abc-123                   # check a dispatched async job
```

---

## Posture / BPA (`scm posture ...`)

Best Practice Assessment against PAN-OS firewall configs: export a config, upload for assessment, and score results. Progress prints to stderr so stdout can be piped cleanly to an agent.

```bash
# Export running (default) or candidate config from a firewall
scm posture export --host <fw> --password <pw> [--user automation] [--output config.xml] [--category running|candidate]

# Upload config to BPA API, poll, and output scored results
scm posture assess --config config.xml [--format json|markdown|csv] [--output report.json] [--keep|--delete-after] [--timeout 300]

# Parse an existing BPA report JSON and score it
scm posture score --report report.json [--scope all|device|service_health|network|policies|objects] [--format json|markdown|csv]

# Agent-friendly: silence progress, capture score
scm posture assess --config config.xml --format json 2>/dev/null | jq '.score'
```

Env vars: `PANOS_HOST`, `PANOS_USER`, `PANOS_PASSWORD`.

---

## Important Notes for Agents

1. **Always commit after changes.** `set`, `delete`, and `load` stage changes; nothing applies until `scm commit`.
2. **One address type per address object.** Exactly one of `--ip-netmask`, `--ip-range`, `--ip-wildcard`, `--fqdn`.
3. **One container per command.** Object, network, security, and identity commands require exactly one of `--folder`, `--snippet`, `--device`. Exceptions: sase, setup folder/label/snippet/device, and quarantined-device take no container; mobile-agent is folder-only.
4. **Boolean fields:** omit false booleans from YAML/requests to avoid API validation errors.
5. **Tag references must exist** before objects reference them.
6. **SDK service names are singular** (e.g. `application_filter`, `external_dynamic_list`, `hip_object`, `service`, `tag`).
7. **Predefined EDLs use short names** (e.g. `panw-bulletproof-ip-list`), not full URLs.
8. **HTTP server profiles require `http_method`.**
9. **Log forwarding profile match lists require `filter`** despite SDK docs.
10. **`--force` skips confirmation prompts** — use on `delete`/`commit` when non-interactive.
11. **Mock mode is explicit:** set `SCM_MOCK=1` to test without credentials (only `scm context test` still has a `--mock` flag); missing credentials otherwise exit 1.
12. **Security rule ordering matters** — use `scm move security rule` to reorder.
13. **Rulebase options:** `pre` (before default), `post` (after), `default` (the default rulebase).
14. **Color names are case-sensitive in the API** but case-insensitive in the CLI validator.
15. **YAML key names may differ from CLI flags** (e.g. YAML `tag` vs CLI `--tags`).
16. **Anti-spyware profiles require at least one rule** (SDK validation).
17. **Decryption profiles** use JSON input for nested settings in the `set` command.
