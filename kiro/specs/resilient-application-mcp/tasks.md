# Implementation Plan: Resilient Local-First Application MCP

## Execution Constraints

- Execute one approved task at a time by default.
- Every task that changes the local student kit starts through `application_sop.py boot --strict` once that SOP exists.
- Do not deploy Franklee under this plan until the user explicitly asks to ship the validated change.
- Any future deployment starts only after local validation has passed and the user has explicitly approved shipping.
- Keep checker implementation, thresholds, rule lists, and private prompts server-only.
- Preserve all unrelated changes in the current CuongCV worktree.

- [ ] 1. Establish versioned contracts, fixture workspace, and manual test source of truth. _Requirements: R1-R18F, R19-R32_
  - [ ] 1.1 Create the revised workspace-template tree, public README/AGENTS career-coach contract, `.mcp` defaults, and Phase-1 supported-format/decision/evidence schemas. _Requirements: R1-R11, R18, R19-R23_
  - [ ] 1.2 Create the manual testcase source of truth at `qa/manual-testcases/resilient-application-mcp.md`, covering MT-01 through MT-08, including expected receipt fields and screenshot/PDF artifacts. _Requirements: R3, R10-R18F, R27, R29-R32_
  - [ ] 1.3 Create deterministic, sanitized fixtures for PDF/DOCX/HTML input, photo/signature states, employer-bullet curation, user-accepted CV risks, hostile document content, and scattered legacy workspace drift. _Requirements: R1-R18, R24-R32_
  - [ ] 1.4 Add contract/fixture validation tests that prove no fixture or public resource embeds checker source, private rule lists, or personal production data. _Requirements: R18, R25, R27_

- [ ] 2. Implement the local Application SOP foundation. _Requirements: R18A-R18F_
  - [ ] 2.1 Add dependency-light `application_sop.py` with typed schema validation, safe relative-path validation, OS file lock, atomic JSON write/replace, human-readable state mirror, and local-only state exclusion rules. _Requirements: R18A, R18C_
  - [ ] 2.2 Implement `boot --strict`, `start`, `status`, `health`, `handoff`, and `postflight`, including active-task/session consistency, snapshot/drift comparison, exact recovery command, and evidence-backed closure. _Requirements: R18B, R18C, R18E, R18F_
  - [ ] 2.3 Implement the fixed allowlisted command dispatcher and command receipts; reject arbitrary shell strings, unsafe paths, missing tasks, stale manifests, and missing evidence. _Requirements: R18C, R18D_
  - [ ] 2.4 Add unit tests for lock contention, interrupted write recovery, state/schema corruption, snapshot drift, handoff recovery, receipt evidence verification, and direct-artifact-without-receipt `NOT READY` handling. _Requirements: R18A-R18F, R27_

- [ ] 3. Implement local workspace auditing, legacy diagnosis, and safe migration planning. _Requirements: R19-R23, R29-R32_
  - [ ] 3.1 Add `workspace_audit.py` to construct an allowlisted, privacy-safe manifest and locally compare the current tree with the ideal workspace contract. _Requirements: R19, R20, R32_
  - [ ] 3.2 Add SOP `diagnose-workspace` timing spans for discovery, source loading, conversion, generation, MCP calls, rendering, and finalization; write local observed-versus-inferred performance reports. _Requirements: R29, R30_
  - [ ] 3.3 Add structure-drift rules for misplaced sources/evidence/jobs/outputs, duplicate or stale outputs, unusually large directories, caches, outdated kit versions, repeated unchanged conversion/rendering, and broad recursive scans. _Requirements: R30, R32_
  - [ ] 3.4 Add `migration-plan` and explicit `apply-migration` commands using copy-first operations, source/destination hashes, migration manifests, reversible archive handling, and no deletion of protected candidate materials. _Requirements: R21, R31_
  - [ ] 3.5 Add regression fixtures/tests that prove read-only diagnosis, no migration without approval, protected-source preservation, and before/after timing reports. _Requirements: R29-R32, R27_

- [ ] 4. Implement career-coach intake, evidence curation, and local source capture. _Requirements: R5-R11, R5A-R5C, R7A-R7C_
  - [ ] 4.1 Add first-run orientation and dynamic intake-status output covering MCP privacy boundaries, relevant folders, required/optional materials, role/JD, photo/signature decisions, and one-CV/three-cover review explanation. _Requirements: R5A-R5C, R19-R23_
  - [ ] 4.2 Add profile/evidence/claim-boundary data models and readiness report generation; enforce that JDs cannot create candidate claims. _Requirements: R5-R9_
  - [ ] 4.3 Add employer inventory extraction and user-authored bullet capture: list known employers, request 10 authentic bullets per employer, recommend 15, record skip/deferral, and preserve original wording plus claim boundaries. _Requirements: R7A, R7B_
  - [ ] 4.4 Add JD-to-evidence selection that selects four or five supported employer bullets, writes rationale to the evidence map, and reports shortages without padding. _Requirements: R4, R7C_
  - [ ] 4.5 Add tests for generic-voice consent, sparse-evidence reminder suppression after deferral, employer-bullet skip, unsupported JD skill handling, photo decision, and non-blocking signature absence. _Requirements: R6-R11, R7A-R7C, R27_

- [ ] 5. Implement Phase-1 CV ingestion and editable HTML CV production. _Requirements: R1-R4, R10, R12-R14_
  - [ ] 5.1 Add capability probes and documented local install guidance for Phase-1 PDF/DOCX/HTML processing; do not silently install packages or claim `.doc`/OCR support. _Requirements: R1, R2_
  - [ ] 5.2 Add local PDF/DOCX/HTML ingest adapters that preserve originals, create Markdown + structure analysis, create source visual references, and block safely on unextractable input. _Requirements: R1-R3_
  - [ ] 5.3 Add verified-evidence-based HTML CV builder with optional supplied photo handling, no-photo layout, JD-specific skill/bullet selection, and `cv-tailored.html` as the primary editable artifact. _Requirements: R4, R7C, R10_
  - [ ] 5.4 Add SOP build/visual-validation commands, PDF derivative where supported, source-to-output comparison report, and clear discrepancy/risk reporting. _Requirements: R3, R12-R14_
  - [ ] 5.5 Add fixture tests for PDF/DOCX/HTML success, unsupported `.doc`, scan-only block, photo supplied/declined, evidence gap, HTML artifact, and visual-reference artifact generation. _Requirements: R1-R4, R10, R12-R14, R27_

- [ ] 6. Implement the private-checker client boundary and quality-loop receipts. _Requirements: R12, R14-R18, R24-R25_
  - [ ] 6.1 Add `mcp_check_client.mjs` with bounded selected-text tool calls, manifest-audit calls, timeout/retry policy, generic failure handling, and no embedded scoring/rule logic. _Requirements: R14, R18, R19-R20, R25_
  - [ ] 6.2 Add one-current-draft CV review record, revision status, candidate risk acceptance record, and stale-draft hash invalidation. _Requirements: R12-R14_
  - [ ] 6.3 Add three distinct cover-letter loop records with fixed purposes, draft-hash progression, signature status, one-page/PDF validation linkage, and `no_safe_revision_possible` handling. _Requirements: R11, R15-R17_
  - [ ] 6.4 Implement receipt-gated `finalize-cv` and `finalize-cover-letter`; reject outdated manifest audits, missing decisions, missing visual/PDF evidence, incomplete review loops, and receipt/artifact hash mismatch. _Requirements: R12-R18F_
  - [ ] 6.5 Add integration tests for selected-text-only requests, one CV loop, three cover loops, repeated draft rejection, MCP outage/rate-limit block, user-accepted CV gap, and secret-sauce absence from local files/receipts. _Requirements: R12-R18, R24-R27_

- [ ] 7. Extend the public MCP with safe workspace auditing and abuse controls. _Requirements: R19-R28_
  - [ ] 7.1 Add the additive `audit_workspace_manifest` tool, version/migration response model, safe relative-path/hash schema, and compact `workspace_current` response. _Requirements: R19-R23_
  - [ ] 7.2 Update health/onboarding/client-skill/template resources to document local SOP preflight, privacy boundary, compatibility version, update policy, and third-party-client limitation. _Requirements: R5B, R18D, R22-R23_
  - [ ] 7.3 Add bounded HTTP body parsing, tool-specific request limits, request timeouts, concurrency/rate-limit middleware, generic errors, and redacted logging policy without changing public authentication. _Requirements: R20, R25-R26_
  - [ ] 7.4 Add MCP HTTP tests for tool compatibility, safe/unsafe/outdated manifests, bundle secrecy, hostile content, size/rate failure behavior, and no checker-internal response fields. _Requirements: R19-R28_

- [ ] 8. Add browser-visible document validation and evidence matrix. _Requirements: R3, R4, R10, R13, R17, R27_
  - [ ] 8.1 Create/update `qa/automation/playwright/resilient-application-mcp.spec.mjs` only after the manual testcase is approved; map every journey to the manual testcase IDs. _Requirements: R3, R13, R17, R27_
  - [ ] 8.2 Add semantic selector/testability contract for the local HTML preview/print surface, including photo/no-photo and document status states. _Requirements: R10, R13_
  - [ ] 8.3 Generate the UX coverage matrix at `output/playwright/resilient-application-mcp/ux-matrix.md`; run rebuilt local browser flows, screenshots, print/PDF checks, and source-reference comparison. _Requirements: R3, R4, R10, R13, R17, R27_
  - [ ] 8.4 Reconcile every document-visible acceptance criterion against manual and browser evidence; feed uncovered cases into the manual testcase and spec docs before closure. _Requirements: R3-R4, R10, R13, R17, R27_

- [ ] 9. Run local release verification and prepare a separate shipping handoff. _Requirements: R27-R28_
  - [ ] 9.1 Run the complete local test/build suite, fixture regression, MCP HTTP suite, Application SOP health/receipt verification, browser/print suite, strict UX-matrix validation, and requirements-to-evidence reconciliation. _Requirements: R27_
  - [ ] 9.2 Update local developer/operator documentation with supported commands, troubleshooting, performance diagnosis, safe migration, privacy model, and explicit non-bypassable-limitations statement. _Requirements: R18D, R26, R29-R32_
  - [ ] 9.3 Prepare—but do not execute—a BuilderOps deployment checklist: Franklee runtime inventory, rollback point, compose rebuild/restart command, public health/MCP verification, and post-deploy manifest-audit call. _Requirements: R28_

## Milestones

| Milestone | User-testable outcome | Automated proof | Manual testcase |
| --- | --- | --- | --- |
| M1 after task 2 | Local SOP can boot, block drift, recover, and refuse unsupported finalization | SOP unit tests | MT-05A |
| M2 after task 4 | Agent gives clear career-coach intake and captures evidence safely | intake/evidence fixtures | MT-02, MT-02A, MT-02B, MT-03 |
| M3 after task 6 | One CV loop / three cover loops create valid local receipts | client + SOP integration tests | MT-04, MT-05 |
| M4 after task 7 | Public MCP safely audits a manifest without receiving private files | MCP HTTP suite | MT-06, MT-07 |
| M5 after task 8 | Editable HTML CV is visually/print validated and coverage is recorded | Playwright + PDF artifacts | MT-01, MT-04 |
| M6 after task 9 | Legacy folder diagnosis shows measured bottlenecks and safe optimization plan | performance fixture | MT-08 |

Do the tasks look good?
