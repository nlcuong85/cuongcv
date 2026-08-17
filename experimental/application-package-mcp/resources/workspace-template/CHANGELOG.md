# Changelog

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
