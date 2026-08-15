#!/usr/bin/env python3
"""Build an editable local HTML CV from verified local source text.

Default behavior uses the bundled German rounded Lebenslauf fallback template.
If the student already has a preferred CV format, use that PDF/DOCX/HTML as the
visual reference instead and iterate locally with browser screenshots until the
HTML matches before calling the CV layout passed.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


SECTION_ALIASES = {
    "experience": {
        "experience", "work experience", "professional experience",
        "berufliche erfahrungen", "berufserfahrung",
    },
    "skills": {
        "skills", "kennnisse", "kenntnisse", "kenntnisse & fähigkeiten",
        "kenntnisse & faehigkeiten", "fähigkeiten", "faehigkeiten",
    },
    "education": {"education", "ausbildung", "studium"},
    "languages": {"languages", "sprachen"},
}


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def section_key(heading: str) -> str | None:
    normalized = normalize_heading(heading).replace(":", "")
    for key, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def load_source(root: Path) -> str:
    source = root / "candidate/extracted/cv-source.md"
    if not source.exists():
        raise SystemExit("Run ingest_cv.py first; candidate/extracted/cv-source.md is missing.")
    return source.read_text(encoding="utf-8").replace("# Extracted CV Source\n", "", 1).strip()


def parse_markdown(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {"name": "", "summary": [], "experience": [], "skills": [], "education": [], "languages": []}
    current = "summary"
    current_entry: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            data["name"] = line[2:].strip()
            continue
        if line.startswith("## "):
            current = section_key(line[3:].strip()) or "summary"
            current_entry = None
            continue
        if not data["name"]:
            data["name"] = line
            continue
        is_bullet = raw.lstrip().startswith(("-", "•", "*"))
        bullet = re.sub(r"^[-•*]\s+", "", line).strip()
        if current == "experience":
            looks_like_entry = (not is_bullet) and (
                bool(re.match(r"^[A-ZÄÖÜ0-9][^.!?]{3,95}(?:\d{4}|bis|–|-|/)", bullet)) or bullet.isupper()
            )
            if looks_like_entry:
                current_entry = {"title": bullet, "subtitle": "", "bullets": []}
                data["experience"].append(current_entry)
            elif current_entry and not current_entry["subtitle"] and len(bullet) < 95 and not is_bullet:
                current_entry["subtitle"] = bullet
            elif current_entry:
                current_entry["bullets"].append(bullet)
            else:
                current_entry = {"title": bullet, "subtitle": "", "bullets": []}
                data["experience"].append(current_entry)
        elif current in {"skills", "languages"}:
            data[current].append(bullet)
        elif current == "education":
            data["education"].append(bullet)
        else:
            data["summary"].append(bullet)
    return data


def escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def render_items(items: list[str]) -> str:
    return "\n".join(f'<li contenteditable="true">{escape(item)}</li>' for item in items if str(item).strip())


def render_experience(entries: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for entry in entries:
        bullets = render_items([str(item) for item in entry.get("bullets", [])])
        parts.append("\n".join([
            '<article class="entry">',
            f'<h3 class="entry-title" contenteditable="true">{escape(entry.get("title"))}</h3>',
            f'<p class="entry-subtitle" contenteditable="true">{escape(entry.get("subtitle"))}</p>' if entry.get("subtitle") else "",
            f"<ul>{bullets}</ul>" if bullets else "",
            "</article>",
        ]))
    return "\n".join(parts)


def render_education(items: list[str]) -> str:
    return "\n".join(f'<p class="education-line" contenteditable="true">{escape(item)}</p>' for item in items if item.strip())


def read_profile_defaults(root: Path) -> dict[str, str]:
    profile_path = root / "profile/master_profile.json"
    if not profile_path.exists():
        return {}
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        "name": str(profile.get("name") or profile.get("full_name") or ""),
        "email": str(profile.get("email") or ""),
        "phone": str(profile.get("phone") or ""),
        "linkedin": str(profile.get("linkedin") or ""),
    }


def build_html(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    root = Path(args.root).resolve()
    source_data = parse_markdown(load_source(root))
    profile = read_profile_defaults(root)
    name = args.name or profile.get("name") or source_data["name"] or "Candidate Name"
    summary = args.summary or " ".join(source_data["summary"][:3]) or "Kurzprofil hier ergänzen."
    email = args.email or profile.get("email") or "email@example.com"
    phone = args.phone or profile.get("phone") or "+49 ..."
    linkedin = args.linkedin or profile.get("linkedin") or "linkedin.com/in/..."
    photo_html = '<div class="photo-frame" aria-label="Kein Foto"></div>'
    if args.photo:
        photo = root / args.photo
        if not photo.exists():
            raise SystemExit("Provided photo path does not exist.")
        photo_html = f'<figure class="photo-frame"><img src="{escape(photo.resolve().as_uri())}" alt="Candidate photo"></figure>'
    template_path = Path(args.template).resolve() if args.template else Path(__file__).resolve().parents[1] / "templates" / "cv_german_rounded.html"
    template = template_path.read_text(encoding="utf-8")
    mapping = {
        "NAME": escape(name), "SUMMARY": escape(summary), "PHONE": escape(phone), "EMAIL": escape(email), "LINKEDIN": escape(linkedin), "PHOTO_HTML": photo_html,
        "EXPERIENCE_HTML": render_experience(source_data["experience"]) or '<article class="entry"><h3 class="entry-title" contenteditable="true">Berufserfahrung ergänzen</h3></article>',
        "SKILLS_HTML": render_items(source_data["skills"]) or '<li contenteditable="true">Kenntnisse ergänzen</li>',
        "EDUCATION_HTML": render_education(source_data["education"]) or '<p class="education-line" contenteditable="true">Ausbildung ergänzen</p>',
        "LANGUAGES_HTML": render_items(source_data["languages"]) or '<li contenteditable="true">Sprachen ergänzen</li>',
    }
    document = template
    for key, value in mapping.items():
        document = document.replace(f"@@{key}@@", value)
    document = re.sub(
        r"\n\s*<!-- TEMPLATE_PREVIEW_START -->.*?<!-- TEMPLATE_PREVIEW_END -->",
        "",
        document,
        flags=re.DOTALL,
    )
    manifest = {
        "source": "candidate/extracted/cv-source.md",
        "template": str(template_path),
        "template_style": "german-rounded-fallback",
        "photo": args.photo or None,
        "requires_playwright_visual_gate": True,
        "pass_rule": "Do not mark as passed until the generated HTML is rendered and visually checked. If a user-provided PDF/DOCX format exists, compare against that reference and iterate until the structure matches.",
    }
    return document, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--job", required=True)
    parser.add_argument("--photo")
    parser.add_argument("--template")
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--linkedin")
    parser.add_argument("--summary")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    target = root / "applications" / args.job / "cv"
    target.mkdir(parents=True, exist_ok=True)
    document, manifest = build_html(args)
    output = target / "cv-tailored.html"
    output.write_text(document, encoding="utf-8")
    manifest["output"] = output.relative_to(root).as_posix()
    (target / "cv-build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
