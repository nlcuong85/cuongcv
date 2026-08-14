#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


FILES = [
    "AGENTS.md",
    "CHANGELOG.md",
    "MIGRATION.md",
    "COPILOT.md",
    "CLAUDE.md",
    "GEMINI.md",
    "copilot_quick_context.md",
    "profile/master_profile.json",
    "profile/evidence_library.json",
    "profile/student-profile-context.md",
    "profile/writing_mode_framework.md",
    "profile/voice_dna.md",
    "profile/mode-bridge.md",
    "profile/academic-voice-bridge.md",
    "profile/academic-writing-playbook.md",
    "profile/academic-human-writing-dna.md",
    "profile/academic-ai-checker-guardrails.md",
    "profile/claim_boundaries.md",
    "memory/skill_memory.md",
    "memory/decisions.md",
    "memory/interaction_tracker.md",
    "memory/benchmark-results.md",
    "memory/source_corpus.md",
    "memory/story-index.md",
    "memory/story-bank.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a compact context pack for a digital twin folder.")
    parser.add_argument("root", nargs="?", default=".", help="Digital twin folder root")
    parser.add_argument("--out", default="context_pack.md", help="Output markdown path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = root / args.out
    parts = ["# Context Pack", ""]

    for rel_path in FILES:
        path = root / rel_path
        if not path.exists():
            parts.append(f"## {rel_path}")
            parts.append("")
            parts.append("_Missing._")
            parts.append("")
            continue

        parts.append(f"## {rel_path}")
        parts.append("")
        suffix = path.suffix.lower()
        fence = "json" if suffix == ".json" else "markdown"
        parts.append(f"```{fence}")
        parts.append(path.read_text(encoding="utf-8", errors="ignore").strip())
        parts.append("```")
        parts.append("")

    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
