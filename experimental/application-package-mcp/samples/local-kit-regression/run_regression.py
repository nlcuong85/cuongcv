#!/usr/bin/env python3
"""Run local-kit regression against existing CuongCV generated artifacts.

This simulates a student laptop workspace. It does not call the remote MCP.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CUONGCV = Path("/Users/pmlecuong/Documents/CuongProjects/CuongCV")
KIT = REPO / "resources" / "application-kit"
WORKSPACE = REPO / "samples" / "local-kit-regression" / "workspace"
GENERATOR = KIT / "scripts" / "local_application_generator.py"
CUONG_GENERATOR = CUONGCV / "application-system/scripts/generate_application.py"

CASES = [
    {
        "slug": "mercedes-ipos",
        "intake": CUONGCV / "application-system/intakes/mercedes-benz-insurance-services-working-student-product-owner-support-insurance-platform-of-services.json",
        "source_output": CUONGCV / "application-system/outputs/mercedes-benz-insurance-services-gmbh-working-student-product-owner-support-insurance-platform-of-services",
        "cv_json": CUONGCV / "application-system/outputs/mercedes-benz-insurance-services-gmbh-working-student-product-owner-support-insurance-platform-of-services/cv/product_owner.json",
    },
    {
        "slug": "sap-threat-modelling",
        "intake": CUONGCV / "application-system/intakes/sap-working-student-threat-modelling-service-operation-and-automation.json",
        "source_output": CUONGCV / "application-system/outputs/sap-working-student-f-m-d-threat-modelling-service-operation-and-automation",
        "cv_json": CUONGCV / "application-system/outputs/sap-working-student-f-m-d-threat-modelling-service-operation-and-automation/cv/process_automation.json",
    },
    {
        "slug": "vishay-controlling",
        "intake": CUONGCV / "application-system/intakes/vishay-semiconductor-werkstudent-controlling.json",
        "source_output": CUONGCV / "application-system/outputs/vishay-semiconductor-gmbh-werkstudent-m-w-d-controlling",
        "cv_json": CUONGCV / "application-system/outputs/vishay-semiconductor-gmbh-werkstudent-m-w-d-controlling/cv/workflow_operations_analyst.json",
    },
]


def clean() -> None:
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    (WORKSPACE / "candidate").mkdir(parents=True)
    (WORKSPACE / "jobs").mkdir()
    (WORKSPACE / "outputs").mkdir()
    shutil.copytree(KIT, WORKSPACE / "application-kit")


def prepare_current_cuongcv_sources() -> None:
    """Generate fresh CuongCV application outputs before replaying the local kit.

    The regression should benchmark the student kit against the current
    application generator, not stale historical letters that the new authoring
    gate is expected to reject.
    """

    generated_root = WORKSPACE / "source-generated"
    generated_root.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        out = generated_root / str(case["slug"])
        subprocess.run(
            [
                "python3",
                str(CUONG_GENERATOR),
                "--intake",
                str(case["intake"]),
                "--output",
                str(out),
            ],
            cwd=str(CUONGCV / "application-system"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )
        case["source_output"] = out
        cv_files = sorted((out / "cv").glob("*.json"))
        if cv_files:
            case["cv_json"] = cv_files[0]


def md_escape(value: object) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text.replace("|", "\\|")


def latex_unescape(text: str) -> str:
    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\$": "$",
        r"\#": "#",
        r"\_": "_",
        r"\{": "{",
        r"\}": "}",
        r"\textbackslash{}": "\\",
        r"\textasciitilde{}": "~",
        r"\textasciicircum{}": "^",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def extract_between(text: str, start: str, end: str) -> str:
    i = text.index(start) + len(start)
    j = text.index(end, i)
    return text[i:j].strip()


def block_to_lines(block: str) -> list[str]:
    return [latex_unescape(item) for item in re.split(r"\\\\\s*", block) if item.strip()]


def parse_source_cover_letter(tex_path: Path) -> dict[str, object]:
    tex = tex_path.read_text(encoding="utf-8")
    sender_block = extract_between(tex, "\\raggedleft\n", "\n\\end{minipage}\n\\end{flushright}")
    recipient_block = extract_between(tex, "\\noindent\n\\begin{minipage}[t]{0.42\\textwidth}\n", "\n\\end{minipage}")
    flushright_blocks = re.findall(r"\\begin\{flushright\}\n(.*?)\n\\end\{flushright\}", tex, flags=re.DOTALL)
    if len(flushright_blocks) < 2:
        raise ValueError(f"Could not find sender and date flushright blocks in {tex_path}")
    date_line = flushright_blocks[1].strip()
    subject_line = re.search(r"\\textbf\{(.+?)\}", tex).group(1)  # type: ignore[union-attr]
    after_subject = tex.split("\\vspace{0.6em}", 1)[1]
    salutation = after_subject.split("\\vspace{0.45em}", 1)[0].strip()
    rest = after_subject.split("\\vspace{0.45em}", 1)[1]
    paragraphs = []
    for _ in range(5):
        paragraph, rest = rest.split("\\vspace{0.45em}", 1) if "\\vspace{0.45em}" in rest else rest.split("\\vspace{0.55em}", 1)
        paragraphs.append(latex_unescape(paragraph))
    signature_match = re.search(r"@@SIGNATURE_NAME@@", tex)
    _ = signature_match
    signature_name_match = re.search(r"\\includegraphics\[width=9cm\]\{.+?\}\\\\\n\\vspace\{0\.2em\}\n(.+?)\n", tex)
    signature_name = latex_unescape(signature_name_match.group(1)) if signature_name_match else block_to_lines(sender_block)[0]
    signature_path_match = re.search(r"\\includegraphics\[width=9cm\]\{(.+?)\}", tex)
    signature_path = latex_unescape(signature_path_match.group(1)) if signature_path_match else ""
    return {
        "sender_lines": block_to_lines(sender_block),
        "recipient_lines": block_to_lines(recipient_block),
        "date_line": latex_unescape(date_line),
        "subject_line": latex_unescape(subject_line),
        "salutation": latex_unescape(salutation),
        "opening_paragraph": paragraphs[0],
        "body_paragraph_one": paragraphs[1],
        "body_paragraph_two": paragraphs[2],
        "motivation_paragraph": paragraphs[3],
        "closing_paragraph": paragraphs[4],
        "signature_name": signature_name,
        "signature_path": signature_path,
        "enclosures": [
            "Curriculum Vitae",
            "Bachelor Degree Diploma",
            "Reference letter from previous employers",
        ],
    }


def build_cv_input(cv_json: Path, intake: dict[str, object]) -> dict[str, object]:
    cv = json.loads(cv_json.read_text(encoding="utf-8"))
    work = cv.get("work", [])
    evidence = []
    for item in work[:3]:
        title = item.get("title", "Role")
        company = item.get("company", "Company")
        overview = item.get("overview", "")
        evidence.append(f"{title} at {company}: {overview}")
    return {
        "name": cv.get("name"),
        "job_title": intake.get("job_title"),
        "company": intake.get("company_name"),
        "overview": cv.get("summary"),
        "skills": cv.get("skills", [])[:14],
        "evidence_alignment": evidence,
        "review_notes": ["Regression fixture generated from existing CuongCV source-truth output."],
    }


def write_candidate_capture() -> None:
    """Populate local candidate memory from CuongCV source-truth outputs.

    This is intentionally written into the regression workspace only. It proves
    how a student-local agent should preserve source analysis without sending
    private data to the MCP service.
    """

    candidate_dir = WORKSPACE / "candidate"
    cvs = [json.loads(Path(case["cv_json"]).read_text(encoding="utf-8")) for case in CASES]  # type: ignore[arg-type]
    first = cvs[0]
    skill_union: list[str] = []
    for cv in cvs:
        for skill in cv.get("skills", []):
            if skill not in skill_union:
                skill_union.append(skill)

    profile = {
        "profileId": "cuong-regression-source-capture",
        "name": first.get("name"),
        "headline": first.get("about"),
        "summary": first.get("summary"),
        "contact": {
            "email": first.get("contact", {}).get("email"),
            "phone": first.get("contact", {}).get("tel"),
            "location": first.get("location"),
            "website": first.get("personalWebsiteUrl"),
            "social": first.get("contact", {}).get("social", []),
        },
        "skills": {
            "core": skill_union[:7],
            "adaptive": skill_union[7:14],
            "not_yet_supported": [],
        },
        "education": first.get("education", []),
        "experience": first.get("work", []),
        "projects": first.get("projects", []),
        "awards": first.get("awards", []),
        "constraints": {
            "must_not_claim": [
                "Do not claim JD-only tools unless they appear in profile, evidence, source CV, or writing samples.",
                "Do not claim professional language fluency unless a newer candidate source confirms it.",
                "Do not change legal/contact/education facts without updating the source profile first.",
            ],
            "review_before_submission": [
                "Candidate must check every generated PDF for one-page layout and correct recipient details.",
                "Candidate must confirm language, availability, and work-authorization wording for each job.",
            ],
        },
    }
    (candidate_dir / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence_lines = [
        "# Evidence",
        "",
        "This file was populated from existing CuongCV source-truth CV JSON and cover-letter outputs for regression testing.",
        "",
        "## Identity And Contact",
        "",
        f"- Name: {first.get('name')}",
        f"- Email: {first.get('contact', {}).get('email')}",
        f"- Phone: {first.get('contact', {}).get('tel')}",
        f"- Location: {first.get('location')}",
        f"- Portfolio: {first.get('personalWebsiteUrl')}",
        "",
        "## Education",
        "",
    ]
    for item in first.get("education", []):
        evidence_lines.append(
            f"- {item.get('degree')} at {item.get('school')} ({item.get('start')} - {item.get('end')}), {item.get('location')}"
        )
    evidence_lines.extend(["", "## Work Experience", ""])
    for item in first.get("work", []):
        evidence_lines.append(f"- {item.get('title')} at {item.get('company')} ({item.get('start')} - {item.get('end')}): {item.get('overview')}")
        for bullet in item.get("bullets", []):
            evidence_lines.append(f"  - {bullet}")
    evidence_lines.extend(["", "## Projects", ""])
    for project in first.get("projects", []):
        evidence_lines.append(f"- {project.get('title') or project.get('name')}: {project.get('description') or project.get('summary') or ''}")
    evidence_lines.extend(["", "## Skills Inventory", ""])
    evidence_lines.append("- Core skills: " + ", ".join(skill_union[:7]))
    evidence_lines.append("- Adaptive skills: " + ", ".join(skill_union[7:14]))
    evidence_lines.extend(
        [
            "",
            "## Cover Letter Evidence Patterns",
            "",
        ]
    )
    for case in CASES:
        draft = parse_source_cover_letter(Path(case["source_output"]) / "cover-letter" / "cover_letter.tex")  # type: ignore[arg-type]
        evidence_lines.append(f"- {case['slug']}: {draft['subject_line']}")
        evidence_lines.append(f"  - Opening trigger: {draft['opening_paragraph']}")
        evidence_lines.append(f"  - Strongest evidence: {draft['body_paragraph_one']}")
        evidence_lines.append(f"  - Second evidence: {draft['body_paragraph_two']}")
    evidence_lines.extend(
        [
            "",
            "## Do Not Claim",
            "",
            "- Do not add skills only because they appear in a job description.",
            "- Do not alter education dates, employer names, or contact details from generated application runs.",
            "- Do not make language or work-authorization claims without a current candidate confirmation source.",
            "",
        ]
    )
    (candidate_dir / "evidence.md").write_text("\n".join(evidence_lines), encoding="utf-8")

    tone_lines = [
        "# Tone Profile",
        "",
        "This file is derived from the existing CuongCV cover-letter outputs used in regression fixtures.",
        "",
        "## Voice Rules",
        "",
        "- Open with the actual work in the job, not generic enthusiasm.",
        "- Use practical evidence from product ownership, business analysis, process work, delivery coordination, and automation.",
        "- Keep the tone calm, direct, and recruiter-safe.",
        "- Avoid overclaiming seniority for working-student roles.",
        "- Keep caveats short and practical when language or authorization facts need review.",
        "",
        "## Paragraph Purpose",
        "",
        "- Paragraph 1: role, company, concrete trigger, why the work fits.",
        "- Paragraph 2: strongest evidence-backed match.",
        "- Paragraph 3: second evidence cluster from a different project or experience.",
        "- Paragraph 4: company or role motivation without generic praise.",
        "- Paragraph 5: practical closing with availability, review caveats, and next step.",
        "",
        "## Authentic Sentence Patterns",
        "",
    ]
    for case in CASES:
        draft = parse_source_cover_letter(Path(case["source_output"]) / "cover-letter" / "cover_letter.tex")  # type: ignore[arg-type]
        tone_lines.append(f"- {draft['opening_paragraph']}")
    tone_lines.extend(
        [
            "",
            "## Avoid",
            "",
            "- Highly motivated and passionate.",
            "- Perfect candidate.",
            "- Extensive experience in every listed requirement.",
            "- Generic praise about being a global leader.",
            "",
        ]
    )
    (candidate_dir / "tone.md").write_text("\n".join(tone_lines), encoding="utf-8")

    analysis_lines = [
        "# Source Analysis",
        "",
        "This file captures line-by-line reusable understanding from the regression source CV and cover-letter outputs.",
        "",
        "## Resume / CV Analysis",
        "",
        "| Source line or section | Meaning | Reusable claim | Evidence strength | Use in CV | Use in cover letter | Risk / uncertainty |",
        "|---|---|---|---|---|---|---|",
    ]
    analysis_lines.append(
        f"| about: {md_escape(first.get('about'))} | Candidate positioning | {md_escape(first.get('about'))} | strong | yes | yes | Keep aligned with profile source |"
    )
    analysis_lines.append(
        f"| summary | Broad role fit across product, BA, delivery, and improvement | {md_escape(first.get('summary'))} | strong | yes | no | Shorten per role |"
    )
    for item in first.get("education", []):
        source = f"{item.get('degree')} - {item.get('school')} - {item.get('start')} to {item.get('end')}"
        analysis_lines.append(
            f"| {md_escape(source)} | Education credential | {md_escape(item.get('degree'))} at {md_escape(item.get('school'))} | strong | yes | maybe | Do not change dates or grade |"
        )
    for item in first.get("work", []):
        source = f"{item.get('title')} at {item.get('company')}: {item.get('overview')}"
        analysis_lines.append(
            f"| {md_escape(source)} | Work evidence | {md_escape(item.get('overview'))} | strong | yes | yes | Select only role-relevant bullets |"
        )
        for bullet in item.get("bullets", []):
            analysis_lines.append(
                f"| {md_escape(bullet)} | Concrete responsibility or output | {md_escape(bullet)} | strong | yes | yes | Avoid inflating beyond original scope |"
            )
    analysis_lines.extend(
        [
            "",
            "## Cover Letter Analysis",
            "",
            "| Source paragraph | Purpose | Tone signal | Reusable structure | Do not repeat |",
            "|---|---|---|---|---|",
        ]
    )
    for case in CASES:
        draft = parse_source_cover_letter(Path(case["source_output"]) / "cover-letter" / "cover_letter.tex")  # type: ignore[arg-type]
        for key, purpose in [
            ("opening_paragraph", "Opening trigger"),
            ("body_paragraph_one", "Strongest evidence"),
            ("body_paragraph_two", "Second evidence"),
            ("motivation_paragraph", "Role motivation"),
            ("closing_paragraph", "Practical close"),
        ]:
            analysis_lines.append(
                f"| {md_escape(draft[key])} | {purpose} | direct, practical | Keep same paragraph role, rewrite for each JD | Do not copy blindly across jobs |"
            )
    analysis_lines.extend(
        [
            "",
            "## Skill Mapping",
            "",
            "| Skill | Source evidence | Strength | Safe wording | Job families where useful |",
            "|---|---|---|---|---|",
        ]
    )
    for skill in skill_union[:14]:
        analysis_lines.append(
            f"| {md_escape(skill)} | Appears in generated source-truth CV skills | strong | {md_escape(skill)} | product, BA, process, operations, automation |"
        )
    analysis_lines.extend(
        [
            "",
            "## Open Questions For Candidate",
            "",
            "- Confirm current language level before jobs with explicit language requirements.",
            "- Confirm current work authorization and residence-permit wording before employer-facing documents.",
            "- Confirm availability and weekly-hour limit for each working-student application.",
            "",
        ]
    )
    (candidate_dir / "source-analysis.md").write_text("\n".join(analysis_lines), encoding="utf-8")


def required_layout_lines(tex: str) -> bool:
    required = [
        "\\documentclass[9pt,a4paper]{article}",
        "\\usepackage[a4paper,left=25mm,right=20mm,top=36mm,bottom=18mm]{geometry}",
        "\\begin{flushright}",
        "\\begin{minipage}[t]{0.34\\textwidth}",
        "\\begin{minipage}[t]{0.42\\textwidth}",
        "\\pagestyle{empty}",
        "\\textbf{Application for",
        "\\textbf{Enclosure:}",
    ]
    return all(item in tex for item in required)


def pdf_visible_text(pdf_path: Path) -> str:
    proc = subprocess.run(["pdftotext", str(pdf_path), "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return proc.stdout


def no_latex_leak(pdf_path: Path) -> bool:
    text = pdf_visible_text(pdf_path)
    forbidden = [
        r"\begin{",
        r"\end{",
        r"\vspace",
        r"\textwidth",
        r"\raggedleft",
        r"\includegraphics",
    ]
    return not any(token in text for token in forbidden)


def run_case(case: dict[str, object]) -> dict[str, object]:
    slug = str(case["slug"])
    intake = json.loads(Path(case["intake"]).read_text(encoding="utf-8"))  # type: ignore[arg-type]
    out = WORKSPACE / "outputs" / slug
    out.mkdir(parents=True)
    job_dir = WORKSPACE / "jobs" / slug
    job_dir.mkdir()
    (job_dir / "job.json").write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")

    source_output = Path(case["source_output"])  # type: ignore[arg-type]
    draft = parse_source_cover_letter(source_output / "cover-letter" / "cover_letter.tex")
    draft_path = out / "cover-letter-draft.json"
    draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cv_input = build_cv_input(Path(case["cv_json"]), intake)  # type: ignore[arg-type]
    cv_input_path = out / "cv-input.json"
    cv_input_path.write_text(json.dumps(cv_input, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            "python3",
            str(WORKSPACE / "application-kit" / "scripts" / "local_application_generator.py"),
            "--draft",
            str(draft_path),
            "--cv-input",
            str(cv_input_path),
            "--output-dir",
            str(out),
            "--template",
            str(WORKSPACE / "application-kit" / "templates" / "cover_letter.tex"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    generated_tex = (out / "cover-letter.tex").read_text(encoding="utf-8") if (out / "cover-letter.tex").exists() else ""
    generated_pdfs = sorted(out.glob("cover-letter-*.pdf"))
    source_tex = (source_output / "cover-letter" / "cover_letter.tex").read_text(encoding="utf-8")
    generated_cv = (out / "cv-tailored.md").read_text(encoding="utf-8") if (out / "cv-tailored.md").exists() else ""
    source_cv = json.loads(Path(case["cv_json"]).read_text(encoding="utf-8"))  # type: ignore[arg-type]
    source_skills = set(source_cv.get("skills", []))
    generated_skill_hits = sum(1 for skill in source_skills if f"- {skill}" in generated_cv)

    return {
        "slug": slug,
        "generator_exit": proc.returncode,
        "manifest_ok": manifest.get("ok"),
        "layout_matches_contract": required_layout_lines(generated_tex),
        "source_layout_matches_contract": required_layout_lines(source_tex),
        "subject_matches_source": draft["subject_line"] in generated_tex,
        "no_visible_latex_leak": no_latex_leak(generated_pdfs[-1]) if generated_pdfs else False,
        "cv_skill_hits_against_source": generated_skill_hits,
        "source_skill_count": len(source_skills),
        "validation_path": str(out / "validation.md"),
        "output_dir": str(out),
    }


def main() -> int:
    clean()
    prepare_current_cuongcv_sources()
    write_candidate_capture()
    results = [run_case(case) for case in CASES]
    ok = all(
        item["manifest_ok"]
        and item["layout_matches_contract"]
        and item["source_layout_matches_contract"]
        and item["subject_matches_source"]
        and item["no_visible_latex_leak"]
        and item["cv_skill_hits_against_source"] >= min(10, item["source_skill_count"])
        for item in results
    )
    report = {
        "ok": ok,
        "workspace": str(WORKSPACE),
        "cases": results,
    }
    (WORKSPACE / "regression-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Local Kit Regression Report", "", f"Overall: {'PASS' if ok else 'FAIL'}", ""]
    for item in results:
        lines.extend(
            [
                f"## {item['slug']}",
                "",
                f"- Manifest OK: {item['manifest_ok']}",
                f"- Layout matches contract: {item['layout_matches_contract']}",
                f"- Source layout matches contract: {item['source_layout_matches_contract']}",
                f"- Subject matches source: {item['subject_matches_source']}",
                f"- No visible LaTeX leak: {item['no_visible_latex_leak']}",
                f"- CV skill hits against source: {item['cv_skill_hits_against_source']} / {item['source_skill_count']}",
                f"- Output dir: `{item['output_dir']}`",
                f"- Validation: `{item['validation_path']}`",
                "",
            ]
        )
    (WORKSPACE / "regression-report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
