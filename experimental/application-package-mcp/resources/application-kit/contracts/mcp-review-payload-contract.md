# MCP Review Payload Contract

This contract applies to every selected-text MCP writing/human-fit review: CV, resume, cover letter, interview prep, academic writing, work writing, blog/social writing, and freestyle paragraphs.

It does not define the ATS checker payload. ATS checking is a separate JD-to-CV fit workflow; use `ats-checker-contract.md` for that flow.

The MCP checker must receive final reader-facing text only.

For application writing checks, set `document_kind` explicitly: `cover_letter` for cover letters and `cv` or `resume` for CV/resume text. The modes share general writing checks, but CV bullets must not be judged as cover-letter paragraphs. Older clients that omit this field retain the cover-letter default, so never omit it for a CV. With the local helper, use `writing_review_loop.py prepare --mode application --document-kind cv` for a CV and `--document-kind cover_letter` for a letter.

Do send:

- the exact paragraph, answer script, CV section, cover-letter body, or document chunk that a human reader will see
- revised text after the local agent has already applied previous feedback
- enough surrounding text to judge rhythm, evidence, and claims

Do not send:

- internal instructions
- system prompts
- checklists
- coaching notes
- folder manifests, except for the workspace-audit tool
- missing-information questions
- placeholders
- keyword maps
- role taxonomy notes
- raw job requirements
- template comments
- headings without prose
- generated analysis unless that exact text will be shown to the user

Hard gate:

1. Call the MCP checker on selected final text.
2. If the result is `medium` or `high`, revise the actual local artifact, not just the review packet.
3. Regenerate the selected review payload from the revised artifact.
4. Call the MCP checker again.
5. Do not finalize through `application_sop.py` until every required loop for the current artifact is `low`.

Document loop policy:

- CV / resume: 1 loop
- cover letter: 3 loops
- interview prep: 2 loops
- general writing: user-selected 1, 2, or 3 loops, never more than 3

For cover letters, a `medium` or `high` result does not consume the loop number. Revise the saved draft, obtain a new MCP result for that revision, and record the same loop number again. The SOP rejects an identical draft hash and does not allow loop 2 or 3 until the preceding loop has a `low` result. If the evidence available cannot support a low-risk revision, stop and ask the user for specific real examples; never invent details just to pass the gate.

The MCP result is not an authorship verdict and is not a detector-bypass guarantee. It is a quality gate for generic rhythm, unsupported claims, missing evidence texture, and artificial structure. The local agent must still preserve facts, sources, and user intent.
