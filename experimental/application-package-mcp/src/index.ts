import http, { IncomingMessage, ServerResponse } from "node:http";
import { createHash } from "node:crypto";
import { URL } from "node:url";
import process from "node:process";
import * as z from "zod/v4";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { checkAtsResumeFit } from "./ats_checker.js";
import { checkWritingHumanFit } from "./checker.js";
import {
  handoutDocument,
  onboardingInstructions,
  readResource,
  readResourceBinary,
  readTemplateDirectory,
  samplePromptsDocument
} from "./resources.js";

const VERSION = "0.2.18";
const PORT = Number(process.env.PORT ?? "5920");
const HOST = process.env.HOST ?? "127.0.0.1";
const TOKEN = process.env.APPLICATION_MCP_TOKEN;
const PUBLIC_SITE_URL = "https://jobmcp.pmlecuong.com/";
const PUBLIC_MCP_ENDPOINT = "https://jobmcp.pmlecuong.com/mcp";
const MAX_HTTP_BODY_BYTES = 64 * 1024;

const PUBLIC_TOOLS = [
  "health",
  "get_onboarding_instructions",
  "get_client_skill",
  "get_workspace_template",
  "get_application_kit_manifest",
  "get_application_kit_bundle",
  "audit_workspace_manifest",
  "get_sample_prompts",
  "check_ats_resume_fit",
  "check_writing_human_fit",
  "suggest_writing_revision"
];

const WORKSPACE_KIT_VERSION = "2026.08.17-ats-public.1";
const REQUIRED_WORKSPACE_PATHS = [
  "AGENTS.md",
  ".mcp/workspace-manifest.json",
  ".mcp/update-policy.json",
  "profile/master_profile.json",
  "profile/evidence_library.json",
  "profile/claim_boundaries.md",
  "voice/voice-profile.md",
  "candidate/source",
  "jobs",
  "applications",
  "scripts/workspace_audit.py",
  "scripts/application_quality_loop.py",
  "scripts/mcp_check_client.mjs",
  "scripts/ats_text_extract.py",
  "application-kit/manifest.json",
  "application-kit/templates/cover_letter.html",
  "application-kit/templates/cover_letter.tex",
  "application-kit/templates/interview_prep.md",
  "application-kit/templates/cv_english_modern.html",
  "application-kit/templates/cv_german_rounded.html",
  "application-kit/contracts/typography-contract.md",
  "application-kit/contracts/ats-checker-contract.md",
  "application-kit/contracts/cv-markdown-contract.md",
  "application-kit/contracts/interview-prep-contract.md",
  "application-kit/contracts/writing-review-contract.md",
  "application-kit/contracts/mcp-review-payload-contract.md",
  "application-kit/scripts/application_sop.py",
  "application-kit/scripts/application_quality_loop.py",
  "application-kit/scripts/mcp_check_client.mjs",
  "application-kit/scripts/ats_text_extract.py",
  "application-kit/scripts/writing_review_loop.py",
  "application-kit/scripts/local_application_generator.py",
  "application-kit/scripts/build_interview_prep.py",
  "application-kit/scripts/build_cv_html.py"
];

const MANAGED_HASHED_PATHS = [
  "AGENTS.md",
  "scripts/application_sop.py",
  "scripts/mcp_check_client.mjs",
  "scripts/ats_text_extract.py",
  "application-kit/manifest.json",
  "application-kit/templates/cover_letter.html",
  "application-kit/templates/cover_letter.tex",
  "application-kit/templates/interview_prep.md",
  "application-kit/templates/cv_english_modern.html",
  "application-kit/templates/cv_german_rounded.html",
  "application-kit/contracts/typography-contract.md",
  "application-kit/contracts/ats-checker-contract.md",
  "application-kit/contracts/cv-markdown-contract.md",
  "application-kit/contracts/interview-prep-contract.md",
  "application-kit/contracts/writing-review-contract.md",
  "application-kit/contracts/mcp-review-payload-contract.md",
  "application-kit/scripts/application_sop.py",
  "application-kit/scripts/application_quality_loop.py",
  "application-kit/scripts/mcp_check_client.mjs",
  "application-kit/scripts/ats_text_extract.py",
  "application-kit/scripts/writing_review_loop.py",
  "application-kit/scripts/local_application_generator.py",
  "application-kit/scripts/build_interview_prep.py",
  "application-kit/scripts/build_cv_html.py"
];

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

async function expectedManagedHashes(): Promise<Record<string, string>> {
  const entries = await Promise.all(
    MANAGED_HASHED_PATHS.map(async (path) => {
      const resourcePath = path.startsWith("application-kit/")
        ? path
        : `workspace-template/${path}`;
      return [path, sha256(await readResource(resourcePath))] as const;
    })
  );
  return Object.fromEntries(entries);
}

function workspaceUpdateDirective(status: "verify_or_update" | "action_required" | "workspace_current" = "verify_or_update"): Record<string, unknown> {
  return {
    status,
    automatic_for_local_agents: true,
    required_before_application_work: true,
    safe_only: true,
    reason: "Whenever a local agent contacts this MCP, it must make sure the student workspace is current before drafting, editing, reviewing, or finalizing application documents.",
    next_actions: [
      "Fetch get_workspace_template when the workspace is missing starter files.",
      "Fetch get_application_kit_bundle and update MCP-managed files only.",
      "Preserve profile, source documents, voice samples, assets, jobs, applications, outputs, and user-written material.",
      "Run scripts/workspace_audit.py locally and send only the privacy-safe .mcp/workspace-manifest.json to audit_workspace_manifest.",
      "Run python3 scripts/application_sop.py --root . boot --strict before material application work.",
      "For every CV/JD edit, run check_ats_resume_fit and record-ats-cv before finalize-cv."
    ],
    managed_only: [
      "AGENTS.md",
      "CLAUDE.md",
      "scripts/",
      "application-kit/manifest.json",
      "application-kit/contracts/",
      "application-kit/scripts/",
      "application-kit/templates/"
    ],
    never_overwrite: [
      "profile/",
      "memory/",
      "voice/",
      "candidate/",
      "jobs/",
      "applications/",
      "outputs/",
      "photos",
      "signatures",
      "source CVs",
      "student writing samples"
    ],
    privacy: "The MCP cannot read or edit the user's disk. The local agent performs safe local updates and sends only manifests or selected text."
  };
}

function safeRelativePath(value: string): boolean {
  return value.length <= 240 && !value.startsWith("/") && !value.includes("\\") && !value.split("/").some((part) => part === "" || part === "." || part === "..");
}

async function auditWorkspaceManifest(manifest: {
  schema_version: string;
  kit_version?: string;
  paths: string[];
  managed_file_hashes?: Record<string, string>;
  candidate_asset_status?: { photo_question_answered?: boolean; signature_question_answered?: boolean };
}): Promise<Record<string, unknown>> {
  const paths = new Set(manifest.paths);
  const missing = REQUIRED_WORKSPACE_PATHS.filter((required) => !paths.has(required) && ![...paths].some((path) => path.startsWith(`${required}/`)));
  const updateRequired = manifest.kit_version !== WORKSPACE_KIT_VERSION;
  const expectedHashes = await expectedManagedHashes();
  const managedHashes = manifest.managed_file_hashes ?? {};
  const hashMismatches = Object.entries(expectedHashes)
    .filter(([path, hash]) => managedHashes[path] !== hash)
    .map(([path]) => path);
  const needsManagedUpdate = updateRequired || hashMismatches.length > 0;
  const status = missing.length || needsManagedUpdate ? "action_required" : "workspace_current";
  return {
    status,
    schema_version: "1.0",
    kit_version: WORKSPACE_KIT_VERSION,
    minimum_supported_version: WORKSPACE_KIT_VERSION,
    workspace_update_required: workspaceUpdateDirective(status),
    missing_paths: missing,
    managed_hash_mismatches: hashMismatches,
    update: needsManagedUpdate
      ? {
          available: true,
          safe_only: true,
          message: "Update MCP-managed templates and scripts only. Never overwrite profile, source documents, voice samples, assets, jobs, or applications."
        }
      : { available: false },
    typography: {
      profile: "latex-lmodern-roman",
      status: hashMismatches.some((path) => path.startsWith("application-kit/templates/cover_letter.")) ? "template_mismatch" : "verified_by_managed_hash",
      message: "Cover letters must match the historical pdfTeX/Latin Modern Roman application style."
    },
    reminders: {
      photo_question_required: !manifest.candidate_asset_status?.photo_question_answered,
      signature_question_required: !manifest.candidate_asset_status?.signature_question_answered,
      privacy: "Manifest must contain relative paths, version state, and managed-file hashes only. Do not include CV text, names, absolute paths, photos, signatures, or document contents."
    },
    checker_boundary: "This audit does not expose or reproduce private writing-checker rules."
  };
}

function jsonText(value: unknown): { content: Array<{ type: "text"; text: string }> } {
  const output =
    value && typeof value === "object" && !Array.isArray(value) && !("workspace_update_required" in value)
      ? { workspace_update_required: workspaceUpdateDirective(), ...value }
      : value;
  return {
    content: [
      {
        type: "text",
        text: `${JSON.stringify(output, null, 2)}\n`
      }
    ]
  };
}

async function createServer(): Promise<McpServer> {
  const instructions = await onboardingInstructions();
  const server = new McpServer(
    {
      name: "student-application-ai-helper",
      version: VERSION
    },
    {
      instructions,
      capabilities: {
        logging: {}
      }
    }
  );

  server.registerResource(
    "onboarding-instructions",
    "application-package://onboarding",
    {
      title: "Student Application AI Helper Onboarding",
      description: "Operating instructions for AI agents using this student writing helper.",
      mimeType: "text/markdown"
    },
    async (uri) => ({
      contents: [{ uri: uri.href, text: instructions }]
    })
  );

  server.registerResource(
    "client-skill",
    "application-package://client-skill/SKILL.md",
    {
      title: "Client Skill",
      description: "A sample skill that students can install locally.",
      mimeType: "text/markdown"
    },
    async (uri) => ({
      contents: [{ uri: uri.href, text: await readResource("client-skill/SKILL.md") }]
    })
  );

  server.registerTool(
    "health",
    {
      title: "Health",
      description: "Return service health, storage mode, and onboarding resource locations."
    },
    async () =>
      jsonText({
        ok: true,
        service: "student-application-ai-helper",
        version: VERSION,
        mode: "local-kit-plus-private-writing-checker",
        workspaceKitVersion: WORKSPACE_KIT_VERSION,
        persistentProfiles: false,
        remoteProcessing: "transient writing checks and ATS CV/JD checks only",
        tokenRequired: Boolean(TOKEN),
        workspace_update_required: workspaceUpdateDirective(),
        tools: PUBLIC_TOOLS,
        resources: [
          "application-package://onboarding",
          "application-package://client-skill/SKILL.md"
        ]
      })
  );

  server.registerTool(
    "get_onboarding_instructions",
    {
      title: "Get Onboarding Instructions",
      description: "Return instructions an AI agent should follow before creating a student writing workspace."
    },
    async () => jsonText({ instructions })
  );

  server.registerTool(
    "audit_workspace_manifest",
    {
      title: "Audit Workspace Manifest",
      description: "Compare a privacy-safe local workspace manifest with the public workspace contract. This tool never reads the caller's filesystem and must not receive document content or absolute paths.",
      inputSchema: {
        schema_version: z.literal("1.0"),
        kit_version: z.string().max(80).optional(),
        paths: z.array(z.string().min(1).max(240).refine(safeRelativePath, "Path must be a safe, non-empty relative POSIX path.")).max(300),
        managed_file_hashes: z.record(z.string().max(240).refine(safeRelativePath), z.string().regex(/^[a-f0-9]{32,128}$/i)).optional(),
        candidate_asset_status: z.object({
          photo_question_answered: z.boolean().optional(),
          signature_question_answered: z.boolean().optional()
        }).optional()
      }
    },
    async (manifest) => jsonText(await auditWorkspaceManifest(manifest))
  );

  server.registerTool(
    "get_client_skill",
    {
      title: "Get Client Skill",
      description: "Return a sample SKILL.md for a student's local AI agent."
    },
    async () =>
      jsonText({
        path: "application-client-skill/SKILL.md",
        content: await readResource("client-skill/SKILL.md")
      })
  );

  server.registerTool(
    "get_workspace_template",
    {
      title: "Get Workspace Template",
      description: "Return the starter folder/files a local AI agent should create on a student machine."
    },
    async () =>
      jsonText({
        root: "student-application-workspace",
        files: await readTemplateDirectory("workspace-template")
      })
  );

  server.registerTool(
    "get_application_kit_manifest",
    {
      title: "Get Application Kit Manifest",
      description: "Return the current local-only application kit version and file list."
    },
    async () =>
      jsonText({
        manifest: JSON.parse(await readResource("application-kit/manifest.json"))
      })
  );

  server.registerTool(
    "get_application_kit_bundle",
    {
      title: "Get Application Kit Bundle",
      description: "Return local-only templates, contracts, scripts, and examples for deterministic application generation."
    },
    async () =>
      jsonText({
        root: "application-kit",
        manifest: JSON.parse(await readResource("application-kit/manifest.json")),
        files: await readTemplateDirectory("application-kit")
      })
  );

  server.registerTool(
    "get_sample_prompts",
    {
      title: "Get Sample Prompts",
      description: "Return user-facing sample prompts and expected outputs for local application work."
    },
    async () =>
      jsonText({
        path: "sample-prompts.md",
        content: await samplePromptsDocument()
      })
  );

  server.registerTool(
    "check_ats_resume_fit",
    {
      title: "Check ATS Resume Fit",
      description:
        "Compare the current CV/resume text with a job description and return an ATS-style score, matched keywords, missing keywords, risks, and human-in-the-loop revision guidance. Submitted text is processed transiently and not stored.",
      inputSchema: {
        document_kind: z.enum(["cv", "resume"]).default("cv").optional(),
        market: z.string().max(80).optional(),
        language: z.string().max(40).optional(),
        role_family: z.string().max(120).optional(),
        company_name: z.string().max(200).optional(),
        job_title: z.string().max(220).optional(),
        job_description: z.string().min(1).max(24000).describe("Current job description text. Do not send unrelated private files."),
        resume_text: z.string().min(1).max(24000).describe("Current extracted CV/resume text."),
        resume_sections: z.record(z.string().max(80), z.string().max(8000)).optional(),
        known_evidence_terms: z.array(z.string().min(1).max(120)).max(200).optional(),
        protected_facts: z.array(z.string().min(1).max(160)).max(100).optional(),
        target_score: z.number().int().min(40).max(95).default(70).optional(),
        max_new_terms: z.number().int().min(1).max(20).default(12).optional()
      }
    },
    async (input) => jsonText(checkAtsResumeFit(input))
  );

  server.registerTool(
    "check_writing_human_fit",
    {
      title: "Check Writing",
      description:
        "Privately check selected writing for reader fit, evidence risk, academic/application conventions, and AI-like patterns. Submitted text is processed transiently and not stored.",
      inputSchema: {
        text: z.string().min(1).max(12000).describe("The selected writing text to check. Send only the section that needs feedback."),
        mode: z
          .enum(["application", "academic", "blog", "work", "social", "general"])
          .default("general")
          .describe("Writing mode to evaluate."),
        audience: z.string().max(200).optional().describe("Optional target reader, such as recruiter, professor, supervisor, or public reader."),
        purpose: z.string().max(300).optional().describe("Optional purpose of the text.")
      }
    },
    async ({ text, mode, audience, purpose }) =>
      jsonText(
        checkWritingHumanFit({
          text,
          mode,
          audience,
          purpose
        })
      )
  );

  server.registerTool(
    "suggest_writing_revision",
    {
      title: "Suggest Revision",
      description:
        "Return a practical revision plan for selected writing. This does not store raw text and does not expose private checker rules.",
      inputSchema: {
        text: z.string().min(1).max(12000).describe("The selected writing text to improve."),
        mode: z
          .enum(["application", "academic", "blog", "work", "social", "general"])
          .default("general")
          .describe("Writing mode to evaluate."),
        audience: z.string().max(200).optional().describe("Optional target reader."),
        purpose: z.string().max(300).optional().describe("Optional purpose of the text.")
      }
    },
    async ({ text, mode, audience, purpose }) => {
      const result = checkWritingHumanFit({ text, mode, audience, purpose });
      return jsonText({
        mode: result.mode,
        riskLevel: result.riskLevel,
        summary: result.summary,
        styleReview: result.styleReview,
        revisionPlan: result.revisionPlan,
        topIssues: result.issues.slice(0, 8),
        doNotDo: result.doNotDo,
        privacy: result.privacy
      });
    }
  );

  return server;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function renderMarkdownAsHtml(markdown: string, title: string): Promise<string> {
  const kitManifest = JSON.parse(await readResource("application-kit/manifest.json"));
  const lines = markdown.split(/\r?\n/);
  const body: string[] = [];
  let inCode = false;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.startsWith("```")) {
      inCode = !inCode;
      body.push(inCode ? "<pre><code>" : "</code></pre>");
      continue;
    }
    if (inCode) {
      body.push(`${escapeHtml(line)}\n`);
      continue;
    }
    if (!line.trim()) {
      body.push("");
      continue;
    }
    if (line.startsWith("# ")) {
      body.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
      continue;
    }
    if (line.startsWith("## ")) {
      body.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
      continue;
    }
    const imageMatch = line.match(/^!\[(.+?)\]\((\/assets\/[A-Za-z0-9._/-]+)\)$/);
    if (imageMatch) {
      body.push(
        `<figure class="diagram"><img src="${escapeHtml(imageMatch[2])}" alt="${escapeHtml(imageMatch[1])}"></figure>`
      );
      continue;
    }
    if (line.startsWith("- ")) {
      body.push(`<p class="bullet">• ${escapeHtml(line.slice(2))}</p>`);
      continue;
    }
    body.push(`<p>${escapeHtml(line)}</p>`);
  }

  return [
    "<!doctype html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="utf-8">',
    `<title>${escapeHtml(title)}</title>`,
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<style>",
    ":root { color-scheme: light; --ink:#171717; --muted:#5f6368; --line:#dedbd2; --paper:#fffaf0; --accent:#1f7a68; --accent2:#b74b35; }",
    "body { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #fffaf0; color: var(--ink); }",
    "main { max-width: 960px; margin: 0 auto; padding: 28px 22px 64px; }",
    ".hero { background: #18332f; color: #fffaf0; padding: 26px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 18px 40px rgba(24,51,47,.16); }",
    ".status { display:inline-block; margin-bottom:12px; padding:6px 10px; border-radius:999px; background:#d7f4dc; color:#153b2f; font-size:13px; font-weight:800; }",
    ".kit { display:grid; grid-template-columns: repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin-top:18px; }",
    ".kit div { background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.22); border-radius:10px; padding:12px; }",
    ".kit strong { display:block; font-size:13px; color:#cce7d3; margin-bottom:4px; }",
    ".links { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }",
    ".links a { display: inline-block; padding: 10px 14px; border-radius: 6px; background: #f4e7ce; color: #18332f; text-decoration: none; font-weight: 700; }",
    "h1 { font-size: 30px; margin: 0 0 12px; }",
    "h2 { margin-top: 28px; font-size: 20px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }",
    "p { line-height: 1.6; margin: 0 0 10px; }",
    ".bullet { margin-left: 16px; }",
    "pre { background: #18332f; color: #fffaf0; padding: 16px; border-radius: 8px; overflow-x: auto; }",
    ".diagram { margin: 22px 0 28px; padding: 14px; background: white; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 12px 28px rgba(24,51,47,.08); }",
    ".diagram img { display: block; width: min(100%, 760px); height: auto; margin: 0 auto; }",
    ".meta { margin-top: 28px; font-size: 14px; color: #475569; }",
    "</style>",
    "</head>",
    "<body>",
    "<main>",
    '<section class="hero">',
    '<div class="status">LOCAL-FIRST APPLICATION WORKSPACE</div>',
    "<h1>Job MCP by pmlecuong</h1>",
    "<p>A guided local workflow for preparing evidence, an editable CV, and a reviewed cover letter. The MCP supplies safe kit guidance and optional selected-text feedback; the private application workspace stays on the candidate laptop.</p>",
    '<div class="kit">',
    `<div><strong>Kit version</strong>${escapeHtml(String(kitManifest.version))}</div>`,
    `<div><strong>Local SOP</strong>Workspace audit and release evidence</div>`,
    `<div><strong>Privacy</strong>Source documents stay on the candidate laptop</div>`,
    `<div><strong>Review boundary</strong>Privacy-safe manifest or selected text only</div>`,
    "</div>",
    '<div class="links"><a href="/">Start Here</a><a href="/sample-prompts">Copy Prompts</a><a href="/privacy">Privacy</a></div>',
    "</section>",
    ...body,
    '<div class="meta">This page supports the AI-agent connection address at <code>/mcp</code>.</div>',
    "</main>",
    "</body>",
    "</html>",
    ""
  ].join("\n");
}

function renderLandingPage(): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Student Application AI Helper</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {
  --paper: #fff8ea;
  --paper-2: #f4efe2;
  --ink: #17130f;
  --muted: #62594d;
  --line: #dfd4bd;
  --green: #167766;
  --green-dark: #123f37;
  --mint: #bff3cf;
  --rust: #c9573d;
  --gold: #f4c765;
  --sky: #9ad9ff;
  --rose: #ffb5a4;
  --lav: #c9bcff;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at 8% 8%, rgba(255,181,164,.32), transparent 28%),
    radial-gradient(circle at 85% 14%, rgba(154,217,255,.32), transparent 30%),
    linear-gradient(180deg, var(--paper), #fffdf7 48%, var(--paper-2));
}
a { color: inherit; }
.page { min-height: 100vh; overflow: hidden; }
.nav {
  width: min(1120px, calc(100% - 40px));
  margin: 0 auto;
  padding: 22px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}
.brand { font-weight: 900; letter-spacing: 0; display: inline-flex; align-items: center; gap: 8px; }
.navlinks { display: flex; align-items: center; gap: 18px; color: var(--muted); font-size: 14px; }
.navlinks a { text-decoration: none; padding: 8px 0; }
.hero {
  width: min(1120px, calc(100% - 40px));
  min-height: calc(100vh - 88px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(340px, .98fr);
  gap: 58px;
  align-items: center;
  padding: 34px 0 88px;
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255,255,255,.65);
  color: var(--green-dark);
  font-size: 13px;
  font-weight: 750;
  box-shadow: 0 10px 30px rgba(18,63,55,.08);
}
.dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; }
h1 {
  margin: 24px 0 22px;
  font-size: clamp(48px, 8vw, 96px);
  line-height: .94;
  letter-spacing: 0;
  max-width: 880px;
}
.lead {
  max-width: 690px;
  font-size: clamp(18px, 2.2vw, 23px);
  line-height: 1.42;
  color: #443f38;
  margin: 0 0 34px;
}
.actions { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.button {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 18px;
  border-radius: 7px;
  font-weight: 800;
  text-decoration: none;
  border: 1px solid transparent;
}
.primary { background: var(--green-dark); color: #fffaf0; }
.secondary { border-color: var(--line); background: rgba(255,255,255,.42); color: var(--ink); }
.button:hover { transform: translateY(-1px); box-shadow: 0 12px 28px rgba(18,63,55,.12); }
.connection {
  margin-top: 26px;
  width: min(100%, 620px);
  border-left: 4px solid var(--rust);
  padding: 10px 0 10px 14px;
  color: var(--muted);
  font-size: 14px;
}
.connection code { color: var(--ink); font-weight: 750; overflow-wrap: anywhere; }
.visual {
  position: relative;
  min-height: 590px;
  border-radius: 16px;
  background:
    linear-gradient(145deg, rgba(30,111,95,.9), rgba(22,61,54,.96)),
    radial-gradient(circle at 70% 20%, rgba(242,193,102,.7), transparent 38%);
  color: #fffaf0;
  padding: 32px;
  box-shadow: 0 30px 80px rgba(24,51,47,.18);
  overflow: hidden;
  animation: floatCard 8s ease-in-out infinite;
}
.visual:before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255,250,240,.08) 1px, transparent 1px),
    linear-gradient(0deg, rgba(255,250,240,.08) 1px, transparent 1px);
  background-size: 46px 46px;
  mask-image: linear-gradient(to bottom, black, transparent 78%);
}
.bubble {
  position: absolute;
  border-radius: 999px;
  opacity: .9;
}
.bubble.one { width: 88px; height: 88px; right: 28px; top: 24px; background: var(--gold); }
.bubble.two { width: 54px; height: 54px; right: 110px; bottom: 26px; background: var(--sky); }
.panel {
  position: relative;
  background: rgba(255,250,240,.12);
  border: 1px solid rgba(255,250,240,.24);
  border-radius: 12px;
  padding: 18px;
  backdrop-filter: blur(8px);
}
.panel + .panel { margin-top: 20px; }
.panel small { display:block; color:#d8f3df; font-weight:800; margin-bottom:8px; }
.panel p { margin:0; line-height:1.45; }
.flow { position: relative; margin: 24px 0; display: grid; gap: 14px; }
.step {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 12px;
  align-items: start;
  padding: 15px;
  background: rgba(255,250,240,.95);
  color: var(--ink);
  border-radius: 12px;
}
.num {
  width: 34px; height: 34px; display: grid; place-items: center;
  background: var(--gold); border-radius: 50%; font-weight: 900;
}
.step strong { display:block; margin-bottom:4px; }
.step span { color: var(--muted); font-size: 14px; line-height: 1.4; }
section { width: min(1120px, calc(100% - 40px)); margin: 0 auto; padding: 92px 0; border-top: 1px solid var(--line); }
.section-title { font-size: clamp(30px, 4vw, 52px); line-height: 1; margin: 0 0 14px; max-width: 760px; }
.section-copy { max-width: 760px; color: var(--muted); font-size: 18px; line-height: 1.55; margin: 0 0 38px; }
.grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 22px; }
.tile { padding: 24px; border: 1px solid var(--line); border-top: 4px solid var(--green); border-radius: 14px; background: rgba(255,255,255,.55); }
.tile .icon { display: inline-grid; place-items: center; width: 40px; height: 40px; border-radius: 12px; background: #e7f7df; margin-bottom: 14px; font-size: 21px; }
.tile h3 { margin: 0 0 10px; font-size: 20px; }
.tile p { margin: 0; color: var(--muted); line-height: 1.55; }
.prompt {
  background: #18332f;
  color: #fffaf0;
  border-radius: 14px;
  padding: 26px;
  overflow-x: auto;
  line-height: 1.55;
  font-size: 15px;
  white-space: pre-wrap;
  box-shadow: 0 20px 60px rgba(18,63,55,.14);
}
.sequence {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
  align-items: stretch;
  margin-top: 34px;
}
.actor {
  position: relative;
  min-height: 280px;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.62);
}
.actor:after {
  content: "→";
  position: absolute;
  right: -22px;
  top: 50%;
  transform: translateY(-50%);
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--gold);
  color: var(--ink);
  font-weight: 900;
  z-index: 2;
}
.actor:last-child:after { display: none; }
.actor .emoji { font-size: 34px; margin-bottom: 14px; }
.actor h3 { margin: 0 0 8px; font-size: 22px; }
.actor p { margin: 0 0 18px; color: var(--muted); line-height: 1.5; }
.actor ul { margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.65; }
.comparison {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
  gap: 34px;
  align-items: center;
}
.chart {
  position: relative;
  min-height: 420px;
  border-radius: 18px;
  border: 1px solid var(--line);
  background:
    linear-gradient(90deg, rgba(23,19,15,.08) 1px, transparent 1px),
    linear-gradient(0deg, rgba(23,19,15,.08) 1px, transparent 1px),
    rgba(255,255,255,.68);
  background-size: 78px 78px;
  padding: 24px;
  overflow: hidden;
}
.axis-x, .axis-y { position: absolute; color: var(--muted); font-size: 13px; font-weight: 750; }
.axis-x { bottom: 18px; right: 26px; }
.axis-y { left: 18px; top: 24px; writing-mode: vertical-rl; transform: rotate(180deg); }
.point {
  position: absolute;
  transform: translate(-50%, 50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 3px solid #fffaf0;
  box-shadow: 0 10px 24px rgba(23,19,15,.18);
}
.point span {
  position: absolute;
  left: 18px;
  bottom: 14px;
  min-width: 190px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #fffaf0;
  color: var(--ink);
  font-size: 13px;
  font-weight: 800;
  border: 1px solid var(--line);
}
.p1 { left: 24%; bottom: 26%; background: var(--rose); }
.p2 { left: 54%; bottom: 58%; background: var(--gold); }
.p3 { left: 78%; bottom: 78%; background: var(--green); }
.legend { display: grid; gap: 14px; }
.legend-item { display: grid; grid-template-columns: 16px 1fr; gap: 12px; align-items: start; color: var(--muted); line-height: 1.5; }
.swatch { width: 16px; height: 16px; border-radius: 50%; margin-top: 4px; }
.swatch.rose { background: var(--rose); }
.swatch.gold { background: var(--gold); }
.swatch.green { background: var(--green); }
.privacy-list { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 18px; }
.privacy-item { border-top: 3px solid var(--rust); padding: 20px 0 0; color: var(--muted); line-height: 1.55; }
.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: -18px;
  color: var(--green-dark);
  font-weight: 800;
  text-decoration: none;
  border-bottom: 2px solid rgba(22,119,102,.26);
}
.detail-link:hover { border-bottom-color: var(--green-dark); }
.footer { width: min(1120px, calc(100% - 40px)); margin: 0 auto; padding: 44px 0 56px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--line); display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; }
.footer a { color: var(--green-dark); font-weight: 750; }
.built-by { display:inline-flex; align-items:center; gap:8px; text-decoration:none; padding:10px 12px; border-radius:999px; background:#fffaf0; border:1px solid var(--line); }
@keyframes floatCard {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@media (max-width: 860px) {
  .nav { align-items: flex-start; }
  .navlinks { gap: 12px; flex-wrap: wrap; justify-content: flex-end; }
  .hero { grid-template-columns: 1fr; padding-top: 18px; gap: 34px; }
  .visual { min-height: auto; }
  .grid, .privacy-list, .sequence, .comparison { grid-template-columns: 1fr; }
  .actor:after { content: "↓"; right: calc(50% - 21px); top: auto; bottom: -30px; transform: none; }
  .actor { min-height: auto; }
  .chart { min-height: 380px; }
  h1 { font-size: clamp(46px, 16vw, 76px); }
}
@media (max-width: 520px) {
  .nav, .hero, section, .footer { width: min(100% - 28px, 1120px); }
  .nav { display:block; }
  .navlinks { margin-top: 12px; justify-content: flex-start; }
  .button { width: 100%; }
  .visual { padding: 18px; }
  section { padding: 74px 0; }
  .point span { min-width: 134px; font-size: 12px; }
}
</style>
</head>
<body>
<div class="page">
  <nav class="nav" aria-label="Main navigation">
    <div class="brand">🧭 Student Application AI Helper</div>
    <div class="navlinks">
      <a href="#start">Start</a>
      <a href="#flow">Flow</a>
      <a href="#compare">Compare</a>
      <a href="#checker">Writing checker</a>
      <a href="/sample-prompts">Prompts</a>
      <a href="#privacy">Privacy</a>
    </div>
  </nav>
  <main class="hero">
    <div>
      <div class="eyebrow"><span class="dot"></span> Free local AI helper for student writing</div>
      <h1>Build better applications without giving away your files.</h1>
      <p class="lead">Use your own AI agent to prepare CV helpers, cover letters, academic sections, and other important writing on your laptop. When you want a second opinion, send only the selected text to the private checker.</p>
      <div class="actions">
        <a class="button primary" href="/sample-prompts">✨ Copy the start prompt</a>
        <a class="button secondary" href="#flow">👀 See the flow</a>
      </div>
      <div class="connection">Start URL for your AI app:<br><code>${PUBLIC_SITE_URL}</code></div>
    </div>
    <aside class="visual" aria-label="How the helper works">
      <div class="bubble one"></div>
      <div class="bubble two"></div>
      <div class="panel">
        <small>LOCAL WORKSPACE</small>
        <p>Your CV, notes, job posts, drafts, and final documents stay on your laptop.</p>
      </div>
      <div class="flow">
        <div class="step"><div class="num">1</div><div><strong>Set up the helper</strong><span>Your AI agent gets the starter files and simple instructions.</span></div></div>
        <div class="step"><div class="num">2</div><div><strong>Draft locally</strong><span>The agent reads your local sources and creates the document on your machine.</span></div></div>
        <div class="step"><div class="num">3</div><div><strong>Check selected text</strong><span>The private checker returns reader, tone, and convention feedback.</span></div></div>
      </div>
      <div class="panel">
        <small>PRIVATE CHECKER</small>
        <p>It gives feedback for application, academic, blog, work, social, and general writing modes.</p>
      </div>
    </aside>
  </main>
  <section id="how">
    <h2 class="section-title">Clear jobs. No technical maze.</h2>
    <p class="section-copy">Students only need to know what to ask their AI agent. The helper handles the setup instructions, local document flow, and optional writing check behind the scenes.</p>
    <div class="grid">
      <div class="tile"><div class="icon">📄</div><h3>Prepare documents</h3><p>Create a one-page cover letter draft, a CV overview helper, and review notes from local evidence.</p></div>
      <div class="tile"><div class="icon">🪄</div><h3>Improve writing</h3><p>Check selected text for generic phrasing, weak evidence, awkward tone, and mode-specific convention problems.</p></div>
      <div class="tile"><div class="icon">🔒</div><h3>Keep control</h3><p>You decide which text is checked. The service does not need your whole workspace or private files.</p></div>
    </div>
  </section>
  <section id="flow">
    <h2 class="section-title">How the private checker fits in.</h2>
    <p class="section-copy">The flow has three parties: the student, the student laptop with the local AI agent, and the MCP server. Your laptop does the drafting. The server only reviews the text you choose to send and returns practical feedback.</p>
    <a class="detail-link" href="/technical-flow">Open the detailed technical flow →</a>
    <div class="sequence" aria-label="Sequence diagram">
      <div class="actor">
        <div class="emoji">🧑‍🎓</div>
        <h3>Student</h3>
        <p>Chooses the task, reviews the final writing, and decides what text can be checked.</p>
        <ul>
          <li>Adds CV and notes locally</li>
          <li>Approves selected text check</li>
          <li>Reviews final output</li>
        </ul>
      </div>
      <div class="actor">
        <div class="emoji">💻</div>
        <h3>Laptop + local AI agent</h3>
        <p>Reads the local folder, drafts locally, renders files locally, and sends only selected text.</p>
        <ul>
          <li>Keeps source files private</li>
          <li>Creates draft and CV helper</li>
          <li>Applies checker feedback locally</li>
        </ul>
      </div>
      <div class="actor">
        <div class="emoji">🧠</div>
        <h3>MCP checker server</h3>
        <p>Reviews the selected writing and returns issues, risk level, and revision guidance.</p>
        <ul>
          <li>No full workspace needed</li>
          <li>Only feedback is returned</li>
          <li>Selected text processed transiently</li>
        </ul>
      </div>
    </div>
  </section>
  <section id="start">
    <h2 class="section-title">Start with one prompt.</h2>
    <p class="section-copy">Paste this into your AI agent after adding the connection address above.</p>
    <pre class="prompt">Set up my Student Application AI Helper workspace.
Use the service only for starter files, instructions, and selected writing checks.
Keep my CV, notes, job posts, drafts, and final documents on my laptop.
After setup, show me the folder I should fill and the next action.</pre>
  </section>
  <section id="compare">
    <div class="comparison">
      <div>
        <h2 class="section-title">Why the checker helps.</h2>
        <p class="section-copy">A normal AI agent can write quickly, but it often sounds generic. A local folder improves factual accuracy. The private checker adds one more layer: reader fit, tone risk, convention checks, and revision guidance.</p>
        <div class="legend">
          <div class="legend-item"><span class="swatch rose"></span><span><strong>Normal AI agent:</strong> fast, but often generic and less grounded.</span></div>
          <div class="legend-item"><span class="swatch gold"></span><span><strong>Local folder:</strong> stronger facts because the agent reads the student's own sources.</span></div>
          <div class="legend-item"><span class="swatch green"></span><span><strong>MCP checker:</strong> strongest flow because the local draft receives private checker feedback before final review.</span></div>
        </div>
      </div>
      <div class="chart" aria-label="Comparison chart">
        <div class="axis-y">Reader trust</div>
        <div class="axis-x">Personal evidence and feedback depth</div>
        <div class="point p1"><span>Normal AI only</span></div>
        <div class="point p2"><span>Local folder helper</span></div>
        <div class="point p3"><span>Local helper + MCP checker</span></div>
      </div>
    </div>
  </section>
  <section id="checker">
    <h2 class="section-title">The checker reviews the writing, not your whole life.</h2>
    <p class="section-copy">Send a paragraph, cover letter, thesis section, overview, literature review excerpt, work update, or social post. Choose the mode and the checker returns what to improve.</p>
    <div class="grid">
      <div class="tile"><div class="icon">🎯</div><h3>Application</h3><p>Role fit, evidence, recruiter clarity, overclaiming, and generic cover-letter language.</p></div>
      <div class="tile"><div class="icon">📚</div><h3>Academic</h3><p>Claim strength, research anchors, citation gaps, overstatement, and formal convention issues.</p></div>
      <div class="tile"><div class="icon">✍️</div><h3>Blog and work</h3><p>Reader value, human rhythm, practical clarity, flat AI phrasing, and missing context.</p></div>
    </div>
  </section>
  <section id="privacy">
    <h2 class="section-title">Private by design.</h2>
    <p class="section-copy">The safest workflow is local first. The server gives reusable help and checks only the text you intentionally submit.</p>
    <div class="privacy-list">
      <div class="privacy-item"><strong>Stays on your laptop:</strong> CV files, personal notes, job posts, drafts, PDFs, and final outputs.</div>
      <div class="privacy-item"><strong>Sent only when you ask:</strong> selected text for writing feedback, plus a writing mode such as application or academic.</div>
      <div class="privacy-item"><strong>Returned to you:</strong> clear feedback, risk level, and practical revision guidance for the selected text.</div>
      <div class="privacy-item"><strong>Not promised:</strong> a fake detector bypass. The goal is clearer, more trustworthy, more human writing.</div>
    </div>
  </section>
  <footer class="footer">
    <p>For students and AI agents: start at <a href="${PUBLIC_SITE_URL}">${PUBLIC_SITE_URL}</a>. Human prompts are at <a href="/sample-prompts">/sample-prompts</a>. Service status is at <a href="/health">/health</a>.</p>
    <p>MCP v${VERSION} · workspace kit ${WORKSPACE_KIT_VERSION}</p>
    <a class="built-by" href="https://pmlecuong.com/" target="_blank" rel="noopener noreferrer">Built by pmlecuong.com ↗</a>
  </footer>
</div>
</body>
</html>`;
}

function renderSiteNav(active = ""): string {
  const items = [
    ["/start", "Start"],
    ["/examples", "Examples"],
    ["/docs", "Docs"],
    ["/technical-flow", "Technical"]
  ];
  return `<nav class="site-nav" aria-label="Main navigation">
    <a class="brand" href="/"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M8 8V6.6C8 5.7 8.7 5 9.6 5h4.8c.9 0 1.6.7 1.6 1.6V8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M4.8 8h14.4c.9 0 1.6.7 1.6 1.6v7.8c0 .9-.7 1.6-1.6 1.6H4.8c-.9 0-1.6-.7-1.6-1.6V9.6c0-.9.7-1.6 1.6-1.6Z" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 13h17M10 13v1.1h4V13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></span><span>Job MCP<em>by pmlecuong</em></span></a>
    <div class="navlinks">${items
      .map(([href, label]) => `<a${active === href ? ' aria-current="page"' : ""} href="${href}">${label}</a>`)
      .join("")}</div>
  </nav>`;
}

function renderSiteFooter(): string {
  return `<footer class="site-footer">
    <span>MCP v${VERSION} · kit ${WORKSPACE_KIT_VERSION}</span>
    <span><a href="/health">Health</a> · <a href="/privacy">Privacy</a> · <a href="/mcp">MCP endpoint</a> · <a href="https://pmlecuong.com/" target="_blank" rel="noopener noreferrer">Built by pmlecuong.com ↗</a></span>
  </footer>`;
}

function renderSiteChrome(title: string, active: string, body: string, bodyClass = ""): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --blue:#071dff; --blue-soft:#1737ff; --paper:#f6f2e8; --white:#fffdf6; --ink:#090b10; --muted:#5e6470; --line:rgba(9,11,16,.16); --yellow:#edff45; --green:#0a4c3f; --mint:#dcf5e6; --dark:#04050d; }
* { box-sizing:border-box; } html { scroll-behavior:smooth; overflow-x:hidden; } body { margin:0; overflow-x:hidden; color:var(--ink); background:var(--paper); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
a { color:inherit; } code, pre { font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; } .blue-page { background:var(--blue); color:white; }
.site-nav { position:relative; z-index:5; min-height:84px; width:min(1220px, calc(100% - 44px)); margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:22px; }
.brand { display:flex; align-items:center; gap:12px; color:inherit; text-decoration:none; font-weight:900; line-height:.92; letter-spacing:-.04em; } .brand-mark { display:grid; place-items:center; width:38px; height:34px; border:1px solid currentColor; border-radius:10px; font-size:16px; } .brand-mark svg { width:22px; height:22px; display:block; } .brand em { display:block; margin-top:2px; font-style:normal; font-size:11px; letter-spacing:.04em; opacity:.82; }
.navlinks { display:flex; gap:24px; align-items:center; flex-wrap:wrap; font-size:13px; font-weight:850; letter-spacing:.08em; text-transform:uppercase; } .navlinks a { text-decoration:none; opacity:.82; } .navlinks a:hover, .navlinks a[aria-current="page"] { opacity:1; text-decoration:underline; text-underline-offset:5px; }
.home-hero { min-height:calc(100svh - 84px); width:min(1220px, calc(100% - 44px)); margin:0 auto; display:grid; grid-template-columns:minmax(0,.86fr) minmax(390px,.78fr); gap:82px; align-items:center; padding:54px 0 86px; }
.mono { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; letter-spacing:.22em; font-size:12px; font-weight:800; }
h1 { margin:18px 0 22px; max-width:660px; font-family:Georgia,"Times New Roman",serif; font-size:clamp(48px,6.1vw,82px); line-height:.88; letter-spacing:-.06em; font-weight:400; text-transform:uppercase; }
.lead { max-width:660px; margin:0; color:var(--muted); font-size:clamp(18px,2vw,24px); line-height:1.45; } .blue-panel .lead, .blue-page .lead { color:rgba(255,255,255,.82); }
.actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:32px; } .button { display:inline-flex; min-height:48px; align-items:center; justify-content:center; padding:0 20px; border:1px solid currentColor; text-decoration:none; font-weight:900; font-size:13px; letter-spacing:.08em; text-transform:uppercase; transition:transform .16s ease, background .16s ease; } .button:hover { transform:translateY(-2px); } .button.primary { background:var(--yellow); color:var(--blue); border-color:var(--yellow); } .button.secondary { background:transparent; color:inherit; }
.command { margin-top:26px; width:min(100%,620px); background:var(--white); color:var(--blue); border:1px solid rgba(255,255,255,.52); box-shadow:0 26px 80px rgba(0,0,0,.22); } .command-tabs { display:flex; justify-content:space-between; align-items:center; gap:18px; padding:14px 17px 0; color:rgba(0,0,242,.62); font-size:12px; font-weight:900; } .command-labels { display:flex; gap:18px; flex-wrap:wrap; } .command pre { margin:0; padding:17px; white-space:pre-wrap; line-height:1.5; font-size:13px; }
.blue-panel { margin:0 max(22px, calc((100% - 1320px)/2)); background:var(--blue); color:white; border:1px solid rgba(9,11,16,.1); box-shadow:0 36px 90px rgba(7,29,255,.18); } .blue-panel .home-hero { min-height:calc(100svh - 120px); } .blue-page .blue-panel { margin:0; background:transparent; border:0; box-shadow:none; } .blue-page .blue-panel .home-hero { min-height:calc(100svh - 84px); }
.signal-card { position:relative; min-height:560px; padding:32px; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.32); box-shadow:0 40px 90px rgba(0,0,0,.18); } .signal-card:before { content:""; position:absolute; inset:-18%; background:radial-gradient(circle at 72% 16%, rgba(237,255,69,.95) 0 13%, transparent 14%), repeating-linear-gradient(90deg, rgba(255,255,255,.35) 0 1px, transparent 1px 32px), repeating-linear-gradient(0deg, rgba(255,255,255,.22) 0 1px, transparent 1px 32px); opacity:.55; } .signal-card > * { position:relative; z-index:1; }
.signal-card h2 { margin:0; max-width:390px; font-family:Georgia,"Times New Roman",serif; font-weight:400; font-size:clamp(34px,3.8vw,54px); line-height:.92; letter-spacing:-.052em; text-transform:uppercase; } .signal-list { display:grid; gap:15px; margin:0; padding:0; list-style:none; } .signal-list li { display:grid; grid-template-columns:36px 1fr; gap:13px; align-items:start; padding-top:15px; border-top:1px solid rgba(255,255,255,.28); } .signal-list b { color:var(--yellow); } .signal-list span { color:rgba(255,255,255,.82); line-height:1.42; }
.section { width:min(1220px, calc(100% - 44px)); margin:0 auto; padding:78px 0; border-top:1px solid var(--line); } .section.compact { padding:54px 0; } .section-title { margin:10px 0 12px; max-width:780px; font-size:clamp(34px,4.5vw,58px); line-height:.96; letter-spacing:-.055em; } .blue-page .section-title { font-family:Georgia,"Times New Roman",serif; font-weight:400; text-transform:uppercase; letter-spacing:-.058em; } .section-copy { max-width:760px; margin:0; color:var(--muted); font-size:18px; line-height:1.55; } .blue-page .section { border-top-color:rgba(255,255,255,.28); } .blue-page .section-copy { color:rgba(255,255,255,.78); } .blue-page .mono { color:rgba(255,255,255,.95); }
.door-grid, .feature-grid, .example-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px; margin-top:34px; background:var(--line); border:1px solid var(--line); } .blue-page .door-grid, .blue-page .feature-grid, .blue-page .example-grid { background:rgba(255,255,255,.34); border-color:rgba(255,255,255,.34); } .feature-grid.four-grid, .example-grid.four-grid { grid-template-columns:repeat(4,minmax(0,1fr)); } .feature-grid.usecase-grid, .example-grid.usecase-grid { grid-template-columns:repeat(5,minmax(0,1fr)); } .door, .feature, .example-card { min-height:220px; padding:28px; background:var(--white); color:var(--ink); text-decoration:none; } .blue-page .door, .blue-page .feature, .blue-page .example-card { background:rgba(255,253,246,.96); } .door small, .feature small, .example-card small, .blue-page .door small.mono, .blue-page .feature small.mono, .blue-page .example-card small.mono { display:block; margin-bottom:18px; color:var(--blue); } .door h3, .feature h3, .example-card h3 { margin:0 0 10px; color:var(--ink); font-size:26px; line-height:1; letter-spacing:-.04em; } .door p, .feature p, .example-card p { margin:0; color:var(--muted); line-height:1.5; }
.privacy-strip { width:100%; background:var(--mint); color:var(--ink); } .blue-page .privacy-strip { background:var(--blue); color:white; border-top:1px solid rgba(255,255,255,.28); } .privacy-strip .section { border-top:0; } .privacy-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:22px; margin-top:36px; } .privacy-grid div { padding-top:18px; border-top:2px solid var(--green); } .blue-page .privacy-grid div { border-top-color:var(--yellow); } .privacy-grid strong { display:block; margin-bottom:9px; } .privacy-grid span { color:#395a52; line-height:1.5; } .blue-page .privacy-grid span { color:rgba(255,255,255,.78); }
.final-cta { width:100%; background:var(--dark); color:white; } .final-cta .section { border-top:0; } .final-cta .section-copy { color:rgba(255,255,255,.75); }
.checker-layout { display:grid; grid-template-columns:minmax(280px,.76fr) minmax(0,1fr); gap:54px; align-items:center; margin-top:36px; } .checker-legend { display:grid; gap:14px; margin-top:24px; color:var(--muted); } .blue-page .checker-legend { color:rgba(255,255,255,.78); } .checker-legend > span { display:grid; grid-template-columns:18px 1fr; gap:12px; align-items:start; } .checker-legend strong { color:var(--ink); } .blue-page .checker-legend strong { color:white; } .dot { width:15px; height:15px; margin-top:4px; border-radius:50%; background:var(--blue); } .dot.fast { background:#de745f; } .dot.local { background:#e0b843; } .dot.checked { background:var(--green); } .xy-chart { position:relative; min-height:360px; border:1px solid var(--line); background:linear-gradient(rgba(9,11,16,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(9,11,16,.06) 1px,transparent 1px),var(--white); background-size:64px 64px; } .xy-chart:before,.xy-chart:after { content:""; position:absolute; background:#65716c; } .xy-chart:before { left:62px; right:30px; bottom:55px; height:1px; } .xy-chart:after { left:62px; top:32px; bottom:55px; width:1px; } .axis { position:absolute; color:var(--muted); font-size:11px; font-weight:900; letter-spacing:.08em; text-transform:uppercase; } .axis.x { right:30px; bottom:22px; } .axis.y { left:18px; top:32px; writing-mode:vertical-rl; transform:rotate(180deg); } .point { position:absolute; width:22px; height:22px; border-radius:50%; border:3px solid var(--white); box-shadow:0 8px 20px rgba(0,0,0,.18); } .point b { position:absolute; left:23px; bottom:18px; width:155px; color:var(--ink); font-size:13px; line-height:1.2; } .point p { position:absolute; left:23px; top:20px; width:170px; margin:0; color:var(--muted); font-size:12px; line-height:1.35; } .point.fast { left:25%; bottom:25%; background:#de745f; } .point.local { left:51%; bottom:51%; background:#e0b843; } .point.checked { left:75%; bottom:74%; background:var(--green); }
.tech-shell { display:grid; gap:28px; } .tech-card { background:var(--white); border:1px solid var(--line); padding:24px; } .tech-card img { display:block; width:100%; min-width:720px; height:auto; } .scroll-x { overflow:auto; } .protocol-grid { display:grid; grid-template-columns:190px minmax(0,1fr); border-top:1px solid var(--line); border-left:1px solid var(--line); background:var(--white); } .protocol-grid div { padding:16px 18px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); color:var(--muted); line-height:1.55; } .protocol-grid .method { color:var(--blue); font-weight:900; background:#f8f4e8; } .protocol-note { margin-top:18px; padding-left:16px; border-left:4px solid var(--yellow); color:var(--muted); line-height:1.55; } .blue-page .protocol-note { color:rgba(255,255,255,.78); }
.doc-callout { margin:24px 0; padding:22px; background:var(--dark); color:white; } .doc-callout p { color:rgba(255,255,255,.78) !important; margin:8px 0 0; } .doc-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1px; margin:22px 0; background:var(--line); border:1px solid var(--line); } .doc-tile { background:var(--white); padding:20px; } .doc-tile strong { display:block; margin-bottom:8px; } .doc-tile p { margin:0; }
.site-footer { width:min(1220px, calc(100% - 44px)); margin:0 auto; padding:26px 0 42px; display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; color:var(--muted); font-size:13px; } .blue-page .site-footer { color:rgba(255,255,255,.76); } .site-footer a { font-weight:850; }
.page-hero { width:min(1220px, calc(100% - 44px)); margin:0 auto; padding:74px 0 48px; } .page-hero h1 { max-width:820px; color:inherit; font-size:clamp(50px,6.5vw,88px); } .page-hero .lead { color:var(--muted); } .blue-page .page-hero .lead { color:rgba(255,255,255,.82); }
.steps { display:grid; gap:1px; margin-top:32px; background:var(--line); border:1px solid var(--line); } .blue-page .steps { background:rgba(255,255,255,.34); border-color:rgba(255,255,255,.34); } .step { display:grid; grid-template-columns:92px 1fr; gap:22px; padding:28px; background:var(--white); } .blue-page .step { background:rgba(255,253,246,.96); color:var(--ink); } .step-number { font-family:Georgia,"Times New Roman",serif; font-size:46px; line-height:1; color:var(--blue); } .step h2 { margin:0 0 8px; font-size:26px; } .step p { margin:0; color:var(--muted); line-height:1.55; }
.copy-button { display:inline-flex; align-items:center; justify-content:center; min-height:32px; padding:0 11px; border:1px solid currentColor; background:transparent; color:inherit; font:inherit; font-size:11px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; cursor:pointer; opacity:.84; transition:opacity .16s ease, transform .16s ease, background .16s ease, color .16s ease; } .copy-button:hover { opacity:1; transform:translateY(-1px); } .copy-button.copied { background:var(--yellow); color:var(--blue); border-color:var(--yellow); opacity:1; }
.prompt-panel { margin-top:32px; padding:26px; background:var(--dark); color:white; } .prompt-header { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:16px; } .prompt-panel pre { margin:0; white-space:pre-wrap; line-height:1.5; font-size:13px; }
.ascii-ritual { display:grid; grid-template-columns:minmax(280px,.42fr) minmax(0,1.08fr); gap:34px; align-items:center; } .ascii-ritual-copy { max-width:430px; } .ascii-terminal { position:relative; overflow:visible; border:0; border-radius:0; background:transparent; box-shadow:none; } .ascii-terminal:before { content:""; position:absolute; inset:6% 0 2%; background:radial-gradient(circle at 48% 50%,rgba(184,255,240,.18),transparent 35%),radial-gradient(circle at 55% 54%,rgba(237,255,69,.16),transparent 24%); filter:blur(2px); animation:ascii-pulse 5.8s ease-in-out infinite; pointer-events:none; } .ascii-terminal-inner { position:relative; padding:0; } .ascii-terminal-bar { display:none; } .ascii-lights { display:none; } .ascii-terminal pre { margin:0; min-height:550px; padding:0; border:0; border-radius:0; background:transparent; color:#d8fff8; text-shadow:0 0 12px rgba(184,255,240,.62),0 0 34px rgba(173,255,95,.24); font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:clamp(8px,.9vw,11.5px); line-height:1.16; letter-spacing:-.045em; white-space:pre; overflow:visible; filter:drop-shadow(0 28px 52px rgba(0,0,0,.26)); transform:translateZ(0); } .ascii-caption { display:flex; justify-content:center; gap:18px; padding:12px 0 0; color:rgba(245,251,255,.68); font-size:13px; line-height:1.4; } .ascii-caption span:last-child { display:none; } .ascii-caption strong { color:var(--yellow); } .ascii-bg { color:rgba(158,211,255,.48); } .ascii-water { color:#8feeff; text-shadow:0 0 12px rgba(143,238,255,.28); } .ascii-foam { color:#f5fffd; text-shadow:0 0 18px rgba(236,255,251,.82),0 0 34px rgba(143,238,255,.26); } .ascii-stone-dark { color:#6f89be; } .ascii-stone { color:#c4d6f2; } .ascii-stone-light { color:#fffef0; text-shadow:0 0 18px rgba(184,255,240,.52),0 0 34px rgba(237,255,69,.16); } .ascii-fish { color:#ffe08a; text-shadow:0 0 14px rgba(255,224,138,.86),0 0 34px rgba(173,255,95,.28); } .ascii-dragon { color:#adff5f; text-shadow:0 0 14px rgba(173,255,95,.88),0 0 42px rgba(184,255,240,.36); } @keyframes ascii-pulse { 0%,100% { opacity:.62; transform:scale(.98); } 50% { opacity:1; transform:scale(1.03); } }
.example-grid.showcase { grid-template-columns:minmax(0,.8fr) minmax(280px,.6fr); align-items:start; } .example-grid.showcase .example-card { min-height:auto; } .sample-frame { padding:18px; background:#eef4ee; border:1px solid #c7d5ca; } .blue-page .sample-frame { background:rgba(255,255,255,.14); border-color:rgba(255,255,255,.28); } .sample-frame img { display:block; width:100%; height:auto; background:white; box-shadow:0 18px 42px rgba(0,0,0,.15); }
.cover-showcase { display:grid; grid-template-columns:minmax(300px,.48fr) minmax(420px,1fr); gap:0; margin-top:42px; border:1px solid rgba(255,255,255,.32); background:rgba(255,255,255,.08); box-shadow:0 34px 100px rgba(0,0,0,.22); overflow:hidden; } .cover-notes { padding:34px; background:rgba(255,253,246,.97); color:var(--ink); display:flex; flex-direction:column; justify-content:space-between; gap:34px; } .cover-notes .mono { color:var(--blue); } .cover-notes h3 { margin:16px 0 12px; font-size:clamp(34px,3.4vw,52px); line-height:.92; letter-spacing:-.06em; } .cover-notes p { margin:0; color:var(--muted); font-size:17px; line-height:1.55; } .cover-checks { display:grid; gap:12px; margin:22px 0 0; padding:0; list-style:none; } .cover-checks li { display:grid; grid-template-columns:28px 1fr; gap:12px; align-items:start; color:#323846; line-height:1.42; } .cover-checks b { color:var(--blue); } .cover-actions { display:flex; flex-wrap:wrap; gap:10px; } .cover-stage { position:relative; min-height:680px; display:grid; place-items:center; padding:34px; background:radial-gradient(circle at 50% 24%,rgba(237,255,69,.2),transparent 20rem),linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.04)); } .cover-stage:before { content:""; position:absolute; inset:36px; border:1px solid rgba(255,255,255,.28); } .cover-stage:after { content:""; position:absolute; width:420px; height:420px; border-radius:50%; background:rgba(237,255,69,.16); filter:blur(80px); transform:translate(24%, -16%); } .cover-paper-link { position:relative; z-index:1; display:block; width:min(520px,100%); padding:16px; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.32); box-shadow:0 30px 90px rgba(0,0,0,.28); transition:transform .18s ease, box-shadow .18s ease; } .cover-paper-link:hover { transform:translateY(-4px) rotate(.35deg); box-shadow:0 42px 120px rgba(0,0,0,.34); } .cover-paper-link img { display:block; width:100%; height:auto; background:white; box-shadow:0 12px 34px rgba(0,0,0,.18); }
.doc-layout { width:min(1220px, calc(100% - 44px)); margin:0 auto; display:grid; grid-template-columns:260px minmax(0,1fr); gap:52px; padding:44px 0 86px; } .side { position:sticky; top:24px; align-self:start; display:grid; gap:10px; } .side a { padding:10px 0; color:var(--muted); text-decoration:none; border-bottom:1px solid var(--line); font-weight:800; } .doc-main h1 { margin-top:0; font-family:Inter,ui-sans-serif,system-ui,sans-serif; font-size:clamp(42px,5vw,68px); text-transform:none; letter-spacing:-.06em; } .doc-main h2 { margin:42px 0 12px; font-size:32px; letter-spacing:-.04em; } .doc-main p, .doc-main li { color:var(--muted); line-height:1.65; } .doc-main code { color:var(--blue); font-weight:850; }
@media (max-width:1100px) { .feature-grid.four-grid, .example-grid.four-grid, .feature-grid.usecase-grid, .example-grid.usecase-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:900px) { .home-hero, .doc-layout, .checker-layout, .ascii-ritual, .cover-showcase { grid-template-columns:1fr; } .blue-panel { margin:0; } .signal-card { min-height:420px; } .door-grid, .feature-grid, .example-grid, .privacy-grid, .example-grid.showcase, .doc-grid { grid-template-columns:1fr 1fr; } .feature-grid.four-grid, .example-grid.four-grid, .feature-grid.usecase-grid, .example-grid.usecase-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .site-nav { align-items:flex-start; padding-top:18px; } .ascii-terminal pre { font-size:9px; min-height:440px; } .cover-stage { min-height:auto; } }
@media (max-width:560px) { .site-nav, .section, .page-hero, .site-footer, .home-hero, .doc-layout { width:min(100% - 32px,1220px); } .site-nav { display:grid; gap:18px; } .navlinks { gap:13px; font-size:11px; } h1 { font-size:clamp(38px,10.2vw,46px); line-height:.92; letter-spacing:-.042em; overflow-wrap:normal; } .home-hero { padding-top:42px; gap:38px; } .signal-card { min-height:360px; padding:22px; } .signal-card h2 { font-size:clamp(30px,8.6vw,38px); } .section-title { font-size:clamp(29px,8.2vw,38px); line-height:1; letter-spacing:-.048em; } .button { width:100%; } .door-grid, .feature-grid, .feature-grid.four-grid, .feature-grid.usecase-grid, .example-grid, .example-grid.four-grid, .example-grid.usecase-grid, .privacy-grid, .example-grid.showcase, .doc-grid { grid-template-columns:1fr; } .step { grid-template-columns:1fr; gap:10px; } .section { padding:58px 0; } .side { position:static; } .xy-chart { min-height:340px; } .point.checked { left:70%; } .point.checked b,.point.checked p { left:-116px; text-align:right; } .protocol-grid { grid-template-columns:1fr; } .ascii-terminal pre { min-height:350px; font-size:5.6px; } .ascii-caption { display:grid; } .cover-notes, .cover-stage { padding:22px; } .cover-paper-link { padding:10px; } }
</style>
</head>
<body class="${bodyClass}">
${renderSiteNav(active)}
${body}
${renderSiteFooter()}
${renderCopyButtonsScript()}
</body>
</html>`;
}

function renderCopyButtonsScript(): string {
  return `<script>
(function () {
  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } finally { document.body.removeChild(area); }
  }
  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    fallbackCopy(text);
  }
  document.addEventListener("click", function (event) {
    var button = event.target instanceof Element ? event.target.closest("[data-copy-target]") : null;
    if (!button) return;
    var selector = button.getAttribute("data-copy-target");
    if (!selector) return;
    var scope = button.closest("[data-copy-scope]") || document;
    var target = scope.querySelector(selector);
    if (!target) return;
    var text = target.textContent || "";
    copyText(text.trim()).then(function () {
      var original = button.getAttribute("data-copy-label") || button.textContent || "Copy";
      button.setAttribute("data-copy-label", original);
      button.textContent = "Copied";
      button.classList.add("copied");
      window.setTimeout(function () {
        button.textContent = original;
        button.classList.remove("copied");
      }, 1400);
    }).catch(function () {
      button.textContent = "Copy failed";
      window.setTimeout(function () { button.textContent = button.getAttribute("data-copy-label") || "Copy"; }, 1600);
    });
  });
})();
</script>`;
}

function renderDragonGateAsciiScript(): string {
  return `<script>
(function () {
  var canvas = document.getElementById("ascii-dragon-gate");
  if (!canvas) return;
  var width = 92;
  var height = 39;
  var chars = {
    lowerWater: ["~", "≈", "˷", "﹏", "∿"],
    upperWater: ["╌", "─", "≈", "﹏"],
    spray: ["·", "˙", "˚", "°", "✧"],
    sparks: ["·", "✦", "✧", "˚"]
  };
  function esc(value) {
    return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function cell(grid, x, y, ch, cls) {
    if (y < 0 || y >= height || x < 0 || x >= width) return;
    grid[y][x] = { ch: ch, cls: cls || "" };
  }
  function put(grid, x, y, text, cls) {
    if (y < 0 || y >= height) return;
    for (var i = 0; i < text.length; i += 1) {
      var px = x + i;
      if (px >= 0 && px < width) cell(grid, px, y, text[i], cls || "");
    }
  }
  function renderGrid(grid) {
    return grid.map(function (row) {
      var html = "";
      var activeClass = null;
      for (var i = 0; i < row.length; i += 1) {
        var item = row[i];
        var cls = item.cls || "";
        if (cls !== activeClass) {
          if (activeClass !== null) html += "</span>";
          html += cls ? "<span class=\\"" + cls + "\\">" : "<span>";
          activeClass = cls;
        }
        html += esc(item.ch);
      }
      if (activeClass !== null) html += "</span>";
      return html;
    }).join("\\n");
  }
  function drawRidge(grid, t) {
    put(grid, 1, 5, "       ╱╲          ╱╲             ╱╲        distant ridge", "ascii-bg");
    put(grid, 5, 6, "______/  ╲________/  ╲___________/  ╲____________________", "ascii-bg");
    put(grid, 4, 8, "                 ╭──────────────────── UPPER RIVER ────────────────────╮", "ascii-stone");
    for (var y = 6; y <= 10; y += 1) {
      for (var x = 20; x < 88; x += 1) {
        if ((x + y + Math.floor(t * 4)) % 4 === 0) cell(grid, x, y + 3, chars.upperWater[(x + y + Math.floor(t * 2)) % chars.upperWater.length], "ascii-water");
      }
    }
    put(grid, 18, 14, "╰──────────────────────────────────────────────────────────────────────╯", "ascii-stone");
  }
  function drawDragonGate(grid, t) {
    var arch = [
      "              ▄████████▄              ",
      "          ▄▄██▓▓▒▒░░▒▒▓▓██▄▄          ",
      "       ▄██▓▒░  ╭────────╮  ░▒▓██▄     ",
      "     ▄█▓▒░    ╱  VŨ MÔN  ╲    ░▒▓█▄   ",
      "   ▄█▓▒░     ╱  REVIEW    ╲     ░▒▓█▄ ",
      "  ██▓▒░     ╱    GATE      ╲     ░▒▓██",
      "  ██▓▒░    ╱                ╲    ░▒▓██",
      "  ██▓▒░    ╲                ╱    ░▒▓██",
      "   ▀█▓▒░    ╲              ╱    ░▒▓█▀ ",
      "     ▀██▓▒░  ╲____________╱  ░▒▓██▀   ",
      "        ▀██▓▓▒▒░░░░░░░░▒▒▓▓██▀       ",
      "           ▀▀████████████▀▀          "
    ];
    arch.forEach(function (line, i) {
      var cls = i < 2 || i > 9 ? "ascii-stone-light" : i < 6 ? "ascii-stone" : "ascii-stone-dark";
      put(grid, 34, 14 + i, line, cls);
    });
    var side = ["                         ╲", "                          ╲▒", "                           ╲▓▒", "                            ╲▓▒░", "                             ╲▓▒░", "                              ╲▓▒", "                               ╲▓", "                                ╲"];
    side.forEach(function (line, i) { put(grid, 61, 16 + i, line, "ascii-stone-dark"); });
    for (var y = 14; y < 32; y += 1) {
      var sway = Math.round(Math.sin(t * 5 + y * 0.45) * 1);
      put(grid, 50 + sway, y, "┃┃┃", "ascii-foam");
      put(grid, 54 + sway, y, "╏╏", "ascii-water");
      put(grid, 58 + sway, y, "│", "ascii-foam");
      if ((y + Math.floor(t * 10)) % 3 === 0) put(grid, 47 + sway, y, "˚", "ascii-foam");
      if ((y + Math.floor(t * 7)) % 4 === 0) put(grid, 62 + sway, y, "✧", "ascii-foam");
    }
    put(grid, 35, 28, "near face", "ascii-stone");
    put(grid, 64, 28, "shadow face", "ascii-stone-dark");
  }
  function drawLowerRiver(grid, t) {
    put(grid, 2, 28, "╭──────────────────── LOWER RIVER: raw draft, real effort, first attempt ─────────╮", "ascii-stone");
    for (var y = 29; y < height; y += 1) {
      for (var x = 0; x < width; x += 1) {
        var density = y > 35 ? 2 : y > 32 ? 3 : 4;
        if ((x + y + Math.floor(t * 6)) % density === 0) cell(grid, x, y, chars.lowerWater[(x + y + Math.floor(t * 3)) % chars.lowerWater.length], "ascii-water");
      }
    }
    put(grid, 2, 34, "╲        ╲          ╲             ╲                 ╲", "ascii-bg");
    put(grid, 8, 36, "╲          ╲             ╲                 ╲", "ascii-bg");
  }
  function drawMist(grid, t) {
    for (var i = 0; i < 70; i += 1) {
      var angle = i * 1.77 + t * 1.7;
      var radiusX = 8 + ((i * 5) % 24);
      var radiusY = 3 + ((i * 7) % 10);
      var sx = Math.round(56 + Math.cos(angle) * radiusX);
      var sy = Math.round(18 + Math.sin(angle * 0.9) * radiusY);
      if (sx >= 0 && sx < width && sy >= 0 && sy < height) cell(grid, sx, sy, chars.spray[(i + Math.floor(t * 6)) % chars.spray.length], "ascii-foam");
    }
  }
  function carpFrame(phase) {
    if (phase > 0.72) return { cls: "ascii-dragon", lines: ["        ╭╲╱╮       ", "  ╭─────╯ 龍╰────╮  ", "≋≋╯  ╭╮      ╭╮  ╰≋", "     ╰╯╲____╱╰╯    ", "       ╱╲  ╱╲      "] };
    if (phase > 0.49) return { cls: "ascii-fish", lines: ["       ╱╲        ", "  ><(((º >))     ", "     ╱▓▒╲        ", "    ╱_╱╲_╲       "] };
    return { cls: "ascii-fish", lines: ["      __", "><(((º >", "  ░▒▓))", "    ╲╲"] };
  }
  function render(time) {
    var t = time / 1000;
    var loop = (t % 9.5) / 9.5;
    var grid = Array.from({ length: height }, function () { return Array.from({ length: width }, function () { return { ch: " ", cls: "" }; }); });
    drawRidge(grid, t);
    drawDragonGate(grid, t);
    drawMist(grid, t);
    drawLowerRiver(grid, t);
    var lowerProgress = Math.min(1, loop / 0.44);
    var leapProgress = Math.min(1, Math.max(0, (loop - 0.36) / 0.28));
    var upperProgress = Math.min(1, Math.max(0, (loop - 0.68) / 0.28));
    var pathX;
    var pathY;
    if (loop < 0.62) {
      pathX = Math.round(4 + lowerProgress * 43 + leapProgress * 10);
      pathY = Math.round(32 - Math.sin(leapProgress * Math.PI) * 18 - leapProgress * 9);
    } else {
      pathX = Math.round(60 + upperProgress * 22);
      pathY = Math.round(9 - Math.sin(upperProgress * Math.PI) * 1.4);
    }
    var fish = carpFrame(loop);
    fish.lines.forEach(function (line, i) { put(grid, pathX, pathY + i, line, fish.cls); });
    var sparkCount = loop > 0.45 ? 32 : 10;
    for (var i = 0; i < sparkCount; i += 1) {
      var angle = i * 1.9 + t * 2.2;
      var radius = 5 + ((i * 7) % 13);
      var sx = Math.round(57 + Math.cos(angle) * radius);
      var sy = Math.round(15 + Math.sin(angle) * radius * 0.48);
      if (sx >= 0 && sx < width && sy >= 0 && sy < height) cell(grid, sx, sy, chars.sparks[(i + Math.floor(t * 5)) % chars.sparks.length], "ascii-foam");
    }
    put(grid, 7, 1, "selected text only", "ascii-stone-light");
    put(grid, 7, 2, "local draft  →  structure/evidence gate  →  higher-level application", "ascii-stone-light");
    put(grid, 5, 17, "not magic", "ascii-foam");
    put(grid, 5, 19, "earned by loops", "ascii-foam");
    put(grid, 70, 17, "3x cover", "ascii-foam");
    put(grid, 70, 19, "1x CV", "ascii-foam");
    put(grid, 70, 21, "2x interview", "ascii-foam");
    put(grid, 70, 23, "1-3x long text", "ascii-foam");
    canvas.innerHTML = renderGrid(grid);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
})();
</script>`;
}

function renderCurrentLandingPage(): string {
  return renderSiteChrome(
    "Job MCP by pmlecuong",
    "/",
    `<div class="blue-panel"><main class="home-hero">
      <section>
        <div class="mono">Local-first career coach · MCP</div>
        <h1>Real evidence. Stronger applications.</h1>
        <p class="lead">Set up a local AI workspace that turns your CV, job description, writing samples, and documents into job-ready packages without uploading your whole career history.</p>
        <div class="actions"><a class="button primary" href="/start">Start setup</a><a class="button secondary" href="/examples">See examples</a></div>
        <div class="command" aria-label="Starter URL for local AI agent" data-copy-scope><div class="command-tabs"><span class="command-labels"><span>Agent URL</span><span>Copy into Codex / Claude</span></span><button class="copy-button" type="button" data-copy-target="pre">Copy</button></div><pre>${PUBLIC_SITE_URL}</pre></div>
      </section>
      <aside class="signal-card" aria-label="Local application workflow summary">
        <h2>Draft local. Review selected text.</h2>
        <ul class="signal-list">
          <li><b>01</b><span>Workspace kit and SOP create the folder foundation.</span></li>
          <li><b>02</b><span>Your CV, JD, voice samples, photo, and evidence stay on your machine.</span></li>
        <li><b>03</b><span>Only selected review text or CV/JD ATS text is sent to the MCP checker when you choose.</span></li>
        </ul>
      </aside>
    </main></div>
    <section class="section compact ascii-ritual-section" aria-labelledby="dragon-gate-title">
      <div class="ascii-ritual">
        <div class="ascii-ritual-copy">
          <div class="mono">Cá chép vượt Vũ Môn</div>
          <h2 class="section-title" id="dragon-gate-title">The draft must cross the gate.</h2>
          <p class="section-copy">The document does not become ready because an AI says so. It moves from raw draft, through structure and evidence checks, into a stronger version the user can actually trust.</p>
        </div>
        <div class="ascii-terminal" aria-label="Animated ASCII Dragon Gate review loop">
          <div class="ascii-terminal-inner">
            <div class="ascii-terminal-bar"><div class="ascii-lights" aria-hidden="true"><i></i><i></i><i></i></div><span>review-loop://vu-mon-transform</span></div>
            <pre id="ascii-dragon-gate" aria-live="off"></pre>
            <div class="ascii-caption"><span><strong>status:</strong> draft → review → revise → rise</span><span>selected text only · local files stay local</span></div>
          </div>
        </div>
      </div>
    </section>
    <section class="section compact"><div class="mono">Five use cases</div><h2 class="section-title">One checker boundary. Five useful outputs.</h2><p class="section-copy">The local agent drafts from your private files. The MCP reviews only the selected reader-facing text, CV/JD ATS text, or a safe structure manifest.</p>
      <div class="feature-grid usecase-grid">
        <a class="feature" href="/technical-flow"><small class="mono">Validator</small><h3>Code-style gate for writing</h3><p>The SOP treats review like a release check: current file, recorded loop, risk result, then revise if needed.</p></a>
        <a class="feature" href="/examples"><small class="mono">CV</small><h3>Editable HTML CV</h3><p>Build or adapt an English/German CV from verified profile material and visual-check it locally.</p></a>
        <a class="feature" href="/docs#ats-check"><small class="mono">ATS</small><h3>Resume-to-JD matching</h3><p>Check how well a CV matches a job description, then ask the user before adding missing keywords.</p></a>
        <a class="feature" href="/docs#interview-prep"><small class="mono">Interview</small><h3>Interview prep</h3><p>Create likely questions, STAR story prompts, weaknesses, culture-fit answers, and two review loops.</p></a>
        <a class="feature" href="/docs#long-writing"><small class="mono">Writing</small><h3>Long-form text</h3><p>Review research, academic, work, blog, or social writing in one to three selected-text loops.</p></a>
      </div>
    </section>
    <section class="section compact"><div class="mono">Why the checker helps</div><h2 class="section-title">Fast AI output is not the same as reader confidence.</h2>
      <div class="checker-layout">
        <div><p class="section-copy">The strongest result comes from a local workspace plus a selected-text checker: private evidence stays local, but the final text still gets a release-style review before the user sends it.</p>
          <div class="checker-legend"><span><i class="dot fast"></i><span><strong>Normal AI</strong> — fast, but often generic.</span></span><span><i class="dot local"></i><span><strong>Local workspace</strong> — grounded in user evidence.</span></span><span><i class="dot checked"></i><span><strong>Local workspace + checker</strong> — evidence plus final quality gate.</span></span></div></div>
        <div class="xy-chart" role="img" aria-label="X Y comparison chart showing normal AI, local workspace, and local workspace plus checker"><span class="axis y">Reader confidence</span><span class="axis x">Evidence and review depth</span><span class="point fast"><b>Normal AI</b><p>Fast draft</p></span><span class="point local"><b>Local workspace</b><p>Grounded draft</p></span><span class="point checked"><b>Local + checker</b><p>Release gate</p></span></div>
      </div>
    </section>
    <section class="section compact"><div class="mono">Where to go</div><h2 class="section-title">Use the menu. Keep the homepage light.</h2><p class="section-copy">Detailed setup, examples, docs, and technical flow live in focused pages.</p>
      <div class="door-grid">
        <a class="door" href="/start"><small class="mono">Start</small><h3>Set up a fresh workspace</h3><p>Create the local folder, install the kit, and let the agent ask for missing files.</p></a>
        <a class="door" href="/examples"><small class="mono">Examples</small><h3>See CV and cover-letter outputs</h3><p>Open English/German CV templates and the German-style cover letter sample.</p></a>
        <a class="door" href="/technical-flow"><small class="mono">Technical</small><h3>Check the safety boundary</h3><p>See the MCP calls, diagrams, and exact data that can cross the boundary.</p></a>
      </div>
    </section>
    <section class="privacy-strip"><div class="section"><div class="mono">Privacy boundary</div><h2 class="section-title">Useful feedback without sending the whole folder.</h2>
      <div class="privacy-grid">
        <div><strong>Local files stay local</strong><span>CVs, notes, job folders, photos, signatures, drafts, PDFs, and outputs.</span></div>
        <div><strong>Structure check is safe</strong><span>The MCP can receive relative paths, version state, and managed-file hashes.</span></div>
        <div><strong>Checks are deliberate</strong><span>You send selected final text only, or CV/JD text for ATS matching. Full folders stay local.</span></div>
        <div><strong>No fake promise</strong><span>It improves clarity and human rhythm. It is not an authorship verdict.</span></div>
      </div></div></section>
    <section class="final-cta"><div class="section"><div class="mono">Ready when you are</div><h2 class="section-title">Open an empty folder. Give the AI this URL. Let it ask properly.</h2><p class="section-copy">The start page now includes the setup prompt, source-material checklist, and agent instructions.</p><div class="actions"><a class="button primary" href="/start">Open start page</a><a class="button secondary" href="/docs">Read docs</a></div></div></section>${renderDragonGateAsciiScript()}`,
    "blue-page"
  );
}

function renderStartPage(): string {
  const starterPrompt = `Please read ${PUBLIC_SITE_URL} and set up a local project folder for me to handle job applications.

Ask me questions along the way if you need my verification.

If you need my picture, CV, cover letter, sample CV, sample cover letter, education track, writing samples, or job description, ask me and I will provide them.

Keep my private files local. Use the MCP only for workspace setup, safe structure/version audit, and selected final reader-facing text review.`;

  const applicationPrompt = `I want to apply for this job. Please read the job description, check fit against my verified CV evidence, and tell me what is missing before drafting.

Create or update the editable HTML CV if needed. Run the ATS resume-to-job-description check after every CV edit and report the score before calling the CV strong for this job.

Create a German-style cover letter only when appropriate. Run the required review loops before saying anything is ready.`;

  const atsPrompt = `Please run the MCP ATS check for this resume/CV and job description.

Send only the extracted CV text and the job description text. Return the ATS score, matched keywords, suggested missing keywords, and what I should confirm before any keyword is added to my resume.`;

  const writingPrompt = `Please review this selected text with the MCP writing checker. Use the correct mode: application, interview_prep, academic, work, blog, social, or general.

Send only the final reader-facing text, not my folder, notes, prompts, PDFs, images, or private source documents.`;

  return renderSiteChrome(
    "Start Setup - Job MCP by pmlecuong",
    "/start",
    `<header class="page-hero"><div class="mono">Start from an empty folder</div><h1>Give your local AI a clean place to work.</h1><p class="lead">Old scattered folders make the process slow. Start fresh, then let the MCP kit scaffold the right structure.</p></header>
    <section class="section compact"><div class="steps">
      <article class="step"><div class="step-number">01</div><div><h2>Create a clean project folder</h2><p>Use Codex, VS Code, Claude, or another local AI workspace. Name it clearly, for example <code>my-job-application</code>.</p></div></article>
      <article class="step"><div class="step-number">02</div><div><h2>Give the AI this URL</h2><p>Ask the agent to read <code>${PUBLIC_SITE_URL}</code>, fetch the workspace template, create the local structure, and ask before making uncertain decisions.</p></div></article>
      <article class="step"><div class="step-number">03</div><div><h2>Provide source material</h2><p>CV or profile source is mandatory. Add job descriptions, education track, certificates, writing samples, role preference, photo if you want one, and signature if you want cover letters signed.</p></div></article>
      <article class="step"><div class="step-number">04</div><div><h2>Send a job description</h2><p>The local agent checks fit, runs ATS matching for the CV/JD pair, drafts locally, then runs the required review loops before saying a document is ready.</p></div></article>
    </div>
    <div class="prompt-panel" data-copy-scope><div class="prompt-header"><div class="mono">Starter prompt</div><button class="copy-button" type="button" data-copy-target="pre">Copy prompt</button></div><pre>${starterPrompt}</pre></div></section>
    <section class="section"><div class="mono">What to prepare</div><h2 class="section-title">The agent can only be strong if the source material is real.</h2><p class="section-copy">The setup conversation should feel like a careful career coach, not a generic chatbot. It should ask for missing evidence, explain why the evidence matters, and stop before inventing facts.</p>
      <div class="feature-grid">
        <article class="feature"><small class="mono">Required</small><h3>CV or profile source</h3><p>PDF, DOCX, HTML, Markdown, LinkedIn export, or structured notes. If there is no old resume, the agent asks for education and work history.</p></article>
        <article class="feature"><small class="mono">Recommended</small><h3>Real writing samples</h3><p>Old emails, IELTS writing, reports, PRDs, BRDs, user stories, or pre-2022 documents help the agent learn authentic tone.</p></article>
        <article class="feature"><small class="mono">Optional</small><h3>Photo and signature</h3><p>Photo is asked for CV use. Signature is asked for cover letters. If the user does not provide them, the agent continues without inventing assets.</p></article>
      </div></section>
    <section class="section"><div class="mono">Copy prompts</div><h2 class="section-title">The prompt page is now part of start.</h2><p class="section-copy">Use these when the workspace already exists and you want to trigger a specific flow.</p>
      <div class="prompt-panel" data-copy-scope><div class="prompt-header"><div class="mono">Job application prompt</div><button class="copy-button" type="button" data-copy-target="pre">Copy prompt</button></div><pre>${applicationPrompt}</pre></div>
      <div class="prompt-panel" data-copy-scope><div class="prompt-header"><div class="mono">ATS check prompt</div><button class="copy-button" type="button" data-copy-target="pre">Copy prompt</button></div><pre>${atsPrompt}</pre></div>
      <div class="prompt-panel" data-copy-scope><div class="prompt-header"><div class="mono">Writing check prompt</div><button class="copy-button" type="button" data-copy-target="pre">Copy prompt</button></div><pre>${writingPrompt}</pre></div></section>`,
    "blue-page"
  );
}

function renderExamplesPage(): string {
  return renderSiteChrome(
    "Examples - Job MCP by pmlecuong",
    "/examples",
    `<header class="page-hero"><div class="mono">Output examples</div><h1>Templates and samples stay separate from the setup story.</h1><p class="lead">Use these only as references. The local agent still has to tailor every document to the actual person and job.</p></header>
    <section class="section compact"><div class="mono">Five use cases</div><h2 class="section-title">Examples are organized by the thing the user wants checked.</h2>
      <div class="example-grid usecase-grid">
        <article class="example-card"><small class="mono">Validator</small><h3>Release-style writing gate</h3><p>The local SOP checks that the reviewed text is the current artifact and reruns when the file changes.</p></article>
        <article class="example-card"><small class="mono">CV</small><h3>Editable resume package</h3><p>HTML CV first, visual review with browser screenshots, then PDF or export when the structure is right.</p></article>
        <article class="example-card"><small class="mono">ATS</small><h3>Resume/JD match report</h3><p>Score the current CV against the job description, list matched keywords, and ask before adding missing terms.</p></article>
        <article class="example-card"><small class="mono">Interview</small><h3>Interview prep answers</h3><p>Likely questions, STAR prompts, weakness answers, culture-fit answers, and two selected-text review loops.</p></article>
        <article class="example-card"><small class="mono">Writing</small><h3>Research or long-form text</h3><p>Academic, work, blog, social, or general text can run one to three selected-text review loops.</p></article>
      </div></section>
    <section class="section compact"><div class="example-grid">
      <a class="example-card" href="/cv-template/english"><small class="mono">CV</small><h3>English HTML resume</h3><p>Editable HTML template for users who do not already have a usable resume format.</p></a>
      <a class="example-card" href="/cv-template/german"><small class="mono">Lebenslauf</small><h3>German HTML CV</h3><p>German-style structure with photo area and real-content placeholders.</p></a>
      <a class="example-card" href="/assets/german-cover-letter-sample.pdf"><small class="mono">Cover letter</small><h3>German business letter PDF</h3><p>One-page sample with sender, recipient, date, subject, body, signature, and enclosures.</p></a>
    </div></section>
    <section class="section"><div class="mono">Rendered sample</div><h2 class="section-title">A German-style cover letter, built locally.</h2><p class="section-copy">Fictional demonstration only. Jane Doe, Stuttgart Hbf, the recruiting team, and the signature graphic are placeholders.</p>
      <div class="cover-showcase">
        <div class="cover-notes">
          <div>
            <div class="mono">Rules shown</div>
            <h3>German structure. Real document feel.</h3>
            <p>The preview shows the exact document discipline the local kit enforces: clean sender block, recipient block, date, bold subject, concise evidence-led body, signature area, and enclosure list.</p>
            <ul class="cover-checks">
              <li><b>01</b><span>One-page A4 letter with business structure.</span></li>
              <li><b>02</b><span>Signature area and enclosure list are visible.</span></li>
              <li><b>03</b><span>Rendered locally before a user sends anything.</span></li>
            </ul>
          </div>
          <div class="cover-actions"><a class="button primary" href="/assets/german-cover-letter-sample.pdf">Open PDF</a><a class="button secondary" href="/docs">Read rules</a></div>
        </div>
        <div class="cover-stage">
          <a class="cover-paper-link" href="/assets/german-cover-letter-sample.pdf" aria-label="Open fictional German-format cover letter PDF"><img src="/assets/german-cover-letter-sample.svg" alt="One-page fictional German-format cover letter sample"></a>
        </div>
      </div></section>`,
    "blue-page"
  );
}

function renderDocsPage(): string {
  return renderSiteChrome(
    "Docs - Job MCP by pmlecuong",
    "/docs",
    `<div class="doc-layout"><aside class="side"><a href="#overview">Overview</a><a href="#use-cases">Use cases</a><a href="#inputs">Inputs</a><a href="#agent-behavior">Agent behavior</a><a href="#gates">Review gates</a><a href="#ats-check">ATS check</a><a href="#interview-prep">Interview prep</a><a href="#long-writing">Long writing</a><a href="#workspace">Workspace drift</a><a href="#privacy">Privacy</a><a href="#routes">Routes</a></aside>
    <main class="doc-main">
      <h1 id="overview">Job MCP by pmlecuong docs</h1>
      <p>This service gives local AI agents a workspace kit, prompt rules, folder-audit guidance, selected-text writing review, and ATS-style resume/job-description matching. It is designed for students and early-career candidates who need practical help preparing job documents without turning their private career folder into a server-side profile.</p>
      <div class="doc-callout"><strong>Core model</strong><p>The local agent does the private work. The MCP supplies generic structure, public instructions, version checks, and selected-text feedback. The MCP cannot browse the user's machine.</p></div>
      <h2 id="use-cases">Five supported use cases</h2>
      <div class="doc-grid">
        <div class="doc-tile"><strong>1. Code-validator style writing gate</strong><p>The local SOP treats writing readiness like a release gate: it checks the current artifact, records the loop, and blocks stale approvals.</p></div>
        <div class="doc-tile"><strong>2. CV / resume</strong><p>The agent converts the user's CV source into editable HTML, preserves or recreates the preferred structure, and runs one review loop.</p></div>
        <div class="doc-tile"><strong>3. ATS resume/JD check</strong><p>The agent sends extracted CV text and job-description text to get an ATS-style score, matched keywords, missing keywords, and safe revision guidance.</p></div>
        <div class="doc-tile"><strong>4. Interview prep</strong><p>The agent can prepare likely questions, STAR story prompts, weakness answers, culture-fit answers, and candidate questions for the employer.</p></div>
        <div class="doc-tile"><strong>5. Long-form writing</strong><p>Academic, work, blog, social, or general writing can be checked in one to three loops, selected by the user.</p></div>
      </div>
      <h2 id="inputs">What the user should provide</h2>
      <p>The agent should ask for enough material to avoid a half-baked profile. If the user cannot provide something, it should adapt; it must not invent facts.</p>
      <ul><li><strong>CV or best available profile source:</strong> PDF, DOCX, HTML, Markdown, LinkedIn export, or structured notes.</li><li><strong>Job description or job URL:</strong> needed for tailoring and role-fit decisions.</li><li><strong>Education path:</strong> Bachelor, Master, Ausbildung/job training, working student, internship, or another path.</li><li><strong>Human-written samples:</strong> old emails, IELTS writing, user stories, PRDs, BRDs, reports, notes, or pre-2022 documents.</li><li><strong>Company bullet bank:</strong> ideally 10–15 user-written bullet points per past company, so the agent can select the best 4–5 for a job.</li><li><strong>Optional assets:</strong> CV photo and PNG/JPG signature for cover letters.</li><li><strong>Enclosures:</strong> CV is mandatory; degree diploma/transcript and employer reference letters should be requested if available.</li></ul>
      <h2 id="agent-behavior">How the local agent should behave</h2>
      <ul><li>Act like a helpful career coach, not a generic document generator.</li><li>Explain what the user needs to provide and why it helps.</li><li>Ask for missing evidence before writing claims.</li><li>Use the user's own tone when enough authentic writing exists.</li><li>Stop asking for more tone samples when the user says the profile is already enough.</li><li>Never treat a document as ready just because chat text says it is ready.</li></ul>
      <h2 id="gates">Review gates</h2>
      <ul><li><strong>CV/resume:</strong> one writing review loop. The payload must be the actual CV text the reader will see.</li><li><strong>ATS check:</strong> run after every CV edit for a job. The local agent must report the ATS score and ask the user before adding any missing keyword that is not already verified.</li><li><strong>Cover letter:</strong> three distinct review loops. Each loop must refer to the current file and record what changed.</li><li><strong>Interview prep:</strong> two low-risk review loops for final spoken answer text, not private notes or coaching scaffolding.</li><li><strong>General writing:</strong> user-selected one to three loops. Do not exceed three unless a future release explicitly changes the contract.</li></ul>
      <h2 id="ats-check">ATS resume/JD check</h2>
      <p>The ATS checker is available for everyone. A local agent can compare a resume or CV against a job description and return a practical match report before the user applies.</p>
      <div class="doc-grid">
        <div class="doc-tile"><strong>Score</strong><p>Returns an ATS-style score out of 100 and a readiness label, calibrated against observed NodeFlair behavior.</p></div>
        <div class="doc-tile"><strong>Matched keywords</strong><p>Shows the terms already visible in the current CV so the user can see what is working.</p></div>
        <div class="doc-tile"><strong>Suggested keywords</strong><p>Lists missing terms from the job description, but marks what needs user confirmation before it can be added.</p></div>
        <div class="doc-tile"><strong>Human-in-the-loop</strong><p>The agent must not invent skills, tools, degrees, language levels, or domain experience just to raise the score.</p></div>
      </div>
      <p>For privacy, the ATS call should send only extracted CV/resume text and job-description text. It should not send photos, signatures, full folders, private notes, or unrelated source files.</p>
      <h2 id="interview-prep">Interview prep workflow</h2>
      <p>Interview prep is optional. If the user accepts it, the local agent should ask for real stories and not hallucinate STAR examples. If it cannot find a story in the profile, it must ask the user for a real incident.</p>
      <div class="doc-grid">
        <div class="doc-tile"><strong>Role questions</strong><p>Likely questions based on job description, company, role family, and user profile.</p></div>
        <div class="doc-tile"><strong>STAR bank</strong><p>Real situation, task, action, result stories drawn from profile evidence or user-provided incidents.</p></div>
        <div class="doc-tile"><strong>Weakness answer</strong><p>A realistic weakness with a concrete improvement system, not a fake perfectionist answer.</p></div>
        <div class="doc-tile"><strong>Culture fit</strong><p>Answers for questions like “Who are you outside work?” and work-life balance expectations.</p></div>
      </div>
      <h2 id="long-writing">Academic and long-form writing</h2>
      <p>The writing checker can support research paragraphs, essays, reports, work updates, blog drafts, or social posts. The local agent should send only the selected text and selected mode, then apply the feedback to the real document locally.</p>
      <ul><li>Academic writing should preserve claims, citations, and argument structure.</li><li>Work writing should stay clear, useful, and decision-oriented.</li><li>Blog/social writing should preserve voice and story rhythm.</li><li>The checker should not receive raw sources, private folders, notes, or full PDFs.</li></ul>
      <h2 id="workspace">Workspace drift and slow folders</h2>
      <p>Old candidate folders can become slow because outputs, drafts, PDFs, screenshots, and generated artifacts pile up. The local SOP should audit folder structure and compare it to the current MCP kit. If drift is detected, it should propose safe cleanup or migration without deleting private data automatically.</p>
      <h2 id="privacy">Privacy contract</h2>
      <p>The MCP can receive a privacy-safe folder manifest or selected final text. It must not receive raw folders, private PDFs, photos, signatures, prompts, coaching notes, or full profile archives.</p>
      <h2 id="routes">Useful routes</h2>
      <ul><li><code>/start</code> setup instructions and copyable prompts.</li><li><code>/examples</code> CV, cover-letter, interview, and writing use-case examples.</li><li><code>/technical-flow</code> diagrams and HTTP/MCP details.</li><li><code>/privacy</code> privacy boundary.</li><li><code>/health</code> service status.</li><li><code>/mcp</code> Streamable HTTP MCP endpoint.</li></ul>
    </main></div>`
  );
}

function renderPrivacyPage(): string {
  return renderSiteChrome(
    "Privacy - Job MCP by pmlecuong",
    "/privacy",
    `<header class="page-hero"><div class="mono">Privacy boundary</div><h1>Your career folder is not the product.</h1><p class="lead">The service supports local work. It does not need to browse, upload, or store your full application workspace.</p></header>
    <section class="section compact"><div class="feature-grid">
      <article class="feature"><small class="mono">Stays local</small><h3>Private files</h3><p>CVs, job posts, profile notes, drafts, PDFs, images, signatures, and outputs remain on the candidate laptop.</p></article>
      <article class="feature"><small class="mono">Can be sent</small><h3>Selected text and ATS text</h3><p>Only the final reader-facing text the user deliberately submits, or extracted CV/JD text for ATS matching.</p></article>
      <article class="feature"><small class="mono">Can be audited</small><h3>Safe manifest</h3><p>Relative paths, kit version, and managed-file hashes; no personal document contents.</p></article>
    </div></section>`,
    "blue-page"
  );
}

function renderTechnicalFlowPage(): string {
  return renderSiteChrome(
    "Technical Flow - Job MCP by pmlecuong",
    "/technical-flow",
    `<header class="page-hero"><div class="mono">Technical flow</div><h1>How the local workflow and review boundary work.</h1><p class="lead">The local Application SOP checks workspace health, records release evidence, and keeps private files on the laptop. The MCP sees only a safe manifest or selected final text.</p></header>
    <section class="section compact"><div class="feature-grid">
      <article class="feature"><small class="mono">Local SOP</small><h3>Hard gate</h3><p>Records current artifact hashes, review loops, and release state before a document is marked ready.</p></article>
      <article class="feature"><small class="mono">Selected text</small><h3>Boundary</h3><p>The MCP receives exact reader-facing text or CV/JD ATS text only, not private folders, PDFs, signatures, images, notes, or prompts.</p></article>
      <article class="feature"><small class="mono">Rerun</small><h3>Rewrite until low</h3><p>Medium/high feedback means the local agent revises the real file and reruns the gate.</p></article>
    </div></section>
    <section class="section tech-shell"><div><div class="mono">Review boundary</div><h2 class="section-title">Private selected-text review.</h2><p class="section-copy">This diagram shows how final text leaves the local workspace only when the user or local agent deliberately sends it for review.</p></div><div class="tech-card scroll-x"><img src="/assets/private-checker-flow.svg" alt="Sequence diagram showing selected-text review between the candidate, local AI agent, local workspace, and MCP checker"></div></section>
    <section class="section tech-shell"><div><div class="mono">Bootstrap</div><h2 class="section-title">How a human prompt creates the local foundation.</h2><p class="section-copy">The MCP returns generic kit files and structure. The local agent and SOP create, inspect, and retain the real candidate workspace.</p></div><div class="tech-card scroll-x"><img src="/assets/bootstrap-scaffolding-flow.svg" alt="Sequence diagram showing human request, public MCP kit retrieval, local workspace scaffolding, strict SOP boot, and privacy-safe manifest audit"></div></section>
    <section class="section"><div class="mono">HTTP and MCP protocol</div><h2 class="section-title">What actually calls what.</h2><p class="section-copy">The human setup URL is <code>${PUBLIC_SITE_URL}</code>. The Streamable HTTP MCP transport endpoint is <code>${PUBLIC_MCP_ENDPOINT}</code>.</p>
      <div class="protocol-grid" aria-label="HTTP endpoint and request contract">
        <div class="method"><code>OPTIONS /mcp</code></div><div>Browser CORS preflight. The server responds <code>204</code> and allows <code>content-type</code>, <code>authorization</code>, and <code>mcp-session-id</code> headers.</div>
        <div class="method"><code>POST /mcp</code></div><div>Streamable HTTP MCP transport. A compatible client sends JSON-RPC lifecycle requests such as <code>initialize</code> and <code>tools/list</code>, followed by <code>tools/call</code>.</div>
        <div class="method"><code>tools/call</code></div><div>For setup, the local agent calls <code>get_workspace_template</code> or <code>get_application_kit_bundle</code>. For structure health, it calls <code>audit_workspace_manifest</code>.</div>
        <div class="method"><code>tools/call</code></div><div>For ATS matching, it calls <code>check_ats_resume_fit</code> with extracted CV/resume text and job-description text. The response includes score, matched keywords, missing keywords, risks, and user-confirmation actions.</div>
        <div class="method"><code>tools/call</code></div><div>For writing review, it calls <code>check_writing_human_fit</code> with selected final reader-facing text and a writing mode.</div>
        <div class="method"><code>GET /health</code></div><div>Service health and public-tool inventory. It is not a candidate-data API.</div>
        <div class="method"><code>GET /assets/*.puml</code></div><div>Read-only canonical PlantUML source. Rendered SVG diagrams are served from matching <code>/assets/*.svg</code> routes.</div>
      </div><p class="protocol-note">The public request body limit is 64 KiB. The endpoint is unauthenticated in this release, stateless, and does not persist candidate profiles or workspace files.</p>
      <div class="actions"><a class="button secondary" href="/assets/private-checker-flow.puml">Review diagram source</a><a class="button secondary" href="/assets/bootstrap-scaffolding-flow.puml">Bootstrap diagram source</a></div></section>`,
    "blue-page"
  );
}

function isAuthorized(req: IncomingMessage): boolean {
  if (!TOKEN) return true;
  const authorization = req.headers.authorization ?? "";
  return authorization === `Bearer ${TOKEN}`;
}

async function parseJsonBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let totalBytes = 0;
  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    totalBytes += buffer.length;
    if (totalBytes > MAX_HTTP_BODY_BYTES) {
      throw new Error("Request body exceeds the public MCP size limit.");
    }
    chunks.push(buffer);
  }
  if (!chunks.length) return undefined;
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function writeJson(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "content-type, authorization, mcp-session-id",
    "access-control-allow-methods": "GET,POST,OPTIONS"
  });
  res.end(`${JSON.stringify(body)}\n`);
}

async function handleHttp(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
  const handout = await handoutDocument();
  const samplePrompts = await samplePromptsDocument();

  if (req.method === "OPTIONS") {
    writeJson(res, 204, {});
    return;
  }

  if (url.pathname === "/favicon.ico") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (url.pathname === "/") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderCurrentLandingPage());
    return;
  }

  if (url.pathname === "/start") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderStartPage());
    return;
  }

  if (url.pathname === "/examples") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderExamplesPage());
    return;
  }

  if (url.pathname === "/docs") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderDocsPage());
    return;
  }

  if (url.pathname === "/handout") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(await renderMarkdownAsHtml(handout, "Job MCP by pmlecuong"));
    return;
  }

  if (url.pathname === "/sample-prompts") {
    res.writeHead(301, { location: "/start" });
    res.end();
    return;
  }

  if (url.pathname === "/privacy") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderPrivacyPage());
    return;
  }

  if (url.pathname === "/technical-flow") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(renderTechnicalFlowPage());
    return;
  }

  if (url.pathname === "/cv-template/english") {
    res.writeHead(200, {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("application-kit/templates/cv_english_modern.html"));
    return;
  }

  if (url.pathname === "/cv-template/german") {
    res.writeHead(200, {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("application-kit/templates/cv_german_rounded.html"));
    return;
  }

  if (url.pathname === "/assets/local-first-human-flow.svg") {
    res.writeHead(200, {
      "content-type": "image/svg+xml; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/local-first-human-flow.svg"));
    return;
  }

  if (url.pathname === "/assets/local-first-human-flow.puml") {
    res.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/local-first-human-flow.puml"));
    return;
  }

  if (url.pathname === "/assets/bootstrap-scaffolding-flow.svg") {
    res.writeHead(200, {
      "content-type": "image/svg+xml; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/bootstrap-scaffolding-flow.svg"));
    return;
  }

  if (url.pathname === "/assets/german-cover-letter-sample.svg") {
    res.writeHead(200, {
      "content-type": "image/svg+xml; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("application-kit/examples/german-cover-letter-demo/cover-letter-preview.svg"));
    return;
  }

  if (url.pathname === "/assets/german-cover-letter-sample.pdf") {
    res.writeHead(200, {
      "content-type": "application/pdf",
      "content-disposition": "inline; filename=fictional-german-cover-letter-sample.pdf",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResourceBinary("application-kit/examples/german-cover-letter-demo/cover-letter.pdf"));
    return;
  }

  if (url.pathname === "/assets/bootstrap-scaffolding-flow.puml") {
    res.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/bootstrap-scaffolding-flow.puml"));
    return;
  }

  if (url.pathname === "/assets/private-checker-flow.svg") {
    res.writeHead(200, {
      "content-type": "image/svg+xml; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/private-checker-flow.svg"));
    return;
  }

  if (url.pathname === "/assets/private-checker-flow.puml") {
    res.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=300"
    });
    res.end(await readResource("diagrams/private-checker-flow.puml"));
    return;
  }

  if (url.pathname === "/health") {
    writeJson(res, 200, {
      ok: true,
      service: "student-application-ai-helper",
      version: VERSION,
      mode: "local-kit-plus-private-writing-checker",
      workspaceKitVersion: WORKSPACE_KIT_VERSION,
      persistentProfiles: false,
      remoteProcessing: "transient writing checks and ATS CV/JD checks only",
      tokenRequired: Boolean(TOKEN),
      workspace_update_required: workspaceUpdateDirective(),
      tools: PUBLIC_TOOLS
    });
    return;
  }

  if (url.pathname === "/client-skill") {
    writeJson(res, 200, {
      path: "application-client-skill/SKILL.md",
      content: await readResource("client-skill/SKILL.md")
    });
    return;
  }

  if (url.pathname === "/workspace-template") {
    writeJson(res, 200, {
      root: "student-application-workspace",
      files: await readTemplateDirectory("workspace-template")
    });
    return;
  }

  if (url.pathname === "/application-kit-manifest") {
    writeJson(res, 200, {
      manifest: JSON.parse(await readResource("application-kit/manifest.json"))
    });
    return;
  }

  if (url.pathname === "/application-kit-bundle") {
    writeJson(res, 200, {
      root: "application-kit",
      manifest: JSON.parse(await readResource("application-kit/manifest.json")),
      files: await readTemplateDirectory("application-kit")
    });
    return;
  }

  if (url.pathname === "/sample-prompts.json") {
    writeJson(res, 200, {
      path: "sample-prompts.md",
      content: samplePrompts
    });
    return;
  }

  if (url.pathname !== "/mcp") {
    writeJson(res, 404, { error: "Not found" });
    return;
  }

  if (!isAuthorized(req)) {
    writeJson(res, 401, { error: "Unauthorized" });
    return;
  }

  if (req.method !== "POST") {
    writeJson(res, 405, { error: "MCP endpoint expects POST." });
    return;
  }

  const body = await parseJsonBody(req);
  const server = await createServer();
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, body);
  } finally {
    res.on("close", () => {
      void transport.close();
      void server.close();
    });
  }
}

async function startHttp(): Promise<void> {
  const httpServer = http.createServer((req, res) => {
    handleHttp(req, res).catch((error: unknown) => {
      console.error(error);
      if (!res.headersSent) {
        writeJson(res, 500, { error: error instanceof Error ? error.message : "Internal server error" });
      } else {
        res.end();
      }
    });
  });

  httpServer.listen(PORT, HOST, () => {
    console.log(`student-application-ai-helper ${VERSION} listening on http://${HOST}:${PORT}/mcp`);
  });
}

async function startStdio(): Promise<void> {
  const server = await createServer();
  await server.connect(new StdioServerTransport());
}

const args = new Set(process.argv.slice(2));
if (args.has("--stdio")) {
  await startStdio();
} else {
  await startHttp();
}
