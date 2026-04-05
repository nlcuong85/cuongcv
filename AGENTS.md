# AGENTS.md

This file is the operating contract for AI agents working in `/Users/pmlecuong/Documents/CuongProjects/CuongCV`.

Follow it before making edits, generating applications, replying to emails, or deploying the CV site.

## Mission

This repository serves two related purposes:

1. The public CV website for **Le Cuong Nguyen**
2. The local application-generation system for role-specific CVs, cover letters, and PDFs

Agents should preserve factual consistency across both layers.

## Fast path

Read only the minimum set that matches the task.

### For public CV site work

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/src/data/resume-data.tsx`

Load other files only if the task expands into layout, deployment, or generator-sync work.

Escalate to deeper reading when:
- the change affects identity-level facts
- the change might also require generator/profile synchronization
- visible layout, print behavior, or deployment is involved

### For application work

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md`
3. the specific intake file or generator source relevant to the task

Do not load public-site component files unless the request actually touches the public CV layer.

Escalate to deeper reading when:
- the task changes generator logic, templates, or tone policy
- the user asks for stronger authenticity or says the application still feels templated
- the output is high-stakes and recruiter-facing
- page-limit, snapshot, or validation issues appear

### For work writing / internal documentation

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/.codex/skills/blog-writer/SKILL.md`
3. `/Users/pmlecuong/.codex/skills/blog-writer/references/writing-mode-framework.md`
4. `/Users/pmlecuong/.codex/skills/blog-writer/references/work-mode-guidance.md`

Do not route this through the application system unless the user explicitly wants application materials.

Escalate to deeper reading when:
- the writing will be reused as a standard or template
- the note affects team decisions, stakeholder commitments, or execution timing
- the user asks for a more personal tone without losing work clarity

### For recruiter or interview emails

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md` only if an intake/output folder already exists for that company
3. the relevant intake/output files if they exist

Keep the read set narrow and avoid loading the full generator stack when the user only needs a reply.

Escalate to deeper reading when:
- the email refers to prior application materials or interview context
- the user asks to match an existing company-specific tone closely
- the email has negotiation, risk, or mismatch implications

## First Actions

When you enter this repository:

1. Read this `AGENTS.md`
2. Read `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md` if the task involves applications
3. Check `git status --short`
4. Identify whether the request is about:
   - public CV site edits
   - generated application artifacts
   - interview or recruiter email drafting
   - work writing / internal documentation
   - deployment / GitHub Pages / PM2 / Docker
   - job-search research

Do not assume the user wants public CV edits when they are asking for company-specific application documents.

## Skills To Load

Use these skills deliberately:

- Use [`job-search-cuong`](/Users/pmlecuong/.codex/skills/job-search-cuong/SKILL.md) for:
  - CV edits
  - application packages
  - cover letters
  - job-search updates
  - GitHub Pages verification for the CV site
- Use [`builder-ops`](/Users/pmlecuong/.codex/skills/builder-ops/SKILL.md) for:
  - repo shipping
  - Git/GitHub work
  - environment checks
  - deployment diagnosis
- Use [`playwright`](/Users/pmlecuong/.codex/skills/playwright/SKILL.md) for:
  - browser validation after visible CV changes
  - print/layout validation
  - live-site verification
- Use [`Blog Writer`](/Users/pmlecuong/.codex/skills/blog-writer/SKILL.md) for:
  - internal work writing
  - user stories
  - requirement clarifications
  - meeting recaps
  - Slack / Teams summaries
  - writing-mode decisions for blog vs work vs application tone

If the task is only drafting a recruiter/interview reply email, you do not need to run the full application workflow. Read the relevant intake and output files first, then draft the reply in the same tone and context.

## Canonical Identity Rules

Use these facts consistently unless the user explicitly updates them:

- Legal / paperwork name: `Le Cuong Nguyen`
- Email: use the current value from `src/data/resume-data.tsx`
- CV site canonical fact file: `src/data/resume-data.tsx`
- Application generator canonical fact file: `application-system/data/master_profile.json`

If the name changes in one canonical source, update the other canonical source too.

Do not silently leave the public CV and generator profile out of sync.

## Source Of Truth

### Public CV layer

- `src/data/resume-data.tsx` is the source of truth for the public CV site
- Prefer data-only edits here
- Only edit components when layout or rendering actually needs to change

### Application layer

- `application-system/data/master_profile.json` is the source of truth for generator profile facts
- `application-system/data/evidence_library.json` stores reusable proof blocks
- `application-system/data/role_profiles.json` stores role presets
- `application-system/data/summary_versions.json` stores reusable summary styles
- `application-system/data/job_taxonomy.json` stores shared JD/search vocabulary
- `application-system/intakes/*.json` stores per-job inputs
- `application-system/scripts/generate_application.py` is the canonical generator
- `application-system/AGENTS.md` is the application-layer operating contract

### Generated outputs

- Output folder: `application-system/outputs/<company-and-job-slug>/`
- Generated CV JSON for printing: `public/generated-cv-data/<company-and-job-slug>/<role>.json`

Generated artifacts are outputs, not the primary source of truth. Edit inputs, then regenerate.

## Request Routing

When the user gives a command, classify it first.

### 1. Public CV edit

Examples:

- “update my CV site”
- “change this project wording”
- “fix the live CV”
- “change my name on the site”

Handle it by:

1. Editing `src/data/resume-data.tsx` first
2. Updating related generator source files if the fact is identity-level
3. Running validation
4. Verifying layout and print output
5. Deploying only if the user wants shipping / live update

### 2. Job-specific application package

Examples:

- “write a cover letter”
- “tailor my CV to this JD”
- “make an application for Mercedes”
- “generate one CV variant”

Handle it by:

1. Creating or updating an intake JSON under `application-system/intakes/`
2. Keeping fixed facts aligned with the public CV
3. Running the generator
4. Running the rule checker
5. Checking PDF page limits
6. Returning the exact artifact paths

### 3. Interview / recruiter email drafting

Examples:

- “draft a thank-you email”
- “reply to this interview invite”
- “answer this recruiter message”

Handle it by:

1. Read the relevant intake JSON and existing application output folder if they exist
2. Match the tone to prior application materials
3. Keep the email concise, natural, and recruiter-safe
4. Prefer clean business English unless the user asks for German
5. Do not overcomplicate the reply with application-system regeneration unless the user asks for document changes

### 4. Deployment / GitHub Pages / environment

Examples:

- “deploy this live”
- “push to GitHub”
- “check the live site”
- “fix the deployment”

Handle it by:

1. Use `builder-ops` patterns
2. Validate locally first
3. Use non-interactive git commands
4. Verify the live site after shipping

### 5. Job search / market research

Handle it with `job-search-cuong` and prefer official job pages.

### 6. Work writing / internal documentation

Examples:

- “write this user story”
- “summarize this meeting”
- “turn this into a Slack update”
- “write a requirement clarification note”
- “draft an internal follow-up message”

Handle it by:

1. Use `Blog Writer`
2. Explicitly switch it into `work mode`
3. Optimize for scanning, alignment, decisions, blockers, and next steps
4. Do not route internal work writing through the application workflow unless the user is explicitly asking for application materials

### 7. Franklee / OpenClaw recovery snapshot

Examples:

- “refresh the Franklee snapshot”
- “back up the OpenClaw server state”
- “update the recovery repo”
- “run the SOP and save the Franklee backup”

Handle it by:

1. Use the repo-backed refresh script:
   - `/Users/pmlecuong/Documents/CuongProjects/OpenClaw-franklee/scripts/sync_franklee_snapshot.py`
2. Treat `/Users/pmlecuong/Documents/CuongProjects/OpenClaw-franklee` as the recovery record repo
3. Keep the snapshot sanitized and non-secret
4. If the task is an SSD SOP execution, prefer the `sop-runner` hook path so the SOP and the Franklee backup stay coupled
5. Update recovery docs when the live Franklee contract changes

## Application Workflow Contract

Use the application workflow when the user asks for:

- cover-letter generation
- company-specific application packages
- CV tailoring from a JD
- multiple CV variants for one role

### Required files

- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/scripts/generate_application.py`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/master_profile.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/evidence_library.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/role_profiles.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/summary_versions.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/job_taxonomy.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic_writing_profile.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic-writing-samples-2012-2018.md`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic-writing-samples-annotated.md`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/writing-mode-framework.md`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/portfolio_digest.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/intakes/`
- `/Users/pmlecuong/.codex/skills/job-search-cuong/scripts/check_application_rules.py`

### Non-negotiable rules

- Do not invent experience
- Keep generated documents aligned with the public CV facts
- Fixed facts that must stay aligned:
  - name
  - contact information
  - address
  - education entries, grades, and locations
  - awards and certifications
  - employer names
  - work start and end dates
  - side-project titles and core descriptions
- Allowed variation by role:
  - `about`
  - summary wording
  - skill ordering and emphasis
  - work bullet selection / emphasis
  - evidence selection for the cover letter

### Skills rule for generated CVs

Target 14 visible skills:

- 7 fixed core skills
- 7 adaptive skills chosen from the role focus and JD

Keep the public CV skills unchanged unless the user explicitly asks to edit the public CV.

### Contact lookup rule

- Look for a named recruiter or contact first
- Use a named contact when verified
- Use `Hiring Team` only when no named contact can be verified

### German-language mismatch rule

If any of the following are true:

- the job posting is written mainly in German
- the requirements explicitly ask for strong / fluent / business German
- the recruiter or JD clearly signals that German is important for the role

and the user has not given a newer fact showing that this requirement is now met, then the cover letter should acknowledge this briefly in the final paragraph.

Use this pattern:

- state that German is still being improved and is not yet at the required professional level
- state strong English ability when relevant
- keep the note brief and honest
- add a polite sentence asking to be considered or referred for another suitable role that better matches the current English-first level if this role is not the right fit

Do not make this the center of the letter. Keep it concise and place it in the closing paragraph so the main body still focuses on fit and evidence.

### Summary version rule

- Default summary: `strongest_balanced`
- If the JD clearly points to a different summary style, set `summary_version`
- If a non-default summary is strongly indicated and ambiguous, ask the user instead of guessing

### Output rule

Default deliverable for one live job URL:

1. one intake JSON
2. one cover letter
3. one CV variant
4. one role-fit snapshot supplement
5. PDFs when possible
6. a short report with contact status, page-limit result, and major risks

### PDF naming rule

- `resume + candidate-name + job-title + timestamp`
- `cover-letter + candidate-name + job-title + timestamp`

### Role-fit snapshot rule

- treat it as a separate one-page supplement, not part of the cover letter or main CV
- keep the four assessment dimensions fixed:
  - `Requirements & Analysis`
  - `Process & Workflow Design`
  - `Delivery & Stakeholder Coordination`
  - `AI Workflow & Automation`
- keep the scores, notes, keywords, tools, domains, and growth areas dynamic per JD
- use only verified skills from the profile; do not promote JD-only tools into claimed experience

### Current role-family set

The application system currently supports 10 role families:

1. `product_manager`
2. `product_owner`
3. `business_analyst`
4. `requirements_process`
5. `process_automation`
6. `pmo_delivery_support`
7. `quality_compliance_ops`
8. `ai_product_ops`
9. `implementation_enablement`
10. `workflow_operations_analyst`

Never delete earlier timestamped PDFs just because a newer one exists.

## Validation And Acceptance

### For public CV changes

Run the relevant checks:

- `pnpm check`
- browser / print validation when visible content changed

Minimum acceptance:

- no broken layout
- no broken links
- A4-friendly print
- CV stays within 2 pages

### For generated applications

Run:

```bash
python3 application-system/scripts/generate_application.py --intake <path> --compile-pdf
python3 /Users/pmlecuong/.codex/skills/job-search-cuong/scripts/check_application_rules.py --resume-data /Users/pmlecuong/Documents/CuongProjects/CuongCV/src/data/resume-data.tsx --summary-versions /Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/summary_versions.json --intake <path>
```

Add `--cover-letter <cover-letter-tex-path>` when validating the generated letter source directly.

Acceptance:

- cover letter must be 1 page
- CV must be 2 pages or fewer
- if output overflows, shorten content first; do not hide the problem with unreadable layout

## Tone And Writing Rules

### Public CV and generated application documents

- Keep wording recruiter-safe
- Be clear, specific, and structured
- Avoid weak wording such as:
  - `currently testing three private apps`
  - `comfortable driving`
  - `Ai-enable Apps`
- Keep RouteOps described as:
  - React + TypeScript travel-planning decision support
  - local Fastify backend
  - deterministic best-balance / cheapest / most-comfort outputs
  - saved trip history

### Email drafting

When drafting replies to recruiters, hiring managers, or interviewers:

- keep the reply concise
- prefer natural, calm, professional English
- match the user’s tone request when specified
- default to a German-corporate style when the user asks for “shorter” or “more German-style”
- avoid exaggerated enthusiasm
- do not sound overly templated

Common email intents:

- thank-you after a call
- confirmation of interview availability
- confirmation of in-person attendance
- short follow-up after application submission

## Project Structure

- `/src/app/` - Next.js App Router pages and layouts
- `/src/components/` - reusable UI components
- `/src/data/resume-data.tsx` - public CV data
- `/src/apollo/` - GraphQL server setup
- `/src/images/logos/` - logo components
- `/application-system/` - application generator, templates, intakes, outputs

## Commands

### Development

```bash
pnpm dev
pnpm build
pnpm start
pnpm export
pnpm deploy
pnpm lint
pnpm lint:fix
pnpm format
pnpm format:fix
pnpm check
pnpm check:fix
```

### Docker

```bash
docker compose build
docker compose up -d
docker compose down
```

### PM2

```bash
./scripts/pm2-start.sh
pnpm install --frozen-lockfile
pnpm build
pm2 start ecosystem.config.js
pm2 save
pm2 status
pm2 logs cv-app
pm2 restart cv-app
pm2 stop cv-app
pm2 delete cv-app
```

PM2 facts:

- production port: `3125`
- cluster mode: `1` instance by default
- logs: `./logs/`

## Git And Safety Rules

- The worktree may be dirty
- Never revert unrelated user changes
- Prefer non-interactive git commands
- Do not claim deployment success until the live site reflects the intended change
- When modifying identity-level facts, check whether both public CV and generator profile need updating

## Delivery Format

When finishing work, report only the relevant items:

### For CV site work

- files changed
- checks run
- deployment result if shipped
- live URL checked if applicable

### For application packages

- intake file used
- output directory
- whether PDFs were compiled
- page-count result
- evidence used
- summary version used
- whether the rule checker passed

### For interview/recruiter emails

- provide the final reply text
- keep it ready to paste
- offer one tighter or warmer variant only if useful
