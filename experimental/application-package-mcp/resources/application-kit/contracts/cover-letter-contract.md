# Cover Letter Contract

This contract is mandatory for local application generation.

The local AI agent may write content, but it must not change the document structure, LaTeX layout, or validation rules. The local renderer owns the layout.

Use this contract for local layout and file validation. For deeper reader, tone, and convention feedback, send only the selected cover-letter text to the remote writing checker.

## Output Files

Required local outputs:

- `cover-letter-draft.json`
- `cover-letter.tex`
- `cover-letter.pdf`
- `cover-letter.md`
- `validation.md`
- `manifest.json`

## Fixed Layout

The generated `cover-letter.tex` must use the provided `templates/cover_letter.tex` without changing:

- `\documentclass[9pt,a4paper]{article}`
- geometry: `left=25mm,right=20mm,top=36mm,bottom=18mm`
- sender block: top-right `0.34\textwidth`
- recipient block: left `0.42\textwidth`
- right-aligned date
- bold subject line
- salutation before body
- exactly five body paragraphs
- signature area
- enclosure list
- `\pagestyle{empty}`
- typography: `\usepackage{tgheros}` and
  `\renewcommand{\familydefault}{\sfdefault}`. This is the required portable
  Helvetica-style profile. Do not use Latin Modern, a serif fallback, or an
  unbundled system font.

## Fixed Paragraph Order

The cover letter body must contain exactly five paragraphs in this order:

1. `opening_paragraph`
2. `body_paragraph_one`
3. `body_paragraph_two`
4. `motivation_paragraph`
5. `closing_paragraph`

## Paragraph Purpose

`opening_paragraph`

- identifies the job title and company
- names a concrete trigger from the job description
- explains why this work fits the candidate's working style
- must not be a generic enthusiasm sentence

`body_paragraph_one`

- gives the strongest evidence-backed match
- must be grounded in `candidate/evidence.md`
- should connect the evidence to the job requirements

`body_paragraph_two`

- gives a second proof point
- should use a different experience, project, or skill cluster
- must not repeat paragraph one

`motivation_paragraph`

- explains why this company or role context matters
- should be practical, specific, and non-fluffy
- must avoid generic praise

`closing_paragraph`

- thanks the reader
- states availability or practical working arrangement when known
- may include a brief language or work-authorization caveat if relevant
- ends with a clear, polite next step

## Length Budget

Hard limits:

- total body text: maximum 1,950 characters
- opening paragraph: maximum 390 characters
- body paragraph one: maximum 430 characters
- body paragraph two: maximum 540 characters
- motivation paragraph: maximum 390 characters
- closing paragraph: maximum 360 characters

If the PDF exceeds one page, shorten in this order:

1. motivation paragraph
2. body paragraph two
3. opening paragraph
4. body paragraph one
5. closing paragraph

Do not reduce font size, margins, or spacing to hide overflow.

## Required Draft JSON

The local AI agent must create:

```json
{
  "sender_lines": ["Name", "Address line", "Phone", "Email"],
  "recipient_lines": ["Company", "Hiring Team", "Location"],
  "date_line": "City, 29 April 2026",
  "subject_line": "Application for Target Role",
  "salutation": "Dear Hiring Team,",
  "opening_paragraph": "",
  "body_paragraph_one": "",
  "body_paragraph_two": "",
  "motivation_paragraph": "",
  "closing_paragraph": "",
  "signature_name": "Name",
  "signature_path": "",
  "enclosures": [
    "Curriculum Vitae",
    "Bachelor Degree Diploma",
    "Reference letter from previous employers"
  ]
}
```

## Validation Rules

The local validator must fail when:

- PDF is missing
- PDF has more than one page
- generated `.tex` changes the fixed layout contract
- any required paragraph is missing
- paragraph count is not five
- any paragraph exceeds its length budget
- `/OpenAction`, `/AA`, `/JavaScript`, or `/JS` appears in the PDF bytes
- visible PDF text contains raw LaTeX commands such as `\begin`, `\end`, `\vspace`, `\textwidth`, `\raggedleft`, or `\includegraphics`
- any draft field contains raw LaTeX layout/control commands instead of plain user-facing text
- unescaped user text breaks LaTeX compilation
- applicant-facing text contains internal workspace language such as `candidate evidence record`, `profile JSON`, `source-analysis file`, or `claims in this draft`
- applicant-facing text uses unsupported-looking overclaim language such as `perfect candidate`, `expert in`, or `proven track record`

When validation fails, the local AI agent must revise `cover-letter-draft.json` and rerun the renderer. It must not manually edit the LaTeX template.

## Human Writing Validation

The local validator checks structure, length, LaTeX safety, PDF safety, and CV helper basics. It does not include the private writing checker rules.

Warnings in this section should be reviewed and usually fixed before submission. They flag:

- generic application phrases
- repeated sentence starts
- very even sentence or paragraph rhythm
- comma-separated skill lists
- missing concrete work or project texture
- missing job-specific opening trigger
- missing optional `voice_source_map`

Passing this local audit does not guarantee an AI Checker percentage. It is a practical risk filter before human review.
