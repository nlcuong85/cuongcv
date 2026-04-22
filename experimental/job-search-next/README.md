# Job Search Next Prototype

This is an experimental job-search subsystem inspired by `career-ops`, but adapted to Cuong's current repository and workflow.

It is intentionally separate from:

- `/Users/pmlecuong/.codex/skills/job-search-cuong`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system`

The current live workflow stays unchanged.

## What this prototype does

Phase 1:

- defines a data contract
- keeps Cuong-specific search config in one place
- imports the current application corpus as a test fixture
- validates that the prototype can see the existing truth surfaces

Phase 2:

- classifies current jobs into role families
- applies simple keep/review/reject filters
- writes an experimental tracker and pipeline
- verifies structural and expectation-level quality against current application outputs

Phase 3:

- creates a read-only bridge from the experimental tracker back to the current application workflow
- shows which leads already map to existing intake/output artifacts
- can write draft promotion payloads in this folder for unmatched leads

## Main files

- `DATA_CONTRACT.md`
- `docs/architecture.md`
- `docs/franklee-queue-integration.md`
- `docs/phase4-sequence-diagrams.md`
- `config/profile.yml`
- `config/portals.yml`
- `data/pipeline.md`
- `data/raw_leads.jsonl`
- `data/tracker.tsv`
- `scripts/sync_check.py`
- `scripts/import_current_jobs.py`
- `scripts/add_job.py`
- `scripts/import_franklee_queue.py`
- `scripts/import_live_franklee_run.py`
- `scripts/import_live_franklee_validator.py`
- `scripts/run_search_queue.py`
- `scripts/check_ats_readiness.py`
- `scripts/scan_jobs.py`
- `scripts/verify_tracker.py`
- `scripts/promote_to_application.py`
- `scripts/build_interaction_tracker.py`
- `scripts/draft_recruiter_email.py`
- `scripts/read_active_browser_tab.py`
- `scripts/browser_form_helper.py`

## Commands

Phase 1:

```bash
python3 experimental/job-search-next/scripts/sync_check.py
python3 experimental/job-search-next/scripts/import_current_jobs.py
```

Phase 2:

```bash
python3 experimental/job-search-next/scripts/scan_jobs.py --from-current-corpus
python3 experimental/job-search-next/scripts/verify_tracker.py
```

Phase 3:

```bash
python3 experimental/job-search-next/scripts/promote_to_application.py
```

Phase 4A:

```bash
python3 experimental/job-search-next/scripts/add_job.py --json experimental/job-search-next/examples/future-lead-example.json
python3 experimental/job-search-next/scripts/scan_jobs.py --all
python3 experimental/job-search-next/scripts/promote_to_application.py --lead-id future-sample-product-ops-student --write-intake
```

Phase 4B:

```bash
python3 experimental/job-search-next/scripts/promote_to_application.py \
  --lead-id future-sample-product-ops-student \
  --write-intake \
  --write-live-intake
```

Then run the real backend:

```bash
python3 application-system/scripts/generate_application.py \
  --intake application-system/intakes/draft-future-sample-product-ops-student.json \
  --compile-pdf
```

Franklee 3 p.m. student queue plus manual lead:

```bash
python3 experimental/job-search-next/scripts/run_search_queue.py \
  --profile student \
  --franklee-source-json experimental/job-search-next/examples/franklee-student-sample.json \
  --company "Example GmbH" \
  --title "Working Student Product Operations" \
  --url "https://example.com/jobs/example-working-student-product-operations" \
  --location "Heilbronn, Baden-Wuerttemberg, Germany" \
  --description "Support product operations, requirements analysis, and AI-assisted workflows."
```

The real local Franklee replica command is:

```bash
python3 /Users/pmlecuong/Documents/CuongProjects/OpenClaw-franklee/scripts/run_local_franklee_job_search.py --profile student --format json
```

Live Franklee April 13 run import:

```bash
python3 experimental/job-search-next/scripts/import_live_franklee_run.py \
  --profile student \
  --date 2026-04-13
python3 experimental/job-search-next/scripts/scan_jobs.py \
  --from-raw-leads \
  --source-prefix franklee_live_student_2026-04-13
```

Cheaper future manual path from live Franklee validator JSON:

```bash
python3 experimental/job-search-next/scripts/import_live_franklee_validator.py \
  --profile student \
  --source-label 2026-04-14
python3 experimental/job-search-next/scripts/scan_jobs.py \
  --from-raw-leads \
  --source-prefix franklee_live_direct_student_2026-04-14
```

Or in one combined queue run:

```bash
python3 experimental/job-search-next/scripts/run_search_queue.py \
  --profile student \
  --live-franklee-direct \
  --source-label 2026-04-14 \
  --company "Example GmbH" \
  --title "Working Student Product Operations" \
  --url "https://example.com/jobs/example-working-student-product-operations" \
  --location "Heilbronn, Baden-Wuerttemberg, Germany" \
  --description "Support product operations, requirements analysis, and AI-assisted workflows."
```

ATS parseability heuristic:

```bash
python3 experimental/job-search-next/scripts/check_ats_readiness.py \
  --scan-generated-resumes \
  --latest-only
```

Recruiter tracker and email drafts:

```bash
python3 experimental/job-search-next/scripts/build_interaction_tracker.py
python3 experimental/job-search-next/scripts/draft_recruiter_email.py --slug audi-ag --intent reply
```

Mode A real-browser companion helper:

```bash
python3 experimental/job-search-next/scripts/read_active_browser_tab.py \
  --extract-form \
  --output-name active-browser-tab
python3 experimental/job-search-next/scripts/browser_form_helper.py \
  --slug bosch-group-werkstudent-cleanroom-process-quality-w-m-div \
  --output-name bosch-browser-helper
```

The browser helper is intentionally not a separate automation browser. It reads the frontmost real browser tab when macOS automation permissions and an open window are available, then prepares suggestions and upload paths for manual use in that same browser session.

## Safety rules

- Live intake writing is allowed only through the explicit promotion path.
- Use `--write-live-intake` only for leads you intentionally want to hand into the real application workflow.
- `review` leads need `--allow-review` before a draft intake can be written.
- `reject` leads do not promote into application drafting.
- The recruiter tracker and email drafter stay in the experimental area and do not modify live `communication-log.md` files automatically.
- The browser helper is Mode A only: read, suggest, and prepare uploads. It does not auto-submit forms.
- Treat current `application-system/` files as the source of truth for existing applications.
- Use the current intakes and manifests as the expectation set during prototype validation.
