#!/usr/bin/env python3
"""Add only project-scoped Job MCP config. Default is a read-only plan.

Requires Python 3.11+. This script cannot grant trust/approval or reload a client.
Review it before execution; --approve records permission to apply this change.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import tomllib
from datetime import datetime, timezone

ENDPOINT = "https://jobmcp.pmlecuong.com/mcp"


def configure(root: Path, approve: bool) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Select an existing workspace directory first.")
    directory = root / ".codex"
    target = directory / "config.toml"
    if not directory.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError("Configuration escapes the selected root or is a symlink; no changes made.")
    original = target.read_text(encoding="utf-8") if target.exists() else ""
    parsed = tomllib.loads(original)
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise ValueError("Existing MCP configuration is not a table; no changes made.")
    existing = servers.get("jobmcp")
    if existing is not None:
        if not isinstance(existing, dict) or existing.get("url") != ENDPOINT:
            raise ValueError("A different jobmcp configuration already exists. Ask the user; do not replace it.")
        if existing.get("enabled") is False:
            raise ValueError("Job MCP is explicitly disabled. Ask the user before changing that setting.")
        return {"status": "already_configured", "connected": False, "next_action": "Reload if needed, discover tools and call health. Configuration is not connection proof."}
    addition = '\n[mcp_servers.jobmcp]\nurl = "' + ENDPOINT + '"\n'
    candidate = original.rstrip() + "\n" + addition
    checked = tomllib.loads(candidate)
    if checked["mcp_servers"]["jobmcp"]["url"] != ENDPOINT:
        raise ValueError("Configuration validation failed; no changes made.")
    if not approve:
        return {"status": "approval_required", "scope": "selected project .codex/config.toml only", "endpoint": ENDPOINT, "changes": "Add Job MCP server; preserve all other settings. No trust or permission changes."}
    directory.mkdir(exist_ok=True)
    backup = None
    if target.exists():
        backup = directory / ("config.toml.jobmcp-backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        with backup.open("x", encoding="utf-8") as handle:
            os.chmod(backup, 0o600)
            handle.write(original)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, prefix=".jobmcp-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        # Refuse to overwrite edits made after the plan was read.
        if (target.read_text(encoding="utf-8") if target.exists() else "") != original:
            raise ValueError("Configuration changed during setup; retry after review. Backup retained.")
        os.replace(temporary, target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return {"status": "configured_awaiting_client_reload", "connected": False, "backup_created": backup is not None, "next_action": "Client must trust/load this project's config. Reload only if needed, then verify tools and health; approval/sandbox policies are unchanged."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Existing folder explicitly selected by the user")
    parser.add_argument("--approve", action="store_true", help="Apply only after the user's/client's required approval")
    args = parser.parse_args()
    try:
        print(json.dumps(configure(Path(args.root), args.approve), indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "blocked", "error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
