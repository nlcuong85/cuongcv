#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from application_context import context_by_slug, contexts_by_job_url
from common import DATA_ROOT, APPLICATION_ROOT, load_json, write_json, write_text
from read_active_browser_tab import detect_browser, read_active_tab


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug")
    parser.add_argument("--browser")
    parser.add_argument("--output-name", default="browser-form-helper")
    parser.add_argument("--follow-up-days", type=int, default=7)
    return parser.parse_args()


def profile_payload() -> dict[str, str]:
    profile = load_json(APPLICATION_ROOT / "data" / "master_profile.json")
    return {
        "full_name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "location": profile.get("location", ""),
        "website": profile.get("website", ""),
        "linkedin": profile.get("linkedin", ""),
        "github": profile.get("github", ""),
    }


def match_context(args: argparse.Namespace, tab_url: str) -> dict[str, object] | None:
    if args.slug:
        return context_by_slug(args.slug, follow_up_days=args.follow_up_days)
    if tab_url:
        return contexts_by_job_url(follow_up_days=args.follow_up_days).get(tab_url.lower())
    return None


def pick_upload_paths(context: dict[str, object] | None) -> dict[str, str]:
    if not context:
        return {"resume_pdf": "", "cover_letter_pdf": ""}
    return {
        "resume_pdf": str(context.get("latest_cv_pdf", "")),
        "cover_letter_pdf": str(context.get("latest_cover_letter_pdf", "")),
    }


def answer_suggestions(fields: list[dict[str, object]], profile: dict[str, str], context: dict[str, object] | None) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    why_message = ""
    if context:
        why_message = (
            f"My background in {context.get('role_anchor', 'structured problem-solving')} "
            f"matches the focus of the {context.get('job_title', 'target role')} position."
        )

    for field in fields:
        haystack = " ".join(
            [
                str(field.get("label", "")),
                str(field.get("name", "")),
                str(field.get("id", "")),
                str(field.get("placeholder", "")),
                str(field.get("type", "")),
            ]
        ).lower()
        value = ""
        note = ""
        if any(token in haystack for token in ["full name", "first name", "last name", "name"]):
            value = profile["full_name"]
        elif any(token in haystack for token in ["email", "e-mail"]):
            value = profile["email"]
        elif any(token in haystack for token in ["phone", "mobile", "tel"]):
            value = profile["phone"]
        elif any(token in haystack for token in ["location", "city", "address"]):
            value = profile["location"]
        elif "linkedin" in haystack:
            value = profile["linkedin"]
        elif any(token in haystack for token in ["portfolio", "website", "personal site"]):
            value = profile["website"]
        elif "github" in haystack:
            value = profile["github"]
        elif any(token in haystack for token in ["cover letter", "motivation", "why this role", "why are you interested"]):
            value = why_message
            note = "Shorten or personalize before pasting."
        elif any(token in haystack for token in ["salary", "compensation", "expected pay"]):
            note = "Answer manually only if required. No default salary is stored in this workflow."
        elif any(token in haystack for token in ["visa", "sponsorship", "work authorization", "permit"]):
            note = "Answer manually. This workflow does not auto-assert immigration or sponsorship facts."

        if value or note:
            suggestions.append(
                {
                    "field": str(field.get("label") or field.get("name") or field.get("type")),
                    "value": value,
                    "note": note,
                }
            )
    return suggestions


def main() -> int:
    args = parse_args()
    browser = detect_browser(args.browser)
    tab_payload = read_active_tab(browser, extract_form=True)
    context = match_context(args, str(tab_payload.get("url", "")))
    profile = profile_payload()
    form_snapshot = tab_payload.get("form_snapshot") or {}
    fields = form_snapshot.get("fields", []) if isinstance(form_snapshot, dict) else []
    uploads = pick_upload_paths(context)
    suggestions = answer_suggestions(fields, profile, context)

    payload = {
        "tab": tab_payload,
        "matched_application": {
            "slug": context.get("slug", "") if context else "",
            "company_name": context.get("company_name", "") if context else "",
            "job_title": context.get("job_title", "") if context else "",
            "job_url": context.get("job_url", "") if context else "",
        },
        "profile": profile,
        "uploads": uploads,
        "suggested_answers": suggestions,
        "mode": "Mode A companion helper",
        "submit_policy": "Do not auto-submit. Review answers in the real browser session before sending.",
    }

    output_base = DATA_ROOT / args.output_name
    write_json(output_base.with_suffix(".json"), payload)

    md_lines = [
        "# Browser Form Helper",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Browser status: `{tab_payload['status']}`",
        f"- Browser: `{tab_payload['browser']}`",
        f"- Title: {tab_payload['title'] or '(none)'}",
        f"- URL: {tab_payload['url'] or '(none)'}",
        f"- Matched application slug: `{payload['matched_application']['slug'] or 'none'}`",
        "",
        "## Recommended Uploads",
        "",
        f"- Resume PDF: `{uploads['resume_pdf'] or 'not matched'}`",
        f"- Cover letter PDF: `{uploads['cover_letter_pdf'] or 'not matched'}`",
        "",
    ]
    if tab_payload.get("error"):
        md_lines.append(f"- Browser read note: `{tab_payload['error']}`")
        md_lines.append("")

    md_lines.extend(["## Suggested Answers", ""])
    if suggestions:
        for item in suggestions:
            line = f"- `{item['field']}`"
            if item["value"]:
                line += f": `{item['value']}`"
            if item["note"]:
                line += f" ({item['note']})"
            md_lines.append(line)
    else:
        md_lines.append("- No field-specific suggestions were produced from the current visible form fields.")

    md_lines.extend(
        [
            "",
            "## Human Steps",
            "",
            "- Keep using your normal logged-in browser session.",
            "- Copy only the suggestions that match the current form.",
            "- Upload the suggested files manually from your real browser.",
            "- Review every answer before the final submit button.",
            "",
        ]
    )
    write_text(output_base.with_suffix(".md"), "\n".join(md_lines))
    print(output_base.with_suffix(".md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
