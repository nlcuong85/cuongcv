#!/usr/bin/env python3
"""Local hard-gate controller for Student Application AI Helper work.

This is deliberately a small, dependency-free adaptation of the Sirius SOP.
It records local evidence and can declare an artifact ready only after the
current artifact hash matches the required local review/validation records.
It never sends state, CV files, or checker logic to the remote MCP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if os.name == "nt":
    import msvcrt
else:
    import fcntl

STATE_SCHEMA = 1
STATE_DIR = ".application-sop"
PROTECTED_PREFIXES = ("candidate/", "profile/", "voice/", "jobs/", "applications/")
ALLOWED_SUFFIXES = {".md", ".html", ".pdf", ".json", ".txt", ".jpg", ".jpeg", ".png", ".docx", ".py", ".mjs"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_rel(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path.as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def default_state(root: Path) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA,
        "created_at": now(),
        "updated_at": now(),
        "root": ".",
        "active": None,
        "decisions": {},
        "voice_intake": {},
        "evidence": {},
        "manifest_audit": None,
        "review_records": [],
        "ats_records": [],
        "command_receipts": [],
        "snapshot": {},
        "handoff": {},
        "risks": [],
    }


def paths(root: Path) -> tuple[Path, Path, Path, Path]:
    directory = root / STATE_DIR
    return directory, directory / "state.json", directory / "state.lock", directory / "SOP_STATE.md"


@contextmanager
def state_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        if os.name == "nt":
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load(root: Path) -> dict[str, Any]:
    directory, state_path, _, _ = paths(root)
    directory.mkdir(parents=True, exist_ok=True)
    if not state_path.exists():
        return default_state(root)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"SOP state is invalid JSON; restore it before continuing: {error}")
    if state.get("schema_version") != STATE_SCHEMA:
        raise SystemExit("Unsupported Application SOP state schema.")
    return state


def mirror(root: Path, state: dict[str, Any]) -> str:
    active = state.get("active") or {}
    review_count = len(state.get("review_records", []))
    handoff = state.get("handoff") or {}
    voice_intake = state.get("voice_intake") or {}
    return "\n".join([
        "# Application SOP State",
        "",
        f"Updated: {state.get('updated_at')}",
        f"Active task: {active.get('task_id', 'None')}",
        f"Job: {active.get('job_slug', 'None')}",
        f"Phase: {active.get('phase', 'ready')}",
        f"Review records: {review_count}",
        f"Open risks: {len(state.get('risks', []))}",
        f"Writing-sample intake: {voice_intake.get('status', 'not asked')}",
        "",
        "## Recovery",
        "",
        f"Current: {handoff.get('current', 'No handoff recorded.')}",
        f"Next command: {handoff.get('next_command', 'python3 application_sop.py boot --strict')}",
        f"Do not assume: {handoff.get('risk', 'No unverified document can be called ready without a release receipt.')}",
        "",
    ])


def save(root: Path, state: dict[str, Any]) -> None:
    directory, state_path, _, mirror_path = paths(root)
    directory.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as handle:
        json.dump(state, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, state_path)
    mirror_path.write_text(mirror(root, state), encoding="utf-8")


def inventory(root: Path) -> dict[str, dict[str, Any]]:
    excluded = {STATE_DIR, ".git", "node_modules", "__pycache__", ".DS_Store"}
    values: dict[str, dict[str, Any]] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in excluded]
        for name in files:
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            if path.suffix.lower() not in ALLOWED_SUFFIXES or rel.startswith(".mcp/"):
                continue
            stat = path.stat()
            values[rel] = {"size": stat.st_size, "sha256": sha256(path)}
    return values


def audit_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, list[str]]:
    old_files = old.get("files", {})
    return {
        "new": sorted(set(new) - set(old_files)),
        "missing": sorted(set(old_files) - set(new)),
        "modified": sorted(key for key in set(old_files) & set(new) if old_files[key].get("sha256") != new[key].get("sha256")),
    }


def require_active(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("last_strict_boot_at"):
        raise SystemExit("Strict preflight is missing. Run application_sop.py boot --strict first.")
    active = state.get("active")
    if not active or not active.get("task_id"):
        raise SystemExit("No active application task. Run start after boot --strict.")
    return active


def receipt(state: dict[str, Any], command: str, inputs: list[str], outputs: list[str], status: str = "passed", detail: str = "") -> None:
    state.setdefault("command_receipts", []).append({
        "at": now(), "command": command, "status": status, "inputs": inputs,
        "outputs": outputs, "detail": detail,
    })
    state["command_receipts"] = state["command_receipts"][-100:]


def decision_gate(state: dict[str, Any], document: str) -> list[str]:
    missing = []
    if document in {"cv", "cover-letter"} and state.get("decisions", {}).get("photo") not in {"provided", "declined", "not_available"}:
        missing.append("photo question has not been answered")
    if document == "cover-letter" and state.get("decisions", {}).get("signature") not in {"provided", "declined", "not_available", "not_answered_after_request"}:
        missing.append("signature has not been requested/recorded")
    if document == "cover-letter" and state.get("decisions", {}).get("enclosures") not in {"cv_only_warned", "cv_plus_diploma", "cv_plus_reference", "cv_plus_two_or_more", "custom_confirmed"}:
        missing.append("cover-letter enclosure choices have not been recorded")
    if not state.get("manifest_audit") or state["manifest_audit"].get("status") != "workspace_current":
        missing.append("current workspace audit is missing")
    return missing


def current_reviews(state: dict[str, Any], artifact_rel: str) -> list[dict[str, Any]]:
    return [record for record in state.get("review_records", []) if record.get("artifact") == artifact_rel]


def current_ats_records(state: dict[str, Any], artifact_rel: str) -> list[dict[str, Any]]:
    return [record for record in state.get("ats_records", []) if record.get("artifact") == artifact_rel]


def cmd_boot(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root)
        current = inventory(root)
        baseline = state.get("snapshot") or {}
        if not baseline:
            state["snapshot"] = {"at": now(), "files": current}
            state["last_strict_boot_at"] = now()
            save(root, state)
            print("Application SOP initialized local baseline.")
            return 0
        diff = audit_diff(baseline, current)
        changed = sum(len(value) for value in diff.values())
        if changed and args.strict:
            print(json.dumps({"status": "blocked", "reason": "workspace drift", "diff": diff}, indent=2))
            return 1
        if args.strict:
            state["last_strict_boot_at"] = now()
            save(root, state)
        print(json.dumps({"status": "ready", "active": state.get("active"), "drift": diff}, indent=2))
        return 0


def cmd_start(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root)
        if not state.get("last_strict_boot_at"):
            raise SystemExit("Strict preflight is missing. Run application_sop.py boot --strict first.")
        if state.get("active") and state["active"].get("task_id") != args.task_id:
            raise SystemExit("Another application task is active; handoff/postflight it first.")
        state["active"] = {"task_id": args.task_id, "job_slug": args.job, "phase": "intake", "started_at": now()}
        state["handoff"] = {"current": "Application task started.", "next_command": "python3 application_sop.py intake-status", "risk": "Do not generate final documents before decisions and evidence are recorded."}
        receipt(state, "start", [], [], detail=args.goal)
        save(root, state)
        print(f"Started {args.task_id} for {args.job}")
    return 0


def cmd_decision(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root); require_active(state)
        state.setdefault("decisions", {})[args.name] = args.value
        receipt(state, "record-decision", [], [], detail=f"{args.name}={args.value}")
        save(root, state)
    print(f"Recorded {args.name}: {args.value}")
    return 0


def voice_intake_status(state: dict[str, Any]) -> dict[str, Any]:
    """Return the consent-aware state that tells an agent whether to ask once."""
    intake = state.get("voice_intake") or {}
    status = intake.get("status")
    if status == "enough":
        return {"status": "suppressed", "ask_user": False, "reason": "candidate_marked_enough", "voice_intake": intake}
    if status == "declined":
        return {"status": "suppressed", "ask_user": False, "reason": "candidate_declined_optional_samples", "voice_intake": intake}
    reminder_at = intake.get("next_reminder_at")
    if reminder_at:
        try:
            due = datetime.fromisoformat(reminder_at.replace("Z", "+00:00"))
        except ValueError:
            due = None
        if due and due > datetime.now(timezone.utc):
            return {"status": "not_due", "ask_user": False, "reason": "reminder_not_due", "next_reminder_at": reminder_at, "voice_intake": intake}
    return {"status": "ask_now", "ask_user": True, "reason": "no_active_suppression_or_reminder", "voice_intake": intake}


def cmd_voice_intake_status(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    print(json.dumps(voice_intake_status(load(root)), indent=2))
    return 0


def cmd_record_voice_intake(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root)
        entry: dict[str, Any] = {
            "status": args.status,
            "source_count": args.source_count,
            "updated_at": now(),
            "note": args.note.strip(),
        }
        if args.status in {"pending", "collecting", "revisit_later"}:
            entry["next_reminder_at"] = datetime.fromtimestamp(
                time.time() + args.remind_after_days * 86400, timezone.utc
            ).replace(microsecond=0).isoformat()
        state["voice_intake"] = entry
        receipt(state, "record-voice-intake", [], [], detail=f"status={args.status}; sources={args.source_count}")
        save(root, state)
    print(json.dumps(voice_intake_status(state), indent=2))
    return 0


def cmd_record_manifest(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); report = root / safe_rel(args.report)
    if not report.exists(): raise SystemExit(f"Manifest audit report not found: {report}")
    value = json.loads(report.read_text(encoding="utf-8"))
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root); require_active(state)
        state["manifest_audit"] = {"status": value.get("status"), "at": now(), "report": report.relative_to(root).as_posix()}
        receipt(state, "record-manifest-audit", [report.relative_to(root).as_posix()], [])
        save(root, state)
    print(value.get("status", "unknown"))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); artifact_rel = safe_rel(args.artifact); artifact = root / artifact_rel
    if not artifact.exists(): raise SystemExit(f"Draft not found: {artifact_rel}")
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root); require_active(state)
        missing = decision_gate(state, args.document)
        if missing: raise SystemExit("Review blocked: " + "; ".join(missing))
        digest = sha256(artifact); prior = current_reviews(state, artifact_rel)
        if args.document == "cover-letter" and any(item.get("loop") == args.loop for item in prior):
            raise SystemExit(f"Cover-letter loop {args.loop} already recorded for this artifact.")
        if args.document == "interview-prep" and args.loop not in {1, 2}:
            raise SystemExit("Interview-prep review loops must be 1 or 2.")
        if args.document == "interview-prep" and any(item.get("loop") == args.loop and item.get("artifact_sha256") == digest for item in prior):
            raise SystemExit(f"Interview-prep loop {args.loop} already recorded for the current artifact.")
        if args.document == "writing" and args.loop not in {1, 2, 3}:
            raise SystemExit("Writing review loops must be 1, 2, or 3.")
        if args.document == "cover-letter" and prior and prior[-1].get("artifact_sha256") == digest:
            raise SystemExit("Cover-letter review requires a revised draft with a distinct hash.")
        result_path = root / safe_rel(args.result)
        if not result_path.exists(): raise SystemExit(f"Checker result not found: {result_path}")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        state.setdefault("review_records", []).append({"at": now(), "document": args.document, "loop": args.loop, "artifact": artifact_rel, "artifact_sha256": digest, "result": result, "result_path": result_path.relative_to(root).as_posix()})
        receipt(state, f"review-{args.document}", [artifact_rel, result_path.relative_to(root).as_posix()], [])
        save(root, state)
    print("Review recorded")
    return 0


def cmd_record_ats(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    artifact_rel = safe_rel(args.artifact)
    result_rel = safe_rel(args.result)
    artifact = root / artifact_rel
    result_path = root / result_rel
    if not artifact.exists():
        raise SystemExit(f"CV/resume artifact not found: {artifact_rel}")
    if not result_path.exists():
        raise SystemExit(f"ATS result not found: {result_rel}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    score = result.get("score")
    if not isinstance(score, int):
        raise SystemExit("ATS result is invalid: integer score is required.")
    if not isinstance(result.get("matched_keywords"), list) or not isinstance(result.get("missing_keywords"), list):
        raise SystemExit("ATS result is invalid: matched_keywords and missing_keywords are required.")
    if result.get("privacy", {}).get("stored") is not False:
        raise SystemExit("ATS result is invalid: privacy.stored must be false.")
    jd_rel = safe_rel(args.job_description) if args.job_description else None
    jd_digest = None
    if jd_rel:
        jd_path = root / jd_rel
        if not jd_path.exists():
            raise SystemExit(f"Job description file not found: {jd_rel}")
        jd_digest = sha256(jd_path)
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root)
        require_active(state)
        record = {
            "at": now(),
            "document": "cv",
            "artifact": artifact_rel,
            "artifact_sha256": sha256(artifact),
            "job_description": jd_rel,
            "job_description_sha256": jd_digest,
            "score": score,
            "targetScore": result.get("targetScore", 70),
            "readiness_label": result.get("readiness_label"),
            "result_path": result_rel,
            "must_ask_user": result.get("must_ask_user", []),
        }
        state.setdefault("ats_records", []).append(record)
        state["ats_records"] = state["ats_records"][-100:]
        receipt(state, "record-ats-cv", [artifact_rel, result_rel] + ([jd_rel] if jd_rel else []), [], detail=f"score={score}")
        save(root, state)
    print(json.dumps({"status": "recorded", "artifact": artifact_rel, "score": score}, indent=2))
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); artifact_rel = safe_rel(args.artifact); artifact = root / artifact_rel
    if not artifact.exists(): raise SystemExit(f"Artifact not found: {artifact_rel}")
    _, _, lock_path, _ = paths(root)
    with state_lock(lock_path):
        state = load(root); active = require_active(state); missing = decision_gate(state, args.document)
        reviews = current_reviews(state, artifact_rel); digest = sha256(artifact)
        matching = [item for item in reviews if item.get("artifact_sha256") == digest]
        if args.document == "cv":
            required_reviews = matching
            if len(required_reviews) < 1: missing.append("1 current CV review record required")
            ats_records = [item for item in current_ats_records(state, artifact_rel) if item.get("artifact_sha256") == digest]
            if not ats_records:
                missing.append("current ATS CV/JD report required; run MCP ATS check and record-ats-cv after the latest CV edit")
        elif args.document == "cover-letter":
            by_loop = {item.get("loop"): item for item in reviews if item.get("loop") in {1, 2, 3}}
            required_reviews = [by_loop[loop] for loop in (1, 2, 3) if loop in by_loop]
            if len(required_reviews) != 3: missing.append("cover-letter loops 1, 2, and 3 are required")
            elif by_loop[3].get("artifact_sha256") != digest: missing.append("cover-letter loop 3 is stale for the current draft")
        elif args.document == "interview-prep":
            by_loop = {item.get("loop"): item for item in matching if item.get("loop") in {1, 2}}
            required_reviews = [by_loop[loop] for loop in (1, 2) if loop in by_loop]
            if len(required_reviews) != 2: missing.append("interview-prep loops 1 and 2 are required")
        elif args.document == "writing":
            required_loop_count = max(1, min(3, args.required_loops))
            by_loop = {item.get("loop"): item for item in matching if item.get("loop") in {1, 2, 3}}
            required_reviews = [by_loop[loop] for loop in range(1, required_loop_count + 1) if loop in by_loop]
            if len(required_reviews) != required_loop_count: missing.append(f"writing loops 1 through {required_loop_count} are required")
        else:
            raise SystemExit(f"Unsupported document type: {args.document}")
        for item in required_reviews:
            if item.get("result", {}).get("riskLevel") not in {None, "low"}:
                missing.append(f"unresolved {item.get('document')} review risk in loop {item.get('loop')}")
        if missing:
            print(json.dumps({"status": "NOT READY", "artifact": artifact_rel, "missing": missing}, indent=2)); return 1
        receipt_dir = root / STATE_DIR / "receipts"; receipt_dir.mkdir(parents=True, exist_ok=True)
        payload = {"receipt_schema": 1, "status": "ready", "artifact": artifact_rel, "artifact_sha256": digest, "document": args.document, "task_id": active["task_id"], "created_at": now(), "reviews": required_reviews, "ats_records": [item for item in current_ats_records(state, artifact_rel) if item.get("artifact_sha256") == digest] if args.document == "cv" else [], "decisions": state.get("decisions", {}), "manifest_audit": state.get("manifest_audit")}
        target = receipt_dir / f"{args.document}-{digest[:12]}.json"; target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        receipt(state, f"finalize-{args.document}", [artifact_rel], [target.relative_to(root).as_posix()])
        save(root, state)
    print(target.relative_to(root))
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); legacy = Path(args.legacy_root).resolve()
    if not legacy.is_dir(): raise SystemExit("Legacy root must be an existing directory.")
    started = time.monotonic(); files = []
    for current, dirs, names in os.walk(legacy):
        dirs[:] = [item for item in dirs if item not in {".git", "node_modules", "__pycache__"}]
        for name in names:
            path = Path(current) / name
            files.append({"path": path.relative_to(legacy).as_posix(), "size": path.stat().st_size})
    duration = round(time.monotonic() - started, 3)
    large = sorted((item for item in files if item["size"] > 5 * 1024 * 1024), key=lambda item: item["size"], reverse=True)
    duplicates: dict[str, int] = {}
    for item in files: duplicates[Path(item["path"]).name] = duplicates.get(Path(item["path"]).name, 0) + 1
    plan = {"status": "approval_required", "operations": [{"action": "index_only", "source": str(legacy), "destination": ".mcp/workspace-manifest.json", "risk": "low", "benefit": "Avoid broad repeated discovery scans."}], "protected": list(PROTECTED_PREFIXES), "deletion": "never automatic"}
    report = {"status": "diagnosed", "legacy_root": str(legacy), "observed": {"file_count": len(files), "inventory_seconds": duration, "large_files": large[:20], "duplicate_names": sorted(name for name, count in duplicates.items() if count > 1)[:50]}, "inference": "Folder structure is not treated as the cause until baseline stage timings identify it.", "next": "Review the local migration plan before any files are changed."}
    destination = root / "applications" / args.job / "audit"; destination.mkdir(parents=True, exist_ok=True)
    (destination / "workspace-diagnosis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (destination / "migration-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); state = load(root)
    snapshot = bool(state.get("snapshot")); active = bool(state.get("active"))
    status = {"snapshot_present": snapshot, "active_task": active, "photo_decision": state.get("decisions", {}).get("photo"), "signature_decision": state.get("decisions", {}).get("signature"), "enclosure_decision": state.get("decisions", {}).get("enclosures"), "voice_intake": voice_intake_status(state), "workspace_audit": (state.get("manifest_audit") or {}).get("status"), "review_records": len(state.get("review_records", [])), "ats_records": len(state.get("ats_records", [])), "release_receipts": len(list((root / STATE_DIR / "receipts").glob("*.json"))) if (root / STATE_DIR / "receipts").exists() else 0}
    print(json.dumps(status, indent=2))
    return 0 if snapshot else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Local Application SOP hard gate")
    value.add_argument("--root", default=".")
    commands = value.add_subparsers(dest="command", required=True)
    boot = commands.add_parser("boot"); boot.add_argument("--strict", action="store_true"); boot.set_defaults(func=cmd_boot)
    start = commands.add_parser("start"); start.add_argument("--task-id", required=True); start.add_argument("--job", required=True); start.add_argument("--goal", required=True); start.set_defaults(func=cmd_start)
    decision = commands.add_parser("record-decision"); decision.add_argument("--name", choices=["photo", "signature", "voice", "enclosures"], required=True); decision.add_argument("--value", required=True); decision.set_defaults(func=cmd_decision)
    voice_status = commands.add_parser("voice-intake-status"); voice_status.set_defaults(func=cmd_voice_intake_status)
    voice_record = commands.add_parser("record-voice-intake"); voice_record.add_argument("--status", choices=["pending", "collecting", "revisit_later", "enough", "declined"], required=True); voice_record.add_argument("--source-count", type=int, default=0); voice_record.add_argument("--remind-after-days", type=int, default=45); voice_record.add_argument("--note", default=""); voice_record.set_defaults(func=cmd_record_voice_intake)
    manifest = commands.add_parser("record-manifest-audit"); manifest.add_argument("--report", required=True); manifest.set_defaults(func=cmd_record_manifest)
    ats = commands.add_parser("record-ats-cv"); ats.add_argument("--artifact", required=True); ats.add_argument("--result", required=True); ats.add_argument("--job-description"); ats.set_defaults(func=cmd_record_ats)
    for name, document in (("review-cv", "cv"), ("review-cover", "cover-letter"), ("review-interview-prep", "interview-prep"), ("review-writing", "writing")):
        review = commands.add_parser(name); review.add_argument("--artifact", required=True); review.add_argument("--result", required=True); review.add_argument("--loop", type=int, default=1); review.set_defaults(func=cmd_review, document=document)
    for name, document in (("finalize-cv", "cv"), ("finalize-cover-letter", "cover-letter"), ("finalize-interview-prep", "interview-prep"), ("finalize-writing", "writing")):
        final = commands.add_parser(name); final.add_argument("--artifact", required=True); final.add_argument("--required-loops", type=int, default=1); final.set_defaults(func=cmd_finalize, document=document)
    diagnose = commands.add_parser("diagnose-workspace"); diagnose.add_argument("--legacy-root", required=True); diagnose.add_argument("--job", required=True); diagnose.set_defaults(func=cmd_diagnose)
    health = commands.add_parser("health"); health.set_defaults(func=cmd_health)
    return value


if __name__ == "__main__":
    args = parser().parse_args()
    raise SystemExit(args.func(args))
