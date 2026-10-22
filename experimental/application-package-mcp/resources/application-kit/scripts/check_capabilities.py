#!/usr/bin/env python3
"""Read-only, task-scoped local prerequisite check. Never installs or uploads."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path

OPERATIONS = {
    "bootstrap": (),
    "native-mcp": (),
    "mcp-wrapper": ("node",),
    "pdf-text": ("pdftotext",),
    "pdf-reference": ("pdftoppm",),
    "docx-ats": ("python-docx",),
    "latex-pdf": ("latexmk", "pdflatex"),
}


def check(operation: str) -> dict:
    missing = []
    if operation != "native-mcp" and sys.version_info < (3, 11):
        missing.append("Python 3.11+")
    for tool in OPERATIONS[operation]:
        available = importlib.util.find_spec("docx") is not None if tool == "python-docx" else shutil.which(tool) is not None
        if not available:
            missing.append(tool)
    return {
        "operation": operation,
        "status": "blocked" if missing else "available",
        "missing": missing,
        "os": platform.system(),
        "next_action": "Ask the agent for OS-specific installation help and approve changes first; preserve sources/drafts and retry only this stage." if missing else "Continue this operation under the existing SOP checks.",
        "help_url": "https://jobmcp.pmlecuong.com/start#dependencies",
        "boundary": "No installs, file changes or uploads. Available means prerequisites found, not extraction, visual validation or release passed. Native MCP transport is owned by your AI client and may work without local Python or Node.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=OPERATIONS, required=True)
    parser.add_argument("--root", help="Already selected workspace. Check only managed destinations; never create files.")
    args = parser.parse_args()
    result = check(args.operation)
    if args.root:
        root = Path(args.root).resolve()
        problems = []
        if not root.is_dir() or not os.access(root, os.W_OK):
            problems.append("Selected workspace is missing or read-only; open a writable dedicated folder.")
        for name in ("candidate", "profile", "memory", "scripts", "application-kit", ".application-sop", ".mcp", "jobs", "outputs", "applications", "voice"):
            if not (root / name).resolve().is_relative_to(root):
                problems.append("A managed destination points outside the selected workspace; choose an in-scope folder.")
        if problems:
            result["workspace_errors"] = problems
            result["status"] = "blocked"
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
