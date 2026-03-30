import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ResumeDocument } from "@/components/resume-document";
import type { ResumeData } from "@/lib/types";

async function loadGeneratedResumeData() {
  const filePath = join(
    process.cwd(),
    "public",
    "generated-cv-data",
    "current.json"
  );
  const raw = await readFile(filePath, "utf-8");
  return JSON.parse(raw) as ResumeData;
}

export default async function GeneratedResumePage() {
  try {
    const data = await loadGeneratedResumeData();
    return <ResumeDocument data={data} showCommandMenu={false} />;
  } catch {
    return (
      <main className="container mx-auto max-w-3xl p-6">
        <p className="font-mono text-sm text-red-700">
          No generated CV is ready for printing yet.
        </p>
      </main>
    );
  }
}
