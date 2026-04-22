#!/usr/bin/env python3

from __future__ import annotations

import json
import sys

from common import APPLICATION_ROOT, CONFIG_ROOT, INTAKE_ROOT, OUTPUT_ROOT, REPO_ROOT, current_corpus


def main() -> int:
    issues: list[str] = []
    warnings: list[str] = []

    required_paths = [
        REPO_ROOT / "AGENTS.md",
        APPLICATION_ROOT / "AGENTS.md",
        APPLICATION_ROOT / "data" / "master_profile.json",
        APPLICATION_ROOT / "data" / "summary_versions.json",
        CONFIG_ROOT / "profile.yml",
        CONFIG_ROOT / "portals.yml",
    ]
    for path in required_paths:
        if not path.exists():
            issues.append(f"Missing required path: {path}")

    intake_count = len(list(INTAKE_ROOT.glob("*.json")))
    output_count = len(list(OUTPUT_ROOT.glob("*/manifest.json")))
    corpus = current_corpus()
    matched_outputs = sum(1 for item in corpus if item.get("has_output"))

    if intake_count == 0:
        issues.append("No intake files found in application-system/intakes")
    if output_count == 0:
        warnings.append("No manifest.json files found in application-system/outputs")
    if matched_outputs < max(1, intake_count // 2):
        warnings.append(
            "Less than half of the intake corpus matched to output manifests by company + job title"
        )

    summary = {
        "repo_root": str(REPO_ROOT),
        "application_root": str(APPLICATION_ROOT),
        "intake_count": intake_count,
        "output_manifest_count": output_count,
        "matched_output_count": matched_outputs,
        "issues": issues,
        "warnings": warnings,
    }

    print("=== job-search-next sync check ===")
    print(json.dumps(summary, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
