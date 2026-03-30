"use client";

import { useEffect, useMemo, useState } from "react";
import { ResumeDocument } from "@/components/resume-document";
import type { ResumeData } from "@/lib/types";

interface GeneratedResumeClientPageProps {
  initialParams?: {
    company: string;
    role: string;
  };
}

export function GeneratedResumeClientPage({
  initialParams,
}: GeneratedResumeClientPageProps) {
  const [data, setData] = useState<ResumeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<{
    company: string;
    role: string;
  } | null>(initialParams ?? null);

  useEffect(() => {
    if (initialParams) {
      return;
    }
    const searchParams = new URLSearchParams(window.location.search);
    setParams({
      company: searchParams.get("company") ?? "",
      role: searchParams.get("role") ?? "",
    });
  }, [initialParams]);

  const dataUrl = useMemo(
    () =>
      params
        ? `/cuongcv/generated-cv-data/${encodeURIComponent(params.company)}/${encodeURIComponent(params.role)}.json`
        : "",
    [params]
  );

  useEffect(() => {
    document.body.dataset.generatedCvStatus = "loading";

    if (!params) {
      return;
    }

    if (!params.company || !params.role) {
      setData(null);
      setError("Missing company or role query parameter.");
      document.body.dataset.generatedCvStatus = "error";
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
          document.body.dataset.generatedCvStatus = "ready";
        }
      } catch (loadError) {
        if (!cancelled) {
          setData(null);
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load generated CV."
          );
          document.body.dataset.generatedCvStatus = "error";
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
