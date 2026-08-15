# Typography Contract

## Required profile

All local cover-letter PDFs generated from this kit must match the historical
application-system cover-letter style used in existing output folders such as
`schwarz-it-werkstudent-marketing-systeme-m-w-d/cover-letter`.

The canonical PDF path is:

- LaTeX source: `application-kit/templates/cover_letter.tex`
- Compiler: `latexmk -pdf` / `pdfTeX`
- Font package: `lmodern`
- Expected PDF fonts: `LMRoman10-Regular` and `LMRoman10-Bold`

Do not switch cover-letter PDFs to Chrome/Skia, Inter, Helvetica, Arial, TeX
Gyre Heros, or another browser/system font unless the user explicitly changes
the visual baseline again.

## Agent rule

Do not edit the typography package lines in a job-specific output. If a workspace audit
reports a template hash mismatch or an old kit version, retrieve the current MCP
application kit and update only MCP-managed files. Never overwrite profile,
voice, source, job, asset, or application files to fix a typography update.

## Release check

Before calling a cover letter ready, the local agent must confirm:

1. `application-kit/templates/cover_letter.tex` contains `fontenc`, `inputenc`, and `lmodern`.
2. `python3 scripts/workspace_audit.py --root .` records the managed hashes.
3. `audit_workspace_manifest` reports `workspace_current`.
4. The generated PDF is one A4 page, embeds Latin Modern Roman regular/bold, and visually matches the historical LaTeX cover-letter rhythm after PNG rendering.
