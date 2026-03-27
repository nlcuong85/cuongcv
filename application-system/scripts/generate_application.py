#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any
import re


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "application-system"
DATA_DIR = APP_ROOT / "data"
TEMPLATES_DIR = APP_ROOT / "templates"
DEFAULT_OUTPUTS_DIR = APP_ROOT / "outputs"
PUBLIC_CV_DATA_DIR = ROOT / "public" / "generated-cv-data"
CURRENT_PUBLIC_CV_PATH = PUBLIC_CV_DATA_DIR / "current.json"
DEFAULT_RENDER_BASE_URL = "http://127.0.0.1:3000/cuongcv"
CHROME_PATH = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2) + "\n")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "application"


def read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def render_template(template: str, mapping: dict[str, str]) -> str:
    rendered = template
    for key, value in mapping.items():
        rendered = rendered.replace(f"@@{key}@@", value)
    return rendered


def latex_escape(text: str) -> str:
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
    return "".join(replacements.get(char, char) for char in text)


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def sentence(text: str) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""
    if clean.endswith((".", "!", "?")):
        return clean
    return clean + "."


def paragraph(*parts: str) -> str:
    return " ".join(sentence(part) for part in parts if part.strip())


def get_role(role_profiles: dict[str, Any], role_id: str) -> dict[str, Any]:
    for role in role_profiles["roles"]:
        if role["id"] == role_id:
            return role
    raise KeyError(f"Unknown role preset: {role_id}")


def get_summary_versions(summary_versions: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {item["id"]: item for item in summary_versions["versions"]}


def requirements_blob(intake: dict[str, Any]) -> str:
    return (" ".join(intake.get("requirements", [])) + " " + intake.get("job_description", "")).lower()


def detect_summary_recommendations(intake: dict[str, Any], summary_versions: dict[str, Any]) -> list[str]:
    blob = requirements_blob(intake)
    scores = {
        "strongest_balanced": 0,
        "product_delivery": 0,
        "business_analysis": 0,
        "german_market_conservative": 0,
        "senior_confident": 0,
    }
    keyword_map = {
        "product_delivery": [
            "rollout",
            "launch",
            "delivery",
            "implementation",
            "lifecycle",
            "go-live",
            "release",
        ],
        "business_analysis": [
            "requirements",
            "workflow",
            "process",
            "documentation",
            "stakeholder interviews",
            "business analysis",
            "acceptance criteria",
        ],
        "german_market_conservative": [
            "structured",
            "reliable",
            "formal",
            "compliance",
            "regulated",
            "process discipline",
        ],
        "senior_confident": [
            "lead",
            "ownership",
            "strategy",
            "drive",
            "scale",
            "senior",
            "manager",
        ],
    }

    for summary_id, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in blob:
                scores[summary_id] += 1

    highest_non_default = max(
        (score for key, score in scores.items() if key != "strongest_balanced"),
        default=0,
    )
    if highest_non_default < 3:
        return []

    winners = [
        summary_id
        for summary_id, score in scores.items()
        if summary_id != "strongest_balanced" and score == highest_non_default
    ]
    if len(winners) > 2:
        return []
    return winners


def evidence_map(evidence_library: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in evidence_library["evidence"]}


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def select_evidence(
    intake: dict[str, Any],
    role: dict[str, Any],
    evidence_library: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_by_id = evidence_map(evidence_library)
    requirements_blob_text = requirements_blob(intake)

    keyword_boosts = {
        "ocr": "talosix_ocr_workflow",
        "healthcare": "talosix_ocr_workflow",
        "regulated": "anduin_regulated_onboarding",
        "onboarding": "anduin_regulated_onboarding",
        "marketplace": "scck_marketplace",
        "ecommerce": "scck_marketplace",
        "e-commerce": "scck_marketplace",
        "digital commerce": "scck_marketplace",
        "seller": "scck_marketplace",
        "business analysis": "nashtech_ba_foundation",
        "requirements": "nashtech_ba_foundation",
        "ai": "scck_marketplace",
        "automation": "talosix_ocr_workflow",
    }

    ordered_ids: list[str] = []
    for keyword, evidence_id in keyword_boosts.items():
        if keyword in requirements_blob_text and evidence_id not in ordered_ids:
            ordered_ids.append(evidence_id)

    for evidence_id in role["evidence_priority"]:
        if evidence_id not in ordered_ids:
            ordered_ids.append(evidence_id)

    return [evidence_by_id[item] for item in ordered_ids[:4]]


def jd_skill_candidates(intake: dict[str, Any]) -> list[str]:
    blob = requirements_blob(intake)
    keyword_skill_map = {
        "business analysis": "Business Analysis",
        "requirements": "Requirements Engineering",
        "acceptance criteria": "Acceptance Criteria",
        "documentation": "Documentation",
        "workflow": "Process Mapping",
        "process": "Operational Analysis",
        "stakeholder": "Stakeholder Interviews",
        "interviews": "Stakeholder Interviews",
        "ecommerce": "Product Roadmapping",
        "e-commerce": "Product Roadmapping",
        "digital commerce": "Product Roadmapping",
        "operations": "Operations-heavy Product Delivery",
        "delivery": "Cross-functional Delivery",
        "rollout": "Cross-functional Delivery",
        "launch": "Cross-functional Delivery",
        "backlog": "Requirement Prioritization",
        "jira": "Jira",
        "confluence": "Confluence",
        "sql": "SQL",
        "ai": "AI-assisted Product Workflows",
        "automation": "n8n Automation",
    }
    candidates: list[str] = []
    for keyword, skill in keyword_skill_map.items():
        if keyword in blob:
            candidates.append(skill)
    return candidates


def build_role_skills(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    total_skills: int = 14,
) -> list[str]:
    core_target = total_skills // 2
    adaptive_target = total_skills - core_target

    core_skills = unique_preserve_order(
        profile.get("core_skills", []) + profile.get("skills", [])
    )[:core_target]

    adaptive_candidates = unique_preserve_order(
        role.get("top_skills", []) + jd_skill_candidates(intake) + profile.get("skills", [])
    )
    adaptive_skills = [
        skill for skill in adaptive_candidates if skill not in core_skills
    ][:adaptive_target]

    if len(adaptive_skills) < adaptive_target:
        fallback = [
            skill
            for skill in unique_preserve_order(profile.get("skills", []) + role.get("top_skills", []))
            if skill not in core_skills and skill not in adaptive_skills
        ]
        adaptive_skills.extend(fallback[: adaptive_target - len(adaptive_skills)])

    return core_skills + adaptive_skills


def sender_lines(profile: dict[str, Any]) -> list[str]:
    return [
        profile["name"],
        profile["location"],
        profile["email"],
        profile["phone"],
        profile["website"],
    ]


def build_sender_block(profile: dict[str, Any]) -> str:
    return "\\\\\n".join(latex_escape(line) for line in sender_lines(profile))


def build_recipient_block(intake: dict[str, Any], latex_mode: bool) -> str:
    lines = []
    if intake.get("contact_name"):
        lines.append(intake["contact_name"])
    elif intake.get("contact_title"):
        lines.append(intake["contact_title"])
    else:
        lines.append("Hiring Team")
    lines.append(intake["company_name"])
    if intake.get("company_location"):
        lines.append(intake["company_location"])

    if latex_mode:
        return "\\\\\n".join(latex_escape(line) for line in lines)
    return "\n".join(html_escape(line) for line in lines)


def build_salutation(intake: dict[str, Any]) -> str:
    if intake.get("contact_name"):
        return f"Dear {intake['contact_name']},"
    return "Dear Hiring Team,"


def summarize_evidence_for_cover_letter(selected: list[dict[str, Any]]) -> tuple[str, str]:
    first = selected[0]
    second = selected[1] if len(selected) > 1 else selected[0]
    return (
        paragraph(
            f"In recent roles, I worked on products where {first['problem'].lower()}",
            first["actions"][0],
            first["actions"][1],
        ),
        paragraph(
            second["actions"][0],
            second["actions"][-1],
            second["results"][0],
        ),
    )


def build_cover_letter_context(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
) -> dict[str, str]:
    opening = paragraph(
        f"I am applying for the {intake['job_title']} position at {intake['company_name']}",
        profile["core_pitch"],
        intake["why_company"],
    )
    body_one, body_two = summarize_evidence_for_cover_letter(selected_evidence)
    closing = paragraph(
        "I am particularly interested in contributing in Germany because I value structured, systems-oriented environments where product work stays close to real operational outcomes",
        f"I would welcome the opportunity to discuss how my background can support {intake['company_name']}",
        f"My availability would be {intake['start_date']}",
    )

    return {
        "SENDER_BLOCK": build_sender_block(profile),
        "RECIPIENT_BLOCK": build_recipient_block(intake, latex_mode=True),
        "DATE_LINE": latex_escape(date.today().strftime("%d %B %Y")),
        "JOB_TITLE": latex_escape(intake["job_title"]),
        "SALUTATION": latex_escape(build_salutation(intake)),
        "OPENING_PARAGRAPH": latex_escape(opening),
        "BODY_PARAGRAPH_ONE": latex_escape(body_one),
        "BODY_PARAGRAPH_TWO": latex_escape(body_two),
        "CLOSING_PARAGRAPH": latex_escape(closing),
        "SIGNATURE_NAME": latex_escape(profile["name"]),
        "ROLE_LABEL": latex_escape(role["label"]),
        "EVIDENCE_IDS": latex_escape(", ".join(item["id"] for item in selected_evidence)),
        "COMPANY_NAME": latex_escape(intake["company_name"]),
    }


def build_cover_letter_html_context(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
) -> dict[str, str]:
    plain_opening = paragraph(
        f"I am applying for the {intake['job_title']} position at {intake['company_name']}",
        profile["core_pitch"],
        intake["why_company"],
    )
    plain_body_one, plain_body_two = summarize_evidence_for_cover_letter(selected_evidence)
    plain_closing = paragraph(
        "I am particularly interested in contributing in Germany because I value structured, systems-oriented environments where product work stays close to real operational outcomes",
        f"I would welcome the opportunity to discuss how my background can support {intake['company_name']}",
        f"My availability would be {intake['start_date']}",
    )
    return {
        "SENDER_BLOCK": html_escape("\n".join(sender_lines(profile))),
        "RECIPIENT_BLOCK": build_recipient_block(intake, latex_mode=False),
        "DATE_LINE": html_escape(date.today().strftime("%d %B %Y")),
        "JOB_TITLE": html_escape(intake["job_title"]),
        "SALUTATION": html_escape(build_salutation(intake)),
        "OPENING_PARAGRAPH": html_escape(plain_opening),
        "BODY_PARAGRAPH_ONE": html_escape(plain_body_one),
        "BODY_PARAGRAPH_TWO": html_escape(plain_body_two),
        "CLOSING_PARAGRAPH": html_escape(plain_closing),
        "SIGNATURE_NAME": html_escape(profile["name"]),
        "ROLE_LABEL": html_escape(role["label"]),
        "EVIDENCE_IDS": html_escape(", ".join(item["id"] for item in selected_evidence)),
        "COMPANY_NAME": html_escape(intake["company_name"]),
    }


def compile_tex(tex_path: Path) -> None:
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_path.name,
        ],
        cwd=tex_path.parent,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def build_generated_resume_data(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
    summary_text: str,
) -> dict[str, Any]:
    work_items = []
    company_links = {
        "Kyanon Digital": "https://kyanon.digital/",
        "SCCK.vn": "https://scck.vn/",
        "Anduin Transaction": "https://www.anduintransact.com/",
        "Talosix": "https://www.talosix.com/",
        "NashTech Global": "https://www.nashtechglobal.com/",
    }

    for job in profile["work_history"]:
        work_items.append(
            {
                "company": job.get("company_label", job["company"]),
                "link": company_links.get(job["company"], profile["website"]),
                "badges": job.get("badges", []),
                "title": job["title"],
                "start": job["start"],
                "end": job["end"],
                "overview": job.get("overview"),
                "bullets": job.get("bullets", []),
            }
        )

    projects = [
        {
            "title": project["name"],
            "techStack": project["tech_stack"],
            "description": project["description"],
        }
        for project in profile["projects"]
    ]

    role_skills = build_role_skills(profile, role, intake)

    return {
        "name": profile["name"],
        "initials": profile["initials"],
        "location": profile["location"],
        "locationLink": profile["location_link"],
        "about": role.get("about", profile["headline"]),
        "summary": summary_text,
        "avatarUrl": profile["avatar_url"],
        "personalWebsiteUrl": profile["website"],
        "contact": {
            "email": profile["email"],
            "tel": profile["phone"],
            "social": [
                {"name": "GitHub", "url": profile["github"], "icon": "github"},
                {"name": "LinkedIn", "url": profile["linkedin"], "icon": "linkedin"},
            ],
        },
        "education": profile["education"],
        "work": work_items,
        "skills": role_skills,
        "awards": profile.get("awards", []),
        "projects": projects,
    }


def wait_for_url(url: str, timeout_seconds: int = 45) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status < 500:
                    return
        except urllib.error.URLError:
            time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}")


def ensure_render_server(render_base_url: str) -> subprocess.Popen[str] | None:
    try:
        wait_for_url(render_base_url, timeout_seconds=2)
        return None
    except RuntimeError:
        process = subprocess.Popen(
            ["pnpm", "dev"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        wait_for_url(render_base_url, timeout_seconds=60)
        return process


def print_cv_pdf(render_url: str, pdf_path: Path) -> None:
    if not CHROME_PATH.exists():
        raise FileNotFoundError(f"Google Chrome not found at {CHROME_PATH}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(CHROME_PATH),
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--virtual-time-budget=8000",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            render_url,
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def get_pdf_page_count(pdf_path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not determine page count for {pdf_path}")
    return int(match.group(1))


def build_notes(
    intake: dict[str, Any],
    selected_for_cover_letter: list[dict[str, Any]],
    generated_roles: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Application Notes for {intake['company_name']}",
        "",
        "## Primary role",
        f"- {intake['primary_role']}",
        "",
        "## Cover-letter evidence used",
    ]
    for item in selected_for_cover_letter:
        lines.append(f"- {item['id']}: {item['title']}")
    lines.extend(
        [
            "",
            "## CV variants generated",
        ]
    )
    for role in generated_roles:
        lines.append(f"- {role['id']}: {role['label']}")
    lines.extend(
        [
            "",
            "## Human review checklist",
            "- Verify hiring contact and salutation.",
            "- Confirm the role preset that best matches the target job.",
            "- Check whether salary expectations are requested in the job ad.",
            "- Trim or add evidence if the company is highly specialized.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a cover letter and requested CV variant outputs.")
    parser.add_argument("--intake", required=True, help="Path to intake JSON.")
    parser.add_argument("--output", help="Custom output directory.")
    parser.add_argument("--compile-pdf", action="store_true", help="Compile cover letter PDF and print CV PDF.")
    parser.add_argument("--render-base-url", default=DEFAULT_RENDER_BASE_URL, help="Base URL for the local CV print route.")
    args = parser.parse_args()

    intake_path = Path(args.intake).resolve()
    intake = load_json(intake_path)
    profile = load_json(DATA_DIR / "master_profile.json")
    role_profiles = load_json(DATA_DIR / "role_profiles.json")
    evidence_library = load_json(DATA_DIR / "evidence_library.json")
    summary_versions = load_json(DATA_DIR / "summary_versions.json")
    summary_version_map = get_summary_versions(summary_versions)

    recommended_summary_versions = detect_summary_recommendations(intake, summary_versions)
    selected_summary_version = intake.get("summary_version") or summary_versions["default"]
    if recommended_summary_versions and "summary_version" not in intake:
        options = ", ".join(recommended_summary_versions)
        raise SystemExit(
            "This JD suggests a non-default CV summary style. "
            f"Please choose one of: {options}. "
            f"Available options: {', '.join(summary_version_map.keys())}. "
            "Add it as `summary_version` in the intake JSON and rerun."
        )
    if selected_summary_version not in summary_version_map:
        raise SystemExit(
            f"Unknown summary_version `{selected_summary_version}`. "
            f"Valid options: {', '.join(summary_version_map.keys())}."
        )
    selected_summary = summary_version_map[selected_summary_version]

    primary_role = get_role(role_profiles, intake["primary_role"])
    target_role_ids = intake.get("target_roles") or [intake["primary_role"]]
    target_roles = [get_role(role_profiles, role_id) for role_id in target_role_ids]

    company_slug = slugify(intake["company_name"])
    output_root = Path(args.output).resolve() if args.output else DEFAULT_OUTPUTS_DIR / company_slug
    cover_letter_dir = output_root / "cover-letter"
    cv_dir = output_root / "cv"

    selected_for_cover_letter = select_evidence(intake, primary_role, evidence_library)
    cover_letter_context = build_cover_letter_context(profile, primary_role, intake, selected_for_cover_letter)
    cover_letter_html_context = build_cover_letter_html_context(profile, primary_role, intake, selected_for_cover_letter)

    write_text(
        cover_letter_dir / "cover_letter.tex",
        render_template(read_template("cover_letter.tex"), cover_letter_context),
    )
    write_text(
        cover_letter_dir / "cover_letter.html",
        render_template(read_template("cover_letter_preview.html"), cover_letter_html_context),
    )

    manifest: dict[str, Any] = {
        "company_name": intake["company_name"],
        "job_title": intake["job_title"],
        "primary_role": primary_role["id"],
        "summary_version": selected_summary["id"],
        "cover_letter_evidence": [item["id"] for item in selected_for_cover_letter],
        "cv_variants": [],
    }

    dev_server_process: subprocess.Popen[str] | None = None
    if args.compile_pdf:
        dev_server_process = ensure_render_server(args.render_base_url)

    for role in target_roles:
        selected_for_cv = select_evidence(intake, role, evidence_library)
        role_payload = build_generated_resume_data(
            profile,
            role,
            intake,
            selected_for_cv,
            selected_summary["text"],
        )
        json_path = cv_dir / f"{role['id']}.json"
        public_json_path = PUBLIC_CV_DATA_DIR / company_slug / f"{role['id']}.json"
        write_json(json_path, role_payload)
        write_json(public_json_path, role_payload)
        write_json(CURRENT_PUBLIC_CV_PATH, role_payload)

        render_url = f"{args.render_base_url}/generated-cv/"
        pdf_path = cv_dir / f"{role['id']}.pdf"
        if args.compile_pdf:
            print_cv_pdf(render_url, pdf_path)
            page_count = get_pdf_page_count(pdf_path)
            if page_count > 2:
                raise SystemExit(
                    f"Generated CV PDF `{pdf_path}` is {page_count} pages. "
                    "CV outputs must stay within 2 pages."
                )

        manifest["cv_variants"].append(
            {
                "role_id": role["id"],
                "role_label": role["label"],
                "summary_version": selected_summary["id"],
                "evidence": [item["id"] for item in selected_for_cv],
                "skills": role_payload["skills"],
                "json_path": str(json_path.relative_to(ROOT)),
                "public_json_path": str(public_json_path.relative_to(ROOT)),
                "render_url": render_url,
                "pdf_path": str(pdf_path.relative_to(ROOT)) if args.compile_pdf else None,
            }
        )

    if args.compile_pdf:
        compile_tex(cover_letter_dir / "cover_letter.tex")
        if dev_server_process is not None:
            dev_server_process.terminate()
            try:
                dev_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dev_server_process.kill()

    write_json(output_root / "manifest.json", manifest)
    write_text(output_root / "notes.md", build_notes(intake, selected_for_cover_letter, target_roles))

    print(f"Generated application package at {output_root}")


if __name__ == "__main__":
    main()
