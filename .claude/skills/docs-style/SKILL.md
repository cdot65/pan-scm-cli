---
name: docs-style
description: >
  Documentation style guide and conventions for pan-scm-cli MkDocs pages. Use this skill when
  writing, reviewing, or refactoring documentation pages under docs/. Enforces consistent structure,
  formatting, headings, admonitions, code blocks, tables, and section ordering across all CLI
  reference pages, guide pages, and about pages. Trigger when the user says things like "fix the
  docs", "update documentation", "write docs for X", "standardize docs", "review doc pages",
  or any task involving markdown files in the docs/ directory.
---

# pan-scm-cli Documentation Style Guide

You are a documentation agent. Every markdown file you write or modify under `docs/` **must**
conform to this guide. Read the full guide before making any changes.

---

## Page Taxonomy

Every documentation page falls into one of these categories. The category determines its
required structure.

| Category | Location | Purpose |
| --- | --- | --- |
| **CLI Reference (Full)** | `docs/cli/<category>/<resource>.md` | CRUD resources with set/delete/load/show/backup |
| **CLI Reference (Read-Only)** | `docs/cli/<category>/<resource>.md` | Resources with only show (and possibly backup) |
| **CLI Reference (Minimal)** | `docs/cli/<category>/<resource>.md` | Resources with limited operations |
| **CLI Special** | `docs/cli/commit.md`, `docs/cli/jobs.md`, `docs/cli/insights.md` | Non-CRUD operational commands |
| **Guide** | `docs/guide/*.md` | Conceptual/procedural documentation |
| **About** | `docs/about/*.md` | Project info, installation, contributing |
| **Home** | `docs/index.md` | Landing page (do not modify structure) |

---

## CLI Reference Pages: Canonical Structure

### Determining Page Type

A resource page is **Full** if it supports all five operations: `set`, `delete`, `load`, `show`, `backup`.
A resource page is **Read-Only** if it only supports `show` (and possibly `backup`).
A resource page is **Minimal** if it supports fewer than all five but more than just show.

Use the actual CLI commands to determine which type applies. When in doubt, check the command
module in `src/scm_cli/commands/`.

---

### Full CLI Reference Page Template

Every full CLI reference page MUST follow this exact section order. Do not skip sections.
Do not reorder sections. Do not invent new top-level sections.

```markdown
# {Resource Name}

{One-sentence description of what this resource is and what it does in SCM.}

## Overview

{2-4 bullet points describing what the CLI commands allow you to do with this resource.
Use an unordered list. Each bullet starts with a verb.}

## {Resource-Specific Context Section} (optional)

{If the resource has important types, components, or concepts the user needs to understand
before using the commands, document them here in a table or short description. Examples:
"Address Types", "Rule Components", "Supported Colors". Only include if genuinely needed
for comprehension.}

## Set {Resource}

Create or update a {resource name}.

### Syntax

```bash
scm set <category> <resource> [OPTIONS]
```

### Options

{Options table — see Table Formatting below}

### Examples

#### {Descriptive Example Title}

```bash
$ scm set <category> <resource> \
    --folder Texas \
    --name example-name \
    --option value
---> 100%
Created {resource}: example-name in folder Texas
```

{Include 2-3 examples showing different configurations or use cases.
Each example gets its own H4 heading with a descriptive title.}

## Delete {Resource}

Delete a {resource name} from SCM.

### Syntax

```bash
scm delete <category> <resource> [OPTIONS]
```

### Options

{Options table}

### Example

```bash
$ scm delete <category> <resource> --folder Texas --name example-name
---> 100%
Deleted {resource}: example-name from folder Texas
```

## Load {Resource}

Load multiple {resource name} objects from a YAML file.

### Syntax

```bash
scm load <category> <resource> [OPTIONS]
```

### Options

{Options table — must include --file, --folder, --snippet, --device, --dry-run}

### YAML File Format

```yaml
---
{resource_key}:
  - name: example-1
    folder: Texas
    {fields...}

  - name: example-2
    folder: Texas
    {fields...}
```

### Examples

#### Load with Original Locations

```bash
$ scm load <category> <resource> --file {resources}.yml
---> 100%
✓ Loaded {resource}: example-1
✓ Loaded {resource}: example-2

Successfully loaded 2 out of 2 {resources} from '{resources}.yml'
```

#### Load with Folder Override

```bash
$ scm load <category> <resource> --file {resources}.yml --folder Austin
---> 100%
✓ Loaded {resource}: example-1
✓ Loaded {resource}: example-2

Successfully loaded 2 out of 2 {resources} from '{resources}.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all {resources}
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show {Resource}

Display {resource name} objects.

### Syntax

```bash
scm show <category> <resource> [OPTIONS]
```

### Options

{Options table}

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific {Resource}

```bash
$ scm show <category> <resource> --folder Texas --name example-name
---> 100%
{Resource}: example-name
  Location: Folder 'Texas'
  {field}: {value}
  {field}: {value}
```

#### List All {Resources} (Default Behavior)

```bash
$ scm show <category> <resource> --folder Texas
---> 100%
{Resources} in folder 'Texas':
------------------------------------------------------------
Name: example-1
  {field}: {value}
------------------------------------------------------------
Name: example-2
  {field}: {value}
------------------------------------------------------------
```

## Backup {Resources}

Backup all {resource name} objects from a specified location to a YAML file.

### Syntax

```bash
scm backup <category> <resource> [OPTIONS]
```

### Options

{Options table — must include --folder, --snippet, --device, --file}

### Examples

#### Backup from Folder

```bash
$ scm backup <category> <resource> --folder Texas
---> 100%
Successfully backed up 15 {resources} to {resource}_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup <category> <resource> --folder Texas --file texas-{resources}.yaml
---> 100%
Successfully backed up 15 {resources} to texas-{resources}.yaml
```

## Best Practices

{Numbered list, 4-6 items. Each item has a bold lead phrase followed by a colon and
explanation. Focus on practical guidance specific to this resource type.}

## Related Topics

{Optional. Only include if there are meaningful cross-references. Use a short bulleted list
linking to related resource pages or guide pages.}
```

---

### Read-Only CLI Reference Page Template

```markdown
# {Resource Name}

{One-sentence description.} {Resource} management is read-only through the CLI.

## Show {Resource}

### Syntax

```bash
scm show <category> <resource> [OPTIONS]
```

### Options

{Options table}

### Examples

```bash
# List all {resources}
$ scm show <category> <resource>

# Show a specific {resource}
$ scm show <category> <resource> --name "example"

# Filter by folder
$ scm show <category> <resource> --folder Texas
```

!!! note
    {Resource} management is read-only. {Resources} cannot be created, updated, or deleted
    through the CLI.
```

---

### Minimal CLI Reference Page Template

For resources that support some but not all CRUD operations, use the Full template but only
include the sections for supported operations. Maintain the same section order — just skip
the sections that don't apply.

**Never** combine multiple operations into a single collapsed section like
"Show / Delete / Load / Backup". Each operation gets its own H2 section with full Syntax,
Options, and Examples subsections.

---

## CLI Special Pages

### Commit Page Structure

```markdown
# Commit

{One-sentence description.}

## Syntax
## Options
## Examples
```

### Jobs Page Structure

```markdown
# Jobs

{One-sentence description.}

## {Subcommand Name}
### Syntax
### Options
### Examples

{Repeat for each subcommand.}
```

### Insights Page Structure

```markdown
# Insights Commands

{Overview paragraph.}

## Overview
## Prerequisites
## Commands
### {Subcommand}
{For each subcommand: description, example commands grouped by use case.}
## Common Options
## Export Formats
## Notes
```

---

## Formatting Rules

### Headings

- **H1 (`#`)**: Page title only. One per page. Must match the resource name.
- **H2 (`##`)**: Major sections (Set, Delete, Load, Show, Backup, Overview, Best Practices).
- **H3 (`###`)**: Subsections (Syntax, Options, Examples, YAML File Format).
- **H4 (`####`)**: Individual examples or sub-subsections within Examples.
- Never skip heading levels (no H2 → H4 without H3).
- Never use H5 or H6.

### Tables

All option tables use this exact format:

```markdown
| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the resource | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--description TEXT` | Description | No |
```

Rules:
- Option names in backticks with type hint: `` `--name TEXT` ``, `` `--port INT` ``
- "Required" column values: `Yes`, `No`, `No*`, `No**`
- Asterisk footnotes go immediately after the table: `\* Explanation here.`
- Separator row uses `---` (no padding dashes for alignment)
- No trailing whitespace in cells

### Code Blocks

- **Command syntax**: Use `bash` language tag. No `$` prefix.
  ```bash
  scm set object address [OPTIONS]
  ```

- **Command examples**: Use `bash` language tag. Include `$` prefix and realistic output.
  ```bash
  $ scm set object address --folder Texas --name webserver --ip-netmask 192.168.1.100/32
  ---> 100%
  Created address: webserver in folder Texas
  ```

- **YAML examples**: Use `yaml` language tag. Include document separator `---` at top.
  ```yaml
  ---
  addresses:
    - name: example
      folder: Texas
  ```

- **JSON examples**: Use `json` language tag.

- **Multi-line commands**: Use backslash continuation with 4-space indent on continuation lines.
  ```bash
  $ scm set object address \
      --folder Texas \
      --name webserver \
      --ip-netmask 192.168.1.100/32
  ```

### Output Formatting in Examples

Use these consistent output patterns:

- **Progress indicator**: `---> 100%`
- **Success (single item)**: `Created {resource}: {name} in folder {folder}`
- **Success (delete)**: `Deleted {resource}: {name} from folder {folder}`
- **Success (bulk load)**: Use `✓` prefix (literal Unicode character, NOT HTML spans)
  ```
  ✓ Loaded {resource}: example-1
  ✓ Loaded {resource}: example-2

  Successfully loaded 2 out of 2 {resources} from '{file}'
  ```
- **Success (backup)**: `Successfully backed up N {resources} to {filename}`

**NEVER use HTML** in output examples. No `<span>` tags, no inline styles. Use plain Unicode
characters (`✓`, `✗`) directly.

### Admonitions

Use MkDocs Material admonition syntax. Supported types and when to use them:

| Type | When to Use |
| --- | --- |
| `!!! note` | Default behavior, important context, clarifications |
| `!!! tip` | Helpful suggestions, workflow improvements |
| `!!! warning` | Security concerns, destructive operations, data loss risk |
| `!!! info` | Background context, architecture details |

Format:
```markdown
!!! note
    Admonition text indented 4 spaces. Can span multiple lines
    as long as all lines are indented.
```

Rules:
- Always indent content 4 spaces
- Keep admonitions concise (1-3 sentences)
- Place admonitions immediately after the content they reference
- Use `note` for the container override reminder in Load sections
- Use `note` for "read-only" disclaimers
- Use `tip` for workflow suggestions (like checking job status after async commit)
- Use `warning` only for genuine risk (credential exposure, data deletion)

### Lists

- Use numbered lists for **Best Practices** (ordered by importance)
- Use bulleted lists for **Overview** sections and feature lists
- Bold the lead phrase in best practice items: `1. **Use Descriptive Names**: explanation`
- Keep list items to 1-2 sentences max

### Container Parameters

When documenting container parameters (--folder, --snippet, --device), use this standard
footnote pattern:

```markdown
| `--folder TEXT`  | Folder location  | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT`  | Device location  | No\* |

\* One of --folder, --snippet, or --device is required.
```

For resources that only support `--folder`:
```markdown
| `--folder TEXT` | Folder location | Yes |
```

---

## Content Guidelines

### Introductory Sentence

Every page starts with a single sentence (not a paragraph) describing the resource.
Pattern: `{Resources} {what they do} in {context}. The scm CLI provides commands to
{operations list}.`

Good:
> Address objects identify network addresses in security policies, NAT rules, and other
> configurations. The `scm` CLI provides commands to create, update, delete, and load
> address objects.

Bad:
> This section covers the commands for managing address objects in Strata Cloud Manager.
> Address objects are fundamental building blocks...

### Overview Section

Use an unordered list with 3-5 items. Each item starts with a verb:
```markdown
## Overview

The `{resource}` commands allow you to:

- Create {resources} with {key configuration}
- Update existing {resource} configurations
- Delete {resources} that are no longer needed
- Bulk import {resources} from YAML files
- Export {resources} for backup or migration
```

### Example Values

Use realistic but obviously fake data:
- **Folders**: `Texas`, `Austin`, `Shared`
- **Names**: `webserver`, `prod-server`, `corp-ldap`, `Allow-Internal-Web`
- **IPs**: `192.168.1.x/32`, `10.0.1.x/24`
- **Domains**: `example.com`, `internal.example.com`
- **Descriptions**: Short, professional phrases

### YAML Key Naming

YAML keys use `snake_case` matching the SDK model field names:
- `ip_netmask` (not `ip-netmask`)
- `source_zones` (not `source-zones`)
- `enable_user_id` (not `enable-user-id`)

CLI flags use `kebab-case`:
- `--ip-netmask`
- `--source-zones`
- `--enable-user-id`

Always document both forms when showing YAML alongside CLI examples.

### Cross-References

Use relative paths for internal links:
```markdown
[Installation](../about/installation.md)
[Configuration](../guide/configuration.md)
```

Never use absolute URLs for internal documentation pages.

---

## Quality Checklist

Before finalizing any documentation page, verify:

- [ ] Page follows the correct template for its category
- [ ] All sections are in the canonical order
- [ ] H1 matches the resource name (singular form, title case)
- [ ] Every code block has a language tag (`bash`, `yaml`, `json`)
- [ ] Command syntax blocks have NO `$` prefix
- [ ] Command example blocks HAVE `$` prefix
- [ ] All option tables have 3 columns: Option, Description, Required
- [ ] Option names include type hints in backticks
- [ ] No HTML in any code block output (use Unicode ✓/✗ directly)
- [ ] Admonitions are 4-space indented
- [ ] YAML examples use `snake_case` keys
- [ ] CLI examples use `kebab-case` flags
- [ ] Container override note is present in Load section
- [ ] "No `--name` = list all" note is present in Show section
- [ ] Best Practices section has numbered items with bold lead phrases
- [ ] No collapsed/combined operation sections (each operation gets full treatment)
- [ ] Multi-line commands use backslash continuation with 4-space indent
- [ ] Page ends with Best Practices or Related Topics (no trailing blank sections)
