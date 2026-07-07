# Command Styling

The canonical style reference for command modules is **`.claude/STYLE_GUIDE.md`**
at the repository root. This file intentionally defers to it so there is a single
source of truth; the guidance below is a summary of the output rules only.

## Output layer (summary)

All user-facing output flows through `scm_cli.utils.output`:

| Concern | API | Stream |
| --- | --- | --- |
| Tables / detail views / JSON / YAML | `emit(data, output, columns=..., title=...)` | stdout |
| Success messages | `success("Created address: web1 in folder Texas")` | stderr (✓) |
| Errors | `error("Address not found: web1")` + `raise typer.Exit(code=1)` | stderr (✗) |
| Warnings | `warning(...)` | stderr (⚠) |
| Progress / notes / tips | `info(...)` | stderr (dim) |

Rules:

- Every `show` command takes `output: OutputFormat = OUTPUT_OPTION` (`--output/-o table|json|yaml`).
- Never hand-roll display code: no `typer.echo` field dumps, no `"-" * N` /
  `"=" * N` separators, no ad-hoc `rich.Console` instances, no `json.dumps` /
  `yaml.dump` spliced into prose.
- Every command is wrapped with `@handle_command_errors("<verb-ing> <resource>")`
  from `scm_cli.utils.decorators`; no blanket `try/except Exception` in command bodies.
- stdout carries data only, so `scm show ... --output json | jq` always works.

For module structure, section separators, option constants, docstring format,
naming, and everything else: see `.claude/STYLE_GUIDE.md`.
