import http, { IncomingMessage, ServerResponse } from "node:http";
import { createHash } from "node:crypto";
import { URL } from "node:url";
import process from "node:process";
import * as z from "zod/v4";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { checkWritingHumanFit } from "./checker.js";
import {
  handoutDocument,
  onboardingInstructions,
  readResource,
  readResourceBinary,
  readTemplateDirectory,
  samplePromptsDocument
} from "./resources.js";

const VERSION = "0.2.12";
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
  "check_writing_human_fit",
  "suggest_writing_revision"
];

const WORKSPACE_KIT_VERSION = "2026.08.15-review-payload.1";
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
  "application-kit/manifest.json",
  "application-kit/templates/cover_letter.html",
  "application-kit/templates/cover_letter.tex",
  "application-kit/templates/interview_prep.md",
  "application-kit/templates/cv_english_modern.html",
  "application-kit/templates/cv_german_rounded.html",
  "application-kit/contracts/typography-contract.md",
  "application-kit/contracts/cv-markdown-contract.md",
  "application-kit/contracts/interview-prep-contract.md",
  "application-kit/contracts/writing-review-contract.md",
  "application-kit/contracts/mcp-review-payload-contract.md",
  "application-kit/scripts/application_sop.py",
  "application-kit/scripts/application_quality_loop.py",
  "application-kit/scripts/mcp_check_client.mjs",
  "application-kit/scripts/writing_review_loop.py",
  "application-kit/scripts/local_application_generator.py",
  "application-kit/scripts/build_interview_prep.py",
  "application-kit/scripts/build_cv_html.py"
];

const MANAGED_HASHED_PATHS = [
  "AGENTS.md",
  "scripts/application_sop.py",
  "scripts/mcp_check_client.mjs",
  "application-kit/manifest.json",
  "application-kit/templates/cover_letter.html",
  "application-kit/templates/cover_letter.tex",
  "application-kit/templates/interview_prep.md",
  "application-kit/templates/cv_english_modern.html",
  "application-kit/templates/cv_german_rounded.html",
  "application-kit/contracts/typography-contract.md",
  "application-kit/contracts/cv-markdown-contract.md",
  "application-kit/contracts/interview-prep-contract.md",
  "application-kit/contracts/writing-review-contract.md",
  "application-kit/contracts/mcp-review-payload-contract.md",
  "application-kit/scripts/application_sop.py",
  "application-kit/scripts/application_quality_loop.py",
  "application-kit/scripts/mcp_check_client.mjs",
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
  return {
    status: missing.length || needsManagedUpdate ? "action_required" : "workspace_current",
    schema_version: "1.0",
    kit_version: WORKSPACE_KIT_VERSION,
    minimum_supported_version: WORKSPACE_KIT_VERSION,
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
  return {
    content: [
      {
        type: "text",
        text: `${JSON.stringify(value, null, 2)}\n`
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
        remoteProcessing: "transient writing checks only",
        tokenRequired: Boolean(TOKEN),
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
    "<h1>Student Application AI Helper</h1>",
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

function renderCurrentLandingPage(): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Student Application AI Helper</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --paper:#f7f5ef; --ink:#152420; --muted:#59635f; --line:#d6d9d1; --green:#156b59; --deep:#0f3028; --mint:#dcf3e6; --sun:#f4c764; --coral:#dc765c; }
* { box-sizing:border-box; } html { scroll-behavior:smooth; } body { margin:0; color:var(--ink); background:var(--paper); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
a { color:inherit; } .shell { overflow:hidden; } .nav, .section, .footer { width:min(1140px, calc(100% - 40px)); margin:0 auto; }
.nav { min-height:74px; display:flex; justify-content:space-between; align-items:center; gap:18px; } .brand { color:var(--deep); font-weight:900; text-decoration:none; letter-spacing:-.03em; } .brand span { color:var(--green); }
.navlinks { display:flex; gap:18px; flex-wrap:wrap; color:var(--muted); font-size:14px; } .navlinks a { text-decoration:none; } .navlinks a:hover { color:var(--green); }
.hero { min-height:calc(100svh - 74px); padding:60px max(20px, calc((100% - 1140px) / 2)) 68px; display:grid; grid-template-columns:minmax(0, 1fr) minmax(420px, .88fr); gap:54px; align-items:center; background:linear-gradient(125deg, #f7f5ef 0 52%, #e4eee7 52% 100%); }
.kicker { color:var(--green); font-size:13px; font-weight:850; letter-spacing:.12em; text-transform:uppercase; } h1 { max-width:750px; margin:17px 0 20px; font-size:clamp(50px, 7vw, 94px); line-height:.94; letter-spacing:-.065em; } .lead { max-width:650px; margin:0; color:#3f4d47; font-size:clamp(18px, 2vw, 23px); line-height:1.48; }
.actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:30px; } .button { display:inline-flex; align-items:center; justify-content:center; min-height:48px; padding:0 17px; border-radius:7px; text-decoration:none; font-weight:800; border:1px solid transparent; transition:transform .18s ease, background .18s ease; } .button:hover { transform:translateY(-2px); } .primary { color:#fff; background:var(--deep); } .secondary { background:transparent; border-color:#aeb8b0; }
.connection { margin-top:24px; max-width:620px; border-top:1px solid var(--line); padding-top:14px; color:var(--muted); font-size:13px; line-height:1.5; } code { color:var(--deep); font-weight:800; overflow-wrap:anywhere; }
.hero-visual { position:relative; min-height:520px; padding:25px; display:flex; align-items:center; background:var(--deep); box-shadow:0 32px 80px rgba(15,48,40,.18); overflow:hidden; } .hero-visual:before { content:""; position:absolute; inset:0; opacity:.18; background-image:linear-gradient(rgba(255,255,255,.7) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.7) 1px,transparent 1px); background-size:38px 38px; mask-image:linear-gradient(#000,transparent); }
.hero-visual:after { content:""; position:absolute; width:220px; height:220px; right:-80px; top:-70px; border-radius:50%; background:var(--sun); } .stack { position:relative; z-index:1; width:100%; } .stage { display:grid; grid-template-columns:42px 1fr; gap:14px; padding:17px 0; border-bottom:1px solid rgba(255,255,255,.21); color:#fff; } .stage:last-child { border-bottom:0; } .stage-num { display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:var(--sun); color:var(--deep); font-weight:900; } .stage h2 { margin:0 0 5px; font-size:19px; } .stage p { margin:0; color:#d1e5da; line-height:1.45; font-size:14px; }
.section { padding:100px 0; border-top:1px solid var(--line); } .eyebrow { color:var(--green); font-size:13px; font-weight:850; text-transform:uppercase; letter-spacing:.11em; } .section h2, .privacy-inner h2 { max-width:820px; margin:12px 0 14px; font-size:clamp(34px,5vw,64px); line-height:.98; letter-spacing:-.055em; } .intro { max-width:760px; margin:0; color:var(--muted); font-size:18px; line-height:1.55; }
.features { margin-top:44px; display:grid; grid-template-columns:repeat(3,1fr); border-top:1px solid var(--line); border-left:1px solid var(--line); } .feature { min-height:188px; padding:24px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); background:rgba(255,255,255,.32); } .feature b { display:block; margin-bottom:10px; font-size:19px; letter-spacing:-.025em; } .feature p { margin:0; color:var(--muted); line-height:1.5; }
.setup-guide { margin-top:42px; display:grid; grid-template-columns:minmax(0,.78fr) minmax(360px,.58fr); gap:28px; align-items:start; } .setup-steps { display:grid; border:1px solid var(--line); background:#fff; } .setup-step { display:grid; grid-template-columns:58px 1fr; gap:18px; padding:22px 24px; border-bottom:1px solid var(--line); } .setup-step:last-child { border-bottom:0; } .setup-step strong { display:grid; place-items:center; width:42px; height:42px; border-radius:50%; background:var(--deep); color:#fff; font-weight:900; } .setup-step h3 { margin:0 0 7px; font-size:20px; letter-spacing:-.035em; } .setup-step p { margin:0; color:var(--muted); line-height:1.5; } .prompt-card { padding:24px; background:var(--deep); color:#fff; box-shadow:18px 20px 0 rgba(15,48,40,.1); } .prompt-card h3 { margin:0 0 10px; font-size:22px; } .prompt-card p { margin:0 0 16px; color:#cfe3d9; line-height:1.5; } .prompt-card code { display:block; padding:13px 14px; margin-bottom:14px; background:rgba(255,255,255,.08); color:#fff; border:1px solid rgba(255,255,255,.16); overflow-wrap:anywhere; } .prompt-card pre { margin:0; white-space:pre-wrap; color:#fff; font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
.comparison-layout { display:grid; grid-template-columns:minmax(280px,.82fr) minmax(0,1.18fr); gap:56px; align-items:center; margin-top:44px; } .comparison-copy h3 { margin:0 0 12px; font-size:clamp(31px,4vw,48px); line-height:1; letter-spacing:-.05em; } .comparison-copy p { margin:0; max-width:460px; color:var(--muted); font-size:18px; line-height:1.55; } .comparison-legend { display:grid; gap:13px; margin-top:26px; color:var(--muted); line-height:1.45; } .comparison-legend > span { display:grid; grid-template-columns:14px 1fr; gap:10px; align-items:start; } .legend-dot { width:14px; height:14px; margin-top:4px; border-radius:50%; } .legend-dot.rose { background:#dc765c; } .legend-dot.gold { background:var(--sun); } .legend-dot.green { background:var(--green); } .comparison-chart { position:relative; min-height:350px; padding:28px 30px 52px 58px; border:1px solid var(--line); background:linear-gradient(rgba(21,36,32,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(21,36,32,.06) 1px,transparent 1px),#fffdf7; background-size:64px 64px; } .comparison-chart:before, .comparison-chart:after { content:""; position:absolute; background:#587068; } .comparison-chart:before { left:58px; right:28px; bottom:51px; height:1px; } .comparison-chart:after { left:58px; top:28px; bottom:51px; width:1px; } .axis { position:absolute; color:var(--muted); font-size:12px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; } .axis.x { right:30px; bottom:20px; } .axis.y { top:30px; left:17px; writing-mode:vertical-rl; transform:rotate(180deg); } .chart-point { position:absolute; display:grid; place-items:center; width:22px; height:22px; border:3px solid #fffdf7; border-radius:50%; box-shadow:0 7px 16px rgba(15,48,40,.2); } .chart-point b { position:absolute; width:152px; left:20px; bottom:18px; color:var(--ink); font-size:13px; line-height:1.2; } .chart-point p { position:absolute; width:165px; left:20px; top:20px; margin:0; color:var(--muted); font-size:12px; line-height:1.35; } .chart-point.ai { left:25%; bottom:25%; background:#dc765c; } .chart-point.local { left:51%; bottom:51%; background:var(--sun); } .chart-point.checker { left:75%; bottom:74%; background:var(--green); }
.simple-flow { position:relative; display:grid; grid-template-columns:repeat(4,1fr); gap:0; margin-top:46px; border:1px solid var(--line); background:#fff; } .simple-flow:before { content:""; position:absolute; top:55px; left:12.5%; right:12.5%; height:1px; background:var(--line); } .simple-step { position:relative; min-height:272px; padding:28px 24px 22px; border-right:1px solid var(--line); } .simple-step:last-child { border-right:0; } .simple-number { position:relative; z-index:1; display:grid; place-items:center; width:56px; height:56px; border-radius:50%; background:var(--paper); border:1px solid var(--green); color:var(--green); font-size:20px; font-weight:900; } .simple-step:nth-child(2) .simple-number, .simple-step:nth-child(4) .simple-number { background:var(--sun); border-color:var(--sun); color:var(--deep); } .simple-step h3 { margin:38px 0 9px; font-size:23px; letter-spacing:-.04em; } .simple-step p { margin:0; color:var(--muted); line-height:1.53; } .flow-footer { display:flex; align-items:center; justify-content:space-between; gap:20px; margin-top:20px; padding:16px 0 0; color:var(--muted); font-size:14px; } .flow-footer strong { color:var(--deep); }
.gates { display:grid; grid-template-columns:1fr 1fr; gap:1px; margin-top:42px; background:var(--line); border:1px solid var(--line); } .gate { padding:30px; background:#fff; } .gate small { color:var(--green); font-weight:850; letter-spacing:.1em; text-transform:uppercase; } .gate h3 { margin:12px 0 10px; font-size:29px; letter-spacing:-.04em; } .gate p { margin:0; color:var(--muted); line-height:1.55; }
section.privacy { width:100%; margin:0; padding:108px 0 116px; border-top:0; background:linear-gradient(110deg, #dff4e9 0%, #d7efe3 56%, #cae8d9 100%); } .privacy-inner { width:min(1140px, calc(100% - 40px)); margin:0 auto; } .privacy-inner > .eyebrow { color:#256e5c; } .privacy-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:48px; row-gap:34px; margin-top:46px; } .privacy-grid div { min-height:112px; padding:20px 0 0; border-top:2px solid rgba(21,107,89,.78); } .privacy-grid strong { display:block; margin-bottom:9px; font-size:17px; letter-spacing:-.02em; } .privacy-grid span { display:block; max-width:500px; color:#38564b; line-height:1.58; }
.letter-example { display:grid; grid-template-columns:minmax(300px,.85fr) minmax(280px,.65fr); gap:56px; align-items:center; } .letter-example h2 { margin-bottom:16px; } .letter-example p { max-width:510px; color:var(--muted); font-size:17px; line-height:1.58; } .letter-points { display:grid; gap:13px; margin:28px 0 0; padding:0; list-style:none; } .letter-points li { display:grid; grid-template-columns:22px 1fr; gap:10px; color:#3f4d47; line-height:1.45; } .letter-points li:before { content:"✓"; color:var(--green); font-weight:950; } .demo-note { margin-top:26px; padding-top:16px; border-top:1px solid var(--line); font-size:13px !important; } .letter-frame { padding:20px; background:#e8eee8; border:1px solid #c4d2c6; box-shadow:18px 20px 0 rgba(21,107,89,.10); } .letter-frame img { display:block; width:100%; height:auto; background:#fff; box-shadow:0 14px 36px rgba(15,48,40,.18); } .sample-link { margin-top:26px; } .final { padding:90px max(20px, calc((100% - 1140px) / 2)); background:var(--deep); color:#fff; } .final h2 { max-width:790px; margin:10px 0 16px; font-size:clamp(38px,5vw,70px); line-height:.97; letter-spacing:-.06em; } .final p { max-width:660px; color:#d1e5da; font-size:18px; line-height:1.55; } .footer { padding:28px 0 42px; color:var(--muted); font-size:14px; display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; } .footer a { color:var(--green); font-weight:800; }
@media (max-width:850px) { .hero { min-height:auto; grid-template-columns:1fr; padding-top:36px; } .hero-visual { min-height:360px; } .features { grid-template-columns:1fr 1fr; } .comparison-layout,.letter-example,.setup-guide { grid-template-columns:1fr; gap:30px; } .simple-flow { grid-template-columns:1fr 1fr; } .simple-flow:before { display:none; } .simple-step:nth-child(2) { border-right:0; } .simple-step { min-height:230px; border-bottom:1px solid var(--line); } .simple-step:nth-child(3), .simple-step:nth-child(4) { border-bottom:0; } .privacy-grid { column-gap:30px; } }
@media (max-width:540px) { .nav,.section,.footer,.privacy-inner { width:min(100% - 40px,1140px); } .nav { align-items:flex-start; padding:18px 0; } .navlinks { gap:10px; justify-content:flex-end; } h1 { font-size:clamp(48px,15vw,70px); } .button { width:100%; } .features,.gates,.simple-flow,.privacy-grid { grid-template-columns:1fr; } .section { padding:72px 0; } .comparison-chart { min-height:330px; padding-left:46px; } .comparison-chart:before { left:46px; } .comparison-chart:after { left:46px; } .axis.y { left:10px; } .chart-point b { width:120px; } .chart-point p { width:126px; } .chart-point.checker { left:72%; } .chart-point.checker b, .chart-point.checker p { left:-112px; text-align:right; } section.privacy { padding:76px 0 82px; } .privacy-grid { row-gap:28px; margin-top:36px; } .privacy-grid div { min-height:auto; padding-top:17px; } .simple-step,.simple-step:nth-child(2) { min-height:auto; padding:24px; border-right:0; border-bottom:1px solid var(--line); } .simple-step:last-child { border-bottom:0; } .simple-step h3 { margin-top:22px; } .flow-footer { align-items:stretch; flex-direction:column; } }
</style>
</head>
<body>
<div class="shell">
  <nav class="nav" aria-label="Main navigation"><a class="brand" href="/">Student Application <span>AI Helper</span></a><div class="navlinks"><a href="#start">Start setup</a><a href="#how">How it works</a><a href="#gates">Quality gates</a><a href="#letter-example">Letter example</a><a href="#privacy">Privacy</a><a href="/sample-prompts">Prompts</a></div></nav>
  <main class="hero">
    <div><div class="kicker">Local-first career coach + MCP</div><h1>Turn your real experience into a stronger application.</h1><p class="lead">Build an evidence-grounded CV and cover letter in your own local folder. You keep control of every file and final decision.</p><div class="actions"><a class="button primary" href="#start">Start setup</a><a class="button secondary" href="/sample-prompts">Copy prompts</a></div><p class="connection">Start URL for your AI agent: <code>${PUBLIC_SITE_URL}</code>. The page explains setup, prompts, privacy, and how the agent connects to the MCP service.</p></div>
    <aside class="hero-visual" aria-label="Four-stage application process"><div class="stack"><div class="stage"><span class="stage-num">1</span><div><h2>Check the workspace</h2><p>The local SOP boots, audits folder health, and identifies safe updates or drift.</p></div></div><div class="stage"><span class="stage-num">2</span><div><h2>Build your evidence</h2><p>Use your CV, job description, personal bullets, documents, and real writing samples.</p></div></div><div class="stage"><span class="stage-num">3</span><div><h2>Draft locally</h2><p>Create an editable HTML CV and a role-specific cover letter from verified material.</p></div></div><div class="stage"><span class="stage-num">4</span><div><h2>Review before release</h2><p>One CV review; three cover-letter review loops; then a local release receipt.</p></div></div></div></aside>
  </main>
  <section id="how" class="section"><div class="eyebrow">What the helper does</div><h2>Clear preparation. Honest tailoring.</h2><p class="intro">The local AI agent explains the next useful action, asks for missing evidence, and flags a weak document before you send it.</p><div class="features"><div class="feature"><b>Workspace health</b><p>Audit folder drift and slow stages before changing an old workspace.</p></div><div class="feature"><b>Evidence into HTML</b><p>Turn verified CV material into an editable HTML CV for the target job.</p></div><div class="feature"><b>Interview prep</b><p>Optionally prepare likely questions, STAR stories, weaknesses, culture-fit answers, and questions to ask the team.</p></div></div></section>
  <section id="start" class="section"><div class="eyebrow">Start from an empty folder</div><h2>What you actually need to do first.</h2><p class="intro">Create a dedicated project folder, give your AI agent the root URL, then let the agent read the setup page and ask for missing source files one by one.</p><div class="setup-guide"><div class="setup-steps"><article class="setup-step"><strong>1</strong><div><h3>Create a clean project folder</h3><p>Use VS Code, Codex, Claude, or another local AI workspace. Name it something clear, for example <em>my-job-application</em>. Start empty so old files do not slow or confuse the setup.</p></div></article><article class="setup-step"><strong>2</strong><div><h3>Give the AI this URL</h3><p>Ask the local AI agent to read the root page, fetch the workspace template and kit, create the local folder structure, and ask questions whenever it needs your verification.</p></div></article><article class="setup-step"><strong>3</strong><div><h3>Provide your real source material</h3><p>Upload your CV or the best available profile source. Tell the AI whether you are doing a Bachelor, Master, Ausbildung/job training, or another path. Add human-written samples such as old emails, IELTS writing, user stories, PRDs, BRDs, reports, or notes. Pre-2022 writing is especially useful for learning your real tone.</p></div></article><article class="setup-step"><strong>4</strong><div><h3>Send a job description</h3><p>Find a job online and give the AI the job URL or pasted description. It checks fit against your verified CV evidence, then prepares a tailored English resume by default plus a cover letter when appropriate.</p></div></article></div><aside class="prompt-card"><h3>Copy this starter prompt</h3><p>Paste this into your local AI agent after opening your empty folder.</p><code>${PUBLIC_SITE_URL}</code><pre>Please read this Student Application AI Helper page and set up a local project folder for me to handle job applications.

Ask me questions along the way if you need my verification or validation.

If you need my picture, CV, cover letter, sample CV, sample cover letter, education track, writing samples, or job description, ask me and I will provide them.

Keep my private files local. Use the MCP only for workspace setup, safe structure/version audit, and selected-text writing review.</pre></aside></div></section>
  <section class="section" aria-labelledby="checker-value-title"><div class="eyebrow">Why the checker helps</div><div class="comparison-layout"><div class="comparison-copy"><h3 id="checker-value-title">Fast drafting is not the same as a strong application.</h3><p>Your local sources make a draft more truthful. A selected-text check adds a final reader-focused review before you decide to release it.</p><div class="comparison-legend"><span><i class="legend-dot rose"></i><span><strong>Normal AI</strong> — quick, but often generic.</span></span><span><i class="legend-dot gold"></i><span><strong>Local workspace</strong> — grounded in your evidence.</span></span><span><i class="legend-dot green"></i><span><strong>Local workspace + checker</strong> — evidence plus a focused quality review.</span></span></div></div><div class="comparison-chart" role="img" aria-label="Comparison chart. Normal AI is low on evidence and reader confidence; local workspace is higher; local workspace plus selected-text checker is highest."><span class="axis y">Reader confidence</span><span class="axis x">Evidence and review depth</span><span class="chart-point ai"><b>Normal AI</b><p>Fast draft</p></span><span class="chart-point local"><b>Local workspace</b><p>Grounded draft</p></span><span class="chart-point checker"><b>Local + checker</b><p>Focused review</p></span></div></div></section>
  <section class="section"><div class="eyebrow">The real workflow</div><h2>Four simple steps. Your files never leave your laptop.</h2><p class="intro">The local agent manages the work in your own folder. The public service cannot browse it; it only receives a privacy-safe structure check or text you actively choose to review.</p><div class="simple-flow" aria-label="Four-step application workflow"><article class="simple-step"><span class="simple-number">01</span><h3>Check the workspace</h3><p>The local SOP checks folder health, updates, and anything that may be making an old workspace slow.</p></article><article class="simple-step"><span class="simple-number">02</span><h3>Add your evidence</h3><p>Bring your CV, role or job description, personal work bullets, and any writing samples that sound like you.</p></article><article class="simple-step"><span class="simple-number">03</span><h3>Tailor locally</h3><p>The agent creates an editable HTML CV and a role-specific cover letter using only verified information.</p></article><article class="simple-step"><span class="simple-number">04</span><h3>Review and prepare</h3><p>Complete the CV/cover-letter gates, then optionally build interview prep from the same verified evidence.</p></article></div><div class="flow-footer"><span><strong>Need the technical detail?</strong> The sequence diagram and PlantUML source live on the technical page.</span><a class="button secondary" href="/technical-flow">Open technical flow</a></div></section>
  <section id="gates" class="section"><div class="eyebrow">Hard local gates</div><h2>The documents do not become “ready” just because a chat says so.</h2><p class="intro">The local Application SOP records the current artifact, review history, and release state. It catches edits made after review instead of treating an old approval as permanent.</p><div class="gates"><article class="gate"><small>CV</small><h3>One review loop</h3><p>Review the editable CV against the job and visual structure. If you accept a known weakness, it is recorded clearly; otherwise the agent explains what needs fixing.</p></article><article class="gate"><small>Cover letter</small><h3>Three distinct loops</h3><p>Each loop requires a current draft and a real revision record. The local SOP releases the letter only after it can verify all three loops against the latest file.</p></article></div></section>
  <section id="letter-example" class="section"><div class="letter-example"><div><div class="eyebrow">Rendered local output</div><h2>A German-style cover letter, built locally.</h2><p>This one-page LaTeX sample follows the familiar German business-letter structure: sender and recipient blocks, date, bold subject, salutation, evidence-led body, signature area, and enclosures.</p><ul class="letter-points"><li><span><strong>For Germany:</strong> use this structured business-letter format when it fits the employer and role.</span></li><li><span><strong>For other markets:</strong> keep the verified evidence and review process, then adapt language and conventions locally.</span></li><li><span><strong>Your signature:</strong> the agent asks for your PNG/JPG and uses it only if you provide it.</span></li></ul><p class="demo-note"><strong>Fictional demonstration only.</strong> The writing is adapted from a candidate-authorized Mercedes-Benz example; Jane Doe, the recruiting team, Stuttgart Hbf, and the signature graphic are placeholders. Never copy another person's signature.</p><p class="sample-link"><a class="button secondary" href="/assets/german-cover-letter-sample.pdf">Open the sample PDF</a></p></div><figure class="letter-frame"><img src="/assets/german-cover-letter-sample.svg" alt="One-page fictional German-format Mercedes-Benz cover letter for Jane Doe, including a clearly labelled fictional sample signature."></figure></div></section>
  <section id="privacy" class="privacy"><div class="privacy-inner"><div class="eyebrow">Privacy boundary</div><h2>Useful feedback without uploading your whole career history.</h2><div class="privacy-grid"><div><strong>Stays on your device</strong><span>Source CV, evidence, profile, writing samples, job files, photos, signatures, drafts, outputs, and SOP history.</span></div><div><strong>Can be sent deliberately</strong><span>A privacy-safe folder manifest for update/audit guidance, or selected writing text for a quality review.</span></div><div><strong>Comes back from the MCP</strong><span>Workspace/version guidance and selected-text feedback: issues, risk labels, and practical revision direction.</span></div><div><strong>What it does not claim</strong><span>It is not an authorship verdict or an AI-detection bypass. It helps you make writing clearer, more evidenced, and more trustworthy.</span></div></div></div></section>
  <section class="final"><div class="kicker" style="color:var(--sun)">Ready when you are</div><h2>Start with the files you already have. Improve the package one honest step at a time.</h2><p>The prompt page tells your AI agent exactly how to set up, audit, prepare, draft, and review the local workspace.</p><div class="actions"><a class="button primary" style="background:var(--sun);color:var(--deep)" href="/sample-prompts">Open guided prompts</a><a class="button secondary" style="border-color:#729489;color:#fff" href="/privacy">Read privacy details</a></div></section>
  <footer class="footer"><span>Student Application AI Helper · local-first application workflow · MCP v${VERSION} · kit ${WORKSPACE_KIT_VERSION}</span><span><a href="/health">Service health</a> · <a href="/sample-prompts">Sample prompts</a> · <a href="/technical-flow">Technical flow</a> · <a href="/cv-template/english">English CV</a> · <a href="/cv-template/german">German CV</a> · <a href="https://pmlecuong.com/" target="_blank" rel="noopener noreferrer">Built by pmlecuong.com ↗</a></span></footer>
</div>
</body>
</html>`;
}

function renderTechnicalFlowPage(): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Technical Flow - Student Application AI Helper</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --paper:#fff8ea; --ink:#17130f; --muted:#62594d; --line:#dfd4bd; --green:#167766; --green-dark:#123f37; --gold:#f4c765; }
* { box-sizing: border-box; }
body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:linear-gradient(180deg,var(--paper),#fffdf7); }
main { width:min(1120px, calc(100% - 36px)); margin:0 auto; padding:28px 0 64px; }
.top { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:42px; }
.brand { font-weight:900; text-decoration:none; color:var(--green-dark); }
.top a:not(.brand) { color:var(--muted); text-decoration:none; font-weight:750; }
.hero { display:grid; grid-template-columns:minmax(0,.9fr) minmax(280px,.55fr); gap:28px; align-items:end; margin-bottom:26px; }
.eyebrow { display:inline-flex; padding:8px 12px; border-radius:999px; border:1px solid var(--line); background:#fffaf0; color:var(--green-dark); font-weight:800; font-size:13px; }
h1 { margin:18px 0 14px; font-size:clamp(38px,7vw,78px); line-height:.95; letter-spacing:0; }
.lead { max-width:760px; color:var(--muted); font-size:19px; line-height:1.55; margin:0; }
.note { border-left:4px solid var(--gold); padding:14px 0 14px 16px; color:var(--muted); line-height:1.55; }
.diagram { background:white; border:1px solid var(--line); border-radius:14px; padding:18px; overflow:auto; box-shadow:0 22px 60px rgba(18,63,55,.1); }
.diagram img { display:block; width:min(100%, 980px); min-width:680px; height:auto; margin:0 auto; }
.diagram-section { margin-top:56px; padding-top:50px; border-top:1px solid var(--line); }
.diagram-section h2 { margin:0 0 10px; font-size:clamp(30px,4vw,48px); line-height:1; letter-spacing:-.04em; }
.diagram-section p { max-width:760px; margin:0 0 24px; color:var(--muted); line-height:1.55; }
.protocol-grid { display:grid; grid-template-columns:180px minmax(0,1fr); border-top:1px solid var(--line); border-left:1px solid var(--line); background:#fffdf7; }
.protocol-grid div { padding:16px 18px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); color:var(--muted); line-height:1.5; }
.protocol-grid .method { color:var(--green-dark); font-weight:850; background:#fffaf0; }
.protocol-grid code { color:var(--ink); font-size:.93em; font-weight:750; overflow-wrap:anywhere; }
.protocol-note { margin-top:18px !important; padding-left:16px; border-left:3px solid var(--gold); }
.grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; margin-top:28px; }
.tile { background:rgba(255,255,255,.66); border:1px solid var(--line); border-top:4px solid var(--green); border-radius:12px; padding:18px; }
.tile h2 { margin:0 0 8px; font-size:19px; }
.tile p { margin:0; color:var(--muted); line-height:1.52; }
.links { display:flex; flex-wrap:wrap; gap:12px; margin-top:24px; }
.button { display:inline-flex; min-height:44px; align-items:center; justify-content:center; padding:0 15px; border-radius:7px; text-decoration:none; font-weight:850; }
.primary { background:var(--green-dark); color:#fffaf0; }
.secondary { border:1px solid var(--line); color:var(--ink); background:#fffaf0; }
@media (max-width:800px) { .hero, .grid, .protocol-grid { grid-template-columns:1fr; } .diagram img { min-width:620px; } .protocol-grid div { border-right:1px solid var(--line); } .protocol-grid .method { padding-bottom:7px; border-bottom:0; } }
</style>
</head>
<body>
<main>
  <nav class="top" aria-label="Technical flow navigation">
    <a class="brand" href="/">🧭 Student Application AI Helper</a>
    <a href="/sample-prompts">Prompts</a>
  </nav>
  <section class="hero">
    <div>
      <div class="eyebrow">Technical sequence diagram</div>
      <h1>How the local workflow and review boundary work.</h1>
      <p class="lead">The local Application SOP checks workspace health, records release evidence, and keeps private files on the laptop. The MCP sees only a privacy-safe folder manifest or writing text the candidate deliberately selects for review.</p>
    </div>
    <p class="note">The service returns guidance, not private checker implementation details. It cannot browse the candidate's local workspace.</p>
  </section>
  <section class="diagram" aria-label="Technical sequence diagram">
    <img src="/assets/private-checker-flow.svg" alt="Sequence diagram showing selected-text review between the candidate, local AI agent, local workspace, and MCP checker">
  </section>
  <section class="grid" aria-label="Flow notes">
    <div class="tile"><h2>Local SOP gate</h2><p>The local controller records a strict boot, current artifact hashes, one CV review, and three distinct cover-letter loops before release.</p></div>
    <div class="tile"><h2>Selected text only</h2><p>The candidate or local agent chooses a paragraph or cover letter to send. It never uploads the CV, workspace, job folder, or output PDFs.</p></div>
    <div class="tile"><h2>Feedback returns</h2><p>The service returns high-level issue labels, risk, and revision guidance. The local agent applies edits and verifies readiness on the laptop.</p></div>
  </section>
  <section class="diagram-section" aria-labelledby="bootstrap-title">
    <div class="eyebrow">Bootstrap and scaffolding</div>
    <h2 id="bootstrap-title">How a human prompt creates a safe local foundation.</h2>
    <p>This diagram shows the one-time setup path: the MCP returns only generic kit files and structure, while the local agent and local SOP create, inspect, and retain the real candidate workspace.</p>
    <div class="diagram" aria-label="Bootstrap and local scaffolding sequence diagram">
      <img src="/assets/bootstrap-scaffolding-flow.svg" alt="Sequence diagram showing human request, public MCP kit retrieval, local workspace scaffolding, strict SOP boot, and privacy-safe manifest audit">
    </div>
  </section>
  <section class="diagram-section" aria-labelledby="protocol-title">
    <div class="eyebrow">HTTP and MCP protocol</div>
    <h2 id="protocol-title">What actually calls what.</h2>
    <p>The human setup URL is <code>${PUBLIC_SITE_URL}</code>. The Streamable HTTP MCP transport endpoint is <code>${PUBLIC_MCP_ENDPOINT}</code>. A compatible AI client sends JSON-RPC requests to the transport endpoint; it does not receive shell or filesystem access to the candidate computer.</p>
    <div class="protocol-grid" aria-label="HTTP endpoint and request contract">
      <div class="method"><code>OPTIONS /mcp</code></div><div>Browser CORS preflight. The server responds <code>204</code> and allows <code>content-type</code>, <code>authorization</code>, and <code>mcp-session-id</code> headers.</div>
      <div class="method"><code>POST /mcp</code></div><div>The MCP transport endpoint. Send <code>content-type: application/json</code> and an <code>Accept</code> header that includes <code>application/json</code> or <code>text/event-stream</code>. The client then sends JSON-RPC lifecycle requests such as <code>initialize</code> and <code>tools/list</code>, followed by JSON-RPC <code>tools/call</code> requests.</div>
      <div class="method"><code>tools/call</code></div><div>For setup, the local agent calls <code>get_workspace_template</code> or <code>get_application_kit_bundle</code>. For structure health, it calls <code>audit_workspace_manifest</code> with relative paths and managed-file hashes only.</div>
      <div class="method"><code>tools/call</code></div><div>For writing review, it calls <code>check_writing_human_fit</code> with selected text and a mode. It does not send the CV, local folder, images, signature, or generated PDF.</div>
      <div class="method"><code>GET /health</code></div><div>Simple service health and public-tool inventory for local diagnosis; it is not a candidate-data API.</div>
      <div class="method"><code>GET /assets/*.puml</code></div><div>Read-only canonical PlantUML source for the public technical diagrams. Rendered SVG diagrams are served from matching <code>/assets/*.svg</code> routes.</div>
    </div>
    <p class="protocol-note">The HTTP handler permits only <code>POST</code> on <code>/mcp</code>; other methods receive <code>405</code>. Public request bodies are limited to 64 KiB. The endpoint is intentionally unauthenticated in this release, but it is stateless and does not persist candidate profiles or workspace files.</p>
  </section>
  <div class="links">
    <a class="button primary" href="/">Back to main page</a>
    <a class="button secondary" href="/assets/private-checker-flow.puml">Open review-diagram source</a>
    <a class="button secondary" href="/assets/local-first-human-flow.puml">Open full-workflow source</a>
    <a class="button secondary" href="/assets/bootstrap-scaffolding-flow.puml">Open bootstrap-diagram source</a>
  </div>
</main>
</body>
</html>`;
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

  if (url.pathname === "/handout") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(await renderMarkdownAsHtml(handout, "Student Application AI Helper"));
    return;
  }

  if (url.pathname === "/sample-prompts") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(await renderMarkdownAsHtml(samplePrompts, "Student Application AI Helper Prompts"));
    return;
  }

  if (url.pathname === "/privacy") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(
      await renderMarkdownAsHtml(
        [
          "# Privacy",
          "",
          "The service is local-first. Your AI agent should keep your full workspace on your laptop.",
          "",
          "The writing checker receives only the text you intentionally submit for feedback. It returns issues and revision guidance. It does not need your CV, job folder, source files, or final documents.",
          "",
          "Do not use the checker for passwords, identity documents, medical records, bank records, or secrets.",
          "",
          "The checker is a writing-quality helper, not proof that text was or was not written by AI."
        ].join("\n"),
        "Student Application AI Helper Privacy"
      )
    );
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
      remoteProcessing: "transient writing checks only",
      tokenRequired: Boolean(TOKEN),
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
