# Typography Contract

## Required profile

All local cover-letter PDFs generated from this kit use the portable
Helvetica-style TeX Gyre Heros family:

```tex
\usepackage{tgheros}
\renewcommand{\familydefault}{\sfdefault}
```

This is deliberately a modern sans-serif profile, aligned with the visual
language of the main CV. It is included in standard TeX Live distributions and
works with `pdflatex`; it must not depend on whatever fonts happen to be
installed on a student's laptop.

## Agent rule

Do not edit the typography lines in a job-specific output. If a workspace audit
reports a template hash mismatch or an old kit version, retrieve the current
MCP application kit and update only MCP-managed files. Never overwrite profile,
voice, source, job, asset, or application files to fix a typography update.

## Release check

Before calling a cover letter ready, the local agent must confirm:

1. `application-kit/templates/cover_letter.tex` contains both required lines.
2. `python3 scripts/workspace_audit.py --root .` records the managed hashes.
3. `audit_workspace_manifest` reports `workspace_current`.
4. The compiled PDF is one A4 page and visually legible.
