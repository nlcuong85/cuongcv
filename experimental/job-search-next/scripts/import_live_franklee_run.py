#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import DATA_ROOT, upsert_raw_leads, write_json, write_text


DEFAULT_TARGET = "root@100.124.166.95"
PROFILE_TO_JOB_ID = {
    "student": "74e37d6d-099b-4ef8-84b1-53a5cbc06b43",
    "fulltime": "daily-germany-fulltime-0900-berlin",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Run date in YYYY-MM-DD format as shown in the Franklee summary")
    parser.add_argument("--profile", choices=["student", "fulltime"], default="student")
    parser.add_argument("--ssh-target", default=DEFAULT_TARGET)
    parser.add_argument("--run-log")
    return parser.parse_args()


def load_remote_summary(args: argparse.Namespace) -> str:
    run_log = args.run_log or f"/root/.openclaw/cron/runs/{PROFILE_TO_JOB_ID[args.profile]}.jsonl"
    remote_python = f"""
import json
from pathlib import Path
path = Path({run_log!r})
target = {args.date!r}
matched = None
for line in path.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    item = json.loads(line)
    summary = item.get('summary') or ''
    if f'Validated Shortlist ({{target}})' in summary:
        matched = summary
if not matched:
    raise SystemExit('No Franklee run found for date: ' + target)
print(matched)
"""
    remote_cmd = "python3 - <<'PY'\n" + remote_python + "\nPY"
    cmd = ["ssh", args.ssh_target, "bash", "-lc", remote_cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "").strip()
        raise SystemExit(f"Failed to read live Franklee run: {stderr}")
    return proc.stdout.strip()


def parse_summary(summary: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"- \*\*(?P<title>.+?)\*\* — \*\*(?P<company>.+?)\*\* — (?P<location>.+?) — "
        r"Work model: (?P<work_model>.+?) — Posted: (?P<posted_date>\d{4}-\d{2}-\d{2}) \((?P<age_days>\d+)d ago\) — "
        r"Language: (?P<language_note>.+?) — Why it matches: (?P<why_match>.+?) — Apply: <(?P<url>https?://[^>]+)>"
    )
    results: list[dict[str, Any]] = []
    current_city = "Other / Unclear"
    for line in summary.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current_city = line[3:].strip()
            continue
        match = pattern.match(line)
        if not match:
            continue
        item = match.groupdict()
        item["age_days"] = int(item["age_days"])
        item["city_bucket"] = current_city
        results.append(item)
    if not results:
        raise SystemExit("Could not parse any job entries from the Franklee summary")
    return results


def infer_language(language_note: str) -> str:
    lower = language_note.lower()
    if "english" in lower and ("german" in lower or "deutsch" in lower):
        return "english + german"
    if "english" in lower:
        return "english"
    if "german" in lower or "deutsch" in lower:
        return "german_or_mixed"
    return "unknown"


def to_raw_lead(item: dict[str, Any], profile: str, date: str) -> dict[str, Any]:
    return {
        "company_name": item["company"],
        "job_title": item["title"],
        "job_url": item["url"],
        "company_location": item["location"],
        "language": infer_language(item["language_note"]),
        "job_description": (
            f"Imported from live Franklee {profile} run on {date}. "
            f"City bucket: {item['city_bucket']}. Work model: {item['work_model']}. "
            f"Posted date: {item['posted_date']}. Language note: {item['language_note']}. "
            f"Why it matches: {item['why_match']}."
        ),
        "requirements": [
            f"Franklee city bucket: {item['city_bucket']}",
            f"Franklee work model: {item['work_model']}",
            f"Franklee language note: {item['language_note']}",
            f"Franklee match note: {item['why_match']}",
        ],
        "source": f"franklee_live_{profile}_{date}",
        "source_profile": profile,
        "source_score": 0,
        "source_posted_date": item["posted_date"],
        "source_work_model": item["work_model"],
        "source_language_note": item["language_note"],
        "source_why_match": item["why_match"],
        "source_domain": re.sub(r"^https?://", "", item["url"]).split("/", 1)[0].lower(),
    }


def main() -> int:
    args = parse_args()
    summary = load_remote_summary(args)
    parsed = parse_summary(summary)

    stem = f"franklee_live_{args.profile}_{args.date}"
    write_text(DATA_ROOT / f"{stem}.md", summary + "\n")
    write_json(DATA_ROOT / f"{stem}.json", parsed)

    stats = upsert_raw_leads([to_raw_lead(item, args.profile, args.date) for item in parsed])
    print(
        json.dumps(
            {
                "date": args.date,
                "profile": args.profile,
                "imported": len(parsed),
                "raw_leads_added": stats["added"],
                "raw_leads_updated": stats["updated"],
                "raw_leads_total": stats["total"],
                "summary_path": str(DATA_ROOT / f"{stem}.md"),
                "json_path": str(DATA_ROOT / f"{stem}.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
