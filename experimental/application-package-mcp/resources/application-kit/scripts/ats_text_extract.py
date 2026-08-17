#!/usr/bin/env python3
"""Prepare a local ATS MCP input packet from a JD file and CV/resume file.

Extraction happens on the user's machine. The MCP receives text only, not the
full workspace or raw PDF file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise SystemExit("pdftotext is required for PDF ATS extraction. Install poppler first.")
    result = subprocess.run([pdftotext, "-layout", str(path), "-"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"pdftotext failed for {path}")
    return result.stdout


def extract_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError as error:
        raise SystemExit("python-docx is required for DOCX ATS extraction. Install python-docx first.") from error
    document = docx.Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_source(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix == ".docx":
        return extract_docx(path)
    if suffix in {".md", ".txt", ".html", ".htm", ".tex", ".json"}:
        return read_text_file(path)
    raise SystemExit(f"Unsupported ATS extraction input type: {path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an ATS checker input JSON from local files.")
    parser.add_argument("--resume", required=True, help="Path to current CV/resume file.")
    parser.add_argument("--jd", required=True, help="Path to current job description text/markdown/json file.")
    parser.add_argument("--out", required=True, help="Output JSON packet for mcp_check_client.mjs ats.")
    parser.add_argument("--company-name", default="")
    parser.add_argument("--job-title", default="")
    parser.add_argument("--market", default="germany")
    parser.add_argument("--language", default="mixed")
    parser.add_argument("--target-score", type=int, default=70)
    args = parser.parse_args()

    resume_path = Path(args.resume).resolve()
    jd_path = Path(args.jd).resolve()
    if not resume_path.exists():
        raise SystemExit(f"Resume file not found: {resume_path}")
    if not jd_path.exists():
        raise SystemExit(f"Job description file not found: {jd_path}")

    packet = {
        "document_kind": "cv",
        "market": args.market,
        "language": args.language,
        "company_name": args.company_name,
        "job_title": args.job_title,
        "job_description": extract_source(jd_path),
        "resume_text": extract_source(resume_path),
        "target_score": args.target_score,
    }

    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
