# MCP Review Payload Contract

This contract applies to every selected-text MCP writing/human-fit review: CV, resume, cover letter, interview prep, academic writing, work writing, blog/social writing, and freestyle paragraphs.

It does not define the ATS checker payload. ATS checking is a separate JD-to-CV fit workflow; use `ats-checker-contract.md` for that flow.

The MCP checker must receive final reader-facing text only.

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

The MCP result is not an authorship verdict and is not a detector-bypass guarantee. It is a quality gate for generic rhythm, unsupported claims, missing evidence texture, and artificial structure. The local agent must still preserve facts, sources, and user intent.
