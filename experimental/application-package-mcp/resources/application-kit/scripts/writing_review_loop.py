#!/usr/bin/env python3
"""Prepare privacy-bounded MCP review packets for general writing.

This script does not call the MCP itself and contains no checker rules. It
extracts local text, chunks it safely, and writes JSON packets that the local AI
agent can send with `mcp_check_client.mjs`. Loops are user-selected from 1 to 3.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

VALID_MODES = {"application", "academic", "blog", "work", "social", "general"}
MAX_LOOPS = 3
DEFAULT_CHUNK_WORDS = 1200


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_rel(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path.as_posix()


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        parts = [node.text or "" for node in para.findall(".//w:t", ns)]
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)
    return "\n\n".join(paragraphs)


def read_pdf(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise SystemExit("PDF extraction requires `pdftotext`. Convert the PDF locally or install poppler first.")
    result = subprocess.run([pdftotext, str(path), "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "pdftotext failed")
    return result.stdout


def read_input(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix in {".html", ".htm"}:
        raw = path.read_text(encoding="utf-8")
        raw = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", raw)
        raw = re.sub(r"(?s)<[^>]+>", " ", raw)
        return html.unescape(raw)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise SystemExit(f"Unsupported input type: {suffix}. Use .md, .txt, .html, .docx, or text-extractable .pdf.")


def split_units(text: str) -> list[str]:
    units: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#") and current:
            units.append("\n".join(current).strip())
            current = [line]
        elif not line.strip() and current:
            current.append(line)
            units.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    if current:
        units.append("\n".join(current).strip())
    return [unit for unit in units if unit]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def chunk_text(text: str, max_words: int) -> list[str]:
    units = split_units(text)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for unit in units:
        count = word_count(unit)
        if current and current_words + count > max_words:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_words = 0
        if count > max_words:
            sentences = re.split(r"(?<=[.!?])\s+", unit)
            buffer: list[str] = []
            buffer_words = 0
            for sentence in sentences:
                sentence_words = word_count(sentence)
                if buffer and buffer_words + sentence_words > max_words:
                    chunks.append(" ".join(buffer).strip())
                    buffer = []
                    buffer_words = 0
                buffer.append(sentence)
                buffer_words += sentence_words
            if buffer:
                chunks.append(" ".join(buffer).strip())
            continue
        current.append(unit)
        current_words += count
    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks or [text.strip()]


def cmd_prepare(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    source = root / safe_rel(args.input)
    if not source.exists():
        raise SystemExit(f"Input not found: {args.input}")
    mode = args.mode.lower()
    if mode not in VALID_MODES:
        raise SystemExit(f"Unsupported mode: {args.mode}")
    loops = max(1, min(MAX_LOOPS, args.loops))
    text = normalize(read_input(source))
    if not text:
        raise SystemExit("Input contains no extractable text.")
    chunks = chunk_text(text, args.max_words)
    output_dir = root / safe_rel(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "source-extracted.txt").write_text(text + "\n", encoding="utf-8")
    chunk_records = []
    for loop in range(1, loops + 1):
        loop_dir = output_dir / f"loop-{loop}"
        loop_dir.mkdir(exist_ok=True)
        for index, chunk in enumerate(chunks, 1):
            payload = {
                "mode": mode,
                "audience": args.audience,
                "purpose": f"General writing MCP review loop {loop}/{loops}: {args.purpose}",
                "text": chunk,
            }
            filename = f"chunk-{index:03d}-input.json"
            (loop_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            chunk_records.append({
                "loop": loop,
                "chunk": index,
                "input": (loop_dir / filename).relative_to(root).as_posix(),
                "expected_result": (loop_dir / f"chunk-{index:03d}-result.json").relative_to(root).as_posix(),
                "words": word_count(chunk),
            })
    manifest = {
        "schema_version": 1,
        "created_at": now(),
        "source": args.input,
        "mode": mode,
        "loops_requested": loops,
        "chunk_count": len(chunks),
        "max_words": args.max_words,
        "outputs": {
            "extracted_text": (output_dir / "source-extracted.txt").relative_to(root).as_posix(),
            "review_manifest": (output_dir / "writing-review-manifest.json").relative_to(root).as_posix(),
            "combined_report": (output_dir / "writing-review-report.md").relative_to(root).as_posix(),
        },
        "chunks": chunk_records,
        "privacy": {
            "full_workspace_uploaded": False,
            "submitted_to_mcp": "selected text chunks only",
            "raw_text_logged_by_mcp": False,
        },
        "commands": [
            f"node application-kit/scripts/mcp_check_client.mjs review {record['input']} {record['expected_result']}"
            for record in chunk_records
        ],
    }
    (output_dir / "writing-review-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest_path = root / safe_rel(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines = [
        "# Writing Review Report",
        "",
        f"- Source: `{manifest['source']}`",
        f"- Mode: `{manifest['mode']}`",
        f"- Loops requested: {manifest['loops_requested']}",
        f"- Chunks: {manifest['chunk_count']}",
        "",
    ]
    all_low = True
    for record in manifest["chunks"]:
        result_path = root / record["expected_result"]
        if not result_path.exists():
            all_low = False
            lines.append(f"## Loop {record['loop']} / Chunk {record['chunk']:03d}")
            lines.append("")
            lines.append("- Status: missing MCP result")
            lines.append("")
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        risk = result.get("riskLevel", "unknown")
        all_low = all_low and risk == "low"
        lines.append(f"## Loop {record['loop']} / Chunk {record['chunk']:03d}")
        lines.append("")
        lines.append(f"- Risk: `{risk}`")
        lines.append(f"- Summary: {result.get('summary', '')}")
        issues = result.get("issues", [])
        if issues:
            lines.append("- Issues:")
            for issue in issues[:8]:
                lines.append(f"  - `{issue.get('code')}`: {issue.get('suggestion')}")
        else:
            lines.append("- Issues: none")
        lines.append("")
    lines.insert(5, f"- Overall: {'ready_for_human_review' if all_low else 'revise'}")
    report_path = root / manifest["outputs"]["combined_report"]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.relative_to(root).as_posix())
    return 0 if all_low else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Prepare and summarize general writing MCP review loops.")
    value.add_argument("--root", default=".")
    commands = value.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--mode", choices=sorted(VALID_MODES), default="general")
    prepare.add_argument("--loops", type=int, default=1)
    prepare.add_argument("--max-words", type=int, default=DEFAULT_CHUNK_WORDS)
    prepare.add_argument("--audience", default="human reader")
    prepare.add_argument("--purpose", default="AI-like writing and reader-fit review")
    prepare.add_argument("--output-dir", default="writing-reviews/current")
    prepare.set_defaults(func=cmd_prepare)
    report = commands.add_parser("report")
    report.add_argument("--manifest", required=True)
    report.set_defaults(func=cmd_report)
    return value


if __name__ == "__main__":
    parsed = parser().parse_args()
    raise SystemExit(parsed.func(parsed))
