# Requirements Document: Resilient Local-First Application MCP

## Introduction

This feature upgrades the public Student Application AI Helper MCP into a resilient, local-first application workflow. It helps an AI agent create editable, evidence-grounded CVs and recruiter-ready cover letters without copying the private writing-checker logic to a student's machine.

The public endpoint remains unauthenticated. The student controls all private source files locally. The MCP receives only selected draft text for a writing review and a privacy-safe workspace manifest for structure/version audit.

### Prior-Art Record

| Source | Observed strength or risk | Decision for this feature |
| --- | --- | --- |
| `application-system/scripts/generate_application.py` | Strong fact/evidence boundaries, structured generation, PDF page gates, signature support | Reuse the evidence-first and durable validation pattern; do not expose Cuong-specific facts/templates. |
| `application-system/AGENTS.md` | Clear recruiter-safe application contract and page-limit rules | Adapt the gate discipline to a generic student workspace. |
| `experimental/application-package-mcp/src/index.ts` | Stateless public MCP, selected-text checker, public resource kit | Keep the service public and stateless; add manifest-only workspace auditing. |
| `experimental/application-package-mcp/resources/application-kit/` | Local PDF renderer and basic validation, but no mandatory human-fit loop or editable HTML CV | Extend only local orchestration and public contracts. Keep private heuristics on Franklee. |

## Scope and Boundaries

Included:

- Phase-1 CV intake from PDF, DOCX, or HTML; Markdown extraction; editable HTML CV generation; source-layout reference rendering.
- Explicit role, supporting-document, voice, photo, and signature conversations.
- One mandatory CV review loop and three distinct cover-letter review loops.
- Public MCP manifest auditing, version reporting, safe-update guidance, and prompt-injection/abuse controls.
- Local workflow scripts, templates, contracts, tests, and operator documentation.

Deferred to Phase 2:

- Legacy binary `.doc` conversion.
- OCR of scanned/non-text PDFs.
- Automatic application to a job board or any external submission.

Explicitly excluded:

- Copying `src/checker.ts`, scoring thresholds, phrase lists, or private anti-abuse logic into the student kit.
- Storing candidate profiles, source CVs, photos, signatures, or generated application documents on Franklee.
- Claims that the checker proves authorship or bypasses AI detection.

## Discovery Inventory and Coverage Matrix

| Source item | Requirement ID | Role | Surface | Workflow state | Data/API/entity | Edge cases | Manual testcase | API/browser proof | Phase | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Existing CV in PDF/DOCX/HTML | R1-R4 | Candidate, local AI agent | `candidate/source`, extraction scripts | intake → extracted → reviewed | local source, Markdown, page images | unsupported extension, no extractable text | MT-01 | CLI fixture + rendered-page inspection | 1 | included |
| Role, evidence and voice onboarding | R5-R9 | Candidate, local AI agent | `profile/`, `voice/` | incomplete → ready/risk-reported | profile/evidence/voice files | no supporting docs, generic voice consent | MT-02 | CLI fixture | 1 | included |
| Employer achievement curation | R7A-R7C | Candidate, local AI agent | `profile/`, `candidate/` | prompted → supplied/skipped → reusable evidence | employer evidence inventory | fewer than 10 bullets, user skip, AI-sounding bullets | MT-02A | CLI fixture | 1 | included |
| Career-coach orientation and voice | R5A-R5C | Candidate, local AI agent | `AGENTS.md`, `README.md`, onboarding | unfamiliar → oriented → guided | public MCP resources, local workspace | confusion, missing files, overly forceful advice | MT-02B | template/CLI fixture | 1 | included |
| Photo / signature decisions | R10-R11 | Candidate, local AI agent | `candidate/source`, cover output | asked → provided/declined | asset status | no photo, missing signature | MT-03 | CLI fixture/output manifest | 1 | included |
| Editable CV and visual parity | R12-R14 | Candidate, local AI agent | `applications/<slug>/cv` | draft → one review → accepted | HTML/PDF/report | layout mismatch, overlong CV | MT-04 | browser screenshot + PDF page render | 1 | included |
| Cover-letter quality loop | R15-R18 | Candidate, local AI agent | `applications/<slug>/cover-letter` | draft → loop 1/2/3 → ready | draft hashes, MCP result records | repeated same draft, medium/high risk, no signature | MT-05 | CLI/integration fixture | 1 | included |
| Local Application SOP hard gate | R18A-R18F | Candidate, local AI agent | `application_sop.py`, `.application-sop/` | boot → task → evidence → close/recover | local state, snapshots, receipts, handoff | stale state, drift, bypass attempt, interrupted session | MT-05A | CLI/state fixture | 1 | included |
| Manifest audit and updater | R19-R23 | Local AI agent, MCP | `.mcp/`, MCP tool | preflight → current/action-required | manifest/update state | absolute paths, traversal, stale kit | MT-06 | MCP HTTP test | 1 | included |
| Prompt-injection and public-service abuse resistance | R24-R28 | Candidate, local AI agent, operator | client scripts, MCP schemas | every operation | untrusted document content | override/exfiltration strings, rate pressure | MT-07 | hostile-input unit/HTTP tests | 1 | included |
| Legacy workspace performance and drift audit | R29-R32 | Candidate, local AI agent | `application_sop.py`, legacy workspace, migration plan | baseline → diagnose → approve migration → verify | local inventory, timings, migration manifest | large folders, duplicates, stale outputs, protected sources | MT-08 | CLI fixture/performance report | 1 | included |
| `.doc` and OCR scans | D1 | Candidate | converter | deferred | source file | scanned/legacy files | future | future | 2 | deferred with reason |

## Requirements

### Requirement 1: Supported input declaration (R1)

**User Story:** As a candidate, I want the agent to tell me which CV formats are supported, so that I can provide a usable source document.

#### Acceptance Criteria

1. WHEN a CV workflow starts THEN the local agent SHALL request a CV in PDF, DOCX, or HTML for Phase 1.
2. IF the candidate supplies a legacy `.doc` or a scan-only PDF THEN the local workflow SHALL report that the format is deferred to Phase 2 and SHALL not silently fabricate extracted content.
3. WHEN a supported file is accepted THEN the workflow SHALL preserve the original under `candidate/source/` and SHALL never overwrite it.

### Requirement 2: Local conversion and source capture (R2)

**User Story:** As a candidate, I want my CV converted into usable structured material locally, so that the agent can tailor it without losing factual control.

#### Acceptance Criteria

1. WHEN a supported CV is supplied THEN the local converter SHALL produce a Markdown extraction and a structured source-analysis record.
2. WHEN text cannot be extracted reliably THEN the workflow SHALL create a clear blocker report and request a supported replacement or Phase-2 processing.
3. The converter SHALL keep candidate source text local and SHALL not send it to the MCP.

### Requirement 3: Source-layout reference (R3)

**User Story:** As a candidate, I want the editable CV to respect my existing format, so that tailoring does not destroy my document identity.

#### Acceptance Criteria

1. WHEN a PDF or DOCX source is supplied THEN the workflow SHALL create local page-image references before generating the editable HTML CV.
2. WHEN an HTML source is supplied THEN the workflow SHALL capture a browser screenshot reference before tailoring.
3. The agent SHALL compare section order, heading hierarchy, alignment, spacing rhythm, typography intent, and photo placement against the reference before declaring visual review complete.

### Requirement 4: Editable HTML primary output (R4)

**User Story:** As a candidate, I want an editable HTML CV, so that a future local AI agent can tailor it for a job description.

#### Acceptance Criteria

1. WHEN CV tailoring is requested THEN the workflow SHALL create `cv-tailored.html` as the editable primary output and a PDF derivative when local rendering is available.
2. The HTML SHALL derive claims only from verified local profile/evidence sources.
3. IF a requested JD skill is unsupported THEN the workflow SHALL place it in a gap report and SHALL not present it as candidate experience.

### Requirement 5: Role and research intake (R5)

**User Story:** As a candidate, I want the agent to understand my target role, so that advice and tailoring are relevant.

#### Acceptance Criteria

1. WHEN a new application starts THEN the agent SHALL ask for the target role, job description or URL, location constraints where relevant, and role family or closest equivalent.
2. The agent SHALL explain which evidence would strengthen the selected role before drafting a serious application.

### Requirement 5A: Career-coach personality and communication contract (R5A)

**User Story:** As a candidate, I want a practical and encouraging career-coach interaction, so that I understand how to build a stronger application without feeling judged or overwhelmed.

#### Acceptance Criteria

1. The workspace template SHALL include a user-facing Markdown contract that defines the local AI agent as a calm, practical, evidence-first career coach.
2. WHEN discussing an application THEN the agent SHALL lead with the most useful next action, explain why it matters in plain language, and offer focused questions that improve factual depth, role fit, or authentic voice.
3. The agent SHALL be encouraging without exaggerated praise, transparent about uncertainty, and direct when evidence, language fit, visual quality, or recruiter readiness is weak.
4. The agent SHALL distinguish a recommendation from a requirement and SHALL respect an informed user choice to skip optional inputs or proceed with stated risks.
5. The agent SHALL never claim to be a recruiter, guarantee an interview/outcome, invent qualifications, or present private checker feedback as an authorship verdict.

### Requirement 5B: Plain-language MCP and workspace orientation (R5B)

**User Story:** As a candidate, I want to understand how the local workspace and public MCP work, so that I know what stays private, what I need to provide, and what the system will do next.

#### Acceptance Criteria

1. On first setup, and whenever the candidate asks, the agent SHALL explain in plain language that source files remain on the local computer; only selected draft text is sent to the public checker; and the checker returns high-level feedback rather than the private implementation.
2. The local `README.md` and `AGENTS.md` SHALL identify the folders the candidate should focus on: `candidate/source/`, `profile/`, `voice/writing-samples/`, `jobs/`, and `applications/`.
3. The orientation SHALL explain the purpose of each folder, the minimum materials to provide, optional materials that improve quality, and the artifacts the workflow will create.
4. The orientation SHALL state that the remote MCP cannot browse the candidate's files; the local agent creates a privacy-safe structure/version manifest for the optional remote audit.
5. The orientation SHALL explain the review gates: one CV review loop, three cover-letter loops, and honest reports when a document still falls below standard.

### Requirement 5C: Guided preparation checklist (R5C)

**User Story:** As a candidate, I want a clear preparation checklist, so that I can improve my package systematically.

#### Acceptance Criteria

1. WHEN onboarding or starting a new job application THEN the agent SHALL present a concise, prioritized checklist of materials already available, materials still needed, and optional materials with expected benefit.
2. The checklist SHALL include: current CV, target job description/URL, target role, employer bullet inventory, supporting evidence, writing samples, photo decision, and signature decision for a cover letter.
3. The agent SHALL tailor the checklist to the selected role and current workspace state instead of showing a generic exhaustive list on every interaction.
4. IF the candidate is missing important inputs THEN the agent SHALL explain the likely impact on the CV/cover letter and propose the smallest useful next contribution.

### Requirement 6: Supporting-document and voice intake (R6)

**User Story:** As a candidate, I want to supply materials that reflect my actual experience and voice, so that documents are less generic and more accurate.

#### Acceptance Criteria

1. WHEN source CV intake completes THEN the agent SHALL invite optional supporting documents and authentic writing samples.
2. IF the candidate provides no voice material THEN the agent SHALL warn that role-appropriate generic voice is less personal and less reliable for authenticity.
3. IF the candidate chooses generic voice THEN the workflow SHALL record that consent locally.

### Requirement 7: Evidence and claim boundary (R7)

**User Story:** As a candidate, I want the system to avoid invented experience, so that my application remains truthful.

#### Acceptance Criteria

1. The workflow SHALL maintain a local evidence library and claim-boundaries file.
2. WHEN a claim lacks local evidence THEN the workflow SHALL ask a candidate question, remove the claim, or mark it as an unresolved gap.
3. A job description SHALL define target requirements only and SHALL never become evidence of a candidate claim.

### Requirement 7A: Authentic employer-bullet curation (R7A)

**User Story:** As a candidate, I want clear guidance to capture my real experience in my own words, so that future applications can select authentic evidence instead of inventing or flattening my work history.

#### Acceptance Criteria

1. WHEN the local profile is being completed or refreshed THEN the agent SHALL list every employer or meaningful work placement currently known from the candidate's source CV/profile.
2. FOR EACH listed employer THEN the agent SHALL recommend that the candidate personally writes at least 10 distinct achievement, responsibility, project, or problem-solving bullets in their own natural voice; it SHALL recommend 15 where the candidate can provide them.
3. The agent SHALL explain that these bullets are source material, not final CV copy, and SHALL encourage the candidate not to use AI to write them so the facts, vocabulary, and tone originate with the candidate.
4. The agent SHALL ask for concrete context where possible: what changed, who was involved, tools/systems used, constraints, decisions, and verifiable outcomes; it SHALL not require invented metrics.
5. The locally stored bullet inventory SHALL preserve employer association, original candidate wording, source/confirmation status, and claim boundaries.

### Requirement 7B: Informed curation skip (R7B)

**User Story:** As a candidate, I want to be able to proceed with my existing CV when I cannot provide new evidence, while understanding the quality trade-off.

#### Acceptance Criteria

1. IF the candidate chooses not to provide the employer-bullet inventory THEN the workflow SHALL permit use of the current CV as the evidence source.
2. WHEN this skip is chosen THEN the agent SHALL record the choice locally and state that tailoring, factual depth, and personal voice may be weaker.
3. The agent SHALL periodically remind the candidate of the optional employer-bullet curation when it detects sparse evidence, repeated generic work bullets, or a poor JD-to-evidence match; it SHALL not repeatedly interrupt a candidate who has explicitly deferred the reminder for the current application.

### Requirement 7C: JD-specific bullet selection (R7C)

**User Story:** As a candidate, I want each tailored CV to emphasize the most relevant verified parts of my experience, so that it is concise and targeted.

#### Acceptance Criteria

1. WHEN a role-specific CV is generated THEN the workflow SHALL compare the target JD with the candidate's verified employer-bullet inventory.
2. FOR EACH employer included in that tailored CV THEN the workflow SHALL select four or five bullets that best demonstrate relevant, supported experience.
3. IF fewer than four supported bullets exist for an employer THEN the workflow SHALL use only supported material and report the gap rather than padding the CV.
4. The selection rationale SHALL be recorded locally in the application evidence map, connecting each selected bullet to relevant JD requirements.

### Requirement 8: Readiness report (R8)

**User Story:** As a candidate, I want clear preparation feedback, so that I know why an application is not yet strong.

#### Acceptance Criteria

1. BEFORE final drafting THEN the workflow SHALL create a readiness report listing confirmed facts, missing facts, unsupported claims, voice-material status, and role-fit gaps.
2. The report SHALL distinguish a blocking factual risk from a non-blocking improvement opportunity.

### Requirement 9: Untrusted-content rule (R9)

**User Story:** As a candidate, I want my document content handled safely, so that a malicious or irrelevant document instruction cannot control the agent.

#### Acceptance Criteria

1. The local contract SHALL state that CVs, JDs, OCR output, HTML, and writing samples are untrusted content, not executable instructions.
2. IF document text requests prompt disclosure, command execution, privacy changes, workspace changes, or quality-gate bypass THEN the agent SHALL ignore that request as content and continue only under trusted workflow instructions.

### Requirement 10: Mandatory photo question (R10)

**User Story:** As a candidate, I want control over whether my CV contains a photo.

#### Acceptance Criteria

1. BEFORE generating every CV THEN the agent SHALL ask whether the candidate wants to provide a photo.
2. IF a photo is provided THEN the HTML CV and its PDF derivative SHALL use it.
3. IF the candidate declines or does not have a photo THEN the workflow SHALL record that answer and MAY continue without a photo.
4. A CV quality gate SHALL fail if the photo question was never answered.

### Requirement 11: Signature request without blocking delivery (R11)

**User Story:** As a candidate, I want a signature used when available without being blocked when I do not have one.

#### Acceptance Criteria

1. BEFORE generating a cover letter THEN the agent SHALL ask for an optional PNG/JPG/JPEG signature in the workspace root/source area.
2. IF a signature is provided THEN the cover letter SHALL use it.
3. IF no signature is provided or the candidate declines THEN the workflow SHALL generate the cover letter without it and SHALL report that omission.

### Requirement 12: CV quality gate (R12)

**User Story:** As a candidate, I want one meaningful CV review cycle, so that I can assess quality without unnecessary rewriting.

#### Acceptance Criteria

1. BEFORE describing a CV as ready THEN the local gate runner SHALL record one selected-text MCP review against the current CV draft.
2. The review record SHALL include a draft hash, high-level result, issues, revision guidance, timestamp, and whether a revision occurred.
3. IF the review remains below the stated standard THEN the agent SHALL report the exact shortcomings and recommended repairs.
4. IF the candidate accepts those shortcomings THEN the workflow SHALL record acceptance and proceed without falsely reporting a pass.

### Requirement 13: CV visual and print review (R13)

**User Story:** As a candidate, I want the final CV to be readable and visually reviewed.

#### Acceptance Criteria

1. WHEN an HTML CV is generated THEN the workflow SHALL produce browser screenshot evidence and print/PDF evidence where supported.
2. IF visual comparison finds material hierarchy, overflow, photo, or section-order drift THEN the workflow SHALL report the discrepancy before final acceptance.

### Requirement 14: CV privacy boundary (R14)

**User Story:** As a candidate, I want a tailored CV without publishing my full profile to the MCP.

#### Acceptance Criteria

1. The CV workflow SHALL send only the selected review text to `check_writing_human_fit` or `suggest_writing_revision`.
2. It SHALL not send the source CV, profile JSON, evidence library, photo, signature, or generated PDF to the public service.

### Requirement 15: Three distinct cover-letter loops (R15)

**User Story:** As a candidate, I want a cover letter to receive resilient multi-pass review before it is called ready.

#### Acceptance Criteria

1. BEFORE describing a cover letter as ready THEN the local gate runner SHALL record exactly three mandatory review loops.
2. Each loop SHALL send selected current draft text to the MCP and save only the bounded result locally.
3. Each successive loop SHALL use a distinct draft hash, unless the result explicitly records that no safe revision was possible and why.
4. The loops SHALL cover: factual grounding/JD relevance; natural voice/repetition/AI-like risk; final recruiter readiness/one-page/signature status.

### Requirement 16: Cover-letter readiness truthfulness (R16)

**User Story:** As a candidate, I want honest reporting rather than a misleading automated pass.

#### Acceptance Criteria

1. IF any mandatory cover-letter loop reports unresolved high-risk issues THEN the final report SHALL state that the letter does not meet the standard and identify the issues.
2. The workflow SHALL not claim that a letter is undetectable as AI-written, guaranteed to be human-written, or guaranteed to pass a third-party detector.

### Requirement 17: Cover-letter physical validation (R17)

**User Story:** As a candidate, I want a usable recruiter-facing document.

#### Acceptance Criteria

1. WHEN cover-letter PDF generation is available THEN the local renderer SHALL enforce one-page maximum and safe PDF checks.
2. IF the PDF overflows THEN the local workflow SHALL shorten content rather than reduce the fixed layout below readable standards.

### Requirement 18: Local-only orchestration (R18)

**User Story:** As an operator, I want the local kit to enforce workflow gates without copying the server’s secret sauce.

#### Acceptance Criteria

1. The student kit SHALL include only a generic MCP client, gate recorder, workspace auditor, templates, and public contracts.
2. The student kit SHALL not include checker source, raw thresholds, hidden phrase lists, private prompts, or scoring explanations.

### Requirement 18A: Dedicated local Application SOP (R18A)

**User Story:** As a candidate, I want the local agent to follow a durable hard-gated process, so that it cannot casually skip evidence, review loops, or recovery steps when creating my application.

#### Acceptance Criteria

1. The student workspace SHALL include a dependency-light `application_sop.py` as the primary local control plane; `AGENTS.md` and any optional `agent.yaml` SHALL remain supporting instructions only.
2. `application_sop.py` SHALL be designed from the SiriusAgent SOP pattern of boot, task state, checkpoints, evidence, drift audit, handoff, and postflight, but SHALL be scoped to one candidate workspace and application-document work.
3. The SOP SHALL store all operational state locally under `.application-sop/`; this state SHALL be excluded from public MCP requests and from any default bundle/update operation.
4. The SOP SHALL never contain, download, or reproduce private MCP checker rules, thresholds, phrase lists, prompts, or scoring implementation.

### Requirement 18B: Mandatory boot and strict preflight (R18B)

**User Story:** As a candidate, I want every material application action to begin from a verified state, so that an interrupted or confused agent does not continue blindly.

#### Acceptance Criteria

1. BEFORE any state-changing application operation—including workspace setup, source ingestion, profile/evidence update, conversion, CV generation, cover-letter generation, quality-loop recording, finalization, or safe update—the supplied local workflow SHALL require `python3 application_sop.py boot --strict`.
2. `boot --strict` SHALL display current task/status, print a concise recovery brief, verify the workspace manifest/current kit compatibility, and audit the defined application-workspace inventory against the last accepted snapshot.
3. IF unexpected drift, a missing required file, an incomplete prior task, a stale mandatory audit, or an unresolved blocking risk exists THEN strict boot SHALL exit non-zero and SHALL name the next safe corrective command.
4. A read-only explanation or status request MAY run without a task, but it SHALL not generate, overwrite, mark ready, or send review content.

### Requirement 18C: Task state, locking, and durable evidence (R18C)

**User Story:** As a candidate, I want every important workflow action to have an auditable local record, so that another agent session can resume safely.

#### Acceptance Criteria

1. The SOP SHALL require an active task and work session before material application work proceeds.
2. State changes SHALL use an inter-process lock and atomic write/replace semantics so concurrent or interrupted processes cannot silently corrupt state.
3. The state model SHALL include: schema version, workspace/kit version, active task, application slug, phase, required decisions, required evidence, command receipts, review-loop records, accepted snapshot, unresolved risks, candidate acceptance records, and handoff details.
4. Each completed critical command SHALL record timestamp, purpose, inputs by safe relative path, exit status, output paths, content hash where applicable, and a bounded log reference.
5. Completion evidence SHALL be an existing output file or recorded successful command result, not a prose assertion from the agent.

### Requirement 18D: Controlled command surface and release receipt (R18D)

**User Story:** As an operator, I want the hard gate to be difficult to bypass accidentally, so that “ready” has a reliable meaning.

#### Acceptance Criteria

1. The public client skill and workspace `AGENTS.md` SHALL require generation, conversion, MCP review, PDF/visual validation, and finalization to be invoked through `application_sop.py` subcommands.
2. The SOP SHALL use a fixed allowlist of its own subcommands and structured arguments; it SHALL not accept arbitrary shell strings for application operations.
3. Each final CV, cover letter, and application manifest SHALL include a local release receipt referring to the active SOP task, validation records, current draft hashes, and readiness result.
4. A finalization command SHALL fail unless the release receipt proves the applicable gate set: one CV loop for a CV; three distinct cover-letter loops for a cover letter; required user decisions; and visual/PDF checks when supported.
5. The SOP SHALL report `NOT READY` rather than produce a false success when records are missing, stale, mismatched to the current draft, or unresolved.
6. The documentation SHALL state honestly that a user or third-party AI client with direct filesystem access can manually bypass local scripts; the release receipt protects the supported workflow and makes a bypass visible, not cryptographically impossible.

### Requirement 18E: Snapshot, drift, and recovery handoff (R18E)

**User Story:** As a candidate, I want the application workflow to recover safely after interruption, context loss, or a new AI-agent session.

#### Acceptance Criteria

1. The SOP SHALL snapshot only the defined application-workspace inventory using safe relative paths and local hashes; it SHALL exclude transient logs, generated caches, source content text, and hidden secrets from reports sent remotely.
2. IF tracked files change after a snapshot THEN audit SHALL identify new, modified, and missing paths and SHALL require an explicit local acceptance or corrective action before strict work resumes.
3. Before an agent handoff, compaction, or end of a material session, the SOP SHALL record current state, exact next command, unresolved risks, and relevant output paths in a local human-readable recovery brief.
4. `postflight` SHALL validate the active task evidence, refresh the snapshot, write the recovery brief, and close the session unless explicitly retained.

### Requirement 18F: Reduced-scope governance and health (R18F)

**User Story:** As a candidate, I want resilience without a burdensome project-management system.

#### Acceptance Criteria

1. The Application SOP SHALL not import SiriusAgent team controls that are irrelevant to a private candidate workspace, including Git author/consumer modes, team changelog promotion, enterprise source-system verification, skill installation, or external-call audit trails.
2. The SOP SHALL provide a concise `health` command that reports readiness of the local application workflow: boot/snapshot freshness, active task consistency, required user decisions, evidence completeness, current manifest audit, and applicable review loops.
3. A readiness score SHALL be advisory; hard blocking SHALL depend on explicit required conditions rather than an opaque score.

### Requirement 19: Manifest-based workspace audit (R19)

**User Story:** As a local AI agent, I want to audit workspace readiness on each workflow call, so that I can guide users to a compatible structure.

#### Acceptance Criteria

1. BEFORE each application-workflow MCP invocation routed through the supplied local wrapper THEN the wrapper SHALL generate or refresh a local manifest and call `audit_workspace_manifest`.
2. The manifest SHALL contain only schema version, public kit version, safe relative paths, hashes of MCP-managed files, and photo/signature-question state.
3. The remote MCP SHALL never read the local filesystem directly.
4. IF the workspace is current and unchanged THEN the tool SHALL return a concise `workspace_current` result without unnecessary migration instructions.

### Requirement 20: Manifest validation and privacy (R20)

**User Story:** As a candidate, I want workspace audits not to expose private information.

#### Acceptance Criteria

1. The MCP SHALL reject absolute paths, traversal paths, backslash paths, oversized manifests, arbitrary document contents, and unrecognized schema versions.
2. The manifest contract SHALL prohibit names, CV text, job text, photos, signatures, absolute paths, and raw private file contents.

### Requirement 21: Update offer and safe migration (R21)

**User Story:** As a candidate, I want to keep the local kit current without losing my data.

#### Acceptance Criteria

1. The MCP audit SHALL return current kit version, missing managed paths, and update availability.
2. The local policy SHALL default to checking every session, notify only when action is needed, and not automatically apply updates.
3. IF a candidate opts into safe automatic updates THEN the updater SHALL change only MCP-managed scripts/templates/contracts after a local backup and changelog entry.
4. The updater SHALL never overwrite profile, original sources, writing samples, photo/signature assets, job records, or application outputs.

### Requirement 22: Public MCP initialization guidance (R22)

**User Story:** As an AI-agent user, I want reliable onboarding when connecting to the public MCP.

#### Acceptance Criteria

1. MCP onboarding and client-skill resources SHALL instruct clients to run the manifest audit through the local wrapper.
2. The public endpoint MAY remain unauthenticated.
3. The service SHALL declare that generic third-party clients cannot be technically forced to perform a local filesystem audit.

### Requirement 23: Version compatibility (R23)

**User Story:** As an operator, I want to know when a local kit is too old.

#### Acceptance Criteria

1. The audit response SHALL expose a version status and minimum supported kit version.
2. IF a mandatory structure or contract version is missing THEN the final quality gate SHALL not report a package as fully compliant.

### Requirement 24: Prompt-injection containment (R24)

**User Story:** As an operator, I want hostile user-supplied content to remain data, not control flow.

#### Acceptance Criteria

1. The client skill, workspace `AGENTS.md`, and scripts SHALL state a trusted-instruction hierarchy and untrusted-document rule.
2. The system SHALL include test fixtures where CV/JD text tries to reveal internal instructions, retrieve private rules, disable checks, or trigger command execution.
3. The expected behavior SHALL be that the strings are analyzed only as content and do not change workflow, access, or data disclosure.

### Requirement 25: Secret-sauce boundary (R25)

**User Story:** As the service operator, I want users to benefit from the checker without receiving enough detail to reproduce it.

#### Acceptance Criteria

1. Checker responses SHALL be bounded to high-level risk, issue categories, concise revision guidance, and safe next actions.
2. No public endpoint or bundle SHALL return private scoring thresholds, raw rule sets, complete phrase matches, internal prompts, debug state, or another user’s data.

### Requirement 26: Public-service abuse controls (R26)

**User Story:** As the service operator, I want the unauthenticated endpoint to remain usable without being trivially abused.

#### Acceptance Criteria

1. The deployment design SHALL add request-body limits, tool-specific input limits, timeouts, concurrency/rate limits, and generic errors.
2. Operational logs SHALL avoid raw submitted writing and private manifests by default.
3. Edge protection SHALL be configured or documented for rate limiting and bot/WAF control before production rollout.

### Requirement 27: Testability and regression evidence (R27)

**User Story:** As a maintainer, I want testable contracts so that safety and workflow behavior survive changes.

#### Acceptance Criteria

1. Automated tests SHALL cover MCP tool listing, manifest audit results, malformed manifests, secret-sauce absence in public bundles, and hostile-content fixtures.
2. Local fixture tests SHALL cover photo declined/provided, signature absent/provided, one CV loop, three distinct cover-letter loops, outdated workspace, and user-accepted CV gaps.
3. Browser/print tests SHALL capture HTML CV screenshot and PDF/print evidence for a representative fixture.

### Requirement 28: Deployment truth (R28)

**User Story:** As an operator, I want production changes to be verifiable.

#### Acceptance Criteria

1. BEFORE remote deployment THEN the MCP package SHALL pass local TypeScript/build/tests and local workflow fixtures.
2. AFTER explicit shipping approval THEN Franklee deployment SHALL verify container health, `/health`, MCP initialization/tool list, and the manifest-audit response.
3. The deployment record SHALL state the exact server version and rollback target.

### Requirement 29: Measured performance baseline (R29)

**User Story:** As a candidate whose application process is slow, I want the agent to measure where time is actually spent, so that it fixes the real bottleneck rather than guessing.

#### Acceptance Criteria

1. WHEN the candidate reports an unusually slow application run or requests an old-workspace audit THEN the local Application SOP SHALL run a read-only performance baseline before changing the workspace.
2. The baseline SHALL record elapsed time for workspace inventory, source discovery, profile/evidence load, job intake, conversion, generation, each MCP review call, PDF/visual validation, and finalization.
3. The report SHALL distinguish observed timings from inferred causes and SHALL state when the available evidence is insufficient to attribute the delay.
4. The report SHALL remain local and SHALL exclude raw CV/JD text, photo/signature data, and private checker feedback details.

### Requirement 30: Legacy workspace structural and drift audit (R30)

**User Story:** As a candidate with a long-used, scattered workspace, I want the agent to understand its actual structure and compare it with the optimal current layout, so that it can make the workflow faster and easier to maintain.

#### Acceptance Criteria

1. WHEN a legacy workspace is nominated by the candidate THEN the SOP SHALL audit it locally using a read-only allowlisted inventory before any migration.
2. The audit SHALL compare the actual tree against the current ideal workspace contract and report: missing required files, misplaced source/evidence/job/output files, duplicate or stale generated outputs, unusually large directories, excessive file counts, orphaned temporary/cache artifacts, and outdated kit/contract versions.
3. The audit SHALL identify likely performance contributors such as broad recursive scans, repeated conversion of unchanged sources, repeated PDF/browser rendering, duplicate evidence search locations, and stale output discovery; it SHALL not label any item as causal without measured timing evidence.
4. The agent SHALL explain findings in simple candidate-facing language and recommend the smallest safe improvement first.

### Requirement 31: Safe migration and optimization plan (R31)

**User Story:** As a candidate, I want help improving an old workspace without losing my CV history or documents.

#### Acceptance Criteria

1. AFTER the read-only audit THEN the SOP SHALL generate a local migration/optimization plan with a proposed path mapping, expected benefit, risk level, and whether the action needs candidate approval.
2. The plan SHALL never delete, overwrite, or silently relocate original CVs, evidence, writing samples, photos, signatures, job records, or previous application outputs.
3. Before any non-safe migration action THEN the agent SHALL present the plan and request explicit approval.
4. Approved moves SHALL be copy-first or reversible, recorded in a migration manifest, and verified with source and destination hashes before the old location is considered archival.
5. Temporary/cache cleanup SHALL use a defined allowlist and a recoverable location where practical; unknown files SHALL be reported, not removed.

### Requirement 32: Performance verification and ongoing hygiene (R32)

**User Story:** As a candidate, I want proof that the workspace improvement helped and protection against future drift.

#### Acceptance Criteria

1. AFTER an approved migration or optimization THEN the SOP SHALL rerun the same baseline workflow and report before/after timings by stage.
2. IF the runtime has not improved materially THEN the report SHALL identify the next measured bottleneck rather than claiming the folder cleanup solved it.
3. The `health` and workspace-audit outputs SHALL include concise hygiene signals: current kit version, stale-output count, duplicate-source warning, large-directory warning, and whether a performance baseline is stale.
4. The supported workflow SHALL avoid broad workspace scans during normal generation by using a maintained index/manifest and content hashes to reuse unchanged extraction/rendering outputs.

## Quality Attributes

- Privacy: candidate documents and assets stay local by default.
- Integrity: no fabricated claims; supported evidence is traceable.
- Resilience: quality reports persist per output; failures produce actionable status.
- Accessibility/readability: generated HTML and PDF are visually inspected for hierarchy and overflow.
- Compatibility: current public clients continue to use the existing check tools; the new audit is additive.

## Non-goals / Deferred Work

| ID | Item | Reason |
| --- | --- | --- |
| D1 | Legacy `.doc` conversion | Requires controlled office conversion and compatibility fixtures; out of Phase 1. |
| D2 | OCR scan conversion | Needs OCR confidence and correction workflow; out of Phase 1. |
| D3 | Automatic remote deployment | Deployment follows only after local validation and explicit shipping approval. |

## Manual Testcase Intent

- `MT-01`: ingest PDF, DOCX, HTML and reject/defer `.doc`/scan-only input safely.
- `MT-02`: validate full evidence/voice onboarding and generic-voice consent.
- `MT-02A`: list known employers, request 10 self-written bullets per employer (15 recommended), record a skip, and select four or five supported bullets against a fixture JD.
- `MT-02B`: verify first-run career-coach orientation explains privacy, MCP boundaries, required folders, materials, review loops, and a role-specific preparation checklist.
- `MT-03`: validate photo and signature conversation states.
- `MT-04`: compare source visual reference with editable HTML and print/PDF output.
- `MT-05`: prove one CV record and three distinct cover-letter-loop records.
- `MT-05A`: prove strict boot blocks drift and incomplete state; prove locked/atomic state updates, an interrupted-session handoff, stale draft-hash rejection, a valid release receipt, and a direct-bypass warning.
- `MT-06`: prove current/outdated/unsafe workspace manifests.
- `MT-07`: prove hostile document content cannot alter control flow or disclose private checker details.
- `MT-08`: audit a fixture legacy workspace with scattered inputs, duplicate outputs, cache files, and stale kit metadata; verify read-only diagnosis, approval-gated copy-first migration, and before/after timing report.

Do the requirements look good? If so, we can move on to the design.
