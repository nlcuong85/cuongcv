#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from common import DATA_ROOT, upsert_raw_leads, write_json, write_text


DEFAULT_TARGET = "root@100.124.166.95"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["student", "fulltime"], default="student")
    parser.add_argument("--ssh-target", default=DEFAULT_TARGET)
    parser.add_argument("--max-age-days", type=int, default=20)
    parser.add_argument("--max-results", type=int, default=0)
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--max-validate", type=int, default=36)
    parser.add_argument("--dedupe-days", type=int, default=21)
    parser.add_argument("--source-label", help="Optional stable label for source tagging; defaults to current Berlin date")
    parser.add_argument("--timeout", type=int, default=240)
    return parser.parse_args()


def run_remote_validator(args: argparse.Namespace) -> list[dict[str, Any]]:
    remote_cmd = (
        "python3 /root/clawdFrankLee/dist/job_search_prefilter.py "
        f"--profile {args.profile} "
        f"--max-age-days {args.max_age_days} "
        f"--max-results {args.max_results} "
        f"--per-query {args.per_query} "
        f"--max-validate {args.max_validate} "
        f"--dedupe-days {args.dedupe_days} "
        "--format json"
    )
    proc = subprocess.run(
        ["ssh", args.ssh_target, remote_cmd],
        capture_output=True,
        text=True,
        timeout=args.timeout,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "").strip()
        raise SystemExit(f"Live Franklee validator failed: {stderr}")
    payload = json.loads(proc.stdout)
    if not isinstance(payload, list):
        raise SystemExit("Live Franklee validator did not return a JSON list")
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


def source_label(args: argparse.Namespace) -> str:
    if args.source_label:
        return args.source_label
    return datetime.now().astimezone().date().isoformat()


def to_raw_lead(item: dict[str, Any], profile: str, label: str) -> dict[str, Any]:
    return {
        "company_name": item.get("company", ""),
        "job_title": item.get("title", ""),
        "job_url": item.get("url") or item.get("normalized_url", ""),
        "company_location": item.get("location", ""),
        "language": infer_language(str(item.get("language_note", ""))),
        "job_description": (
            f"Imported from live Franklee validator for profile {profile} with source label {label}. "
            f"Work model: {item.get('work_model', '')}. "
            f"Posted date: {item.get('posted_date', '')}. "
            f"Language note: {item.get('language_note', '')}. "
            f"Why it matches: {item.get('why_match', '')}."
        ),
        "requirements": [
            f"Franklee work model: {item.get('work_model', '')}",
            f"Franklee language note: {item.get('language_note', '')}",
            f"Franklee match note: {item.get('why_match', '')}",
        ],
        "source": f"franklee_live_direct_{profile}_{label}",
        "source_profile": profile,
        "source_score": item.get("score", 0) or 0,
        "source_posted_date": item.get("posted_date", ""),
        "source_work_model": item.get("work_model", ""),
        "source_language_note": item.get("language_note", ""),
        "source_why_match": item.get("why_match", ""),
        "source_domain": item.get("domain", ""),
    }


def main() -> int:
    args = parse_args()
    label = source_label(args)
    results = run_remote_validator(args)
    stem = f"franklee_live_direct_{args.profile}_{label}"
    write_json(DATA_ROOT / f"{stem}.json", results)
    write_text(
        DATA_ROOT / f"{stem}.md",
        "\n".join(
            [
                f"# Live Franklee Direct Validator Import",
                "",
                f"- Profile: {args.profile}",
                f"- Source label: {label}",
                f"- Imported jobs: {len(results)}",
                f"- SSH target: {args.ssh_target}",
                f"- Parameters: max_age_days={args.max_age_days}, max_results={args.max_results}, per_query={args.per_query}, max_validate={args.max_validate}, dedupe_days={args.dedupe_days}",
                "",
            ]
            + [
                f"- {item.get('company', '')} | {item.get('title', '')} | {item.get('location', '')} | {item.get('url', '')}"
                for item in results
            ]
            + [""]
        ),
    )
    stats = upsert_raw_leads([to_raw_lead(item, args.profile, label) for item in results])
    print(
        json.dumps(
            {
                "profile": args.profile,
                "source_label": label,
                "imported": len(results),
                "raw_leads_added": stats["added"],
                "raw_leads_updated": stats["updated"],
                "raw_leads_total": stats["total"],
                "json_path": str((DATA_ROOT / f"{stem}.json").resolve()),
                "markdown_path": str((DATA_ROOT / f"{stem}.md").resolve()),
                "source_prefix": f"franklee_live_direct_{args.profile}_{label}",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
