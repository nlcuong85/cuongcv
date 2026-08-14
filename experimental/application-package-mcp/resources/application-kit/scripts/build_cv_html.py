#!/usr/bin/env python3
"""Build a readable, editable local HTML CV from verified local source text.

This intentionally does not invent a designed CV. It preserves source order and
creates a simple editable semantic document; visual review compares it locally
against the user's rendered source reference before finalization.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", default="."); parser.add_argument("--job", required=True); parser.add_argument("--photo")
    args = parser.parse_args(); root = Path(args.root).resolve(); source = root / "candidate/extracted/cv-source.md"
    if not source.exists(): raise SystemExit("Run ingest_cv.py first; candidate/extracted/cv-source.md is missing.")
    text = source.read_text(encoding="utf-8").replace("# Extracted CV Source\n", "", 1).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    photo_html = ""
    if args.photo:
        photo = root / args.photo
        if not photo.exists(): raise SystemExit("Provided photo path does not exist.")
        photo_html = f'<img class="photo" src="{html.escape(Path(args.photo).as_posix())}" alt="Candidate photo">'
    body = []
    for index, line in enumerate(lines):
        escaped = html.escape(line)
        if index == 0: body.append(f"<h1 contenteditable=\"true\">{escaped}</h1>")
        elif line.isupper() and len(line) < 70: body.append(f"<h2 contenteditable=\"true\">{escaped}</h2>")
        else: body.append(f"<p contenteditable=\"true\">{escaped}</p>")
    target = root / "applications" / args.job / "cv"; target.mkdir(parents=True, exist_ok=True)
    document = """<!doctype html><html><head><meta charset=\"utf-8\"><title>Tailored CV</title><style>
body{font-family:Arial,sans-serif;max-width:800px;margin:36px auto;color:#1f2937;line-height:1.45}.header{display:flex;justify-content:space-between;gap:24px}.photo{max-width:120px;max-height:150px;object-fit:cover}h1{margin-bottom:4px}h2{border-bottom:1px solid #cbd5e1;padding-bottom:3px;margin-top:24px;font-size:1.05rem}p{margin:6px 0}@media print{body{margin:14mm}.photo{max-width:105px}}</style></head><body><main><div class=\"header\"><div>""" + "\n".join(body) + f"</div>{photo_html}</div></main></body></html>"
    output = target / "cv-tailored.html"; output.write_text(document, encoding="utf-8")
    (target / "cv-build-manifest.json").write_text(json.dumps({"source": source.relative_to(root).as_posix(), "photo": args.photo or None, "output": output.relative_to(root).as_posix()}, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__": raise SystemExit(main())
