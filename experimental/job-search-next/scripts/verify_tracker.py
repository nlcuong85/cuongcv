#!/usr/bin/env python3

from __future__ import annotations

import csv
from collections import Counter

from common import DATA_ROOT, role_match_status, write_text


REQUIRED_COLUMNS = [
    "lead_id",
    "source",
    "company_name",
    "job_title",
    "job_url",
    "source_domain",
    "predicted_role",
    "expected_role",
    "role_match",
    "job_mode",
    "decision",
    "fit_score",
    "location_status",
    "language_signal",
    "strong_german_required",
    "company_priority",
    "existing_intake_path",
    "existing_output_dir",
    "reasons",
]


def main() -> int:
    tracker_path = DATA_ROOT / "tracker.tsv"
    if not tracker_path.exists():
        raise SystemExit(f"Missing tracker file: {tracker_path}")

    with tracker_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        errors.append("tracker.tsv has no data rows")

    seen_ids: set[str] = set()
    decision_counts = Counter()
    comparable = 0
    exact_matches = 0
    compatible_matches = 0
    with_outputs = 0

    for row in rows:
        for column in REQUIRED_COLUMNS:
            if column not in row:
                errors.append(f"Missing required column: {column}")
                break

        lead_id = row.get("lead_id", "")
        if lead_id in seen_ids:
            errors.append(f"Duplicate lead_id: {lead_id}")
        seen_ids.add(lead_id)

        decision = row.get("decision", "")
        if decision not in {"keep", "review", "reject"}:
            errors.append(f"Invalid decision for {lead_id}: {decision}")
        decision_counts[decision] += 1

        try:
            fit_score = int(row.get("fit_score", "0"))
        except ValueError:
            errors.append(f"Non-integer fit_score for {lead_id}: {row.get('fit_score')}")
            fit_score = 0
        if fit_score < 0 or fit_score > 100:
            errors.append(f"fit_score out of range for {lead_id}: {fit_score}")

        expected_role = row.get("expected_role", "")
        predicted_role = row.get("predicted_role", "")
        if expected_role:
            comparable += 1
            match_status = role_match_status(expected_role, predicted_role)
            if match_status == "exact":
                exact_matches += 1
                compatible_matches += 1
            elif match_status == "compatible":
                compatible_matches += 1

        if row.get("existing_output_dir"):
            with_outputs += 1

    exact_accuracy = (exact_matches / comparable * 100.0) if comparable else 0.0
    compatible_accuracy = (compatible_matches / comparable * 100.0) if comparable else 0.0
    if comparable and compatible_accuracy < 70.0:
        warnings.append(
            "Role-family matching is still weak against current expectations: "
            f"exact={exact_accuracy:.1f}% compatible={compatible_accuracy:.1f}%"
        )

    report_lines = [
        "# Verification Report",
        "",
        f"- Rows checked: {len(rows)}",
        f"- Comparable expectation rows: {comparable}",
        f"- Role-family exact accuracy: {exact_accuracy:.1f}%",
        f"- Role-family compatible accuracy: {compatible_accuracy:.1f}%",
        f"- Rows linked to existing outputs: {with_outputs}",
        f"- Decisions: keep={decision_counts['keep']}, review={decision_counts['review']}, reject={decision_counts['reject']}",
        "",
    ]

    if errors:
        report_lines.append("## Errors")
        report_lines.append("")
        report_lines.extend(f"- {error}" for error in errors)
        report_lines.append("")

    if warnings:
        report_lines.append("## Warnings")
        report_lines.append("")
        report_lines.extend(f"- {warning}" for warning in warnings)
        report_lines.append("")

    if not errors and not warnings:
        report_lines.append("## Status")
        report_lines.append("")
        report_lines.append("- Tracker validation passed cleanly.")
        report_lines.append("")

    write_text(DATA_ROOT / "verification_report.md", "\n".join(report_lines))
    print("\n".join(report_lines))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
