# Current Skill vs. Career-Ops

## Scope

This assessment compares:

- Current local skill:
  - `/Users/pmlecuong/.codex/skills/job-search-cuong`
- Related local skills:
  - `/Users/pmlecuong/.codex/skills/web-search-skill`
  - `/Users/pmlecuong/.codex/skills/builder-ops`
  - `/Users/pmlecuong/.codex/skills/playwright`
  - `/Users/pmlecuong/.codex/skills/codex-understanding`
  - `/Users/pmlecuong/.codex/skills/.system/skill-creator`
- Reference repo:
  - `/Users/pmlecuong/Documents/CuongProjects/CuongCV/experimental/job-search-skill-assessment/external/career-ops`

## Files reviewed

Current skill side:

- `job-search-cuong/SKILL.md`
- `job-search-cuong/agents/openai.yaml`
- `job-search-cuong/references/profile_sources.md`
- `job-search-cuong/references/skill-memory.md`
- `job-search-cuong/references/cv-site-ops.md`
- `web-search-skill/SKILL.md`
- `builder-ops/SKILL.md`
- `playwright/SKILL.md`
- `codex-understanding/SKILL.md`
- `skill-creator/SKILL.md`

Career-ops side:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `DATA_CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/CODEX.md`
- `docs/SCRIPTS.md`
- `config/profile.example.yml`
- `templates/portals.example.yml`
- `package.json`
- `modes/_shared.md`
- `modes/auto-pipeline.md`
- `modes/scan.md`
- `modes/apply.md`
- `modes/pipeline.md`
- `batch/README.md`
- `batch/batch-prompt.md`
- `scan.mjs`
- `update-system.mjs`
- `verify-pipeline.mjs`
- `generate-pdf.mjs`
- `cv-sync-check.mjs`
- `analyze-patterns.mjs`
- `followup-cadence.mjs`
- `dashboard/internal/ui/screens/pipeline.go`

## Executive assessment

The current `job-search-cuong` skill is strong on:

- repo-specific truth
- Germany-specific application constraints
- CV/application factual consistency
- operational memory for Franklee and the current application generator

But it is weak on:

- clear system boundaries
- portable structured state
- low-token automation surfaces
- deterministic job-search tooling
- reusable tracker analytics
- update-safe separation between stable system logic and user-specific data

`career-ops` is not better because its prompts are longer. It is better because it turns job search into an operating system with:

- a clean data contract
- dedicated scripts for repetitive checks
- a tracker-centered workflow
- a scanner that does useful work without an LLM
- explicit update boundaries
- separate modes instead of one expanding instruction blob

## What the current skill gets right

These should be preserved:

1. Strong alignment with Cuong's real CV repo and application generator
2. Explicit non-invention rules for experience and factual identity
3. Germany-specific cover-letter, language-risk, and page-limit rules
4. Integration with `web-search-skill`, `builder-ops`, and `playwright`
5. Real operational memory for Franklee production behavior

## Main weaknesses in the current skill

### 1. Too many jobs in one skill

`job-search-cuong` currently mixes:

- Germany job search
- CV site editing
- GitHub Pages deployment
- application generation
- recruiter email handling
- Franklee runtime operations

That makes it useful, but also heavy, harder to maintain, and harder to evolve safely.

### 2. Too much durable memory lives in markdown

`references/skill-memory.md` contains valuable learned behavior, but it is also acting as:

- changelog
- operating memory
- production runtime note store
- policy surface

That makes the skill smarter, but not more structured. Important logic is hard to validate automatically.

### 3. Not enough deterministic helper scripts

The current skill has only one local script:

- `scripts/check_application_rules.py`

Compared with `career-ops`, that means many repeated tasks still depend on prompt discipline rather than machine-checkable scripts.

### 4. No explicit data contract

There is no clean separation between:

- stable system logic
- Cuong-specific data
- generated outputs
- remote Franklee runtime state

That makes future refactoring risky.

### 5. No tracker-centered operating model

Current workflow is strong for one-off application generation, but weak for:

- portfolio-wide pipeline visibility
- status normalization
- dedup
- follow-up cadence
- retrospective analysis of what roles convert

### 6. No update-safe extension layer

The current skill is deeply personalized, but it does not yet separate:

- base workflow
- user-specific targeting
- experimental enhancements

That makes improvement harder because every change feels like editing the live engine.

## What career-ops does materially better

### 1. System vs user separation

Best idea:

- `DATA_CONTRACT.md`

Why it matters:

- protects user data from system updates
- makes future upstream sync or local refactors safe
- prevents personal facts from leaking into shared prompt files

Fast adaptation for Cuong:

- define the same boundary for:
  - skill logic
  - Cuong-specific profile data
  - application artifacts
  - Franklee runtime data

### 2. Mode decomposition

Best idea:

- dedicated mode files for scan, apply, pipeline, tracker, deep research, follow-up, pattern analysis

Why it matters:

- smaller context
- clearer routing
- easier iterative improvement

Fast adaptation for Cuong:

- split the current skill into a small orchestration skill plus focused sub-workflows

### 3. Deterministic scanner

Best idea:

- `scan.mjs` uses ATS APIs directly and writes results into pipeline state without burning LLM tokens

Why it matters:

- low cost
- repeatable
- easy to test
- better than stuffing portal-scanning logic into prompt text

Fast adaptation for Cuong:

- build a Germany-focused scanner prototype that:
  - reads a Cuong profile config
  - scans a curated set of ATS sources
  - applies hard filters before any model reasoning
  - writes results into an experimental tracker

### 4. Pipeline integrity scripts

Best ideas:

- `verify-pipeline.mjs`
- `normalize-statuses.mjs`
- `dedup-tracker.mjs`
- `merge-tracker.mjs`

Why they matter:

- turns tracker hygiene into code, not hope

Fast adaptation for Cuong:

- add a small tracker schema plus validator for experimental job-search runs

### 5. Sync checks

Best idea:

- `cv-sync-check.mjs`

Why it matters:

- catches setup drift early
- reinforces source-of-truth discipline

Fast adaptation for Cuong:

- add a `job-search sync check` prototype that validates:
  - CV truth parity
  - generator truth parity
  - search config presence
  - output folders
  - key environment files

### 6. Update-safe system refresh

Best idea:

- `update-system.mjs`

Why it matters:

- makes the system maintainable over time

Fast adaptation for Cuong:

- not an immediate priority for the Cuong repo, but the pattern is valuable:
  - explicit allowlist of update-safe files
  - explicit never-touch user files

### 7. Analytics on pipeline outcomes

Best ideas:

- `analyze-patterns.mjs`
- `followup-cadence.mjs`

Why they matter:

- they help improve job-search strategy using accumulated data

Fast adaptation for Cuong:

- extremely useful
- especially because current workflow is optimized for document generation, not learning loops

### 8. Dedicated dashboard

Best idea:

- Go TUI dashboard over the tracker

Why it matters:

- gives operational visibility

Fast adaptation for Cuong:

- not phase 1
- useful later if the experimental tracker becomes real

## What not to copy directly

These parts of `career-ops` should not be copied as-is:

1. The role archetypes
   - They are built for Santiago's AI-market targeting, not Cuong's Germany-first role mix.
2. The compensation logic
   - Cuong's market, visa, and role-family filters are different.
3. The default language and tone system
   - Cuong needs stricter recruiter-safe German-market behavior.
4. The tracker schema as the only source of truth
   - Cuong already has a richer application generator and canonical CV sources.
5. The PDF generation template
   - Cuong already has a CV/application rendering pipeline; replacing it now would add risk with little gain.
6. The assumption that one system owns everything
   - In Cuong's repo, the application generator is already a real subsystem and must stay authoritative for generated application artifacts.

## What we can copy or adapt quickly

## P0: very fast, low-risk, high value

1. Add an experimental data contract document
   - Define:
     - system layer
     - Cuong profile layer
     - job-search tracker layer
     - generated outputs
     - Franklee/live-runtime layer

2. Create a small experimental profile config
   - Example file:
     - `experimental/job-search-skill-assessment/prototype/profile.yml`
   - Store:
     - role families
     - geography rules
     - language constraints
     - salary floors
     - exclusion rules

3. Create an experimental tracker format
   - Keep it separate from current application outputs
   - Use markdown or TSV first
   - Track:
     - source
     - URL
     - company
     - role
     - city
     - language risk
     - salary
     - status
     - notes

4. Create a sync-check script prototype
   - Validate the minimum required local truth before a search run

## P1: fast and worth building next

1. Build a zero-token discovery script
   - Germany-first
   - ATS/API-first
   - curated companies and portals
   - writes only into the experimental tracker/pipeline

2. Build tracker hygiene scripts
   - dedup
   - normalize statuses
   - validate paths
   - check dead URLs

3. Split the current job-search logic into experimental sub-docs
   - `scan.md`
   - `pipeline.md`
   - `tracker.md`
   - `followup.md`
   - `research.md`
   - `franklee-runtime.md`

4. Move volatile Franklee memory out of the main skill narrative
   - keep it in a dedicated operational reference or structured runtime config

## P2: medium effort, strong upside

1. Add retrospective analytics
   - pattern analysis by role family, city, language requirement, salary disclosure, source

2. Add follow-up cadence support
   - only for applications that have actually been submitted

3. Add a pipeline inbox
   - search adds leads
   - human or agent promotes good leads into application workflow

## P3: only after P0-P2 work well

1. Dashboard
   - terminal UI or lightweight local web view

2. Safe update layer for the experimental subsystem

3. Batch orchestration for multi-offer assessment
   - only after tracker and filters are stable

## Recommended target architecture for Cuong

Do not replace the current workflow. Add a new experimental layer beside it:

1. Discovery layer
   - finds and prefilters openings
   - no document generation yet

2. Evaluation layer
   - scores fit against Cuong-specific rules
   - flags language/salary/location risk

3. Promotion layer
   - promotes selected leads into the current application system

4. Application layer
   - keep existing `application-system/` as the canonical document generator

5. Operations layer
   - tracker, dedup, liveness, follow-up, analytics

This is the right adaptation because `career-ops` should improve the front half of the funnel for Cuong, not replace the back half that already exists.

## Proposed implementation plan

### Phase 1

Create a separate prototype folder:

- `experimental/job-search-next/`

Inside it:

- `DATA_CONTRACT.md`
- `config/profile.yml`
- `config/portals.yml`
- `data/pipeline.md`
- `data/tracker.md`
- `scripts/sync_check.py`
- `scripts/scan_jobs.py`
- `scripts/verify_tracker.py`
- `docs/architecture.md`

Goal:

- prove a clean discovery and tracker loop without touching the live skill

### Phase 2

Add Cuong-specific discovery logic:

- Germany-only or region-scoped filters
- English-first filter
- hard reject explicit strong-German roles
- salary-floor logic per role family
- company allowlist/priority list

Goal:

- produce a clean shortlist better than current ad hoc search

### Phase 3

Add promotion bridge into the current application workflow:

- selected lead becomes intake seed
- optional JD cache
- optional contact lookup
- optional application recommendation report

Goal:

- make job search feed the existing application engine cleanly

### Phase 4

If the prototype proves useful:

- refactor `job-search-cuong` to route into this new subsystem
- keep Franklee ops separate from normal local job-search usage

## My recommendation

The best near-term move is not "copy career-ops."

The best move is:

1. copy the architecture patterns
2. copy the deterministic helper-script mindset
3. copy the data-contract separation
4. copy the tracker/integrity/analytics layer
5. keep Cuong's existing application generator as the document engine

If approved, the first implementation step should be a new experimental subsystem under:

- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/experimental/job-search-next`

That would let us build the useful parts of `career-ops` quickly without destabilizing the current repo workflow.
