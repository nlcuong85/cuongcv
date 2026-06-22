# CuongCV SOP Governance Sequence

## Substantial work

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent
    participant Contract as AGENTS.md
    participant SOP as SOP.py
    participant State as governance/.sop/state.json
    participant Brief as governance/SOP_STATE.md
    participant Repo as CuongCV repository
    participant Logs as governance/.sop/run_logs

    User->>Agent: Request substantial work
    Agent->>Contract: Read operating contract
    Agent->>SOP: preflight --strict
    SOP->>State: Lock and load durable state
    SOP->>Repo: Compare source snapshot
    SOP-->>Agent: Goal, task, handoff, drift, risks
    Agent->>SOP: session --goal ... --task-id ...
    SOP->>State: Transactionally persist fresh session

    loop Meaningful work unit
        Agent->>Repo: Edit canonical source
        Agent->>SOP: run --cwd ... -- command
        SOP->>Repo: Execute command without shell
        Repo-->>SOP: stdout, stderr, exit code
        SOP->>Logs: Atomically persist command log
        SOP->>State: Persist evidence and checkpoint
        Agent->>SOP: handoff --current --next --risk
        SOP->>State: Persist exact continuation state
        SOP->>Brief: Refresh readable recovery view
    end

    Agent->>SOP: postflight --summary ...
    SOP->>State: Validate, close session, and snapshot
    SOP->>Repo: Confirm zero post-snapshot drift
    Agent-->>User: Report files, checks, and residual risk
```

## Concurrent mutation protection

```mermaid
sequenceDiagram
    participant A as SOP command A
    participant Lock as state.lock
    participant State as state.json
    participant B as SOP command B

    A->>Lock: Acquire exclusive lock
    A->>State: Read, modify, atomically replace
    B->>Lock: Wait
    A-->>Lock: Release
    B->>Lock: Acquire exclusive lock
    B->>State: Read A's committed state, modify, replace
    B-->>Lock: Release
```

## Recovery rules

- Run `status`, `resume`, and `audit` after context compaction.
- Verify filesystem and generated artifacts before claiming completion.
- Use evidence-backed `kiro-done` for Kiro tasks.
- Use `--keep-session` only when deliberately continuing the same work.
- Update this document when the SOP command contract changes materially.
