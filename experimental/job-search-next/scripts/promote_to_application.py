#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv

from common import (
    APPLICATION_ROOT,
    DATA_ROOT,
    PROMOTIONS_ROOT,
    all_leads,
    replace_tabs,
    slugify,
    write_json,
    write_text,
)


SUMMARY_BY_ROLE = {
    "business_analyst": "business_analysis",
    "requirements_process": "business_analysis",
    "process_automation": "strongest_balanced",
    "ai_product_ops": "strongest_balanced",
    "implementation_enablement": "strongest_balanced",
    "workflow_operations_analyst": "business_analysis",
    "product_manager": "product_delivery",
    "product_owner": "product_delivery",
    "pmo_delivery_support": "product_delivery",
    "quality_compliance_ops": "german_market_conservative",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lead-id")
    parser.add_argument("--write-intake", action="store_true")
    parser.add_argument("--write-live-intake", action="store_true")
    parser.add_argument("--allow-review", action="store_true")
    return parser.parse_args()


def build_draft_intake(lead: dict[str, str], tracker_row: dict[str, str]) -> dict[str, object]:
    predicted_role = tracker_row.get("predicted_role", "") or lead.get("primary_role", "")
    summary_version = SUMMARY_BY_ROLE.get(predicted_role, "strongest_balanced")
    return {
        "company_name": lead.get("company_name", ""),
        "company_location": lead.get("company_location", ""),
        "contact_name": lead.get("contact_name", ""),
        "contact_title": "",
        "contact_lookup_status": lead.get("contact_lookup_status", "")
        or "No named recruiter or contact has been verified yet in the prototype flow, so the draft intake uses a fallback contact until live lookup is completed.",
        "job_title": lead.get("job_title", ""),
        "job_url": lead.get("job_url", ""),
        "job_description": lead.get("job_description", ""),
        "requirements": lead.get("requirements", []) or [],
        "language": lead.get("language", "english"),
        "primary_role": predicted_role,
        "summary_version": summary_version,
        "target_roles": lead.get("target_roles", []) or [predicted_role],
        "why_company": "",
        "cover_letter_opening": "",
        "cover_letter_motivation": "",
        "cover_letter_body_one": "",
        "cover_letter_body_two": "",
        "cover_letter_closing": "",
        "prototype_origin": "experimental/job-search-next",
        "prototype_lead_id": lead.get("lead_id", ""),
    }


def main() -> int:
    args = parse_args()
    tracker_path = DATA_ROOT / "tracker.tsv"
    if not tracker_path.exists():
        raise SystemExit(f"Missing tracker file: {tracker_path}")

    if args.write_live_intake and not args.write_intake:
        raise SystemExit("--write-live-intake requires --write-intake")

    with tracker_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    leads_by_id = {lead.get("lead_id", ""): lead for lead in all_leads(include_current=True, include_raw=True)}

    header = [
        "lead_id",
        "decision",
        "predicted_role",
        "promotion_status",
        "existing_intake_path",
        "existing_output_dir",
        "draft_payload_path",
        "notes",
    ]
    tsv_lines = ["\t".join(header)]
    preview_lines = [
        "# Promotion Preview",
        "",
        "This is a read-only bridge from the experimental tracker to the current application workflow.",
        "",
    ]
    matched_any = False

    for row in rows:
        decision = row.get("decision", "")
        if decision not in {"keep", "review"}:
            continue
        if args.lead_id and row.get("lead_id") != args.lead_id:
            continue
        matched_any = True

        lead_id = row.get("lead_id", "")
        predicted_role = row.get("predicted_role", "")
        existing_intake = row.get("existing_intake_path", "")
        existing_output = row.get("existing_output_dir", "")
        lead = leads_by_id.get(lead_id, {})

        if args.write_intake and lead:
            if decision == "review" and not args.allow_review:
                if args.lead_id:
                    raise SystemExit(
                        f"Lead {lead_id} is marked review. Re-run with --allow-review if you want a draft intake."
                    )
                promotion_status = "review_blocked"
                draft_path = ""
                note = "Review leads are not promoted unless --allow-review is provided."
            else:
                draft_payload = build_draft_intake(lead, row)
                draft_name = f"{slugify(lead_id or row.get('job_title', 'lead'))}.json"
                draft_abs_path = PROMOTIONS_ROOT / "intakes" / draft_name
                write_json(draft_abs_path, draft_payload)
                draft_path = str(draft_abs_path.relative_to(PROMOTIONS_ROOT.parent))
                live_intake_path = ""
                if args.write_live_intake:
                    live_name = f"draft-{draft_name}"
                    live_abs_path = APPLICATION_ROOT / "intakes" / live_name
                    write_json(live_abs_path, draft_payload)
                    live_intake_path = str(live_abs_path.relative_to(APPLICATION_ROOT.parent))
                if existing_intake or existing_output:
                    if live_intake_path:
                        promotion_status = "live_intake_written_from_existing_match"
                        note = f"Draft intake written in prototype and live intake folder: {live_intake_path}"
                    else:
                        promotion_status = "draft_written_from_existing_match"
                        note = "Draft intake written in prototype folder; live application already exists"
                else:
                    if live_intake_path:
                        promotion_status = "live_intake_written"
                        note = f"Draft intake written in prototype and live intake folder: {live_intake_path}"
                    else:
                        promotion_status = "draft_written"
                        note = "Draft intake written in prototype folder"
        elif existing_intake or existing_output:
            promotion_status = "existing_application"
            draft_path = ""
            note = "Matched to current application corpus"
        else:
            promotion_status = "draft_needed"
            draft_path = ""
            note = "No live intake/output match; run with --write-intake to create a draft intake"

        preview_lines.append(
            f"- {row.get('company_name', '')} | {row.get('job_title', '')} | {decision} | {promotion_status}"
        )
        preview_lines.append(f"  intake: {existing_intake or 'none'}")
        preview_lines.append(f"  output: {existing_output or 'none'}")
        preview_lines.append(f"  draft: {draft_path or 'none'}")

        tsv_lines.append(
            "\t".join(
                replace_tabs(value)
                for value in [
                    lead_id,
                    decision,
                    predicted_role,
                    promotion_status,
                    existing_intake,
                    existing_output,
                    draft_path,
                    note,
                ]
            )
        )

    preview_lines.append("")
    if args.lead_id and not matched_any:
        raise SystemExit(
            f"Lead {args.lead_id} is not promotable from the current tracker. "
            "It may be reject, missing, or outside the selected scan set."
        )
    write_text(DATA_ROOT / "promotion-preview.md", "\n".join(preview_lines))
    write_text(DATA_ROOT / "promotion-map.tsv", "\n".join(tsv_lines) + "\n")
    print(f"Wrote promotion preview to {DATA_ROOT / 'promotion-preview.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
