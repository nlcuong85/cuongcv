# Implementation Plan: Free-User Onboarding

User authorized the full local implementation and three test/repair loops on 2026-10-22. Batch scope is local implementation and validation; deployment is separate. Manual source of truth: tests.md T01-T21. Existing user changes remain intact.

- [x] 1. Implement the first-run path and public instruction parity. _Requirements: ONB-01 through ONB-05, ONB-07, ONB-08_
  - Preserve current tokens; add accessible client/folder/help sections and beginner flow.
  - Fix shared clipboard success/failure/focus behavior and direct-fragment disclosures.
  - Update public resources and maintain managed policy/release gates.
- [x] 2. Implement task-specific local capability and safe-source recovery. _Requirements: ONB-02, ONB-06_
  - Reuse existing conversion owners; test missing tools and preserved originals.
- [x] 3. Update canonical diagrams and static rendered assets. _Requirements: ONB-10_
  - Correct bootstrap, review, workflow and legacy documentation; inspect renders.
- [x] 4. Add focused HTTP/CLI/browser regression and local proof. _Requirements: ONB-09, all mapped criteria_
  - Map automation to tests.md before writing it; record client/device gaps explicitly.
  - Loop 1: behavior/protocol/kit regression on rebuilt loopback runtime.
  - Loop 2: UX/accessibility/copy/mobile/diagrams; repair defects and repeat affected tests.
  - Loop 3: fresh-runtime spec-to-browser reconciliation and final regression.
  - Each loop records localhost URL, manual checks, artifacts, blockers and earliest affected task.
  - Completed local validation uses focused Playwright suites and the local UX matrix at `experimental/application-package-mcp/output/playwright/free-user-onboarding/ux-matrix.md`.
  - A later authorized release must add live health verification and production browser evidence; no deployment runs in this batch.

Completion above denotes local implementation/test work only. Actual account/client UI, physical device and production acceptance are not implied by checked tasks; see acceptance.md.

- [x] 5. Revise entry to agent-led configuration after owner feedback. _Requirements: ONB-01.2, ONB-04.1, ONB-10.1, ONB-11_
  - Add pre-connection public agent guidance and an approval-controlled project-config helper.
  - Replace manual-first entry with folder/request/agent visual and collapsed fallback; shorten canonical prompt and sync public instructions.
  - Update T01/T02/T21 and add T22 plus helper HTTP/isolated mutation tests; inspect branded desktop/mobile diagrams.
  - Rebuild/restart local runtime; 13 code/API and 14 Playwright checks passed. Preserve actual-client/device caveats and deployment boundary.
