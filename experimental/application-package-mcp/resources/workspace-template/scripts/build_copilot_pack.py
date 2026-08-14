#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


FILES = [
    "AGENTS.md",
    "COPILOT.md",
    "copilot_quick_context.md",
    "profile/student-profile-context.md",
    "profile/master_profile.json",
    "profile/evidence_library.json",
    "profile/writing_mode_framework.md",
    "profile/voice_dna.md",
    "profile/claim_boundaries.md",
    "profile/mode-bridge.md",
    "profile/academic-voice-bridge.md",
    "profile/academic-writing-playbook.md",
    "profile/academic-human-writing-dna.md",
    "memory/skill_memory.md",
    "memory/benchmark-results.md",
    "memory/story-index.md",
    "memory/story-bank.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Copilot-optimized compact context pack.")
    parser.add_argument("root", nargs="?", default=".", help="Student digital-twin root")
    parser.add_argument("--out", default="copilot_context.md", help="Output markdown path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = root / args.out
    parts = [
        "# Copilot Context Pack",
        "",
        "This compact pack is optimized for local AI agents with limited context.",
        "Use `context_pack.md` only when this file is not enough.",
        "",
    ]

    for rel_path in FILES:
        path = root / rel_path
        parts.append(f"## {rel_path}")
        parts.append("")
        if not path.exists():
            parts.append("_Missing._")
            parts.append("")
            continue
        parts.append(path.read_text(encoding="utf-8", errors="ignore").strip())
        parts.append("")

    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

