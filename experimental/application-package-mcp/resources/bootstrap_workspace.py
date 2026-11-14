#!/usr/bin/env python3
"""Install the public Job MCP workspace kit into one user-approved local folder.

This script never sends local candidate files to the server. It downloads a
versioned public archive, validates its digest and members, and preserves
student-owned content. The MCP manifest audit remains a separate final step.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
AGENT_FILES = {"AGENTS.md", "CLAUDE.md", "COPILOT.md", "GEMINI.md"}
PROTECTED_PREFIXES = ("profile/", "memory/", "voice/", "candidate/", "jobs/", "applications/", "outputs/")
POLICY_START = "<!-- JOB-MCP-MANDATORY-POLICY:START -->"
POLICY_END = "<!-- JOB-MCP-MANDATORY-POLICY:END -->"
ALLOWED_SUFFIXES = {".md", ".json", ".py", ".mjs", ".html", ".tex", ".ttf", ".png", ".svg", ".pdf"}


def die(message: str) -> None:
    raise SystemExit(message)


def fetch(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        die("Bootstrap download requires HTTPS or loopback HTTP for local tests")
    request = Request(url, headers={"User-Agent": "JobMCP-WorkspaceBootstrap/0.2.27", "Accept": "application/gzip"})
    with urlopen(request, timeout=30) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_ARCHIVE_BYTES:
            die("Public kit archive exceeds size limit")
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        die("Public kit archive exceeds size limit")
    return data


def safe_target(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or not relative or any(part in {"", ".", ".."} for part in posix.parts):
        die(f"Unsafe archive path: {relative!r}")
    target = root.joinpath(*posix.parts)
    if any(parent.is_symlink() for parent in (target, *target.parents) if parent == root or root in parent.parents):
        die(f"Symlink in workspace path: {relative!r}")
    if not target.resolve().is_relative_to(root):
        die(f"Archive path escapes workspace: {relative!r}")
    return target


def merged_agent_text(existing: bytes, incoming: bytes) -> bytes:
    current = existing.decode("utf-8")
    template = incoming.decode("utf-8")
    start = template.find(POLICY_START)
    end = template.find(POLICY_END, start)
    if start < 0 or end < 0:
        die("Canonical agent policy markers are missing from the kit")
    block = template[start:end + len(POLICY_END)]
    old_start = current.find(POLICY_START)
    old_end = current.find(POLICY_END, old_start)
    if old_start >= 0 and old_end >= 0:
        current = current[:old_start] + block + current[old_end + len(POLICY_END):]
    else:
        current = current.rstrip() + "\n\n" + block + "\n"
    return current.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Existing dedicated folder approved by the user")
    parser.add_argument("--base-url", default="https://jobmcp.pmlecuong.com/")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--approve-workspace", action="store_true", help="Confirm the user approved writes to this exact folder")
    args = parser.parse_args()
    if not args.approve_workspace:
        die("Ask the user to approve the exact workspace folder before installing; then use --approve-workspace")
    requested_root = Path(args.root)
    if not requested_root.is_absolute() or requested_root.is_symlink():
        die("Workspace must be a real absolute directory")
    root = requested_root.resolve()
    if not root.is_dir() or root in {Path.home().resolve(), (Path.home() / "Documents").resolve(), Path("/")}:
        die("Choose an existing dedicated workspace folder, not a home/Documents root")
    expected = args.expected_sha256.lower()
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        die("Expected archive SHA-256 must be 64 hexadecimal characters")
    archive = fetch(args.base_url.rstrip("/") + "/complete-workspace-kit.tar.gz")
    if hashlib.sha256(archive).hexdigest() != expected:
        die("Public kit archive SHA-256 does not match the MCP bootstrap plan")

    installed, updated, preserved = [], [], []
    backup_root = root / ".mcp" / "managed-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        staged = []
        seen = set()
        for member in bundle:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] not in {"workspace-template", "application-kit"}:
                die(f"Unexpected archive member: {member.name!r}")
            if not member.isdir() and not member.isfile():
                die(f"Unsafe archive member type: {member.name!r}")
            if member.isdir():
                continue
            if parts[0] == "workspace-template":
                relative = PurePosixPath(*parts[1:]).as_posix()
            else:
                relative = PurePosixPath(*parts).as_posix()
            if Path(relative).suffix.lower() not in ALLOWED_SUFFIXES and Path(relative).name != ".gitkeep":
                continue
            if relative in seen:
                die(f"Duplicate archive member: {relative}")
            seen.add(relative)
            target = safe_target(root, relative)
            source = bundle.extractfile(member)
            if source is None or member.size > 4 * 1024 * 1024:
                die(f"Invalid or oversized kit member: {relative}")
            incoming = source.read(4 * 1024 * 1024 + 1)
            if len(incoming) != member.size:
                die(f"Truncated kit member: {relative}")
            staged.append((relative, target, incoming))
        # Validate the entire archive before writing any file to the workspace.
        for relative, target, incoming in staged:
            if target.exists():
                if not target.is_file():
                    die(f"Kit target is not a regular file: {relative}")
                if relative in AGENT_FILES:
                    incoming = merged_agent_text(target.read_bytes(), incoming)
                elif relative.startswith(PROTECTED_PREFIXES) or not (
                    relative.startswith("application-kit/") or relative.startswith("scripts/") or relative == ".mcp/update-policy.json"
                ):
                    preserved.append(relative)
                    continue
                if target.read_bytes() == incoming:
                    continue
                backup = safe_target(backup_root, relative)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                updated.append(relative)
            else:
                installed.append(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                handle.write(incoming)
                temporary = Path(handle.name)
            os.replace(temporary, target)
    audit = subprocess.run([sys.executable, str(root / "application-kit/scripts/workspace_audit.py"), "--root", str(root)], capture_output=True, text=True)
    if audit.returncode:
        die("Local workspace inventory failed: " + audit.stderr[-1000:])
    print(json.dumps({"status": "installed_needs_mcp_audit", "workspace": str(root),
                      "installed": len(installed), "updated": len(updated), "preserved": len(preserved),
                      "manifest": ".mcp/workspace-manifest.json", "next": "Call audit_workspace_manifest with this manifest; require workspace_current before application work."}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
