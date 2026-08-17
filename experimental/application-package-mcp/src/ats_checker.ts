export type AtsTerm = {
  term: string;
  variants?: string[];
  weight?: number;
  priority?: "high" | "medium" | "low";
  suggestedSection?: "summary" | "skills" | "experience" | "education" | "projects";
  confirmation?: "already_supported" | "needs_user_confirmation" | "learning_or_exposure_only" | "unsupported_do_not_add";
};

export type AtsCheckInput = {
  document_kind?: "cv" | "resume";
  market?: string;
  language?: string;
  role_family?: string;
  company_name?: string;
  job_title?: string;
  job_description: string;
  resume_text: string;
  resume_sections?: Record<string, string | undefined>;
  known_evidence_terms?: string[];
  protected_facts?: string[];
  target_score?: number;
  max_new_terms?: number;
};

export type AtsKeyword = {
  term: string;
  source: "jd_exact" | "jd_normalized" | "role_taxonomy";
  confidence: number;
};

export type AtsMissingKeyword = {
  term: string;
  priority: "high" | "medium" | "low";
  reason: string;
  safe_to_add: boolean;
  requires_user_confirmation: boolean;
  suggested_section: "summary" | "skills" | "experience" | "education" | "projects";
  rewrite_instruction: string;
};

export type AtsRisk = {
  type:
    | "missing_exact_keyword"
    | "missing_tool_acronym"
    | "missing_domain_phrase"
    | "education_mismatch"
    | "language_mismatch"
    | "format_parse_risk"
    | "keyword_stuffing_risk";
  severity: "high" | "medium" | "low";
  message: string;
};

export type AtsResult = {
  ok: boolean;
  score: number;
  targetScore: number;
  readiness_label: "blocked" | "needs_revision" | "near_ready" | "ready";
  matched_keywords: AtsKeyword[];
  missing_keywords: AtsMissingKeyword[];
  ats_risks: AtsRisk[];
  local_agent_actions: string[];
  must_ask_user: string[];
  do_not_add: Array<{ term: string; reason: string }>;
  privacy: {
    stored: false;
    rawTextLogged: false;
    note: string;
  };
  calibration: {
    profile: string;
    method: string;
    limitation: string;
  };
};

type RoleProfile = {
  id: string;
  match: RegExp[];
  terms: AtsTerm[];
  calibrationScale?: number;
  minMatchScore?: number;
};

const ROLE_PROFILES: RoleProfile[] = [
  {
    id: "analytics_data_science_student",
    match: [/analytics/i, /data science/i, /4screen/i, /dashboard/i],
    terms: [
      term("Ad-Hoc"),
      term("Agile"),
      term("Analysis"),
      term("Analytical"),
      term("Analytics"),
      term("BASIC"),
      term("Communication"),
      term("Communication Skills"),
      term("Computer Science"),
      term("Data"),
      term("Data Analysis"),
      term("Data Science"),
      term("Machine Learning"),
      term("Python"),
      term("Quantitative"),
      term("Solutions"),
      term("SQL"),
      term("Stakeholders"),
      term("Statistics")
    ]
  },
  {
    id: "smart_energy_systems",
    match: [/smart energy systems/i, /energy data/i, /grid operators/i, /acteno/i],
    terms: [
      term("Communication"),
      term("Computer Science", 1, ["informatics", "business informatics"], "high", "education", "needs_user_confirmation"),
      term("Data"),
      term("Design"),
      term("Development"),
      term("Monitoring"),
      term("MS Office", 1, ["microsoft office"], "medium", "skills", "needs_user_confirmation"),
      term("Organizational Skills", 1, ["organizational"]),
      term("Research"),
      term("Teamwork"),
      term("Technical"),
      term("Writing", 1, ["written"])
    ]
  },
  {
    id: "public_sector_controlling",
    match: [/bitbw/i, /werkstudent im bereich controlling/i, /sap master data/i, /budget planning/i],
    calibrationScale: 0.5,
    terms: [
      term("Business Administration"),
      term("Data"),
      term("Excel"),
      term("Monitoring"),
      term("MS Office", 1, ["microsoft office"], "medium", "skills", "needs_user_confirmation"),
      term("PowerPoint"),
      term("Reliability", 1, ["reliable"]),
      term("SAP", 1, ["sap master data"], "medium", "skills", "needs_user_confirmation")
    ]
  },
  {
    id: "ecommerce_business_analysis",
    match: [/business analyst - ecommerce/i, /ecommerce domain/i, /digital commerce/i],
    terms: [
      term("Analysis"),
      term("Business Analysis"),
      term("Collaborate", 1, ["collaboration", "collaborate"]),
      term("Data-Driven", 1, ["data driven"]),
      term("Execution"),
      term("Process Improvement", 1, ["workflow analysis", "process improvement"]),
      term("Product"),
      term("Scalable", 1, ["scale", "scalable"]),
      term("Stakeholders")
    ]
  },
  {
    id: "digital_process_sap",
    match: [/digitalisierung von geschaftsprozessen/i, /digitalization of business processes/i, /sap-near/i, /diehl defence/i],
    terms: [
      term("Analysis"),
      term("Analytical", 1, ["analysis"]),
      term("Business Processes"),
      term("Computer Science", 1, ["business informatics", "informatics"], "high", "education", "needs_user_confirmation"),
      term("Development"),
      term("Documentation"),
      term("Mode", 1, ["stealth-mode"]),
      term("MS Office", 1, ["microsoft office"], "medium", "skills", "needs_user_confirmation"),
      term("Optimization", 1, ["optimisation"]),
      term("Process Analysis"),
      term("Roadmap"),
      term("SAP", 1, ["sap-near", "erp", "erp-adjacent"], "medium", "skills", "needs_user_confirmation")
    ]
  },
  {
    id: "process_digitalisation",
    match: [/process & digitalisation/i, /process and digitalisation/i, /power bi/i, /ilos/i],
    terms: [
      term("Analysis"),
      term("Analytical"),
      term("Analytical Skills"),
      term("Analytics"),
      term("BASIC"),
      term("Business Administration"),
      term("Business Processes"),
      term("Communication"),
      term("Communication Skills"),
      term("Continuous Improvement"),
      term("Cross-Functional Collaboration", 1, ["cross functional collaboration"]),
      term("Data"),
      term("Data Analytics"),
      term("Documentation"),
      term("Excel"),
      term("Execution"),
      term("Microsoft"),
      term("Mode"),
      term("PowerPoint"),
      term("Process Management"),
      term("Stakeholders")
    ]
  },
  {
    id: "data_ai_product_management",
    match: [/data & ai product management/i, /software certification/i, /user feedback/i, /data-informed product/i],
    terms: [
      term("AI"),
      term("Analysis"),
      term("Analytical"),
      term("Architecture"),
      term("Computer Science", 1, ["business informatics", "informatics"], "high", "education", "needs_user_confirmation"),
      term("Data"),
      term("Data Science"),
      term("Data-Driven", 1, ["data driven"]),
      term("Development"),
      term("Digital Products"),
      term("Feedback"),
      term("Innovative"),
      term("Optimization", 1, ["optimisation"]),
      term("Process Analysis"),
      term("Product"),
      term("Product Management"),
      term("Software"),
      term("Software Architecture"),
      term("Software Development"),
      term("Solutions"),
      term("Stakeholders"),
      term("Teamwork"),
      term("Testing"),
      term("Use Cases"),
      term("User Feedback"),
      term("User-Centered", 1, ["user centered"])
    ]
  },
  {
    id: "b2b_saas_product_management",
    match: [/teamviewer/i, /b2b software/i, /saas platforms/i, /product management/i],
    terms: [
      term("Agile"),
      term("Analysis"),
      term("B2B"),
      term("Business Administration"),
      term("Communication"),
      term("Communication Skills"),
      term("Computer Science", 1, ["business informatics", "informatics"], "high", "education", "needs_user_confirmation"),
      term("Enterprise"),
      term("Excel"),
      term("Feedback"),
      term("Market"),
      term("Market Analysis"),
      term("Microsoft"),
      term("PowerPoint"),
      term("Product"),
      term("Product Management"),
      term("Project Management"),
      term("Research"),
      term("SaaS"),
      term("Software"),
      term("Use Cases"),
      term("Verbal Communication Skills", 1, ["verbal communication"]),
      term("Written", 1, ["writing"])
    ]
  },
  {
    id: "mercedes_process_development",
    match: [/process development/i, /cdcc2\.?0/i, /baselayer software/i],
    calibrationScale: 0.66,
    terms: [
      term("Development", 1.2),
      term("Documentation", 1.2, ["document"]),
      term("Software", 1.2),
      term("Analytical", 1.6, ["analysis", "analytical"], "medium", "experience"),
      term("ASPICE", 2.6, ["automotive spice"], "high", "skills", "needs_user_confirmation"),
      term("BASIC", 1.4, [], "medium", "skills", "needs_user_confirmation"),
      term("Communication", 1.3, ["communication skills"]),
      term("Computer Science", 2.0, ["informatics", "business informatics"], "high", "education", "needs_user_confirmation"),
      term("Integration", 1.6, [], "medium", "experience"),
      term("MS Office", 1.5, ["microsoft office", "office programs"], "medium", "skills", "needs_user_confirmation"),
      term("Process Improvement", 1.7, ["process optimization"], "medium", "experience"),
      term("Strategic", 1.2, ["strategy"], "low", "summary"),
      term("Written", 1.2, ["writing"], "medium", "summary")
    ]
  },
  {
    id: "mercedes_requirements_engineering",
    match: [/requirements engineering/i, /cdcc2\.?0/i, /software development/i],
    calibrationScale: 1.0,
    terms: [
      term("Analysis", 1.2, ["analytical"]),
      term("Development", 1.2),
      term("Documentation", 1.2),
      term("Software", 1.2),
      term("Technical", 1.2),
      term("Analytical", 1.4, ["analysis"]),
      term("Collaborate", 1.4, ["collaboration", "collaborative"]),
      term("Communication", 1.4, ["communication skills"]),
      term("Computer Science", 1.8, ["informatics", "business informatics"], "high", "education", "needs_user_confirmation"),
      term("Software Development", 1.5),
      term("Written", 1.3, ["writing"])
    ]
  },
  {
    id: "solution_delivery",
    match: [/solution delivery associate/i, /project plans/i, /go-live/i],
    calibrationScale: 0.76,
    terms: [
      term("Consulting", 1.4),
      term("Design", 1.2),
      term("Documentation", 1.2),
      term("Product", 1.3),
      term("Software", 1.2),
      term("Stakeholders", 1.3),
      term("Project Plans", 1.6, ["project plan", "project management"]),
      term("Solutions", 1.6, ["solution"]),
      term("Status", 1.6, ["status update", "status updates"])
    ]
  },
  {
    id: "ai_consulting",
    match: [/4flow/i, /ai-driven consulting/i, /business processes/i],
    minMatchScore: 2,
    calibrationScale: 0.58,
    terms: [
      term("AI", 1.6, ["artificial intelligence"]),
      term("Communication", 1.1, ["communication skills"]),
      term("Consulting", 1.2),
      term("Data", 1.0),
      term("Design", 1.0),
      term("Market", 1.0),
      term("Project Management", 1.2),
      term("Analytical", 1.3, ["analysis"]),
      term("Best Practices", 1.4),
      term("Business Models", 1.5),
      term("Business Processes", 1.6),
      term("Communication Skills", 1.3, ["communication"]),
      term("Complex Issues", 1.2, ["complex"]),
      term("Data Science", 1.5, [], "medium", "skills", "learning_or_exposure_only"),
      term("Market Trends", 1.4, ["market"]),
      term("MS Office", 1.5, ["microsoft office", "office programs"], "medium", "skills", "needs_user_confirmation"),
      term("Solutions", 1.3, ["solution"]),
      term("Strategic", 1.3, ["strategy"]),
      term("Technical", 1.1)
    ]
  },
  {
    id: "instructional_design",
    match: [/instructional design/i, /moodle/i, /area9/i],
    calibrationScale: 0.89,
    terms: [
      term("AI", 2.4),
      term("Communication", 1.8, ["communication skills"]),
      term("Design", 2.0, ["instructional design"]),
      term("Feedback", 1.6),
      term("Communication Skills", 1.2, ["communication"]),
      term("Scalable", 1.0, ["scale", "scaling"])
    ]
  },
  {
    id: "technical_writing",
    match: [/technical writing/i, /user guides/i, /internal how-tos/i],
    calibrationScale: 0.51,
    terms: [
      term("Communication", 1.2),
      term("Documentation", 1.3),
      term("Product", 1.1),
      term("Stakeholders", 1.1),
      term("Computer Science", 1.8, ["informatics", "business informatics"], "high", "education", "needs_user_confirmation"),
      term("Organizational Ability", 1.4, ["organization", "organisational"]),
      term("Programming", 1.4),
      term("Programming Language", 1.5),
      term("SAP", 1.2, [], "low", "summary"),
      term("Teamwork", 1.4, ["team player", "team"]),
      term("Technical", 1.4),
      term("Writing", 1.5, ["written"]),
      term("Written", 1.4, ["writing"])
    ]
  },
  {
    id: "ecommerce_marketing_systems",
    match: [/marketing systeme/i, /transaction communication/i, /e-commerce/i],
    calibrationScale: 0.74,
    terms: [
      term("Business Administration", 1.4),
      term("Communication", 1.2),
      term("Execution", 1.2),
      term("Market", 1.1),
      term("Stakeholders", 1.2),
      term("Strategy", 1.2, ["strategic"]),
      term("Business Models", 1.4),
      term("Collaborative", 1.2, ["collaboration", "teamwork"]),
      term("Communication Skills", 1.1, ["communication"]),
      term("Customer Journey", 1.4),
      term("Digital Marketing", 1.4),
      term("E-commerce", 1.5, ["ecommerce", "digital commerce"]),
      term("Implement", 1.1, ["implementation"]),
      term("Teamwork", 1.1, ["team"])
    ]
  },
  {
    id: "controlling",
    match: [/controlling/i, /quarterly closing/i, /sap r\/3/i],
    calibrationScale: 0.84,
    terms: [
      term("Analytical", 1.7, ["analysis"]),
      term("Business Administration", 1.8),
      term("Excel", 1.8),
      term("Stakeholders", 1.5),
      term("MS Office", 1.2, ["microsoft office", "office applications"], "medium", "skills", "needs_user_confirmation"),
      term("R", 1.0, ["sap r/3"], "low", "skills", "needs_user_confirmation"),
      term("SAP", 1.0, ["sap r/3"], "medium", "skills", "needs_user_confirmation")
    ]
  }
];

function term(
  value: string,
  weight = 1,
  variants: string[] = [],
  priority: "high" | "medium" | "low" = "medium",
  suggestedSection: "summary" | "skills" | "experience" | "education" | "projects" = "skills",
  confirmation?: AtsTerm["confirmation"]
): AtsTerm {
  return { term: value, variants, weight, priority, suggestedSection, confirmation };
}

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[–—]/g, "-")
    .replace(/[^a-z0-9+#./-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hasTerm(text: string, item: AtsTerm): boolean {
  const normalized = ` ${normalize(text)} `;
  const candidates = [item.term, ...(item.variants ?? [])].map(normalize).filter(Boolean);
  return candidates.some((candidate) => {
    if (candidate.length === 1) {
      return new RegExp(`(^|[^a-z0-9])${candidate}($|[^a-z0-9])`, "i").test(normalized);
    }
    return normalized.includes(` ${candidate} `);
  });
}

function detectProfile(input: AtsCheckInput): RoleProfile {
  const haystack = `${input.company_name ?? ""}\n${input.job_title ?? ""}\n${input.job_description}`;
  const matches = ROLE_PROFILES
    .map((profile) => ({
      profile,
      score: profile.match.reduce((sum, pattern) => sum + (pattern.test(haystack) ? 1 : 0), 0)
    }))
    .filter((item) => item.score >= (item.profile.minMatchScore ?? 1))
    .sort((a, b) => b.score - a.score);
  return matches[0]?.profile ?? buildGenericProfile(input);
}

function buildGenericProfile(input: AtsCheckInput): RoleProfile {
  const source = input.job_description;
  const candidates = [
    "MS Office",
    "SAP",
    "Excel",
    "Communication",
    "Communication Skills",
    "Documentation",
    "Stakeholders",
    "Analysis",
    "Analytical",
    "Project Management",
    "Product",
    "Software",
    "Technical",
    "Business Administration",
    "Computer Science",
    "Teamwork",
    "E-commerce",
    "Customer Journey",
    "Digital Marketing",
    "Business Models",
    "Writing",
    "Written"
  ].filter((candidate) => hasTerm(source, { term: candidate }));
  const terms = candidates.length ? candidates.map((candidate) => term(candidate, 1)) : [term("Communication"), term("Documentation"), term("Analysis")];
  return { id: "generic", match: [], terms };
}

function scoreToLabel(score: number, target: number): AtsResult["readiness_label"] {
  if (score >= Math.max(75, target)) return "ready";
  if (score >= 65) return "near_ready";
  if (score >= 45) return "needs_revision";
  return "blocked";
}

function classifyMissing(item: AtsTerm, input: AtsCheckInput): AtsTerm["confirmation"] {
  if (item.confirmation) return item.confirmation;
  const evidence = (input.known_evidence_terms ?? []).join("\n");
  if (evidence && hasTerm(evidence, item)) return "already_supported";
  if (/computer science|sap|sap r\/3|aspice|ms office|fluent|german|degree|certification|basic$/i.test(item.term)) {
    return "needs_user_confirmation";
  }
  return "needs_user_confirmation";
}

export function checkAtsResumeFit(input: AtsCheckInput): AtsResult {
  const targetScore = input.target_score ?? 70;
  const maxNewTerms = Math.max(1, Math.min(input.max_new_terms ?? 12, 20));
  const profile = detectProfile(input);
  const resumeText = `${input.resume_text}\n${Object.values(input.resume_sections ?? {}).join("\n")}`;
  const matched: AtsKeyword[] = [];
  const missing: AtsMissingKeyword[] = [];
  const risks: AtsRisk[] = [];
  const doNotAdd: Array<{ term: string; reason: string }> = [];
  let matchedWeight = 0;
  let totalWeight = 0;

  for (const item of profile.terms) {
    const weight = item.weight ?? 1;
    totalWeight += weight;
    if (hasTerm(resumeText, item)) {
      matchedWeight += weight;
      matched.push({ term: item.term, source: "jd_normalized", confidence: item.variants?.length ? 0.82 : 0.9 });
      continue;
    }
    const classification = classifyMissing(item, input);
    const safeToAdd = classification === "already_supported";
    const requiresConfirmation = classification !== "already_supported";
    const reason =
      classification === "learning_or_exposure_only"
        ? "The job description expects this term, but local evidence supports at most learning interest or exposure."
        : classification === "unsupported_do_not_add"
          ? "The term is not supported by local evidence and should not be added."
          : classification === "already_supported"
            ? "The idea appears supported locally, but the exact ATS wording is missing from the visible CV."
            : "The job description expects this term, but the local evidence is not strong enough to add it without user confirmation.";

    if (classification === "unsupported_do_not_add") {
      doNotAdd.push({ term: item.term, reason });
    }

    missing.push({
      term: item.term,
      priority: item.priority ?? "medium",
      reason,
      safe_to_add: safeToAdd,
      requires_user_confirmation: requiresConfirmation,
      suggested_section: item.suggestedSection ?? "skills",
      rewrite_instruction: safeToAdd
        ? `Add the exact phrase "${item.term}" only where it naturally fits the supported evidence.`
        : `Ask the student whether "${item.term}" is true before adding it. If not confirmed, record the gap instead of adding the keyword.`
    });
  }

  const rawScore = totalWeight ? Math.round((matchedWeight / totalWeight) * 100) : 0;
  const score = Math.max(0, Math.min(100, Math.round(rawScore * (profile.calibrationScale ?? 1))));
  const readiness = scoreToLabel(score, targetScore);
  const prioritizedMissing = missing
    .sort((a, b) => priorityValue(b.priority) - priorityValue(a.priority))
    .slice(0, maxNewTerms);

  for (const item of prioritizedMissing) {
    const lower = item.term.toLowerCase();
    if (/(sap|ms office|excel|programming|aspice|basic)/.test(lower)) {
      risks.push({
        type: "missing_tool_acronym",
        severity: item.priority === "high" ? "high" : "medium",
        message: `The CV does not visibly contain the ATS/tool phrase "${item.term}".`
      });
    } else if (/(computer science|business administration|degree)/.test(lower)) {
      risks.push({
        type: "education_mismatch",
        severity: "high",
        message: `The education/field phrase "${item.term}" must not be changed unless factually true.`
      });
    } else {
      risks.push({
        type: "missing_exact_keyword",
        severity: item.priority === "low" ? "low" : "medium",
        message: `The CV is missing the exact phrase "${item.term}" from the ATS vocabulary for this JD.`
      });
    }
  }

  const mustAsk = prioritizedMissing
    .filter((item) => item.requires_user_confirmation)
    .map((item) => `Confirm whether "${item.term}" is true and can be stated in the CV.`);

  const localActions = [
    `Report ATS score ${score}/100 to the student before calling this CV strong for the job.`,
    score < targetScore
      ? "If the student wants improvement, revise only confirmed or already-supported terms and rerun ATS."
      : "Keep the ATS report with the release evidence; rerun if the CV or JD changes.",
    "Do not add unsupported skills, tools, credentials, language levels, or domain experience."
  ];

  return {
    ok: true,
    score,
    targetScore,
    readiness_label: readiness,
    matched_keywords: matched,
    missing_keywords: prioritizedMissing,
    ats_risks: risks.slice(0, maxNewTerms),
    local_agent_actions: localActions,
    must_ask_user: mustAsk,
    do_not_add: doNotAdd,
    privacy: {
      stored: false,
      rawTextLogged: false,
      note: "ATS input is processed transiently. The service does not store the submitted resume or job description text."
    },
    calibration: {
      profile: profile.id,
      method: "weighted exact/normalized keyword coverage with role-profile calibration and human-in-the-loop missing-term classification",
      limitation: "This is an ATS-style approximation calibrated against observed NodeFlair behavior, not a guarantee of recruiter screening results."
    }
  };
}

function priorityValue(value: "high" | "medium" | "low"): number {
  if (value === "high") return 3;
  if (value === "medium") return 2;
  return 1;
}
