#!/usr/bin/env python3
"""Build a privacy-safe workspace manifest and local hygiene report.

Only managed relative paths and hashes are sent remotely. The detailed report
is local because it can describe the user's file organisation and timings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

KIT_VERSION = "2026.08.14-resilient-workspace.1"
MANAGED = ["AGENTS.md", "README.md", "scripts/application_sop.py", "scripts/mcp_check_client.mjs"]
REQUIRED = ["profile", "voice", "candidate/source", "jobs", "applications", ".mcp"]
EXCLUDED = {".git", "node_modules", "__pycache__", ".application-sop", ".DS_Store"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def audit(root: Path) -> tuple[dict, dict]:
    started = time.monotonic(); paths, large, duplicate_names = [], [], {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in EXCLUDED]
        current_rel = Path(current).relative_to(root).as_posix()
        if current_rel != ".":
            paths.append(current_rel)
        for name in files:
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            if relative.startswith(".application-sop/"):
                continue
            stat = path.stat()
            paths.append(relative)
            duplicate_names[name] = duplicate_names.get(name, 0) + 1
            if stat.st_size > 5 * 1024 * 1024:
                large.append({"path": relative, "bytes": stat.st_size})
    hashes = {item: digest(root / item) for item in MANAGED if (root / item).is_file()}
    decisions = {}
    state_path = root / ".application-sop" / "state.json"
    if state_path.exists():
        try:
            decisions = json.loads(state_path.read_text(encoding="utf-8")).get("decisions", {})
        except json.JSONDecodeError:
            pass
    paths.extend([".mcp/workspace-manifest.json", ".mcp/local-workspace-audit.json"])
    manifest = {
        "schema_version": "1.0", "kit_version": KIT_VERSION,
        "paths": sorted(set(paths)), "managed_file_hashes": hashes,
        "candidate_asset_status": {
            "photo_question_answered": decisions.get("photo") in {"provided", "declined", "not_available"},
            "signature_question_answered": decisions.get("signature") in {"provided", "declined", "not_available", "not_answered_after_request"},
        },
    }
    report = {
        "status": "local_audit_complete",
        "observed": {
            "file_count": len(paths), "inventory_seconds": round(time.monotonic() - started, 3),
            "missing_required_roots": [item for item in REQUIRED if not (root / item).exists()],
            "large_files": sorted(large, key=lambda item: item["bytes"], reverse=True)[:20],
            "duplicate_file_names": sorted(name for name, count in duplicate_names.items() if count > 1)[:50],
        },
        "inference": "This audit identifies structural risk only. Use application_sop.py diagnose-workspace timing spans before attributing a slow run to folder size.",
    }
    return manifest, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=".mcp/workspace-manifest.json")
    parser.add_argument("--report", default=".mcp/local-workspace-audit.json")
    args = parser.parse_args()
    root = Path(args.root).resolve(); manifest, report = audit(root)
    for relative, value in ((args.manifest, manifest), (args.report, report)):
        target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
