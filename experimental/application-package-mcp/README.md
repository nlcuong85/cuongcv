# Student Application AI Helper

Remote MCP service and human-facing website for student writing support.

The public website explains the workflow in plain language. The MCP endpoint gives local AI agents starter files, a lightweight application kit, prompt examples, and private selected-text writing checks.

## Public URLs

```text
https://jobmcp.pmlecuong.com/
https://jobmcp.pmlecuong.com/cv-template/english
https://jobmcp.pmlecuong.com/cv-template/german
https://jobmcp.pmlecuong.com/sample-prompts
https://jobmcp.pmlecuong.com/privacy
https://jobmcp.pmlecuong.com/mcp
https://jobmcp.pmlecuong.com/health
```

Use the root URL (`https://jobmcp.pmlecuong.com/`) in user-facing setup prompts. Keep `/mcp` as the technical Streamable HTTP transport endpoint for compatible AI clients and smoke tests.

## Privacy Model

Student files stay on the student laptop:

- CV files
- profile notes
- job posts
- writing samples
- drafts
- PDFs
- final documents

The server processes selected writing text only when the student asks for a check. The checker returns feedback and revision guidance. Raw submitted text is not stored by the service.

Private checker rules, voice DNA, AI-checker guardrails, and audit scripts are not included in the downloadable student kit.

## MCP Tools

- `health`
- `get_onboarding_instructions`
- `get_client_skill`
- `get_workspace_template`
- `get_application_kit_manifest`
- `get_application_kit_bundle`
- `audit_workspace_manifest`
- `get_sample_prompts`
- `check_writing_human_fit`
- `suggest_writing_revision`

## Local Kit Role

The local kit renders and validates basic application outputs:

```text
cover-letter-draft.json
cover-letter.tex
cover-letter-<candidate-name>-<job-title>-<timestamp>.pdf
cover-letter.md
cv-tailored.md
interview-prep.md
interview-prep-questions.md
validation.md
manifest.json
```

Advanced tone, reader, convention, and AI-like-pattern feedback is handled by the remote checker tools for selected text only.

The local kit includes workflow gates, optional interview prep, general writing review, and a public client, but **not** checker logic: one recorded CV review loop, three distinct cover-letter review loops, and two interview-prep review loops are required before an agent describes those artifacts as ready. General writing can use one, two, or three review loops. Interview prep is optional; if accepted, the local agent asks for interview details, culture-fit/outside-work context, concerns, and real examples before creating `interview-prep.md`, then sends only selected prep sections to the MCP checker. The public `audit_workspace_manifest` tool receives only a structure/version manifest; it cannot read a student's disk or document content.

## Development

```bash
npm ci
npm test
python3 samples/local-kit-regression/run_regression.py
npm run start:http
```

Local endpoint:

```text
http://127.0.0.1:5920/mcp
```

## Release And Maintenance Lessons

Version tracking is part of the product. Keep the visible landing footer aligned with:

- service version in `package.json`, `package-lock.json`, and `src/index.ts`
- workspace kit version in `src/index.ts`, `resources/application-kit/manifest.json`, and `resources/application-kit/scripts/workspace_audit.py`

Before production deploy, run:

```bash
npm test
python3 samples/local-kit-regression/run_regression.py
env MCP_URL=https://jobmcp.pmlecuong.com/mcp npm run smoke:remote
```

Notes for future agents:

- `npm run smoke:remote` defaults to `http://127.0.0.1:5920/mcp`; set `MCP_URL` explicitly for production.
- The local-kit regression is a real release gate. If it fails, inspect the generated `validation.md` files before loosening rules.
- Do not hardcode application documents in templates when they depend on user confirmation. Use placeholders rendered from validated draft JSON.
- Validate three separate surfaces after deployment: internal `/health`, public `/health`, and the public landing/footer text.
- Production should stay a Git checkout of the latest pushed commit. Use a rollback tag before pulling and rebuild/restart from the canonical checkout.

## Franklee Deployment

Remote path:

```text
/DATA/AppData/application-package-mcp
```

Container:

```text
application-package-mcp
```
