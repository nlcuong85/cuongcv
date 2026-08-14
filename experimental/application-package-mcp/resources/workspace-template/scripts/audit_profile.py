#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_PROFILE_SECTIONS = [
    "identity",
    "contact",
    "education",
    "work_history",
    "projects",
    "skills",
    "languages",
    "target_directions",
    "constraints",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def audit_profile(root: Path) -> list[str]:
    issues: list[str] = []
    profile_path = root / "profile" / "master_profile.json"
    evidence_path = root / "profile" / "evidence_library.json"

    if not profile_path.exists():
        add_issue(issues, "Missing profile/master_profile.json. Copy master_profile.example.json and fill it.")
        return issues

    profile = load_json(profile_path)

    for section in REQUIRED_PROFILE_SECTIONS:
        if section not in profile:
            add_issue(issues, f"Missing required profile section: {section}")

    identity = profile.get("identity", {})
    if not identity.get("full_name"):
        add_issue(issues, "identity.full_name is empty.")
    if not identity.get("preferred_name"):
        add_issue(issues, "identity.preferred_name is empty.")

    skills = profile.get("skills", {})
    if not skills.get("core"):
        add_issue(issues, "skills.core is empty.")

    languages = profile.get("languages", [])
    for item in languages:
        if not item.get("language") or not item.get("level"):
            add_issue(issues, "Every language entry needs language and level.")

    for project in profile.get("projects", []):
        for evidence_id in project.get("evidence_ids", []):
            if not evidence_path.exists():
                add_issue(issues, f"Project {project.get('name', '<unnamed>')} references evidence but evidence_library.json is missing.")
                continue

    if not evidence_path.exists():
        add_issue(issues, "Missing profile/evidence_library.json. Copy evidence_library.example.json and fill it.")
        return issues

    evidence = load_json(evidence_path).get("evidence", [])
    evidence_ids = {item.get("id") for item in evidence}

    for project in profile.get("projects", []):
        for evidence_id in project.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                add_issue(issues, f"Project {project.get('name', '<unnamed>')} references unknown evidence id: {evidence_id}")

    for item in evidence:
        if not item.get("id"):
            add_issue(issues, "Evidence item is missing id.")
        if not item.get("claim"):
            add_issue(issues, f"Evidence item {item.get('id', '<unknown>')} is missing claim.")
        if not item.get("source"):
            add_issue(issues, f"Evidence item {item.get('id', '<unknown>')} is missing source.")
        if item.get("strength") not in {"strong", "medium", "weak"}:
            add_issue(issues, f"Evidence item {item.get('id', '<unknown>')} needs strength: strong, medium, or weak.")

    return issues


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    issues = audit_profile(root)

    if issues:
        print("Profile audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Profile audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
