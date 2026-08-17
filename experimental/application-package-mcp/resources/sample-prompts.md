# Student Application AI Helper Prompts

Use these prompts with your local AI agent. Your private sources remain on your own computer; the MCP provides the workspace kit, safe structure/version advice, and optional selected-text feedback.

Start URL:

```text
https://jobmcp.pmlecuong.com/
```

## 1. Start A New Application Workspace

```text
Set up my Student Application AI Helper workspace and explain the process as a practical career coach.
First fetch the latest workspace and application kit from the MCP.
Run the strict local SOP boot and create a privacy-safe workspace manifest.
Ask the MCP to audit that manifest and tell me whether the workspace is current.
Then show me a short checklist of what I already have, what is missing, and the single best next action.
Keep my CV, job files, evidence, photos, signatures, drafts, and final outputs local.
```

## 2. Diagnose My Old Or Slow Workspace

```text
My Student Application AI Helper folder has been used for a while and the process feels slow.
Do not assume the cause. Run the local workspace diagnosis first and measure file inventory, duplicate/stale material, protected sources, structure drift, and stage timings.
Compare the result with the current ideal workspace structure.
Give me a plain-language report explaining what is slowing the work down and a copy-first migration plan.
Do not delete, overwrite, move, or migrate anything until I approve the plan.
```

## 3. Prepare My Evidence Before Drafting

```text
Help me prepare an honest application profile before drafting.
Ask for my target role and job description or URL. Ask me to provide my current CV as PDF, DOCX, or HTML; keep the original in candidate/source. If I do not have an old resume, ask me for a LinkedIn export, profile notes, or structured education/work history so you can build the first CV source locally.
Ask whether I am doing a Bachelor, Master, Ausbildung/job training, school program, or another path, and use that answer in my education section.
For each company in my experience, list the employer and ask me to write at least 10 authentic achievement/work bullets myself (15 is even better). Remind me not to use AI to invent these bullets.
Invite supporting documents and real writing samples, explain what they improve, and record if I choose a generic voice instead. Recommend human-written material from before ChatGPT became common, such as old emails, IELTS writing, user stories, PRDs, BRDs, reports, or notes I wrote myself.
Ask whether I want to provide a CV photo. Ask for a signature image for the cover letter, but continue if I do not have one.
Ask which cover-letter enclosures I can attach. CV/Lebenslauf is mandatory. Ask whether I can provide a Bachelor diploma/transcript and a previous-employer reference/employer certificate. If I only have the CV, warn me that fewer than two attachments makes the application weaker, then do not list missing documents.
```

## 4. Create A Tailored Editable CV

```text
Create a tailored CV for jobs/<job-folder> using only verified local evidence.
Preserve my original CV source and inspect its visual structure before generating an editable HTML CV.
Use the English resume template by default unless I ask for a German Lebenslauf format or the job clearly needs one.
Use four or five of my verified bullets per employer that best match this job description. Do not add skills or achievements I cannot prove.
Put unsupported JD requirements into a gap report, not into my CV.
Run the ATS resume-to-job-description check after every meaningful CV edit. Show me the score, matched keywords, suggested missing keywords, and what I must confirm before anything is added.
Show me the HTML CV, any PDF derivative, and a clear quality report. Run the one mandatory CV review loop and tell me exactly what is still weak before I decide to proceed.
```

## 5. Check ATS Match Between My Resume And A Job Description

```text
Please run the MCP ATS check for my current resume/CV and this job description.
Extract the CV text locally and send only the extracted CV text plus the job description text to the MCP.
Return the ATS score, matched keywords, suggested missing keywords, and the exact user confirmations needed before any missing keyword can be added.
Do not add unsupported skills, tools, degrees, language levels, domain experience, or achievements just to improve the score.
If I confirm a suggested keyword is true, revise the CV locally and rerun the ATS check.
```

## 6. Create A Cover Letter With The Three-Loop Gate

```text
Create a one-page cover letter for jobs/<job-folder> from my verified local evidence and writing voice.
Use my signature if I provided one; otherwise continue and record that no signature is available.
Use only the enclosure documents I confirmed. Always include my CV/Lebenslauf; include diploma/transcript or employer reference only if I can attach them.
Run three separate review and revision loops. In every loop, show the current draft, what changed, and any remaining weak or unsupported point.
For any private writing check, submit only the selected cover-letter text, never my whole CV, workspace, or job folder.
Do not call the cover letter ready until the local SOP verifies three distinct current review records and creates a release receipt.
```

## 7. Use My Current CV Without Extra Curation

```text
I want to proceed using my current CV instead of writing a new employer bullet inventory.
Record that I am choosing this shortcut and explain the likely tradeoff for role matching.
Still use only verified information, tailor the ordering and emphasis honestly, run the required CV review and ATS check, and remind me later that a personal bullet inventory would improve future applications.
```

## 8. Create Interview Prep For This Role

```text
Please prepare interview prep for jobs/<job-folder>.
First ask me for the interview date/time, format, duration, location or meeting link, interviewer names or email signatures, expected language, and my biggest concerns.
Ask me for 3 to 5 actual past incident stories I personally experienced and can discuss in STAR format.
Also ask me what I do outside work or study, how I recharge, and what values matter to me, so the culture-fit answer does not sound like a workaholic script.
Use my local CV, cover letter, job description, evidence, communication log, and writing voice. Do not invent hobbies, interviewer facts, achievements, STAR stories, STAR results, language levels, visa details, or metrics. If my local profile has no actual incident stories, ask me for them instead of making them up from CV bullets.
If my profile is too thin, create interview-prep-questions.md and ask me to fill it before polishing the final prep.
After creating the prep, run two MCP writing review loops on interview-prep-review-input-loop-1.json and interview-prep-review-input-loop-2.json, save interview-prep-review-result-loop-1.json and interview-prep-review-result-loop-2.json, and record the review/finalize receipt through the local SOP. If you edit the prep afterward, repeat both review loops.
Send only final spoken answer text to the MCP checker. Do not send coaching notes, missing-info questions, raw job requirements, keyword maps, or planning scaffolding.
```

## 9. General Writing Review

```text
Please review this writing with the MCP checker.
Mode: academic.
Review loops: 2.

Use application-kit/contracts/writing-review-contract.md and application-kit/contracts/mcp-review-payload-contract.md.
If the text is long, extract and chunk it locally with writing_review_loop.py.
Send only selected final reader-facing text chunks to the MCP.
Do not invent citations, sources, data, methods, personal stories, or claims.
Give me a practical revision plan and rerun the selected number of loops, never more than three. If any loop returns medium or high, revise the real local document before the next loop.
```

## 10. Skip Interview Prep

```text
For this job, skip interview prep for now.
Record that I skipped it, but do not block the CV or cover-letter package.
```

## 11. Review Selected Text Only

```text
Review this selected text with the MCP writing checker.
Mode: application.
Tell me what is generic, unsupported, overly polished, unclear, or weak for a recruiter. Return a practical revision plan first.
Use final reader-facing text only. Do not send scaffolding, prompt notes, hidden comments, keyword maps, or internal planning text.
Do not treat the result as proof of authorship or as a way to bypass AI detection. Revise the local file without inventing facts.
```

## 12. Check For A Safe Kit Update

```text
Run the privacy-safe workspace manifest audit before we start work.
If the kit is current, continue without changing files.
If an update is available, show me exactly which generic kit files would change. Do not overwrite my candidate sources, profile, voice samples, job folders, drafts, outputs, photos, signatures, or SOP history without my approval.
```

## Simple Rule

```text
My application evidence stays local.
The MCP sees only a privacy-safe folder manifest, selected text I deliberately select for writing review, or extracted CV/JD text for ATS matching.
The local SOP—not a chat promise—records whether CV, ATS, cover-letter, interview-prep, and writing gates are complete.
```
