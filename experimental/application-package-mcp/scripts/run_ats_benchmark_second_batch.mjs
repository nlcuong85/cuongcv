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
    id: "4screen-analytics",
    expected: 42,
    intake: "application-system/intakes/4screen-analytics-and-data-science-working-student.json",
    cv: "application-system/outputs/4screen-analytics-data-science-working-student-f-m-x/cv/resume-le-cuong-nguyen-analytics-data-science-working-student-f-m-x-20260412-182017.pdf",
    nodeflairMatched: ["Ad-Hoc", "Analysis", "Analytical", "Analytics", "Data", "Data Analysis", "SQL", "Stakeholders"],
    nodeflairSuggested: ["Agile", "BASIC", "Communication", "Communication Skills", "Computer Science", "Data Science", "Machine Learning", "Python", "Quantitative", "Solutions", "Statistics"]
  },
  {
    id: "acteno-smart-energy",
    expected: 41,
    intake: "application-system/intakes/acteno-energy-ai-meets-energy-hybrid-systems.json",
    cv: "application-system/outputs/acteno-energy-gmbh-praktikum-werkstudium-smart-energy-systems/cv/resume-le-cuong-nguyen-praktikum-werkstudium-smart-energy-systems-20260413-111254.pdf",
    nodeflairMatched: ["Data", "Design", "Development", "Technical", "Writing"],
    nodeflairSuggested: ["Communication", "Computer Science", "Monitoring", "MS Office", "Organizational Skills", "Research", "Teamwork"]
  },
  {
    id: "bitbw-controlling",
    expected: 25,
    intake: "application-system/intakes/bitbw-werkstudent-im-bereich-controlling.json",
    cv: "application-system/outputs/it-baden-wurttemberg-bitbw-werkstudent-im-bereich-controlling-w-m-d/cv/resume-cuong-le-nguyen-werkstudent-im-bereich-controlling-w-m-d-20260328-203343.pdf",
    nodeflairMatched: ["Business Administration", "Data"],
    nodeflairSuggested: ["Excel", "Monitoring", "MS Office", "PowerPoint", "Reliability", "SAP"]
  },
  {
    id: "bosch-ecommerce-ba",
    expected: 66,
    intake: "application-system/intakes/bosch-business-analyst-ecommerce.json",
    cv: "application-system/outputs/robert-bosch-gmbh-business-analyst-ecommerce/cv/resume-le-cuong-nguyen-business-analyst-ecommerce-20260405-133242.pdf",
    nodeflairMatched: ["Analysis", "Business Analysis", "Execution", "Process Improvement", "Product", "Stakeholders"],
    nodeflairSuggested: ["Collaborate", "Data-Driven", "Scalable"]
  },
  {
    id: "diehl-digital-process",
    expected: 50,
    intake: "application-system/intakes/diehl-defence-werkstudent-digitalisierung-von-geschaeftsprozessen.json",
    cv: "application-system/outputs/aim-infrarot-module-gmbh-diehl-defence-werkstudent-m-w-d-digitalisierung-von-geschaftsprozessen/cv/resume-cuong-le-nguyen-werkstudent-m-w-d-digitalisierung-von-geschaftsprozessen-20260328-233212.pdf",
    nodeflairMatched: ["Analysis", "Development", "Documentation", "Mode", "Process Analysis", "SAP"],
    nodeflairSuggested: ["Analytical", "Business Processes", "Computer Science", "MS Office", "Optimization", "Roadmap"]
  },
  {
    id: "ilos-process-digitalisation",
    expected: 38,
    intake: "application-system/intakes/ilos-process-digitalisation-working-student.json",
    cv: "application-system/outputs/ilos-projects-gmbh-process-digitalisation-working-student/cv/resume-le-cuong-nguyen-process-digitalisation-working-student-20260412-195223.pdf",
    nodeflairMatched: ["Analysis", "Business Administration", "Data", "Documentation", "Excel", "Execution", "Mode", "Stakeholders"],
    nodeflairSuggested: ["Analytical", "Analytical Skills", "Analytics", "BASIC", "Business Processes", "Communication", "Communication Skills", "Continuous Improvement", "Cross-Functional Collaboration", "Data Analytics", "Microsoft", "PowerPoint", "Process Management"]
  },
  {
    id: "mercedes-data-ai-pm",
    expected: 42,
    intake: "application-system/intakes/mercedes-benz-ag-werkstudent-data-ai-product-management-software-certification.json",
    cv: "application-system/outputs/mercedes-benz-ag-werkstudent-in-data-ai-product-management-software-certification/cv/resume-cuong-le-nguyen-werkstudent-in-data-ai-product-management-software-certification-20260328-201540.pdf",
    nodeflairMatched: ["AI", "Analysis", "Data", "Development", "Digital Products", "Feedback", "Product", "Product Management", "Software", "Stakeholders", "User Feedback"],
    nodeflairSuggested: ["Analytical", "Architecture", "Computer Science", "Data Science", "Data-Driven", "Innovative", "Optimization", "Process Analysis", "Software Architecture", "Software Development", "Solutions", "Teamwork", "Testing", "Use Cases", "User-Centered"]
  },
  {
    id: "teamviewer-product-management",
    expected: 43,
    intake: "application-system/intakes/teamviewer-work-student-product-management.json",
    cv: "application-system/outputs/teamviewer-germany-gmbh-work-student-product-management-all-genders/cv/resume-le-cuong-nguyen-work-student-product-management-all-genders-20260412-153249.pdf",
    nodeflairMatched: ["Analysis", "B2B", "Business Administration", "Market", "Market Analysis", "Product", "Product Management", "Project Management", "Research", "Software"],
    nodeflairSuggested: ["Agile", "Communication", "Communication Skills", "Computer Science", "Enterprise", "Excel", "Feedback", "Microsoft", "PowerPoint", "SaaS", "Use Cases", "Verbal Communication Skills", "Written"]
  }
];

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(repoRoot, relativePath), "utf8"));
}

function intakeToJobDescription(intake) {
  return [
    intake.company_name,
    intake.job_title,
    intake.job_description,
    Array.isArray(intake.requirements) ? intake.requirements.join("\n") : "",
    intake.why_company
  ]
    .filter(Boolean)
    .join("\n\n");
}

function extractPdfText(relativePath) {
  return execFileSync("pdftotext", ["-layout", path.join(repoRoot, relativePath), "-"], {
    cwd: repoRoot,
    encoding: "utf8",
    maxBuffer: 12 * 1024 * 1024
  });
}

function markdownReport(results) {
  const lines = [
    "# ATS Benchmark - second observed NodeFlair batch",
    "",
    "This benchmark compares the local MCP ATS approximation against a second set of observed NodeFlair ATS scores and keyword lists.",
    "",
    "| Case | NodeFlair | Local | Delta | Profile | NodeFlair matched | NodeFlair suggested | Status |",
    "| --- | ---: | ---: | ---: | --- | --- | --- | --- |"
  ];
  for (const item of results) {
    lines.push(`| ${item.id} | ${item.expected} | ${item.actual} | ${item.delta} | ${item.profile} | ${item.nodeflairMatched.join(", ")} | ${item.nodeflairSuggested.join(", ")} | ${Math.abs(item.delta) <= item.tolerance ? "pass" : "fail"} |`);
  }
  lines.push(
    "",
    `Tolerance: ±${results[0]?.tolerance ?? 8} points per case. Keyword lists are observed NodeFlair UI outputs captured through authenticated browser testing.`,
    ""
  );
  return lines.join("\n");
}

mkdirSync(outputDir, { recursive: true });

const tolerance = Number(process.env.ATS_BENCHMARK_TOLERANCE ?? "8");
const results = [];

for (const benchmark of CASES) {
  const intake = readJson(benchmark.intake);
  const result = checkAtsResumeFit({
    company_name: intake.company_name,
    job_title: intake.job_title,
    language: intake.language,
    role_family: intake.primary_role,
    job_description: intakeToJobDescription(intake),
    resume_text: extractPdfText(benchmark.cv),
    target_score: 70,
    max_new_terms: 18
  });
  results.push({
    id: benchmark.id,
    expected: benchmark.expected,
    actual: result.score,
    delta: result.score - benchmark.expected,
    tolerance,
    profile: result.calibration.profile,
    matched: result.matched_keywords.map((keyword) => keyword.term),
    missing: result.missing_keywords.map((keyword) => keyword.term),
    nodeflairMatched: benchmark.nodeflairMatched,
    nodeflairSuggested: benchmark.nodeflairSuggested,
    readiness_label: result.readiness_label
  });
}

writeFileSync(path.join(outputDir, "ats-benchmark-second-batch-results.json"), JSON.stringify({ generated_at: new Date().toISOString(), tolerance, results }, null, 2) + "\n");
writeFileSync(path.join(outputDir, "ats-benchmark-second-batch-results.md"), markdownReport(results));

for (const row of results) {
  assert.ok(Math.abs(row.delta) <= tolerance, `${row.id}: expected ${row.expected}, local ${row.actual}, delta ${row.delta}`);
}

console.log(markdownReport(results));
