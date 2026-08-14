# Local Retry Policy

The local AI agent must follow this retry loop.

## Required Loop

1. Read the latest MCP application kit.
2. Read local candidate and job files.
3. Write `cover-letter-draft.json`.
4. Run `local_application_generator.py`.
5. Read `validation.md`.
6. If validation fails, revise only `cover-letter-draft.json` and rerun.
7. Stop after three failed retries and report the exact validation errors.

## What Must Not Be Changed During Retry

- LaTeX template
- page margins
- font size
- vertical spacing
- sender/recipient/date/subject order
- paragraph order
- enclosure structure

## Preferred Fixes

If the cover letter is too long:

1. remove filler
2. shorten motivation paragraph
3. shorten the second evidence paragraph
4. make the opening more direct
5. keep closing practical

If tone is wrong:

1. reread `candidate/tone.md`
2. reread local writing samples
3. replace generic claims with evidence-backed concrete language
4. remove internal workspace language and overly even model-answer cadence
5. keep the business-letter structure unchanged
6. send only the selected cover-letter text to the remote writing checker when the student wants deeper feedback

If skills are wrong:

1. reread `candidate/profile.json`
2. reread `candidate/evidence.md`
3. remove JD-only skills
4. keep exactly 7 core plus up to 7 adaptive skills when supported
