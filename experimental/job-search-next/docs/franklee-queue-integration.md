# Franklee Queue Integration

This note explains how the experimental job-search front door now uses the Franklee 15:00 student workflow as an input source.

## What the 15:00 job actually does

The Franklee 15:00 Europe/Berlin student job is validator-first and currently runs through a systemd timer/service on the Franklee host, not through the old OpenClaw cron/agentTurn path.

Current production surfaces:

- SSH target: `root@100.124.166.95`
- workspace: `/root/clawdFrankLee`
- timer: `/etc/systemd/system/franklee-job-search-slack.timer`
- service: `/etc/systemd/system/franklee-job-search-slack.service`
- runner: `/usr/local/bin/franklee-job-search-slack-runner.py`
- validator: `/root/clawdFrankLee/dist/job_search_prefilter.py`
- output/manifest folder: `/root/.openclaw/manual-recovery/`
- Slack channel: `C0AN1ENTLMQ`

It runs the validator directly:

```bash
python3 /root/clawdFrankLee/dist/job_search_prefilter.py --combined-1500 --max-age-days 20
```

The runner saves the report Markdown, validates the visible output contract, posts visible chunks to Slack, and writes a delivery manifest. Do not infer success from scheduler state alone; verify scheduler, report artifact, delivery manifest, and Slack timestamps separately.

The old OpenClaw cron id `74e37d6d-099b-4ef8-84b1-53a5cbc06b43` is historical for this workflow. Do not re-enable it unless there is a deliberate migration plan.

Health check:

```bash
ssh root@100.124.166.95 'systemctl list-timers franklee-job-search-slack.timer --all --no-pager'
ssh root@100.124.166.95 'systemctl status franklee-job-search-slack.service --no-pager'
ssh root@100.124.166.95 'journalctl -u franklee-job-search-slack.service --since "today 14:55" --no-pager'
ssh root@100.124.166.95 'ls -lh /root/.openclaw/manual-recovery/job-search-$(date +%F)-1500*'
```

A healthy day has service `0/SUCCESS`, a `job-search-YYYY-MM-DD-1500.md` report, a `job-search-YYYY-MM-DD-1500.delivery.json` manifest with `status: posted`, and Slack `message_ts` values.

Current visible report contract:

- two sections only: `Section 1` for working student / internship / part-time and `Section 2` for full-time
- no separate German-heavy `Section 3`
- no-date jobs are allowed and render as `Posted: Date not found`
- dated stale jobs are still rejected
- one bad URL must become a row-level `fetch_failed`, not a whole-run failure

## What is implemented in this repo

The experimental front door can now import the Franklee student shortlist into:

- `data/raw_leads.jsonl`
- `data/franklee_student_queue.json`
- `data/franklee_student_queue.md`

New scripts:

- `scripts/import_franklee_queue.py`
- `scripts/import_live_franklee_run.py`
- `scripts/import_live_franklee_validator.py`
- `scripts/run_search_queue.py`
- `scripts/check_ats_readiness.py`

## Future manual workflow

If you want to start from the Franklee 3 p.m. queue only:

```bash
python3 experimental/job-search-next/scripts/run_search_queue.py \
  --profile student \
  --franklee-source-json experimental/job-search-next/examples/franklee-student-sample.json
```

If you also want to add one manual lead in the same run:

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

That run will:

1. import the Franklee queue
2. append the manual lead
3. run the experimental keep/review/reject filter
4. write:
   - `data/pipeline.md`
   - `data/tracker.tsv`
   - `data/verification_report.md`

## Promotion gate

Promotion is now stricter:

- `keep` can be promoted normally
- `review` cannot write an intake unless `--allow-review` is added
- `reject` cannot be promoted from the tracker

Example:

```bash
python3 experimental/job-search-next/scripts/promote_to_application.py \
  --lead-id sample-mobility-gmbh-working-student-business-analysis-ai-workflow \
  --write-intake
```

## Live Franklee run replay

If remote Franklee is reachable, you can import the exact jobs that were actually posted by a real cron run on a specific date:

```bash
python3 experimental/job-search-next/scripts/import_live_franklee_run.py \
  --profile student \
  --date 2026-04-13
python3 experimental/job-search-next/scripts/scan_jobs.py \
  --from-raw-leads \
  --source-prefix franklee_live_student_2026-04-13
```

That writes:

- `data/franklee_live_student_2026-04-13.md`
- `data/franklee_live_student_2026-04-13.json`

## Cheaper future path: direct live validator

If the goal is a manual search run without triggering Slack delivery, use the validator directly over SSH:

```bash
python3 experimental/job-search-next/scripts/import_live_franklee_validator.py \
  --profile student \
  --source-label 2026-04-14
python3 experimental/job-search-next/scripts/scan_jobs.py \
  --from-raw-leads \
  --source-prefix franklee_live_direct_student_2026-04-14
```

This path does:

1. call `/root/clawdFrankLee/dist/job_search_prefilter.py --format json` directly
2. import the returned shortlist into `raw_leads.jsonl`
3. avoid posting to Slack or relying on saved daily delivery artifacts

If you want one command instead of two:

```bash
python3 experimental/job-search-next/scripts/run_search_queue.py \
  --profile student \
  --live-franklee-direct \
  --source-label 2026-04-14
```

## ATS heuristic check

The ATS check is heuristic, not a certification.

It currently verifies:

- PDF page count
- extractable text volume via `pdftotext`
- presence of risky Unicode characters that often cause parser issues

Example:

```bash
python3 experimental/job-search-next/scripts/check_ats_readiness.py \
  --scan-generated-resumes \
  --latest-only \
  --report-name ats-readiness-generated-resumes
```

Review override:

```bash
python3 experimental/job-search-next/scripts/promote_to_application.py \
  --lead-id some-review-lead \
  --write-intake \
  --allow-review
```

## ATS / API status

What exists:

- SerpAPI client with key rotation and retry
- Exa search client
- direct official-site sitemap crawling fallback
- public ATS-hosted job-page discovery through domains such as Greenhouse, Lever, Ashby, Personio, Join, and StepStone

What does not exist:

- a generic ATS submission API
- automatic application form submission
- direct apply automation into Workday, Greenhouse, Lever, or similar systems

So the current implementation is a discovery and filtering workflow, not an auto-apply bot.
