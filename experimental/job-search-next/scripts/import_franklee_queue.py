#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import DATA_ROOT, FRANKLEE_LOCAL_RUNNER, upsert_raw_leads, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["student", "fulltime"], default="student")
    parser.add_argument("--source-json", help="Use an existing Franklee JSON payload instead of running the local replica")
    parser.add_argument("--max-age-days", type=int, default=20)
    parser.add_argument("--max-results", type=int, default=0)
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--max-validate", type=int, default=36)
    parser.add_argument("--dedupe-days", type=int, default=21)
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


def load_franklee_results(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.source_json:
        payload = json.loads(Path(args.source_json).read_text(encoding="utf-8"))
    else:
        if not FRANKLEE_LOCAL_RUNNER.exists():
            raise SystemExit(f"Franklee local runner not found: {FRANKLEE_LOCAL_RUNNER}")
        cmd = [
            sys.executable,
            str(FRANKLEE_LOCAL_RUNNER),
            "--profile",
            args.profile,
            "--max-age-days",
            str(args.max_age_days),
            "--max-results",
            str(args.max_results),
            "--per-query",
            str(args.per_query),
            "--max-validate",
            str(args.max_validate),
            "--dedupe-days",
            str(args.dedupe_days),
            "--format",
            "json",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=args.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SystemExit(
                f"Franklee local runner timed out after {args.timeout}s. "
                "Use --source-json with a saved payload if you want an offline import."
            ) from exc
        if proc.returncode != 0:
            stderr = (proc.stderr or proc.stdout or "").strip()
            raise SystemExit(f"Franklee local runner failed: {stderr}")
        payload = json.loads(proc.stdout)

    if isinstance(payload, dict):
        payload = payload.get("results", [])
    if not isinstance(payload, list):
        raise SystemExit("Franklee payload did not resolve to a result list")
    return [item for item in payload if isinstance(item, dict)]


def infer_language(language_note: str) -> str:
    lower = language_note.lower()
    if "english" in lower and ("german" in lower or "deutsch" in lower):
        return "english + german"
    if "english" in lower:
        return "english"
    if "german" in lower or "deutsch" in lower:
        return "german_or_mixed"
    return "unknown"


def build_description(item: dict[str, Any]) -> str:
    parts = [
        "Imported from the Franklee validator shortlist.",
        f"Company: {item.get('company', '')}.",
        f"Location: {item.get('location', '')}.",
        f"Work model: {item.get('work_model', '')}.",
        f"Posted date: {item.get('posted_date', '')}.",
        f"Language note: {item.get('language_note', '')}.",
        f"Why it matches: {item.get('why_match', '')}.",
    ]
    return " ".join(part for part in parts if part.strip())


def franklee_item_to_raw(item: dict[str, Any], profile: str) -> dict[str, Any]:
    requirements = [
        f"Franklee work model: {item.get('work_model', '')}",
        f"Franklee language note: {item.get('language_note', '')}",
        f"Franklee match note: {item.get('why_match', '')}",
    ]
    return {
        "company_name": item.get("company", ""),
        "job_title": item.get("title", ""),
        "job_url": item.get("url") or item.get("normalized_url", ""),
        "company_location": item.get("location", ""),
        "language": infer_language(str(item.get("language_note", ""))),
        "job_description": build_description(item),
        "requirements": [entry for entry in requirements if entry.strip()],
        "source": f"franklee_{profile}_cron",
        "source_profile": profile,
        "source_score": item.get("score", 0) or 0,
        "source_posted_date": item.get("posted_date", ""),
        "source_work_model": item.get("work_model", ""),
        "source_language_note": item.get("language_note", ""),
        "source_why_match": item.get("why_match", ""),
        "source_domain": item.get("domain", ""),
    }


def write_summary(results: list[dict[str, Any]], profile: str) -> None:
    summary_lines = [
        f"# Franklee {profile.title()} Queue Snapshot",
        "",
        f"- Imported items: {len(results)}",
        f"- Snapshot JSON: data/franklee_{profile}_queue.json",
        "",
    ]
    if results:
        summary_lines.append("## Sample")
        summary_lines.append("")
        for item in results[:5]:
            summary_lines.append(
                f"- {item.get('company', '')} | {item.get('title', '')} | {item.get('location', '')} | {item.get('url', '')}"
            )
    else:
        summary_lines.append("No items were returned by the source payload.")
    write_text(DATA_ROOT / f"franklee_{profile}_queue.md", "\n".join(summary_lines) + "\n")


def main() -> int:
    args = parse_args()
    results = load_franklee_results(args)
    write_json(DATA_ROOT / f"franklee_{args.profile}_queue.json", results)
    write_summary(results, args.profile)

    mapped = [franklee_item_to_raw(item, args.profile) for item in results]
    stats = upsert_raw_leads(mapped)
    print(
        json.dumps(
            {
                "profile": args.profile,
                "imported": len(results),
                "raw_leads_added": stats["added"],
                "raw_leads_updated": stats["updated"],
                "raw_leads_total": stats["total"],
                "snapshot_json": str(DATA_ROOT / f"franklee_{args.profile}_queue.json"),
                "snapshot_summary": str(DATA_ROOT / f"franklee_{args.profile}_queue.md"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
