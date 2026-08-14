#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


WEAK_PHRASES = [
    "to whom it may concern",
    "i am passionate about innovation",
    "i believe i am a good fit",
    "i think i would be a good fit",
    "dynamic and fast-paced environment",
    "as a highly motivated individual",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def audit(root: Path, draft_path: Path) -> list[str]:
    issues: list[str] = []
    text = draft_path.read_text(encoding="utf-8", errors="ignore")
    lowered = text.lower()

    for phrase in WEAK_PHRASES:
        if phrase in lowered:
            issues.append(f"Draft contains weak or generic phrase: `{phrase}`.")

    words = word_count(text)
    if words > 650:
        issues.append(f"Draft is long for a cover letter or recruiter note: {words} words.")

    profile_path = root / "profile" / "master_profile.json"
    if profile_path.exists():
        profile = load_json(profile_path)
        full_name = profile.get("identity", {}).get("full_name")
        preferred_name = profile.get("identity", {}).get("preferred_name")
        if full_name and full_name not in text and preferred_name and preferred_name not in text:
            issues.append("Draft does not contain the person's full or preferred name.")

        must_not_claim = profile.get("constraints", {}).get("must_not_claim", [])
        for claim in must_not_claim:
            if claim and claim.lower() in lowered:
                issues.append(f"Draft appears to include a forbidden or unsupported claim: `{claim}`.")

    if re.search(r"\b(native|fluent|expert|senior|lead)\b", lowered):
        issues.append("Draft uses a strong capability word. Verify it is supported by the profile or evidence library.")

    return issues


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: audit_application.py <digital-twin-root> <draft-path>")
        return 2

    root = Path(sys.argv[1]).resolve()
    draft_path = Path(sys.argv[2]).resolve()

    if not draft_path.exists():
        print(f"ERROR: draft not found: {draft_path}")
        return 2

    issues = audit(root, draft_path)
    if issues:
        print("Application audit warnings:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Application audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
