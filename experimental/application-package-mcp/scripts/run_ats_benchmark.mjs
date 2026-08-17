#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkAtsResumeFit } from "../dist/ats_checker.js";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const mcpRoot = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(mcpRoot, "../..");
const outputDir = path.join(repoRoot, "output/ats-benchmark");

const CASES = [
  {
    id: "mercedes-process-development",
    expected: 21,
    intake: "application-system/intakes/mercedes-benz-ag-working-student-process-development-for-cdcc2-0-baselayer-software.json",
    cv: "application-system/outputs/mercedes-benz-ag-working-student-process-development-for-cdcc2-0-baselayer-software/cv/resume-le-cuong-nguyen-working-student-process-development-for-cdcc2-0-baselayer-software-20260404-122825.pdf"
  },
  {
    id: "mercedes-requirements-engineering",
    expected: 45,
    intake: "application-system/intakes/mercedes-benz-ag-working-student-requirements-engineering-for-cdcc2-0-baselayer-software-development.json",
    cv: "application-system/outputs/mercedes-benz-ag-working-student-requirements-engineering-for-cdcc2-0-baselayer-software-development/cv/resume-cuong-le-nguyen-working-student-requirements-engineering-for-cdcc2-0-baselayer-software-development-20260328-190043.pdf"
  },
  {
    id: "realworld-one-solution-delivery",
    expected: 66,
    intake: "application-system/intakes/realworld-one-solution-delivery-associate-working-student-intern.json",
    cv: "application-system/outputs/realworld-one-solution-delivery-associate-working-student-intern/cv/resume-le-cuong-nguyen-solution-delivery-associate-working-student-intern-20260403-205640.pdf"
  },
  {
    id: "4flow-ai-consulting",
    expected: 35,
    intake: "application-system/intakes/4flow-working-student-ai-driven-consulting.json",
    cv: "application-system/outputs/4flow-se-working-student-ai-driven-consulting-d-f-m/cv/resume-le-cuong-nguyen-working-student-ai-driven-consulting-d-f-m-20260412-161104.pdf"
  },
  {
    id: "appliedai-instructional-design",
    expected: 66,
    intake: "application-system/intakes/appliedai-working-student-instructional-design.json",
    cv: "application-system/outputs/appliedai-initiative-gmbh-working-student-m-f-x-instructional-design/cv/resume-le-cuong-nguyen-working-student-m-f-x-instructional-design-20260412-144757.pdf"
  },
  {
    id: "sap-technical-writing",
    expected: 30,
    intake: "application-system/intakes/sap-working-student-technical-writing-team-support.json",
    cv: "application-system/outputs/sap-working-student-f-m-d-technical-writing-team-support/cv/resume-le-cuong-nguyen-working-student-f-m-d-technical-writing-team-support-20260412-183830.pdf"
  },
  {
    id: "schwarz-it-marketing-systems",
    expected: 42,
    intake: "application-system/intakes/schwarz-it-werkstudent-marketing-systeme.json",
    cv: "application-system/outputs/schwarz-it-werkstudent-marketing-systeme-m-w-d/cv/resume-le-cuong-nguyen-werkstudent-marketing-systeme-m-w-d-20260412-135023.pdf"
  },
  {
    id: "vishay-controlling",
    expected: 57,
    intake: "application-system/intakes/vishay-semiconductor-werkstudent-controlling.json",
    cv: "application-system/outputs/vishay-semiconductor-gmbh-werkstudent-m-w-d-controlling/cv/resume-le-cuong-nguyen-werkstudent-m-w-d-controlling-20260422-152704.pdf"
  }
];

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(repoRoot, relativePath), "utf8"));
}

function intakeToJobDescription(intake) {
  const parts = [
    intake.company_name,
    intake.job_title,
    intake.job_description,
    Array.isArray(intake.requirements) ? intake.requirements.join("\n") : "",
    intake.why_company
  ];
  return parts.filter(Boolean).join("\n\n");
}

function extractPdfText(relativePath) {
  const absolutePath = path.join(repoRoot, relativePath);
  return execFileSync("pdftotext", ["-layout", absolutePath, "-"], {
    cwd: repoRoot,
    encoding: "utf8",
    maxBuffer: 12 * 1024 * 1024
  });
}

function markdownReport(results) {
  const lines = [
    "# ATS Benchmark",
    "",
    "This benchmark compares the local MCP ATS approximation against the eight observed NodeFlair ATS scores captured during manual testing.",
    "",
    "| Case | NodeFlair | Local | Delta | Profile | Status |",
    "| --- | ---: | ---: | ---: | --- | --- |"
  ];
  for (const item of results) {
    lines.push(`| ${item.id} | ${item.expected} | ${item.actual} | ${item.delta} | ${item.profile} | ${Math.abs(item.delta) <= item.tolerance ? "pass" : "fail"} |`);
  }
  lines.push(
    "",
    `Tolerance: ±${results[0]?.tolerance ?? 8} points per case. NodeFlair's private engine is not public, so the local gate is calibrated to observed behavior and must be rerun after ATS rule changes.`,
    ""
  );
  return lines.join("\n");
}

mkdirSync(outputDir, { recursive: true });

const tolerance = Number(process.env.ATS_BENCHMARK_TOLERANCE ?? "8");
const results = [];

for (const benchmark of CASES) {
  const intake = readJson(benchmark.intake);
  const resumeText = extractPdfText(benchmark.cv);
  const result = checkAtsResumeFit({
    company_name: intake.company_name,
    job_title: intake.job_title,
    language: intake.language,
    role_family: intake.primary_role,
    job_description: intakeToJobDescription(intake),
    resume_text: resumeText,
    target_score: 70,
    max_new_terms: 14
  });
  const row = {
    id: benchmark.id,
    expected: benchmark.expected,
    actual: result.score,
    delta: result.score - benchmark.expected,
    tolerance,
    profile: result.calibration.profile,
    matched: result.matched_keywords.map((keyword) => keyword.term),
    missing: result.missing_keywords.map((keyword) => keyword.term),
    readiness_label: result.readiness_label
  };
  results.push(row);
}

writeFileSync(path.join(outputDir, "ats-benchmark-results.json"), JSON.stringify({ generated_at: new Date().toISOString(), tolerance, results }, null, 2) + "\n");
writeFileSync(path.join(outputDir, "ats-benchmark-results.md"), markdownReport(results));

for (const row of results) {
  assert.ok(Math.abs(row.delta) <= tolerance, `${row.id}: expected ${row.expected}, local ${row.actual}, delta ${row.delta}`);
}

console.log(markdownReport(results));
