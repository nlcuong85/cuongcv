#!/usr/bin/env python3
"""Local-only application package renderer.

This script intentionally runs on the student laptop. It renders files and runs
basic document checks. Advanced writing feedback is provided by the remote MCP
checker only for selected text that the student intentionally submits.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PARAGRAPH_KEYS = [
    "opening_paragraph",
    "body_paragraph_one",
    "body_paragraph_two",
    "motivation_paragraph",
    "closing_paragraph",
]

PARAGRAPH_LIMITS = {
    "opening_paragraph": 390,
    "body_paragraph_one": 430,
    "body_paragraph_two": 540,
    "motivation_paragraph": 390,
    "closing_paragraph": 360,
}

REQUIRED_TEMPLATE_MARKERS = [
    r"\documentclass[9pt,a4paper]{article}",
    r"\usepackage[a4paper,left=25mm,right=20mm,top=36mm,bottom=18mm]{geometry}",
    r"\usepackage{fontspec}",
    r"\setmainfont{Inter-Regular}[Path=fonts/,Extension=.ttf,BoldFont=Inter-Bold]",
    r"\pagestyle{empty}",
    "@@SENDER_BLOCK@@",
    "@@RECIPIENT_BLOCK@@",
    "@@DATE_LINE@@",
    "@@SUBJECT_LINE@@",
    "@@SALUTATION@@",
    "@@OPENING_PARAGRAPH@@",
    "@@BODY_PARAGRAPH_ONE@@",
    "@@BODY_PARAGRAPH_TWO@@",
    "@@MOTIVATION_PARAGRAPH@@",
    "@@CLOSING_PARAGRAPH@@",
    "@@SIGNATURE_NAME@@",
]

REQUIRED_HTML_TEMPLATE_MARKERS = [
    '@font-face',
    'font-family: "Inter"',
    "@@SENDER_BLOCK@@",
    "@@RECIPIENT_BLOCK@@",
    "@@DATE_LINE@@",
    "@@SUBJECT_LINE@@",
    "@@SALUTATION@@",
    "@@OPENING_PARAGRAPH@@",
    "@@BODY_PARAGRAPH_ONE@@",
    "@@BODY_PARAGRAPH_TWO@@",
    "@@MOTIVATION_PARAGRAPH@@",
    "@@CLOSING_PARAGRAPH@@",
    "@@SIGNATURE_NAME@@",
    "@@ENCLOSURE_ITEMS@@",
]

LOCAL_TEMPLATE_PHRASES = [
    "please accept my application",
    "i am applying for",
    "i am writing to apply",
    "i wanted to apply for",
    "i would welcome the opportunity",
    "i would be glad to discuss",
    "i believe i can contribute",
    "i have built a strong foundation",
    "that has made me comfortable",
]

LOCAL_EVIDENCE_MARKERS = [
    "project",
    "worked",
    "built",
    "mapped",
    "documented",
    "tested",
    "supported",
    "coordinated",
    "authored",
    "created",
]

LOCAL_ARTIFACT_MARKERS = [
    "user story",
    "acceptance criteria",
    "guide",
    "how-to",
    "report",
    "workflow",
    "document",
    "deck",
    "wiki",
    "handover",
    "note",
]

LOCAL_WORK_FRICTION_MARKERS = [
    "hard",
    "difficult",
    "unclear",
    "missing",
    "gap",
    "issue",
    "problem",
    "checked",
    "review",
    "learned",
    "trained me",
]


@dataclass
class Validation:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def sentence_starts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sentence_text in re.split(r"(?<=[.!?])\s+", normalize_space(text)):
        match = re.match(r"([A-Za-z']+)", sentence_text.strip())
        if match:
            key = match.group(1).lower()
            counts[key] = counts.get(key, 0) + 1
    return counts


def local_authoring_checks(draft: dict[str, Any]) -> Validation:
    errors: list[str] = []
    warnings: list[str] = []
    text = normalize_space(" ".join(str(draft.get(key) or "") for key in PARAGRAPH_KEYS))
    lowered = text.lower()
    phrase_hits = [phrase for phrase in LOCAL_TEMPLATE_PHRASES if phrase in lowered]
    if phrase_hits:
        errors.append("Cover-letter draft uses template application phrasing: " + ", ".join(f"`{item}`" for item in phrase_hits[:5]) + ".")
    starts = sentence_starts(text)
    repeated = [f"{word}={count}" for word, count in starts.items() if word in {"i", "this", "my"} and count >= 3]
    if repeated:
        errors.append("Cover-letter draft repeats sentence starts too often: " + ", ".join(repeated) + ".")
    the_count = starts.get("the", 0)
    if the_count >= 3:
        warnings.append(f"Cover-letter draft starts {the_count} sentences with `The`; vary one if the final MCP checker flags it.")
    if re.search(r"[,;][^.!?]+,[^.!?]+,[^.!?]+,[^.!?]+", text):
        errors.append("Cover-letter draft contains a list-like sentence; replace the list with one concrete work example.")
    if not any(marker in lowered for marker in LOCAL_EVIDENCE_MARKERS):
        errors.append("Cover-letter draft lacks candidate evidence: add one real project, task, workflow, or supported activity.")
    if not any(marker in lowered for marker in LOCAL_ARTIFACT_MARKERS):
        errors.append("Cover-letter draft lacks a concrete work artifact such as a guide, report, workflow, note, deck, or handover.")
    if not any(marker in lowered for marker in LOCAL_WORK_FRICTION_MARKERS):
        warnings.append("Cover-letter draft may be too smooth; add what was unclear, checked, missing, learned, or reviewed.")
    return Validation(errors, warnings)


def join_latex_lines(lines: list[str]) -> str:
    return "\\\\\n".join(latex_escape(str(line).strip()) for line in lines if str(line).strip())


def html_escape(value: str) -> str:
    return html.escape(value, quote=True)


def join_html_lines(lines: list[str]) -> str:
    return "<br>\n".join(html_escape(str(line).strip()) for line in lines if str(line).strip())


def validate_template(template: str) -> list[str]:
    errors: list[str] = []
    for marker in REQUIRED_TEMPLATE_MARKERS:
        if marker not in template:
            errors.append(f"Template is missing required marker or layout line: {marker}")
    return errors


def validate_html_template(template: str) -> list[str]:
    errors: list[str] = []
    for marker in REQUIRED_HTML_TEMPLATE_MARKERS:
        if marker not in template:
            errors.append(f"HTML template is missing required marker or layout line: {marker}")
    return errors


def build_mapping(draft: dict[str, Any]) -> dict[str, str]:
    enclosures = draft.get("enclosures") or [
        "Curriculum Vitae",
        "Bachelor Degree Diploma",
        "Reference letter from previous employers",
    ]
    _ = enclosures
    signature_path = str(draft.get("signature_path") or "").strip()
    mapping = {
        "SENDER_BLOCK": join_latex_lines(list(draft.get("sender_lines") or [])),
        "RECIPIENT_BLOCK": join_latex_lines(list(draft.get("recipient_lines") or [])),
        "DATE_LINE": latex_escape(str(draft.get("date_line") or "")),
        "SUBJECT_LINE": latex_escape(str(draft.get("subject_line") or "")),
        "SALUTATION": latex_escape(str(draft.get("salutation") or "Dear Hiring Team,")),
        "OPENING_PARAGRAPH": latex_escape(str(draft.get("opening_paragraph") or "")),
        "BODY_PARAGRAPH_ONE": latex_escape(str(draft.get("body_paragraph_one") or "")),
        "BODY_PARAGRAPH_TWO": latex_escape(str(draft.get("body_paragraph_two") or "")),
        "MOTIVATION_PARAGRAPH": latex_escape(str(draft.get("motivation_paragraph") or "")),
        "CLOSING_PARAGRAPH": latex_escape(str(draft.get("closing_paragraph") or "")),
        "SIGNATURE_PATH": latex_escape(signature_path),
        "SIGNATURE_NAME": latex_escape(str(draft.get("signature_name") or "")),
    }
    if not signature_path:
        mapping["SIGNATURE_PATH"] = "signature-placeholder-do-not-use.png"
    return mapping


def build_html_mapping(draft: dict[str, Any]) -> dict[str, str]:
    enclosures = [
        f"<li>{html_escape(str(item).strip())}</li>"
        for item in list(draft.get("enclosures") or [
            "Curriculum Vitae",
            "Bachelor Degree Diploma",
            "Reference letter from previous employers",
        ])
        if str(item).strip()
    ]
    signature_path = str(draft.get("signature_path") or "").strip()
    signature_image = ""
    if signature_path:
        signature_image = inline_signature_svg(signature_path)
    return {
        "COMPANY_NAME": html_escape(str(draft.get("company_name") or "Application")),
        "SENDER_BLOCK": join_html_lines(list(draft.get("sender_lines") or [])),
        "RECIPIENT_BLOCK": join_html_lines(list(draft.get("recipient_lines") or [])),
        "DATE_LINE": html_escape(str(draft.get("date_line") or "")),
        "SUBJECT_LINE": html_escape(str(draft.get("subject_line") or "")),
        "SALUTATION": html_escape(str(draft.get("salutation") or "Dear Hiring Team,")),
        "OPENING_PARAGRAPH": html_escape(str(draft.get("opening_paragraph") or "")),
        "BODY_PARAGRAPH_ONE": html_escape(str(draft.get("body_paragraph_one") or "")),
        "BODY_PARAGRAPH_TWO": html_escape(str(draft.get("body_paragraph_two") or "")),
        "MOTIVATION_PARAGRAPH": html_escape(str(draft.get("motivation_paragraph") or "")),
        "CLOSING_PARAGRAPH": html_escape(str(draft.get("closing_paragraph") or "")),
        "SIGNATURE_IMAGE": signature_image,
        "SIGNATURE_NAME": html_escape(str(draft.get("signature_name") or "")),
        "ENCLOSURE_ITEMS": "\n".join(enclosures),
    }


def render_template(template: str, mapping: dict[str, str]) -> str:
    rendered = template
    for key, value in mapping.items():
        rendered = rendered.replace(f"@@{key}@@", value)
    return rendered


def resolve_local_signature_path(draft: dict[str, Any], draft_path: Path) -> dict[str, Any]:
    """Resolve a workspace-relative signature before LaTeX runs from an output folder."""
    signature_path = str(draft.get("signature_path") or "").strip()
    if not signature_path or Path(signature_path).is_absolute():
        return draft
    for base in (draft_path.parent, *draft_path.parents):
        candidate = base / signature_path
        if candidate.is_file():
            resolved = dict(draft)
            resolved["signature_path"] = str(candidate.resolve())
            return resolved
    return draft


def prepare_signature_image(draft: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    signature_path = str(draft.get("signature_path") or "").strip()
    if not signature_path:
        return draft
    source = Path(signature_path)
    if not source.is_file():
        return draft
    target = output_dir / "signature-rendered.png"
    try:
        from PIL import Image  # type: ignore

        image = Image.open(source).convert("RGBA")
        bbox = image.getbbox()
        if bbox:
            left = max(0, bbox[0] - 12)
            top = max(0, bbox[1] - 12)
            right = min(image.width, bbox[2] + 12)
            bottom = min(image.height, bbox[3] + 12)
            image = image.crop((left, top, right, bottom))
        background = Image.new("RGBA", (900, 220), (255, 253, 248, 255))
        x = max(0, (background.width - image.width) // 2)
        y = max(0, (background.height - image.height) // 2)
        background.alpha_composite(image, (x, y))
        background.convert("RGB").save(target)
        prepared = dict(draft)
        prepared["signature_path"] = str(target.resolve())
        return prepared
    except Exception:
        return draft


def inline_signature_svg(path: str) -> str:
    try:
        resolved = Path(path).resolve()
        if resolved.suffix.lower() != ".svg":
            return f'<img class="signature-image" src="{html_escape(resolved.as_uri())}" alt="Signature" />'
        svg = resolved.read_text(encoding="utf-8").strip()
        if "<svg" not in svg:
            return f'<img class="signature-image" src="{html_escape(resolved.as_uri())}" alt="Signature" />'
        return re.sub(r"<svg\s+", '<svg class="signature-image" role="img" aria-label="Signature" ', svg, count=1)
    except Exception:
        return ""


def strip_signature_if_missing(tex: str, draft: dict[str, Any]) -> str:
    signature_path = str(draft.get("signature_path") or "").strip()
    if signature_path:
        return tex
    return re.sub(
        r"\\includegraphics\[width=9cm\]\{signature-placeholder-do-not-use\.png\}\\\\\n\\vspace\{0\.2em\}\n",
        "",
        tex,
    )


def resolve_chrome() -> str | None:
    candidates = [
        os.environ.get("GOOGLE_CHROME_BIN"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def validate_draft(draft: dict[str, Any]) -> Validation:
    errors: list[str] = []
    warnings: list[str] = []
    forbidden_latex = re.compile(
        r"\\(begin|end|vspace|textbf|includegraphics|raggedleft|flushright|minipage|usepackage|documentclass)\b"
    )
    for key in ["sender_lines", "recipient_lines", "date_line", "subject_line", "signature_name"]:
        if not draft.get(key):
            errors.append(f"Missing required draft field: {key}")
    scalar_fields = ["date_line", "subject_line", "salutation", "signature_name", *PARAGRAPH_KEYS]
    for key in scalar_fields:
        value = str(draft.get(key) or "")
        if forbidden_latex.search(value):
            errors.append(f"{key} contains raw LaTeX control text; only plain user-facing text is allowed.")
    for key in ["sender_lines", "recipient_lines", "enclosures"]:
        for item in list(draft.get(key) or []):
            if forbidden_latex.search(str(item)):
                errors.append(f"{key} contains raw LaTeX control text; only plain user-facing text is allowed.")
    for key in PARAGRAPH_KEYS:
        text = normalize_space(str(draft.get(key) or ""))
        if not text:
            errors.append(f"Missing required paragraph: {key}")
            continue
        limit = PARAGRAPH_LIMITS[key]
        if len(text) > limit:
            errors.append(f"{key} exceeds {limit} characters: {len(text)}")
    total = sum(len(normalize_space(str(draft.get(key) or ""))) for key in PARAGRAPH_KEYS)
    if total > 1950:
        errors.append(f"Body text exceeds 1950 characters: {total}")
    if len(list(draft.get("sender_lines") or [])) < 3:
        warnings.append("Sender block has fewer than 3 lines.")
    if len(list(draft.get("recipient_lines") or [])) < 2:
        warnings.append("Recipient block has fewer than 2 lines.")
    return Validation(errors, warnings)


def print_html_pdf(html_path: Path, output_dir: Path) -> tuple[Path | None, list[str]]:
    warnings: list[str] = []
    chrome = resolve_chrome()
    if not chrome:
        warnings.append("Google Chrome or Chromium not found; install Chrome or set GOOGLE_CHROME_BIN to render the Inter PDF.")
        return None, warnings
    pdf_path = output_dir / "cover-letter.pdf"
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-first-run",
        "--no-pdf-header-footer",
        "--virtual-time-budget=3000",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if proc.returncode != 0:
        warnings.append("Chrome PDF rendering failed:\n" + proc.stdout[-2500:])
        return None, warnings
    return pdf_path if pdf_path.exists() else None, warnings


def pdf_page_count(pdf_path: Path) -> int | None:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        proc = subprocess.run([pdfinfo, str(pdf_path)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        match = re.search(r"^Pages:\s+(\d+)$", proc.stdout, re.MULTILINE)
        if match:
            return int(match.group(1))
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def validate_pdf(pdf_path: Path | None) -> Validation:
    errors: list[str] = []
    warnings: list[str] = []
    if not pdf_path:
        errors.append("Hard typography gate cannot pass: Chrome did not produce an Inter PDF.")
        return Validation(errors, warnings)
    pages = pdf_page_count(pdf_path)
    if pages is None:
        warnings.append("Could not determine PDF page count.")
    elif pages != 1:
        errors.append(f"PDF must be exactly 1 page, got {pages}.")
    pdffonts = shutil.which("pdffonts")
    if not pdffonts:
        errors.append("Hard typography gate cannot run: install Poppler pdffonts to verify Inter is embedded.")
    else:
        output = subprocess.run([pdffonts, str(pdf_path)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False).stdout
        if "Inter-Regular" not in output or "Inter-Bold" not in output:
            errors.append("Hard typography gate failed: cover-letter PDF does not embed Inter Regular and Inter Bold.")
        for forbidden_font in ["LMRoman", "TeXGyre", "NimbusRomNo9", "Times-Roman"]:
            if forbidden_font in output:
                errors.append(f"Hard typography gate failed: forbidden non-Inter font detected: {forbidden_font}.")
    data = pdf_path.read_bytes()
    for token in [b"/OpenAction", b"/JavaScript", b"/JS"]:
        if token in data:
            errors.append(f"PDF contains active-content marker: {token.decode()}")
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        proc = subprocess.run([pdftotext, str(pdf_path), "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        visible_text = proc.stdout
        for token in [
            r"\begin{",
            r"\end{",
            r"\vspace",
            r"\textwidth",
            r"\raggedleft",
            r"\includegraphics",
        ]:
            if token in visible_text:
                errors.append(f"PDF visible text leaks LaTeX control text: {token}")
    return Validation(errors, warnings)


def write_cover_letter_md(draft: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cover Letter",
        "",
        "\n".join(str(item) for item in draft.get("sender_lines", [])),
        "",
        "\n".join(str(item) for item in draft.get("recipient_lines", [])),
        "",
        str(draft.get("date_line", "")),
        "",
        f"**{draft.get('subject_line', '')}**",
        "",
        str(draft.get("salutation", "Dear Hiring Team,")),
        "",
    ]
    for key in PARAGRAPH_KEYS:
        lines.extend([str(draft.get(key, "")), ""])
    lines.extend(["Best regards,", "", str(draft.get("signature_name", "")), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def build_cv_markdown(cv_input: dict[str, Any], path: Path) -> Validation:
    errors: list[str] = []
    warnings: list[str] = []
    name = str(cv_input.get("name") or "Candidate")
    job_title = str(cv_input.get("job_title") or "Target Role")
    company = str(cv_input.get("company") or "Target Company")
    overview = normalize_space(str(cv_input.get("overview") or cv_input.get("summary") or ""))
    skills = [str(item).strip() for item in cv_input.get("skills", []) if str(item).strip()]
    evidence = [str(item).strip() for item in cv_input.get("evidence_alignment", []) if str(item).strip()]
    notes = [str(item).strip() for item in cv_input.get("review_notes", []) if str(item).strip()]

    if overview:
        word_count = len(overview.split())
        if word_count < 55:
            warnings.append(f"CV overview may be too short: {word_count} words.")
        if word_count > 125:
            errors.append(f"CV overview is too long: {word_count} words.")
    else:
        errors.append("CV overview is missing.")
    if len(skills) > 14:
        errors.append(f"CV skills must not exceed 14 items, got {len(skills)}.")
    if len(skills) < 8:
        warnings.append(f"CV skills list is short: {len(skills)} items.")

    lines = [
        f"# {name}",
        "",
        "## Target Role",
        "",
        f"{job_title} - {company}",
        "",
        "## Overview",
        "",
        overview,
        "",
        "## Skills",
        "",
        *(f"- {skill}" for skill in skills),
        "",
        "## Evidence Alignment",
        "",
        *(f"- {item}" for item in evidence),
        "",
        "## Review Notes",
        "",
        *(f"- {item}" for item in (notes or ["Candidate review required before submission."])),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return Validation(errors, warnings)


def validation_markdown(results: dict[str, Validation]) -> str:
    lines = ["# Local Application Validation", ""]
    ok = all(result.ok for result in results.values())
    lines.extend([f"Overall: {'PASS' if ok else 'FAIL'}", ""])
    for name, result in results.items():
        lines.extend([f"## {name}", ""])
        lines.append("Errors:")
        lines.extend([f"- {item}" for item in result.errors] or ["- None"])
        lines.append("")
        lines.append("Warnings:")
        lines.extend([f"- {item}" for item in result.warnings] or ["- None"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--cv-input", type=Path)
    args = parser.parse_args()

    script_root = Path(__file__).resolve().parents[1]
    template_path = args.template or script_root / "templates" / "cover_letter.tex"
    html_template_path = script_root / "templates" / "cover_letter.html"
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(script_root / "fonts", output_dir / "fonts", dirs_exist_ok=True)

    draft = prepare_signature_image(resolve_local_signature_path(read_json(args.draft), args.draft.resolve()), output_dir)
    template = template_path.read_text(encoding="utf-8")
    html_template = html_template_path.read_text(encoding="utf-8")
    template_validation = Validation(validate_template(template), [])
    html_template_validation = Validation(validate_html_template(html_template), [])
    draft_validation = validate_draft(draft)
    authoring_validation = local_authoring_checks(draft)
    tex_path = output_dir / "cover-letter.tex"
    html_path = output_dir / "cover-letter.html"
    if template_validation.ok:
        tex = strip_signature_if_missing(render_template(template, build_mapping(draft)), draft)
        tex_path.write_text(tex, encoding="utf-8")
        write_cover_letter_md(draft, output_dir / "cover-letter.md")
    if html_template_validation.ok:
        html_path.write_text(render_template(html_template, build_html_mapping(draft)), encoding="utf-8")

    pdf_path, compile_warnings = print_html_pdf(html_path, output_dir) if html_path.exists() else (None, [])
    compile_validation = Validation([], compile_warnings)
    pdf_validation = validate_pdf(pdf_path)

    cv_validation = Validation([], ["No CV input provided; skipped cv-tailored.md."])
    if args.cv_input and args.cv_input.exists():
        cv_validation = build_cv_markdown(read_json(args.cv_input), output_dir / "cv-tailored.md")

    results = {
        "template": template_validation,
        "html_template": html_template_validation,
        "draft": draft_validation,
        "local_authoring": authoring_validation,
        "compile": compile_validation,
        "pdf": pdf_validation,
        "cv_markdown": cv_validation,
    }
    (output_dir / "validation.md").write_text(validation_markdown(results), encoding="utf-8")
    manifest = {
        "ok": all(result.ok for result in results.values()),
        "draft": str(args.draft),
        "template": str(template_path),
        "outputs": {
            "tex": str(tex_path) if tex_path.exists() else "",
            "html": str(html_path) if html_path.exists() else "",
            "pdf": str(pdf_path) if pdf_path else "",
            "cover_letter_md": str(output_dir / "cover-letter.md"),
            "cv_tailored_md": str(output_dir / "cv-tailored.md") if (output_dir / "cv-tailored.md").exists() else "",
            "validation": str(output_dir / "validation.md"),
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0 if manifest["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
