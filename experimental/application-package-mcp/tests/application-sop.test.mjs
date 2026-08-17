import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { copyFile, cp, mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

const root = path.resolve(new URL("..", import.meta.url).pathname);

function sop(workspace, ...args) {
  return execFileSync("python3", [path.join(workspace, "application-kit/scripts/application_sop.py"), "--root", workspace, ...args], { encoding: "utf8" });
}

test("local Application SOP requires decisions, current audit, and distinct cover review hashes", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "application-sop-"));
  await cp(path.join(root, "resources/workspace-template"), workspace, { recursive: true });
  await mkdir(path.join(workspace, "application-kit"));
  await cp(path.join(root, "resources/application-kit"), path.join(workspace, "application-kit"), { recursive: true });

  assert.match(sop(workspace, "boot", "--strict"), /initialized local baseline/);
  sop(workspace, "start", "--task-id", "APP-1", "--job", "test-role", "--goal", "test");

  const initialVoiceStatus = JSON.parse(sop(workspace, "voice-intake-status"));
  assert.equal(initialVoiceStatus.status, "ask_now");
  sop(workspace, "record-voice-intake", "--status", "revisit_later", "--remind-after-days", "45");
  const deferredVoiceStatus = JSON.parse(sop(workspace, "voice-intake-status"));
  assert.equal(deferredVoiceStatus.status, "not_due");
  sop(workspace, "record-voice-intake", "--status", "enough", "--source-count", "4");
  const suppressedVoiceStatus = JSON.parse(sop(workspace, "voice-intake-status"));
  assert.equal(suppressedVoiceStatus.status, "suppressed");
  assert.equal(suppressedVoiceStatus.reason, "candidate_marked_enough");

  sop(workspace, "record-decision", "--name", "photo", "--value", "declined");
  sop(workspace, "record-decision", "--name", "signature", "--value", "declined");
  sop(workspace, "record-decision", "--name", "enclosures", "--value", "cv_plus_diploma");
  await writeFile(path.join(workspace, "audit.json"), JSON.stringify({ status: "workspace_current" }));
  sop(workspace, "record-manifest-audit", "--report", "audit.json");

  const letter = path.join(workspace, "applications/test-role/cover-letter/cover-letter.md");
  await mkdir(path.dirname(letter), { recursive: true });
  const result = path.join(workspace, "review.json");
  await writeFile(result, JSON.stringify({ riskLevel: "low", issues: [] }));
  for (const [loop, text] of [[1, "First version."], [2, "Second version revised."], [3, "Third version ready."]]) {
    await writeFile(letter, text);
    sop(workspace, "review-cover", "--loop", String(loop), "--artifact", "applications/test-role/cover-letter/cover-letter.md", "--result", "review.json");
  }
  const output = sop(workspace, "finalize-cover-letter", "--artifact", "applications/test-role/cover-letter/cover-letter.md").trim();
  const receipt = JSON.parse(await readFile(path.join(workspace, output), "utf8"));
  assert.equal(receipt.status, "ready");
  assert.equal(receipt.reviews.length, 3);

  await writeFile(letter, "Changed after receipt.");
  const blocked = (() => { try { sop(workspace, "finalize-cover-letter", "--artifact", "applications/test-role/cover-letter/cover-letter.md"); } catch (error) { return error.stdout; } })();
  assert.match(blocked, /NOT READY/);

  const prep = path.join(workspace, "applications/test-role/interview-prep/interview-prep.md");
  await mkdir(path.dirname(prep), { recursive: true });
  await writeFile(prep, "Interview prep with a 60-second introduction, answer scripts, and culture-fit notes.");
  const prepResult = path.join(workspace, "interview-review.json");
  await writeFile(prepResult, JSON.stringify({ riskLevel: "low", issues: [], privacy: { stored: false } }));
  sop(workspace, "review-interview-prep", "--loop", "1", "--artifact", "applications/test-role/interview-prep/interview-prep.md", "--result", "interview-review.json");
  sop(workspace, "review-interview-prep", "--loop", "2", "--artifact", "applications/test-role/interview-prep/interview-prep.md", "--result", "interview-review.json");
  const prepReceiptOutput = sop(workspace, "finalize-interview-prep", "--artifact", "applications/test-role/interview-prep/interview-prep.md").trim();
  const prepReceipt = JSON.parse(await readFile(path.join(workspace, prepReceiptOutput), "utf8"));
  assert.equal(prepReceipt.status, "ready");
  assert.equal(prepReceipt.document, "interview-prep");
  assert.equal(prepReceipt.reviews.length, 2);

  await writeFile(prep, "Interview prep changed after review.");
  const stalePrep = (() => { try { sop(workspace, "finalize-interview-prep", "--artifact", "applications/test-role/interview-prep/interview-prep.md"); } catch (error) { return error.stdout; } })();
  assert.match(stalePrep, /NOT READY/);
  assert.match(stalePrep, /interview-prep loops 1 and 2 are required/);

  const cv = path.join(workspace, "applications/test-role/cv/cv-tailored.md");
  await mkdir(path.dirname(cv), { recursive: true });
  await writeFile(cv, "CV with requirements analysis, documentation, stakeholder communication, and product support.");
  const cvResult = path.join(workspace, "cv-review.json");
  await writeFile(cvResult, JSON.stringify({ riskLevel: "low", issues: [], privacy: { stored: false } }));
  sop(workspace, "review-cv", "--loop", "1", "--artifact", "applications/test-role/cv/cv-tailored.md", "--result", "cv-review.json");
  const noAtsCv = (() => { try { sop(workspace, "finalize-cv", "--artifact", "applications/test-role/cv/cv-tailored.md"); } catch (error) { return error.stdout; } })();
  assert.match(noAtsCv, /NOT READY/);
  assert.match(noAtsCv, /current ATS CV\/JD report required/);
  await mkdir(path.join(workspace, "applications/test-role/validation"), { recursive: true });
  await writeFile(path.join(workspace, "jobs/test-role.md"), "Job description requiring documentation and communication.");
  await writeFile(
    path.join(workspace, "applications/test-role/validation/ats-report.json"),
    JSON.stringify({
      ok: true,
      score: 57,
      targetScore: 70,
      readiness_label: "needs_revision",
      matched_keywords: [{ term: "Documentation" }],
      missing_keywords: [{ term: "MS Office" }],
      privacy: { stored: false }
    }),
  );
  sop(
    workspace,
    "record-ats-cv",
    "--artifact",
    "applications/test-role/cv/cv-tailored.md",
    "--result",
    "applications/test-role/validation/ats-report.json",
    "--job-description",
    "jobs/test-role.md",
  );
  const cvReceiptOutput = sop(workspace, "finalize-cv", "--artifact", "applications/test-role/cv/cv-tailored.md").trim();
  const cvReceipt = JSON.parse(await readFile(path.join(workspace, cvReceiptOutput), "utf8"));
  assert.equal(cvReceipt.status, "ready");
  assert.equal(cvReceipt.document, "cv");
  assert.equal(cvReceipt.ats_records.length, 1);
  assert.equal(cvReceipt.ats_records[0].score, 57);
  await writeFile(cv, "CV changed after ATS report.");
  const staleAtsCv = (() => { try { sop(workspace, "finalize-cv", "--artifact", "applications/test-role/cv/cv-tailored.md"); } catch (error) { return error.stdout; } })();
  assert.match(staleAtsCv, /NOT READY/);
  assert.match(staleAtsCv, /1 current CV review record required/);
  assert.match(staleAtsCv, /current ATS CV\/JD report required/);

  const writing = path.join(workspace, "writing-reviews/sample/revised.md");
  await mkdir(path.dirname(writing), { recursive: true });
  await writeFile(writing, "A revised academic paragraph with a scoped claim, method boundary, and practical limitation.");
  await writeFile(path.join(workspace, "writing-review.json"), JSON.stringify({ riskLevel: "low", issues: [], privacy: { stored: false } }));
  sop(workspace, "review-writing", "--loop", "1", "--artifact", "writing-reviews/sample/revised.md", "--result", "writing-review.json");
  sop(workspace, "review-writing", "--loop", "2", "--artifact", "writing-reviews/sample/revised.md", "--result", "writing-review.json");
  const writingReceiptOutput = sop(workspace, "finalize-writing", "--required-loops", "2", "--artifact", "writing-reviews/sample/revised.md").trim();
  const writingReceipt = JSON.parse(await readFile(path.join(workspace, writingReceiptOutput), "utf8"));
  assert.equal(writingReceipt.status, "ready");
  assert.equal(writingReceipt.document, "writing");
  assert.equal(writingReceipt.reviews.length, 2);
});

test("local generator resolves a workspace-relative signature when compilation runs elsewhere", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "application-signature-"));
  await mkdir(path.join(workspace, "application-kit"));
  await cp(path.join(root, "resources/application-kit"), path.join(workspace, "application-kit"), { recursive: true });
  await mkdir(path.join(workspace, "candidate"));
  await copyFile(
    path.join(root, "resources/application-kit/examples/german-cover-letter-demo/signature-rendered.png"),
    path.join(workspace, "candidate/signature.png"),
  );

  const exampleDraft = JSON.parse(await readFile(
    path.join(root, "resources/application-kit/examples/german-cover-letter-demo/cover-letter-draft.json"),
    "utf8",
  ));
  exampleDraft.signature_path = "candidate/signature.png";
  exampleDraft.enclosures = ["Curriculum Vitae"];
  const draftPath = path.join(workspace, "applications/test-role/cover-letter-draft.json");
  await mkdir(path.dirname(draftPath), { recursive: true });
  await writeFile(draftPath, JSON.stringify(exampleDraft, null, 2));

  const outputDir = path.join(workspace, "applications/test-role/cover-letter");
  execFileSync(
    "python3",
    [
      path.join(workspace, "application-kit/scripts/local_application_generator.py"),
      "--draft", draftPath,
      "--output-dir", outputDir,
    ],
    { cwd: root, encoding: "utf8" },
  );
  const tex = await readFile(path.join(outputDir, "cover-letter.tex"), "utf8");
  assert.match(tex, /\\item Curriculum Vitae/);
  assert.doesNotMatch(tex, /Bachelor Degree Diploma/);
  assert.doesNotMatch(tex, /Reference letter from previous employers/);
  const validation = await readFile(path.join(outputDir, "validation.md"), "utf8");
  assert.match(validation, /fewer than two enclosures/i);
  const generated = readdirSync(outputDir).filter((name) => /^cover-letter-.*\.pdf$/.test(name));
  assert.equal(generated.length, 1);
  const pdfInfo = execFileSync("pdfinfo", [path.join(outputDir, generated[0])], { encoding: "utf8" });
  assert.match(pdfInfo, /^Pages:\s+1$/m);
});

test("CV HTML builder strips raw-template preview sample from generated output", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "cv-html-builder-"));
  await mkdir(path.join(workspace, "application-kit"));
  await cp(path.join(root, "resources/application-kit"), path.join(workspace, "application-kit"), { recursive: true });
  await mkdir(path.join(workspace, "candidate/extracted"), { recursive: true });
  await writeFile(
    path.join(workspace, "candidate/extracted/cv-source.md"),
    [
      "# Real Candidate",
      "",
      "## Summary",
      "",
      "Requirements-focused student with practical experience in process notes and stakeholder follow-up.",
      "",
      "## Experience",
      "",
      "### Working Student - Operations Support",
      "Demo Company · 2024 - Present",
      "- Wrote user stories and acceptance criteria.",
      "- Maintained process documentation for recurring service cases.",
      "",
      "## Skills",
      "",
      "- Requirements analysis",
      "- Process mapping",
      "",
      "## Education",
      "",
      "- B.Sc. Business Informatics, Demo University, 2021 - 2026",
      "",
      "## Languages",
      "",
      "- German - B2",
      "- English - C1",
      "",
    ].join("\n"),
  );

  execFileSync(
    "python3",
    [
      path.join(workspace, "application-kit/scripts/build_cv_html.py"),
      "--root", workspace,
      "--job", "sample",
      "--name", "Real Candidate",
      "--email", "real@example.com",
      "--phone", "+49 170 7654321",
      "--linkedin", "linkedin.com/in/real-candidate",
    ],
    { cwd: root, encoding: "utf8" },
  );
  const generated = await readFile(path.join(workspace, "applications/sample/cv/cv-tailored.html"), "utf8");
  assert.match(generated, /Real Candidate/);
  assert.match(generated, /Professional Experience/);
  assert.match(generated, /Education/);
  assert.doesNotMatch(generated, /@@NAME@@/);
  assert.doesNotMatch(generated, /Jane Schneider/);
  assert.doesNotMatch(generated, /TEMPLATE_PREVIEW_START/);
  assert.doesNotMatch(generated, /samplePhotoSvg/);
});

test("interview prep builder creates culture-fit prep and missing-info questions", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "interview-prep-builder-"));
  await mkdir(path.join(workspace, "application-kit"));
  await cp(path.join(root, "resources/application-kit"), path.join(workspace, "application-kit"), { recursive: true });
  await mkdir(path.join(workspace, "candidate"), { recursive: true });
  await mkdir(path.join(workspace, "jobs/sample-product-owner"), { recursive: true });
  await writeFile(
    path.join(workspace, "candidate/profile.json"),
    JSON.stringify(
      {
        name: "Real Candidate",
        summary: "Business informatics student with practical experience in requirements, stakeholder communication, and product support.",
        skills: ["Requirements Engineering", "Stakeholder Communication", "Testing Support", "Agile Collaboration"]
      },
      null,
      2,
    ),
  );
  await writeFile(
    path.join(workspace, "candidate/evidence.md"),
    [
      "# Evidence",
      "",
      "- Wrote user stories and acceptance criteria for a product workflow.",
      "- Coordinated with developers and business stakeholders to clarify delivery scope.",
      "- Reviewed testing notes and turned feedback into practical backlog changes.",
      "",
    ].join("\n"),
  );
  await writeFile(
    path.join(workspace, "jobs/sample-product-owner/job.json"),
    JSON.stringify(
      {
        company_name: "Sample Mobility GmbH",
        job_title: "Working Student Product Owner Support",
        why_company: "The role connects product support, requirements, testing, and stakeholder communication.",
        job_description: "Support Product Owners with requirements, agile planning, testing documentation, stakeholder communication, and product data insights.",
        requirements: ["Requirements support", "Testing documentation", "Agile collaboration", "Stakeholder communication"]
      },
      null,
      2,
    ),
  );
  await writeFile(
    path.join(workspace, "jobs/sample-product-owner/interview.json"),
    JSON.stringify(
      {
        date: "2026-09-01 10:00",
        format: "Microsoft Teams",
        duration: "45 minutes",
        language: "English",
        interviewers: ["Jane Recruiter, Talent Acquisition"],
        outside_work: "I recharge through running, cooking, and reading about product design.",
        concerns: ["German is still improving"]
      },
      null,
      2,
    ),
  );

  execFileSync(
    "python3",
    [
      path.join(workspace, "application-kit/scripts/build_interview_prep.py"),
      "--root", workspace,
      "--job", "sample-product-owner",
    ],
    { cwd: root, encoding: "utf8" },
  );
  const prep = await readFile(path.join(workspace, "applications/sample-product-owner/interview-prep/interview-prep.md"), "utf8");
  assert.match(prep, /Sample Mobility GmbH/);
  assert.match(prep, /Culture Fit: Who Are You Outside Work/);
  assert.match(prep, /running, cooking, and reading about product design/);
  assert.match(prep, /Strong Answer Scripts/);
  assert.match(prep, /Why likely:/);
  assert.match(prep, /What They Are Likely Screening For/);
  assert.match(prep, /Actual STAR incidents are missing/);
  assert.match(prep, /Ask the student:/);
  assert.match(prep, /Do not convert generic CV responsibilities into a STAR story/);
  assert.match(prep, /I work too hard/);
  assert.match(prep, /Do not invent/);
  const questions = await readFile(path.join(workspace, "applications/sample-product-owner/interview-prep/interview-prep-questions.md"), "utf8");
  assert.match(questions, /actual past incident stories/);
  assert.match(questions, /I will not invent STAR stories/);
  const manifest = JSON.parse(await readFile(path.join(workspace, "applications/sample-product-owner/interview-prep/interview-prep-manifest.json"), "utf8"));
  assert.equal(manifest.privacy.mcp_called, false);
  assert.equal(manifest.review_gate.required, true);
  assert.equal(manifest.review_gate.loops_required, 2);
  assert.match(manifest.outputs.join(" "), /interview-prep-review-input-loop-1\.json/);
  assert.match(manifest.outputs.join(" "), /interview-prep-review-input-loop-2\.json/);
  assert.equal(manifest.evidence_status, "needs_user_clarification");
  const reviewInput1 = JSON.parse(await readFile(path.join(workspace, "applications/sample-product-owner/interview-prep/interview-prep-review-input-loop-1.json"), "utf8"));
  const reviewInput2 = JSON.parse(await readFile(path.join(workspace, "applications/sample-product-owner/interview-prep/interview-prep-review-input-loop-2.json"), "utf8"));
  assert.equal(reviewInput1.mode, "application");
  assert.match(reviewInput1.purpose, /loop 1/);
  assert.match(reviewInput1.text, /Spoken Answers/);
  assert.match(reviewInput2.purpose, /loop 2/);
  assert.match(reviewInput2.text, /Role Read And Readiness/);
  assert.match(reviewInput2.text, /evidence anchor/i);
  assert.doesNotMatch(reviewInput1.text, /Missing Information To Ask The Student/);
});

test("writing review loop prepares chunked MCP packets and report", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "writing-review-loop-"));
  await mkdir(path.join(workspace, "application-kit"));
  await cp(path.join(root, "resources/application-kit"), path.join(workspace, "application-kit"), { recursive: true });
  await mkdir(path.join(workspace, "drafts"), { recursive: true });
  await writeFile(
    path.join(workspace, "drafts/academic.md"),
    [
      "# Abstract",
      "",
      "This study discusses digital-service adoption in a student context. The claim is intentionally scoped because the draft does not include a validated survey sample yet.",
      "",
      "# Method Note",
      "",
      "The current section should explain what evidence exists, what is still missing, and why the limitation matters for readers.",
      "",
    ].join("\n"),
  );
  execFileSync(
    "python3",
    [
      path.join(workspace, "application-kit/scripts/writing_review_loop.py"),
      "--root", workspace,
      "prepare",
      "--input", "drafts/academic.md",
      "--mode", "academic",
      "--loops", "3",
      "--max-words", "30",
      "--output-dir", "writing-reviews/academic-test",
    ],
    { cwd: root, encoding: "utf8" },
  );
  const manifestPath = path.join(workspace, "writing-reviews/academic-test/writing-review-manifest.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  assert.equal(manifest.mode, "academic");
  assert.equal(manifest.loops_requested, 3);
  assert.ok(manifest.chunk_count >= 2);
  assert.ok(manifest.chunks.every((chunk) => chunk.input.includes("loop-")));
  for (const chunk of manifest.chunks) {
    await writeFile(path.join(workspace, chunk.expected_result), JSON.stringify({ riskLevel: "low", summary: "ok", issues: [], privacy: { stored: false } }));
  }
  const reportOutput = execFileSync(
    "python3",
    [
      path.join(workspace, "application-kit/scripts/writing_review_loop.py"),
      "--root", workspace,
      "report",
      "--manifest", "writing-reviews/academic-test/writing-review-manifest.json",
    ],
    { cwd: root, encoding: "utf8" },
  ).trim();
  assert.equal(reportOutput, "writing-reviews/academic-test/writing-review-report.md");
  const report = await readFile(path.join(workspace, reportOutput), "utf8");
  assert.match(report, /ready_for_human_review/);
});
