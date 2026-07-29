# Franklee 15:00 Job-Search Bot Governance

Date: 2026-06-29

## Current Contract

The Franklee 15:00 Europe/Berlin Germany job-search bot is a deterministic systemd workflow on the Franklee host. It is not currently maintained as an OpenClaw cron or agentTurn workflow.

Production surfaces:

- SSH target: `root@100.124.166.95`
- Workspace: `/root/clawdFrankLee`
- OpenClaw state: `/root/.openclaw`
- Timer: `/etc/systemd/system/franklee-job-search-slack.timer`
- Service: `/etc/systemd/system/franklee-job-search-slack.service`
- Runner: `/usr/local/bin/franklee-job-search-slack-runner.py`
- Validator: `/root/clawdFrankLee/dist/job_search_prefilter.py --combined-1500 --max-age-days 20`
- Output directory: `/root/.openclaw/manual-recovery/`
- Slack channel: `C0AN1ENTLMQ`

The old OpenClaw cron id `74e37d6d-099b-4ef8-84b1-53a5cbc06b43` is historical. Do not re-enable it without a deliberate migration plan.

## Health Check

Run these read-only checks:

```bash
ssh root@100.124.166.95 'systemctl list-timers franklee-job-search-slack.timer --all --no-pager'
ssh root@100.124.166.95 'systemctl status franklee-job-search-slack.service --no-pager'
ssh root@100.124.166.95 'journalctl -u franklee-job-search-slack.service --since "<date> 14:55" --until "<date> 16:15" --no-pager'
ssh root@100.124.166.95 'ls -lh /root/.openclaw/manual-recovery/job-search-<date>-1500*'
```

A healthy day means:

- timer fired around 15:00 Europe/Berlin
- service exited `0/SUCCESS`
- `/root/.openclaw/manual-recovery/job-search-YYYY-MM-DD-1500.md` exists
- `/root/.openclaw/manual-recovery/job-search-YYYY-MM-DD-1500.delivery.json` has `status: posted`
- Slack `message_ts` values are present

The 2026-06-29 verification showed successful runs from 2026-06-22 through 2026-06-29, with daily reports and delivery manifests posted to Slack.

## Runtime Rules

- Scheduler success is not delivery success. Verify systemd, saved report, delivery manifest, and Slack timestamps independently.
- The runner must remain idempotent. It skips reposting when the delivery manifest already says `posted`; use `FRANKLEE_FORCE_REPOST=1` only for intentional reposts.
- Slack posts must stay chunked conservatively and retry transient rate limit or network failures.
- Validator failures from one candidate URL must be row-level `fetch_failed`, not whole-run failures. Keep handling `http.client.IncompleteRead`.
- The visible report has exactly two sections:
  - `Section 1` for working student / internship / part-time
  - `Section 2` for full-time
- Do not restore a German-heavy `Section 3`.
- Jobs with missing dates are allowed and render as `Posted: Date not found`; stale rejection applies only when a date exists.

## Repo Surfaces To Keep In Sync

When this contract changes, update all of these in the same work session:

- `AGENTS.md`
- `experimental/job-search-next/docs/franklee-queue-integration.md`
- `experimental/job-search-next/README.md`
- `/Users/pmlecuong/.codex/skills/job-search-cuong/SKILL.md`
- durable Codex memory ad-hoc note under `/Users/pmlecuong/.codex/memories/extensions/ad_hoc/notes/`
