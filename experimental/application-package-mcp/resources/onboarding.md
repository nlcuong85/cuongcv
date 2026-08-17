# Student Application AI Helper Onboarding

Use this service to help a student build a local AI writing workspace.

## Automatic Workspace Update Rule

Whenever a local AI agent connects to this MCP, it must treat the first contact as a workspace setup/update checkpoint. The student should not need to paste a special setup prompt every time.

Before drafting, editing, reviewing, or finalizing application documents, the local agent must:

1. Fetch or refresh `get_workspace_template` when starter files are missing.
2. Fetch `get_application_kit_bundle` and update MCP-managed files only.
3. Preserve all student-owned content: profile, memory, voice samples, candidate files, jobs, applications, outputs, photos, signatures, and source documents.
4. Run `scripts/workspace_audit.py` locally.
5. Send only the privacy-safe `.mcp/workspace-manifest.json` to `audit_workspace_manifest`.
6. Run `python3 scripts/application_sop.py --root . boot --strict`.
7. For every CV/JD edit, run the ATS check and record it before `finalize-cv`.

Every major MCP response also includes a machine-readable `workspace_update_required` block so compatible local agents can perform this automatically.

The current workspace follows the digital-twin structure:

```text
student-application-workspace/
  AGENTS.md
  CHANGELOG.md
  MIGRATION.md
  COPILOT.md
  CLAUDE.md
  GEMINI.md
  context_pack.md
  copilot_context.md
  copilot_quick_context.md
  profile/
    master_profile.json
    evidence_library.json
    student-profile-context.md
    voice_dna.md
    claim_boundaries.md
    writing_mode_framework.md
  memory/
    skill_memory.md
    decisions.md
    interaction_tracker.md
    benchmark-results.md
    legacy/
  scripts/
    migrate_legacy_workspace.py
    audit_profile.py
    audit_application.py
    audit_research_markdown.py
    build_context_pack.py
    build_copilot_pack.py
  candidate/
  jobs/
  outputs/
  application-kit/
```

## Resilient Application Mode

For CV and cover-letter work, use the local `application_sop.py` from the public application kit. It is a client-side hard gate: strict boot checks local workspace drift, work is recorded locally, and final documents need a local release receipt. The MCP does not read the workspace; it receives selected text or a privacy-safe structure manifest only.

Ask the student for their target role/JD, current CV, education track, preferred CV language/format, optional supporting/voice material, photo decision, optional signature, and confirmed cover-letter enclosures. The CV source is mandatory: if they do not have an old resume, ask them to provide the best available CV draft, profile notes, LinkedIn export, or structured education/work history so the local agent can build the first CV source locally. Also ask whether they are currently doing a Bachelor, Master, Ausbildung/job training, school program, or another path; use that answer to populate the education section accurately. Recommend that they write 10 authentic bullets per employer (15 is better); use four or five verified bullets per employer for a tailored CV. A CV gets one review loop; a cover letter gets three distinct review loops; interview prep gets two review loops.

For enclosures, the CV/Lebenslauf is mandatory. Specifically ask whether the student can provide a Bachelor degree diploma or transcript/certificate, and whether they can provide a reference letter or employer certificate from a previous employer. Include only documents the student confirms they can attach. If the student only has the CV, warn plainly that the application package is weaker with fewer than two attachments and recommend adding at least one proof document; if they cannot provide it, do not mention it in the enclosure list.

For CV format, ask first whether the student already has a preferred PDF, DOCX, HTML, screenshot, or template. If yes, convert/extract it locally, rebuild it as editable HTML, and use browser/Playwright screenshots in a loop until the generated HTML matches the reference structure before calling it passed. If the student has no preferred format, use the bundled English resume fallback in `application-kit/templates/cv_english_modern.html` by default. Use `application-kit/templates/cv_german_rounded.html` only when the student wants a German Lebenslauf format or the target market clearly needs it.

For optional voice material, offer authentic self-written examples such as past user stories, emails/letters, IELTS writing, work descriptions, personal statements, reports, notes, or previous applications. First query `voice-intake-status` through the local SOP. If the student says existing material is enough, record `record-voice-intake --status enough` and never prompt them again unless they explicitly reopen the topic. A deferred reminder is allowed only when they request one, and should be set no more frequently than every 45 days.

For interview preparation, offer it after a CV or cover-letter package is started or completed. It is optional and should not block document release. If the student accepts, ask for interview date/time, format, duration, location or meeting link, interviewer names/titles/email signatures, expected language, concerns, and 3 to 5 actual past incident stories they can discuss in STAR format. Also ask the culture-fit question directly: what they do outside work or study, how they recharge, and what values matter to them. Use `application-kit/contracts/interview-prep-contract.md` and run `application-kit/scripts/build_interview_prep.py`. Then run two MCP writing review loops on `interview-prep-review-input-loop-1.json` and `interview-prep-review-input-loop-2.json`, save `interview-prep-review-result-loop-1.json` and `interview-prep-review-result-loop-2.json`, and record the local SOP receipt. If actual incidents are missing, create `interview-prep-questions.md` and ask the student to write or confirm real stories instead of inventing from CV bullets.

## Existing Student Workspaces

Some students may already have the older structure:

```text
candidate/
jobs/
outputs/
application-kit/
```

When an old workspace is detected:

1. Fetch the latest workspace template from the MCP server.
2. Add missing digital-twin files and folders.
3. Do not delete, rename, or overwrite old student files.
4. Run:

```bash
python3 scripts/migrate_legacy_workspace.py .
```

5. Preserve old `candidate/` data under `memory/legacy/` when it cannot be safely mapped.
6. Treat `profile/` and `memory/` as source of truth only after the student or local agent reviews migrated facts.

## Allowed Service Calls

Use the service for:

- setup instructions
- starter workspace files
- current local kit files
- simple prompt examples
- selected writing checks

Do not upload full CV folders, source documents, identity documents, passwords, bank records, or secrets.

## Local Workflow

1. Fetch `get_workspace_template`.
2. Fetch `get_application_kit_bundle`.
3. Create or update the local digital-twin structure.
4. If old files exist, run the migration script.
5. Read `AGENTS.md`, `profile/`, and `memory/`.
6. Read the target job or writing goal under `jobs/<target>/`.
7. Draft locally.
8. Render local application outputs when needed.
9. Offer optional interview prep once for the job. If accepted, create `interview-prep.md`, `interview-prep-questions.md`, `interview-prep-review-input-loop-1.json`, `interview-prep-review-input-loop-2.json`, `interview-prep-review-result-loop-1.json`, `interview-prep-review-result-loop-2.json`, and `interview-prep-manifest.json` locally.
10. Send only selected writing text to the checker when the student asks.
11. Revise locally and save outputs under `outputs/<target>/`.

For general writing review, use `application-kit/contracts/writing-review-contract.md`. Ask the student to choose 1, 2, or 3 loops and a mode (`application`, `academic`, `blog`, `work`, `social`, or `general`). Extract and chunk locally with `application-kit/scripts/writing_review_loop.py`, send only selected chunk input JSON files to the MCP checker, and summarize the returned results locally. Never run more than 3 loops and never invent academic citations, methods, data, or findings.
12. Ask the student to review before final use.

## Checker Modes

- `application`: cover letters, CV overviews, recruiter emails
- `academic`: thesis sections, literature reviews, abstracts, article paragraphs
- `blog`: reflective or public articles
- `work`: team updates, user stories, meeting notes
- `social`: LinkedIn or short public posts
- `general`: anything else

## Writing Rules

- Do not invent facts, dates, degrees, tools, results, or language levels.
- Do not use another person's story or tone as if it belongs to the student.
- Do not add fake errors to look human.
- Do not treat a detector score as proof.
- Improve writing by making it clearer, more specific, better supported, and more useful for the reader.
- Keep private checker logic on the server. The local folder should not contain `audit_human_fit.py` or private AI-checker heuristics.
