# Job MCP Free-User Onboarding Audit and Improvement Proposal

**Status:** Proposal only — no application code, production settings, authentication, database, or existing OAuth plan changed
**Reviewed:** 2026-10-22
**Scope:** First-run experience for anonymous/free users connecting a compatible AI client to Job MCP and starting work in a private local folder

## Executive decision

Keep the existing anonymous/free tools and the MCP-first product direction. Improve the onboarding path around them; do not turn the website into an application-writing service, add accounts, or alter the separate authentication plan.

The present service works at the protocol and local-kit level, but a new user can still mistake “read this website” for “connect the MCP,” arrive without an opened project folder, or assume ordinary ChatGPT on a phone can access files on a computer. The recommended change is a concise, client-aware first-run guide that makes four things explicit: which client to use, how to connect it, how to safely open one dedicated folder, and what the user needs to provide first.

The five issues and ranked fix order below combine the earlier clean-environment audit with the live Chrome/DevTools inspection performed for this proposal. The product owner reports that many users are new to ChatGPT/Codex; that is important audience context, not an independently measured analytics percentage.

## Audit evidence

### Live website inspection

I opened the published site in Chrome and inspected the homepage, `/start`, and `/docs`. I reviewed desktop and 390 × 844 phone-sized screenshots, read the visible page structure, and used Chrome DevTools Protocol for read-only page metadata and text inspection. No website state was changed.

| Surface | What is there now | What a first-time user may not understand |
|---|---|---|
| `/` homepage | “Start setup,” a site URL labelled for an agent, a local-first privacy summary, and a prominent marketing hero | Whether copying the root URL actually adds the MCP connection, or just asks an AI to read a web page |
| `/start` | Four setup steps, one long starter prompt, an extensive source-material checklist, then job, ATS, and writing prompts | Which step to do first in the AI client; whether the user needs to create/open a project before pasting the prompt; which materials are truly needed today |
| `/docs` | Thorough description of use cases, review rules, inputs, privacy, and routes | Client-specific connection and local-folder setup are not the first thing a new user sees |

At the captured desktop size (1920 × 957), the large hero consumes much of the opening view and pushes setup steps down. At 390 × 844, the `/start` hero and the beginning of step 01 fill the opening screen; the first step is cut off at the bottom. The rendered `/start` page is about 4,900 CSS pixels tall and includes three additional copyable prompts after the starter prompt. The content is useful; its first-run ordering and density are the problem.

### Clean-environment test from the earlier audit

The earlier Argon clean-environment run established that the basic connection path is viable:

- MCP `initialize` / `tools/list` negotiation succeeded.
- Workspace-template and application-kit retrieval succeeded.
- The strict local workspace boot check passed in a clean temporary workspace.
- The tested Argon environment had Node.js and Python available.
- It did not have Poppler, `latexmk`, or `python-docx` installed. These should be treated as optional, task-specific document-processing dependencies unless a particular output path genuinely requires one; they should not be presented as prerequisites for connecting to the MCP or creating the basic workspace.

This is positive evidence that the MCP service itself is not the primary first-run blocker. It does **not** prove that every AI client, operating system, plan, optional document conversion, or phone-to-computer workflow works without additional setup.

### Relevant current implementation locations

The public pages are rendered in `src/index.ts`:

- Homepage CTA: around line 1355.
- Homepage “install the kit” wording: around line 1401.
- Homepage final call to action: around line 1413.
- Starter prompt: around line 1419.
- `/start` heading and four setup cards: around lines 1444–1447.
- Starter prompt panel: around line 1451.
- Docs page renderer: starts around line 1507.

These are proposed update locations only. No changes have been made to them.

## The five onboarding issues

### 1. The guide URL and the MCP connection endpoint are easy to confuse

The homepage presents `https://jobmcp.pmlecuong.com/` as an “Agent URL” to copy into Codex/Claude. The site also says “Give the AI this URL.” But reading the public website is not the same as registering the MCP server in an AI client. The transport endpoint is `https://jobmcp.pmlecuong.com/mcp`.

**Risk:** A new user pastes the public website into a normal chat, expects tools to be connected, and receives questions or errors because the client has not actually configured the MCP server.

**Recommendation:** Give the two URLs different names and jobs:

- **Setup guide:** `https://jobmcp.pmlecuong.com/` — explains the workflow and gives prompts.
- **MCP connection address:** `https://jobmcp.pmlecuong.com/mcp` — add this in a compatible client’s MCP settings.

The page must say plainly: “Copying a prompt does not connect Job MCP. Connect it once in your AI app first.” Provide the exact setup steps for each supported client instead of implying that one URL works identically everywhere.

### 2. The user is told to create a folder, but not shown how to get the AI into it safely

The current page says “Create a clean project folder,” but does not provide the first-time user with a client-specific route to create/select that folder and open it as the AI’s workspace. A remote MCP service cannot create a directory on the user’s computer by itself; the local client must already have permission and a working folder context.

**Risk:** The user starts from a general conversation with no project open, gives the agent a vague request, and then faces permission prompts or follow-up questions they do not understand.

**Recommendation:** Explain the minimum safe sequence: create or select one dedicated folder such as `Documents/Job Applications`, open that folder in the local-capable client, and allow access only to that folder. The AI can create subfolders inside the selected workspace. Do not encourage “full permission” to all Documents or the whole computer. If the user has not opened a folder, the prompt should ask the client to guide them to do that before it tries to write files.

### 3. “Codex, VS Code, Claude, or another” hides important client and plan differences

The `/start` page names several clients as if they offer the same capabilities. They do not. MCP connection setup is client-specific, and local file access is separate from MCP access.

OpenAI’s current documentation says desktop workflows can access a user-opened local folder when access is granted; ChatGPT web/mobile do not directly access files on the user’s computer. Supported desktop Codex chats can be continued from the ChatGPT mobile app’s Remote tab, but that is remote control/continuation of a desktop task—not direct MCP setup on mobile. Custom MCP apps in ChatGPT are currently documented as web-only, with plan/workspace restrictions; direct mobile use is not documented as supported. These product details can change and should be rechecked before publication.

**Risk:** A phone-only ChatGPT user or a user on an ineligible plan follows instructions that cannot work in their current surface. A user may also believe signing in to a website gives an AI client local-folder access.

**Recommendation:** Add a short “Where are you working?” choice with a recommended path for **Codex on a computer** and separate, honest guidance for ChatGPT web, ChatGPT mobile/Remote, and other clients. Clearly label unsupported or limited paths. Do not promise that a browser sign-in, pasting the site URL, or mobile access automatically connects a laptop’s local files.

### 4. The first-run page asks users to absorb too much before they can start

The setup page includes four cards, an expansive material checklist, and four separate prompt use cases (starter, job application, ATS, writing). It contains necessary guidance, but the beginner must decide which material to find and which prompt to use before getting one clear success.

**Risk:** Users delay, paste the wrong prompt, or think they must prepare a complete CV, job description, samples, certificates, photo, and signature before they can begin.

**Recommendation:** Make the first task small: connect the client, open the dedicated folder, copy one setup prompt, and provide the CV/profile information they already have. Ask for a job description when they start a specific application. Keep writing samples as recommended; photo and signature as optional. Preserve the full checklist and the ATS/interview/writing prompts lower on the page under “Already set up?” or expandable “More help” sections.

### 5. Prerequisites and recovery are not explained at the moment they matter

The clean Argon run showed Node.js and Python were available but Poppler, `latexmk`, and `python-docx` were not. The core MCP/workspace bootstrap passed, while those packages can matter for some optional conversion/rendering tasks. The public onboarding currently does not make that distinction clear or give a beginner a simple recovery path when a later task asks for a missing tool.

**Risk:** A user sees a package/dependency error and concludes the whole MCP setup is broken, or is asked to install tools without understanding whether they are essential or optional.

**Recommendation:** State that connecting Job MCP and creating the base workspace do not require installing every document tool. Detect or explain a missing dependency only when the user chooses the specific task that needs it. Provide OS-specific, copyable installation steps, a “skip this optional output” route, and a recovery message that says what failed, what still works, and what the user can do next. Never make an optional converter appear required for ATS or writing checks.

## Recommended fix order

This order addresses the highest-probability blockers first, then improves confidence and recovery. It deliberately avoids an auth/database project.

| Priority | Change | Why this order | Done when |
|---|---|---|---|
| **P0.1 — Clarify connection** | Separate the setup-guide URL from the `/mcp` endpoint; explain that prompt-copying does not configure a client; add supported-client connection instructions | Without a real MCP connection, the user cannot access MCP tools at all | A beginner can identify which address goes in client settings and can verify that tools are available before continuing |
| **P0.2 — Establish a safe local workspace** | Put “create/select one folder and open it in your local-capable AI client” before the starter prompt; explain folder-only permissions | The local agent cannot safely create the job workspace without a selected writable location | The client has an open dedicated folder; the agent creates only within it; no whole-computer permission is requested |
| **P1.1 — Simplify the first run** | One recommended path and one setup prompt; defer detailed inputs and specialist prompts until after setup | Reduces cognitive load without deleting necessary material or review guidance | New user can complete first setup without choosing among several prompts or collecting optional files |
| **P1.2 — Add client capability matrix** | Distinguish Codex desktop/local workspace, ChatGPT web MCP availability, phone-only limitations, Remote continuation, and other verified clients | Prevents following impossible instructions and keeps claims accurate | Every published path is explicitly tested and has an accurate support/limitation label |
| **P1.3 — Add dependency and error recovery** | Separate core setup from optional conversion tools; add OS-aware help and safe skip paths | The connection should not appear broken because an optional PDF/DOCX tool is absent | Missing optional dependency produces a task-specific explanation and does not block unrelated tools |
| **P2 — Improve mobile scanning and measure friction** | Keep first action near the top; collapse details; test narrow layouts; add privacy-safe onboarding event counts | Validates whether changes improve completion and identifies the next real blocker | Mobile users can see the primary next action; aggregate metrics distinguish connection/setup from checker use without collecting document text |

**Recommended first release:** P0.1 + P0.2 + P1.1 as one focused onboarding improvement. P1.2 is required before advertising more than the tested client path. P1.3 and P2 follow as the recovery/measurement pass. The current free tools remain anonymous and available under their existing server rules.

## Proposed first-run page structure and copy direction

Keep the current visual identity. Change the hierarchy, not the brand.

### Opening block

**Headline:** “Start your job-application workspace”
**Subheading:** “Connect Job MCP once, open one private folder on your computer, then let your AI guide you through the first step.”

Primary action: **“Set up with Codex on my computer”**. Secondary links: **“I use ChatGPT in a browser”**, **“I’m on my phone”**, and **“I use another MCP client”**—each opening only verified instructions.

### Four visible beginner steps

1. **Choose your AI app.** The app is where you talk to the AI; Job MCP is the set of tools it can call.
2. **Connect Job MCP once.** Add the MCP address in that app. Copying a prompt alone does not connect it.
3. **Open one private folder.** Use a dedicated job-application folder and grant access only to that folder.
4. **Copy the setup prompt.** Start with your existing CV/profile. You can add a job description later.

### Short privacy statement, with detail available

“Your CV and job files stay in the local workspace. The MCP cannot browse your computer. When you request a check, the AI client sends the selected text needed for that check.” Link to the full privacy page and retain all existing precise privacy details there.

### Keep the detailed material

Do **not** remove the source-material guidance, CV review rules, ATS safeguards, optional interview preparation, writing modes, or privacy controls. Move them below the first success path, organize them by the user’s next task, and use expandable sections where appropriate. A concise first screen should not mean weaker review or safety rules.

### Diagram idea

Use a small, plain-language four-step diagram (HTML/CSS or accessible SVG), not technical PlantUML in the onboarding hero:

```text
You choose a client → connect Job MCP → open one private folder → ask for help
                                     ↘ only selected check text is sent when requested
```

The diagram should reinforce the local-vs-remote boundary and work at phone width. Keep the technical protocol diagram on `/technical-flow`.

## Proposed source-file update map

| File/page | Proposed work |
|---|---|
| `src/index.ts` homepage around 1355 | Make “Start setup” explicitly mean client setup; retain “See examples” as secondary |
| `src/index.ts` homepage around 1401 | Replace “install the kit” with accurate wording such as “Connect Job MCP and prepare one local workspace” |
| `src/index.ts` homepage around 1413 | Update final CTA so it no longer implies that an empty folder plus root URL alone completes connection |
| `src/index.ts` starter prompt around 1419 | Keep one setup prompt; instruct the agent to verify client connection and folder context first, request permission only for the selected workspace, then ask for available profile/CV material |
| `src/index.ts` `/start` around 1444–1451 and following content | Reorder into the four-step beginner path; place source-material and task-specific prompts after setup; preserve their substantive requirements |
| `src/index.ts` `renderDocsPage()` around 1507 | Add “Getting started by client” near the top; preserve detailed behavior/privacy documentation below |
| `README.md` | Keep developer-facing distinction between public guide root and `/mcp` transport endpoint accurate; do not confuse this with user instructions |
| Existing tests under `tests/` | Add route/content assertions and end-to-end tests for the first-run paths; do not change auth tests or auth plan |

No change to `docs/optional-google-oauth-account-path-plan.md` is included in this proposal.

## Test plan and acceptance criteria for a later implementation

### First-time-user journeys

Write manual test cases before automating, then execute complete browser flows—not just heading-presence checks:

1. **Codex desktop, no folder open:** user reaches the setup page, understands that MCP connection is a separate step, connects to `/mcp`, creates/opens one dedicated folder, copies the starter prompt, and completes a base workspace setup.
2. **Codex desktop, folder already open:** user can start without being told to recreate it; the agent verifies folder scope and does not overwrite user files.
3. **ChatGPT web:** user sees accurate MCP availability/plan caveats and is not promised access to local computer files.
4. **Phone-only:** user sees the direct limitation and a safe next step; if using Remote to a paired desktop task, the copy labels it as remote continuation, not mobile MCP setup.
5. **Missing CV:** agent can ask for profile/work-history facts rather than blocking or inventing facts; the user understands that a job description is needed later for tailoring/ATS.
6. **Missing optional converter:** connection and unrelated tools still work; the error identifies the one optional task affected and gives a skip/recovery path.
7. **Permission boundary:** user is never told to give full-disk or whole-Documents access; only the selected workspace is used.
8. **Copy controls:** each button copies the prompt matching its visible task, with keyboard and screen-reader labels.

### Engineering/UI checks

- Unit/content tests confirm root-vs-`/mcp` URLs are correctly labelled, specialist prompts remain available, and privacy language does not overclaim.
- Playwright covers all public onboarding routes and full journeys with a clean browser context; retain screenshots and trace for failures.
- Test desktop and narrow viewport layouts (390 px, 430 px, and desktop): primary action visible near the top, no horizontal overflow, no cut-off buttons, expandable content operable.
- Test keyboard navigation, focus visibility, semantic headings, and accessible names for copy/expand controls.
- Run the existing `npm test` and clean local-kit regression; no weakening of strict boot or privacy checks to make onboarding pass.
- Before any production release, follow the repository release checklist in `MAINTENANCE_NOTES.md`: local tests, local-kit regression, production smoke test against the explicit `/mcp` URL, `/health`, visible footer/version check, and rollback readiness. This proposal itself performs no release.

### Success measures

First establish a baseline; do not invent targets from the owner-reported user mix. If privacy-safe event tracking is later approved, aggregate only:

- setup page viewed;
- client path selected;
- connection instructions opened;
- starter prompt copied;
- workspace template fetched;
- first checker called;
- categorized setup/connection failure;
- step abandonment by stage.

Do not collect CVs, job descriptions, prompt bodies, selected review text, checker responses, or raw local paths as onboarding analytics. Keep protocol events (initialize/discovery/tool listing) separate from meaningful setup/checker actions. The service must continue to explain that it cannot confirm a user completed a local application unless that user explicitly opts into a suitable, privacy-reviewed signal.

## Product and safety boundaries

- Keep the anonymous/free MCP path intact; this work adds no login, account, API key, quota, or dashboard change.
- The website is a guide, not a substitute for MCP setup in the client.
- The remote server cannot create or inspect local folders; the local AI client performs local file work only after the user opens/grants the selected workspace.
- Recommend least-privilege folder access. “Give full permission” is not the safe default.
- Keep full CVs and application folders local. Send only task-selected content for the requested ATS/writing check, consistent with the existing privacy contract.
- Preserve user confirmation, evidence-based claims, review loops, and optional-material distinctions.
- Do not promise support for a client/plan/device path until it has been verified end-to-end.

## OpenAI client notes to recheck before implementation/release

Product access changes. At the review date, official OpenAI documentation states:

- Desktop Work can open a local folder/project and grant access to only needed files; Work on web and mobile cannot directly access local computer files. Supported desktop Codex conversations can be accessed remotely from mobile.
- Custom MCP apps in ChatGPT are described as web-only and have plan/workspace availability restrictions; direct custom MCP use on mobile is not documented as supported.
- MCP client configuration is client-specific; OpenAI’s documented Codex setup uses an MCP server URL and verification step. The Job MCP service must direct compatible clients to `https://jobmcp.pmlecuong.com/mcp`, not leave users to infer which URL to use.

Re-check the official sources during implementation because feature availability can change:

- [OpenAI Help Center — ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275)
- [OpenAI Help Center — Creating custom MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-creating-custom-mcp-apps-in-chatgpt)
- [OpenAI Developers — Docs MCP and Codex configuration example](https://developers.openai.com/learn/docs-mcp)

## Decision requested before implementation

This document is a proposal, not approval to implement or deploy. The recommended first implementation slice is **P0.1 + P0.2 + P1.1**, with the existing free tools, MCP server behavior, auth plan, and privacy model held constant. Once approved, implement through the repository’s normal test/release process and validate the complete new-user journeys on the actual target clients.
