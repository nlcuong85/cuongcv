#!/usr/bin/env python3

from __future__ import annotations

import argparse

from application_context import build_application_contexts
from common import DATA_ROOT, replace_tabs, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--follow-up-days", type=int, default=7)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contexts = build_application_contexts(follow_up_days=args.follow_up_days)

    header = [
        "slug",
        "company_name",
        "job_title",
        "primary_role",
        "stage",
        "next_action",
        "suggested_intent",
        "follow_up_due",
        "days_since_anchor",
        "contact_name",
        "package_generated_on",
        "communication_log",
        "latest_cv_pdf",
        "latest_cover_letter_pdf",
    ]
    tsv_lines = ["\t".join(header)]

    stage_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}
    due_rows = 0
    md_lines = [
        "# Interaction Tracker",
        "",
        f"Generated from `application-system/outputs/*` using a follow-up threshold of `{args.follow_up_days}` days.",
        "",
        "## Summary",
        "",
    ]

    for context in contexts:
        stage = context["stage"]
        action = context["next_action"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        action_counts[action] = action_counts.get(action, 0) + 1
        if context["follow_up_due"]:
            due_rows += 1

        tsv_lines.append(
            "\t".join(
                replace_tabs(value)
                for value in [
                    context["slug"],
                    context["company_name"],
                    context["job_title"],
                    context["primary_role"],
                    stage,
                    action,
                    context["suggested_intent"],
                    "yes" if context["follow_up_due"] else "no",
                    context["days_since_anchor"],
                    context["contact_name"],
                    context["package_generated_on"],
                    context["communication_log_path"],
                    context["latest_cv_pdf"],
                    context["latest_cover_letter_pdf"],
                ]
            )
        )

    md_lines.extend(
        [
            f"- Total application output folders: {len(contexts)}",
            f"- Follow-up due now: {due_rows}",
            "",
            "## Stage Counts",
            "",
        ]
    )
    for stage, count in sorted(stage_counts.items()):
        md_lines.append(f"- `{stage}`: {count}")

    md_lines.extend(["", "## Next Actions", ""])
    for action, count in sorted(action_counts.items()):
        md_lines.append(f"- `{action}`: {count}")

    md_lines.extend(["", "## Priority Rows", ""])
    priority_contexts = [
        context
        for context in contexts
        if context["follow_up_due"] or context["next_action"] in {"draft_reply", "reply_optional", "send_initial_application"}
    ]
    if not priority_contexts:
        md_lines.append("- No immediate recruiter action is due from the current logs.")
    else:
        for context in priority_contexts:
            md_lines.append(
                f"- `{context['slug']}` | {context['company_name']} | {context['job_title']} | "
                f"{context['stage']} | next: `{context['next_action']}`"
            )

    write_text(DATA_ROOT / "interaction-tracker.tsv", "\n".join(tsv_lines) + "\n")
    write_text(DATA_ROOT / "interaction-tracker.md", "\n".join(md_lines) + "\n")
    print(f"Wrote interaction tracker to {DATA_ROOT / 'interaction-tracker.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
