import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const mcpUrl = process.env.MCP_URL ?? "http://127.0.0.1:5920/mcp";
const token = process.env.APPLICATION_MCP_TOKEN;

const expectedTools = [
  "audit_workspace_manifest",
  "check_writing_human_fit",
  "get_application_kit_bundle",
  "get_application_kit_manifest",
  "get_client_skill",
  "get_onboarding_instructions",
  "get_sample_prompts",
  "get_workspace_template",
  "health",
  "suggest_writing_revision"
];

const client = new Client({ name: "student-application-ai-helper-smoke", version: "0.1.0" });
const transport = new StreamableHTTPClientTransport(new URL(mcpUrl), {
  requestInit: token
    ? {
        headers: {
          authorization: `Bearer ${token}`
        }
      }
    : undefined
});

await client.connect(transport);

try {
  const tools = await client.listTools();
  const names = tools.tools.map((tool) => tool.name).sort();
  assert.deepEqual(names, expectedTools);

  const skillResult = await client.callTool({ name: "get_client_skill", arguments: {} });
  const skill = JSON.parse(skillResult.content[0].text);
  assert.match(skill.content, /Student Application Client/);
  assert.match(skill.content, /selected-text writing checks/);

  const templateResult = await client.callTool({ name: "get_workspace_template", arguments: {} });
  const template = JSON.parse(templateResult.content[0].text);
  assert.equal(template.root, "student-application-workspace");
  assert.ok(template.files.some((file) => file.path === "profile/master_profile.json"));
  assert.ok(template.files.some((file) => file.path === "memory/skill_memory.md"));
  assert.ok(template.files.some((file) => file.path === "scripts/migrate_legacy_workspace.py"));
  assert.ok(template.files.some((file) => file.path === "scripts/audit_voice_fit.py"));
  assert.ok(!template.files.some((file) => file.path.includes("audit_human_fit")));

  const kitResult = await client.callTool({ name: "get_application_kit_manifest", arguments: {} });
  const kit = JSON.parse(kitResult.content[0].text);
  assert.equal(kit.manifest.mode, "local-only");
  assert.equal(kit.manifest.privacy.advanced_checker_rules_in_bundle, false);

  const checkResult = await client.callTool({
    name: "check_writing_human_fit",
    arguments: {
      mode: "academic",
      text:
        "This paper will prove a groundbreaking result. The study is important. The study is useful. The study is clearly revolutionary for students and institutions."
    }
  });
  const check = JSON.parse(checkResult.content[0].text);
  assert.equal(check.mode, "academic");
  assert.equal(check.privacy.stored, false);
  assert.ok(check.issues.length > 0);

  const promptsResult = await client.callTool({ name: "get_sample_prompts", arguments: {} });
  const prompts = JSON.parse(promptsResult.content[0].text);
  assert.match(prompts.content, /Student Application AI Helper Prompts/);
  assert.match(prompts.content, /https:\/\/jobmcp\.pmlecuong\.com\/mcp/);

  console.log(
    JSON.stringify(
      {
        ok: true,
        mcpUrl,
        mode: "local-kit-plus-private-writing-checker",
        kitVersion: kit.manifest.version,
        tools: names
      },
      null,
      2
    )
  );
} finally {
  await client.close();
}
