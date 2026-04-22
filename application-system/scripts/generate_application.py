#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import re
import shutil
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "application-system"
DATA_DIR = APP_ROOT / "data"
TEMPLATES_DIR = APP_ROOT / "templates"
DEFAULT_OUTPUTS_DIR = APP_ROOT / "outputs"
PUBLIC_CV_DATA_DIR = ROOT / "public" / "generated-cv-data"
CURRENT_PUBLIC_CV_PATH = PUBLIC_CV_DATA_DIR / "current.json"
DEFAULT_RENDER_BASE_URL = "http://127.0.0.1:3000/cuongcv"
CHROME_PATH = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

SNAPSHOT_AXIS_DEFS = [
    {
        "id": "requirements_analysis",
        "label": "Requirements & Analysis",
        "focus": "requirements, acceptance criteria, and stakeholder translation",
        "base": 3.5,
        "color": "#2B6CB0",
        "preferred_evidence": [
            "nashtech_ba_foundation",
            "anduin_regulated_onboarding",
            "kyanon_superapp_delivery",
        ],
        "role_boosts": {
            "business_analyst": 0.3,
            "requirements_process": 0.4,
            "product_owner": 0.2,
            "workflow_operations_analyst": 0.3,
            "implementation_enablement": 0.1,
            "quality_compliance_ops": 0.1,
        },
        "group_boosts": {
            "requirements_process": 0.3,
            "workflow_operations": 0.2,
            "process_digitalization": 0.1,
            "quality_test_compliance": 0.1,
        },
    },
    {
        "id": "process_workflow",
        "label": "Process & Workflow Design",
        "focus": "workflow mapping, process improvement, and digitalization support",
        "base": 3.4,
        "color": "#2F855A",
        "preferred_evidence": [
            "scck_marketplace",
            "talosix_ocr_workflow",
            "anduin_regulated_onboarding",
        ],
        "role_boosts": {
            "requirements_process": 0.2,
            "process_automation": 0.4,
            "business_analyst": 0.2,
            "workflow_operations_analyst": 0.4,
            "implementation_enablement": 0.2,
            "quality_compliance_ops": 0.2,
        },
        "group_boosts": {
            "requirements_process": 0.2,
            "process_digitalization": 0.3,
            "workflow_operations": 0.3,
            "implementation_enablement": 0.2,
            "quality_test_compliance": 0.1,
            "ai_workflow_automation": 0.1,
        },
    },
    {
        "id": "delivery_coordination",
        "label": "Delivery & Stakeholder Coordination",
        "focus": "rollout, coordination, and cross-functional execution discipline",
        "base": 3.6,
        "color": "#B7791F",
        "preferred_evidence": [
            "kyanon_superapp_delivery",
            "anduin_regulated_onboarding",
            "scck_marketplace",
        ],
        "role_boosts": {
            "product_manager": 0.2,
            "product_owner": 0.3,
            "business_analyst": 0.1,
            "pmo_delivery_support": 0.6,
            "implementation_enablement": 0.5,
            "workflow_operations_analyst": 0.2,
            "quality_compliance_ops": 0.2,
        },
        "group_boosts": {
            "pmo_delivery": 0.3,
            "implementation_enablement": 0.3,
            "workflow_operations": 0.1,
            "process_digitalization": 0.1,
            "quality_test_compliance": 0.1,
        },
    },
    {
        "id": "ai_workflow_automation",
        "label": "AI Workflow & Automation",
        "focus": "AI-assisted workflow design, automation thinking, and practical tooling",
        "base": 2.8,
        "color": "#805AD5",
        "preferred_evidence": [
            "portfolio_ai_workflow_systems",
            "scck_marketplace",
            "talosix_ocr_workflow",
        ],
        "role_boosts": {
            "product_manager": 0.1,
            "process_automation": 0.3,
            "workflow_operations_analyst": 0.1,
            "ai_product_ops": 0.5,
        },
        "group_boosts": {
            "process_digitalization": 0.1,
            "workflow_operations": 0.1,
            "ai_workflow_automation": 0.4,
        },
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2) + "\n")


def path_for_manifest(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "application"


def file_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "document"


def package_slug(intake: dict[str, Any]) -> str:
    return slugify(f"{intake['company_name']}-{intake['job_title']}")


def render_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def build_pdf_filename(prefix: str, profile: dict[str, Any], intake: dict[str, Any], timestamp: str) -> str:
    return (
        f"{prefix}-"
        f"{file_slug(profile['name'])}-"
        f"{file_slug(intake['job_title'])}-"
        f"{timestamp}.pdf"
    )


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


def normalize_text_for_ats(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\ufeff": "",
        "\u00df": "ss",
    }
    normalized = "".join(replacements.get(char, char) for char in text)
    normalized = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_payload_for_ats(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_text_for_ats(value)
    if isinstance(value, list):
        return [normalize_payload_for_ats(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_payload_for_ats(item) for key, item in value.items()}
    return value


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


def get_taxonomy_groups(taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in taxonomy.get("groups", []) if isinstance(item, dict)]


def requirements_blob(intake: dict[str, Any]) -> str:
    return (
        " ".join(
            [
                intake.get("job_title", ""),
                " ".join(intake.get("requirements", [])),
                intake.get("job_description", ""),
            ]
        )
    ).lower()


def matched_taxonomy_groups(intake: dict[str, Any], taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    blob = requirements_blob(intake)
    matches: list[dict[str, Any]] = []
    for group in get_taxonomy_groups(taxonomy):
        keywords = [str(item).lower() for item in group.get("keywords", [])]
        if any(keyword in blob for keyword in keywords):
            matches.append(group)
    return matches


def detect_summary_recommendations(
    intake: dict[str, Any],
    summary_versions: dict[str, Any],
    taxonomy: dict[str, Any],
) -> list[str]:
    blob = requirements_blob(intake)
    scores = {item["id"]: 0 for item in summary_versions["versions"]}
    keyword_map = {
        "product_delivery": [
            "rollout",
            "launch",
            "delivery",
            "implementation",
            "enablement",
            "onboarding",
            "lifecycle",
            "go-live",
            "release",
        ],
        "business_analysis": [
            "requirements",
            "workflow",
            "process",
            "documentation",
            "workflow analyst",
            "operations analyst",
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

    for group in matched_taxonomy_groups(intake, taxonomy):
        for summary_id, increment in group.get("summary_scores", {}).items():
            if summary_id in scores:
                scores[summary_id] += int(increment)

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
    taxonomy: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_by_id = evidence_map(evidence_library)
    requirements_blob_text = requirements_blob(intake)

    ordered_ids: list[str] = []
    for group in matched_taxonomy_groups(intake, taxonomy):
        for evidence_id in group.get("evidence_boosts", []):
            if evidence_id in evidence_by_id and evidence_id not in ordered_ids:
                ordered_ids.append(evidence_id)

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
        "ai": "portfolio_ai_workflow_systems",
        "automation": "portfolio_ai_workflow_systems",
    }
    for keyword, evidence_id in keyword_boosts.items():
        if keyword in requirements_blob_text and evidence_id in evidence_by_id and evidence_id not in ordered_ids:
            ordered_ids.append(evidence_id)

    for evidence_id in role["evidence_priority"]:
        if evidence_id not in ordered_ids:
            ordered_ids.append(evidence_id)

    return [evidence_by_id[item] for item in ordered_ids[:4]]


def verified_skill_inventory(profile: dict[str, Any], role: dict[str, Any]) -> list[str]:
    return unique_preserve_order(
        profile.get("core_skills", []) + profile.get("skills", []) + role.get("top_skills", [])
    )


def jd_skill_candidates(
    intake: dict[str, Any],
    taxonomy: dict[str, Any],
    profile: dict[str, Any],
    role: dict[str, Any],
) -> list[str]:
    blob = requirements_blob(intake)
    candidates: list[str] = []
    for group in matched_taxonomy_groups(intake, taxonomy):
        candidates.extend(str(skill) for skill in group.get("skills", []))

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
        "implementation": "Project Coordination",
        "enablement": "Project Coordination",
        "onboarding": "Project Coordination",
        "handover": "Project Coordination",
        "backlog": "Requirement Prioritization",
        "jira": "Jira",
        "confluence": "Confluence",
        "sql": "SQL",
        "python": "Python",
        "cloud": "Cloud Cost Analysis",
        "finops": "Cloud Cost Analysis",
        "cost optimization": "Technical Cost Optimization",
        "analytics": "Data Analysis",
        "data analysis": "Data Analysis",
        "dashboard": "Dashboarding",
        "monitoring": "Monitoring and Reporting",
        "reporting": "Monitoring and Reporting",
        "excel": "Excel",
        "powerpoint": "PowerPoint",
        "governance": "Process Governance",
        "tagging": "Resource Structuring",
        "architecture": "Systems Thinking",
        "ai": "AI-assisted Product Workflows",
        "automation": "n8n Automation",
    }
    for keyword, skill in keyword_skill_map.items():
        if keyword in blob:
            candidates.append(skill)
    verified = set(verified_skill_inventory(profile, role))
    return [skill for skill in unique_preserve_order(candidates) if skill in verified]


def build_role_skills(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    taxonomy: dict[str, Any],
    total_skills: int = 14,
) -> list[str]:
    core_target = total_skills // 2
    adaptive_target = total_skills - core_target

    core_skills = unique_preserve_order(
        profile.get("core_skills", []) + profile.get("skills", [])
    )[:core_target]

    adaptive_candidates = unique_preserve_order(
        role.get("top_skills", []) + jd_skill_candidates(intake, taxonomy, profile, role) + profile.get("skills", [])
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
    location_lines = split_address_lines(profile["location"])
    return [profile["name"], *location_lines, profile["phone"], profile["email"]]


def split_address_lines(value: str) -> list[str]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if parts and parts[-1].lower() in {"germany", "deutschland"}:
        parts = parts[:-1]
    if len(parts) >= 3:
        return [", ".join(parts[:-1]), parts[-1]]
    if len(parts) == 2:
        return [parts[0], parts[1]]
    return [value]


def join_lines(lines: list[str], latex_mode: bool) -> str:
    if latex_mode:
        return "\\\\\n".join(latex_escape(line) for line in lines)
    return "\n".join(html_escape(line) for line in lines)


def build_sender_block(profile: dict[str, Any], latex_mode: bool) -> str:
    return join_lines(sender_lines(profile), latex_mode)


def build_snapshot_contact_block(profile: dict[str, Any], latex_mode: bool) -> str:
    location_lines = split_address_lines(profile["location"])
    lines = [profile["name"]]
    lines.extend(location_lines[:2] if location_lines else [profile["location"]])
    lines.extend([profile["phone"], profile["email"]])
    return join_lines(lines, latex_mode)


def join_inline_items(values: list[str], latex_mode: bool) -> str:
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    if latex_mode:
        return r" \textbullet{} ".join(latex_escape(item) for item in cleaned)
    return " &bull; ".join(html_escape(item) for item in cleaned)


def preferred_contact_line(intake: dict[str, Any]) -> str:
    if intake.get("contact_name"):
        return intake["contact_name"]
    if intake.get("contact_title"):
        return intake["contact_title"]
    return "Hiring Team"


def build_recipient_block(intake: dict[str, Any], latex_mode: bool) -> str:
    lines = [intake["company_name"], preferred_contact_line(intake)]
    if intake.get("company_location"):
        lines.extend(split_address_lines(intake["company_location"]))
    return join_lines(lines, latex_mode)


def build_snapshot_target_block(intake: dict[str, Any], latex_mode: bool) -> str:
    lines = [intake["company_name"], intake["job_title"]]
    if intake.get("company_location"):
        lines.extend(split_address_lines(intake["company_location"]))
    return join_lines(lines, latex_mode)


def build_salutation(intake: dict[str, Any]) -> str:
    if intake.get("contact_name"):
        return f"Dear {intake['contact_name']},"
    return "Dear Hiring Team,"


def subject_line(intake: dict[str, Any]) -> str:
    if intake.get("subject_line"):
        return str(intake["subject_line"]).strip()
    return f"Application for {intake['job_title']}"


def date_line(profile: dict[str, Any]) -> str:
    location_lines = split_address_lines(profile["location"])
    city_line = location_lines[-1] if location_lines else profile["location"]
    location_city = re.sub(r"^\d{4,5}\s+", "", city_line).strip()
    return f"{location_city}, {date.today().strftime('%d %B %Y')}"


def signature_path() -> str:
    return str((APP_ROOT / "signature.png").resolve())


def next_available_start(today: date | None = None) -> date:
    current = today or date.today()
    return current + timedelta(days=14)


def default_availability_sentence() -> str:
    start = next_available_start()
    return (
        f"I am available to start from {start.strftime('%d %B %Y')} "
        "and can work up to 20 hours per week in line with my current student visa"
    )


def start_date_sentence(intake: dict[str, Any]) -> str:
    override = (intake.get("availability_override") or "").strip()
    if override:
        return override

    value = (intake.get("start_date") or "").strip()
    if not value:
        return default_availability_sentence()
    if value.lower() in {"by mutual agreement", "mutual agreement", "negotiable"}:
        return default_availability_sentence()
    return f"I am available to start {value}"


def apply_availability_placeholder(text: str, intake: dict[str, Any]) -> str:
    return text.replace("@@AVAILABILITY@@", start_date_sentence(intake))


def enclosure_lines(intake: dict[str, Any]) -> list[str]:
    values = intake.get("enclosures") or [
        "Curriculum Vitae",
        "Bachelor Degree Diploma",
        "Reference letter from previous employers",
    ]
    return [str(item).strip() for item in values if str(item).strip()]


def summarize_evidence_for_cover_letter(selected: list[dict[str, Any]]) -> tuple[str, str]:
    first = selected[0]
    second = selected[1] if len(selected) > 1 else selected[0]
    return (
        paragraph(
            "In previous roles, I was usually most useful when work sat between process clarity and execution discipline",
            first["actions"][0],
            first["results"][0],
        ),
        paragraph(
            "That experience fits roles where the work is not abstract strategy, but making sure changes are understood, implemented carefully, and useful in day-to-day operations",
            second["actions"][0],
            second["results"][0],
        ),
    )


def contribution_sentence(role: dict[str, Any]) -> str:
    strengths = [str(item).strip() for item in role.get("cover_letter_strengths", []) if str(item).strip()]
    if len(strengths) >= 3:
        return f"I believe I can contribute most through {strengths[0]}, {strengths[1]}, and {strengths[2]}"
    if len(strengths) == 2:
        return f"I believe I can contribute most through {strengths[0]} and {strengths[1]}"
    if len(strengths) == 1:
        return f"I believe I can contribute most through {strengths[0]}"
    return "I believe I can contribute most through structured business analysis, clear requirement definition, and reliable operational follow-through"


def source_line_for_job(intake: dict[str, Any]) -> str:
    url = str(intake.get("job_url", "")).lower()
    if "bosch.com" in url:
        return "After reading the role on the Bosch careers page, I wanted to apply."
    if "mercedes-benz.com" in url:
        return "After reading the role on the Mercedes-Benz careers page, I wanted to apply."
    if "jobs.sap.com" in url:
        return "After reading the role on the SAP careers page, I wanted to apply."
    if "linkedin.com" in url:
        return "After reading the role description more carefully, I wanted to apply."
    if "stepstone" in url or "arbeitnow" in url or "indeed" in url:
        return "After reading the job description more carefully, I wanted to apply."
    return "After reading the job description, I wanted to apply."


def role_hook_sentence(intake: dict[str, Any], role: dict[str, Any]) -> str:
    strengths = [str(item).strip() for item in role.get("cover_letter_strengths", []) if str(item).strip()]
    if len(strengths) >= 3:
        return f"It fits how I work best because it stays close to {strengths[0]}, {strengths[1]}, and {strengths[2]}."
    if len(strengths) == 2:
        return f"It fits how I work best because it stays close to {strengths[0]} and {strengths[1]}."
    return f"It fits how I work best because it stays close to {role.get('label', 'structured digital work').lower()}."


def extract_concrete_role_focus(intake: dict[str, Any]) -> str:
    description = " ".join(str(intake.get("job_description", "")).split())
    patterns = [
        r"\bThe role focuses on ([^.]+)\.",
        r"\bThe role involves ([^.]+)\.",
        r"\bThe role supports ([^.]+)\.",
        r"\bThe role combines ([^.]+)\.",
        r"\bThe role centers on ([^.]+)\.",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def concrete_trigger_sentence(intake: dict[str, Any]) -> str:
    focus = extract_concrete_role_focus(intake)
    if focus:
        return f"What caught my attention immediately is that the work is concrete: {focus}"
    return "What caught my attention immediately is that the work itself sounds concrete, useful, and close to real operations"


def build_authentic_opening(intake: dict[str, Any], role: dict[str, Any], application_voice: dict[str, Any]) -> str:
    _ = application_voice
    return paragraph(
        f"I wanted to apply for the {intake['job_title']} role at {intake['company_name']}",
        concrete_trigger_sentence(intake),
        role_hook_sentence(intake, role),
    )


def build_authentic_motivation(intake: dict[str, Any], role: dict[str, Any], application_voice: dict[str, Any]) -> str:
    _ = application_voice
    return paragraph(
        intake["why_company"],
        f"That matters to me because I do my best work in roles where the value is practical, the contribution is visible, and the learning stays tied to real operations rather than abstract ownership.",
    )


def build_authentic_closing(intake: dict[str, Any], application_voice: dict[str, Any]) -> str:
    _ = application_voice
    return paragraph(
        "Thank you for considering my application.",
        start_date_sentence(intake),
        f"I would be glad to discuss how I can support {intake['company_name']} in this role.",
    )


def build_cover_letter_context(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
    authentic_voice: dict[str, Any],
) -> dict[str, str]:
    application_voice = authentic_voice.get("application_voice", {})
    opening = intake.get("cover_letter_opening") or build_authentic_opening(intake, role, application_voice)
    body_one, body_two = summarize_evidence_for_cover_letter(selected_evidence)
    body_one = intake.get("cover_letter_body_one") or body_one
    body_two = intake.get("cover_letter_body_two") or body_two
    motivation = intake.get("cover_letter_motivation") or build_authentic_motivation(intake, role, application_voice)
    custom_closing = intake.get("cover_letter_closing")
    closing = apply_availability_placeholder(custom_closing, intake) if custom_closing else build_authentic_closing(intake, application_voice)

    return {
        "SENDER_BLOCK": build_sender_block(profile, latex_mode=True),
        "RECIPIENT_BLOCK": build_recipient_block(intake, latex_mode=True),
        "DATE_LINE": latex_escape(date_line(profile)),
        "SUBJECT_LINE": latex_escape(subject_line(intake)),
        "SALUTATION": latex_escape(build_salutation(intake)),
        "OPENING_PARAGRAPH": latex_escape(opening),
        "BODY_PARAGRAPH_ONE": latex_escape(body_one),
        "BODY_PARAGRAPH_TWO": latex_escape(body_two),
        "MOTIVATION_PARAGRAPH": latex_escape(motivation),
        "CLOSING_PARAGRAPH": latex_escape(closing),
        "SIGNATURE_NAME": latex_escape(profile["name"]),
        "SIGNATURE_PATH": latex_escape(signature_path()),
        "ENCLOSURES": latex_escape(", ".join(enclosure_lines(intake))),
        "ROLE_LABEL": latex_escape(role["label"]),
        "EVIDENCE_IDS": latex_escape(", ".join(item["id"] for item in selected_evidence)),
        "COMPANY_NAME": latex_escape(intake["company_name"]),
        "CONTACT_LOOKUP_STATUS": latex_escape(
            "named contact found" if intake.get("contact_name") else "fallback to hiring team after no named recruiter was available"
        ),
    }


def build_cover_letter_html_context(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
    authentic_voice: dict[str, Any],
) -> dict[str, str]:
    application_voice = authentic_voice.get("application_voice", {})
    plain_opening = intake.get("cover_letter_opening") or build_authentic_opening(intake, role, application_voice)
    plain_body_one, plain_body_two = summarize_evidence_for_cover_letter(selected_evidence)
    plain_body_one = intake.get("cover_letter_body_one") or plain_body_one
    plain_body_two = intake.get("cover_letter_body_two") or plain_body_two
    motivation = intake.get("cover_letter_motivation") or build_authentic_motivation(intake, role, application_voice)
    custom_closing = intake.get("cover_letter_closing")
    plain_closing = apply_availability_placeholder(custom_closing, intake) if custom_closing else build_authentic_closing(intake, application_voice)
    return {
        "SENDER_BLOCK": build_sender_block(profile, latex_mode=False),
        "RECIPIENT_BLOCK": build_recipient_block(intake, latex_mode=False),
        "DATE_LINE": html_escape(date_line(profile)),
        "SUBJECT_LINE": html_escape(subject_line(intake)),
        "SALUTATION": html_escape(build_salutation(intake)),
        "OPENING_PARAGRAPH": html_escape(plain_opening),
        "BODY_PARAGRAPH_ONE": html_escape(plain_body_one),
        "BODY_PARAGRAPH_TWO": html_escape(plain_body_two),
        "MOTIVATION_PARAGRAPH": html_escape(motivation),
        "CLOSING_PARAGRAPH": html_escape(plain_closing),
        "SIGNATURE_NAME": html_escape(profile["name"]),
        "SIGNATURE_PATH": html_escape(signature_path()),
        "ENCLOSURES": html_escape(", ".join(enclosure_lines(intake))),
        "ROLE_LABEL": html_escape(role["label"]),
        "EVIDENCE_IDS": html_escape(", ".join(item["id"] for item in selected_evidence)),
        "COMPANY_NAME": html_escape(intake["company_name"]),
        "CONTACT_LOOKUP_STATUS": html_escape(
            "named contact found" if intake.get("contact_name") else "fallback to hiring team after no named recruiter was available"
        ),
    }


def clamp_score(value: float, low: float = 2.6, high: float = 4.4) -> float:
    return max(low, min(high, value))


def matched_group_ids(intake: dict[str, Any], taxonomy: dict[str, Any]) -> set[str]:
    return {group["id"] for group in matched_taxonomy_groups(intake, taxonomy)}


def companies_for_axis(axis: dict[str, Any], selected_evidence: list[dict[str, Any]]) -> list[str]:
    preferred = axis.get("preferred_evidence", [])
    companies: list[str] = []
    for evidence_id in preferred:
        for item in selected_evidence:
            if item.get("id") == evidence_id:
                company = str(item.get("company") or item.get("role") or "").strip()
                if company and company not in companies:
                    companies.append(company)
    if companies:
        return companies[:2]
    for item in selected_evidence:
        company = str(item.get("company") or item.get("role") or "").strip()
        if company and company not in companies:
            companies.append(company)
    return companies[:2]


def short_company_name(value: str) -> str:
    cleaned = re.sub(r"\s+[–-].*$", "", value).strip()
    replacements = {
        "Anduin Transaction": "Anduin",
        "Kyanon Digital": "Kyanon",
        "NashTech": "NashTech",
        "SCCK.vn": "SCCK.vn",
        "Talosix": "Talosix",
        "Portfolio": "Portfolio",
    }
    return replacements.get(cleaned, cleaned)


def sentence_case_preserve(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return stripped[0].upper() + stripped[1:]


def snapshot_signature_path() -> str:
    return signature_path()


def score_snapshot_axes(
    role: dict[str, Any],
    intake: dict[str, Any],
    taxonomy: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    group_ids = matched_group_ids(intake, taxonomy)
    blob = requirements_blob(intake)
    axes: list[dict[str, Any]] = []
    for axis in SNAPSHOT_AXIS_DEFS:
        score = float(axis["base"])
        score += float(axis.get("role_boosts", {}).get(role["id"], 0.0))
        for group_id in group_ids:
            score += float(axis.get("group_boosts", {}).get(group_id, 0.0))
        if any(item.get("id") in axis.get("preferred_evidence", []) for item in selected_evidence):
            score += 0.1
        if axis["id"] == "delivery_coordination" and ("good knowledge of german" in blob or "german and english" in blob or "deutsch" in blob):
            score -= 0.3
        score = round(clamp_score(score), 1)
        companies = [short_company_name(item) for item in companies_for_axis(axis, selected_evidence)]
        evidence_line = ", ".join(companies) if companies else "Portfolio and delivery history"
        if axis["id"] == "requirements_analysis":
            if "quality_test_compliance" in group_ids or "aspice" in blob or "automotive spice" in blob:
                note = (
                    "This fit is strongest when the role needs traceable documentation, structured handovers, and "
                    f"requirement clarity that can stand up to compliance-heavy delivery, as in {evidence_line}."
                )
            elif "workflow_operations" in group_ids:
                note = (
                    "This fit is strongest when the role needs workflow analysis that turns messy operating routines, "
                    f"handoffs, and reporting needs into clear documentation across {evidence_line}."
                )
            elif "pmo_delivery" in group_ids:
                note = (
                    "My evidence here is less about formal requirements theory and more about turning stakeholder "
                    f"inputs into documented priorities, decision-ready notes, and delivery structure across {evidence_line}."
                )
            else:
                note = (
                    "Strongest evidence comes from translating stakeholder needs into user stories, acceptance criteria, "
                    f"and delivery-ready documentation across {evidence_line}."
                )
        elif axis["id"] == "process_workflow":
            if "process_digitalization" in group_ids:
                note = (
                    "This is the most direct fit for the posting. My experience here comes from workflow cleanup, "
                    f"operating logic, and structured process improvement in {evidence_line}."
                )
            elif "workflow_operations" in group_ids:
                note = (
                    "This area maps well when the role is closer to workflow ownership, operating routines, or process support, "
                    f"because that is the kind of structure I have worked with in {evidence_line}."
                )
            elif "implementation_enablement" in group_ids:
                note = (
                    "What maps well here is turning process logic into rollout-ready steps, adoption support, and cleaner handoffs, "
                    f"which I have done in {evidence_line}."
                )
            elif "quality_test_compliance" in group_ids:
                note = (
                    "What maps well here is not only process design but also making ways of working explicit, "
                    f"repeatable, and reviewable in environments like {evidence_line}."
                )
            elif "ai_workflow_automation" in group_ids:
                note = (
                    "This area becomes stronger when the role expects process design with automation thinking, since "
                    f"I have used workflow structuring and tooling support together in {evidence_line}."
                )
            else:
                note = (
                    "This is the area that aligns most directly with the role. My experience here comes from workflow "
                    f"cleanup, operating logic, and structured process improvement in {evidence_line}."
                )
        elif axis["id"] == "delivery_coordination":
            if "implementation_enablement" in group_ids:
                note = (
                    "This score reflects implementation-heavy work where onboarding, adoption support, and structured follow-through "
                    f"matter as much as planning, which I have handled in environments such as {evidence_line}."
                )
            elif "pmo_delivery" in group_ids or "rollout" in blob or "onboarding" in blob:
                note = (
                    "This score reflects practical coordination work around rollout, onboarding, prioritization, and "
                    f"cross-functional follow-through in environments such as {evidence_line}."
                )
            else:
                note = (
                    "I am confident coordinating rollout, prioritization, and cross-functional follow-through in "
                    f"English-speaking environments based on {evidence_line}."
                )
            if "deutsch" in blob or "german" in blob:
                note += (
                    " For German-speaking stakeholder settings, I still see clear room to grow and I am improving "
                    "my German consistently."
                )
        else:
            if "ai_workflow_automation" in group_ids or "openai" in blob or "copilot" in blob or "n8n" in blob:
                note = (
                    "This becomes more relevant when the role expects practical AI enablement or automation support. "
                    f"I have used these approaches in {evidence_line}, while still treating the area as a capability I am actively deepening."
                )
            else:
                note = (
                    "I have applied AI to workflow support, automation, and structured problem-solving in "
                    f"{evidence_line}, but I still position this as a developing capability rather than a finished specialty."
                )
        axes.append(
            {
                "id": axis["id"],
                "label": axis["label"],
                "score": score,
                "focus": axis["focus"],
                "evidence_line": evidence_line,
                "note": note,
                "color": axis["color"],
            }
        )
    return axes


def select_snapshot_tools(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
) -> list[str]:
    blob = requirements_blob(intake)
    verified = set(verified_skill_inventory(profile, role))
    keyword_skill_map = [
        ("jira", "Jira"),
        ("confluence", "Confluence"),
        ("bpmn", "BPMN"),
        ("sql", "SQL"),
        ("n8n", "n8n Automation"),
        ("automation", "n8n Automation"),
        ("openai", "OpenAI"),
        ("codex", "Codex"),
        ("copilot", "GitHub Copilot"),
        ("github", "GitHub"),
        ("kiro", "Kiro"),
        ("context", "Context Engineering"),
        ("vibe", "Vibe Coding"),
    ]
    candidates: list[str] = []
    for keyword, skill in keyword_skill_map:
        if keyword in blob and skill in verified and skill not in candidates:
            candidates.append(skill)

    defaults = [
        "Jira",
        "Confluence",
        "BPMN",
        "SQL",
        "n8n Automation",
        "OpenAI",
        "Codex",
        "GitHub Copilot",
        "GitHub",
        "Kiro",
        "Context Engineering",
        "Vibe Coding",
    ]
    for skill in defaults:
        if skill in verified and skill not in candidates:
            candidates.append(skill)
    return candidates[:6]


def select_snapshot_domains(selected_evidence: list[dict[str, Any]]) -> list[str]:
    domain_map = {
        "b2b": "B2B",
        "marketplace": "Marketplace",
        "operations": "Digital Operations",
        "industrial": "Industrial Commerce",
        "healthcare": "Healthcare",
        "ocr": "OCR Workflows",
        "legaltech": "LegalTech",
        "regulated": "Regulated Workflows",
        "onboarding": "Onboarding",
        "delivery": "Product Delivery",
        "workflow": "Workflow Design",
        "automation": "Automation",
        "portfolio": "AI Workflow Systems",
    }
    values: list[str] = []
    for item in selected_evidence:
        for tag in item.get("tags", []):
            label = domain_map.get(str(tag).lower())
            if label and label not in values:
                values.append(label)
    return values[:4]


def select_role_fit_keywords(intake: dict[str, Any], taxonomy: dict[str, Any], role: dict[str, Any]) -> list[str]:
    labels = {
        "requirements_process": "Requirements & Process",
        "process_digitalization": "Digitalization",
        "pmo_delivery": "PMO Support",
        "implementation_enablement": "Implementation & Enablement",
        "workflow_operations": "Workflow Operations",
        "quality_test_compliance": "Quality & Compliance",
        "ai_workflow_automation": "AI Workflow",
    }
    values = [role["label"]]
    for group in matched_taxonomy_groups(intake, taxonomy):
        label = labels.get(group["id"])
        if label and label not in values:
            values.append(label)
    return values[:4]


def select_snapshot_growth_areas(
    intake: dict[str, Any],
    axes: list[dict[str, Any]],
    taxonomy: dict[str, Any],
) -> list[str]:
    blob = requirements_blob(intake)
    groups = matched_group_ids(intake, taxonomy)
    values: list[str] = []
    if "german" in blob or "deutsch" in blob:
        values.append("German communication")
    if any(axis["id"] == "ai_workflow_automation" and float(axis["score"]) < 4.0 for axis in axes):
        values.append("AI workflow depth")
    if {"requirements_process", "process_digitalization", "quality_test_compliance", "workflow_operations"} & groups:
        values.append("Process standards")
    if "pmo_delivery" in groups:
        values.append("Executive reporting")
    if "implementation_enablement" in groups:
        values.append("German adoption support")
    if not values:
        values.extend(["German communication", "Process standards"])
    return values[:4]


def snapshot_polygon_points(axes: list[dict[str, Any]], radius_unit: float = 10.0) -> list[tuple[float, float]]:
    top, right, bottom, left = [float(axis["score"]) * radius_unit for axis in axes]
    return [(0.0, top), (right, 0.0), (0.0, -bottom), (-left, 0.0)]


def snapshot_polygon_path_latex(axes: list[dict[str, Any]], radius_unit: float = 10.0) -> str:
    points = snapshot_polygon_points(axes, radius_unit)
    return " -- ".join(f"({x:.1f},{y:.1f})" for x, y in points) + " -- cycle"


def snapshot_polygon_points_html(axes: list[dict[str, Any]], center: tuple[float, float] = (75.0, 75.0), radius_unit: float = 14.0) -> str:
    cx, cy = center
    points = snapshot_polygon_points(axes, radius_unit)
    html_points = [(cx + x, cy - y) for x, y in points]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in html_points)


def build_snapshot_payload(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    axes = score_snapshot_axes(role, intake, taxonomy, selected_evidence)
    tools = select_snapshot_tools(profile, role, intake)
    domains = select_snapshot_domains(selected_evidence)
    role_fit = select_role_fit_keywords(intake, taxonomy, role)
    growth_areas = select_snapshot_growth_areas(intake, axes, taxonomy)
    return {
        "title": "Role Fit Snapshot and Self-Assessment",
        "intro": f"This supplement is based on my own assessment against the current job description for {intake['job_title']} at {intake['company_name']}. It highlights the four fit areas I consider most relevant to the role and complements my cover letter and CV.",
        "axes": axes,
        "tools": tools,
        "domains": domains,
        "role_fit_keywords": role_fit,
        "growth_areas": growth_areas,
        "score_scale": "1 = awareness, 3 = applied in projects, 5 = drove outcomes across roles",
    }


def build_snapshot_context(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    snapshot: dict[str, Any],
    latex_mode: bool,
) -> dict[str, str]:
    axes = snapshot["axes"]
    polygon = snapshot_polygon_path_latex(axes) if latex_mode else snapshot_polygon_points_html(axes)
    joined_tools = join_inline_items(snapshot["tools"], latex_mode)
    joined_domains = join_inline_items(snapshot["domains"], latex_mode)
    joined_fit = join_inline_items(snapshot["role_fit_keywords"], latex_mode)
    joined_growth = join_inline_items(snapshot["growth_areas"], latex_mode)
    mapping = {
        "SENDER_BLOCK": build_snapshot_contact_block(profile, latex_mode=latex_mode),
        "DOCUMENT_TITLE": latex_escape(snapshot["title"]) if latex_mode else html_escape(snapshot["title"]),
        "INTRO_LINE": latex_escape(snapshot["intro"]) if latex_mode else html_escape(snapshot["intro"]),
        "SCORE_SCALE": latex_escape(snapshot["score_scale"]) if latex_mode else html_escape(snapshot["score_scale"]),
        "POLYGON_PATH": polygon,
        "TOOLS_LINE": joined_tools,
        "DOMAINS_LINE": joined_domains,
        "ROLE_FIT_LINE": joined_fit,
        "GROWTH_AREAS_LINE": joined_growth,
        "SIGNATURE_NAME": latex_escape(profile["name"]) if latex_mode else html_escape(profile["name"]),
        "SIGNATURE_PATH": latex_escape(snapshot_signature_path()) if latex_mode else html_escape(snapshot_signature_path()),
    }
    axis_keys = ["TOP", "RIGHT", "BOTTOM", "LEFT"]
    for key, axis in zip(axis_keys, axes):
        mapping[f"{key}_LABEL"] = latex_escape(axis["label"]) if latex_mode else html_escape(axis["label"])
        mapping[f"{key}_SCORE"] = latex_escape(f"{axis['score']:.1f}/5") if latex_mode else html_escape(f"{axis['score']:.1f}/5")
        mapping[f"{key}_NOTE"] = latex_escape(axis["note"]) if latex_mode else html_escape(axis["note"])
        mapping[f"{key}_COLOR"] = axis["color"].replace("#", "")
        if axis["label"] == "Requirements & Analysis":
            latex_display = r"Requirements \&\\ Analysis"
            latex_chart = r"Req."
            html_display = "Req."
        elif axis["label"] == "Process & Workflow Design":
            latex_display = r"Process \&\\ Workflow Design"
            latex_chart = r"Process"
            html_display = "Process"
        elif axis["label"] == "Delivery & Stakeholder Coordination":
            latex_display = r"Delivery \&\\ Stakeholder Coordination"
            latex_chart = r"Delivery"
            html_display = "Delivery"
        else:
            latex_display = r"AI Workflow \&\\ Automation"
            latex_chart = r"AI"
            html_display = "AI"
        mapping[f"{key}_AXIS_DISPLAY"] = latex_chart if latex_mode else html_display
    mapping["LEGEND_TOP"] = mapping["TOP_LABEL"] + " " + mapping["TOP_SCORE"]
    mapping["LEGEND_RIGHT"] = mapping["RIGHT_LABEL"] + " " + mapping["RIGHT_SCORE"]
    mapping["LEGEND_BOTTOM"] = mapping["BOTTOM_LABEL"] + " " + mapping["BOTTOM_SCORE"]
    mapping["LEGEND_LEFT"] = mapping["LEFT_LABEL"] + " " + mapping["LEFT_SCORE"]
    return mapping


def compile_tex(tex_path: Path) -> None:
    result = subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_path.name,
        ],
        cwd=tex_path.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        output = result.stdout.decode("utf-8", errors="replace")
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=output,
            stderr=None,
        )


def sanitize_cover_letter_pdf(pdf_path: Path) -> None:
    qpdf_path = shutil.which("qpdf")
    if not qpdf_path:
        raise FileNotFoundError("qpdf is required to generate upload-safe cover letter PDFs.")

    with tempfile.TemporaryDirectory(prefix="cover-letter-sanitize-", dir=pdf_path.parent) as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        qdf_path = tmp_dir / "cover_letter.qdf.pdf"
        edited_qdf_path = tmp_dir / "cover_letter.edited.qdf.pdf"
        sanitized_path = tmp_dir / "cover_letter.sanitized.pdf"

        subprocess.run(
            [qpdf_path, "--qdf", "--object-streams=disable", str(pdf_path), str(qdf_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        qdf_text = qdf_path.read_text(encoding="latin-1")
        sanitized_qdf_text = re.sub(
            r"\n\s*/OpenAction\s+\d+\s+\d+\s+R",
            "",
            qdf_text,
            count=1,
        )
        sanitized_qdf_text = re.sub(
            r"\n\s*/OpenAction\s*\[\s*\n\s*\d+\s+\d+\s+R\s*\n\s*/Fit\s*\n\s*\]",
            "",
            sanitized_qdf_text,
            count=1,
        )
        edited_qdf_path.write_text(sanitized_qdf_text, encoding="latin-1")

        result = subprocess.run(
            [qpdf_path, str(edited_qdf_path), str(sanitized_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode not in {0, 3}:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                output=result.stdout,
                stderr=None,
            )

        shutil.move(sanitized_path, pdf_path)


def archive_generated_pdf(
    generated_pdf: Path,
    target_dir: Path,
    prefix: str,
    profile: dict[str, Any],
    intake: dict[str, Any],
    timestamp: str,
) -> Path:
    archived_pdf = target_dir / build_pdf_filename(prefix, profile, intake, timestamp)
    shutil.move(generated_pdf, archived_pdf)
    return archived_pdf


def build_generated_resume_data(
    profile: dict[str, Any],
    role: dict[str, Any],
    intake: dict[str, Any],
    selected_evidence: list[dict[str, Any]],
    summary_text: str,
    taxonomy: dict[str, Any],
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

    role_skills = intake.get("cv_skills_override") or build_role_skills(profile, role, intake, taxonomy)

    return {
        "name": profile["name"],
        "initials": profile["initials"],
        "location": profile["location"],
        "locationLink": profile["location_link"],
        "about": intake.get("cv_about_override") or role.get("about", profile["headline"]),
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
    snapshot_payload: dict[str, Any],
) -> str:
    axis_summary = ", ".join(
        f"{item['label']} ({item['score']:.1f}/5)" for item in snapshot_payload["axes"]
    )
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
            "## Role fit snapshot",
            f"- Axes: {axis_summary}",
            f"- Tools: {', '.join(snapshot_payload['tools'])}",
            f"- Role-fit keywords: {', '.join(snapshot_payload['role_fit_keywords'])}",
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
    taxonomy = load_json(DATA_DIR / "job_taxonomy.json")
    authentic_voice = load_json(DATA_DIR / "authentic_writing_profile.json")
    summary_version_map = get_summary_versions(summary_versions)

    recommended_summary_versions = detect_summary_recommendations(intake, summary_versions, taxonomy)
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
    selected_summary_text = intake.get("cv_summary_override") or selected_summary["text"]

    primary_role = get_role(role_profiles, intake["primary_role"])
    target_role_ids = intake.get("target_roles") or [intake["primary_role"]]
    target_roles = [get_role(role_profiles, role_id) for role_id in target_role_ids]

    company_slug = package_slug(intake)
    output_root = Path(args.output).resolve() if args.output else DEFAULT_OUTPUTS_DIR / company_slug
    cover_letter_dir = output_root / "cover-letter"
    cv_dir = output_root / "cv"
    snapshot_dir = output_root / "skill-assessment"

    selected_for_cover_letter = select_evidence(intake, primary_role, evidence_library, taxonomy)
    cover_letter_context = build_cover_letter_context(profile, primary_role, intake, selected_for_cover_letter, authentic_voice)
    cover_letter_html_context = build_cover_letter_html_context(profile, primary_role, intake, selected_for_cover_letter, authentic_voice)
    snapshot_payload = build_snapshot_payload(profile, primary_role, intake, selected_for_cover_letter, taxonomy)
    snapshot_tex_context = build_snapshot_context(profile, primary_role, intake, snapshot_payload, latex_mode=True)
    snapshot_html_context = build_snapshot_context(profile, primary_role, intake, snapshot_payload, latex_mode=False)

    write_text(
        cover_letter_dir / "cover_letter.tex",
        render_template(read_template("cover_letter.tex"), cover_letter_context),
    )
    write_text(
        cover_letter_dir / "cover_letter.html",
        render_template(read_template("cover_letter_preview.html"), cover_letter_html_context),
    )
    write_text(
        snapshot_dir / "role_fit_snapshot.tex",
        render_template(read_template("role_fit_snapshot.tex"), snapshot_tex_context),
    )
    write_text(
        snapshot_dir / "role_fit_snapshot.html",
        render_template(read_template("role_fit_snapshot_preview.html"), snapshot_html_context),
    )
    write_json(snapshot_dir / "role_fit_snapshot.json", snapshot_payload)

    manifest: dict[str, Any] = {
        "company_name": intake["company_name"],
        "job_title": intake["job_title"],
        "primary_role": primary_role["id"],
        "summary_version": selected_summary["id"],
        "cover_letter_evidence": [item["id"] for item in selected_for_cover_letter],
        "skill_assessment": {
            "axes": snapshot_payload["axes"],
            "tools": snapshot_payload["tools"],
            "domains": snapshot_payload["domains"],
            "role_fit_keywords": snapshot_payload["role_fit_keywords"],
            "json_path": path_for_manifest(snapshot_dir / "role_fit_snapshot.json"),
            "html_path": path_for_manifest(snapshot_dir / "role_fit_snapshot.html"),
            "pdf_path": None,
        },
        "cv_variants": [],
    }

    dev_server_process: subprocess.Popen[str] | None = None
    render_id = render_timestamp()

    if args.compile_pdf:
        dev_server_process = ensure_render_server(args.render_base_url)

    for role in target_roles:
        selected_for_cv = select_evidence(intake, role, evidence_library, taxonomy)
        role_payload = build_generated_resume_data(
            profile,
            role,
            intake,
            selected_for_cv,
            selected_summary_text,
            taxonomy,
        )
        role_payload = normalize_payload_for_ats(role_payload)
        json_path = cv_dir / f"{role['id']}.json"
        public_json_path = PUBLIC_CV_DATA_DIR / company_slug / f"{role['id']}.json"
        write_json(json_path, role_payload)
        write_json(public_json_path, role_payload)
        write_json(CURRENT_PUBLIC_CV_PATH, role_payload)

        render_url = f"{args.render_base_url}/generated-cv/"
        pdf_path = cv_dir / build_pdf_filename("resume", profile, intake, render_id)
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
                "json_path": path_for_manifest(json_path),
                "public_json_path": path_for_manifest(public_json_path),
                "render_url": render_url,
                "pdf_path": path_for_manifest(pdf_path) if args.compile_pdf else None,
            }
        )

    if args.compile_pdf:
        compile_tex(cover_letter_dir / "cover_letter.tex")
        cover_letter_pdf = archive_generated_pdf(
            cover_letter_dir / "cover_letter.pdf",
            cover_letter_dir,
            "cover-letter",
            profile,
            intake,
            render_id,
        )
        sanitize_cover_letter_pdf(cover_letter_pdf)
        cover_letter_pages = get_pdf_page_count(cover_letter_pdf)
        if cover_letter_pages > 1:
            raise SystemExit(
                f"Generated cover letter PDF `{cover_letter_pdf}` is {cover_letter_pages} pages. "
                "Cover letters must stay within 1 page."
            )
        compile_tex(snapshot_dir / "role_fit_snapshot.tex")
        snapshot_pdf = archive_generated_pdf(
            snapshot_dir / "role_fit_snapshot.pdf",
            snapshot_dir,
            "role-fit-snapshot",
            profile,
            intake,
            render_id,
        )
        snapshot_pages = get_pdf_page_count(snapshot_pdf)
        if snapshot_pages > 1:
            raise SystemExit(
                f"Generated skill assessment PDF `{snapshot_pdf}` is {snapshot_pages} pages. "
                "Role Fit Snapshot outputs must stay within 1 page."
            )
        manifest["skill_assessment"]["pdf_path"] = path_for_manifest(snapshot_pdf)
        if dev_server_process is not None:
            dev_server_process.terminate()
            try:
                dev_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dev_server_process.kill()

    write_json(output_root / "manifest.json", manifest)
    write_text(output_root / "notes.md", build_notes(intake, selected_for_cover_letter, target_roles, snapshot_payload))

    print(f"Generated application package at {output_root}")


if __name__ == "__main__":
    main()
