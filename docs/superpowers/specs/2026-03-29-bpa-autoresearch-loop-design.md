# BPA Autoresearch Loop — Design Spec

Autoresearch-style agentic loop for PAN-OS firewall BPA score optimization, embedded in the pan-scm-cli repo.

## Background

Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) runs an LLM agent that modifies a training script, evaluates the result, keeps improvements, discards regressions, and repeats. We adapt this pattern to iteratively harden a PAN-OS firewall configuration scored by the Best Practice Assessment (BPA) Config Upload API.

## Architecture Overview

```
program.md (human-editable instructions)
  |
  v
Agent Loop
  |
  |-- scm posture export --host $PANOS_HOST --user automation → config.xml
  |-- scm posture assess --config config.xml --delete-after → report.json
  |-- scm posture score --report report.json --scope security → baseline
  |
  |-- Loop:
  |     1. Agent reads failing checks from report.json
  |     2. Agent edits config.xml (security policy only)
  |     3. git commit -m "experiment: <description>"
  |     4. scm posture assess --config config.xml → report.json
  |     5. scm posture score --report report.json → new score
  |     6. Improved? keep + log to results.tsv : git reset + log failure
  |     7. Repeat
```

### Mapping to autoresearch

| autoresearch | PAN-OS BPA equivalent |
|---|---|
| `prepare.py` (read-only, `evaluate_bpb`) | CLI commands: `posture export`, `posture assess`, `posture score` |
| `train.py` (agent-editable) | `config.xml` (agent-editable) |
| `program.md` (human-editable) | `program.md` (human-editable) |
| `val_bpb` (lower=better) | BPA pass % (higher=better) — agent maximizes this value |
| 5-min wall-clock budget | API round-trip (~1-2 min) |
| `results.tsv` | `results.tsv` |

### Key differences from autoresearch

- Config XML instead of Python code — agent edits XML elements, not code
- Results are deterministic (same config = same score) unlike stochastic training
- Experiments are offline — the firewall never sees experimental configs
- Winning configs deployed manually after human review

## CLI `posture` Command Group

Three new subcommands added to `pan-scm-cli`.

### `scm posture export`

Exports running config from a PAN-OS firewall via XML API.

```bash
scm posture export \
  --host 10.0.0.1 \
  --user automation \
  --output config.xml \
  --category running        # running | candidate
```

- Hits PAN-OS XML API: `https://<host>/api/?type=export&category=configuration`
- Auth: password from `.env` (`PANOS_PASSWORD`) or `--password` flag
- Generates ephemeral API key from username/password via `/api/?type=keygen`
- Outputs raw XML config file

### `scm posture assess`

Uploads config to BPA API, polls for completion, returns report.

```bash
scm posture assess \
  --config config.xml \
  --delete-after \
  --output report.json \
  --timeout 300              # max poll seconds
```

3-step flow:
1. `POST /posture/checks/v1/reports/config-file-upload` — get `task_id` + `upload_url`
2. `PUT {upload_url}` — upload config bytes to presigned GCS URL
3. `GET /posture/checks/v1/reports/{task_id}/bpa-result` — poll until COMPLETED
4. Fetch report from `report_url` in response

Auth: SCM OAuth2 via existing context system. Presigned GCS upload needs no additional auth.

### `scm posture score`

Parses BPA report JSON and returns a numeric score.

```bash
scm posture score \
  --report report.json \
  --scope security           # all | security | decryption | threat
  --format plain              # plain | json
```

- `--format plain` outputs single number to stdout (e.g., `82.5`)
- `--format json` outputs `{"score": 82.5, "passed": 33, "failed": 7, "total": 40}`
- `--scope security` filters to security policy checks only

**Note:** The report JSON schema is not yet fully defined in `posture.yaml`. First manual run will capture the schema, which gets added back to the spec. The `score` command's parsing logic is built after schema discovery.

## Authentication

### `.env` file (repo root)

```bash
# SCM OAuth2 (existing CLI context system)
SCM_CLIENT_ID=your-client-id
SCM_CLIENT_SECRET=your-client-secret
SCM_TSG_ID=your-tsg-id

# PAN-OS Firewall
PANOS_HOST=10.0.0.1
PANOS_USER=automation
PANOS_PASSWORD=your-password
```

### Auth by command

| Command | Auth Source |
|---|---|
| `scm posture export` | `PANOS_*` env vars → XML API keygen |
| `scm posture assess` | SCM OAuth2 via context system |
| `scm posture score` | None (local file parsing) |

## Agent Scope and Safety

### In-scope modifications (security policy only)

- Add security profiles to rules missing them (antivirus, anti-spyware, vulnerability, URL filtering, file blocking, wildfire)
- Attach log forwarding profiles
- Convert port-based rules to app-id rules
- Add decryption profiles
- Tighten overly permissive rules (any/any to specific apps)

### Out-of-scope (never modify)

- Do not delete rules
- Do not modify source/destination zones
- Do not touch network, routing, interface, GlobalProtect, or certificate config
- Do not add new rules — only harden existing ones
- Do not modify the "automation" user account or admin access
- Do not remove existing allow rules — only add profiles/restrictions

### Deployment

The loop produces an optimized `config.xml` on a branch. To apply:
1. Human reviews the git diff
2. Human decides what to push via SCM or import via XML API
3. Deployment is intentionally NOT automated

## File Layout

### New/modified files in pan-scm-cli

```
src/scm_cli/commands/posture.py         # NEW — export, assess, score commands
src/scm_cli/utils/validators.py         # MODIFIED — add BPA Pydantic models
src/scm_cli/utils/sdk_client.py         # MODIFIED — add BPA methods (raw requests)
tests/test_posture_commands.py           # NEW — unit tests
program.md                               # NEW — agentic loop instructions
posture.yaml                             # MOVED — OpenAPI spec (source of truth)
```

### Git tracking

| File | Tracked | Reason |
|---|---|---|
| `program.md` | Yes | Versioned agentic instructions |
| `posture.yaml` | Yes | API spec, source of truth |
| `src/scm_cli/commands/posture.py` | Yes | CLI implementation |
| `config.xml` | No | Sensitive firewall config |
| `report.json` | No | Ephemeral scoring output |
| `results.tsv` | No | Experiment log, branch-local |
| `.env` | No | Credentials |

## Rate Limits and Constraints

- BPA API: max 5 concurrent jobs (spec returns 429 on exceed)
- Sequential loop = 1 active job at a time
- Timeout per assess: 300s default, kill and discard on exceed
- Always use `--delete-after` for zero persistence of config in cloud

## Conventions

### From autoresearch
- `program.md` at repo root
- `results.tsv` as TSV (not CSV)
- Branch naming: `autoresearch/<tag>`
- Single editable file, single metric, binary keep/revert

### From pan-scm-cli
- 191-char section separators
- Google-style docstrings
- `str | None` type hints (Python 3.10+)
- Pydantic v2 validators
- Typer command patterns
- Factory-boy test factories

## Open Items

- BPA report JSON schema: unknown until first manual run, then added to `posture.yaml`
- Scoring weights: equal weight per check, or category-weighted? Decide after seeing report structure
- Poll interval for assess: start with 5s, tune based on observed processing time
