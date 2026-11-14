import assert from "node:assert/strict";
import test from "node:test";
import { checkWritingHumanFit } from "../dist/checker.js";

const cvText = `# Riley Example
## Profile
Information Systems student with a campus-service documentation project. The project involved a four-step quick guide for a mock intake process, a four-slide presentation, and meeting notes with follow-up actions. The handoff step was unclear in the first draft, so a peer reviewer checked it before the guide was revised. The scope was a class exercise, not professional developer documentation or SAP implementation work.

## Project Experience
Information Design Project Contributor, Example University, October 2025 to March 2026.
- Turned a mock campus-service intake flow into a four-step guide for another student to follow.
- Prepared a short presentation and meeting notes with specific follow-up actions.
- Checked the guide with a peer reviewer and clarified one confusing handoff step.

## Education
Master of Science in Information Systems, Example University, current student.

## Skills
Concise writing, document formatting, process mapping, Microsoft Word, PowerPoint, and Excel.

## Languages
English C1 and German B1 are fictional test-profile values, not certificates.`;

test("CV application review does not impose cover-letter story rules", () => {
  const cv = checkWritingHumanFit({ text: cvText, mode: "application", document_kind: "cv", audience: "recruiter" });
  const legacyLetter = checkWritingHumanFit({ text: cvText, mode: "application", audience: "recruiter" });
  assert.equal(cv.documentKind, "cv");
  assert.equal(legacyLetter.documentKind, "cover_letter");
  assert.ok(legacyLetter.issues.some((issue) => issue.code === "missing_personal_work_anchor"));
  assert.ok(!cv.issues.some((issue) => issue.code === "missing_personal_work_anchor"));
  assert.ok(!cv.issues.some((issue) => issue.message.toLowerCase().includes("the letter")));
  assert.notEqual(cv.riskLevel, "high");
});
