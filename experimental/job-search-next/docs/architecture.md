# Architecture

## Goal

Improve the front half of Cuong's job-search workflow without replacing the current document-generation system.

## System shape

```text
Current intakes + outputs
        |
        v
Phase 1 corpus import
        |
        v
Phase 2 classification + filtering
        |
        +--> tracker.tsv
        +--> pipeline.md
        +--> verification_report.md
        |
        v
Phase 3 promotion bridge
        |
        +--> promotion-map.tsv
        +--> promotion-preview.md
        +--> optional draft payloads in promotions/
        |
        v
Existing application-system/ (read-only for now)
```

## Design principles

1. The existing `application-system/` remains the application artifact engine.
2. This prototype focuses on discovery, prefiltering, and tracking.
3. Validation uses the current real application corpus, not fake fixtures.
4. The prototype is allowed to be opinionated about:
   - role-family fit
   - German-language risk
   - geography filters
   - source and company priority
5. The prototype is not allowed to invent or overwrite live application truth.

## Phase interpretation

### Phase 1

- create explicit boundaries
- import current corpus
- check that truth surfaces are present

### Phase 2

- classify jobs into Cuong-relevant role families
- keep/review/reject
- verify the tracker against current output expectations

### Phase 3

- map tracker leads to existing live intakes and outputs
- generate promotion-ready previews for future handoff

### Phase 4A

- accept new future jobs directly into the prototype
- classify them together with the existing corpus
- write draft intake payloads in the prototype for selected future leads

### Phase 4B

- rewire the live `job-search-cuong` skill to use this subsystem first
- keep the current `application-system/` as the document-generation backend

## Expected future extension

Later, if this prototype proves useful, a live scanner can plug into the same tracker format and promotion bridge without changing the current application generator.
