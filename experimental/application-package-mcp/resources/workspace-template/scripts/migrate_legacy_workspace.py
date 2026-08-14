#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


REQUIRED_DIRS = [
    "profile",
    "memory",
    "memory/legacy",
    "scripts",
    "candidate",
    "jobs",
    "outputs",
]

STARTER_FILES = {
    "profile/master_profile.json": "profile/master_profile.example.json",
    "profile/evidence_library.json": "profile/evidence_library.example.json",
}


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def copy_if_missing(source: Path, target: Path) -> bool:
    if not source.exists() or target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def append_note(path: Path, note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    if note not in existing:
        path.write_text((existing.rstrip() + "\n\n" + note.strip() + "\n").lstrip(), encoding="utf-8")


def migrate_candidate_profile(root: Path, report: list[str]) -> None:
    old_profile = root / "candidate" / "profile.json"
    new_profile = root / "profile" / "master_profile.json"
    if not old_profile.exists():
        return

    old_data = read_json(old_profile)
    looks_like_master = all(key in old_data for key in ["identity", "education", "skills", "constraints"])
    if looks_like_master and not new_profile.exists():
        shutil.copy2(old_profile, new_profile)
        report.append("Copied candidate/profile.json to profile/master_profile.json.")
        return

    legacy_target = root / "memory" / "legacy" / "candidate" / "profile.json"
    if copy_if_missing(old_profile, legacy_target):
        report.append("Preserved old candidate/profile.json under memory/legacy/candidate/profile.json.")

    append_note(
        root / "memory" / "skill_memory.md",
        "- Legacy candidate profile was preserved under `memory/legacy/candidate/profile.json`; review it before copying facts into `profile/master_profile.json`.",
    )


def migrate_text_file(root: Path, source_rel: str, target_rel: str, report: list[str]) -> None:
    source = root / source_rel
    target = root / target_rel
    if copy_if_missing(source, target):
        report.append(f"Copied {source_rel} to {target_rel}.")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    report: list[str] = []

    for rel_dir in REQUIRED_DIRS:
        path = root / rel_dir
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            report.append(f"Created {rel_dir}/.")

    for target_rel, source_rel in STARTER_FILES.items():
        copied = copy_if_missing(root / source_rel, root / target_rel)
        if copied:
            report.append(f"Created {target_rel} from {source_rel}.")

    migrate_candidate_profile(root, report)
    migrate_text_file(root, "candidate/evidence.md", "memory/legacy/candidate/evidence.md", report)
    migrate_text_file(root, "candidate/tone.md", "memory/legacy/candidate/tone.md", report)
    migrate_text_file(root, "candidate/source-analysis.md", "memory/legacy/candidate/source-analysis.md", report)
    migrate_text_file(root, "candidate/benchmark-results.md", "memory/benchmark-results.md", report)

    writing_samples = root / "candidate" / "writing-samples"
    if writing_samples.exists():
        target = root / "memory" / "legacy" / "candidate" / "writing-samples"
        if not target.exists():
            shutil.copytree(writing_samples, target)
            report.append("Preserved candidate/writing-samples under memory/legacy/candidate/writing-samples.")

    append_note(
        root / "CHANGELOG.md",
        f"## {datetime.utcnow().date()} - Legacy Workspace Migration\n\n- Added digital-twin structure around the existing student workspace.\n- Preserved old candidate data under `memory/legacy/` where needed.\n- No files were uploaded to the MCP server.\n",
    )

    append_note(
        root / "memory" / "decisions.md",
        "- Keep old `candidate/`, `jobs/`, and `outputs/` folders during migration. Treat `profile/` and `memory/` as source of truth after student review.",
    )

    print("Migration complete.")
    if report:
        for item in report:
            print(f"- {item}")
    else:
        print("- No changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
