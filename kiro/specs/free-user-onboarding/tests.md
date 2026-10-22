# Test Specification: Job MCP Free-User Onboarding

Date: 2026-10-22. Status: local implementation checks executed in three review loops; see [acceptance.md](acceptance.md) for results and outstanding actual-client/device portions.

Companions: [requirements.md](requirements.md), [design.md](design.md), and the [source audit](../../../experimental/application-package-mcp/docs/free-user-onboarding-proposal.md).

This document defined manual cases before automation. The user subsequently authorized local implementation and three review loops. Expectations below remain the QA source of truth; execution status is qualified in acceptance.md rather than treating a local test as proof of all device/account paths.

## Test scope and rules

Latest user-approved correction: the main route is folder → paste request → agent-led configuration with applicable approval. Manual settings are fallback, not prerequisites. T01/T02/T21 follow this sequence; add T22 below. The previous four-step ordering is superseded. A prompt/config helper is not allowed to self-grant permissions or fake a live connection.

Validate the beginner's journey from the website through a real compatible client to a working local workspace. Also prove the limited paths, recovery, retained detailed instructions, privacy, and existing anonymous MCP behavior. A mock browser test cannot pass real client registration, tool discovery, local folder selection, or phone continuation.

Use the exact rebuilt local runtime at `http://127.0.0.1:5943` by default, its `/mcp` transport, and synthetic candidate material. Record SHA plus dirty diff reference, service/kit version, OS/client/browser version, account eligibility where relevant, date, BASE_URL, commands, and artifact paths. If the client cannot reach loopback, use an explicitly selected test endpoint and record that difference; never silently substitute production.

No private Cuong CV, tone corpus, recruiter correspondence, real student data, tokens, or unsanitized client screenshots in committed fixtures. Isolated OS accounts/VMs are preferred for clean-user proof; a temp folder on an existing Mac does not prove a clean dependency environment.

### Environments

| Environment | Required proof | Status at authoring |
| --- | --- | --- |
| Desktop browsers, 1366x768 and 1920x1080 | Site navigation, copy, layout, keyboard | NOT RUN for new feature |
| Mobile viewports, 390x844 and 430x932 | Fold position, reflow, touch targets | NOT RUN for new feature |
| macOS + recommended installed Codex client | Real configuration, empty/reused folder, local setup | NOT RUN |
| Windows + recommended compatible client | Documents/OneDrive location, paths with spaces, local setup | NOT RUN |
| Clean Argon/Linux temporary workspace | Published/local kit bootstrap and optional capability absence | Earlier audit passed only its stated baseline; rerun needed |
| ChatGPT browser | Actual available plan/workspace path or accurate limitation | NOT RUN |
| Phone + paired desktop session | Real supported Remote continuation | NOT RUN; emulation cannot replace device proof |

A path cannot be labelled verified in public content until its actual client evidence exists. If a secondary device is unavailable, label its guidance limited/unverified and list the blocked acceptance; do not claim complete support.

## Fixtures and evidence

Prepare synthetic fixtures during implementation: short verified profile notes; CV/JD text; a tiny supported document; an existing workspace with a sentinel source/output; an unrelated user-authored instruction block; stale managed block; read-only directory; symlink escaping a nominated root; task environments with missing converter binaries/modules. Preserve originals and compare hashes before/after.

Evidence directory: `output/playwright/free-user-onboarding/<run-id>/`. Use a local acceptance record for CLI/client results and a UX matrix at `output/playwright/free-user-onboarding/ux-matrix.md`. Redact identity, account tokens, native account screens, and home paths before sharing. Keep disposable artifacts outside tracked source unless sanitized fixtures are deliberately added.

Each result row records: case/criterion, status (`PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, justified `N/A`), runtime identity, fixture, observed result, artifact, blocker, and earliest affected owner. A passing test from an older build cannot pass changed copy or new behavior automatically.

## Manual test cases

### T01 — Two addresses, two jobs

Requirements: ONB-01.1-.2; ONB-04.1. Method: HTTP + browser.

Preconditions: clean browser context; rebuilt local site.

1. Open homepage, follow Start setup, then open the recommended client section.
2. Read labels for the guide root and `/mcp` address; copy the connection address.
3. Check the local docs link and any homepage address copy.

Expected: root labelled setup guide; `/mcp` labelled connection address; exact copied endpoint; explicit statement that pasting a URL/prompt does not connect tools. No CTA implies the website registers the client.

Evidence: homepage/start screenshots, copied value, HTML content checks. Automation: `onboarding-content.test.mjs` and navigation suite.

### T02 — Actual client connection proof

Requirements: ONB-01.3; ONB-05.1. Method: actual client + MCP.

Preconditions: eligible test client with Job MCP absent; test endpoint reachable.

1. Open a dedicated folder and paste the published setup request; allow the agent to retrieve the pre-connection HTTPS guide and use the client's supported configuration mechanism. Approve only the specific required change when asked; manual settings are fallback if the client cannot configure itself.
2. Discover its tools and call a harmless health tool.
3. Confirm server identity and expected tool names.
4. Confirm reading the website alone did not produce that state.

Expected: actual client tool availability is demonstrated separately from HTTP availability. No invented app menu labels or hidden CLI prerequisites. Record protocol mode/version and actual result. Website tests alone cannot pass this case.

### T03 — First workspace with no folder open

Requirements: ONB-02.1,.3; ONB-05.1-.3. Method: actual client + local CLI.

Preconditions: client connected; no project open; compatible Python available for the local kit.

1. Follow folder instructions to create/select `Documents/Job Applications` or a chosen equivalent.
2. Open it in the client and grant the necessary scoped permissions.
3. Paste the setup prompt; follow public template/kit and local strict boot/audit.
4. Inspect created files and the agent's readiness report.

Expected: no writes before selected context; no full-disk permission demand; supported bootstrap completes in the selected root; safe manifest only; report separates connection, workspace readiness, and missing candidate facts. No application-ready claim.

### T04 — Reuse workspace without data loss

Requirements: ONB-02.2; ONB-05.2; ONB-06.4. Method: actual client + fixture hashes.

Preconditions: existing workspace with source/output sentinels, custom instructions, stale managed section.

1. Choose reuse and run setup/update guidance.
2. Follow audit/update recovery for stale managed content.
3. Repeat once after a simulated interrupted setup.

Expected: unrelated instructions, sources, and prior outputs retain content/hashes; changes stay within managed rules; no duplicate nested workspace or silent reset; interrupted state resumes through SOP rather than a fresh overwrite.

### T05 — Folder permission and path boundaries

Requirements: ONB-02.1,.3-.4. Method: local fixture + actual client.

1. Test a path with spaces/non-ASCII characters and Windows redirected Documents.
2. Try a read-only folder, no permission, and a symlink escaping the selected root.
3. Follow the offered recovery to a writable in-scope folder.

Expected: OS-appropriate selection, no username assumption or broad privilege escalation, no writes outside root, useful error with safe next step; original files untouched. A missing Windows/device environment is BLOCKED, not PASS.

### T06 — ChatGPT browser branch

Requirements: ONB-03.1-.2,.4. Method: browser + actual eligible/ineligible client as available.

1. Select ChatGPT browser and inspect source/date/conditions.
2. On an eligible account, follow verified setup and prove tool discovery if advertised.
3. On an ineligible surface, inspect limitation and recommended next route.

Expected: local laptop files are not promised without a verified supported desktop connection; plan/admin conditions explicit; login is not described as granting Job MCP/filesystem access. Record an unavailable account condition as BLOCKED.

### T07 — Phone-only and paired-desktop distinction

Requirements: ONB-03.1,.3-.4. Method: actual phone + desktop where available.

1. Open phone guidance without a paired desktop task.
2. Confirm the useful next step is clear without trying unsupported local writes.
3. Separately continue an existing permitted desktop session from the supported mobile feature, if available.

Expected: limitation and Remote continuation are distinct. Phone/browser emulation can verify layout only. Real device proof records desktop availability, folder scope, and actual action outcome without exposing secrets.

### T08 — Other/unknown client and stale support claim

Requirements: ONB-03.1-.2,.4. Method: browser + content record review.

1. Open Other client and inspect conditions, source, date, and evidence label.
2. Review an unknown/unverified client path and a deliberately stale test record.

Expected: endpoint and generic compatibility guidance remain useful, but unsupported menus/capabilities are not fabricated. Stale/unverified support is not advertised as fully tested. Test fixture modifications must stay local.

### T09 — Minimal intake and retained material

Requirements: ONB-04.1-.4. Method: browser + local agent.

1. Start with profile notes and no CV, JD, writing samples, photo, or signature.
2. Complete the smallest setup/intake step.
3. Open all detailed sections and find specialist application, ATS, and writing prompts.
4. Start a specific ATS request without a JD.

Expected: facts requested rather than invented; JD required at the matching stage, not base setup; optional assets can be declined; evidence/voice/employer bullets and mandatory photo/signature questions/review gates remain documented. ATS cannot report a meaningful match without both required texts.

### T10 — Responsive first action and long content

Requirements: ONB-04.1; ONB-07.1. Method: real browser measurements + visual review.

1. Cold-open `/start` at all four named viewports.
2. Measure recommended action bounding box and document/viewport widths.
3. Expand longest help, long addresses and prompts; use 200% browser zoom.
4. Inspect screenshots at each state.

Expected: recommended action fully inside initial viewport at default scale; no page horizontal overflow/clipped labels; text remains readable rather than artificially reduced; zoom reflows and controls remain available. Expanded detailed content may scroll vertically.

### T11 — Keyboard, semantics, and disclosure operation

Requirements: ONB-07.2. Method: browser + accessibility inspection.

1. Navigate all setup actions using Tab/Shift+Tab and Enter/Space.
2. Open/close disclosures; inspect heading order, focus, accessible names and live status.
3. Measure mobile hit areas; inspect contrast and focus visibility.

Expected: meaningful order and labels; no hidden focusable controls or focus trap; at least 44x44 CSS-pixel action targets; copy result announced without unexpected focus movement. Automated accessibility snapshots supplement visual/keyboard review.

### T12 — Every copy success and failure route

Requirements: ONB-07.2-.3. Method: browser with controlled clipboard behavior.

1. Click address, setup, application, ATS, and writing copy actions; compare exact clipboard payload to its own visible text.
2. Deny/reject async clipboard and separately exercise legacy fallback success, false return, and exception.
3. Repeatedly activate one button, then a different button; keyboard-trigger it.

Expected: correct per-scope text; success only on confirmed copy; selectable text/manual instructions on failure; status announced; labels/focus recover; no cross-button status reset or false “Copied.” Shared-copy consumers on other pages also work.

### T13 — Wrong endpoint, unavailable service, and missing tools

Requirements: ONB-01.4; ONB-05.1. Method: actual client + controlled network failure.

1. Configure an incorrect guide-root address in a disposable client configuration.
2. Try unreachable endpoint, healthy website without expected MCP tools, and corrected `/mcp` configuration.

Expected: actionable distinction between address/configuration and network/service failure; no tool-success claim from page health; no document upload/reinstall demand; corrected configuration enables discovery. Restore only test configuration.

### T14 — Core setup versus task dependencies

Requirements: ONB-06.1-.2. Method: isolated environment + actual client.

1. Use native remote MCP connection without assuming local Node/Python availability.
2. Start local-kit bootstrap without compatible Python.
3. Start the supplied JS wrapper without Node separately.

Expected: native connection requirement described accurately; local capability blockers identify the affected operation; OS-specific verified instructions and permission boundary; no silent install. Test report does not generalize one client's dependencies to all clients.

### T15 — Missing converters, preserved release gates

Requirements: ONB-06.2-.3. Method: isolated fixtures/CLI + local agent.

1. Remove/mock absence of Poppler, DOCX extraction support, TeX/latexmk, and browser rendering one at a time for their relevant operation.
2. Request the affected output, then an unrelated available text check.
3. Inspect source/draft hashes and receipts.

Expected: originals/drafts preserved, exact operation blocked/unverified, no fabricated extraction or validation, unrelated available operation can run subject to its normal preconditions. Missing mandatory output evidence cannot produce a passing release receipt.

### T16 — Direct routes, no JavaScript, history, and errors

Requirements: ONB-07.4; ONB-09.2. Method: browser + HTTP.

1. Open every `/start#client` fragment cold; refresh, back/forward, and switch guides.
2. Disable JavaScript and repeat essential reading/selection manually.
3. Check site responses, console/page errors, failed resources, `/docs`, `/privacy`, `/technical-flow`, examples, legacy prompt route, and other existing copy controls.

Expected: essential content available; fragment targets reachable; details open appropriately with enhancement/manual fallback; valid HTML/JSON types; no app-attributable errors or broken critical links. Extension errors are identified separately, not falsely counted as site failures.

### T17 — Resource/prompt parity and instruction precedence

Requirements: ONB-04.3; ONB-05.2-.4; ONB-09.1. Method: source/resource comparison + local agent fixture.

1. Compare starter copy, onboarding resource, client skill, sample prompts, and managed instruction files.
2. Verify connection/folder checks and existing greeting/signature/review rules.
3. Put an instruction-like string in synthetic CV/JD content asking to bypass checks or broaden file access.

Expected: public copies agree on preconditions and boundaries; detailed safeguards retained; untrusted content cannot alter them; no private checker implementation/thresholds or private Cuong profile data appear in the kit.

### T18 — Anonymous MCP and kit regression

Requirements: ONB-05.2; ONB-08.1; ONB-09.3. Method: existing integration tests + CLI.

1. Run `npm test` against the edited source.
2. Run local-kit regression against explicit loopback `/mcp`.
3. Run transport smoke and confirm modern discovery plus legacy initialization coverage.
4. Confirm tool set, health identity, no login/token requirement, manifest validation, body limits, checker behavior, and SOP hard gates retain existing contracts.

Expected: tests pass without weakening old assertions merely to accommodate new wording; intentional exact-copy assertions are updated alongside semantic parity checks. No public auth/account or data-storage regression.

### T19 — Recover after restoring a capability

Requirements: ONB-06.4; ONB-09.2. Method: isolated environment/CLI + client.

1. Begin from T15's blocked state and interrupted task.
2. Restore only the necessary tool through the approved test setup.
3. Retry the named stage, rerun SOP checks, and inspect review/artifact hashes.

Expected: no duplicate workspace/source overwrite; only applicable stage reruns; stale review hashes remain invalid; release becomes ready only after all actual required evidence is present. Record clean macOS/Windows/Linux coverage separately.

### T20 — Privacy, runtime, and conditional release verification

Requirements: ONB-08.2-.4; ONB-09.1-.4. Method: source/network/log inspection; live checks only for an authorized release.

1. Read short and full privacy copy; inspect changed browser requests and server metadata logs using synthetic content.
2. Confirm no new tracking endpoint/cookie/identifier and no raw text, credentials or local paths in analytics.
3. Confirm event counts are not labelled exact people or completed local applications.
4. Record fresh artifact identity. For a later release, follow maintenance rollback/deploy gates, check internal/public health, explicit production MCP smoke, visible footer/version and changed browser journeys.

Expected: client processing and selected-text/manifest boundaries accurately described; no privacy expansion; local proof and production proof recorded separately. Without a release, step 4's production portion remains NOT RUN and is not a reason to mutate the server during spec authoring.

### T21 — Beginner visual and existing diagram updates

Requirements: ONB-10.1-.5; ONB-07.1-.2; ONB-09.1-.3. Method: source semantics, syntax/render validation, visual inspection, HTTP and actual browser.

1. Inspect the `/start` four-step visual against the nearby instructions. Follow its connection/folder help links and repeat on both phone viewports, desktop, keyboard, 200% zoom, and with JavaScript disabled.
2. Review every row in design.md's diagram inventory. Confirm the bootstrap source shows actual client registration/tool verification and folder permission before local writes, supported protocol alternatives, missing-context recovery, and executable bootstrap ordering.
3. Compare privacy/review flows to writing checks, ATS CV/JD inputs, safe manifest, and local finalization gates. Reject “MCP only distributes files” or blanket “no data leaves” claims on current diagrams.
4. Syntax-check changed `.puml`, render matching SVG and PNG previews, and visually inspect line/label overlap, cropping, arrow meaning, contrast/background and readable text. Compare source and render so an old SVG cannot accompany new source.
5. Open `/technical-flow` and every retained `/assets/*.svg` and `.puml` route on the rebuilt runtime; verify status and expected MIME/content, not HTML fallback. Confirm images actually decode/display, captions/alt text/explanations agree, and full-size/scoped-scroll access works for complex diagrams.
6. Check the older docs diagram is corrected or unmistakably historical with a working current link. Confirm optional-auth diagrams were not redesigned and existing public asset URLs still resolve.

Expected: beginner flow understandable without a renderer/plugin or horizontal scroll; technical detail remains accessible without shrinking all text; all affected sources, rendered assets, page copy and endpoints agree. Evidence: inventory disposition, syntax/render outputs, semantic review notes, screenshots of beginner/technical views and response-content checks. A `.puml` parser pass alone cannot pass this case.

Automation ownership: proposed `onboarding-diagrams.spec.mjs` plus existing asset HTTP tests. Manual visual/semantic inspection remains required. Diagram inspection performed during spec authoring is baseline review, not acceptance of future changed diagrams.

### T22 — Agent-led bootstrap and approval-controlled configuration

Requirements: ONB-11.1-.4; revised ONB-01.2, ONB-04.1, ONB-10.1.

1. Before native MCP registration, fetch `/agent-setup.md` and the optional helper through ordinary HTTP. Verify source/content type, explicit scope, client approval and no permissions self-grant.
2. In a temporary selected project, run the helper without approval. Expect a plan and no `.codex` files created.
3. Provide approval in the isolated fixture; verify a project-scoped entry, backup and preserved existing comments/model/other servers. Repeat and expect an idempotent result. No global/trust/approval/sandbox configuration may change.
4. Test conflicting/disabled entries, malformed TOML, symlink escapes and denial; expect no overwrite or escalation. Real client denial/reload behavior needs actual-client evidence in addition to helper fixtures.
5. Open `/start`: main action leads directly to one setup request; the coloured diagram shows folder/request/agent nodes with directional arrows and approval boundary. Manual settings remain collapsed until requested. Check desktop/mobile screenshots and matching sample/managed instructions.

Proof owners: `tests/onboarding-agent-bootstrap.test.mjs`, route checks in `tests/mcp-http.test.mjs`, revised navigation/interaction browser suites and visual inspection. Actual fresh-client loading remains separately qualified.

## Acceptance-criterion coverage

Every acceptance criterion maps below. Browser N/A means another proof method is required, not that the criterion is waived.

| Criteria | Cases | Required proof | Browser-only limitation |
| --- | --- | --- | --- |
| ONB-01.1-.2 | T01 | Browser/HTTP and copy text | None |
| ONB-01.3 | T02 | Actual client discovery/health | Website cannot pass it |
| ONB-01.4 | T13 | Actual client recovery + guide | Error-copy alone insufficient |
| ONB-02.1 | T03,T05 | OS folder chooser + scoped write | Browser N/A for local filesystem |
| ONB-02.2 | T04 | Hash preservation + client | Browser N/A for local state |
| ONB-02.3 | T03,T05 | Client permissions + guide | Actual permission settings required |
| ONB-02.4 | T05 | Denial/symlink fixture | CLI/client proof |
| ONB-03.1 | T06,T07,T08 | Browser choice/navigation | Actual support tested separately |
| ONB-03.2 | T06,T08 | Dated record + client evidence | Docs alone insufficient |
| ONB-03.3 | T07 | Guide + physical device | Emulation proves layout only |
| ONB-03.4 | T06,T07,T08 | UI-first instructions + boundary review | Actual client UI labels checked |
| ONB-04.1 | T01,T09,T10 | Browser ordered path/fold | None |
| ONB-04.2 | T09 | Actual intake conversation | No fabricated facts |
| ONB-04.3 | T09,T17 | Expanded details + resource parity | None |
| ONB-04.4 | T09 | Agent skip/defer and readiness | Actual flow required |
| ONB-05.1 | T02,T03,T13 | Client prerequisites | Mock cannot pass |
| ONB-05.2 | T03,T04,T17,T18 | SOP/manifest/public-resource evidence | CLI/client required |
| ONB-05.3 | T03,T09 | Agent report and real state | No page-generated fake status |
| ONB-05.4 | T17 | Managed policy + hostile fixture | CLI/client required |
| ONB-06.1 | T14 | Clean capability matrix/probes | Isolated host required |
| ONB-06.2 | T14,T15 | Scoped error/help and install boundary | Client/CLI required |
| ONB-06.3 | T15 | Draft preservation and gate failure | Browser N/A for receipts |
| ONB-06.4 | T04,T19 | Resume and hashes | Client/CLI required |
| ONB-07.1 | T10 | DOM measurements + screenshots | Visual review required |
| ONB-07.2 | T11,T12 | Keyboard/accessibility/focus | Visual review required |
| ONB-07.3 | T12 | Exact clipboard and negative states | None |
| ONB-07.4 | T16 | No-JS/direct/history paths | None |
| ONB-08.1 | T18 | Existing MCP contracts | API/CLI proof required |
| ONB-08.2 | T20 | Copy + processing-boundary review | Provider policies not proved by page |
| ONB-08.3-.4 | T20 | Network/log/source inspection | No identity inference |
| ONB-09.1 | T17,T20 | Owner map/diff reconciliation | Source proof |
| ONB-09.2 | T16,T19,T20 | Complete evidence ledger | Unrun cases remain explicit |
| ONB-09.3 | T18,T20 | Local + conditional release gates | No deployment claim without live proof |
| ONB-09.4 | T20 | Defect-to-source/manual regression record | Apply on any discovered defect |
| ONB-10.1 | T21,T10,T11 | User visual/order/reflow/keyboard/no-JS | Actual page required |
| ONB-10.2-.3 | T21 | Bootstrap/protocol/privacy/review semantic review | Browser image alone cannot prove semantics |
| ONB-10.4 | T21,T16 | Syntax/render + served source/SVG + captions/alt | Visual review required |
| ONB-10.5 | T21 | Full inventory and preserved URL checks | Documentation copies included |
| ONB-11.1-.4 | T22,T01,T12 | Ordinary HTTP instructions, temporary config plan/apply/conflict tests and primary browser path | Helper success is not live client registration proof |

## Automation plan and execution commands

Keep existing Node HTTP/SOP suites. Create focused page-content and browser suites only during implementation. Browser navigation suite maps T01,T06-T10,T16; interaction suite maps T11,T12,T16. Both link to this file and case IDs. They do not simulate a pass for actual client setup.

Existing commands, run from `experimental/application-package-mcp/`:

```bash
npm ci
npm test
APPLICATION_MCP_URL=http://127.0.0.1:5943/mcp python3 samples/local-kit-regression/run_regression.py
MCP_URL=http://127.0.0.1:5943/mcp npm run smoke:remote
```

The last two require the rebuilt local service already running with disposable data. Node tests choose their own ports/data roots; keep them isolated from feature acceptance. For missing-tool tests, change only the disposable fixture's environment/tool resolution, not the host's installed packages.

Planned browser command after Playwright config/dependencies are added:

```bash
BASE_URL=http://127.0.0.1:5943 npx playwright test --config qa/automation/playwright/playwright.config.mjs onboarding-navigation.spec.mjs onboarding-interactions.spec.mjs
```

Add the planned `onboarding-diagrams.spec.mjs` to the browser command when that suite is implemented. Do not report these planned commands as executed or currently available. Start each suite by asserting correct service/page identity. Capture trace on failure, screenshots for layout/disclosures/diagrams and errors, and app-attributable console/network failures. Use semantic selectors from design.md; repair semantics before relying on fragile DOM order.

## Milestone and exit criteria

At M1, M2 and M3 from requirements.md: rebuild/restart, run affected cases, inspect actual runtime, update evidence, and provide the local URL plus a small manual check pack. An earlier defect reopens its source owner and dependent completed cases. No final stabilization task can hide a failed prerequisite.

Exit for implementation acceptance: all applicable criteria have passing evidence; required actual-client tests pass; secondary unsupported paths are labelled honestly; no unresolved high-impact data-loss/privacy/false-success defect; original kit/MCP regression passes. Exit for deployment acceptance additionally requires the authorized release's live evidence and rollback record. No fabricated pass for unavailable accounts/devices.

Suggested beginner evaluation: observe five first-time users on the recommended computer path without verbal coaching. Ask each to connect, open a folder, and begin with profile facts. Proposed target: at least four complete the path and all can distinguish the connection address from the guide. Record sample size, time, prompts for help, and failure step. This is a usability target for later evaluation, not a measured claim or substitute for technical tests; recruitment and study execution are not product code tasks.

## Current results

| Evidence category | Status |
| --- | --- |
| Three spec documents authored | Complete |
| Earlier live website/Argon audit | Inherited baseline, scope limited as described |
| Product behavior | Implemented locally; acceptance.md records evidence and limits |
| T01-T21 execution | Local portions executed; actual-client/device portions pending as mapped in acceptance.md |
| Actual macOS/Windows/mobile client UI acceptance | Not end-to-end verified; SDK/CLI proof recorded separately |
| Deployment | Not performed |

Record future runs here by dated reference or link to the UX matrix. Do not change these statuses because a Markdown structure validator passes.
