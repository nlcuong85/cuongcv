# Student Application MCP Maintenance Notes

Durable lessons from the August 2026 enclosure/version release.

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
  - `resources/client-skill/SKILL.md`
  - `resources/sample-prompts.md`
  - private Cuong generator files under `application-system/`
- Do not expose private checker rules, thresholds, profile data, candidate files, or generated packages in the public kit.
- Do not let local kit defaults invent user documents. Ask, record, validate, and render only confirmed user-provided attachments.
- If a rule is a hard gate, enforce it in `application_sop.py` or the local renderer, not only in Markdown instructions.

