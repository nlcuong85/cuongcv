# Student Application AI Helper Onboarding

Use this service to help a student build a local AI writing workspace.

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

Ask the student for their target role/JD, current CV, preferred CV format, optional supporting/voice material, photo decision, and optional signature. Recommend that they write 10 authentic bullets per employer (15 is better); use four or five verified bullets per employer for a tailored CV. A CV gets one review loop; a cover letter gets three distinct review loops.

For CV format, ask first whether the student already has a preferred PDF, DOCX, HTML, screenshot, or template. If yes, convert/extract it locally, rebuild it as editable HTML, and use browser/Playwright screenshots in a loop until the generated HTML matches the reference structure before calling it passed. If the student has no preferred format, suggest the bundled German rounded Lebenslauf fallback in `application-kit/templates/cv_german_rounded.html`.

For optional voice material, offer authentic self-written examples such as past user stories, emails/letters, IELTS writing, work descriptions, personal statements, reports, notes, or previous applications. First query `voice-intake-status` through the local SOP. If the student says existing material is enough, record `record-voice-intake --status enough` and never prompt them again unless they explicitly reopen the topic. A deferred reminder is allowed only when they request one, and should be set no more frequently than every 45 days.

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
9. Send only selected writing text to the checker when the student asks.
10. Revise locally and save outputs under `outputs/<target>/`.
11. Ask the student to review before final use.

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
