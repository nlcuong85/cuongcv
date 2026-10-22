# Local onboarding implementation and acceptance record

Date: 2026-10-22. Owner-authorized scope: implement locally, run three distinct review/repair loops, and preserve the separate account-path proposal.

Local preview: http://127.0.0.1:5943/start

## Latest revision: agent-led setup and visible diagram

The owner's subsequent UX correction supersedes the manual-first entry described in the earlier three-loop record below. Current local version is **0.2.22**, kit **2026.10.22-onboarding.2**.

The main path is now: open one folder → paste a three-line request → let the agent configure/check the connection and prepare the workspace, with the client's required approval. Manual settings are collapsed fallback help. `/agent-setup.md` is available over ordinary HTTP/HTTPS before MCP is registered; root guide and prompt link to it. It explains supported client configuration, existing-entry reuse/conflicts, approval and reload boundaries without claiming downloaded instructions can grant access.

A prominent cream/blue/yellow diagram now has folder/chat/shield icons, connecting arrows, user/agent ownership labels and an approval strip. It becomes vertical on mobile. Both desktop and mobile figure screenshots were inspected visually; labels/arrows and contrast are readable without a diagram renderer.

The optional Python project-config helper was tested only in isolated temporary projects: no writes before approval, backup/preservation, idempotence, malformed/conflicting/disabled configuration and symlink escape rejection. It never changes global trust, sandbox or approval settings and reports awaiting-load rather than connected. The helper does not prove that a real client has loaded the new configuration.

Latest checks: **13 code/API tests passed**, **14 browser tests passed**, modern/legacy smoke passed with kit .2, and revised bootstrap PlantUML parsed/rendered. Logs: `/tmp/jobmcp-agentled-tests.log`, `/tmp/jobmcp-agentled-browser.log`. Screenshots: local ignored `output/playwright/free-user-onboarding/artifacts/onboarding-diagrams-T21-pu-1cb36-er-carry-corrected-boundary/agent-map-desktop.png` and `agent-map-mobile.png` beneath the service checkout.

Requirements ONB-01.2/04.1/10.1 were revised, ONB-11 and T22 added, and sample/managed instruction entrypoints synchronized. Real fresh-client registration/reload and physical-device acceptance remain unverified as before. Production has not been updated: the canonical public URLs in copied prompts will serve this new guide only after deployment. The local endpoint is available for inspecting/testing the new guide now.

## Runtime and change identity

- Source: `experimental/application-package-mcp/` in CuongCV.
- Base Git HEAD: `043d0507ba1a7ed42991871c5b40c19af7ae8b7d`; implementation is an uncommitted working-tree change, not a release commit.
- Service version: 0.2.21; public kit: `2026.10.22-onboarding.1`.
- Rebuilt `dist/index.js --http`, HOST 127.0.0.1, PORT 5943, disposable local runtime data.
- Browser: Playwright 1.64.1 / Chromium 156 on macOS; fresh browser contexts.
- No production deployment, account implementation, or optional-auth diagram redesign.

## Implemented outcome

The first screen offers one recommended computer route and named alternatives. A native HTML four-step visual links to client connection, selected folder and setup prompt. The guide root and MCP address have separate labels. Client instructions cite current official documentation, disclose plan/rollout conditions and unverified actual-device paths, and keep advanced CLI instructions optional. Detailed evidence, voice, asset, ATS, writing, interview and release rules remain under discoverable help.

Shared copy actions now verify fallback success, retain accessible labels, announce results, and offer selectable text on failure. Direct fragment links reveal their target help. Essential content works without JavaScript. The new setup module uses existing blue/cream visual tokens. Technical views provide labelled, keyboard-focusable diagram scroll regions and full-size links.

The local kit includes a read-only operation-specific capability probe. Missing PDF/DOCX helpers produce recovery guidance; original ingestion now prevents replacing an existing different source or following output symlinks out of scope. All public instruction entrypoints and the sample setup prompt carry the prerequisites without removing existing welcome/review policies.

Updated PlantUML/SVG pairs: bootstrap, private checker, and local workflow. The older docs flow is unmistakably historical and linked to the current inventory. Bootstrap now shows modern/legacy discovery, connection/folder stopping conditions and local scaffold before executing the SOP. Review text covers selected writing, CV/JD ATS inputs and manifests without claiming the user's AI provider never processes source text.

## Three review loops

| Loop | Focus | Findings and repairs | Outcome/evidence |
| --- | --- | --- | --- |
| 1 | Behavior, compatibility, kit and protocol | Updated obsolete exact-copy assertions to the approved first-run labels while retaining semantic/gate assertions. Kept core connection separate from local converters. Added protection against original-source overwrite during retry. | Existing 6 Node integration tests passed; local-kit regression passed its 3 existing cases; explicit loopback smoke passed modern and legacy modes. Logs: `/tmp/jobmcp-loop1-tests.log`, `/tmp/jobmcp-kit-loop1.log`. |
| 2 | Browser UX, accessibility, copy failures, mobile and diagrams | Initial browser run was blocked until Chromium was installed. Actual browser then found ATS copy-label capitalization inconsistent with the intended label and low-contrast status text on a dark panel. Fixed labels/status contrast and strengthened technical diagram scroll containment/full-size access. | 13 browser journeys passed after repair. Screenshots inspected at 390px and desktop; all four technical SVGs rendered to PNG and visually inspected. Log: `/tmp/jobmcp-browser-loop2-repair.log`. |
| 3 | Fresh runtime and spec reconciliation, missing tools, source preservation | Fresh SDK workspace fixture proved real template/kit retrieval, local strict boot and current remote audit. Fixed a test harness argument shape and a missing test import. Added real missing-PDF-tool execution using an isolated PATH, supported text fallback, doubled CSS layout-zoom check, console/request assertions and complete diagram inventory. Corrected diagram stopping semantics using break frames. | Final 11 Node tests and 14 browser tests passed. SDK-to-local workspace passed with `workspace_current`; both protocol modes passed again. Syntax/render checks and npm audit passed. Logs: `/tmp/jobmcp-loop3-final-tests.log`, `/tmp/jobmcp-browser-loop3-final.log`. |

The loop count is a review structure, not a claim of universal acceptance. Repairs reran the affected checks. A fixed three-pass count cannot replace unavailable device/account evidence.

## Requirement and case reconciliation

Manual intent remains [tests.md](tests.md). Every criterion is covered by its existing criterion-to-case table; the execution results below qualify that mapping rather than overwriting it with an inflated pass.

| Requirement | Local evidence | Remaining boundary |
| --- | --- | --- |
| ONB-01.1-.4 | URL labels/payloads, UI path, SDK discovery/health, old/new protocol tests | Real fresh desktop UI registration and client-specific connection-error recovery still require that client/account |
| ONB-02.1-.4 | Folder/OneDrive/permissions guidance; temporary local scaffold; preserved-original/retry and symlink tests; scoped read-only capability probe | Windows redirected Documents, actual client folder chooser, OS read-only access and managed-update user flow not fully end-to-end proven |
| ONB-03.1-.4 | Browser/phone/other branches, fragment/reload/history, dated official sources and explicit limited/unverified labels | No fresh ChatGPT web account or physical phone pairing tested; no generic client compatibility guarantee |
| ONB-04.1-.4 | Four-step browser flow, retained material/prompts, public resource comparison, existing SOP/fact-boundary tests | Actual novice conversation and observed beginner study remain pending |
| ONB-05.1-.4 | Prompt/resource parity; SDK kit fetch, local strict boot and manifest current; existing release/injection regression | Third-party model compliance with instructions is not guaranteed or tested by a static resource assertion |
| ONB-06.1-.4 | Capability absence/restoration tests; missing-Poppler operation leaves source untouched; text alternative works; existing local release gates pass regression | Real user-authorized package installation on each OS not performed; no gates bypassed |
| ONB-07.1-.4 | Named 4 viewport sizes, first-action bounds, readable screenshots, keyboard/disclosure/copy statuses, no-JS and direct links, doubled CSS layout zoom | CSS zoom is a local reflow approximation, not physical-device or native browser UI zoom/screen-reader certification |
| ONB-08.1-.4 | Anonymous health/tools/protocol contracts; unchanged analytics scope; no new POST tracking from browser flows; public privacy copy reviewed | Anonymous visits remain event estimates; no claim of exact users or measured onboarding conversion |
| ONB-09.1-.4 | Owner map/docs, tests, runtime restart, evidence ledger and defect repairs | Production checks not run because this request was local implementation |
| ONB-10.1-.5 | Beginner HTML visual; canonical source syntax/SVG generation; four PNG inspections; browser image decode/MIME/routes, scoped scrolling and source links | Current public site changes only after a later deployment |

| Manual cases | Execution status |
| --- | --- |
| T01,T08,T10-T12,T16,T18,T21 | Local automated/manual visual checks passed within the limits above |
| T02-T05 | SDK/CLI/source parts passed; actual fresh-client UI and Windows portions pending |
| T06-T07 | Guide/limitation UI passed; actual hosted account and physical-phone portions pending |
| T09,T13-T15,T17,T19 | Applicable local script/API/content portions passed; full user/OS/client journeys pending where specified |
| T20 | Local privacy/runtime checks passed; production portion not run |

## Evidence and reproducibility

Service directory commands:

```bash
npm test
BASE_URL=http://127.0.0.1:5943 npm run test:browser
MCP_URL=http://127.0.0.1:5943/mcp npm run test:onboarding-workspace
APPLICATION_MCP_URL=http://127.0.0.1:5943/mcp python3 samples/local-kit-regression/run_regression.py
MCP_URL=http://127.0.0.1:5943/mcp npm run smoke:remote
npm audit
```

Start the rebuilt local service separately before URL-dependent commands. Test config is in `qa/automation/playwright/playwright.config.mjs`; three focused suites map to manual cases. Browser artifacts/screenshots/report are local and ignored under `experimental/application-package-mcp/output/playwright/free-user-onboarding/`. The clean-workspace script creates a synthetic temporary folder and prints its exact path; it never reads private CV material. The repository's existing kit regression uses existing local fixtures and was explicitly pointed at localhost, not the public service.

Diagram PNG inspection previews: `/tmp/jobmcp-bootstrap-final.png`, `/tmp/jobmcp-review-final.png`, `/tmp/jobmcp-human-final.png`, `/tmp/jobmcp-history-final.png`. Canonical `.puml` and rendered `.svg` remain in the repository. Optional-auth sources remain untouched.

## Review handoff

Open the local `/start` page, choose a client branch, inspect the four-step visual, copy the address/setup prompt, expand materials and dependency help, then open `/technical-flow` at phone width and use a full-size diagram link. The local application is reviewable now. Full all-device acceptance is not asserted; the pending real-client/device checks and subsequent authorized release are explicit follow-up work.
