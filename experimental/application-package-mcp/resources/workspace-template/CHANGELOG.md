# Changelog

## 2026-11-14 Safe agent-file updates

- Workspace audits and the local SOP now hash only the mandatory Job MCP policy block in `AGENTS.md`, `CLAUDE.md`, `COPILOT.md`, and `GEMINI.md`.
- Candidate-owned instructions outside that block survive kit updates and do not create false managed-file drift. Changes to the mandatory block still fail the audit.

## 2026-11-14 CV writing-review routing

- Application writing packets now identify CV/resume versus cover letter, so CVs are not judged by cover-letter story and paragraph rules.
- The one-loop CV and three-loop cover-letter SOP policies remain unchanged.

## 2026-11-14 SOP baseline recovery

- Strict boot now accepts normal candidate CV, JD, profile, and generated-output changes instead of freezing the workspace after first setup.
- Managed-file updates still require a current MCP workspace audit before strict boot refreshes the baseline.
- The task handoff now points to the supported employment-type question command.

## First Setup

- Created the student application digital-twin workspace.
- Added `profile/`, `memory/`, `scripts/`, `jobs/`, `outputs/`, and `application-kit/`.
- Keep this file updated when profile facts, evidence, memory, scripts, or structure change.

## Writing-sample consent update

- Added an optional, consent-aware writing-sample invitation for authentic self-written materials.
- The local SOP now records whether a reminder is due, deferred, declined, or the candidate says the current material is enough.
- An `enough` or `declined` decision stops future unsolicited reminders unless the candidate explicitly reopens the topic.
- Added the same rule to `CLAUDE.md` and `voice/writing-samples/README.md`.

## ATS public checker update

- Added the public ATS resume/job-description checker to the normal application flow.
- The local agent must run ATS after meaningful CV edits, report the score, and show matched and suggested keywords.
- Suggested keywords are human-in-the-loop only: the agent must ask before adding skills, tools, degrees, language levels, or domain experience not already proven locally.
