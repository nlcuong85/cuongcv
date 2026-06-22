# SOP Governance Hardening — 2026-06-19

## Context

CuongCV previously had no durable controller for multi-step agent work. Application generation, public-site changes, validation, and deployment could therefore be separated from their exact goal and handoff after context compaction.

## Root cause

- Immediate gap: no persisted session, command, handoff, or repository-snapshot state.
- Mechanism: `AGENTS.md` documented domain workflows but had no executable workflow controller.
- Source-level cause: repository governance depended on chat continuity rather than an evidence-backed local state machine.

## Upgrade

- Added `SOP.py` with tasks, sessions, checkpoints, handoffs, Kiro evidence, command logging, repository snapshots, strict preflight, and postflight.
- Added machine-readable `state.json` and generated `SOP_STATE.md`.
- Added transaction-wide locking. This improves on the source Focalboard implementation, whose lock covered individual reads and writes but not the whole read-modify-write operation.
- Added atomic file replacement with file and directory synchronization.
- Restricted `run --cwd` to paths inside CuongCV and removed shell execution.
- Added regression tests for evidence enforcement, fresh sessions, path containment, drift detection, and concurrent updates.

## Required workflow

```bash
python3 SOP.py preflight --strict
python3 SOP.py status
python3 SOP.py resume
python3 SOP.py session --goal "<current work>" --task-id "<stable-id>"
python3 SOP.py run -- pnpm check
python3 SOP.py handoff --current "..." --next "..." --risk "..."
python3 SOP.py postflight --summary "..." --next-step "..."
```
