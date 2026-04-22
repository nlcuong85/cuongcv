# Live Franklee Replay Report

## Source

- Live host: `root@100.124.166.95`
- Cron job: `74e37d6d-099b-4ef8-84b1-53a5cbc06b43`
- Profile: `student`
- Run date: `2026-04-13`
- Imported summary: `data/franklee_live_student_2026-04-13.md`
- Parsed jobs JSON: `data/franklee_live_student_2026-04-13.json`

## New workflow result

- Jobs imported from the live Franklee run: `3`
- Experimental tracker result:
  - `keep=1`
  - `review=2`
  - `reject=0`
- Tracker validation: passed

## Per-job outcome

- `keep`:
  - Bosch Group | Werkstudent Cleanroom Process & Quality (w/m/div.)
  - predicted role: `quality_compliance_ops`
  - fit score: `93`
  - prototype draft intake written:
    - `promotions/intakes/bosch-group-werkstudent-cleanroom-process-quality-w-m-div.json`

- `review`:
  - Robert Bosch GmbH | Werkstudent im Support der Fertigungssteuerung einer Halbleiterfertigung (w/m/div.)
  - predicted role: `requirements_process`
  - fit score: `43`
  - not promoted automatically

- `review`:
  - Robert Bosch Manufacturing Solutions GmbH | Praktikum im Projektmanagement Sondermaschinenbau
  - predicted role: `requirements_process`
  - fit score: `69`
  - not promoted automatically

## ATS heuristic result

- Report: `data/ats-readiness-generated-resumes.md`
- Generated resume PDFs tested: `43`
- Verdicts:
  - `pass=0`
  - `warn=43`
  - `fail=0`

Interpretation:

- All tested resumes had extractable text and stayed within the configured page limit.
- All warnings came from detected Unicode-risk characters, not from non-extractable PDFs or overlong resumes.
- This means the current generated resumes look parseable, but they are not yet strong enough to claim universal ATS safety.
