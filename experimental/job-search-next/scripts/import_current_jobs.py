#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter

from common import DATA_ROOT, current_corpus, write_json, write_text


def main() -> int:
    items = current_corpus()
    role_counter = Counter(item.get("expected_primary_role", "") or "unknown" for item in items)
    output_counter = Counter("with_output" if item.get("has_output") else "intake_only" for item in items)

    payload = {
        "summary": {
            "total_items": len(items),
            "with_output": output_counter["with_output"],
            "intake_only": output_counter["intake_only"],
            "role_distribution": dict(sorted(role_counter.items())),
        },
        "items": items,
    }
    write_json(DATA_ROOT / "current_corpus.json", payload)

    lines = [
        "# Current Corpus Summary",
        "",
        f"- Total items: {len(items)}",
        f"- With output manifests: {output_counter['with_output']}",
        f"- Intake only: {output_counter['intake_only']}",
        "",
        "## Expected role distribution",
        "",
    ]
    for role, count in sorted(role_counter.items()):
        lines.append(f"- {role}: {count}")

    write_text(DATA_ROOT / "current_corpus_summary.md", "\n".join(lines) + "\n")

    print(f"Imported {len(items)} current jobs into {DATA_ROOT / 'current_corpus.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
