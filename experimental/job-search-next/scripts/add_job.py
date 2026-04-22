#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import raw_lead_record, upsert_raw_leads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Path to a JSON file describing a lead")
    parser.add_argument("--company")
    parser.add_argument("--title")
    parser.add_argument("--url")
    parser.add_argument("--location")
    parser.add_argument("--language", default="english")
    parser.add_argument("--description")
    parser.add_argument("--description-file")
    parser.add_argument("--lead-id")
    parser.add_argument("--source", default="manual")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.json:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    else:
        if not args.company or not args.title:
            print("Either --json or both --company and --title are required.", file=sys.stderr)
            return 1
        description = args.description or ""
        if args.description_file:
            description = Path(args.description_file).read_text(encoding="utf-8")
        payload = {
            "lead_id": args.lead_id,
            "company_name": args.company,
            "job_title": args.title,
            "job_url": args.url or "",
            "company_location": args.location or "",
            "language": args.language,
            "job_description": description,
            "requirements": [],
            "source": args.source,
        }

    upsert_raw_leads([payload])
    record = raw_lead_record(payload)
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
