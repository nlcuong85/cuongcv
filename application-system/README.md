# Application System

This folder is a CLI-first application generator for Nguyen Le Cuong's Germany job search workflow.

It is designed for AI-agent usage from the project root. The generator accepts one intake JSON file and produces:

- one tailored cover letter
- one HTML preview of the cover letter
- one requested CV variant by default
- optional PDFs compiled from LaTeX for the cover letter and browser print for the CV
- a manifest that explains which evidence blocks were used

## Why this exists

The public CV site in this repository is still the canonical profile surface, but job applications need a second layer:

- structured evidence from Cuong's CV and portfolio
- role-specific positioning without inventing experience
- company-specific document generation
- deterministic file outputs that Codex or other CLI agents can inspect

## Source of truth

- Master profile facts: `data/master_profile.json`
- Reusable case-study proof: `data/evidence_library.json`
- Four role presets: `data/role_profiles.json`
- Portfolio voice and case-study digest: `data/portfolio_digest.json`
- Company/job intake: `intakes/*.json`

The public CV source at `src/data/resume-data.tsx` remains the canonical fact layer for fixed CV data. The application generator may vary summary positioning, skills emphasis, and work-bullet wording, but it should stay aligned with the online CV for:

- contact information
- education entries and grades
- awards/certifications
- side-project identity
- employer names
- work-history dates

## Supported outputs

- `cover-letter/cover_letter.tex`
- `cover-letter/cover_letter.html`
- `cover-letter/cover_letter.pdf` when `--compile-pdf` is used
- `cv/<role>.json`
- `cv/<role>.pdf` when `--compile-pdf` is used
- `manifest.json`
- `notes.md`

## Role variants

The generator creates only the requested role variant unless the intake explicitly sets `target_roles`.

1. `product_manager`
2. `product_owner`
3. `business_analyst`
4. `ai_product_ops`

These variants only change emphasis, summary, selected achievements, and skill ordering. They do not rewrite Cuong's career history.

## Usage

Run from the repository root:

```bash
python3 application-system/scripts/generate_application.py \
  --intake application-system/intakes/sample-generic-company.json
```

Compile PDFs as well:

```bash
python3 application-system/scripts/generate_application.py \
  --intake application-system/intakes/sample-generic-company.json \
  --compile-pdf
```

Choose a custom output directory:

```bash
python3 application-system/scripts/generate_application.py \
  --intake application-system/intakes/sample-generic-company.json \
  --output application-system/outputs/my-target-company
```

## Intake contract

The intake file is plain JSON. Expected fields:

- `company_name`
- `company_location`
- `contact_name`
- `contact_title`
- `job_title`
- `job_url`
- `language`
- `primary_role`
- `target_roles` (optional array)
- `start_date`
- `why_company`
- `job_description`
- `requirements`

If the contact name is unknown, leave it empty. The generator will fall back to a safe salutation.

## CV rendering path

The CV PDF reuses the main Next.js CV layout instead of a separate LaTeX template:

1. the generator writes role-specific resume JSON to `public/generated-cv-data/<company>/<role>.json`
2. the app renders it at `/cuongcv/generated-cv/?company=<company>&role=<role>`
3. headless Chrome prints that route to PDF using the site's existing print styles

## Future agent workflow

Later, when a job URL is provided, an AI agent should:

1. extract job/company details into a new intake JSON
2. confirm only missing facts with the user
3. run this generator
4. review the generated cover letter and the requested CV variant
5. choose the strongest generated version for submission

## Notes

- The templates are conservative and German-application friendly.
- Tone is calibrated using Cuong's public writing, but final job documents remain concise and recruiter-safe.
- The system keeps evidence explicit so future edits stay auditable.
