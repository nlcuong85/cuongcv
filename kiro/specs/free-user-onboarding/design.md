# Design Document: Job MCP Free-User Onboarding

## Overview

### Agent-led revision, 2026-10-22

The user's correction supersedes the earlier manual-first page structure below: the normal path is **open one folder → paste one setup request → approve agent-led configuration where required**. The prominent cream/blue/yellow diagram uses three icon nodes, arrows and an approval strip; HTML text equivalents remain accessible. Manual client settings and the raw address are collapsed fallback help after the main workflow. Client limitation help remains available.

Pre-connection entry: `GET /agent-setup.md` serves readable Markdown over ordinary HTTP/HTTPS, linked from the page head and setup prompt. It requires no native MCP registration. It directs the local agent to inspect/reuse or configure the supported client, respect required approval and verify tools after load. `GET /agent-setup/configure_codex_mcp.py` serves a reviewable helper as text only. No remote execution, browser permission grant or server-side filesystem access is introduced.

Helper owner: `resources/bootstrap/configure_codex_mcp.py`. Plan-only by default; `--approve` applies a project-scoped `.codex/config.toml` addition within the selected root. Existing TOML is parsed and preserved, a local backup precedes mutation, conflicting/disabled entries and escapes block changes, temporary write/replace reduces partial writes, and changed config is detected before replacement. Trust/approval/sandbox fields are never changed. A client may still need to trust or reload project configuration; the response never equates config creation with connection. The native CLI alternative registers user-level config only when that scope is explained and authorized. Actual UI reload/account verification remains a separate acceptance boundary.

This revision changes ONB-01.2, ONB-04.1 and ONB-10.1 and adds ONB-11/T22. Earlier four-step/manual setup sketches in this document are retained as design history, not current implementation instructions.

Date: 2026-10-22. Locally implemented following user authorization. Read [acceptance.md](acceptance.md) for three-loop evidence and limits; the design itself does not certify client/device support.

Keep the current Node/TypeScript service and server-rendered public pages. Improve the existing `/start` path using the established blue palette, typography, shared chrome, buttons, and responsive styles. Use native links and disclosures to keep the full instructions available without presenting every paragraph at once. No new application framework, account service, database, or installer is needed.

Source checkout: `experimental/application-package-mcp/` beneath CuongCV. Existing public pages and route handlers are in `src/index.ts`; `renderStartPage()` owns the setup copy, `renderDocsPage()` owns reference content, and `renderCopyButtonsScript()` supplies shared clipboard behavior. Current `package.json` reports service version 0.2.20. Record the exact tested SHA/version at execution time rather than treating this observation as a future release identity.

## Architecture

```text
PUBLIC GUIDE                          USER'S CLIENT / COMPUTER
GET / -> /start -> client section ---> register /mcp in client settings
              |                       -> discover tools / call health
              +-> folder instructions -> select writable Documents subfolder
              +-> setup prompt -------> fetch public template + kit
              |                       -> local audit / strict SOP flow
              +-> detailed help        -> readiness report / next user question

REMOTE MCP: generic kit + manifest audit + selected-text checks
            no access to the computer's filesystem
```

There are two independent capabilities: using remote MCP tools and writing into a local workspace. A browser page cannot prove either just by loading. The website guides the user; the actual client proves tool discovery, and the local agent proves scoped bootstrap. No green “Connected” badge is inferred from copying an address or a successful website health fetch.

### Source and runtime coordinates

| Surface | Coordinate | Verification responsibility |
| --- | --- | --- |
| Local source | `experimental/application-package-mcp` | Record Git SHA and dirty files |
| Local rebuilt service | `http://127.0.0.1:5943` for feature acceptance | `npm run build`, start `dist/index.js --http` with HOST/PORT and disposable data dir |
| MCP acceptance endpoint | `http://127.0.0.1:5943/mcp` | Both supported protocol generations and actual tool result |
| Public site/MCP/health | `https://jobmcp.pmlecuong.com/`, `/mcp`, `/health` | Only after an authorized release: health, content, protocol, browser |
| Production checkout | `/DATA/AppData/application-package-mcp` on Franklee | Rediscover live working directory/compose labels before release |
| Likely service compose | `experimental/application-package-mcp/docker-compose.yml` within production checkout | Confirm against container labels; don't assume checkout root compose |
| Container / port | `application-package-mcp` / 5920 | Confirm live inventory |
| Data/migrations | Existing operational data only; no new schema/migration | No candidate data or production metric DB in fixtures |
| Role/test seed | Anonymous visitor; synthetic candidate fixture | No credentials required for Job MCP; client account eligibility recorded separately |

## Components and Interfaces

### 1. Public page composition

| Owner | Change | Requirement |
| --- | --- | --- |
| Current homepage renderer in `src/index.ts` | Clarify setup CTA and two URL purposes; preserve examples and existing identity | ONB-01,04 |
| `renderStartPage()` | Short first screen, client sections, four ordered steps, single starter prompt, detailed disclosures | ONB-01 to ONB-07 |
| `src/onboarding.ts` | Implemented public setup body and canonical entry prompt, composed by `renderStartPage()` | ONB-01 to ONB-07 |
| `renderDocsPage()` | Link to client getting-started sections; retain full API/workflow/reference detail | ONB-01,03,04 |
| `renderCopyButtonsScript()` | Accurate fallback result, live status, manual-copy failure route; preserve other copy consumers | ONB-07 |
| Shared site styles/chrome | Reflow, restrained hero sizing, focus/target sizing, long-address wrapping | ONB-07 |
| `resources/onboarding.md`, `resources/client-skill/SKILL.md` | Connection and workspace preconditions, dependency distinctions, clear next action | ONB-02,05,06 |
| `resources/workspace-template/AGENTS.md`, `CLAUDE.md`, `COPILOT.md`, `GEMINI.md`, README | Equivalent preconditions within existing managed-policy rules | ONB-02,05,06 |
| `resources/sample-prompts.md` and any duplicated public prompt resources | Same minimal setup contract; preserve specialist prompt meanings | ONB-04,05 |
| Existing local capability/ingestion helpers under `resources/application-kit/` | Inspect actual probes first; add only missing task-specific checks/recovery | ONB-06 |
| Service README and maintenance notes | Update endpoint/client explanation and test commands | ONB-09 |

Use function/symbol names as anchors; line numbers in the proposal are historical. Do not change `src/checker.ts`, authentication, rate limits, protocol handlers, private profiles, or the account plan to solve an onboarding copy issue. If capability recovery needs local-script changes, use their real owners and existing tests rather than inventing a second bootstrap engine.

### 2. Screen and copy design

```text
/start
  Start your job-application workspace
  Connect your AI app, open one private folder, then begin.
  [Set up with Codex on my computer]     <- visible at first viewport
  ChatGPT in browser | On my phone | Another client

  1 Choose app  2 Connect tools  3 Open folder  4 Run setup
  Setup guide: [root address]
  MCP connection address: [/mcp address] [Copy MCP address]
  Verified app instructions + tool-availability check
  Selected-folder instructions for macOS / Windows / other
  Starter prompt [Copy setup prompt]

  Your files and checks: brief boundary + full privacy link
  > What to prepare and what is optional
  > Already set up? Application / ATS / writing prompts
  > Missing tools or something failed?
```

This is the information hierarchy, not a requirement to render four horizontal cards. At phone widths use an ordered vertical list. Avoid decorative hero height that pushes the first useful action below the fold. The small four-step flow can be HTML text with an accessible ordered list; it needs no renderer server or image dependency.

Every major section answers its purpose and next step in plain language. Technical protocol details stay in `/docs` and `/technical-flow`. Detailed instructions remain intact under headings/disclosures. Retain existing example/privacy routes and legacy prompt-route behavior. Do not state that scattered folders themselves cause slowness without measured evidence.

### Diagram inventory and update contract

The existing `.puml` sources and three served SVGs were inspected during this spec revision. Their existence does not mean the new onboarding behavior is already represented. PlantUML remains the editable source for technical diagrams; the short beginner visual is native HTML/CSS with an ordered-list text equivalent. Website visitors do not install a PlantUML extension or contact a rendering server.

All paths below are relative to `experimental/application-package-mcp/`.

| Asset/view | Current gap or purpose | Required implementation change | Publication and proof |
| --- | --- | --- | --- |
| New `/start` beginner visual | Current spec only described an optional small flow | Required four steps using plain labels; horizontal where comfortable, vertical at phone widths; connect/address and folder help links associated with the relevant steps | HTML/CSS ordered list; T10,T11,T21 |
| `resources/diagrams/bootstrap-scaffolding-flow.puml` and `.svg` | Starts with a request and `initialize + tools/list`; lacks initial client registration/folder choice | Add user client configuration, real tools verification, selected writable folder, recovery when either is missing, then actual kit/scaffold/strict-check ordering; show modern discovery or legacy initialization as alternatives | Existing `/assets/bootstrap-scaffolding-flow.puml` and `.svg` on `/technical-flow`; update captions and alt text |
| `resources/diagrams/private-checker-flow.puml` and `.svg` | Explains selected writing review but not the separate ATS input pair; loops need source-contract parity | Keep writing-mode flow; add a clearly bounded ATS branch or adjacent labelled explanation for selected CV/JD text; distinguish permission from repeated per-call prompting; show review evidence and local release validation accurately | Existing private-checker source/SVG routes; nearby text equivalent and privacy parity |
| `resources/diagrams/local-first-human-flow.puml` and `.svg` | Downloadable but not currently embedded in the modern homepage; broad “private files never leave” wording risks confusing selected text | Align setup/resume preconditions, privacy text, CV/cover gates and optional capability failures with the current flow; preserve its existing URL even if it stays a technical/download view | Test public asset routes and legibility, including explicit background/contrast |
| `docs/diagrams/local-first-mcp-application-flow.puml` and `.svg` | Older “Classmate” flow uses old folder paths and calls MCP only a distribution layer | Correct to current workspace paths and checker/manifest boundary, or clearly mark historical with a current-source link; do not leave it appearing authoritative | Repository documentation links and source/render parity; not a new user hero |
| `docs/diagrams/optional-auth/*` | Separate future account proposal | Leave account design intact; cross-check only that its anonymous path does not contradict current onboarding | Record any conflict for its own owner; no auth redesign under this feature |

Portable beginner equivalent:

```text
Choose your AI app -> Connect Job MCP -> Open one private folder -> Run setup
                         |                    |
                   Tools not available?   No folder/access?
                   Open connection help   Open folder help
```

Technical update semantics:

```text
User registers MCP in client -> client verifies available tools
User selects writable folder -> local agent retrieves generic kit
Local client scaffolds in selected root -> local SOP checks/audit
  -> manifest only to structure audit -> report next input/action
Selected writing OR selected CV + JD -> checker -> bounded feedback
Local evidence + required review/visual gates -> release or explicit blocker
```

Match the exact bootstrap script ordering after inspecting its implementation; a diagram must not depict the SOP running before its own executable files exist. Do not draw the remote service creating local directories. Do not put local file reads inside the MCP participant. Do not imply a green diagram step is proof the current user's setup has passed.

Rendering workflow for later implementation: edit canonical source, syntax-check, render same-basename SVG plus temporary PNG preview, inspect labels/arrows/background/contrast, compare source semantics to requirements, then verify actual served routes and page placement. Keep readable explanations next to images, meaningful alt text, stable source links, and a labelled full-size link/scroll region for complex sequences. Never send private candidate content to a public renderer. Runtime serves static rendered assets; no new server renderer is needed for visitors. Rebuild/restart before browser proof and check SVG MIME type/content rather than accepting an HTML fallback with HTTP 200.

### 3. Client guide contract

Use fragment-linked sections such as `#codex-computer`, `#chatgpt-browser`, `#phone-remote`, and `#other-client`. Essential content is server-rendered. Native `<details>/<summary>` may group longer instructions; any script enhancing fragment navigation must open the target disclosure on initial load, reload, hash change, and back/forward. Without JavaScript, the linked section and its summary must remain reachable and manually openable.

Each path contains: who it works for; required client/account conditions; verified steps; exact MCP address; how to prove tools exist; local-folder capability; failure recovery; verification date/source. Codex is the recommended route, but a complete UI click sequence is published only after checking the installed app version and actual client. Do not guess menu labels from a different client. CLI instructions are an advanced alternative, not the first demand on a beginner.

ChatGPT browser/phone guidance uses the dated sources from the proposal as a starting point. Revalidate current product docs and the real device before publication. Separate direct custom-MCP support, remote continuation of a paired desktop task, and local filesystem capabilities. A working Tailscale login is an example of an external authorization journey, not evidence that a particular AI client supports Job MCP or exposes laptop files.

### 4. Starter prompt contract

Candidate wording, to be synchronized across public copies:

```text
Help me prepare a private job-application workspace using Job MCP.
Read https://jobmcp.pmlecuong.com/ for the workflow.
First check whether Job MCP tools are available and whether I have opened
a dedicated writable folder. If either is missing, guide me through that step.
Work only inside the folder I select and preserve existing files.
Use the current public workspace kit and its required local checks.
Start with my existing CV or ask for my work and education facts.
Keep source files local; send only the permitted manifest or selected text
needed for a check. Tell me what is ready and the next thing you need from me.
```

This is an entry prompt, not the complete managed policy. Kit instructions still carry the service introduction/signature requirements, strict boot/audit flow, factual boundaries, and output review gates. A real client may need user permission or a tool installation; the agent must report this specifically, not claim the prompt can grant it.

### 5. Workspace and capability progression

```text
unknown client -> tools unavailable -> connection guidance -> tools verified
tools verified -> no selected folder -> folder guidance -> workspace selected
workspace selected -> bootstrap/update -> strict checks -> setup ready
                                                |              |
                                      recoverable blocker       v
                                                   source/profile intake
                                                            -> requested task
                                                            -> task capability check
```

The server returns generic files; the local client writes them. Resolve the actual Documents location through the OS/client chooser. Suggest a subfolder, allow another user-selected location, and avoid hardcoded home paths. Inspect existing files before applying managed updates. Do not traverse symlinks outside the selected root. A read-only or unrelated folder triggers a new selection, not a permission-escalation instruction.

| Requested operation | Capability to inspect | Missing capability behavior |
| --- | --- | --- |
| Connect native MCP client | Client's remote transport support and reachable endpoint | Client setup help; no universal local Node/Python prerequisite |
| Bootstrap/audit public Python kit | Compatible Python and required kit files | Python setup help for detected OS; pause local bootstrap |
| Supplied JS MCP wrapper | Compatible Node and wrapper prerequisites | Offer verified native-client route where supported; do not claim wrapper succeeded |
| Text-based profile intake/remote selected-text check | User-confirmed text, connected tools; applicable local workflow preconditions | Ask for facts; preserve strict workflow requirements |
| PDF extraction/reference | Actual extraction/rendering tools used by adapter, including Poppler where required | Preserve source; request text alternative or install help; output unverified |
| DOCX extraction/reference | Actual Python/office tools used by adapter, including `python-docx` where required | Preserve source; task-specific help or supported alternative |
| TeX/PDF generation | Actual TeX engine/`latexmk` used by renderer | Keep editable draft; PDF blocked; no visual-pass receipt |
| HTML visual/print validation | Supported browser and rendering path | Keep HTML; visual/print acceptance pending |

Installation help must be version/OS verified during execution. It must state what changes and whether elevation is needed. No background package installation, shell-piped remote code, or broad host changes are part of clicking a website button. Choosing an alternate input/output may change the required gate set only through an existing supported contract, never an invented pass.

## Data Models

### Static guide content

Prefer a small typed content structure close to the existing renderer when duplication warrants it; do not create a CMS. Public values must be escaped when inserted into HTML.

```text
ClientGuide:
  id, displayName, surface, os[], status(supported|limited|unverified)
  prerequisites[], setupSteps[], verifySteps[], recoverySteps[]
  supportsLocalWorkspace, sourceUrls[], checkedAt, evidenceRef

SetupCopy:
  setupGuideUrl, mcpConnectionUrl, starterPrompt
  materialGroups(requiredNow|requiredForTask|recommended|optional)
```

`evidenceRef` points to a sanitized QA record, not a user session or token. An official support statement alone cannot turn an untested integration into tested support. Server content is authoritative for what is displayed; client runtime is authoritative for tool availability; local SOP state is authoritative for workspace and document readiness.

### Local capability result

Reuse the current probe's schema where present. Any extension should represent: operation, available capabilities, missing capabilities, affected artifacts, next safe action, and `blocked/unverified/available` status. Store only locally under existing SOP evidence ownership. Do not create a new remote profile or upload local environment paths to analytics.

### State ownership and persistence

| State | Owner | Reload/back behavior |
| --- | --- | --- |
| Selected client help section | URL fragment | Direct links and browser history restore location |
| Expanded optional help | Native disclosure/ephemeral DOM | May reset; essential information never lost |
| Copy pending/success/failure | Browser memory and live region | Reset on reload; never persisted as connection proof |
| Connection, local folder, bootstrap status | Actual AI client and local SOP | Website cannot infer or persist a successful state |
| Candidate facts and files | Local workspace | Existing safe update/integrity rules |
| Theme/language preferences | Existing site behavior | No new preference store introduced |

## Error Handling

| Condition | Visible response / recovery | Prohibited success claim |
| --- | --- | --- |
| Clipboard rejected/unavailable | Keep text visible; “Could not copy. Select and copy the text below.” | “Copied” without confirmed clipboard/fallback success |
| Legacy fallback returns false | Same manual-copy path; restore focus | Treating nonthrowing `execCommand` as success |
| MCP not configured | Guide to client settings and exact address | Connected because homepage opened |
| Endpoint/network failure | Distinguish address/configuration from reachability; preserve work; retry after correction | Reinstall everything or upload private CV |
| No folder / denied access | Guide to choose/open a writable dedicated folder | Whole-computer access required |
| Existing workspace drift | Existing audit/update path with scoped managed changes | Blank-folder overwrite |
| No CV or JD | Ask for facts now; JD when needed for target task | Invented profile or fake ATS match |
| Optional converter missing | Name operation, what remains available, and recovery/skip choice | Final ready document without applicable gate evidence |
| Unknown client/device support | Limited/unverified label with official source and next route | Guaranteed support based on generic MCP compatibility |

Copy controls use `aria-live="polite"` status. If a fallback is used, inspect its boolean result and exceptions, restore focus, and preserve the original accessible label during/reset after feedback. Scope every copy target to its own container. Do not introduce a global button selector that copies the first prompt for every action.

## Operational UI Hardening Contract

| Surface | Primary action owner | Supporting actions / hidden-state rule |
| --- | --- | --- |
| Homepage | Start setup links to `/start` | Examples/reference remain secondary; no competing setup prompts |
| `/start` introduction | Choose recommended client path | Alternatives visible by name; no fake connect button |
| Active guide section | Copy MCP address, then open folder instructions | Accessible names distinguish address from prompt |
| Starter panel | Copy setup prompt | Exactly one starter prompt; specialist prompts in returning-user section |
| Detailed help | Expand/read/copy relevant task prompt | Collapsed content doesn't expose focusable hidden controls |

There are no new data-entry forms, uploads, save operations, or destructive actions; form validation and database transaction contracts are not applicable. Copy is the only browser mutation. Internal navigation uses same-tab links; external official documentation may use a new tab with an explicit accessible indication and `rel="noopener noreferrer"`. Do not automatically navigate to a custom app URI unless verified and accompanied by a normal fallback.

Preserve typography and spacing tokens from the current shared chrome. Use wrapping `<pre>`/code blocks for long URLs and prompts and scope overflow where needed. Validate the named viewports, 200% zoom, focus, contrast, touch targets, reduced motion if existing animation is reused, and the first useful action's viewport position. Do not shrink text merely to pass a fold measurement.

## Testing Strategy

[tests.md](tests.md) is the manual testcase source of truth for this feature, authored before future browser automation. It contains T01-T20 and maps every acceptance criterion. When execution adds a repository QA tree, preserve IDs and link to these cases rather than creating divergent expectations.

### Selector Contract

- Prefer roles and accessible names for links, buttons, headings, and disclosure summaries.
- Proposed exact copy labels: `Copy MCP address`, `Copy setup prompt`, `Copy application prompt`, `Copy ATS prompt`, `Copy writing prompt`.
- Use deliberate test hooks only where needed: `data-testid="onboarding-steps"`, `client-guide-<id>`, `copy-status-<scope>`, and `setup-prompt`.
- Avoid `nth()`, CSS parent chains, or DOM-order assumptions for primary controls.
- Verify inactive/hidden controls are absent from the keyboard sequence, not merely visually transparent.

### Suite ownership and UX coverage matrix

| Layer | Existing/proposed owner | Evidence |
| --- | --- | --- |
| Existing build/MCP contracts | `tests/mcp-http.test.mjs`, `tests/application-sop.test.mjs` | Preserve anonymous, version, protocol, resource and gate regression |
| New HTTP page contract tests | Proposed `tests/onboarding-content.test.mjs` | URL labels, prompt retention, HTML content type, no-JS readable content |
| Browser navigation/layout | Proposed `qa/automation/playwright/onboarding-navigation.spec.mjs` | Maps to T01,T06-T10,T16 |
| Browser copy/accessibility | Proposed `qa/automation/playwright/onboarding-interactions.spec.mjs` | Maps to T11,T12,T16 |
| Diagram semantics/render/publication | Existing asset checks plus proposed `qa/automation/playwright/onboarding-diagrams.spec.mjs` | T21 and ONB-10; source/render parity and actual images, not URL presence alone |
| Local kit | `samples/local-kit-regression/` plus focused capability fixtures | T03-T05,T14,T15,T17-T19 |
| Actual clients/devices | Manual procedures in tests.md | Tool discovery + real scoped local operation |
| UX matrix | Proposed `output/playwright/free-user-onboarding/ux-matrix.md` | Criterion, case, artifact, runtime, status, blocker |

These new suite paths do not exist merely because the design names them. Playwright dependencies/configuration must be inspected and added only during approved implementation. Use Chrome DevTools for exploration and diagnostics; use focused repeatable browser automation for regression. Neither substitutes for testing the actual external client.

### Local Validation and browser validation at each milestone

Execution sequence: update manual expectations; implement slice; build; restart exact local service; run focused tests and kit fixtures; click changed paths; inspect screenshots and errors; record every criterion; provide the localhost URL and small manual pack at M1/M2/M3. Reopen the earliest failing owner and rerun dependent journeys before continuing.

Existing commands from service directory:

```bash
npm ci
npm test
# Start the rebuilt service separately on loopback 5943 with disposable data.
APPLICATION_MCP_URL=http://127.0.0.1:5943/mcp python3 samples/local-kit-regression/run_regression.py
MCP_URL=http://127.0.0.1:5943/mcp npm run smoke:remote
```

Use distinct temporary data and synthetic candidates. Record exact start command, SHA, package/kit version, OS, client version, and BASE_URL. Browser routes must return HTML and `/health` JSON with expected service identity; an HTML fallback at an API URL fails the check. Future Playwright commands/config are defined in tests.md and are planned until implemented.

### Production Handoff

An eventual release follows root AGENTS and `MAINTENANCE_NOTES.md`: local proof first; inspect real Franklee checkout/container/compose and current SHA; save rollback reference; stage only authorized files; rebuild/restart from canonical source; run live health checks internally and publicly, verify both protocol paths, expected tool list, visible version and changed public pages. Synchronize service/kit versions when a release changes the managed kit. Record config/image/source rollback coordinates and any disposable-data cleanup. This specification does not deploy or modify the existing auth plan.

## Lessons Applied and prior-art boundaries

| Source | Apply | Result |
| --- | --- | --- |
| Resilient MCP R5B/R5C, R18-R23 | Existing local state/audit and review ownership | Improve entry instructions; avoid a parallel setup controller |
| Argon clean-environment audit | Core setup distinct from optional rendering | Capability recovery without fake finalization |
| Shared copy helper source | Fallback can ignore `execCommand` failure | T12 verifies fallback false/rejection and focus recovery |
| BuilderOps artifact lessons | Rebuild runtime before UI proof | Runtime record for each milestone |
| Account-path plan | No transfer of auth UI into this feature | Anonymous setup remains available |
| Typical SPA/account architectures | Not applicable | No new framework, sessions, or database |

## References and publication checks

Primary references checked for spec controls on 2026-10-22:

- [Kiro Feature Specs](https://kiro.dev/docs/specs/feature-specs/) — requirements/design/tasks lifecycle; this package adds an explicit test document at the user's request.
- [Playwright locators](https://playwright.dev/docs/locators) — semantic locator strategy for maintainable browser proof.
- [MDN Clipboard.writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText) — asynchronous clipboard failure/permission boundary.

Client references inherited from the proposal; recheck the actual current client before publishing menu labels or availability claims:

- [OpenAI ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275).
- [OpenAI custom MCP apps](https://help.openai.com/en/articles/12584461-creating-custom-mcp-apps-in-chatgpt).
- [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp).

These sources define design controls. Only the execution evidence can prove Job MCP meets them. Support records must name product changes or unavailable device/plan tests honestly.
