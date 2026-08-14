#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
DISPLAY_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)


def normalize_heading(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s*\{#[^}]+\}\s*$", "", text)
    text = re.sub(r"^\d+(\.\d+)*\s*", "", text)
    return re.sub(r"[^a-z0-9 ]+", "", text).strip()


def has_any_heading(text: str, options: list[str]) -> bool:
    normalized = [normalize_heading(m.group(2)) for m in HEADING_RE.finditer(text)]
    wanted = {normalize_heading(x) for x in options}
    return any(heading in wanted for heading in normalized)


def section_text(text: str, options: list[str]) -> str:
    headings = [(m.start(), m.group(2).strip()) for m in HEADING_RE.finditer(text)]
    wanted = {normalize_heading(x) for x in options}
    for index, (start, title) in enumerate(headings):
        if normalize_heading(title) in wanted:
            end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
            return text[start:end]
    return ""


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def audit(path: Path, docmost: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[dict] = []

    required_sections = {
        "abstract": ["abstract", "summary"],
        "introduction": ["introduction"],
        "problem": ["research problem", "problem statement", "research question", "problem formulation"],
        "literature": ["related literature", "literature review", "related work", "state of the art"],
        "method": ["methods", "methodology", "method", "model", "approach"],
        "discussion": ["discussion", "results", "results and discussion", "assessment"],
        "conclusion": ["conclusion", "conclusions"],
        "references": ["references", "bibliography"],
    }

    for key, options in required_sections.items():
        if not has_any_heading(text, options):
            issues.append({"type": "missing_section", "severity": "error", "message": f"Missing expected section: {key}"})

    if not has_any_heading(text, ["limitations", "limitations and future work"]):
        issues.append({"type": "missing_limitations", "severity": "warning", "message": "No limitations section found."})

    abstract = section_text(text, ["abstract", "summary"])
    if abstract and word_count(abstract) > 320:
        issues.append({"type": "abstract_too_long", "severity": "warning", "message": "Abstract or summary is longer than 320 words."})

    if not re.search(r"research question|problem statement|objective|this study asks|we ask|the question addressed", text, re.IGNORECASE):
        issues.append({"type": "question_not_explicit", "severity": "warning", "message": "Research question or objective is not clearly signaled."})

    if text.count('"') >= 6:
        issues.append({"type": "many_quotes", "severity": "warning", "message": "Frequent direct quotation detected. Prefer paraphrase and citation."})

    if IMAGE_RE.search(text) and not re.search(r"Figure\s+\d+", text):
        issues.append({"type": "figure_captioning", "severity": "warning", "message": "Images are present but explicit Figure labels were not found."})

    references = section_text(text, ["references", "bibliography"])
    if references and not re.search(r"https?://|doi\.org", references, re.IGNORECASE):
        issues.append({"type": "weak_reference_links", "severity": "warning", "message": "References section has no visible URLs or DOI links."})

    if docmost:
        forbidden = ["\\begin{cases}", "\\end{cases}", "\\left", "\\right", "\\[", "\\]", "\\(", "\\)", "<br"]
        for token in forbidden:
            if token in text:
                issues.append({"type": "docmost_equation_hazard", "severity": "error", "message": f"DocMost-sensitive token found: {token}"})
        for block in DISPLAY_BLOCK_RE.findall(text):
            if "\n" in block.strip():
                issues.append({"type": "multiline_display_math", "severity": "warning", "message": "Multiline $$...$$ block detected."})
                break

    return {"path": str(path), "issue_count": len(issues), "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a research Markdown draft.")
    parser.add_argument("path", help="Markdown file to audit")
    parser.add_argument("--docmost", action="store_true", help="Enable stricter equation checks for DocMost-like editors")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on error severity issues")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    report = audit(Path(args.path), args.docmost)
    print(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False))

    if args.strict and any(issue["severity"] == "error" for issue in report["issues"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
