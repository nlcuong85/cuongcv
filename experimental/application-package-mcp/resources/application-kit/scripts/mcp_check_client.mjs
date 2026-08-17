#!/usr/bin/env node
// Public MCP caller only. It deliberately contains no checker rules or scores.
import fs from "node:fs/promises";

const endpoint = process.env.APPLICATION_MCP_URL ?? "https://jobmcp.pmlecuong.com/mcp";
const [command, inputPath, outputPath] = process.argv.slice(2);
if (!command || !inputPath || !outputPath) {
  console.error("Usage: mcp_check_client.mjs <review|audit|ats> <input.json> <output.json>");
  process.exit(2);
}
const input = JSON.parse(await fs.readFile(inputPath, "utf8"));
const toolByCommand = {
  audit: "audit_workspace_manifest",
  review: "check_writing_human_fit",
  ats: "check_ats_resume_fit"
};
const tool = toolByCommand[command];
if (!tool) {
  console.error("Unknown command. Use review, audit, or ats.");
  process.exit(2);
}
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), 20_000);
try {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {"content-type": "application/json", accept: "application/json, text/event-stream"},
    body: JSON.stringify({jsonrpc: "2.0", id: 1, method: "tools/call", params: {name: tool, arguments: input}}),
    signal: controller.signal
  });
  if (!response.ok) throw new Error(`MCP request failed (${response.status})`);
  const body = await response.text();
  // Streamable HTTP commonly returns an SSE frame (`event: message` + `data:`).
  // Accept both that framing and a direct JSON response without interpreting any
  // checker content locally.
  const dataLine = body.split("\n").find((line) => line.startsWith("data: "));
  const message = dataLine ? dataLine.slice(6) : body;
  const result = JSON.parse(message);
  const content = result.result?.content?.[0]?.text;
  if (!content) throw new Error("MCP response did not include a bounded text result.");
  await fs.writeFile(outputPath, `${JSON.stringify(JSON.parse(content), null, 2)}\n`);
} catch (error) {
  console.error(error instanceof Error ? error.message : "MCP request failed");
  process.exit(1);
} finally {
  clearTimeout(timer);
}
