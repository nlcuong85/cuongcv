# Requirements Document: Job MCP Free-User Onboarding

## Introduction

Date: 2026-10-22. Status: authorized for local implementation; locally implemented and checked in three review loops. Actual-client/device acceptance remains qualified in [acceptance.md](acceptance.md).

Help a person who has only used ordinary ChatGPT reach their first useful Job MCP workflow without knowing what an MCP server, project workspace, or document converter is. Keep the existing anonymous tools available, explain one recommended computer-based path clearly, and preserve the detailed guidance needed for good application documents.

This is a focused Feature Spec using the repository's visible `kiro/specs/` convention. The user requested requirements, design, and test documents together; all three are authored for joint review. The third artifact is [tests.md](tests.md), not an implementation task checklist. Product execution is a separate step.

### Authority and related specifications

Latest user correction, 2026-10-22: make the normal flow folder → one pasted request → agent-led connection/configuration with required approval. Manual MCP settings become fallback help. A prominent branded diagram replaces the subtle text-only overview. This decision supersedes the earlier manual-first sequence, including historical audit recommendations that prescribed manual client setup.

- Source proposal: [Free-user onboarding audit and improvement proposal](../../../experimental/application-package-mcp/docs/free-user-onboarding-proposal.md).
- Parent: [Resilient application MCP requirements](../resilient-application-mcp/requirements.md), [design](../resilient-application-mcp/design.md), and [tasks](../resilient-application-mcp/tasks.md).
- Existing service: `experimental/application-package-mcp/src/index.ts`, public resources, HTTP tests, local-kit regression, and `MAINTENANCE_NOTES.md`.
- Separate future account work: `experimental/application-package-mcp/docs/optional-google-oauth-account-path-plan.md`. No login, Google OAuth, API-key, account dashboard, quota, or tool-toggle implementation belongs to this feature.

The new requirements refine parent R5B/R5C, R18B-R18F, R19-R23, R27, and R28. They do not reduce evidence, privacy, review-loop, managed-instruction, or finalization requirements. Parent task checkboxes are planning history, not proof of current implementation. Reconcile source and evidence before executing any parent task again.

### Evidence and current state

The proposal records a live Chrome/DevTools review of `/`, `/start`, and `/docs`, including desktop and 390-pixel mobile views. It records approximately 4,900 pixels of mobile `/start` content and a first screen dominated by the hero. These are inherited observations from that audit, not new measurements made during this spec-authoring pass.

The earlier isolated Argon test successfully initialized MCP, listed tools, fetched the workspace/template kit, and completed strict Python bootstrap/audit in a temporary directory. Node and Python were present; Poppler, `latexmk`, and `python-docx` were absent. This proves that tested Linux path only. Fresh Windows/macOS client onboarding, a phone-to-desktop journey, and optional document production remain unverified here.

| Audit issue | Source owner | Proposed state | Priority |
| --- | --- | --- | --- |
| A1: guide URL confused with transport address | Public page copy and client guide | Separate labels and connection proof | P0.1 |
| A2: no usable folder/permission starting point | `/start`, starter prompt, local instructions | Explicit selected-workspace path | P0.2 |
| A3: clients/devices treated as equivalent | Client instructions and support claims | Dated capability records and honest limitations | P1.2 |
| A4: too much before first success | `/start` hierarchy and prompts | One first-run path, details retained below | P1.1 |
| A5: dependencies and recovery unclear | Local kit, public help, error copy | Task-specific capabilities and recovery | P1.3 |
| Mobile scanning and measurement follow-up | Layout, QA, existing metrics | Responsive acceptance; new analytics deferred | P2 |

### Roles and flow

| Role | Needs | Boundary |
| --- | --- | --- |
| New computer user | Choose a client, connect, open a folder, begin | No shell knowledge required for primary path |
| Returning user | Reuse workspace and find a specific task | No forced reinstallation or data replacement |
| Phone user | Understand a phone-only path versus an existing paired desktop task | Phone continuation is not proof of direct mobile MCP support |
| Local AI agent | Verify available tools and writable workspace; apply public kit | Cannot infer permissions or act as a remote filesystem service |
| Maintainer/tester | Reproduce failures and support claims | Cannot count anonymous IP-derived visitors as exact people |

```text
Choose client -> connect and verify tools -> open one dedicated folder
      |                                            |
      +-> limitation/help if unsupported            v
                              setup prompt -> local bootstrap -> first next step
                                                    |
                           selected text/manifest -> MCP feedback
```

## Requirements

Acceptance criteria have stable identifiers `ONB-01.1` etc. Each criterion is normative; [tests.md](tests.md) defines the proof and its current status.

### Requirement 1: Distinguish guidance from connection (ONB-01)

**User Story:** As a new user, I want to know exactly what to copy and where, so that reading the website is not mistaken for connecting its tools.

#### Acceptance Criteria

1. WHEN connection instructions display addresses THEN the website SHALL label `https://jobmcp.pmlecuong.com/` as the setup guide and `https://jobmcp.pmlecuong.com/mcp` as the MCP connection address.
2. WHEN the user follows the first-run path THEN the guide SHALL ask the local agent to configure a missing server using its supported mechanism and required approval; it SHALL distinguish a configured entry from a verified live connection and SHALL NOT imply downloaded instructions grant permission.
3. WHEN a client is configured THEN its guide SHALL require tool discovery or a harmless Job MCP health call before declaring the connection successful; a website HTTP 200 SHALL NOT suffice.
4. IF connection or discovery fails THEN the guide SHALL offer a client-specific next action and SHALL NOT tell the user to repeat application generation or upload private files to fix it.

### Requirement 2: Establish a safe local workspace (ONB-02)

**User Story:** As a beginner without a project open, I want the client to guide me into one dedicated folder, so that the agent has a clear place to work.

#### Acceptance Criteria

1. WHEN local setup begins without an open folder THEN the instructions SHALL show how to create/select and open `Job Applications` within the operating system's Documents location, or a user-chosen equivalent, before writing workspace files. They SHALL account for redirected/OneDrive Documents rather than assume a literal username path.
2. IF the user already has a dedicated workspace THEN the agent SHALL offer reuse, inspect managed-file compatibility locally, and preserve existing sources, instructions outside managed blocks, and outputs.
3. WHEN access is requested THEN the primary guidance SHALL request the selected workspace's required capabilities and SHALL NOT require whole-disk, whole-Documents, or unrestricted execution merely for setup. Client permission controls and file selection SHALL be explained separately.
4. IF permissions, a read-only directory, or a symlink escaping the selected root prevent safe setup THEN the agent SHALL stop that write, explain the affected step, and offer a writable in-scope folder without deleting or moving user files.

### Requirement 3: Offer accurate client and device paths (ONB-03)

**User Story:** As a user of ChatGPT, Codex, or another client, I want instructions that match my actual app and device.

#### Acceptance Criteria

1. WHEN `/start` opens THEN it SHALL expose a recommended Codex-on-computer path and clearly named ChatGPT-browser, phone/Remote, and other-client guidance.
2. WHEN a client path is published as supported THEN its record SHALL name the app/surface, applicable operating system, plan or administrator conditions, verification date, official source, and actual end-to-end evidence; otherwise it SHALL be labelled limited or not yet verified.
3. IF a user has only a mobile browser/chat THEN the guidance SHALL state the local-folder limitation and provide a computer-based next step; it SHALL describe supported paired-desktop continuation separately, subject to that client's verified availability.
4. WHEN connection steps are shown THEN the guide SHALL use verified UI instructions first, place CLI alternatives under advanced help, and SHALL NOT imply Google login or Tailscale login automatically authorizes Job MCP or local folder access.

### Requirement 4: Reduce first-run decisions while retaining substance (ONB-04)

**User Story:** As a nontechnical candidate, I want one small useful first step before collecting all my documents.

#### Acceptance Criteria

1. WHEN the recommended path is displayed THEN it SHALL present open a private folder, paste one setup request, and approve agent-led setup if required, in that order, with one clearly labelled setup prompt. Manual settings SHALL be collapsed fallback help.
2. WHEN setup asks for source material THEN it SHALL accept an existing CV or user-confirmed profile/work-history notes, ask a focused next question if neither exists, and defer the target JD until tailoring or ATS matching is requested.
3. WHEN detailed material is moved below the first-run section THEN CV/evidence guidance, writing samples, employer bullets, photo/signature decisions, review loops, privacy, and the application/ATS/writing prompts SHALL remain discoverable with their original substantive safeguards.
4. IF an optional input is unavailable THEN the guide SHALL explain its benefit and an honest continue/defer choice, without inventing facts or assets. Setup completion SHALL NOT imply a ready application.

### Requirement 5: Make the setup prompt and agent instructions agree (ONB-05)

**User Story:** As a user pasting the prompt, I want the agent to verify the prerequisites and give me a clear next action.

#### Acceptance Criteria

1. WHEN setup starts THEN the prompt and public agent instructions SHALL direct the agent to verify usable Job MCP tools and selected writable folder context before bootstrap; absent context SHALL produce the relevant setup guidance, not a false success.
2. WHEN prerequisites are available THEN the agent SHALL fetch the public managed template/kit, apply its existing safe update rules, run the local audit and strict SOP flow, and send only the permitted manifest for remote structure audit.
3. WHEN bootstrap completes THEN the agent SHALL distinguish connection status, workspace readiness, and outstanding profile/document tasks, naming one next user action and any actual blocker.
4. WHEN the prompt is shortened THEN mandatory greeting/signature policy, factual confirmation, privacy boundaries, and application release gates SHALL remain in the public resource/managed instructions; examples, scraped pages, or candidate files SHALL NOT override them.

### Requirement 6: Explain dependencies at the affected task (ONB-06)

**User Story:** As a beginner seeing a package error, I want to know what still works and how to recover.

#### Acceptance Criteria

1. WHEN core setup or an optional document task starts THEN the local workflow SHALL check the capabilities that task actually requires and identify missing tools by purpose, rather than requiring every converter up front. Client-native remote MCP connection SHALL NOT be described as always requiring Node or Python on the user's computer.
2. IF a required local capability is missing THEN the guidance SHALL name the affected operation, show a verified OS-specific help route, and request the applicable permission before installation; it SHALL NOT silently run a remote installer or elevate privileges.
3. IF PDF/DOCX/rendering support is missing THEN the workflow SHALL preserve originals/drafts and permit unrelated available checks, while marking the affected output blocked or unverified; it SHALL NOT fabricate extraction, visual validation, or release receipts.
4. WHEN the capability is restored THEN retry SHALL resume the affected stage and existing SOP checks, without duplicating the workspace, overwriting candidate sources, or marking skipped mandatory gates as passed.

### Requirement 7: Provide readable, accessible interactions (ONB-07)

**User Story:** As a phone or keyboard user, I want setup instructions and copy controls I can use comfortably.

#### Acceptance Criteria

1. WHEN viewed at 390x844, 430x932, 1366x768, or 1920x1080 at default scale THEN `/start` SHALL display the primary client-path action wholly within the initial viewport, with no page-level horizontal overflow or clipped action labels. At 200% zoom content SHALL reflow without losing controls.
2. WHEN navigating with a keyboard or assistive technology THEN links, client choices, disclosure summaries, and copy buttons SHALL have meaningful names, visible focus, logical order, and announced status; mobile actions SHALL have at least 44x44 CSS-pixel hit areas.
3. WHEN a copy action succeeds THEN it SHALL copy only the matching address/prompt and announce success; IF clipboard access fails THEN it SHALL provide selectable visible text and manual-copy guidance without reporting success.
4. WHEN JavaScript is disabled or a client panel is opened directly/reloaded THEN essential steps, addresses, prompts, privacy links, and limitations SHALL remain readable; browser back/forward SHALL preserve valid route/fragment behavior without showing a false completed setup state.

### Requirement 8: Preserve anonymous operation and truthful privacy (ONB-08)

**User Story:** As a free user, I want setup to work without a new account and without exposing my career folder.

#### Acceptance Criteria

1. WHEN the improved guide is released THEN current anonymous tools, protocol generations, input limits, review behavior, and `tokenRequired: false` public operation SHALL remain compatible; connecting to the tools SHALL NOT require a new account or API key.
2. WHEN describing privacy THEN the website SHALL distinguish local workspace storage, the AI client's own processing policy, selected checker text, and the safe manifest; it SHALL NOT imply no data ever leaves the computer.
3. WHEN collecting evidence or existing operational metrics THEN the feature SHALL exclude private CV/JD/prompt bodies, raw local paths, credentials, and checker text from analytics; no new event endpoint, identifier, fingerprint, or tracking cookie SHALL be introduced in this release.
4. WHEN reporting usage THEN anonymous visit/protocol/tool counts SHALL be labelled as those events rather than exact people, verified local completion, or conversions across sessions.

### Requirement 9: Maintain source, regression, and runtime truth (ONB-09)

**User Story:** As a maintainer, I want the website, local instructions, tests, and deployed artifact to agree.

#### Acceptance Criteria

1. WHEN implementing this feature THEN the affected page copy, resource instructions, README, and manually specified test expectations SHALL be updated together using [design.md](design.md)'s owner map.
2. WHEN validating THEN each criterion SHALL have mapped browser/API/CLI or actual-client evidence, with blocked/not-run cases explicitly recorded; page screenshots and mock tool responses SHALL NOT establish actual client setup success.
3. BEFORE release THEN local build/tests, local-kit regression, responsive/keyboard/copy journeys, and supported real-client checks SHALL pass against a fresh identified artifact; AFTER authorized deployment THEN public/internal health, transport smoke, visible content/version, and changed browser paths SHALL be checked.
4. IF an implementation or user report reveals a missed edge case THEN the earliest affected requirement/design/manual case SHALL be revised and adjacent regression rerun before completion is claimed.

### Requirement 10: User-facing diagrams and existing visual consistency (ONB-10)

**User Story:** As a beginner, I want a short visual explanation of what I do and where my files go, so that the diagrams clarify setup instead of adding technical work.

#### Acceptance Criteria

1. WHEN `/start` presents setup THEN it SHALL include a prominent branded visual with folder, request and agent-setup nodes, directional connectors and a clear approval boundary. It SHALL use the page's blue/cream/yellow palette, match the normal agent-led instructions, become vertical on narrow screens, and remain readable without an external renderer or JavaScript.
2. WHEN existing technical diagrams are updated THEN the bootstrap view SHALL show client registration/tool verification and selected-folder access before local writes, with missing-connection/folder recovery; it SHALL distinguish modern discovery from legacy initialization rather than imply only one supported protocol.
3. WHEN privacy/review diagrams or their captions are published THEN they SHALL distinguish local files, selected writing text, CV/JD text for ATS, and the allowed manifest; they SHALL preserve the actual review/release gates and SHALL NOT claim that no source-derived text ever leaves the device or that the MCP is only a distribution layer.
4. WHEN a `.puml` source changes THEN its served SVG SHALL be regenerated, syntax/render checked, visually inspected, and tested together with its source route, caption, alternative text, and nearby text explanation. Detailed technical diagrams MAY use labelled scoped scrolling/open-full-size access; the beginner four-step visual SHALL NOT require pinch-zoom or horizontal scrolling.
5. WHEN diagram maintenance is implemented THEN the inventory in design.md SHALL be reconciled, including unembedded but still downloadable assets and older documentation copies; a superseded diagram SHALL be corrected or clearly labelled historical with a link to the current view, and existing public asset URLs SHALL remain valid unless an explicit migration is approved.

### Requirement 11: Agent-led connection before MCP is registered (ONB-11)

**User Story:** As a beginner, I want my local agent to handle MCP setup from one pasted request, so that I do not have to understand server settings.

#### Acceptance Criteria

1. WHEN tools are not yet connected THEN the agent SHALL be able to retrieve public setup instructions through ordinary HTTPS, configure the supported client with applicable approval, preserve unrelated settings and verify discovery/health after loading. Manual setup SHALL be fallback only.
2. IF configuration approval is denied, the client cannot edit/load settings, or an existing entry conflicts THEN the workflow SHALL stop that mutation, explain the exact limit and offer minimal fallback/reload guidance without changing global approval, trust or sandbox settings.
3. WHEN the optional Codex project-config helper is used THEN it SHALL default to a read-only plan, apply only under explicit approval, preserve/backup valid existing settings, reject symlink escapes/malformed/conflicting/disabled entries and report configured-awaiting-load rather than connected.
4. WHEN the user pastes the root guide or setup request THEN the public page SHALL expose the pre-connection agent guide, and sample prompts/managed instructions/diagrams/tests SHALL agree on the agent-led flow and approval boundary.

## Delivery order and exclusions

| Milestone | Included priorities | User-testable outcome | Exit proof |
| --- | --- | --- | --- |
| M1: usable first path | P0.1, P0.2, P1.1; accurate minimum client labels from P1.2 | User connects, selects folder, bootstraps with one prompt | T01-T05, T09-T12, T16-T18 |
| M2: accurate alternatives and recovery | Remaining P1.2 and P1.3 | Other surfaces have honest guidance; missing dependencies are recoverable | T06-T08, T13-T15, T19 |
| M3: responsive acceptance and release readiness | P2 layout/QA, source/runtime reconciliation | Same journey remains usable at phone widths and production matches tested source | T10-T12, T16-T20 |

Responsive layout and ONB-10's beginner visual are implemented and checked in M1; M3 completes the cross-surface acceptance sweep and all existing-diagram reconciliation. T21 is required at both milestones for their changed visuals. No path may advertise unverified capabilities while waiting for M2. New onboarding analytics remain deferred pending a separate data contract; the proposal's measurement ideas are retained for later consideration.

Excluded: OAuth/account work, server-side CV storage, application submission, private Cuong profile/tone import, wholesale redesign, new frontend framework, and a dependency auto-installer. Existing mandatory conversion/review requirements remain binding whenever their output is requested.

## Traceability manifest

| Source | Requirement | Owner/contract | Invariant or recovery | Manual case | Proof |
| --- | --- | --- | --- | --- | --- |
| A1 / parent R22 | ONB-01 | URL labels and client connection guide | No connection from page read alone | T01,T02,T13 | HTTP/browser + actual client |
| A2 / parent R18B,R21 | ONB-02 | Folder guide and public instructions | Selected root; preserve files | T03,T04,T05 | Actual client + local hashes |
| A3 / phone feedback | ONB-03 | Capability records | Limited until verified | T06,T07,T08 | Browser + actual device/client |
| A4 / parent R5B,R5C | ONB-04 | First-run and advanced-help structure | Details retained; no fabricated inputs | T09,T10,T17 | Browser + local intake |
| Parent R18B-R23 | ONB-05 | Starter prompt and managed resources | Connection, bootstrap, readiness distinct | T02,T03,T04,T17,T18 | MCP/CLI + actual client |
| A5 / parent R1-R4,R18D | ONB-06 | Capability help/SOP adapters | Missing converter cannot pass release | T14,T15,T19 | Isolated CLI + client |
| Live mobile/copy review | ONB-07 | Shared chrome and copy script | Failure visible; no JS fallback | T10,T11,T12,T16 | Browser measurements/screenshots |
| Owner free-path decision | ONB-08 | Existing service/metrics boundary | No auth or tracking expansion | T18,T20 | MCP tests + log/request inspection |
| Parent R27,R28 | ONB-09 | QA and runtime record | Fresh artifact; explicit evidence gaps | T16,T18,T19,T20 | Local and release records |
| Existing public/documentation diagrams | ONB-10 | Visual inventory in design.md | Source/render/copy parity; accessible beginner flow | T21,T10,T16 | Syntax/render, visual and browser proof |
| User correction: agent-led setup | ONB-11 | /agent-setup.md, project-config helper, page/prompt resources | Approval-controlled mutation; no permission self-grant | T22,T01,T12 | HTTP and isolated helper tests + browser |

## Lessons Applied

| Reference | Risk observed | Decision | Resulting control |
| --- | --- | --- | --- |
| Prior Job MCP audit | Backend boot passed but beginners still stalled | Apply | ONB-01 to ONB-05 prove the client journey |
| Existing resilient spec | Optional renderer absence could be confused with release permission | Apply | ONB-06 preserves blocked/unverified output state |
| Existing service source | SSR HTML with shared copy script; no SPA required | Apply | Retain stack; design failure handling explicitly |
| BuilderOps browser lessons | Source/tests can pass while served artifact is stale | Apply | ONB-09 requires artifact identity and live behavior |
| Existing anonymous metrics | Requests are not verified users | Apply | ONB-08.3-.4; no new tracking in this release |

## Review and evidence status

The user authorized local batch implementation and three review/repair loops. See [tasks.md](tasks.md) and [acceptance.md](acceptance.md) for completed local work, test evidence, and remaining device/account checks. Documentation validation is not acceptance proof. Official primary references and dated client-verification responsibilities are recorded in [design.md](design.md).
