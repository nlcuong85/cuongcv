"use client";

import { useEffect, useMemo, useState } from "react";
import { ResumeDocument } from "@/components/resume-document";
import type { ResumeData } from "@/lib/types";

export function GeneratedResumeClientPage() {
  const [data, setData] = useState<ResumeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<{
    company: string;
    role: string;
  } | null>(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    setParams({
      company: searchParams.get("company") ?? "",
      role: searchParams.get("role") ?? "",
    });
  }, []);

  const dataUrl = useMemo(
    () =>
      params
        ? `/cuongcv/generated-cv-data/${encodeURIComponent(params.company)}/${encodeURIComponent(params.role)}.json`
        : "",
    [params]
  );

  useEffect(() => {
    if (!params) {
      return;
    }

    if (!params.company || !params.role) {
      setError("Missing company or role query parameter.");
      return;
    }

    let cancelled = false;
    setError(null);

    async function loadResume() {
      try {
        const response = await fetch(dataUrl, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Failed to load generated CV (${response.status})`);
        }
        const payload = (await response.json()) as ResumeData;
        if (!cancelled) {
          setData(payload);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load generated CV."
          );
        }
      }
    }

    void loadResume();

    return () => {
      cancelled = true;
    };
  }, [dataUrl, params]);

  if (error) {
    return (
      <main className="container mx-auto max-w-3xl p-6">
        <p className="font-mono text-sm text-red-700">{error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="container mx-auto max-w-3xl p-6">
        <p className="font-mono text-sm text-muted-foreground">
          Loading generated CV...
        </p>
      </main>
    );
  }

  return <ResumeDocument data={data} showCommandMenu={false} />;
}
