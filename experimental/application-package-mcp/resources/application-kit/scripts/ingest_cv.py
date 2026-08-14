#!/usr/bin/env python3
"""Local Phase-1 CV ingestion for PDF-with-text, DOCX, and HTML.

The source is copied unchanged into candidate/source. Text extraction is local;
legacy .doc and scan-only PDFs fail with an explicit Phase-2 message.
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import zipfile
from pathlib import Path


def html_to_text(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", value, flags=re.I)
    value = re.sub(r"<(br|/p|/h[1-6]|/li|/div)[^>]*>", "\n", value, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def read_docx(source: Path) -> str:
    with zipfile.ZipFile(source) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = xml.replace("</w:p>", "\n").replace("</w:tr>", "\n")
    return html.unescape(re.sub(r"<[^>]+>", "", xml)).strip()


def read_pdf(source: Path) -> str:
    try:
        result = subprocess.run(["pdftotext", str(source), "-"], text=True, capture_output=True, timeout=30, check=True)
    except (FileNotFoundError, subprocess.SubprocessError) as error:
        raise SystemExit("PDF text extraction requires Poppler pdftotext. Install it locally or provide DOCX/HTML.") from error
    text = result.stdout.strip()
    if len(re.sub(r"\s+", "", text)) < 80:
        raise SystemExit("This PDF appears scan-only or has insufficient selectable text. OCR scan support is Phase 2; provide DOCX/HTML or a text PDF.")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(); source = Path(args.source).resolve(); root = Path(args.root).resolve()
    if not source.is_file(): raise SystemExit("CV source file does not exist.")
    suffix = source.suffix.lower()
    if suffix == ".doc": raise SystemExit("Legacy .doc conversion is Phase 2. Please provide PDF-with-text, DOCX, or HTML.")
    target_dir = root / "candidate" / "source"; target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"cv-original{suffix}"; shutil.copy2(source, target)
    if suffix == ".pdf": text = read_pdf(source)
    elif suffix == ".docx": text = read_docx(source)
    elif suffix in {".html", ".htm"}: text = html_to_text(source.read_text(encoding="utf-8", errors="ignore"))
    else: raise SystemExit("Supported Phase-1 formats: PDF, DOCX, HTML.")
    extracted = root / "candidate" / "extracted"; extracted.mkdir(parents=True, exist_ok=True)
    (extracted / "cv-source.md").write_text(f"# Extracted CV Source\n\n{text}\n", encoding="utf-8")
    headings = [line.strip() for line in text.splitlines() if 2 < len(line.strip()) < 70 and line.strip().upper() == line.strip()][:30]
    (extracted / "cv-structure.json").write_text(__import__("json").dumps({"source": target.relative_to(root).as_posix(), "headings": headings, "format": suffix}, indent=2) + "\n", encoding="utf-8")
    print(extracted / "cv-source.md")
    return 0


if __name__ == "__main__": raise SystemExit(main())
