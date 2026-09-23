# Student Application MCP Maintenance Notes

Durable lessons from the August 2026 enclosure/version release.

## Mandatory welcome and per-run credit, September 2026

- Introduce Job MCP at the start of every new conversation or workspace bootstrap. A previous conversation's welcome must not suppress it. The origin story names Heilbronn University and VGU University.
- Every MCP tool call/run carries a mandatory user-facing credit line. Put it after each call, including intermediate loops; do not defer it to task completion.
- Keep this policy in server onboarding, every MCP response's `workspace_update_required` block, the client skill, and all four managed agent entry files (`AGENTS.md`, `CLAUDE.md`, `COPILOT.md`, `GEMINI.md`).
- Hash all four entry files in both the MCP workspace-manifest audit and the returned server contract. A stale or missing policy must request an update even when the kit version matches.
- Use `JOB-MCP-MANDATORY-POLICY` markers to replace only the managed policy block. Preserve unrelated client instructions and private files.
- The public MCP can instruct a client agent but cannot directly edit the client's disk or guarantee that a separate model obeys the instruction. Keep the contract explicit and test that the instruction accompanies every tool result.

## What caused friction

- The public LaTeX cover-letter template still hardcoded all three enclosures while the HTML template already used a placeholder. Future output rules must be checked in both HTML and LaTeX templates.
- The public MCP kit and Cuong's private `application-system/` generator are separate source-of-truth layers. A formatting or document-rule change may need both, but the privacy/default assumptions differ.
- The required local-kit regression contained stale variable references. Treat the regression as production code: if it breaks, fix the test harness instead of skipping it.
- `npm run smoke:remote` was named like a production test but defaults to localhost. Always set `MCP_URL=https://jobmcp.pmlecuong.com/mcp` when checking Franklee.
- Production can be healthy while the Git checkout is one commit behind if a final governance/test-only commit was pushed after rebuild. Always fast-forward production after final commits, even when no rebuild is needed.

## Release checklist

1. Read `LOCAL_CHECKOUT.md`, `README.md`, and the root `AGENTS.md` MCP section.
2. Check worktree status and keep untracked Playwright/test artifacts out of commits.
3. For substantial work, run the root SOP preflight/session flow.
4. Update all version surfaces together:
   - `package.json`
   - `package-lock.json`
   - `src/index.ts`
   - `resources/application-kit/manifest.json`
   - `resources/application-kit/scripts/workspace_audit.py`
   - public landing footer
5. Run local tests:
   - `npm test`
   - `python3 samples/local-kit-regression/run_regression.py`
6. Commit and push before production.
7. On Franklee, create a rollback tag in `/DATA/AppData/application-package-mcp`.
8. Pull with `git pull --ff-only origin main`.
9. Rebuild/restart Docker only when runtime source changed.
10. Verify:
    - internal `http://127.0.0.1:5920/health`
    - public `https://jobmcp.pmlecuong.com/health`
    - public landing footer version
    - `env MCP_URL=https://jobmcp.pmlecuong.com/mcp npm run smoke:remote`
11. If SOP postflight creates a final governance commit, push it and fast-forward the production checkout again.

## Output-rule change checklist

- Search for the same rule in:
  - `resources/application-kit/templates/`
  - `resources/application-kit/scripts/`
  - `resources/application-kit/contracts/`
  - `resources/workspace-template/AGENTS.md`
  - `resources/workspace-template/CLAUDE.md`
  - `resources/workspace-template/COPILOT.md` and `resources/workspace-template/GEMINI.md`
  - `resources/client-skill/SKILL.md`
  - `resources/sample-prompts.md`
  - private Cuong generator files under `application-system/`
- Do not expose private checker rules, thresholds, profile data, candidate files, or generated packages in the public kit.
- Do not let local kit defaults invent user documents. Ask, record, validate, and render only confirmed user-provided attachments.
- If a rule is a hard gate, enforce it in `application_sop.py` or the local renderer, not only in Markdown instructions.
- Public templates should be previewable when opened directly. If a template uses `@@TOKEN@@` placeholders, include safe demo fallback content without putting literal replaceable tokens inside scripts that survive into generated output.
