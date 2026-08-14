# Migration Guide

Use this when the student already has the older MCP workspace structure.

## Old Structure

```text
candidate/
jobs/
outputs/
application-kit/
```

## New Structure

```text
AGENTS.md
CHANGELOG.md
MIGRATION.md
COPILOT.md
CLAUDE.md
GEMINI.md
context_pack.md
copilot_context.md
copilot_quick_context.md
profile/
memory/
scripts/
candidate/
jobs/
outputs/
application-kit/
```

## Safe Migration Rule

Do not delete or overwrite student data.

Run:

```bash
python3 scripts/migrate_legacy_workspace.py .
```

The migration script:

- keeps `candidate/`, `jobs/`, and `outputs/` in place
- copies old candidate files into `memory/legacy/candidate/`
- creates missing `profile/` and `memory/` files from safe starter templates
- adds notes that tell the agent where old data came from
- does not send anything to the MCP server
- does not include the private human-fit checker script

After migration, the local agent should read `profile/` and `memory/` first, then use preserved old files only as supporting evidence.

