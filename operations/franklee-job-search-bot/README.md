# Franklee 15:00 job-search bot

This folder mirrors the production runner and validator for controlled development. Franklee remains the runtime host; this is not the separate experimental queue prototype.

## Runtime contract

- systemd timer/service: `franklee-job-search-slack.timer` / `.service`
- validator: `/root/clawdFrankLee/dist/job_search_prefilter.py`
- runner: `/usr/local/bin/franklee-job-search-slack-runner.py`
- OpenClaw agent: `franklee-job-ranker`
- output: `/root/.openclaw/manual-recovery/`
- OpenClaw Node: `/opt/openclaw-runtime/node-v24.22.1/bin/node`
- model stage: `openai/gpt-6-luna`, medium thinking

## AI ranking boundary

Python remains the authority for discovery, eligibility, applied/recent deduplication, role and location filters, language grouping, and the candidate set. The AI receives only the deterministic 7-student / 9-full-time visible shortlist with public job fields and a bounded description excerpt. URLs and candidate-profile data are excluded.

The dedicated agent has `tools.deny: ["*"]`, `skills: []`, `contextInjection: "never"`, no subagent permissions, and no channel binding. The runner verifies the agent's model and restrictions before each model call. Job-page strings are treated as untrusted data. Responses must match a strict JSON schema and contain exactly the input candidate IDs; a failed or malformed call falls back to the original deterministic report.

`FRANKLEE_AI_RANKING_MODE` supports:

- `off`: no model call
- `shadow` (default): record a private, URL-free ranking sidecar and post the unchanged Python-rendered report
- `rank`: reorder only the same already-validated displayed candidates; eligibility, section membership, and language-first grouping stay Python-controlled

Do not promote to `rank` until shadow comparisons have been reviewed. Never test by manually running the Slack publisher unless an actual channel post is explicitly intended. Use synthetic candidate fixtures and the no-delivery AI canary for model tests.

## Language classification

The Python validator classifies English and German independently from sentence-sized evidence in the structured job description/qualifications (falling back to page text only when structured content is absent). Each language is recorded as `required`, `preferred`, `optional`, `not_required`, `not_mentioned`, `unclear`, or `conflicting`; explicit CEFR levels A1–C2 and `+` variants are retained without inferring a level from phrases such as “good German.”

The public `language_bucket` remains backward-compatible: `main` contains roles without an explicit German requirement, while `german_required` contains explicit requirements plus unclear/conflicting cases for manual review. Each result retains bounded evidence quotes and separate English/German classification objects. Language classification does not change application-open, freshness, location, role, or dedupe gates. Regression coverage is in `tests/test_language_classification.py`.

## Local validation

```bash
python3 -m unittest discover -s operations/franklee-job-search-bot/tests -v
python3 -m py_compile operations/franklee-job-search-bot/src/*.py
```

Production verification must inspect the timer, service, hashes of the three deployed Python files, the dedicated agent policy, and the next real sidecar/manifest. Do not force-post a daily report as a test.
