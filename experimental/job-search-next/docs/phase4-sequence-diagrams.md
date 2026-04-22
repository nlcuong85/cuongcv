# Phase 4 Sequence Diagrams

This document shows the difference between the old workflow and the new workflow we are building.

## Old workflow

The old path is more direct but less structured.

```mermaid
sequenceDiagram
    participant User
    participant Skill as "job-search-cuong"
    participant Search as "Ad hoc search / browsing"
    participant App as "application-system"
    participant Output as "Generated application package"

    User->>Skill: "Find a job / make application"
    Skill->>Search: Search manually or semi-manually
    Search-->>Skill: Possible jobs or one chosen job
    Skill->>App: Create or update intake
    App->>Output: Generate CV, cover letter, snapshot
    Output-->>User: Application artifacts
```

Problem:

- search and filtering are mixed together
- no separate tracker-first stage
- no clean keep/review/reject funnel before document generation

## New workflow after Phase 4A

This keeps the current application engine, but adds a front-door controller.

```mermaid
sequenceDiagram
    participant User
    participant Intake as "job-search-next add_job / scanner"
    participant Tracker as "job-search-next tracker"
    participant Filter as "job-search-next classification + filtering"
    participant Bridge as "promotion bridge"
    participant App as "application-system"

    User->>Intake: Add future job URL/JD
    Intake->>Tracker: Save raw lead
    Tracker->>Filter: Classify role and fit
    Filter-->>User: keep / review / reject
    User->>Bridge: Promote selected lead
    Bridge->>Bridge: Write draft intake payload
    Bridge-->>User: Promotion-ready intake draft
    Note over App: App system stays unchanged in Phase 4A
```

## New workflow after full Phase 4B

This is the target operating model.

```mermaid
sequenceDiagram
    participant User
    participant Skill as "job-search-cuong"
    participant Next as "job-search-next"
    participant App as "application-system"
    participant Output as "Generated application package"

    User->>Skill: "Search jobs" or paste JD/URL
    Skill->>Next: Route to discovery + tracker layer
    Next-->>Skill: keep / review / reject result
    alt User approves promotion
        Skill->>Next: Promote selected lead
        Next->>App: Write intake for real workflow
        App->>Output: Generate CV, cover letter, snapshot
        Output-->>User: Final recruiter-ready artifacts
    else User does not approve
        Skill-->>User: Keep in review queue only
    end
```

## Short explanation

Old workflow:

- search and apply are too close together

New workflow:

- collect lead
- classify it
- decide if it is worth attention
- only then hand it to the real application engine

Phase 4B in this repo now means:

- the live skill routes future job-search work into `experimental/job-search-next`
- approved promotions can write a real draft intake into `application-system/intakes/`
- the existing `application-system/` remains the generator and truth layer for application artifacts

## Queue-assisted workflow with Franklee 3 p.m. student source

This is the practical future workflow for manual job-search requests.

```mermaid
sequenceDiagram
    participant User
    participant Skill as "job-search-cuong"
    participant Franklee as "Franklee 15:00 student validator"
    participant Manual as "Manual URL / JD"
    participant Next as "job-search-next"
    participant App as "application-system"

    User->>Skill: "Run job search" + optional manual URL
    Skill->>Franklee: Import current student shortlist
    Skill->>Manual: Read manual job input
    Franklee-->>Next: Validated queue items
    Manual-->>Next: Manual lead
    Next->>Next: Merge, dedupe, classify, keep/review/reject
    Next-->>Skill: Tracker + pipeline result
    alt keep
        Skill->>Next: Promote approved lead
        Next->>App: Write draft intake
        App-->>Skill: CV / cover letter / snapshot workflow
    else review
        Skill-->>User: Ask before promotion
    else reject
        Skill-->>User: Stop before document generation
    end
```
