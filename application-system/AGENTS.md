# AGENTS.md

This file is the operating contract for AI agents working inside `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system`.

Use it instead of a README when the task is about:

- cover-letter generation
- tailored CV generation
- intake creation from a job URL or job description
- role-family selection
- role-fit snapshot / self-assessment generation
- PDF compilation or application-package validation

## Mission

This folder is the structured application layer for **Le Cuong Nguyen**.

The generator must produce recruiter-safe, German-market-friendly application artifacts while preserving fixed facts from the public CV layer in:

- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/src/data/resume-data.tsx`

This system always writes in `application mode` from:

- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/writing-mode-framework.md`

It may borrow sincerity, lived context, and contribution-oriented confidence from Cuong's authentic voice, but it must not drift into blog mode, work mode, or academic mode.

## Fast path

For most application tasks, do not load the whole folder.

### For generating or revising one application package

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md`
3. the specific intake file
4. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/scripts/generate_application.py` only if the task changes generator behavior

Load profile/tone/reference JSON files only when the task actually edits those layers.

Escalate to deeper reading when:
- the user asks for a tone shift or stronger authenticity
- the generated output feels generic, flat, or too templated
- the task modifies templates, scoring logic, or summary behavior
- page-limit or layout problems appear in rendered PDFs

### For tone / voice work

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md`
3. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/writing-mode-framework.md`
4. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic_writing_profile.json`
5. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/portfolio_digest.json`

Load the raw authentic archive only when you need stronger evidence for a tone decision.

Escalate to deeper reading when:
- abstract voice notes are not enough to resolve the tone decision
- the user wants higher fidelity to Cuong's real historical writing
- there is tension between recruiter safety and authentic voice
- a change may affect future outputs broadly

### For rule/debug/layout work

Read:
1. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/AGENTS.md`
3. the specific intake file
4. `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/scripts/generate_application.py`
5. the relevant template or generated output involved in the bug

Do not load all taxonomy/profile/evidence files unless the bug points there.

Escalate to deeper reading when:
- the bug may come from profile data, taxonomy, or evidence selection
- the output mismatch is not explained by the first file set
- the issue is recurring across multiple applications

## First Actions

When you enter this folder for application work:

1. Read `/Users/pmlecuong/Documents/CuongProjects/CuongCV/AGENTS.md`
2. Read this file
3. Check `git status --short`
4. Identify whether the task is:
   - intake creation/update
   - cover letter
   - CV variant
   - role-fit snapshot
   - generator logic/template change
   - PDF validation only

## Canonical Files

Use these as the source of truth:

- profile facts: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/master_profile.json`
- reusable evidence: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/evidence_library.json`
- role families: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/role_profiles.json`
- shared summary variants: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/summary_versions.json`
- shared JD/search taxonomy: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/job_taxonomy.json`
- portfolio/tone digest: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/portfolio_digest.json`
- authentic voice DNA: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic_writing_profile.json`
- raw authentic writing archive: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic-writing-samples-2012-2018.md`
- annotated authentic writing guide: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/authentic-writing-samples-annotated.md`
- writing-mode framework: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/writing-mode-framework.md`
- intakes: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/intakes/*.json`
- generator: `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/scripts/generate_application.py`
- rule checker: `/Users/pmlecuong/.codex/skills/job-search-cuong/scripts/check_application_rules.py`

Generated artifacts are outputs, not truth. Edit the structured inputs and regenerate.

## Identity Contract

Keep these fixed unless the user explicitly updates them:

- name: `Le Cuong Nguyen`
- contact details
- address
- education entries, grades, and locations
- awards and certifications
- employer names
- work dates
- side-project names and core descriptions

If a fixed fact changes in the generator layer, check whether the public CV layer in `src/data/resume-data.tsx` must also change.

## Application Outputs

Each package can contain:

- `cover-letter/cover_letter.tex`
- `cover-letter/cover_letter.html`
- `cover-letter/cover-letter-<name>-<job>-<timestamp>.pdf`
- `skill-assessment/role_fit_snapshot.tex`
- `skill-assessment/role_fit_snapshot.html`
- `skill-assessment/role_fit_snapshot.json`
- `skill-assessment/role-fit-snapshot-<name>-<job>-<timestamp>.pdf`
- `cv/<role>.json`
- `cv/resume-<name>-<job>-<timestamp>.pdf`
- `manifest.json`
- `notes.md`
- `communication-log.md`

Keep earlier timestamped PDFs. Never delete prior rendered versions just because a newer run exists.

## Communication Log Rules

For recruiter or interview email work tied to an existing application package:

- create or update `communication-log.md` in that package folder
- append every meaningful inbound or outbound email interaction
- record the concrete date logged, participants, direction, status, summary, and the final reply text when a reply is drafted
- if no reply is needed, record that explicitly instead of leaving the thread undocumented
- treat this file as the communication history for future reapplications or follow-ups

## Role Families

The current supported role families are:

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

Role families affect:

- `About` text
- evidence priority
- adaptive skill ordering
- cover-letter strength framing
- role-fit keyword selection
- role-fit snapshot scoring and notes

Role families do not change factual identity.

## Summary Versions

The CV summary paragraph is controlled separately by `summary_version`.

Default:

- `strongest_balanced`

Other reusable summary styles live in `summary_versions.json`.

If the JD strongly points to another summary and the intake does not specify one, stop and ask the user instead of guessing when the choice is materially ambiguous.

## Skills Rule

Generated CVs must show:

- 7 fixed core skills
- 7 adaptive skills

The master profile must keep exactly 7 core skills. Do not quietly add tool names into the core list.

## Cover Letter Rules

Hard rules:

- one page maximum
- conservative German business-letter structure
- left company block
- right sender block
- right-aligned date
- bold subject line
- embedded signature image from `application-system/signature.png`
- enclosure line

Content rules:

- prefer named recruiter/contact lookup first
- use `Hiring Team` only when no named contact can be verified
- default availability is 14 days from the current date
- default work constraint is up to 20 hours per week unless the user overrides it
- do not invent experience
- keep tone formal and evidence-oriented
- keep the final letter recruiter-safe, but let the opening and motivation feel personally grounded rather than fully templated
- preserve sincerity and contribution-oriented confidence from Cuong's authentic pre-AI writing, while removing old repetition and outdated phrasing
- when changing tone logic materially, review the raw authentic writing archive first rather than relying only on abstract voice notes
- do not use blog mode, work mode, or academic mode language in final application artifacts

German mismatch rule:

If the role explicitly requires strong/fluent/business German and Cuong does not clearly meet it, acknowledge that briefly in the last paragraph, state that German is being improved, and optionally ask to be considered for a more suitable English-first role if needed.

## Role Fit Snapshot Rules

The role-fit snapshot is a separate one-page supplement, not part of the cover letter and not the main CV.

Current contract:

- title: `Role Fit Snapshot and Self-Assessment`
- it must state clearly that it is based on Cuong's own assessment against the current job description
- one page maximum
- same font family and general paper rhythm as the cover letter
- no signature section
- top-right sender/contact block with blank left space above the title block, matching the cover-letter rhythm

Fixed assessment dimensions:

1. `Requirements & Analysis`
2. `Process & Workflow Design`
3. `Delivery & Stakeholder Coordination`
4. `AI Workflow & Automation`

These four dimensions are fixed. Do not keep changing the chart structure per job.

What should stay dynamic per job:

- axis scores
- axis note wording
- role-fit keywords
- methods & tools
- domain exposure
- growth areas

Snapshot content must be visibly tied to both:

- the current JD
- verified facts from Cuong's profile

Do not inject JD-only tools as if they were Cuong's own skills. If a tool appears only in the JD and not in the verified inventory, it may influence fit language but not become a claimed skill.

## Intake Workflow

When the user provides a job URL or JD:

1. Create or update an intake JSON under `intakes/`
2. Set the most defensible `primary_role`
3. Add `target_roles` only when the user explicitly wants multiple variants or when testing role-family coverage
4. Add `summary_version` when needed
5. Regenerate through the Python generator

Default deliverable for one role:

- one intake JSON
- one cover letter
- one CV variant
- one role-fit snapshot
- PDFs when requested or useful

## Validation Workflow

Before shipping application changes:

1. Run the generator
2. Run the rule checker
3. Check page limits:
   - cover letter: 1 page
   - role-fit snapshot: 1 page
   - CV: 2 pages
4. If layout changed, inspect the actual rendered PDF, not only the source template

Preferred checks:

```bash
python3 application-system/scripts/generate_application.py --intake <path> --compile-pdf
python3 /Users/pmlecuong/.codex/skills/job-search-cuong/scripts/check_application_rules.py \
  --resume-data /Users/pmlecuong/Documents/CuongProjects/CuongCV/src/data/resume-data.tsx \
  --summary-versions /Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/summary_versions.json \
  --master-profile /Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/master_profile.json \
  --intake <path> \
  --cover-letter <cover-letter-source> \
  --cover-letter-pdf <cover-letter-pdf> \
  --pdf <cv-pdf>
```

If the snapshot layout changes materially, render and visually inspect the real PDF output before handing it back.

## Editing Rules

- Prefer structured JSON changes over ad hoc rewriting
- Prefer generator/template fixes over editing generated outputs directly
- Use deterministic wording grounded in evidence
- Keep the online CV and generator profile aligned on fixed facts
- Do not treat generated PDFs as editable source files

## Reporting Contract

When you finish an application-system task, report:

- intake file used
- output directory
- whether PDFs were compiled
- summary version used
- role family/families used
- whether the rule checker passed
- any remaining layout or content risk
