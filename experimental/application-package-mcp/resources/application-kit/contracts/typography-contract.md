# Typography Contract

## Required profile

All local cover-letter PDFs generated from this kit must use Inter Regular and
Inter Bold through the browser print path. The release PDF is rendered from
`application-kit/templates/cover_letter.html`, not from TeX, because the main CV
also uses the Chrome/HTML print pipeline.

The local workspace must have:

- `application-kit/fonts/Inter-Regular.ttf`
- `application-kit/fonts/Inter-Bold.ttf`

Use `python3 application-kit/scripts/install_inter_fonts.py` to install the
verified font files when they are missing.

## Agent rule

Do not edit the typography CSS in a job-specific output. If a workspace audit
reports a template hash mismatch or an old kit version, retrieve the current MCP
application kit and update only MCP-managed files. Never overwrite profile,
voice, source, job, asset, or application files to fix a typography update.

## Release check

Before calling a cover letter ready, the local agent must confirm:

1. `application-kit/templates/cover_letter.html` contains `@font-face` rules for Inter.
2. `python3 scripts/workspace_audit.py --root .` records the managed hashes.
3. `audit_workspace_manifest` reports `workspace_current`.
4. The generated PDF is one A4 page, embeds Inter Regular/Bold, and is visually legible after PNG rendering.
