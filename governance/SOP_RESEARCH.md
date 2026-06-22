# CuongCV SOP Harness Rationale

Created: `2026-06-19`

## Problem

CuongCV combines a public Next.js CV, an application generator, recruiter-facing outputs, and deployment workflows. Long tasks can cross these layers. Chat compaction or a new agent session can lose the exact goal, command evidence, changed files, page-limit results, and next action.

## Source-of-truth hierarchy

1. Canonical product facts remain in `src/data/resume-data.tsx` and `application-system/data/master_profile.json` as defined by `AGENTS.md`.
2. `governance/.sop/state.json` is the machine-readable source of truth for work state.
3. `governance/SOP_STATE.md` is the generated human-readable recovery view.
4. Repository files and the running application prove implementation state.
5. Chat summaries are context only and never completion evidence.

The SOP records workflow state; it does not replace the CV or application data sources.

## Design decisions

- State mutations hold one exclusive `fcntl` lock across the complete read-modify-write transaction. This prevents two commands from reading the same state and later overwriting one another.
- JSON and Markdown writes use a same-directory temporary file, file `fsync`, atomic replacement, and directory `fsync`.
- `run --cwd` accepts only directories inside the repository and executes argument arrays without a shell.
- Kiro completion requires evidence.
- Strict preflight fails on missing snapshots, filesystem drift, stale sessions, or inconsistent Kiro state.
- Postflight updates the handoff, closes the session by default, validates state, records a new snapshot, and confirms that snapshot is clean.

## Snapshot scope

Snapshots cover source and governance files. They exclude generated or high-churn paths such as `.git`, `node_modules`, `.next`, `out`, logs, application outputs, generated CV JSON, test reports, and SOP command logs. Generated application deliverables remain governed by their intake files, generator validation, and explicit handoff evidence.

## Operational rule

Use SOP commands sequentially from an agent workflow even though mutations are transaction-safe. The lock prevents lost updates; it does not decide which competing logical goal should win.
