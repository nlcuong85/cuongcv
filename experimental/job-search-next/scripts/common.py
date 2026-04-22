from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


SCRIPT_ROOT = Path(__file__).resolve().parent
PROTOTYPE_ROOT = SCRIPT_ROOT.parent
EXPERIMENTAL_ROOT = PROTOTYPE_ROOT.parent
REPO_ROOT = EXPERIMENTAL_ROOT.parent
APPLICATION_ROOT = REPO_ROOT / "application-system"
INTAKE_ROOT = APPLICATION_ROOT / "intakes"
OUTPUT_ROOT = APPLICATION_ROOT / "outputs"
DATA_ROOT = PROTOTYPE_ROOT / "data"
CONFIG_ROOT = PROTOTYPE_ROOT / "config"
PROMOTIONS_ROOT = PROTOTYPE_ROOT / "promotions"
RAW_LEADS_PATH = DATA_ROOT / "raw_leads.jsonl"
FRANKLEE_ROOT = Path("/Users/pmlecuong/Documents/CuongProjects/OpenClaw-franklee")
FRANKLEE_LOCAL_RUNNER = FRANKLEE_ROOT / "scripts" / "run_local_franklee_job_search.py"
FRANKLEE_RECOVERY_DOC = FRANKLEE_ROOT / "docs" / "franklee-recovery.md"

ROLE_COMPATIBILITY_GROUPS = [
    {"business_analyst", "requirements_process", "workflow_operations_analyst"},
    {"product_manager", "product_owner", "pmo_delivery_support"},
    {"ai_product_ops", "process_automation"},
    {"implementation_enablement", "pmo_delivery_support", "workflow_operations_analyst"},
]


def ensure_dirs() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    PROMOTIONS_ROOT.mkdir(parents=True, exist_ok=True)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not load as a mapping")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def slugify(text: str) -> str:
    text = normalize_spaces(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def normalize_key(*parts: str) -> str:
    return "::".join(slugify(part) for part in parts if normalize_spaces(part))


def source_domain(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def replace_tabs(value: Any) -> str:
    text = normalize_spaces("" if value is None else str(value))
    return text.replace("\t", " ")


def current_corpus() -> list[dict[str, Any]]:
    manifest_by_key: dict[str, dict[str, Any]] = {}
    notes_by_dir: dict[Path, Path] = {}

    for manifest_path in sorted(OUTPUT_ROOT.glob("*/manifest.json")):
        manifest = load_json(manifest_path)
        company = manifest.get("company_name", "")
        title = manifest.get("job_title", "")
        key = normalize_key(company, title)
        manifest_by_key[key] = {
            "path": manifest_path,
            "data": manifest,
            "output_dir": manifest_path.parent,
        }
        notes_path = manifest_path.parent / "notes.md"
        if notes_path.exists():
            notes_by_dir[manifest_path.parent] = notes_path

    items: list[dict[str, Any]] = []
    for intake_path in sorted(INTAKE_ROOT.glob("*.json")):
        intake = load_json(intake_path)
        company = intake.get("company_name", "")
        title = intake.get("job_title", "")
        key = normalize_key(company, title)
        manifest_entry = manifest_by_key.get(key)
        manifest = manifest_entry["data"] if manifest_entry else {}
        output_dir = manifest_entry["output_dir"] if manifest_entry else None
        notes_path = notes_by_dir.get(output_dir) if output_dir else None
        expected_role = manifest.get("primary_role") or intake.get("primary_role") or ""
        expected_summary = manifest.get("summary_version") or intake.get("summary_version") or ""
        items.append(
            {
                "lead_id": slugify(f"{company}-{title}") or intake_path.stem,
                "company_name": company,
                "job_title": title,
                "job_url": intake.get("job_url", ""),
                "company_location": intake.get("company_location", ""),
                "language": intake.get("language", ""),
                "job_description": intake.get("job_description", ""),
                "requirements": intake.get("requirements", []),
                "target_roles": intake.get("target_roles", []),
                "primary_role": intake.get("primary_role", ""),
                "summary_version": intake.get("summary_version", ""),
                "contact_name": intake.get("contact_name", ""),
                "contact_lookup_status": intake.get("contact_lookup_status", ""),
                "intake_path": str(intake_path.relative_to(REPO_ROOT)),
                "output_dir": str(output_dir.relative_to(REPO_ROOT)) if output_dir else "",
                "manifest_path": str(manifest_entry["path"].relative_to(REPO_ROOT)) if manifest_entry else "",
                "notes_path": str(notes_path.relative_to(REPO_ROOT)) if notes_path else "",
                "expected_primary_role": expected_role,
                "expected_summary_version": expected_summary,
                "has_output": bool(output_dir),
            }
        )

    return items


def load_current_corpus_from_disk() -> list[dict[str, Any]]:
    corpus_path = DATA_ROOT / "current_corpus.json"
    if corpus_path.exists():
        payload = load_json(corpus_path)
        items = payload.get("items", [])
        if isinstance(items, list):
            return items
    return current_corpus()


def role_match_status(expected_role: str, predicted_role: str) -> str:
    if not expected_role or not predicted_role:
        return "unknown"
    if expected_role == predicted_role:
        return "exact"
    for group in ROLE_COMPATIBILITY_GROUPS:
        if expected_role in group and predicted_role in group:
            return "compatible"
    return "no"


def raw_lead_record(payload: dict[str, Any]) -> dict[str, Any]:
    company = normalize_spaces(payload.get("company_name", ""))
    title = normalize_spaces(payload.get("job_title", ""))
    lead_id = payload.get("lead_id") or slugify(f"{company}-{title}")
    return {
        "lead_id": lead_id,
        "company_name": company,
        "job_title": title,
        "job_url": normalize_spaces(payload.get("job_url", "")),
        "company_location": normalize_spaces(payload.get("company_location", "")),
        "language": normalize_spaces(payload.get("language", "english")),
        "job_description": normalize_spaces(payload.get("job_description", "")),
        "requirements": payload.get("requirements", []) or [],
        "target_roles": payload.get("target_roles", []) or [],
        "primary_role": normalize_spaces(payload.get("primary_role", "")),
        "summary_version": normalize_spaces(payload.get("summary_version", "")),
        "contact_name": normalize_spaces(payload.get("contact_name", "")),
        "contact_lookup_status": normalize_spaces(payload.get("contact_lookup_status", "")),
        "intake_path": "",
        "output_dir": "",
        "manifest_path": "",
        "notes_path": "",
        "expected_primary_role": normalize_spaces(payload.get("expected_primary_role", "")),
        "expected_summary_version": normalize_spaces(payload.get("expected_summary_version", "")),
        "has_output": False,
        "source": normalize_spaces(payload.get("source", "manual")),
        "source_profile": normalize_spaces(payload.get("source_profile", "")),
        "source_score": payload.get("source_score", 0) or 0,
        "source_posted_date": normalize_spaces(payload.get("source_posted_date", "")),
        "source_work_model": normalize_spaces(payload.get("source_work_model", "")),
        "source_language_note": normalize_spaces(payload.get("source_language_note", "")),
        "source_why_match": normalize_spaces(payload.get("source_why_match", "")),
        "source_domain": normalize_spaces(payload.get("source_domain", "")),
    }


def load_raw_leads() -> list[dict[str, Any]]:
    if not RAW_LEADS_PATH.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in RAW_LEADS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            items.append(raw_lead_record(payload))
    return items


def raw_lead_identity(payload: dict[str, Any]) -> str:
    record = raw_lead_record(payload)
    job_url = record.get("job_url", "")
    if job_url:
        return f"url::{normalize_spaces(job_url).lower()}"
    lead_id = record.get("lead_id", "")
    return f"id::{lead_id}"


def write_raw_leads(items: list[dict[str, Any]]) -> None:
    ensure_dirs()
    normalized = [raw_lead_record(item) for item in items]
    lines = [json.dumps(item, ensure_ascii=True) for item in normalized]
    RAW_LEADS_PATH.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


def append_raw_lead(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    record = raw_lead_record(payload)
    with RAW_LEADS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return record


def upsert_raw_leads(payloads: list[dict[str, Any]]) -> dict[str, int]:
    current = load_raw_leads()
    by_identity: dict[str, dict[str, Any]] = {raw_lead_identity(item): raw_lead_record(item) for item in current}
    added = 0
    updated = 0
    for payload in payloads:
        record = raw_lead_record(payload)
        identity = raw_lead_identity(record)
        if identity in by_identity:
            updated += 1
        else:
            added += 1
        by_identity[identity] = record
    ordered = sorted(by_identity.values(), key=lambda item: (item.get("source", ""), item.get("company_name", ""), item.get("job_title", "")))
    write_raw_leads(ordered)
    return {"added": added, "updated": updated, "total": len(ordered)}


def all_leads(include_current: bool = True, include_raw: bool = True) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    if include_current:
        for item in load_current_corpus_from_disk():
            identity = raw_lead_identity(item)
            if identity and identity not in seen:
                seen.add(identity)
                items.append(item)
    if include_raw:
        for item in load_raw_leads():
            identity = raw_lead_identity(item)
            if identity and identity not in seen:
                seen.add(identity)
                items.append(item)
    return items
