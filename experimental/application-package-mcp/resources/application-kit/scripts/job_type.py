#!/usr/bin/env python3
"""Conservative local job-type evidence extraction; never inspect candidate status."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = {
    "working-student": r"\b(?:werkstudent(?:in)?|working[ -]student|studentische[rs]? hilfskraft)\b",
    "internship": r"\b(?:internship|intern|praktikum|praktikant(?:in)?)\b",
    "full-time": r"\b(?:full[ -]time|vollzeit|40\s*(?:hours|stunden)\s*(?:per week|pro woche)|permanent full[ -]time)\b",
    "part-time": r"\b(?:part[ -]time|teilzeit)\b",
}
STRUCTURED = {
    "FULL_TIME": "full-time", "PART_TIME": "part-time", "INTERN": "internship",
}


def classify(text: str, employment_type: str = "") -> dict:
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        for kind, pattern in PATTERNS.items():
            if re.search(pattern, sentence, re.I):
                found.append({"type": kind, "evidence": sentence.strip()[:350]})
    structured = {STRUCTURED[token] for token in re.split(r"[\s,;]+", employment_type.upper()) if token in STRUCTURED}
    detected = set(structured) or {item["type"] for item in found}
    return {
        "status": "confirmed" if len(detected) == 1 else "ask_user",
        "employment_type": next(iter(detected)) if len(detected) == 1 else None,
        "evidence": found[:8], "structured_types": sorted(structured),
        "reason": "conflicting_or_ambiguous" if len(detected) > 1 else "not_stated" if not detected else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--employment-type", default="")
    args = parser.parse_args()
    print(json.dumps(classify(args.job.read_text(encoding="utf-8"), args.employment_type), indent=2))


if __name__ == "__main__":
    main()
