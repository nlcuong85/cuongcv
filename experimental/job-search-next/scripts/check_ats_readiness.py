#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import DATA_ROOT, write_json, write_text


UNICODE_RISK_PATTERN = re.compile(r"[\u2013\u2014\u2018\u2019\u201c\u201d\u00a0\u200b\u200c\u200d\ufeff]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", action="append", default=[], help="Specific PDF path to test")
    parser.add_argument("--scan-generated-resumes", action="store_true")
    parser.add_argument("--latest-only", action="store_true", help="When scanning generated resumes, keep only the newest PDF per output folder")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--min-chars", type=int, default=1200)
    parser.add_argument("--report-name", default="ats-readiness-report")
    return parser.parse_args()


def ensure_tools() -> None:
    for cmd in ("pdfinfo", "pdftotext"):
        if not shutil.which(cmd):
            raise SystemExit(f"Missing required tool: {cmd}")


def latest_resume_pdfs() -> list[Path]:
    candidates = sorted(Path("application-system/outputs").glob("*/cv/*.pdf"))
    if not candidates:
        return []
    if not args.latest_only:
        return candidates
    grouped: dict[Path, Path] = {}
    for path in candidates:
        parent = path.parent
        current = grouped.get(parent)
        if current is None or path.name > current.name:
            grouped[parent] = path
    return sorted(grouped.values())


def read_pdf_info(path: Path) -> dict[str, int]:
    proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or "pdfinfo failed")
    pages = 0
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split(":", 1)[1].strip())
            break
    return {"pages": pages}


def extract_text(path: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
        tmp_path = Path(handle.name)
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(path), str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip() or "pdftotext failed")
        return tmp_path.read_text(encoding="utf-8", errors="replace")
    finally:
        tmp_path.unlink(missing_ok=True)


def analyze_pdf(path: Path, max_pages: int, min_chars: int) -> dict[str, object]:
    info = read_pdf_info(path)
    text = extract_text(path)
    normalized = re.sub(r"\s+", " ", text).strip()
    risk_count = len(UNICODE_RISK_PATTERN.findall(text))
    word_count = len(re.findall(r"\b\w+\b", normalized))
    char_count = len(normalized)

    checks = {
        "text_extractable": char_count >= min_chars,
        "page_limit_ok": 1 <= info["pages"] <= max_pages,
        "unicode_risk_ok": risk_count == 0,
        "has_contact_markers": any(token in normalized.lower() for token in ("le cuong nguyen", "@", "heilbronn", "linkedin")),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if checks["text_extractable"] and checks["page_limit_ok"] and checks["unicode_risk_ok"]:
        verdict = "pass"
    elif checks["text_extractable"]:
        verdict = "warn"
    else:
        verdict = "fail"

    return {
        "pdf_path": str(path.resolve()),
        "pages": info["pages"],
        "char_count": char_count,
        "word_count": word_count,
        "unicode_risk_count": risk_count,
        "checks": checks,
        "failed_checks": failed,
        "verdict": verdict,
    }


def build_markdown(results: list[dict[str, object]], max_pages: int, min_chars: int) -> str:
    pass_count = sum(1 for item in results if item["verdict"] == "pass")
    warn_count = sum(1 for item in results if item["verdict"] == "warn")
    fail_count = sum(1 for item in results if item["verdict"] == "fail")
    lines = [
        "# ATS Readiness Report",
        "",
        "This is a heuristic ATS parseability check, not a guarantee for every ATS product.",
        "",
        f"- PDFs tested: {len(results)}",
        f"- Max pages rule: {max_pages}",
        f"- Minimum extracted characters: {min_chars}",
        f"- Verdicts: pass={pass_count}, warn={warn_count}, fail={fail_count}",
        "",
    ]
    for item in results:
        path = item["pdf_path"]
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else "none"
        lines.append(
            f"- [{item['verdict']}] {Path(path).name} | pages={item['pages']} | chars={item['char_count']} | unicode_risk={item['unicode_risk_count']} | failed={failed}"
        )
    lines.append("")
    return "\n".join(lines)


def gather_pdfs(args: argparse.Namespace) -> list[Path]:
    paths = [Path(entry) for entry in args.pdf]
    if args.scan_generated_resumes:
        candidates = sorted(Path("application-system/outputs").glob("*/cv/*.pdf"))
        if args.latest_only:
            grouped: dict[Path, Path] = {}
            for path in candidates:
                parent = path.parent
                current = grouped.get(parent)
                if current is None or path.name > current.name:
                    grouped[parent] = path
            paths.extend(sorted(grouped.values()))
        else:
            paths.extend(candidates)
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def main() -> int:
    ensure_tools()
    pdfs = gather_pdfs(args)
    if not pdfs:
        raise SystemExit("No PDFs selected. Use --pdf or --scan-generated-resumes.")

    results = [analyze_pdf(path, args.max_pages, args.min_chars) for path in pdfs]
    report_stem = args.report_name
    write_json(DATA_ROOT / f"{report_stem}.json", {"results": results})
    write_text(DATA_ROOT / f"{report_stem}.md", build_markdown(results, args.max_pages, args.min_chars))

    summary = {
        "tested": len(results),
        "pass": sum(1 for item in results if item["verdict"] == "pass"),
        "warn": sum(1 for item in results if item["verdict"] == "warn"),
        "fail": sum(1 for item in results if item["verdict"] == "fail"),
        "json_report": str((DATA_ROOT / f"{report_stem}.json").resolve()),
        "markdown_report": str((DATA_ROOT / f"{report_stem}.md").resolve()),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(main())
