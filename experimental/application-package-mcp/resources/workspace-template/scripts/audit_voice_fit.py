#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


GENERIC_PHRASES = [
    "the present study",
    "the current study",
    "it is imperative",
    "a plethora of",
    "multifaceted",
    "robust framework",
    "in today's globalized world",
    "plays a crucial role",
    "cutting-edge",
    "holistic",
    "transformative",
    "dynamic landscape",
    "optimize outcomes",
    "maximize value",
]

INFLATED_PHRASES = [
    "leveraging",
    "high-precision",
    "preponderance",
    "profound implications",
    "volatile economic landscapes",
    "stakeholder ecosystem",
    "world-class",
]


def sentence_lengths(text: str) -> list[int]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [len(re.findall(r"\b[\w'-]+\b", sentence)) for sentence in sentences if sentence.strip()]


def strip_reference_blocks(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("- "):
            continue
        lines.append(line)
    return "\n".join(lines)


def audit(text: str, mode: str) -> list[str]:
    issues: list[str] = []
    auditable_text = strip_reference_blocks(text)
    lowered = auditable_text.lower()

    for phrase in GENERIC_PHRASES:
        if phrase in lowered:
            issues.append(f"Generic or over-polished phrase found: `{phrase}`.")

    for phrase in INFLATED_PHRASES:
        if phrase in lowered:
            issues.append(f"Inflated phrase found: `{phrase}`.")

    lengths = sentence_lengths(auditable_text)
    if lengths:
        average = sum(lengths) / len(lengths)
        if average > 30:
            issues.append(f"Average sentence length is high: {average:.1f} words.")
        long_sentences = [length for length in lengths if length > 42]
        if long_sentences:
            issues.append(f"{len(long_sentences)} sentence(s) are longer than 42 words; simplify where possible.")

    if mode == "academic":
        practical_context_markers = [
            "student",
            "teacher",
            "household",
            "family",
            "bank",
            "government",
            "community",
            "company",
            "user",
            "process",
            "department",
        ]
        if not any(marker in lowered for marker in practical_context_markers):
            issues.append("Academic draft may be too detached from practical reality; mention the affected people, process, or setting when relevant.")

        if "limitation" not in lowered and "limited" not in lowered and "should be interpreted carefully" not in lowered and "however" not in lowered:
            issues.append("Academic draft lacks an explicit limitation or caution boundary.")

    if mode == "application":
        if "i " not in lowered and "my " not in lowered:
            issues.append("Application draft may be too detached; include a concrete first-person evidence anchor when appropriate.")
        if not re.search(r"\b(project|worked|built|analyzed|supported|created|tested|documented)\b", lowered):
            issues.append("Application draft lacks concrete work or project evidence.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit selected writing against the student's local voice notes.")
    parser.add_argument("path", help="Draft file to audit")
    parser.add_argument("--mode", default="academic", choices=["academic", "application", "work", "social", "personal", "blog"])
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: draft not found: {path}")
        return 2

    issues = audit(path.read_text(encoding="utf-8", errors="ignore"), args.mode)
    if issues:
        print("Voice-fit audit warnings:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Voice-fit audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

