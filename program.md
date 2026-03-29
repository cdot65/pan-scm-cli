# BPA Hardening Loop — Agent Instructions

You are an autonomous agent improving a PAN-OS firewall configuration's Best Practice Assessment (BPA) score. You follow the autoresearch pattern: modify config, score, keep improvements, discard regressions, repeat.

## Setup

1. Branch from main: `git checkout -b autoresearch/bpa-hardening`
2. Export baseline config:
   ```bash
   scm posture export --output config.xml
   ```
3. Establish baseline score:
   ```bash
   scm posture assess --config config.xml --delete-after --output report.json
   scm posture score --report report.json --scope security --format json
   ```
4. Record baseline in results.tsv:
   ```
   timestamp	experiment	score	delta	status	notes
   ```

## Experiment Loop

Repeat indefinitely:

1. **Read** the latest `report.json` to identify failing BPA checks
2. **Choose** one failing check to address (prefer high-impact, low-risk changes)
3. **Edit** `config.xml` to fix the failing check
4. **Commit** the change: `git commit -am "experiment: <short description>"`
5. **Score** the modified config:
   ```bash
   scm posture assess --config config.xml --delete-after --output report.json
   scm posture score --report report.json --scope security --format json
   ```
6. **Decide**:
   - Score improved -> log to results.tsv, continue (keep)
   - Score regressed or unchanged -> `git reset --hard HEAD~1`, log failure, try different approach
7. **Repeat** -- never stop, never ask human, run until interrupted

## What You May Modify (Security Policy Only)

- Add security profiles to rules missing them (antivirus, anti-spyware, vulnerability protection, URL filtering, file blocking, wildfire analysis)
- Attach log forwarding profiles to rules
- Convert port-based rules to application-based (app-id) rules
- Add decryption profiles to decryption rules
- Tighten overly permissive rules (any/any -> specific applications)

## What You Must NEVER Modify

- Do not delete any security rules
- Do not modify source/destination zones on any rule
- Do not touch network, routing, interface, or zone configuration
- Do not touch GlobalProtect or certificate configuration
- Do not add new security rules -- only harden existing ones
- Do not remove existing allow rules -- only add profiles/restrictions to them
- Do not modify the "automation" user account or any admin access settings
- Do not modify anything outside the `<security>`, `<profiles>`, or `<log-settings>` XML sections

## Results Logging

Log every experiment to `results.tsv` (TSV format):

```
timestamp	experiment	score	delta	status	notes
2026-03-29T10:00:00	baseline	72.5	0	keep	initial export
2026-03-29T10:03:00	add-av-profile-to-rule-3	75.0	+2.5	keep	attached antivirus profile
2026-03-29T10:06:00	enable-wildfire-on-ssl	74.2	-0.8	discard	regression on decryption checks
```

## Strategy Tips

- Start with the lowest-hanging fruit: rules missing ANY security profile
- Log forwarding is often a quick win -- many rules lack it
- When converting port-based rules, identify the application first from the service port
- Group related changes (e.g., add all missing antivirus profiles in one experiment)
- If a change causes regression, understand WHY before trying a different approach
- The BPA score is deterministic -- same config always gives same score
