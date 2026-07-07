# AI Agent Integration

The `scm` CLI ships with an `AGENTS.md` file designed to be consumed by AI coding agents such as Claude Code and Gemini CLI. This guide explains how to configure your agent to use the CLI effectively.

## Overview

AI coding agents can operate the `scm` CLI to automate Strata Cloud Manager tasks:

- Create, update, and delete SCM configuration objects via shell commands
- Perform bulk imports and exports using YAML files
- Commit staged changes and monitor job status
- Query insights for alerts, tunnels, and connectivity health
- Chain commands into end-to-end workflows (policy creation, backup/restore, audits)

## The AGENTS.md File

The `AGENTS.md` file at the repository root is a machine-readable reference covering every CLI command, option, YAML format, and workflow pattern. It is designed to give an AI agent enough context to operate the CLI without human guidance.

It includes:

- Authentication setup and context management
- Full command syntax for all 7 resource categories
- Option tables with types, defaults, and constraints
- YAML file formats for bulk load/backup operations
- Common multi-step workflows with exact commands
- 15 critical gotchas (boolean omission, tag ordering, required fields, etc.)

## Claude Code

### Project-Level Instructions

Add the `AGENTS.md` file to your Claude Code project instructions so it is automatically loaded into context.

**Option 1 — Reference in CLAUDE.md:**

Add this line to your project's `CLAUDE.md`:

```markdown
## SCM CLI Reference

When performing Strata Cloud Manager operations, refer to [AGENTS.md](AGENTS.md) for
the complete CLI command reference, YAML formats, and workflow patterns.
```

Claude Code automatically reads `CLAUDE.md` at the start of every conversation, so it will know where to find the CLI reference.

**Option 2 — Direct inclusion:**

For smaller projects, paste the contents of `AGENTS.md` directly into your `CLAUDE.md` under a dedicated section. This ensures the full reference is always in context without requiring a file read.

### MCP Server Integration

If the `scm` CLI is installed in a remote environment (Docker container, jump host, etc.), you can expose it as an MCP server tool so Claude Code can execute commands remotely.

### Example Prompts

Once Claude Code has access to `AGENTS.md`, you can issue natural-language instructions:

```
Create address objects for our three web servers (10.1.1.10, 10.1.1.11, 10.1.1.12)
in the Texas folder, group them into a "web-servers" address group, then create a
security rule allowing traffic from the trust zone to those servers on ports 80 and
443. Commit when done.
```

```
Backup all address objects and security rules from the Texas folder to YAML files.
```

```
Check if there are any critical alerts or down tunnels in SCM.
```

```
Load the services defined in services.yml with a dry run first, then apply if
everything looks correct.
```

## Gemini CLI

### Project-Level Instructions

Gemini CLI reads instructions from a `GEMINI.md` file at the project root.

**Option 1 — Reference the file:**

Create or update `GEMINI.md`:

```markdown
## SCM CLI Reference

When performing Strata Cloud Manager operations, read the file `AGENTS.md` in this
repository for the complete CLI command reference, YAML formats, and workflow patterns.
Always read AGENTS.md before executing scm commands.
```

**Option 2 — Symlink or include:**

If Gemini CLI supports file includes, reference `AGENTS.md` directly. Otherwise, copy the relevant sections into `GEMINI.md`.

### Example Prompts

The same natural-language prompts work with Gemini CLI once it has access to the reference:

```
Show me all security rules in the Texas folder, then delete any rules that are disabled.
```

```
Create a syslog server profile pointing to 192.168.1.100 on UDP/514 with BSD format,
then create a log forwarding profile that sends all traffic logs to it.
```

## Other AI Agents

The `AGENTS.md` file works with any AI agent that can:

1. Read local files for context
2. Execute shell commands

For agents without a dedicated instructions file, feed `AGENTS.md` as part of the system prompt or initial context. The file is self-contained and does not depend on external resources.

| Agent | Instructions File | How to Include |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` | Reference or inline `AGENTS.md` |
| Gemini CLI | `GEMINI.md` | Reference or inline `AGENTS.md` |
| Aider | `.aider.conf.yml` | Add to `read` file list |
| Cursor | `.cursorrules` | Inline relevant sections |
| Windsurf | `.windsurfrules` | Inline relevant sections |
| Copilot | `.github/copilot-instructions.md` | Reference or inline `AGENTS.md` |

## Authentication for Agents

AI agents running non-interactively should use environment variables for authentication to avoid storing credentials in instruction files:

```bash
export SCM_CLIENT_ID="your-client-id"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="your-tsg-id"
```

Alternatively, pre-configure a context before the agent session:

```bash
scm context create automation --client-id <id> --client-secret <secret> --tsg-id <tsg>
scm context use automation
```

:::warning
Never include credentials directly in `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or any
file committed to version control. Use environment variables or pre-configured contexts.
:::

## Best Practices

1. **Start with mock mode**: When testing agent workflows, set `SCM_MOCK=1` to validate the command structure without making API calls.
2. **Use dry runs for bulk operations**: Always run `scm load ... --dry-run` before applying YAML imports to catch errors early.
3. **Commit explicitly**: Instruct your agent to commit only when you confirm. Staged changes have no effect until committed.
4. **Scope agent permissions**: Limit the agent to specific folders to prevent unintended changes across your SCM tenant.
5. **Review before destructive actions**: Configure your agent to pause for confirmation before `delete` or `commit` operations.
6. **Use `--force` judiciously**: The `--force` flag on delete commands skips confirmation prompts. Only enable it for automated pipelines where you trust the input.

## Related Topics

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Advanced Topics](advanced-topics.md)
- [Operations](operations.md)
