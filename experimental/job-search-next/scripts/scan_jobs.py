#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import Counter

from common import (
    CONFIG_ROOT,
    DATA_ROOT,
    all_leads,
    load_yaml,
    normalize_spaces,
    replace_tabs,
    role_match_status,
    source_domain,
    write_text,
)


def detect_job_mode(title: str, text: str) -> str:
    haystack = f"{title} {text}".lower()
    if "working student" in haystack or "werkstudent" in haystack:
        return "working_student"
    if "intern" in haystack or "praktikum" in haystack:
        return "internship"
    if "part time" in haystack or "teilzeit" in haystack:
        return "part_time"
    return "full_time"


def location_status(
    location: str,
    allowed_country: str,
    preferred_states: list[str],
    preferred_location_terms: list[str],
) -> str:
    lower = (location or "").lower()
    country = allowed_country.lower()
    if not lower:
        return "unknown"
    if "remote" in lower:
        return "remote"
    if country not in lower and "germany" not in lower:
        return "outside_country"
    if any(term.lower() in lower for term in preferred_location_terms):
        return "preferred_scope"
    if any(state.lower() in lower for state in preferred_states):
        return "preferred_state"
    return "country_ok"


def detect_language_signal(language: str, text: str) -> str:
    haystack = f"{language} {text}".lower()
    if "english" in haystack:
        return "english"
    if "german" in haystack or "deutsch" in haystack:
        return "german_or_mixed"
    return "unknown"


def has_pattern(text: str, patterns: list[str]) -> bool:
    haystack = normalize_spaces(text).lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def has_explicit_strong_german(text: str, patterns: list[str]) -> bool:
    haystack = normalize_spaces(text).lower()
    negated_markers = [
        "without explicit strong german requirement",
        "without an explicit strong german requirement",
        "without explicit fluent german requirement",
        "without an explicit fluent german requirement",
        "no explicit strong german requirement",
        "no explicit fluent german requirement",
    ]
    if any(marker in haystack for marker in negated_markers):
        return False
    return any(pattern.lower() in haystack for pattern in patterns)


def classify_role(title: str, text: str, keyword_map: dict[str, list[str]]) -> tuple[str, int, dict[str, int]]:
    title_lower = normalize_spaces(title).lower()
    haystack = normalize_spaces(text).lower()

    title_first_rules = [
        ("product_owner", ["product owner"]),
        ("product_manager", ["product manager", "product management"]),
        ("implementation_enablement", ["instructional design", "technical writing", "solution delivery", "team support"]),
        ("workflow_operations_analyst", ["service operations analyst", "operations analyst", "life cycle management"]),
        ("process_automation", ["automation manager", "data-automation", "data automation", "automation"]),
        ("quality_compliance_ops", ["quality", "threat modelling", "threat modeling", "detection engineering"]),
        ("requirements_process", ["requirements engineering", "prozessmanagement", "process management"]),
        ("business_analyst", ["business analyst", "analytics", "controlling"]),
        ("ai_product_ops", ["genai", "llm", "agentic", " ai ", "for ai", "data & ai"]),
        ("pmo_delivery_support", ["project management", "project office", "pmo"]),
    ]
    for role, phrases in title_first_rules:
        if any(phrase in f" {title_lower} " for phrase in phrases):
            return role, 4, {role: 4}

    scores: dict[str, int] = {}
    for role, keywords in keyword_map.items():
        score = 0
        for keyword in keywords:
            lower = keyword.lower()
            if lower in title_lower:
                score += 3
            elif lower in haystack:
                score += 1
        scores[role] = score
    best_role = max(scores, key=scores.get) if scores else "unknown"
    return best_role, scores.get(best_role, 0), scores


def company_priority(company_name: str, tracked_companies: list[dict[str, str]]) -> str:
    lower = company_name.lower()
    for company in tracked_companies:
        if company["name"].lower() in lower:
            return company.get("priority", "normal")
    return "normal"


def decision_for_item(
    predicted_role: str,
    role_hits: int,
    preferred_roles: list[str],
    explicit_strong_german: bool,
    loc_status: str,
    job_mode: str,
    allowed_job_modes: list[str],
    priority: str,
) -> tuple[str, int, list[str]]:
    reasons: list[str] = []
    score = 0

    if predicted_role in preferred_roles:
        score += 35
        reasons.append("role family is in target set")
    else:
        reasons.append("role family is outside target set")

    score += min(role_hits, 6) * 8
    reasons.append(f"role keyword hits: {role_hits}")

    if explicit_strong_german:
        score -= 40
        reasons.append("explicit strong German requirement")

    if job_mode in allowed_job_modes:
        score += 10
        reasons.append(f"job mode allowed: {job_mode}")
    else:
        score -= 15
        reasons.append(f"job mode outside preferred set: {job_mode}")

    if loc_status == "preferred_state":
        score += 12
        reasons.append("location is in preferred state")
    elif loc_status in {"preferred_scope", "country_ok", "remote", "unknown"}:
        score += 6
        reasons.append(f"location acceptable: {loc_status}")
    else:
        score -= 20
        reasons.append("location outside allowed country")

    if priority == "high":
        score += 10
        reasons.append("company is high priority")
    elif priority == "medium":
        score += 5
        reasons.append("company is medium priority")

    if explicit_strong_german:
        return "reject", max(score, 0), reasons
    if predicted_role in preferred_roles and role_hits >= 2 and loc_status != "outside_country":
        return "keep", min(score, 100), reasons
    if predicted_role in preferred_roles or role_hits >= 2 or priority in {"high", "medium"}:
        return "review", min(max(score, 0), 100), reasons
    return "reject", min(max(score, 0), 100), reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-current-corpus", action="store_true")
    parser.add_argument("--from-raw-leads", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--source-prefix")
    args = parser.parse_args()

    if not (args.from_current_corpus or args.from_raw_leads or args.all):
        raise SystemExit("Use one of: --from-current-corpus, --from-raw-leads, --all")

    profile = load_yaml(CONFIG_ROOT / "profile.yml")
    portals = load_yaml(CONFIG_ROOT / "portals.yml")
    corpus = all_leads(
        include_current=args.from_current_corpus or args.all,
        include_raw=args.from_raw_leads or args.all,
    )
    if args.source_prefix:
        corpus = [item for item in corpus if str(item.get("source", "")).startswith(args.source_prefix)]

    policy = profile["search_policy"]
    preferred_roles = profile["role_targets"]["priority_role_families"]
    keyword_map = profile["role_targets"]["keyword_map"]
    language_policy = profile["language_policy"]
    tracked_companies = portals.get("tracked_companies", [])

    rows: list[list[str]] = []
    keep_lines: list[str] = []
    review_lines: list[str] = []
    reject_lines: list[str] = []

    for item in corpus:
        title = item.get("job_title", "")
        description = item.get("job_description", "")
        requirements = " ".join(item.get("requirements", []) or [])
        text = " ".join([title, description, requirements])
        predicted_role, role_hits, _ = classify_role(title, text, keyword_map)
        explicit_strong_german = has_explicit_strong_german(text, language_policy["explicit_strong_german_patterns"])
        loc_status = location_status(
            item.get("company_location", ""),
            policy["allowed_country"],
            policy["preferred_states"],
            policy.get("preferred_location_terms", []),
        )
        job_mode = detect_job_mode(title, text)
        lang_signal = detect_language_signal(item.get("language", ""), text)
        priority = company_priority(item.get("company_name", ""), tracked_companies)
        decision, fit_score, reasons = decision_for_item(
            predicted_role=predicted_role,
            role_hits=role_hits,
            preferred_roles=preferred_roles,
            explicit_strong_german=explicit_strong_german,
            loc_status=loc_status,
            job_mode=job_mode,
            allowed_job_modes=policy["allowed_job_modes"],
            priority=priority,
        )

        expected_role = item.get("expected_primary_role", "") or item.get("primary_role", "")
        role_match = role_match_status(expected_role, predicted_role)
        row = [
            item.get("lead_id", ""),
            item.get("source", ""),
            item.get("company_name", ""),
            title,
            item.get("job_url", ""),
            source_domain(item.get("job_url", "")),
            predicted_role,
            expected_role,
            role_match,
            job_mode,
            decision,
            str(fit_score),
            loc_status,
            lang_signal,
            "yes" if explicit_strong_german else "no",
            priority,
            item.get("intake_path", ""),
            item.get("output_dir", ""),
            " | ".join(reasons),
        ]
        rows.append(row)

        bullet = f"- [{decision}] {item.get('company_name', '')} | {title} | {predicted_role} | score {fit_score}"
        if decision == "keep":
            keep_lines.append(bullet)
        elif decision == "review":
            review_lines.append(bullet)
        else:
            reject_lines.append(bullet)

    header = (
        "lead_id\tsource\tcompany_name\tjob_title\tjob_url\tsource_domain\tpredicted_role\t"
        "expected_role\trole_match\tjob_mode\tdecision\tfit_score\tlocation_status\t"
        "language_signal\tstrong_german_required\tcompany_priority\texisting_intake_path\t"
        "existing_output_dir\treasons"
    )
    tracker_lines = [header]
    tracker_lines.extend("\t".join(replace_tabs(value) for value in row) for row in rows)
    write_text(DATA_ROOT / "tracker.tsv", "\n".join(tracker_lines) + "\n")

    pipeline_parts = [
        "# Experimental Job Pipeline",
        "",
        "## Keep",
        "",
        *(keep_lines or ["- none"]),
        "",
        "## Review",
        "",
        *(review_lines or ["- none"]),
        "",
        "## Reject",
        "",
        *(reject_lines or ["- none"]),
        "",
    ]
    write_text(DATA_ROOT / "pipeline.md", "\n".join(pipeline_parts))

    counts = Counter(row[10] for row in rows)
    source_label = "all leads" if args.all else "current corpus" if args.from_current_corpus else "raw leads"
    if args.source_prefix:
        source_label = f"{source_label} matching source prefix {args.source_prefix}"
    print(
        f"Scanned {len(rows)} jobs from {source_label}: "
        f"keep={counts['keep']} review={counts['review']} reject={counts['reject']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
