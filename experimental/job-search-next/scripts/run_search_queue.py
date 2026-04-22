#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import PROTOTYPE_ROOT, upsert_raw_leads
from import_franklee_queue import load_franklee_results, franklee_item_to_raw
from import_live_franklee_validator import run_remote_validator, to_raw_lead as live_to_raw_lead


SCRIPT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["student", "fulltime"], default="student")
    parser.add_argument("--skip-franklee", action="store_true")
    parser.add_argument("--franklee-source-json")
    parser.add_argument("--live-franklee-direct", action="store_true")
    parser.add_argument("--ssh-target", default="root@100.124.166.95")
    parser.add_argument("--source-label")
    parser.add_argument("--max-age-days", type=int, default=20)
    parser.add_argument("--max-results", type=int, default=0)
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--max-validate", type=int, default=36)
    parser.add_argument("--dedupe-days", type=int, default=21)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--manual-json", action="append", default=[])
    parser.add_argument("--company")
    parser.add_argument("--title")
    parser.add_argument("--url")
    parser.add_argument("--location")
    parser.add_argument("--language", default="english")
    parser.add_argument("--description")
    parser.add_argument("--description-file")
    parser.add_argument("--lead-id")
    parser.add_argument("--scan-mode", choices=["raw", "all"], default="raw")
    return parser.parse_args()


def add_inline_manual_lead(args: argparse.Namespace) -> int:
    if not (args.company or args.title or args.url or args.description or args.description_file):
        return 0
    if not args.company or not args.title:
        raise SystemExit("Inline manual lead requires at least --company and --title")
    description = args.description or ""
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")
    upsert_raw_leads(
        [
            {
                "lead_id": args.lead_id,
                "company_name": args.company,
                "job_title": args.title,
                "job_url": args.url or "",
                "company_location": args.location or "",
                "language": args.language,
                "job_description": description,
                "requirements": [],
                "source": "manual_inline",
            }
        ]
    )
    return 1


def add_manual_json_leads(paths: list[str]) -> int:
    count = 0
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        upsert_raw_leads([payload])
        count += 1
    return count


def run_subprocess(*parts: str) -> None:
    cmd = [sys.executable, *parts]
    proc = subprocess.run(cmd, check=False, cwd=PROTOTYPE_ROOT.parent.parent)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    args = parse_args()
    imported = 0
    if not args.skip_franklee:
        if args.live_franklee_direct:
            import_args = argparse.Namespace(
                profile=args.profile,
                ssh_target=args.ssh_target,
                max_age_days=args.max_age_days,
                max_results=args.max_results,
                per_query=args.per_query,
                max_validate=args.max_validate,
                dedupe_days=args.dedupe_days,
                source_label=args.source_label,
                timeout=args.timeout,
            )
            results = run_remote_validator(import_args)
            label = args.source_label or "latest"
            mapped = [live_to_raw_lead(item, args.profile, label) for item in results]
        else:
            import_args = argparse.Namespace(
                profile=args.profile,
                source_json=args.franklee_source_json,
                max_age_days=args.max_age_days,
                max_results=args.max_results,
                per_query=args.per_query,
                max_validate=args.max_validate,
                dedupe_days=args.dedupe_days,
                timeout=args.timeout,
            )
            results = load_franklee_results(import_args)
            mapped = [franklee_item_to_raw(item, args.profile) for item in results]
        upsert_raw_leads(mapped)
        imported = len(results)

    manual_from_json = add_manual_json_leads(args.manual_json)
    manual_inline = add_inline_manual_lead(args)

    scan_flag = "--from-raw-leads" if args.scan_mode == "raw" else "--all"
    run_subprocess(str(SCRIPT_ROOT / "scan_jobs.py"), scan_flag)
    run_subprocess(str(SCRIPT_ROOT / "verify_tracker.py"))

    print(
        json.dumps(
            {
                "franklee_imported": imported,
                "manual_json_added": manual_from_json,
                "manual_inline_added": manual_inline,
                "scan_mode": args.scan_mode,
                "pipeline": str(PROTOTYPE_ROOT / "data" / "pipeline.md"),
                "tracker": str(PROTOTYPE_ROOT / "data" / "tracker.tsv"),
                "verification": str(PROTOTYPE_ROOT / "data" / "verification_report.md"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
