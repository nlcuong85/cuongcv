# Student Application AI Helper

Remote MCP service and human-facing website for student writing support.

The public website explains the workflow in plain language. The MCP endpoint gives local AI agents starter files, a lightweight application kit, prompt examples, and private selected-text writing checks.

## Public URLs

```text
https://jobmcp.pmlecuong.com/
https://jobmcp.pmlecuong.com/sample-prompts
https://jobmcp.pmlecuong.com/privacy
https://jobmcp.pmlecuong.com/mcp
https://jobmcp.pmlecuong.com/health
```

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
validation.md
manifest.json
```

Advanced tone, reader, convention, and AI-like-pattern feedback is handled by the remote checker tools for selected text only.

The local kit includes workflow gates and a public client, but **not** checker logic: one recorded CV review loop and three distinct cover-letter review loops are required before an agent describes an application as ready. The public `audit_workspace_manifest` tool receives only a structure/version manifest; it cannot read a student's disk or document content.

## Development

```bash
npm install
npm test
npm run start:http
```

Local endpoint:

```text
http://127.0.0.1:5920/mcp
```

## Franklee Deployment

Remote path:

```text
/DATA/AppData/application-package-mcp
```

Container:

```text
application-package-mcp
```
