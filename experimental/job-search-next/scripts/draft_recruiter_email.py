#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from application_context import ROLE_LABELS, context_by_slug, context_snapshot
from common import DATA_ROOT, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--intent", choices=["auto", "followup", "reply"], default="auto")
    parser.add_argument("--follow-up-days", type=int, default=7)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def greeting(contact_name: str) -> str:
    cleaned = (contact_name or "").strip()
    if not cleaned:
        return "Dear Hiring Team,"
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[0].strip()
    if cleaned.lower().endswith("team"):
        return f"Dear {cleaned},"
    return f"Dear {cleaned},"


def fallback_subject(intent: str, job_title: str) -> str:
    if intent == "followup":
        return f"Follow-up on application for {job_title}"
    return f"Re: Application for {job_title}"


def followup_body(context: dict[str, object]) -> str:
    applied_on = context.get("package_generated_on", "")
    role_anchor = context.get("role_anchor", "") or ROLE_LABELS.get(str(context.get("primary_role", "")), "structured problem-solving")
    return "\n".join(
        [
            greeting(str(context.get("contact_name", ""))),
            "",
            f"I hope you are well. I wanted to follow up on my application for the {context['job_title']} role.",
            f"I remain interested in the opportunity because it aligns well with my background in {role_anchor}.",
            f"My current package in this workflow was prepared on {applied_on}, and I would be glad to provide any additional information if helpful.",
            "",
            "Thank you for your time and consideration.",
            "",
            "Best regards,",
            "Le Cuong Nguyen",
        ]
    )


def rejection_reply_body(context: dict[str, object]) -> str:
    return "\n".join(
        [
            greeting(str(context.get("contact_name", ""))),
            "",
            "Thank you for your message and for taking the time to review my application.",
            f"I appreciate the update regarding the {context['job_title']} role and the consideration you gave my profile.",
            f"I remain interested in {context['company_name']} and would be glad to be considered again for suitable future opportunities.",
            "",
            "Kind regards,",
            "Le Cuong Nguyen",
        ]
    )


def generic_reply_body(context: dict[str, object]) -> str:
    return "\n".join(
        [
            greeting(str(context.get("contact_name", ""))),
            "",
            "Thank you for your message.",
            f"I appreciate the update regarding the {context['job_title']} role and I am happy to provide any additional information if useful.",
            "",
            "Kind regards,",
            "Le Cuong Nguyen",
        ]
    )


def choose_intent(context: dict[str, object], requested_intent: str, force: bool) -> str:
    if requested_intent != "auto":
        return requested_intent

    suggested = str(context.get("suggested_intent", "none"))
    if suggested != "none":
        return suggested
    if force:
        return "followup"
    raise SystemExit(
        f"No follow-up or reply is suggested for {context['slug']} from the current log state. "
        "Use --intent explicitly or add --force."
    )


def validate_context_for_intent(context: dict[str, object], intent: str, force: bool) -> None:
    stage = str(context.get("stage", ""))
    if intent == "followup" and stage not in {"submitted_waiting"} and not force:
        raise SystemExit(
            f"{context['slug']} is in stage `{stage}`, so a follow-up email is not recommended automatically. "
            "Use --force only if you want a manual draft anyway."
        )
    if intent == "reply" and stage == "package_generated" and not force:
        raise SystemExit(
            f"{context['slug']} has no recruiter communication log yet. "
            "Use --force if you still want a generic reply draft."
        )


def build_email(context: dict[str, object], intent: str) -> tuple[str, str]:
    communication = context.get("communication", {})
    latest_inbound = communication.get("latest_inbound")
    latest_event = communication.get("latest_event")
    subject = ""
    if latest_inbound and getattr(latest_inbound, "subject", ""):
        subject = latest_inbound.subject
    elif latest_event and getattr(latest_event, "subject", ""):
        subject = latest_event.subject
    subject = subject or fallback_subject(intent, str(context["job_title"]))

    if intent == "followup":
        body = followup_body(context)
    else:
        status = ""
        if latest_inbound:
            status = latest_inbound.status.lower()
        elif latest_event:
            status = latest_event.status.lower()
        if any(token in status for token in ["rejected", "declined", "closed"]):
            body = rejection_reply_body(context)
        else:
            body = generic_reply_body(context)
    return subject, body


def main() -> int:
    args = parse_args()
    context = context_by_slug(args.slug, follow_up_days=args.follow_up_days)
    intent = choose_intent(context, args.intent, args.force)
    validate_context_for_intent(context, intent, args.force)
    subject, body = build_email(context, intent)

    output_dir = DATA_ROOT / "email-drafts"
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{context['slug']}-{intent}.md"
    json_path = output_dir / f"{context['slug']}-{intent}.json"

    markdown = "\n".join(
        [
            f"# Email Draft: {context['company_name']}",
            "",
            f"- Slug: `{context['slug']}`",
            f"- Intent: `{intent}`",
            f"- Suggested from tracker: `{context['suggested_intent']}`",
            f"- Current stage: `{context['stage']}`",
            f"- Contact: `{context['contact_name'] or 'Hiring Team'}`",
            f"- Communication log: `{context['communication_log_path'] or 'none'}`",
            "",
            f"Subject: {subject}",
            "",
            "```text",
            body,
            "```",
            "",
        ]
    )

    payload = {
        "subject": subject,
        "body": body,
        "intent": intent,
        "context": context_snapshot(context),
    }
    write_text(md_path, markdown)
    write_json(json_path, payload)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
