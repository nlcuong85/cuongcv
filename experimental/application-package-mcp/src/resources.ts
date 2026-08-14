import { promises as fs } from "node:fs";
import path from "node:path";

export type TemplateFile = {
  path: string;
  content: string;
};

export function projectRoot(): string {
  return process.env.APPLICATION_MCP_PROJECT_ROOT ?? process.cwd();
}

export function resourcesDir(): string {
  return path.join(projectRoot(), "resources");
}

export async function readResource(relativePath: string): Promise<string> {
  const root = resourcesDir();
  const target = path.normalize(path.join(root, relativePath));
  if (!target.startsWith(root)) {
    throw new Error(`Unsafe resource path: ${relativePath}`);
  }
  return fs.readFile(target, "utf8");
}

export async function readResourceBinary(relativePath: string): Promise<Buffer> {
  const root = resourcesDir();
  const target = path.normalize(path.join(root, relativePath));
  if (!target.startsWith(root)) {
    throw new Error(`Unsafe resource path: ${relativePath}`);
  }
  return fs.readFile(target);
}

export async function readTemplateDirectory(relativePath: string): Promise<TemplateFile[]> {
  const root = path.join(resourcesDir(), relativePath);
  const files: TemplateFile[] = [];
  const binarySuffixes = [".pdf", ".png", ".jpg", ".jpeg", ".svg", ".ttf", ".otf", ".woff", ".woff2"];

  async function walk(current: string): Promise<void> {
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      if (
        entry.name === ".DS_Store" ||
        entry.name === "__pycache__" ||
        entry.name.endsWith(".pyc") ||
        binarySuffixes.some((suffix) => entry.name.toLowerCase().endsWith(suffix))
      ) {
        continue;
      }
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
      } else if (entry.isFile()) {
        files.push({
          path: path.relative(root, full),
          content: await fs.readFile(full, "utf8")
        });
      }
    }
  }

  await walk(root);
  return files.sort((a, b) => a.path.localeCompare(b.path));
}

export async function onboardingInstructions(): Promise<string> {
  return readResource("onboarding.md");
}

export async function handoutDocument(): Promise<string> {
  const root = projectRoot();
  return fs.readFile(path.join(root, "handout", "student-application-ai-helper.md"), "utf8");
}

export async function samplePromptsDocument(): Promise<string> {
  return readResource("sample-prompts.md");
}
