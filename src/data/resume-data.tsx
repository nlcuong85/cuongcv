import type { ResumeData } from "@/lib/types";

export const RESUME_DATA: ResumeData = {
  name: "Cuong Le Nguyen",
  initials: "CLN",
  location: "Gildenstraße 13, 74074 Heilbronn, Germany",
  locationLink:
    "https://www.google.com/maps/place/Gildenstra%C3%9Fe+13,+74074+Heilbronn,+Germany",
  about:
    "Product Owner/Manager building AI-enabled and B2B products across eCommerce, LegalTech, and Ai-enable Apps.",
  summary: (
    <>
      Experienced product professional with a strong foundation in research,
      requirements, stakeholder alignment, rollout, and continuous improvement.
      I have worked across eCommerce, LegalTech, healthcare, and digital
      operations, with a focus on structured execution and measurable business
      impact.
    </>
  ),
  avatarUrl: "/cuongcv/images/avatar.jpg",
  personalWebsiteUrl: "https://pmlecuong.com/",
  contact: {
    email: "nlcuong999@gmail.com",
    tel: "+49 163 3628505",
    social: [
      {
        name: "GitHub",
        url: "https://github.com/nlcuong85",
        icon: "github",
      },
      {
        name: "LinkedIn",
        url: "https://www.linkedin.com/in/lecuongair/",
        icon: "linkedin",
      },
    ],
  },
  education: [
    {
      school: "Heilbronn University",
      degree: "Master in Software Engineering",
      start: "Summer 2026",
      end: "Present",
      location: "Heilbronn, Germany",
    },
    {
      school: "Vietnamese-German University (VGU)",
      degree: "MA in Business Information Systems (BIS)",
      start: "2024",
      end: "Present",
      location: "Binh Duong, Vietnam",
    },
    {
      school: "Troy University, Alabama, USA (HCMC campus)",
      degree:
        "BA in Business Administration and General Management; GPA: 3.3/4.0",
      start: "2010",
      end: "2015",
      location: "Ho Chi Minh City, Vietnam",
    },
    {
      school: "Newlands College (High School), New Zealand",
      degree: "Grade 12th & 13th",
      start: "2009",
      end: "2010",
      location: "Wellington, New Zealand",
    },
  ],
  work: [
    {
      company: "Kyanon Digital – IT Services and Consulting",
      link: "https://kyanon.digital/",
      badges: ["Onsite"],
      title: "Senior Product Owner",
      start: "Aug 2024",
      end: "Jan 2026",
      description: (
        <>
          Led product delivery and rollout planning for AEON Vietnam digital
          products, including AEON Kids Version 2 and the iAEON super-app
          initiative.
          <ul className="list-inside list-disc">
            <li>
              Owned backlog, delivery coordination, and cross-functional
              alignment across design, engineering, QC, and business
              stakeholders
            </li>
            <li>
              Contributed to the presentation and solution framing that helped
              win the AEON super-app engagement for the AEON group in Vietnam
            </li>
            <li>
              Supported AEON Kids Version 2 rollout and formalized
              Jira/Confluence/OKR working templates to improve visibility and
              execution discipline
            </li>
          </ul>
        </>
      ),
    },
    {
      company: "SCCK.vn – Ecommerce Platform for Mechanical Market",
      link: "https://scck.vn/",
      badges: ["Remote"],
      title: "Product Development Manager",
      start: "Jul 2020",
      end: "Jul 2024",
      description: (
        <>
          Built product workflows, supplier onboarding, and buyer experience for
          a B2B marketplace serving Vietnam’s mechanical and industrial sourcing
          sector.
          <ul className="list-inside list-disc">
            <li>
              Led cross-functional delivery across operations, engineering, and
              product design to improve marketplace trust, onboarding, and
              real-world purchasing workflows
            </li>
            <li>
              Shaped marketplace features around supplier credibility, category
              complexity, COD expectations, and operational constraints rather
              than a consumer-style storefront model
            </li>
            <li>
              Developed and deployed “Ní Cơ Khí,” an AI chatbot using Botpress
              and OpenAI for FAQs and real-time price lookups
            </li>
          </ul>
        </>
      ),
    },
    {
      company: "Anduin Transaction – Onboarding App for Private Markets",
      link: "https://www.anduintransact.com/",
      badges: ["Onsite"],
      title: "Associate Product Manager",
      start: "Feb 2021",
      end: "May 2023",
      description: (
        <>
          Drove onboarding experience improvements for private capital firms and
          digital signing adoption.
          <ul className="list-inside list-disc">
            <li>
              Coordinated with legal and vendors (GlobalSign, DocuSign) to meet
              EU AES/QES standards → 40% increase in secure signing adoption
            </li>
            <li>
              Migrated project management from Airtable to Jira enabling the
              company to track and prioritize 3× more requests
            </li>
            <li>
              Partnered with CS/Data to address drivers of low NPS and maintain
              an average score of 75 in 2022
            </li>
          </ul>
        </>
      ),
    },
    {
      company: "Talosix LLC – Healthcare App Product",
      link: "https://www.talosix.com/",
      badges: ["Onsite"],
      title: "Product Owner",
      start: "Jun 2019",
      end: "Feb 2021",
      description: (
        <>
          Improved patient care and clinical workflows with compliance and UX
          initiatives.
          <ul className="list-inside list-disc">
            <li>
              Co-developed HIPAA and GDPR roadmaps → reduced compliance
              incidents by 30%
            </li>
            <li>
              Evaluated and remedied poor UX in core flows with stakeholders and
              engineering
            </li>
            <li>
              Shipped OCR note-reading feature improving doctor productivity by
              20% and helping secure a $2M UK project
            </li>
          </ul>
        </>
      ),
    },
    {
      company: "NashTech Global",
      link: "https://www.nashtechglobal.com/",
      badges: ["Onsite"],
      title: "Business Analyst",
      start: "Mar 2018",
      end: "Jun 2019",
      description: (
        <>
          Delivered requirements and documentation for multi-industry projects.
          <ul className="list-inside list-disc">
            <li>
              Delivered the Fitness First self-service app suite, replacing
              legacy member workflows and saving the client $500k/year
            </li>
            <li>
              Authored user stories, acceptance criteria, process diagrams, and
              workflows to ensure clarity and alignment
            </li>
          </ul>
        </>
      ),
    },
  ],
  skills: [
    "Product Roadmapping",
    "Market Research",
    "UX/UI",
    "Business Analyst",
    "Information Architecture",
    "Operation Management and Process",
    "Professional English",
    "Agile & Scrum",
    "Figma",
    "Jira",
    "Confluence",
    "Business Mindset",
    "HTML & CSS",
    "Next.js",
    "C++",
    "SQL",
    "Ai Tech Stack 2025",
    "Linux",
    "n8n Automation",
    "Docker",
    "Github",
    "HomeLab",
    "3D Prototyping and Manufacturing",
    "Spec-Driven Development (AWS framework)",
    "Context Engineering",
  ],
  awards: [
    "Product Management 101 - Udemy",
    "Advanced Product Management: Vision, Strategy & Metric - Udemy",
    "Scrum Fundamentals Certified - SCRUMstudy: 746783",
    "UI UX 101: Digital Product Design - Keyframe HCM",
    "Foundation of Project Management - Google on Coursera",
    "Project Initiation - Starting a successful project - Google on Coursera",
    "IELTS 7.5 - Issued on April 2025",
    "AI Mentor for Kyanon Fresher",
  ],
  projects: [
    {
      title: "AI-Powered WordPress CMS Portal",
      techStack: [
        "TypeScript",
        "Next.js",
        "WordPress API",
        "OpenAI",
        "Gemini",
        "Claude",
      ],
      description:
        "Private portal that connects user WordPress sites to a CMS; uses AI agents to draft, revise, and publish posts with change tracking.",
    },
    {
      title: "AI To-Do Insights (Stealth)",
      techStack: [
        "TypeScript",
        "Next.js",
        "AI",
        "React Native",
        "iOS",
        "Android",
        "Local-first",
      ],
      description:
        "Stealth-mode to-do app that surfaces insights and suggests next steps using AI.",
    },
    {
      title: "RouteOps",
      techStack: ["React", "TypeScript", "Fastify", "SQLite"],
      description:
        "Browser-based travel-planning decision-support prototype with a local Fastify backend, deterministic best-balance/cheapest/most-comfort outputs, and saved trip history.",
    },
  ],
} as const;
