---
"pan-scm-cli": major
---

**2.0: one CLI grammar, everywhere (breaking).** Object names are now positional (`scm set object tag prod --color Red`, not `--name prod`). Every containerized set/delete/show accepts `--folder`, `--snippet`, and `--device` with exactly-one enforcement (previously ~20 types were folder-only). All `load` commands support `--dry-run`; all `backup` commands support `--file` (including SASE). Flag unification: tags are always `--tags` (repeatable) — CSV `--tag` variants removed; `vlan-interface --tag` renamed `--vlan-id`; job ids are always `--id` (operations `--job-id` removed); dead `--list` flags removed from identity shows; dead `--mock` params removed from insights (use `SCM_MOCK=1`). Show commands gained `--max-results`. There are no deprecation aliases — update scripts to the new grammar (see the migration table in the release notes).
