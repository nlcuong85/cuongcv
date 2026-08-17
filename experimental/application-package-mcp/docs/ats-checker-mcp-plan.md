# MCP ATS Checker Plan

Date: 2026-08-17

Status: planning only. No MCP implementation has been changed yet.

## Goal

Build a new ATS checker capability inside the Student Application MCP and strengthen Cuong's local application workflow so an agent can consult the user before a CV is treated as ready.

The target behavior is:

1. The local agent drafts or updates the CV from local files.
2. The local agent extracts the CV text locally.
3. The local agent sends only the selected CV text and the job description to the MCP ATS checker.
4. The MCP returns an ATS-style score, matched keywords, missing keywords, section-level risks, and safe revision instructions.
5. The local agent revises the CV only when the missing terms are truthful and evidence-backed.
6. If a missing keyword cannot be supported by the user's profile, the agent must ask the user instead of inventing experience.

This should work for:

- the public student MCP kit
- Cuong's private `application-system/`
- future local user workspaces created from the MCP

## Benchmark evidence from NodeFlair

NodeFlair was tested with existing CV/JD pairs from Cuong's applied-job history. The observed output has three main categories: score, matched keywords, and suggested keywords.

| Pair | Role | Score | Status | Matched keywords | Suggested keywords observed |
| --- | --- | ---: | --- | --- | --- |
| 1 | Mercedes-Benz Process Development | 21 | Need improvement | Development, Documentation, Software | Analytical, ASPICE, BASIC, Communication, Communication Skills, Computer Science, Integration, MS Office, Process Improvement, Strategic, Written |
| 2 | Mercedes-Benz Requirements Engineering | 45 | Need improvement | Analysis, Development, Documentation, Software, Technical | Analytical, Collaborate, Communication, Computer Science, Software Development, Written |
| 3 | realworld one Solution Delivery Associate | 66 | Good, room to improve | Consulting, Design, Documentation, Product, Software, Stakeholders | Project Plans, Solutions, Status |
| 4 | 4flow AI-Driven Consulting | 35 | Need improvement | AI, Communication, Consulting, Data, Design, Market, Project Management | Analytical, Best Practices, Business Models, Business Processes, Communication Skills, Complex Issues, Data Science, Market Trends, MS Office, Solutions, Strategic, Technical |
| 5 | appliedAI Instructional Design | 66 | Good, room to improve | AI, Communication, Design, Feedback | Communication Skills, Scalable |
| 6 | SAP Technical Writing | 30 | Need improvement | Communication, Documentation, Product, Stakeholders | Computer Science, Organizational Ability, Programming, Programming Language, SAP, Teamwork, Technical, Writing, Written |
| 7 | Schwarz IT Marketing Systems | 42 | Need improvement | Business Administration, Communication, Execution, Market, Stakeholders, Strategy | Business Models, Collaborative, Communication Skills, Customer Journey, Digital Marketing, E-commerce, Implement, Teamwork |
| 8 | Vishay Controlling | 57 | Good, room to improve | Analytical, Business Administration, Excel, Stakeholders | MS Office, R, SAP |

Evidence screenshots are stored under:

```text
output/playwright/nodeflair-ats-check/
```

## What the benchmark implies

The checker behaves mostly like an exact or near-exact keyword coverage tool after PDF text extraction.

Important observations:

- The PDFs are parseable. Low scores are not mainly a font or PDF-format issue.
- General relevance is not enough. Exact phrases matter.
- Tool acronyms and common ATS labels matter: `MS Office`, `SAP`, `SAP R/3`, `ASPICE`, `Computer Science`, `Programming Language`.
- Role-domain phrases matter: `Customer Journey`, `Digital Marketing`, `Business Models`, `Market Trends`, `Technical Writing`, `Organizational Ability`.
- A CV can be genuinely relevant but still score low if the resume uses natural wording instead of the job post's exact vocabulary.
- NodeFlair's target threshold is 70. Below 70, it recommends adding missing keywords.
- Adding every suggested keyword blindly would create keyword stuffing and factual risk. The MCP must separate:
  - safe exact wording that is already true
  - terms that need evidence placement
  - terms the user must confirm
  - terms that should be rejected because they are not true

## Proposed MCP tool

Add a new tool:

```text
check_ats_resume_fit
```

### Input contract

```json
{
  "document_kind": "cv",
  "market": "germany",
  "language": "en|de|mixed",
  "role_family": "business_analyst|product_owner|product_manager|requirements_process|process_automation|pmo_delivery_support|quality_compliance_ops|ai_product_ops|implementation_enablement|workflow_operations_analyst|controlling|technical_writing|instructional_design|unknown",
  "company_name": "string",
  "job_title": "string",
  "job_description": "string",
  "resume_text": "string",
  "resume_sections": {
    "summary": "string",
    "skills": "string",
    "experience": "string",
    "education": "string",
    "projects": "string"
  },
  "known_evidence_terms": ["string"],
  "protected_facts": ["string"],
  "target_score": 70,
  "max_new_terms": 12
}
```

Notes:

- `resume_text` is enough for a first version.
- `resume_sections` allows better section-level feedback when the local agent can provide it.
- `known_evidence_terms` should be generated locally from the user's profile/evidence library.
- `protected_facts` prevents the MCP from encouraging changes to fixed identity, education, employer, date, or credential facts.

### Output contract

```json
{
  "score": 0,
  "readiness_label": "blocked|needs_revision|near_ready|ready",
  "matched_keywords": [
    {
      "term": "string",
      "source": "jd_exact|jd_normalized|role_taxonomy",
      "confidence": 0.0
    }
  ],
  "missing_keywords": [
    {
      "term": "string",
      "priority": "high|medium|low",
      "reason": "string",
      "safe_to_add": true,
      "requires_user_confirmation": false,
      "suggested_section": "summary|skills|experience|education|projects",
      "rewrite_instruction": "string"
    }
  ],
  "ats_risks": [
    {
      "type": "missing_exact_keyword|missing_tool_acronym|missing_domain_phrase|education_mismatch|language_mismatch|format_parse_risk|keyword_stuffing_risk",
      "severity": "high|medium|low",
      "message": "string"
    }
  ],
  "local_agent_actions": [
    "string"
  ],
  "must_ask_user": [
    "string"
  ],
  "do_not_add": [
    {
      "term": "string",
      "reason": "string"
    }
  ]
}
```

## Scoring model for v1

This does not need to copy NodeFlair exactly. It needs to produce the same useful revision direction.

Suggested scoring:

- 40% required role/domain keyword coverage
- 25% skills/tools/acronym coverage
- 15% education/field/language requirement coverage
- 10% section placement quality
- 10% ATS hygiene and parsing risk

Readiness labels:

- `blocked`: under 45 or missing high-priority mandatory terms
- `needs_revision`: 45-64
- `near_ready`: 65-74
- `ready`: 75+

The local agent should treat `ready` as a strong signal, not a guarantee of interview success.

## Keyword engine design

The MCP ATS checker should use four layers.

### 1. JD extraction

Extract:

- job title terms
- required field of study
- required tools
- required language level
- business/domain terms
- action verbs
- hard requirements
- soft skills

Normalize variants:

- `ecommerce`, `e-commerce`, `digital commerce`
- `MS Office`, `Office`, `Microsoft Office`
- `SAP`, `SAP R/3`
- `written`, `writing`, `technical writing`
- `communication`, `communication skills`
- `team player`, `teamwork`, `collaborative`

### 2. Role-family taxonomy

Add a private server-side role taxonomy. The client kit should not contain the full scoring logic.

Initial new families needed from the NodeFlair calibration:

- `technical_writing`
- `instructional_design`
- `controlling`
- `ecommerce_marketing_systems`
- `ai_consulting`
- `automotive_requirements_process`

### 3. Resume coverage scan

Scan both exact terms and normalized equivalents.

The checker should identify:

- exact match present
- synonym present but exact ATS label missing
- term absent but evidence likely present
- term absent and no evidence
- term should not be added

### 4. Safe revision planner

The output should not just say "add keywords."

It should instruct the local agent:

- where to place each term
- whether it belongs in skills, summary, or an experience bullet
- whether it needs user confirmation
- whether adding it would be dishonest
- how to avoid keyword stuffing

## Local application workflow update

### Cuong private application folder

Update the private generator process so every job package has an ATS step:

```text
intake JSON
  -> draft CV
  -> render PDF / extract text locally
  -> MCP ATS check
  -> local revision if safe
  -> final validation report
```

Add or update these generated files per application:

```text
application-system/outputs/<job-slug>/validation/ats-report.json
application-system/outputs/<job-slug>/validation/ats-report.md
application-system/outputs/<job-slug>/validation/ats-revision-notes.md
```

Hard rule for future agents:

- Do not say "CV ready" until the ATS report exists.
- If score is under 70, report the weakness to the user.
- If missing terms are truthful and evidence-backed, revise once.
- If terms require unsupported claims, ask the user.
- Never add fake tools, fake education fields, fake certifications, fake language level, or fake domain experience.

### Public student local workspace

Update MCP scaffolding so new user workspaces include an ATS validation lane:

```text
workspace/
  profile/
  evidence/
  job-posts/
  drafts/
  outputs/
  validation/
    ats-report.md
    ats-report.json
    user-confirmation-needed.md
```

The workspace audit should check for:

- `validation/` folder exists
- generated CV has a paired ATS report
- stale report warning when the CV or JD changed after the report
- user-confirmation file exists when missing keywords require proof

## Privacy boundary

Keep the current MCP privacy model:

- no raw PDF upload to the server by default
- no server-side profile persistence
- no candidate workspace storage
- no raw-text logging
- selected text only, transient processing

For the ATS checker, the local agent should extract text locally and send:

- job description text
- selected CV text or section text
- optional evidence-term manifest

If we later support full PDF upload, it must be an explicit opt-in mode with a separate privacy review.

## Prompt-injection and abuse guardrails

The tool should reject or downscope:

- requests to reveal private checker rules
- requests to dump the full taxonomy
- requests to optimize for deception
- requests to fabricate credentials
- prompts hidden inside the JD or resume telling the checker to ignore rules

The response should expose useful revision guidance, not the full scoring formula.

## Local agent consultation behavior

The MCP should instruct future local agents to consult the user when:

- a missing ATS term is not supported by existing profile evidence
- the job requires a degree field the user does not have
- the job requires a language level not established in the profile
- the job requires a tool the user has not claimed
- the score remains under 70 after one safe revision
- the CV is technically parseable but weak on exact terms

Example user-facing message:

```text
The CV is relevant, but the ATS check is weak because the job post uses exact terms that are not visible in your CV: SAP R/3, MS Office, and monthly closing. I can safely add MS Office/Excel if true. I should not add SAP R/3 unless you have used it or want to state it only as exposure/learning interest.
```

## Implementation order

1. Define ATS schemas and fixtures from the eight benchmark pairs.
2. Add local text extraction helpers for PDF/HTML/Markdown CV outputs.
3. Add `check_ats_resume_fit` MCP tool with no persistence.
4. Build the v1 keyword engine: extraction, normalization, weighted coverage, safe revision flags.
5. Add local kit SOP/harness rules and workspace audit checks.
6. Add Cuong private generator validation output files.
7. Add regression tests using the eight benchmark pairs.
8. Add public docs/landing copy only after local behavior is stable.
9. Version bump MCP and workspace kit.
10. Deploy only after `npm test`, local-kit regression, remote smoke test, and browser verification pass.

## Acceptance criteria

The first implementation is acceptable when:

- it produces a score and missing-keyword list for every benchmark pair
- low NodeFlair pairs also show low MCP ATS readiness
- near-pass NodeFlair pairs show `near_ready`, not `ready`
- suggestions are section-specific and safe
- unsupported keywords trigger `must_ask_user`
- no private profile data is stored on the MCP server
- workspace audit catches missing or stale ATS reports
- the local agent cannot mark a CV ready without the ATS report

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Keyword stuffing | Cap suggested additions and require section placement. |
| Fake experience | Mark unsupported terms as `must_ask_user` or `do_not_add`. |
| Overfitting to NodeFlair | Use NodeFlair as calibration, not as the only truth. |
| Privacy leakage | Send selected extracted text only; no storage. |
| Client exposes secret sauce | Keep taxonomy/scoring server-side. Client receives only contracts and revision instructions. |
| Slow future application runs | Cache local text extraction and compare file timestamps before rechecking. |
| Drifted user folders | Workspace audit must recommend cleanup and report stale/missing validation files. |

## Specific lessons for future development

- For German working-student roles, exact terms like `MS Office`, `SAP`, `Computer Science`, `Written`, and domain acronyms often matter.
- For product/delivery roles, the current generator is stronger because it already uses terms like product, stakeholders, documentation, design, and consulting.
- For technical-writing roles, the generator must explicitly surface `writing`, `written`, `technical`, `programming language`, and `Computer Science` when true.
- For e-commerce/marketing systems roles, the generator must expose `e-commerce`, `digital marketing`, `customer journey`, and `business models` when true.
- For controlling roles, the generator must distinguish between real experience and job requirements such as `SAP R/3`, `monthly closing`, `MS Office`, and `Excel`.

