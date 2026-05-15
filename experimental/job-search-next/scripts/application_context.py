from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from common import OUTPUT_ROOT, REPO_ROOT, current_corpus, load_json, normalize_key, normalize_spaces


ROLE_LABELS = {
    "product_manager": "product delivery and prioritization",
    "product_owner": "backlog ownership and delivery coordination",
    "business_analyst": "business analysis and stakeholder translation",
    "requirements_process": "requirements, process design, and structured handovers",
    "process_automation": "workflow automation and process improvement",
    "pmo_delivery_support": "project coordination and delivery support",
    "quality_compliance_ops": "quality, compliance, and process operations",
    "ai_product_ops": "AI-enabled workflow and operations support",
    "implementation_enablement": "implementation enablement and documentation",
    "workflow_operations_analyst": "workflow analysis and operations support",
}


@dataclass
class CommunicationEvent:
    logged_date: str
    heading: str
    direction: str
    status: str
    reply_needed: str
    contact: str
    event_type: str
    subject: str
    summary: str
    incoming_message: str
    draft_reply: str
    index: int


def extract_iso_date(text: str) -> str:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text or "")
    return match.group(1) if match else ""


def safe_date(text: str) -> date | None:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def file_date(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def first_non_empty(*values: str) -> str:
    for value in values:
        cleaned = normalize_spaces(value)
        if cleaned:
            return cleaned
    return ""


def markdown_code_block_after(text: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\s*\n\s*```(?:text)?\n(.*?)```"
    match = re.search(pattern, text, flags=re.DOTALL)
    return normalize_spaces(match.group(1)) if match else ""


def blockquote_after(text: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\s*\n((?:>\s?.*\n?)+)"
    match = re.search(pattern, text)
    if not match:
        return ""
    lines = [line[1:].strip() for line in match.group(1).splitlines() if line.startswith(">")]
    return normalize_spaces(" ".join(lines))


def parse_communication_section(section_text: str, heading: str, index: int) -> CommunicationEvent:
    lines = section_text.splitlines()
    line_map: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if ":" in stripped:
                label, value = stripped[2:].split(":", 1)
                line_map[label.strip().lower()] = normalize_spaces(value)

    summary_match = re.search(r"-\s+Summary:\s*(.+)", section_text)
    if "### Inbound" in section_text:
        direction = "inbound"
    elif "### Outbound" in section_text:
        direction = "outbound"
    else:
        direction_raw = line_map.get("direction", "")
        if "incoming" in direction_raw.lower() or "inbound" in direction_raw.lower():
            direction = "inbound"
        elif "outgoing" in direction_raw.lower() or "outbound" in direction_raw.lower():
            direction = "outbound"
        else:
            direction = ""

    contact = first_non_empty(line_map.get("from", ""), line_map.get("to", ""), line_map.get("contact", ""))
    event_type = first_non_empty(line_map.get("type", ""), line_map.get("source note", ""))
    return CommunicationEvent(
        logged_date=first_non_empty(extract_iso_date(heading), line_map.get("logged on", "")),
        heading=heading,
        direction=direction,
        status=first_non_empty(line_map.get("status", ""), "unknown"),
        reply_needed=first_non_empty(line_map.get("reply needed", ""), ""),
        contact=contact,
        event_type=event_type,
        subject=first_non_empty(line_map.get("subject", ""), ""),
        summary=normalize_spaces(summary_match.group(1)) if summary_match else "",
        incoming_message=first_non_empty(
            blockquote_after(section_text, "Incoming message:"),
            blockquote_after(section_text, "### Incoming Email"),
        ),
        draft_reply=first_non_empty(
            markdown_code_block_after(section_text, "### Draft Reply"),
            markdown_code_block_after(section_text, "### Suggested Reply"),
            markdown_code_block_after(section_text, "Draft email:"),
        ),
        index=index,
    )


def parse_communication_log(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {
            "path": "",
            "events": [],
            "latest_event": None,
            "latest_inbound": None,
            "latest_outbound": None,
            "inbound_count": 0,
            "outbound_count": 0,
        }

    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^##\s+", text, flags=re.MULTILINE)
    events: list[CommunicationEvent] = []
    for index, part in enumerate(parts[1:], start=1):
        lines = part.splitlines()
        if not lines:
            continue
        heading = normalize_spaces(lines[0])
        section_text = "\n".join(lines[1:])
        events.append(parse_communication_section(section_text, heading, index))

    events.sort(key=lambda event: (event.logged_date or "9999-12-31", event.index))
    latest_event = events[-1] if events else None
    latest_inbound = next((event for event in reversed(events) if event.direction == "inbound"), None)
    latest_outbound = next((event for event in reversed(events) if event.direction == "outbound"), None)
    return {
        "path": str(path),
        "events": events,
        "latest_event": latest_event,
        "latest_inbound": latest_inbound,
        "latest_outbound": latest_outbound,
        "inbound_count": sum(1 for event in events if event.direction == "inbound"),
        "outbound_count": sum(1 for event in events if event.direction == "outbound"),
    }


def latest_pdf_path(path: Path) -> str:
    if not path.exists():
        return ""
    pdfs = sorted(path.glob("*.pdf"), key=lambda item: item.stat().st_mtime, reverse=True)
    return str(pdfs[0]) if pdfs else ""


def infer_stage(communication: dict[str, Any], follow_up_days: int) -> dict[str, Any]:
    events: list[CommunicationEvent] = communication.get("events", [])
    latest_event: CommunicationEvent | None = communication.get("latest_event")
    latest_inbound: CommunicationEvent | None = communication.get("latest_inbound")
    latest_outbound: CommunicationEvent | None = communication.get("latest_outbound")

    stage = "package_generated"
    next_action = "confirm_if_application_was_sent"
    suggested_intent = "none"
    follow_up_due = False
    days_since_anchor = ""

    if latest_event:
        anchor_date = safe_date(latest_event.logged_date)
        if anchor_date:
            days_since_anchor = str((date.today() - anchor_date).days)

        status_lower = latest_event.status.lower()
        reply_lower = latest_event.reply_needed.lower()
        type_lower = latest_event.event_type.lower()

        if any(token in status_lower for token in ["rejected", "declined", "closed"]):
            stage = "closed_rejected"
            next_action = "archive_or_reapply_later"
            suggested_intent = "reply" if "optional" in reply_lower else "none"
        elif latest_event.direction == "outbound" and "draft ready to send" in status_lower:
            stage = "draft_ready_to_send"
            next_action = "send_initial_application"
        elif latest_event.direction == "outbound":
            stage = "submitted_waiting"
            next_action = "wait_for_response"
            suggested_intent = "followup"
        elif latest_event.direction == "inbound":
            if "optional" in reply_lower or "not required" in reply_lower:
                stage = "reply_optional"
                next_action = "reply_optional"
                suggested_intent = "reply"
            else:
                stage = "reply_pending"
                next_action = "draft_reply"
                suggested_intent = "reply"

        if stage == "submitted_waiting" and latest_outbound and latest_outbound.logged_date:
            outbound_date = safe_date(latest_outbound.logged_date)
            inbound_date = safe_date(latest_inbound.logged_date) if latest_inbound else None
            if outbound_date:
                elapsed_days = (date.today() - outbound_date).days
                days_since_anchor = str(elapsed_days)
                if not inbound_date or inbound_date < outbound_date:
                    follow_up_due = elapsed_days >= follow_up_days
                    if follow_up_due:
                        next_action = "draft_follow_up"
                        suggested_intent = "followup"

        if latest_event.direction == "inbound" and "initial application" in type_lower:
            stage = "submitted_waiting"

        onboarding_signal = any(
            any(
                token in " ".join([event.status, event.event_type, event.summary]).lower()
                for token in [
                    "hiring task closed",
                    "preparation for planned employment",
                    "joiner",
                    "verbal offer received",
                ]
            )
            for event in events
        )
        if onboarding_signal and stage != "closed_rejected":
            stage = "onboarding_pending"
            next_action = "wait_or_follow_up_on_contract"
            suggested_intent = "followup"
            if anchor_date:
                follow_up_due = (date.today() - anchor_date).days >= follow_up_days

    return {
        "stage": stage,
        "next_action": next_action,
        "suggested_intent": suggested_intent,
        "follow_up_due": follow_up_due,
        "days_since_anchor": days_since_anchor,
    }


def build_application_contexts(follow_up_days: int = 7) -> list[dict[str, Any]]:
    corpus_items = current_corpus()
    corpus_by_output = {
        item.get("output_dir", ""): item
        for item in corpus_items
        if normalize_spaces(item.get("output_dir", ""))
    }
    corpus_by_key = {
        normalize_key(item.get("company_name", ""), item.get("job_title", "")): item
        for item in corpus_items
    }

    contexts: list[dict[str, Any]] = []
    for manifest_path in sorted(OUTPUT_ROOT.glob("*/manifest.json")):
        manifest = load_json(manifest_path)
        output_dir = manifest_path.parent
        output_key = str(output_dir.relative_to(OUTPUT_ROOT.parent))
        company_name = manifest.get("company_name", "")
        job_title = manifest.get("job_title", "")
        key = normalize_key(company_name, job_title)
        corpus_item = corpus_by_output.get(output_key) or corpus_by_key.get(key) or {}

        communication_path = output_dir / "communication-log.md"
        communication = parse_communication_log(communication_path if communication_path.exists() else None)
        latest_cv_pdf = ""
        for variant in manifest.get("cv_variants", []):
            pdf_path = normalize_spaces(variant.get("pdf_path", ""))
            if pdf_path:
                latest_cv_pdf = str((REPO_ROOT / pdf_path).resolve())
        if not latest_cv_pdf:
            latest_cv_pdf = latest_pdf_path(output_dir / "cv")

        latest_cover_letter_pdf = latest_pdf_path(output_dir / "cover-letter")
        stage_info = infer_stage(communication, follow_up_days)
        primary_role = manifest.get("primary_role", "") or corpus_item.get("primary_role", "")
        contact_name = first_non_empty(
            corpus_item.get("contact_name", ""),
            getattr(communication.get("latest_event"), "contact", ""),
            getattr(communication.get("latest_inbound"), "contact", ""),
            getattr(communication.get("latest_outbound"), "contact", ""),
        )
        role_keywords = manifest.get("skill_assessment", {}).get("role_fit_keywords", []) or []
        contexts.append(
            {
                "slug": output_dir.name,
                "company_name": company_name,
                "job_title": job_title,
                "primary_role": primary_role,
                "role_anchor": first_non_empty(
                    ", ".join(role_keywords),
                    ROLE_LABELS.get(primary_role, ""),
                    primary_role.replace("_", " "),
                ),
                "summary_version": manifest.get("summary_version", ""),
                "output_dir": str(output_dir),
                "manifest_path": str(manifest_path),
                "communication_log_path": str(communication_path) if communication_path.exists() else "",
                "contact_name": contact_name,
                "job_url": corpus_item.get("job_url", ""),
                "intake_path": corpus_item.get("intake_path", ""),
                "package_generated_on": file_date(manifest_path),
                "latest_cv_pdf": latest_cv_pdf,
                "latest_cover_letter_pdf": latest_cover_letter_pdf,
                "communication": communication,
                **stage_info,
            }
        )

    return contexts


def context_by_slug(slug: str, follow_up_days: int = 7) -> dict[str, Any]:
    target = normalize_spaces(slug)
    for context in build_application_contexts(follow_up_days=follow_up_days):
        if context["slug"] == target:
            return context
    raise KeyError(f"No application output found for slug: {slug}")


def contexts_by_job_url(follow_up_days: int = 7) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for context in build_application_contexts(follow_up_days=follow_up_days):
        job_url = normalize_spaces(context.get("job_url", "")).lower()
        if job_url:
            mapping[job_url] = context
    return mapping


def event_to_dict(event: CommunicationEvent | None) -> dict[str, Any] | None:
    if not event:
        return None
    return {
        "logged_date": event.logged_date,
        "heading": event.heading,
        "direction": event.direction,
        "status": event.status,
        "reply_needed": event.reply_needed,
        "contact": event.contact,
        "event_type": event.event_type,
        "subject": event.subject,
        "summary": event.summary,
        "incoming_message": event.incoming_message,
        "draft_reply": event.draft_reply,
        "index": event.index,
    }


def context_snapshot(context: dict[str, Any]) -> dict[str, Any]:
    snapshot = dict(context)
    communication = snapshot.get("communication", {})
    snapshot["communication"] = {
        "path": communication.get("path", ""),
        "events": [event_to_dict(event) for event in communication.get("events", [])],
        "latest_event": event_to_dict(communication.get("latest_event")),
        "latest_inbound": event_to_dict(communication.get("latest_inbound")),
        "latest_outbound": event_to_dict(communication.get("latest_outbound")),
        "inbound_count": communication.get("inbound_count", 0),
        "outbound_count": communication.get("outbound_count", 0),
    }
    return json.loads(json.dumps(snapshot, ensure_ascii=True))
