import { Suspense } from "react";
import { Awards } from "@/app/components/Awards";
import { Education } from "@/app/components/Education";
import { Header } from "@/app/components/Header";
import { Projects } from "@/app/components/Projects";
import { Skills } from "@/app/components/Skills";
import { Summary } from "@/app/components/Summary";
import { WorkExperience } from "@/app/components/WorkExperience";
import { CommandMenu } from "@/components/command-menu";
import { SectionErrorBoundary } from "@/components/section-error-boundary";
import { SectionSkeleton } from "@/components/section-skeleton";
import type { ResumeData } from "@/lib/types";

interface ResumeDocumentProps {
  data: ResumeData;
  showCommandMenu?: boolean;
}

function getCommandMenuLinks(data: ResumeData) {
  const links = [];

  if (data.personalWebsiteUrl) {
    links.push({
      url: data.personalWebsiteUrl,
      title: "Personal Website",
    });
  }

  return [
    ...links,
    ...data.contact.social.map((socialMediaLink) => ({
      url: socialMediaLink.url,
      title: socialMediaLink.name,
    })),
  ];
}

export function ResumeDocument({
  data,
  showCommandMenu = true,
}: ResumeDocumentProps) {
  return (
    <main
      className="container relative mx-auto scroll-my-12 overflow-auto p-4 print:p-11 md:p-16"
      id="main-content"
    >
      <div className="sr-only">
        <h1>{data.name}&apos;s Resume</h1>
      </div>

      <section
        className="mx-auto w-full max-w-2xl space-y-8 bg-white print:space-y-4"
        aria-label="Resume Content"
      >
        <SectionErrorBoundary sectionName="Header">
          <Suspense fallback={<SectionSkeleton lines={4} />}>
            <Header data={data} />
          </Suspense>
        </SectionErrorBoundary>

        <div className="space-y-8 print:space-y-4">
          <SectionErrorBoundary sectionName="Summary">
            <Suspense fallback={<SectionSkeleton lines={2} />}>
              <Summary summary={data.summary} />
            </Suspense>
          </SectionErrorBoundary>

          <SectionErrorBoundary sectionName="Work Experience">
            <Suspense fallback={<SectionSkeleton lines={6} />}>
              <WorkExperience work={data.work} />
            </Suspense>
          </SectionErrorBoundary>

          <SectionErrorBoundary sectionName="Education">
            <Suspense fallback={<SectionSkeleton lines={3} />}>
              <Education education={data.education} />
            </Suspense>
          </SectionErrorBoundary>

          <SectionErrorBoundary sectionName="Skills">
            <Suspense fallback={<SectionSkeleton lines={2} />}>
              <Skills skills={data.skills} />
            </Suspense>
          </SectionErrorBoundary>

          <SectionErrorBoundary sectionName="Awards & Certifications">
            <Suspense fallback={<SectionSkeleton lines={3} />}>
              <Awards awards={data.awards} />
            </Suspense>
          </SectionErrorBoundary>

          <SectionErrorBoundary sectionName="Projects">
            <Suspense fallback={<SectionSkeleton lines={5} />}>
              <Projects projects={data.projects} />
            </Suspense>
          </SectionErrorBoundary>
        </div>
      </section>

      {showCommandMenu ? (
        <nav className="print:hidden" aria-label="Quick navigation">
          <CommandMenu links={getCommandMenuLinks(data)} />
        </nav>
      ) : null}
    </main>
  );
}
