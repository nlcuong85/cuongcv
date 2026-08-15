# Interview Prep Contract

This contract is mandatory when the student chooses to create interview preparation for a job.

Interview prep is optional. The local agent must offer it after a CV or cover letter package is started or completed:

```text
Would you like me to prepare an interview-prep file for this role as well?
```

If the student declines, record the skip in the job notes or local SOP decision memory and continue. Do not block CV or cover-letter work.

If the student accepts, create:

- `interview-prep.md`
- `interview-prep-questions.md`
- `interview-prep-review-input.json`
- `interview-prep-review-input-loop-1.json`
- `interview-prep-review-input-loop-2.json`
- `interview-prep-review-result-loop-1.json` after the first MCP review call
- `interview-prep-review-result-loop-2.json` after the second MCP review call
- `interview-prep-manifest.json`

The prep must be based on local files only: job description, CV/source profile, cover letter, evidence library, writing samples, notes, and communication log. The MCP checker may be used only for selected text if the student explicitly asks.

## Required Intake Questions

Ask for missing information before finalizing the prep:

- interview date, time, duration, format, location, or meeting link
- interviewer names, roles, email signatures, recruiter messages, or calendar invite text
- expected language: English, German, or mixed
- target concerns: German level, visa/work authorization, availability, confidence, salary, relocation, technical/domain gaps
- 3 to 5 strongest work examples the student is comfortable discussing
- 3 to 5 actual incident stories from the student's past, written or confirmed by the student, with situation, task, action, result, and lesson where possible
- one non-work / outside-study answer: hobbies, routines, values, personality, and how the student recharges

STAR stories are a hard gate. If the local profile or interview intake does not contain actual incident stories, the agent must ask the student for them. Generic CV responsibilities, skill lists, cover-letter claims, and job requirements are not enough to create STAR stories.

If the student only provided a CV and job description, generate a useful first draft but mark it as `needs_user_clarification` and create `interview-prep-questions.md`.

The final prep must not read like a loose questionnaire. Open questions belong mainly in `interview-prep-questions.md`. The main `interview-prep.md` should be a Mercedes/Acteno-grade coaching document with role interpretation, likely-question rationale, answer scripts, weakness strategy, culture-fit coaching, screening logic, and clear incomplete markers where evidence is missing.

## MCP Review Gate

Read `mcp-review-payload-contract.md` before this gate. The review inputs must contain final spoken answer text only. Do not send the whole prep document, question bank, missing-info prompts, role-analysis notes, raw requirements, or coaching checklists as writing-review text.

Interview prep requires two MCP writing review loops before the local agent may call it ready for practice.

The local builder must create two selected review packets:

- loop 1: 60-second introduction, strong answer scripts, strengths/weaknesses, and culture-fit answer material
- loop 2: company/team read, role needs, positioning, likely-question rationale, STAR boundary, screening logic, and bottom line

The local agent must then call:

```bash
node application-kit/scripts/mcp_check_client.mjs review applications/<job>/interview-prep/interview-prep-review-input-loop-1.json applications/<job>/interview-prep/interview-prep-review-result-loop-1.json
node application-kit/scripts/mcp_check_client.mjs review applications/<job>/interview-prep/interview-prep-review-input-loop-2.json applications/<job>/interview-prep/interview-prep-review-result-loop-2.json
python3 application-kit/scripts/application_sop.py --root . review-interview-prep --loop 1 --artifact applications/<job>/interview-prep/interview-prep.md --result applications/<job>/interview-prep/interview-prep-review-result-loop-1.json
python3 application-kit/scripts/application_sop.py --root . review-interview-prep --loop 2 --artifact applications/<job>/interview-prep/interview-prep.md --result applications/<job>/interview-prep/interview-prep-review-result-loop-2.json
python3 application-kit/scripts/application_sop.py --root . finalize-interview-prep --artifact applications/<job>/interview-prep/interview-prep.md
```

If either review returns `medium` or `high`, revise the actual `interview-prep.md`, regenerate both review inputs from the revised prep, and rerun the MCP checks. If the prep changes after the reviews, run both review loops again. Do not send the full workspace, full CV file, photos, signatures, or private writing archive to the MCP. Send only the selected final-answer review inputs.

## Mandatory Structure

`interview-prep.md` must contain:

1. Process Overview
2. What The Company / Team Seems To Do
3. What The Role Actually Needs
4. Interviewer / Recruiter Read
5. Best Positioning
6. 60-Second Introduction
7. Likely Questions
8. Strong Answer Scripts
9. Strengths And Weaknesses
10. STAR Story Bank
11. Culture Fit: Who Are You Outside Work?
12. Questions To Ask Them
13. Things To Avoid
14. Practical Logistics
15. 24-Hour Checklist
16. What They Are Likely Screening For
17. Bottom Line
18. Missing Information To Ask The Student

Likely questions must include a short reason why each question is likely. Answer scripts must be usable spoken examples, not only abstract advice.

## Weakness Answer Rules

Prefer honest, low-risk, growth-oriented weaknesses:

- over-structuring before sharing an early draft
- balancing depth with speed
- needing more domain-specific knowledge while showing a concrete learning plan
- German professional fluency still improving, only when relevant

Reject or rewrite risky answers:

- `I work too hard`
- `I am a perfectionist`
- `I have no weakness`
- `I am bad at communication`
- `I do not handle stress well`
- any weakness that makes the student sound unreliable, careless, dishonest, or hard to work with

## Culture-Fit Rule

Germany-focused interviews often check whether the candidate is balanced, self-aware, and healthy to work with. Always include a section for questions such as:

- What do you do outside work or study?
- How do you recharge?
- How would teammates describe you?
- How do you balance ambition with health and normal life?
- What values matter to you at work?

The answer must not sound like a workaholic performance script. It should show ambition, but also normal life, reflection, and team fit.

## Evidence Rules

- Do not invent interviewer facts.
- Separate verified facts from interpretation.
- Do not invent hobbies, values, STAR incidents, STAR results, achievements, metrics, visa facts, or language levels.
- Build STAR stories only from explicit user-provided incidents or clearly stored profile incident records. If the source only says a skill, responsibility, achievement claim, or cover-letter paragraph without a concrete incident, ask the student for a real story instead of turning it into a fake STAR answer.
- If evidence is missing, ask the user in `interview-prep-questions.md`.
- If the answer is a draft assumption, label it clearly.
- Do not use another candidate's Mercedes/Acteno examples as if they belong to this student.
