# UX Coverage Matrix - resilient-application-mcp

Use this matrix to ensure browser testing covers complete UX/UI flows.

| ID | Requirement Ref | Journey | Type | Expected | Status | Evidence |
|----|------------------|---------|------|----------|--------|----------|
| PUB-01 | R5B, R19 | Landing to prompts | happy | User can open the guided prompt page from the landing navigation; current workflow copy is visible. | pass | `.playwright-cli/page-2026-08-14T19-37-18-625Z.yml` |
| PUB-02 | R5B, R18A | Prompt and public copy | validation | Prompt page states the CV/cover-letter gates and old-workspace diagnosis without stale legacy instructions. | pass | `tests/mcp-http.test.mjs` + Playwright prompt snapshot |
| PUB-03 | R24-R28 | Public unauthenticated documentation routes | auth | Not applicable: the public landing, prompts, diagrams, and health route are intentionally unauthenticated. | N/A | `tests/mcp-http.test.mjs` |
| PUB-04 | R19-R23 | Technical assets and service health | network | Technical page embeds the rendered review diagram and serves canonical PlantUML source; health route responds. | pass | `http://127.0.0.1:5942/technical-flow`, `curl /health` |
| PUB-05 | R19-R23 | Documentation reload/state | persistence | Not applicable: these routes are static explanatory content and do not persist browser state. | N/A | `src/index.ts` |

## Notes
- Set `Status` to `pass`, `fail`, or `N/A`.
- Replace `Evidence` with screenshot/trace paths.
- Do not mark testing complete while required rows remain `todo`.
