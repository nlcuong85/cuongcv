import React from "react";
import { Section } from "@/components/ui/section";

type Awards = readonly string[];

interface AwardsProps {
  awards: Awards | undefined;
}

export function Awards({ awards }: AwardsProps) {
  if (!awards || awards.length === 0) return null;

  return (
    <Section>
      <h2 className="text-xl font-bold" id="awards-section">
        Awards & Certifications
      </h2>
      <ul className="list-inside list-disc space-y-1 font-mono text-xs print:text-[10px]" aria-labelledby="awards-section">
        {awards.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </Section>
  );
}

