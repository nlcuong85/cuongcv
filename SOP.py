#!/usr/bin/env python3
"""
CuongCV SOP harness.

Purpose:
    Keep long-running AI-agent work recoverable after context compaction,
    interruption, or a new session. The conversation summary is not the source
    of truth. This file plus governance/.sop/state.json and
    governance/SOP_STATE.md are.

Core rule for every future agent:
    1. Read AGENTS.md.
    2. Run: python3 SOP.py status
    3. Run: python3 SOP.py resume
    4. Continue only from persisted task/checkpoint/Kiro state, not from memory.

The harness is intentionally dependency-free so it works in a bare Python
environment and can be inspected quickly.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
GOVERNANCE_DIR = ROOT / "governance"
SOP_DIR = GOVERNANCE_DIR / ".sop"
RUN_LOG_DIR = SOP_DIR / "run_logs"
STATE_PATH = SOP_DIR / "state.json"
STATE_LOCK_PATH = SOP_DIR / "state.lock"
STATE_MD_PATH = GOVERNANCE_DIR / "SOP_STATE.md"
AGENTS_PATH = ROOT / "AGENTS.md"
SOP_RESEARCH_PATH = GOVERNANCE_DIR / "SOP_RESEARCH.md"
README_PATH = ROOT / "README.md"
APPLICATION_AGENTS_PATH = ROOT / "application-system" / "AGENTS.md"
KIRO_SPECS_DIR = ROOT / "kiro" / "specs"

VALID_TASK_STATUSES = {"pending", "in_progress", "done", "blocked", "cancelled"}
DEFAULT_AUDIT_EXCLUDES = {
    ".DS_Store",
    ".git",
    "__pycache__",
    "node_modules",
    ".next",
    ".pm2",
    "out",
    "logs",
    "tmp",
    "coverage",
    "test-results",
    "playwright-report",
}
DEFAULT_AUDIT_EXCLUDED_PATHS = {
    "governance/.sop/state.json",
    "governance/.sop/state.lock",
    "governance/SOP_STATE.md",
}
DEFAULT_AUDIT_EXCLUDED_PREFIXES = {
    ".git/",
    ".next/",
    ".pm2/",
    "node_modules/",
    "out/",
    "logs/",
    "tmp/",
    "coverage/",
    "test-results/",
    "playwright-report/",
    "application-system/outputs/",
    "public/generated-cv-data/",
    "governance/.sop/run_logs/",
}

_ACTIVE_LOCK: Any = None


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_state() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "repo": str(ROOT),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "mission": "CuongCV durable work controller for public-site changes, application generation, Kiro specs, validation evidence, deployment, and recoverable handoffs.",
        "source_relationship": {
            "public_cv_source": str(ROOT / "src" / "data" / "resume-data.tsx"),
            "application_profile_source": str(ROOT / "application-system" / "data" / "master_profile.json"),
            "application_generator": str(ROOT / "application-system" / "scripts" / "generate_application.py"),
            "public_site": "https://pmlecuong.com",
            "kiro_specs": str(KIRO_SPECS_DIR),
        },
        "required_resume_files": [
            str(AGENTS_PATH),
            str(STATE_MD_PATH),
            str(README_PATH),
            str(APPLICATION_AGENTS_PATH),
        ],
        "current_phase": "governance-bootstrap",
        "active_goal": "Establish a durable CuongCV SOP so long-running site, application, and deployment work can resume safely after compaction.",
        "active_task_id": None,
        "tasks": [
            {
                "id": "T-0001",
                "title": "Create the CuongCV SOP.py durable governance harness",
                "status": "in_progress",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "evidence": [],
                "notes": [
                    "Requested by the user on 2026-06-19 to bring the hardened Focalboard SOP workflow into CuongCV."
                ],
            }
        ],
        "kiro": {
            "active_spec": None,
            "active_task": None,
            "specs": {},
        },
        "checkpoints": [],
        "decisions": [
            {
                "date": "2026-06-19",
                "decision": "Use persisted local state and explicit resume briefs instead of trusting compressed chat memory.",
                "reason": "Compressed summaries can omit exact Kiro task status, validation evidence, and unfinished browser work.",
            }
        ],
        "open_questions": [],
        "sensitive_paths": [
            str(ROOT / ".env.local"),
            str(ROOT / "application-system" / "signature.png"),
        ],
        "repo_snapshot": {
            "created_at": None,
            "file_count": 0,
            "directory_count": 0,
            "files": {},
            "directories": [],
        },
        "work_session": {
            "id": None,
            "active": False,
            "started_at": None,
            "ended_at": None,
            "goal": None,
            "task_id": None,
            "last_update": None,
        },
        "handoff": {
            "updated_at": None,
            "current": None,
            "next": None,
            "risk": None,
            "files": [],
            "commands": [],
        },
        "command_log": [],
    }


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    default = default_state()
    for key, value in default.items():
        state.setdefault(key, value)
    required = state.get("required_resume_files", [])
    state["required_resume_files"] = list(dict.fromkeys([str(AGENTS_PATH), str(STATE_MD_PATH), str(README_PATH), str(APPLICATION_AGENTS_PATH)] + required))
    state.setdefault("work_session", default["work_session"])
    state.setdefault("handoff", default["handoff"])
    state.setdefault("command_log", [])
    state.setdefault("repo_snapshot", default["repo_snapshot"])
    state.setdefault("kiro", default["kiro"])
    return state


@contextmanager
def state_lock(exclusive: bool):
    global _ACTIVE_LOCK
    if _ACTIVE_LOCK is not None:
        yield
        return
    SOP_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_LOCK_PATH.open("a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        _ACTIVE_LOCK = lock_fh
        try:
            yield
        finally:
            _ACTIVE_LOCK = None
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as fh:
        temp_path = Path(fh.name)
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    temp_path.replace(path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def load_state() -> dict[str, Any]:
    with state_lock(exclusive=False):
        if not STATE_PATH.exists():
            return default_state()
        with STATE_PATH.open("r", encoding="utf-8") as fh:
            return normalize_state(json.load(fh))


def save_state(state: dict[str, Any]) -> None:
    with state_lock(exclusive=True):
        state["updated_at"] = now_iso()
        atomic_write_text(STATE_PATH, json.dumps(state, indent=2, sort_keys=True) + "\n")
        write_state_markdown(state)


def get_task(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in state.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise SystemExit(f"Unknown task id: {task_id}")


def next_task_id(state: dict[str, Any]) -> str:
    max_num = 0
    for task in state.get("tasks", []):
        tid = str(task.get("id", ""))
        if tid.startswith("T-"):
            try:
                max_num = max(max_num, int(tid.split("-", 1)[1]))
            except ValueError:
                pass
    return f"T-{max_num + 1:04d}"


def render_state_markdown(state: dict[str, Any]) -> str:
    active_task = state.get("active_task_id") or "None"
    work_session = state.get("work_session") or {}
    handoff = state.get("handoff") or {}
    lines = [
        "# SOP State",
        "",
        "This file is generated by `SOP.py`. Edit task state through the script when possible.",
        "",
        "## Recovery Instructions",
        "",
        "When an agent resumes after context compaction or a new session:",
        "",
        "1. Read `AGENTS.md`.",
        "2. Run `python3 SOP.py status`.",
        "3. Run `python3 SOP.py resume`.",
        "4. Continue only from the persisted active task, pending tasks, checkpoints, and open questions below.",
        "5. Do not mark work complete without concrete evidence in the task entry.",
        "",
        "## Current State",
        "",
        f"- repo: `{state.get('repo')}`",
        f"- updated_at: `{state.get('updated_at')}`",
        f"- current_phase: `{state.get('current_phase')}`",
        f"- active_goal: {state.get('active_goal')}",
        f"- active_task_id: `{active_task}`",
        f"- work_session: `{work_session.get('id') or 'None'}` active=`{work_session.get('active')}`",
        "",
        "## Required Resume Files",
        "",
    ]
    for path in state.get("required_resume_files", []):
        lines.append(f"- `{path}`")

    lines.extend(["", "## Tasks", ""])
    for task in state.get("tasks", []):
        lines.append(f"- `{task.get('id')}` [{task.get('status')}] {task.get('title')}")
        evidence = task.get("evidence") or []
        if evidence:
            lines.append(f"  - evidence: {'; '.join(evidence)}")
        notes = task.get("notes") or []
        if notes:
            lines.append(f"  - notes: {'; '.join(notes)}")
        if task.get("blocked_reason"):
            lines.append(f"  - blocked_reason: {task.get('blocked_reason')}")

    lines.extend(["", "## Current Handoff", ""])
    if handoff.get("updated_at"):
        lines.append(f"- updated_at: `{handoff.get('updated_at')}`")
        lines.append(f"- current: {handoff.get('current')}")
        lines.append(f"- next: {handoff.get('next')}")
        lines.append(f"- risk: {handoff.get('risk')}")
        if handoff.get("files"):
            lines.append(f"- files: {', '.join(handoff.get('files', []))}")
        if handoff.get("commands"):
            lines.append(f"- commands: {', '.join(handoff.get('commands', []))}")
    else:
        lines.append("- None recorded.")

    kiro = state.get("kiro") or {}
    lines.extend(["", "## Kiro Execution State", ""])
    lines.append(f"- active_spec: `{kiro.get('active_spec') or 'None'}`")
    lines.append(f"- active_task: `{kiro.get('active_task') or 'None'}`")
    specs = (kiro.get("specs") or {})
    if not specs:
        lines.append("- No Kiro task state recorded yet.")
    for spec_name, spec_state in sorted(specs.items()):
        lines.append(f"- `{spec_name}`")
        for task_id, task_state in sorted((spec_state.get("tasks") or {}).items()):
            lines.append(
                f"  - task `{task_id}` [{task_state.get('status')}] {task_state.get('title', '')}"
            )
            evidence = task_state.get("evidence") or []
            if evidence:
                lines.append(f"    - evidence: {'; '.join(evidence)}")
            if task_state.get("risk"):
                lines.append(f"    - risk: {task_state.get('risk')}")

    lines.extend(["", "## Recent Commands", ""])
    command_log = state.get("command_log", [])[-8:]
    if not command_log:
        lines.append("- None recorded.")
    for entry in command_log:
        lines.append(f"- `{entry.get('time')}` exit={entry.get('exit_code')} `{entry.get('command')}`")
        if entry.get("log_path"):
            lines.append(f"  - log: `{entry.get('log_path')}`")

    lines.extend(["", "## Latest Checkpoints", ""])
    checkpoints = state.get("checkpoints", [])[-8:]
    if not checkpoints:
        lines.append("- None yet.")
    for checkpoint in checkpoints:
        lines.append(f"- `{checkpoint.get('time')}` {checkpoint.get('label')}: {checkpoint.get('summary')}")
        for key in ("next_steps", "files_changed", "commands_run", "open_questions"):
            values = checkpoint.get(key) or []
            if values:
                lines.append(f"  - {key}: {'; '.join(values)}")

    lines.extend(["", "## Decisions", ""])
    for decision in state.get("decisions", []):
        lines.append(f"- `{decision.get('date')}` {decision.get('decision')}")
        if decision.get("reason"):
            lines.append(f"  - reason: {decision.get('reason')}")

    lines.extend(["", "## Open Questions", ""])
    questions = state.get("open_questions", [])
    if not questions:
        lines.append("- None.")
    else:
        for question in questions:
            lines.append(f"- {question}")

    lines.extend(["", "## Sensitive Paths", ""])
    for path in state.get("sensitive_paths", []):
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def write_state_markdown(state: dict[str, Any]) -> None:
    atomic_write_text(STATE_MD_PATH, render_state_markdown(state))


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_exclude(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    rel = path.relative_to(ROOT).as_posix()
    return (
        rel in DEFAULT_AUDIT_EXCLUDED_PATHS
        or any(rel.startswith(prefix) for prefix in DEFAULT_AUDIT_EXCLUDED_PREFIXES)
        or any(part in DEFAULT_AUDIT_EXCLUDES for part in rel_parts)
    )


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_repo_inventory(include_hashes: bool = False) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    directories: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if should_exclude(path):
            continue
        rel = relative_path(path)
        if path.is_dir():
            directories.append(rel)
            continue
        if not path.is_file():
            continue
        stat = path.stat()
        entry: dict[str, Any] = {
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }
        if include_hashes:
            entry["sha256"] = file_digest(path)
        files[rel] = entry
    return {
        "created_at": now_iso(),
        "file_count": len(files),
        "directory_count": len(directories),
        "files": files,
        "directories": directories,
    }


def diff_snapshot(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, list[str]]:
    previous_files = set((previous or {}).get("files", {}).keys())
    current_files = set(current.get("files", {}).keys())
    previous_dirs = set((previous or {}).get("directories", []))
    current_dirs = set(current.get("directories", []))

    modified: list[str] = []
    previous_file_meta = (previous or {}).get("files", {})
    for rel in sorted(previous_files & current_files):
        prev = previous_file_meta.get(rel, {})
        cur = current["files"].get(rel, {})
        if prev.get("sha256") and cur.get("sha256"):
            changed = prev.get("sha256") != cur.get("sha256")
        else:
            changed = prev.get("size") != cur.get("size") or prev.get("mtime") != cur.get("mtime")
        if changed:
            modified.append(rel)

    return {
        "new_files": sorted(current_files - previous_files),
        "deleted_files": sorted(previous_files - current_files),
        "modified_files": modified,
        "new_directories": sorted(current_dirs - previous_dirs),
        "deleted_directories": sorted(previous_dirs - current_dirs),
    }


def print_status(state: dict[str, Any]) -> None:
    print(f"Repo: {state.get('repo')}")
    print(f"Updated: {state.get('updated_at')}")
    print(f"Phase: {state.get('current_phase')}")
    print(f"Active goal: {state.get('active_goal')}")
    print(f"Active task: {state.get('active_task_id') or 'None'}")
    print("")
    print("Tasks:")
    for task in state.get("tasks", []):
        print(f"  {task.get('id')} [{task.get('status')}] {task.get('title')}")
    print("")
    kiro = state.get("kiro") or {}
    print("Kiro:")
    print(f"  active_spec: {kiro.get('active_spec') or 'None'}")
    print(f"  active_task: {kiro.get('active_task') or 'None'}")
    print("")
    print("Open questions:")
    questions = state.get("open_questions") or []
    if not questions:
        print("  None")
    for question in questions:
        print(f"  - {question}")
    snapshot = state.get("repo_snapshot") or {}
    print("")
    print("Repo snapshot:")
    if snapshot.get("created_at"):
        print(f"  created_at: {snapshot.get('created_at')}")
        print(f"  files: {snapshot.get('file_count')} directories: {snapshot.get('directory_count')}")
    else:
        print("  None recorded. Run: python3 SOP.py snapshot")
    handoff = state.get("handoff") or {}
    print("")
    print("Handoff:")
    if handoff.get("updated_at"):
        print(f"  updated_at: {handoff.get('updated_at')}")
        print(f"  current: {handoff.get('current')}")
        print(f"  next: {handoff.get('next')}")
        print(f"  risk: {handoff.get('risk')}")
    else:
        print("  None recorded. Run: python3 SOP.py handoff ...")


def print_resume_brief(state: dict[str, Any]) -> None:
    print("# Compaction Recovery Brief")
    print("")
    print("Do not trust compressed conversation memory as completion proof.")
    print("Rehydrate from these files and this persisted state.")
    print("")
    print("Must read:")
    for path in state.get("required_resume_files", []):
        exists = "exists" if Path(path).exists() else "missing"
        print(f"- {path} ({exists})")
    print("")
    print(f"Current phase: {state.get('current_phase')}")
    print(f"Active goal: {state.get('active_goal')}")
    print(f"Active task: {state.get('active_task_id') or 'None'}")
    kiro = state.get("kiro") or {}
    print(f"Active Kiro spec: {kiro.get('active_spec') or 'None'}")
    print(f"Active Kiro task: {kiro.get('active_task') or 'None'}")
    print("")
    active = state.get("active_task_id")
    if active:
        task = get_task(state, active)
        print(f"Continue task: {task.get('id')} [{task.get('status')}] {task.get('title')}")
        if task.get("notes"):
            print("Task notes:")
            for note in task.get("notes", []):
                print(f"- {note}")
    else:
        pending = [t for t in state.get("tasks", []) if t.get("status") in {"pending", "in_progress", "blocked"}]
        if pending:
            print("No active task is set. Review pending/blocked tasks before starting anything new:")
            for task in pending:
                print(f"- {task.get('id')} [{task.get('status')}] {task.get('title')}")
        else:
            print("No active or pending tasks recorded.")
    print("")
    handoff = state.get("handoff") or {}
    print("Current handoff:")
    if handoff.get("updated_at"):
        print(f"- updated_at: {handoff.get('updated_at')}")
        print(f"- current: {handoff.get('current')}")
        print(f"- next: {handoff.get('next')}")
        print(f"- risk: {handoff.get('risk')}")
        for path in handoff.get("files", []):
            print(f"- file: {path}")
        for command in handoff.get("commands", []):
            print(f"- command: {command}")
    else:
        print("- None recorded.")
    print("")
    print("Latest checkpoints:")
    checkpoints = state.get("checkpoints", [])[-5:]
    if not checkpoints:
        print("- None yet.")
    for checkpoint in checkpoints:
        print(f"- {checkpoint.get('time')} {checkpoint.get('label')}: {checkpoint.get('summary')}")
    print("")
    print("Resume rule: verify filesystem state before claiming a task is done.")


def kiro_spec_dir(spec: str) -> Path:
    path = KIRO_SPECS_DIR / spec
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Unknown Kiro spec: {spec} ({path})")
    return path


def parse_kiro_tasks(spec: str) -> dict[str, dict[str, str]]:
    tasks_path = kiro_spec_dir(spec) / "tasks.md"
    if not tasks_path.exists():
        raise SystemExit(f"Missing tasks.md for Kiro spec: {spec}")
    tasks: dict[str, dict[str, str]] = {}
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        marker = stripped[3:4].lower()
        rest = stripped[6:].strip() if len(stripped) > 6 else ""
        task_id = None
        title = rest
        if "." in rest:
            candidate, possible_title = rest.split(".", 1)
            if candidate.strip().isdigit():
                task_id = candidate.strip()
                title = possible_title.strip()
        if not task_id:
            task_id = str(len(tasks) + 1)
        tasks[task_id] = {
            "title": title,
            "checkbox": "done" if marker == "x" else "pending",
            "source": str(tasks_path),
        }
    return tasks


def ensure_kiro_spec_state(state: dict[str, Any], spec: str) -> dict[str, Any]:
    kiro = state.setdefault("kiro", {"active_spec": None, "active_task": None, "specs": {}})
    specs = kiro.setdefault("specs", {})
    spec_state = specs.setdefault(
        spec,
        {
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "tasks": {},
            "notes": [],
        },
    )
    parsed = parse_kiro_tasks(spec)
    for task_id, parsed_task in parsed.items():
        spec_state.setdefault("tasks", {}).setdefault(
            task_id,
            {
                "title": parsed_task["title"],
                "status": parsed_task["checkbox"],
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "evidence": [],
                "risk": None,
            },
        )
        spec_state["tasks"][task_id]["title"] = parsed_task["title"]
        spec_state["tasks"][task_id]["checkbox"] = parsed_task["checkbox"]
    spec_state["updated_at"] = now_iso()
    return spec_state


def cmd_kiro_status(args: argparse.Namespace) -> None:
    state = load_state()
    spec_state = ensure_kiro_spec_state(state, args.spec)
    save_state(state)
    print(f"Kiro spec: {args.spec}")
    print(f"tasks.md: {kiro_spec_dir(args.spec) / 'tasks.md'}")
    print("")
    for task_id, task in sorted(spec_state.get("tasks", {}).items(), key=lambda item: (0, int(item[0])) if item[0].isdigit() else (1, item[0])):
        print(f"{task_id}. [{task.get('status')}] checkbox={task.get('checkbox')} {task.get('title')}")
        evidence = task.get("evidence") or []
        if evidence:
            print(f"   evidence: {'; '.join(evidence)}")
        if task.get("risk"):
            print(f"   risk: {task.get('risk')}")


def cmd_kiro_start(args: argparse.Namespace) -> None:
    state = load_state()
    spec_state = ensure_kiro_spec_state(state, args.spec)
    task = spec_state.get("tasks", {}).get(args.task)
    if not task:
        raise SystemExit(f"Unknown Kiro task {args.task} in {args.spec}")
    if task.get("status") == "done" and not args.reopen:
        raise SystemExit(f"Kiro task {args.spec}#{args.task} is already done. Use --reopen if this is intentional.")
    task["status"] = "in_progress"
    task["updated_at"] = now_iso()
    if args.note:
        task.setdefault("notes", []).append(args.note)
    state.setdefault("kiro", {})["active_spec"] = args.spec
    state.setdefault("kiro", {})["active_task"] = args.task
    state["active_goal"] = f"Execute Kiro spec {args.spec} task {args.task}: {task.get('title')}"
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": "kiro-start",
            "summary": f"Started Kiro task {args.spec}#{args.task}: {task.get('title')}",
            "next_steps": ["Update handoff after each meaningful unit of work.", "Do not mark done without evidence."],
            "files_changed": [str(kiro_spec_dir(args.spec) / "tasks.md")],
            "commands_run": [f"python3 SOP.py kiro-start --spec {args.spec} --task {args.task}"],
            "open_questions": [],
        }
    )
    save_state(state)
    print(f"Started Kiro task {args.spec}#{args.task}")


def cmd_kiro_done(args: argparse.Namespace) -> None:
    if not args.evidence:
        raise SystemExit("Kiro completion requires at least one --evidence entry.")
    state = load_state()
    spec_state = ensure_kiro_spec_state(state, args.spec)
    task = spec_state.get("tasks", {}).get(args.task)
    if not task:
        raise SystemExit(f"Unknown Kiro task {args.task} in {args.spec}")
    task["status"] = "done"
    task["updated_at"] = now_iso()
    task.setdefault("evidence", []).extend(args.evidence)
    if args.playwright:
        task.setdefault("playwright_evidence", []).extend(args.playwright)
        task.setdefault("evidence", []).extend([f"Playwright: {item}" for item in args.playwright])
    if args.risk:
        task["risk"] = args.risk
    kiro = state.setdefault("kiro", {})
    if kiro.get("active_spec") == args.spec and kiro.get("active_task") == args.task:
        kiro["active_task"] = None
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": "kiro-done",
            "summary": f"Completed Kiro task {args.spec}#{args.task}: {task.get('title')}",
            "next_steps": args.next_step or [],
            "files_changed": args.file or [],
            "commands_run": [f"python3 SOP.py kiro-done --spec {args.spec} --task {args.task}"],
            "open_questions": [],
        }
    )
    save_state(state)
    print(f"Completed Kiro task {args.spec}#{args.task}")


def cmd_kiro_block(args: argparse.Namespace) -> None:
    state = load_state()
    spec_state = ensure_kiro_spec_state(state, args.spec)
    task = spec_state.get("tasks", {}).get(args.task)
    if not task:
        raise SystemExit(f"Unknown Kiro task {args.task} in {args.spec}")
    task["status"] = "blocked"
    task["blocked_reason"] = args.reason
    task["updated_at"] = now_iso()
    state.setdefault("open_questions", []).append(f"Kiro {args.spec}#{args.task}: {args.reason}")
    kiro = state.setdefault("kiro", {})
    if kiro.get("active_spec") == args.spec and kiro.get("active_task") == args.task:
        kiro["active_task"] = None
    save_state(state)
    print(f"Blocked Kiro task {args.spec}#{args.task}")


def cmd_validate_kiro(args: argparse.Namespace) -> None:
    spec = args.spec
    tasks = parse_kiro_tasks(spec)
    state = load_state()
    spec_state = ensure_kiro_spec_state(state, spec)
    problems: list[str] = []
    for task_id, task in spec_state.get("tasks", {}).items():
        if task_id not in tasks:
            problems.append(f"Task {task_id} exists in SOP state but not in tasks.md")
        if task.get("status") == "done" and not task.get("evidence"):
            problems.append(f"Task {task_id} is done in SOP state without evidence")
    save_state(state)
    if problems:
        print("Kiro validation failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(f"Kiro validation passed for {spec}.")


def cmd_init(args: argparse.Namespace) -> None:
    if STATE_PATH.exists() and not args.force:
        state = load_state()
        write_state_markdown(state)
        print("SOP state already exists. Refreshed SOP_STATE.md.")
        return
    state = default_state()
    state["active_task_id"] = "T-0001"
    state["checkpoints"].append(
        {
            "time": now_iso(),
            "label": "init",
            "summary": "Initialized durable SOP governance state for the CuongCV repository.",
            "next_steps": ["Validate SOP.py", "Update AGENTS.md and governance documentation"],
            "files_changed": [str(STATE_PATH), str(STATE_MD_PATH), str(ROOT / "SOP.py")],
            "commands_run": ["python3 SOP.py init"],
            "open_questions": [],
        }
    )
    save_state(state)
    print(f"Initialized SOP state at {STATE_PATH}")


def cmd_status(args: argparse.Namespace) -> None:
    print_status(load_state())


def cmd_resume(args: argparse.Namespace) -> None:
    print_resume_brief(load_state())


def cmd_add_task(args: argparse.Namespace) -> None:
    state = load_state()
    task_id = args.id or next_task_id(state)
    if task_id in {task.get("id") for task in state.get("tasks", [])}:
        raise SystemExit(f"Task already exists: {task_id}")
    task = {
        "id": task_id,
        "title": args.title,
        "status": args.status,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "evidence": [],
        "notes": args.note or [],
    }
    state.setdefault("tasks", []).append(task)
    save_state(state)
    print(f"Added {task_id}")


def cmd_start(args: argparse.Namespace) -> None:
    state = load_state()
    active = state.get("active_task_id")
    if active and active != args.task_id:
        raise SystemExit(f"Cannot start {args.task_id}; active task already set: {active}")
    task = get_task(state, args.task_id)
    if task.get("status") == "done":
        raise SystemExit(f"Cannot start completed task: {args.task_id}")
    task["status"] = "in_progress"
    task["updated_at"] = now_iso()
    if args.note:
        task.setdefault("notes", []).append(args.note)
    state["active_task_id"] = args.task_id
    save_state(state)
    print(f"Started {args.task_id}")


def cmd_done(args: argparse.Namespace) -> None:
    if not args.evidence:
        raise SystemExit("Completion requires at least one --evidence entry.")
    state = load_state()
    task = get_task(state, args.task_id)
    task["status"] = "done"
    task["updated_at"] = now_iso()
    task.setdefault("evidence", []).extend(args.evidence)
    if args.note:
        task.setdefault("notes", []).append(args.note)
    if state.get("active_task_id") == args.task_id:
        state["active_task_id"] = None
    save_state(state)
    print(f"Completed {args.task_id}")


def cmd_block(args: argparse.Namespace) -> None:
    state = load_state()
    task = get_task(state, args.task_id)
    task["status"] = "blocked"
    task["blocked_reason"] = args.reason
    task["updated_at"] = now_iso()
    if state.get("active_task_id") == args.task_id:
        state["active_task_id"] = None
    state.setdefault("open_questions", []).append(args.reason)
    save_state(state)
    print(f"Blocked {args.task_id}")


def cmd_checkpoint(args: argparse.Namespace) -> None:
    state = load_state()
    checkpoint = {
        "time": now_iso(),
        "label": args.label,
        "summary": args.summary,
        "next_steps": args.next_step or [],
        "files_changed": args.file or [],
        "commands_run": args.command or [],
        "open_questions": args.question or [],
    }
    state.setdefault("checkpoints", []).append(checkpoint)
    for question in args.question or []:
        state.setdefault("open_questions", []).append(question)
    save_state(state)
    print(f"Checkpoint recorded: {args.label}")


def cmd_handoff(args: argparse.Namespace) -> None:
    state = load_state()
    state["handoff"] = {
        "updated_at": now_iso(),
        "current": args.current,
        "next": args.next,
        "risk": args.risk,
        "files": args.file or [],
        "commands": args.command or [],
    }
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": args.label,
            "summary": f"Handoff updated: {args.current}",
            "next_steps": [args.next],
            "files_changed": args.file or [],
            "commands_run": args.command or ["python3 SOP.py handoff"],
            "open_questions": [],
        }
    )
    save_state(state)
    print("Handoff updated.")


def cmd_session(args: argparse.Namespace) -> None:
    state = load_state()
    session = state.get("work_session") or {}
    if args.end:
        session["active"] = False
        session["ended_at"] = now_iso()
        session["last_update"] = now_iso()
        state["work_session"] = session
        save_state(state)
        print(f"Ended work session {session.get('id') or 'None'}")
        return

    requested_goal = args.goal or session.get("goal")
    requested_task_id = args.task_id or session.get("task_id") or state.get("active_task_id")
    should_start_fresh = (
        not session.get("active")
        or not session.get("id")
        or (
            not args.continue_existing
            and (
                (args.goal and args.goal != session.get("goal"))
                or (args.task_id and args.task_id != session.get("task_id"))
            )
        )
    )
    session_id = f"WS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}" if should_start_fresh else session.get("id")
    session.update(
        {
            "id": session_id,
            "active": True,
            "started_at": now_iso() if should_start_fresh else session.get("started_at") or now_iso(),
            "ended_at": None,
            "goal": requested_goal,
            "task_id": requested_task_id,
            "last_update": now_iso(),
        }
    )
    state["work_session"] = session
    if requested_goal:
        state["active_goal"] = requested_goal
    save_state(state)
    print(f"Work session active: {session_id}")


def run_audit_for_preflight() -> int:
    state = load_state()
    previous = state.get("repo_snapshot") or {}
    if not previous.get("created_at"):
        print("No baseline snapshot exists. Run: python3 SOP.py snapshot")
        return 2
    current = collect_repo_inventory(include_hashes=bool(previous.get("files") and any("sha256" in meta for meta in previous["files"].values())))
    diff = diff_snapshot(previous, current)
    changed_count = sum(len(values) for values in diff.values())
    if changed_count == 0:
        print("Audit passed: no filesystem drift since the last SOP snapshot.")
        return 0
    print(f"Audit warning: {changed_count} filesystem change(s) since last snapshot.")
    for label, values in diff.items():
        if values:
            print(f"- {label}: {len(values)}")
    return 1


def cmd_preflight(args: argparse.Namespace) -> None:
    state = load_state()
    print_status(state)
    print("")
    print_resume_brief(state)
    print("")
    warnings = []
    work_session = state.get("work_session") or {}
    kiro = state.get("kiro") or {}
    if work_session.get("active") and work_session.get("goal") != state.get("active_goal"):
        warnings.append("active work_session goal differs from active_goal; start a fresh SOP session for the current task.")
    if state.get("active_goal", "").startswith("Execute Kiro spec") and not kiro.get("active_task"):
        warnings.append("active_goal points at a Kiro task but no active Kiro task is set; update session/handoff before coding.")
    if warnings:
        print("Preflight warnings:")
        for warning in warnings:
            print(f"- {warning}")
        print("")
    audit_code = run_audit_for_preflight()
    if warnings and args.strict:
        raise SystemExit(1)
    if audit_code == 1 and args.strict:
        raise SystemExit(1)
    if audit_code == 2 and args.strict:
        raise SystemExit(2)
    state = load_state()
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": args.label,
            "summary": "Preflight completed: status, resume brief, and audit check were run.",
            "next_steps": ["Set or verify active task, update handoff, then use SOP.py run for commands where practical."],
            "files_changed": [],
            "commands_run": ["python3 SOP.py preflight"],
            "open_questions": [],
        }
    )
    save_state(state)
    print("Preflight recorded.")


def cmd_postflight(args: argparse.Namespace) -> None:
    state = load_state()
    state["active_goal"] = args.summary
    state["current_phase"] = "postflight"
    if not args.keep_session:
        session = state.get("work_session") or {}
        if session.get("active"):
            session["active"] = False
            session["ended_at"] = now_iso()
            session["last_update"] = now_iso()
            state["work_session"] = session
    state["handoff"] = {
        "updated_at": now_iso(),
        "current": args.summary,
        "next": "; ".join(args.next_step or []) or "Review latest checkpoints before continuing.",
        "risk": "Do not resume from stale chat context; run SOP preflight/status/resume and verify filesystem drift first.",
        "files": args.file or [],
        "commands": ["python3 SOP.py postflight"],
    }
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": args.label,
            "summary": args.summary,
            "next_steps": args.next_step or [],
            "files_changed": args.file or [],
            "commands_run": ["python3 SOP.py postflight"],
            "open_questions": args.question or [],
        }
    )
    for question in args.question or []:
        state.setdefault("open_questions", []).append(question)
    save_state(state)
    cmd_validate(argparse.Namespace())
    state = load_state()
    state["repo_snapshot"] = collect_repo_inventory(include_hashes=args.hashes)
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": f"{args.label}-snapshot",
            "summary": "Postflight recorded fresh repository snapshot.",
            "next_steps": [],
            "files_changed": [str(STATE_PATH), str(STATE_MD_PATH)],
            "commands_run": ["python3 SOP.py postflight"],
            "open_questions": [],
        }
    )
    save_state(state)
    audit_code = run_audit_for_preflight()
    if audit_code != 0:
        raise SystemExit(audit_code)
    print("Postflight complete.")


def cmd_run(args: argparse.Namespace) -> None:
    if not args.command:
        raise SystemExit("Usage: python3 SOP.py run -- <command>")
    command_parts = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command_parts:
        raise SystemExit("Usage: python3 SOP.py run -- <command>")
    command = shlex.join(command_parts)
    requested_cwd = Path(args.cwd).expanduser() if args.cwd else ROOT
    run_cwd = (requested_cwd if requested_cwd.is_absolute() else ROOT / requested_cwd).resolve()
    try:
        run_cwd.relative_to(ROOT)
    except ValueError:
        raise SystemExit(f"--cwd must stay inside the repository: {run_cwd}") from None
    if not run_cwd.exists() or not run_cwd.is_dir():
        raise SystemExit(f"Invalid --cwd directory: {run_cwd}")
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_name = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".log"
    log_path = RUN_LOG_DIR / log_name
    started = now_iso()
    completed = None
    result = subprocess.run(command_parts, cwd=run_cwd, shell=False, text=True, capture_output=True)
    completed = now_iso()
    output = []
    if result.stdout:
        output.append("STDOUT:\n" + result.stdout)
    if result.stderr:
        output.append("STDERR:\n" + result.stderr)
    atomic_write_text(log_path, "\n\n".join(output) if output else "(no output)\n")
    state = load_state()
    entry = {
        "time": completed,
        "started_at": started,
        "command": command,
        "cwd": str(run_cwd),
        "exit_code": result.returncode,
        "log_path": str(log_path),
    }
    state.setdefault("command_log", []).append(entry)
    state["command_log"] = state["command_log"][-50:]
    state.setdefault("checkpoints", []).append(
        {
            "time": completed,
            "label": args.label,
            "summary": f"Ran command with exit code {result.returncode} in {run_cwd}: {command}",
            "next_steps": [],
            "files_changed": [],
            "commands_run": [command],
            "open_questions": [],
            "run_log": str(log_path),
        }
    )
    save_state(state)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    print(f"\n[SOP run] cwd={run_cwd} exit={result.returncode} log={log_path}")
    if result.returncode != 0 and not args.allow_failure:
        raise SystemExit(result.returncode)


def cmd_snapshot(args: argparse.Namespace) -> None:
    state = load_state()
    inventory = collect_repo_inventory(include_hashes=args.hashes)
    state["repo_snapshot"] = inventory
    state.setdefault("checkpoints", []).append(
        {
            "time": now_iso(),
            "label": args.label,
            "summary": f"Recorded repository snapshot with {inventory['file_count']} files and {inventory['directory_count']} directories.",
            "next_steps": ["Run python3 SOP.py audit before and after future multi-step work."],
            "files_changed": [str(STATE_PATH), str(STATE_MD_PATH)],
            "commands_run": ["python3 SOP.py snapshot"],
            "open_questions": [],
        }
    )
    save_state(state)
    print(f"Snapshot recorded: {inventory['file_count']} files, {inventory['directory_count']} directories")


def cmd_audit(args: argparse.Namespace) -> None:
    state = load_state()
    previous = state.get("repo_snapshot") or {}
    if not previous.get("created_at"):
        print("No baseline snapshot exists. Run: python3 SOP.py snapshot")
        raise SystemExit(2)
    current = collect_repo_inventory(include_hashes=bool(previous.get("files") and any("sha256" in meta for meta in previous["files"].values())))
    diff = diff_snapshot(previous, current)
    changed_count = sum(len(values) for values in diff.values())

    print(f"Baseline: {previous.get('created_at')} ({previous.get('file_count')} files, {previous.get('directory_count')} directories)")
    print(f"Current:  {current.get('created_at')} ({current.get('file_count')} files, {current.get('directory_count')} directories)")
    print("")
    if changed_count == 0:
        print("Audit passed: no filesystem drift since the last SOP snapshot.")
        return

    print("Audit found filesystem drift:")
    for label, values in diff.items():
        if not values:
            continue
        print(f"\n{label}:")
        limit = args.limit
        for item in values[:limit]:
            print(f"  - {item}")
        if len(values) > limit:
            print(f"  ... {len(values) - limit} more")

    if args.record:
        state.setdefault("checkpoints", []).append(
            {
                "time": now_iso(),
                "label": args.label,
                "summary": f"Audit recorded {changed_count} filesystem change(s) since the last snapshot.",
                "next_steps": ["Review drift; run python3 SOP.py snapshot after accepting the new repo state."],
                "files_changed": diff["new_files"] + diff["modified_files"] + diff["deleted_files"],
                "commands_run": ["python3 SOP.py audit --record"],
                "open_questions": [],
                "audit_diff": diff,
            }
        )
        save_state(state)
        print("\nAudit checkpoint recorded.")

    if args.fail_on_drift:
        raise SystemExit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    state = load_state()
    missing = []
    for path in [AGENTS_PATH, APPLICATION_AGENTS_PATH, README_PATH, SOP_RESEARCH_PATH, STATE_PATH, STATE_MD_PATH, ROOT / "SOP.py"]:
        if not path.exists():
            missing.append(str(path))
    for path in state.get("required_resume_files", []):
        if not Path(path).exists():
            missing.append(path)
    active = state.get("active_task_id")
    if active:
        task = get_task(state, active)
        if task.get("status") != "in_progress":
            missing.append(f"active_task_id {active} is not in_progress")
    kiro = state.get("kiro") or {}
    if state.get("active_goal", "").startswith("Execute Kiro spec") and not kiro.get("active_task"):
        missing.append("active_goal references a Kiro task but kiro.active_task is empty")
    if missing:
        print("Validation failed:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)
    print("Validation passed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CuongCV SOP governance harness")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize or refresh SOP state")
    init.add_argument("--force", action="store_true", help="Overwrite existing SOP state")
    init.set_defaults(func=cmd_init)

    status = sub.add_parser("status", help="Print current SOP task state")
    status.set_defaults(func=cmd_status)

    resume = sub.add_parser("resume", help="Print compaction recovery brief")
    resume.set_defaults(func=cmd_resume)

    add = sub.add_parser("add-task", help="Add a task")
    add.add_argument("title")
    add.add_argument("--id")
    add.add_argument("--status", choices=sorted(VALID_TASK_STATUSES), default="pending")
    add.add_argument("--note", action="append")
    add.set_defaults(func=cmd_add_task)

    start = sub.add_parser("start", help="Start a task")
    start.add_argument("task_id")
    start.add_argument("--note")
    start.set_defaults(func=cmd_start)

    done = sub.add_parser("done", help="Complete a task with evidence")
    done.add_argument("task_id")
    done.add_argument("--evidence", action="append", required=True)
    done.add_argument("--note")
    done.set_defaults(func=cmd_done)

    block = sub.add_parser("block", help="Block a task")
    block.add_argument("task_id")
    block.add_argument("--reason", required=True)
    block.set_defaults(func=cmd_block)

    checkpoint = sub.add_parser("checkpoint", help="Record a checkpoint")
    checkpoint.add_argument("--label", required=True)
    checkpoint.add_argument("--summary", required=True)
    checkpoint.add_argument("--next-step", action="append")
    checkpoint.add_argument("--file", action="append")
    checkpoint.add_argument("--command", action="append")
    checkpoint.add_argument("--question", action="append")
    checkpoint.set_defaults(func=cmd_checkpoint)

    handoff = sub.add_parser("handoff", help="Record exact resume instructions for context compaction")
    handoff.add_argument("--current", required=True)
    handoff.add_argument("--next", required=True)
    handoff.add_argument("--risk", required=True)
    handoff.add_argument("--file", action="append")
    handoff.add_argument("--command", action="append")
    handoff.add_argument("--label", default="handoff")
    handoff.set_defaults(func=cmd_handoff)

    session = sub.add_parser("session", help="Start, update, or end a durable work session")
    session.add_argument("--goal")
    session.add_argument("--task-id")
    session.add_argument("--end", action="store_true")
    session.add_argument("--continue-existing", action="store_true", help="Update the current active session instead of starting a fresh one when goal/task changes")
    session.set_defaults(func=cmd_session)

    run_cmd = sub.add_parser("run", help="Run a shell command and record exit code plus log")
    run_cmd.add_argument("--label", default="run")
    run_cmd.add_argument("--allow-failure", action="store_true")
    run_cmd.add_argument("--cwd", help="Directory to run from, relative to repo root or absolute")
    run_cmd.add_argument("command", nargs=argparse.REMAINDER)
    run_cmd.set_defaults(func=cmd_run)

    preflight = sub.add_parser("preflight", help="Run status, resume, and audit before work")
    preflight.add_argument("--label", default="preflight")
    preflight.add_argument("--strict", action="store_true")
    preflight.set_defaults(func=cmd_preflight)

    postflight = sub.add_parser("postflight", help="Record final checkpoint, validate, snapshot, and audit")
    postflight.add_argument("--label", default="postflight")
    postflight.add_argument("--summary", required=True)
    postflight.add_argument("--next-step", action="append")
    postflight.add_argument("--file", action="append")
    postflight.add_argument("--question", action="append")
    postflight.add_argument("--hashes", action="store_true")
    postflight.add_argument("--keep-session", action="store_true", help="Keep the current durable work session active after postflight")
    postflight.set_defaults(func=cmd_postflight)

    snapshot = sub.add_parser("snapshot", help="Record current repository file/folder inventory")
    snapshot.add_argument("--label", default="repo-snapshot")
    snapshot.add_argument("--hashes", action="store_true", help="Store SHA-256 file hashes for stronger modified-file detection")
    snapshot.set_defaults(func=cmd_snapshot)

    audit = sub.add_parser("audit", help="Compare current repository inventory with last SOP snapshot")
    audit.add_argument("--record", action="store_true", help="Record audit drift as a checkpoint")
    audit.add_argument("--label", default="repo-audit")
    audit.add_argument("--limit", type=int, default=60)
    audit.add_argument("--fail-on-drift", action="store_true")
    audit.set_defaults(func=cmd_audit)

    validate = sub.add_parser("validate", help="Validate SOP governance files and state")
    validate.set_defaults(func=cmd_validate)

    kiro_status = sub.add_parser("kiro-status", help="Print durable task state for a Kiro spec")
    kiro_status.add_argument("--spec", required=True)
    kiro_status.set_defaults(func=cmd_kiro_status)

    kiro_start = sub.add_parser("kiro-start", help="Start a Kiro spec task in durable SOP state")
    kiro_start.add_argument("--spec", required=True)
    kiro_start.add_argument("--task", required=True)
    kiro_start.add_argument("--note")
    kiro_start.add_argument("--reopen", action="store_true")
    kiro_start.set_defaults(func=cmd_kiro_start)

    kiro_done = sub.add_parser("kiro-done", help="Mark a Kiro spec task done with evidence")
    kiro_done.add_argument("--spec", required=True)
    kiro_done.add_argument("--task", required=True)
    kiro_done.add_argument("--evidence", action="append", required=True)
    kiro_done.add_argument("--playwright", action="append")
    kiro_done.add_argument("--file", action="append")
    kiro_done.add_argument("--next-step", action="append")
    kiro_done.add_argument("--risk")
    kiro_done.set_defaults(func=cmd_kiro_done)

    kiro_block = sub.add_parser("kiro-block", help="Block a Kiro spec task with a durable reason")
    kiro_block.add_argument("--spec", required=True)
    kiro_block.add_argument("--task", required=True)
    kiro_block.add_argument("--reason", required=True)
    kiro_block.set_defaults(func=cmd_kiro_block)

    validate_kiro = sub.add_parser("validate-kiro", help="Validate durable Kiro state against tasks.md")
    validate_kiro.add_argument("--spec", required=True)
    validate_kiro.set_defaults(func=cmd_validate_kiro)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    # The lock covers the entire read-modify-write command transaction. Nested
    # load/save calls reuse it, preventing concurrent commands from overwriting
    # each other's logical updates.
    with state_lock(exclusive=True):
        args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
