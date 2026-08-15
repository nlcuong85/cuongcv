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
