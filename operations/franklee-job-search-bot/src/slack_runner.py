#!/usr/bin/env python3
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


CHANNEL = "C0AN1ENTLMQ"
WORKDIR = Path("/root/clawdFrankLee")
STATE_DIR = Path("/root/.openclaw")
OUTPUT_DIR = STATE_DIR / "manual-recovery"
CONFIG_PATH = STATE_DIR / "openclaw.json"
VALIDATOR = WORKDIR / "dist" / "job_search_prefilter.py"
AI_RANKER = WORKDIR / "dist" / "ai_ranker.py"
CHUNK_LIMIT = 2500


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_token():
    config = json.loads(CONFIG_PATH.read_text())
    return config["channels"]["slack"]["botToken"]


def write_manifest(path, payload):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def slack_api(method, token, payload, *, attempts=5):
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(f"https://slack.com/api/{method}", data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("ok"):
                return data
            error = data.get("error") or "slack_api_error"
            last_error = RuntimeError(f"{method} failed: {error}")
            if error == "ratelimited":
                time.sleep(min(60, 2 * attempt))
            elif error in {"internal_error", "fatal_error", "request_timeout"}:
                time.sleep(min(30, 2**attempt))
            else:
                raise last_error
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else min(60, 2**attempt)
                time.sleep(delay)
            elif 500 <= exc.code < 600:
                time.sleep(min(30, 2**attempt))
            else:
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(min(30, 2**attempt))
    raise RuntimeError(f"{method} failed after {attempts} attempts: {last_error}")


def chunks_by_line(text, limit=CHUNK_LIMIT):
    chunks = []
    current = ""
    for line in text.splitlines():
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) > limit and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def to_slack_mrkdwn(text):
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            lines.append(f"*{line[3:]}*")
        elif line.startswith("### "):
            lines.append(f"*{line[4:]}*")
        elif line.startswith("#### "):
            lines.append(f"*{line[5:]}*")
        else:
            lines.append(line.replace("**", "*"))
    return "\n".join(lines)


def validate_output(text):
    required = [
        "Daily Germany Job Search",
        "Rules applied:",
        "Section 1",
        "Section 2",
        "Analytics:",
        "Recent-posted cache:",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"validator output missing expected sections: {', '.join(missing)}")


def load_validator_module():
    spec = importlib.util.spec_from_file_location("franklee_job_search_prefilter", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("validator module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ai_mode():
    mode = os.environ.get("FRANKLEE_AI_RANKING_MODE", "shadow").strip().lower()
    return mode if mode in {"off", "shadow", "rank"} else "shadow"


def run_ai_ranker(payload):
    if not AI_RANKER.is_file():
        return {"status": "failed", "model": "openai/gpt-6-luna", "thinking": "medium", "error": "ranker_unavailable"}
    try:
        result = subprocess.run(
            ["python3", str(AI_RANKER), "--timeout", "130"],
            cwd=str(WORKDIR),
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=145,
            check=False,
        )
        if result.returncode != 0:
            return {"status": "failed", "model": "openai/gpt-6-luna", "thinking": "medium", "error": "ranker_process_failed"}
        response = json.loads(result.stdout)
        if not isinstance(response, dict) or response.get("status") not in {"ok", "failed", "skipped_empty"}:
            return {"status": "failed", "model": "openai/gpt-6-luna", "thinking": "medium", "error": "ranker_response_invalid"}
        return response
    except subprocess.TimeoutExpired:
        return {"status": "failed", "model": "openai/gpt-6-luna", "thinking": "medium", "error": "ranker_timeout"}
    except Exception:
        return {"status": "failed", "model": "openai/gpt-6-luna", "thinking": "medium", "error": "ranker_runtime_error"}


def apply_ai_order(payload, ranking):
    by_id = {entry["candidate_id"]: entry for entry in ranking.get("rankings", [])}
    for section, field, limit in (("student", "student_results", 7), ("fulltime", "fulltime_results", 9)):
        items = payload.get(field) or []
        for item in items:
            item["_ai_priority"] = 999
        for item in items[:limit]:
            identity = str(item.get("normalized_url") or item.get("url") or "").strip().lower()
            candidate_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            entry = by_id.get(candidate_id)
            if entry and entry.get("section") == section:
                item["_ai_priority"] = int(entry["priority"])


def format_report(payload, validator, mode, ai_result):
    if mode == "rank" and ai_result.get("status") == "ok":
        apply_ai_order(payload, ai_result)
    body = validator.render_combined_1500(
        student_results=payload.get("student_results") or [],
        fulltime_results=payload.get("fulltime_results") or [],
        max_age_days=20,
        analytics=payload,
    )
    if mode == "rank" and ai_result.get("status") == "ok":
        body = body.replace(
            "Language note: English-first roles are listed first; German-required or German-unclear roles remain in their matching section for awareness.",
            "Language note: English-first roles are listed first; German-required or German-unclear roles remain in their matching section for awareness.\nAI note: model-assisted ordering only within the Python-validated shortlist; Python eligibility gates are unchanged.",
        )
    return body


def write_private_json(path, payload):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        tmp.replace(path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def post_result(token, title, body):
    chunks = chunks_by_line(to_slack_mrkdwn(body))
    message_ts = []
    for idx, chunk in enumerate(chunks, 1):
        if idx > 1:
            time.sleep(1.2)
        prefix = f"*{title}*" if len(chunks) == 1 else f"*{title} - part {idx}/{len(chunks)}*"
        message = slack_api(
            "chat.postMessage",
            token,
            {
                "channel": CHANNEL,
                "text": f"{prefix}\n{chunk}",
                "mrkdwn": True,
                "unfurl_links": False,
                "unfurl_media": False,
            },
        )
        message_ts.append(message["ts"])
    return message_ts


def post_failure(token, today, output_path, message):
    text = (
        f"*Daily Germany Job Search failed ({today})*\n"
        f"{message}\n"
        f"Output saved at `{output_path}`."
    )
    data = slack_api(
        "chat.postMessage",
        token,
        {
            "channel": CHANNEL,
            "text": text,
            "mrkdwn": True,
            "unfurl_links": False,
            "unfurl_media": False,
        },
    )
    return data["ts"]


def main():
    today = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"job-search-{today}-1500.md"
    manifest_path = OUTPUT_DIR / f"job-search-{today}-1500.delivery.json"

    if manifest_path.exists() and os.environ.get("FRANKLEE_FORCE_REPOST") != "1":
        try:
            existing = json.loads(manifest_path.read_text())
            if existing.get("status") == "posted":
                print(json.dumps({"ok": True, "skipped": "already_posted", "manifest": str(manifest_path)}))
                return 0
        except Exception:
            pass

    token = load_token()
    started_at = now_iso()
    cmd = [
        "python3",
        str(VALIDATOR),
        "--combined-1500",
        "--max-age-days",
        "20",
        "--debug",
    ]
    manifest = {
        "date": today,
        "status": "running",
        "started_at": started_at,
        "command": cmd,
        "output": str(output_path),
        "channel": CHANNEL,
    }
    write_manifest(manifest_path, manifest)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(WORKDIR),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
            check=False,
        )
        manifest.update(
            {
                "validator_returncode": result.returncode,
                "validator_output_bytes": len(result.stdout.encode("utf-8")),
                "validator_finished_at": now_iso(),
            }
        )
        if result.returncode != 0:
            output_path.write_text("Job validator failed; details remain in systemd logs.\n", encoding="utf-8")
            failure_ts = post_failure(token, today, output_path, f"Validator exited with code {result.returncode}.")
            manifest.update({"status": "validator_failed", "failure_ts": failure_ts, "finished_at": now_iso()})
            write_manifest(manifest_path, manifest)
            print(json.dumps({"ok": False, "output": str(output_path), "returncode": result.returncode, "failure_ts": failure_ts}))
            return result.returncode

        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise RuntimeError("validator returned an invalid JSON payload")
        validator = load_validator_module()
        mode = ai_mode()
        ai_result = {"status": "disabled", "mode": mode}
        if mode != "off":
            ai_result = run_ai_ranker(payload)
            ai_result["mode"] = mode
            ai_result["recorded_at"] = now_iso()
            ai_sidecar_suffix = "ai-shadow" if mode == "shadow" else "ai-ranking"
            ai_sidecar_path = OUTPUT_DIR / f"job-search-{today}-1500.{ai_sidecar_suffix}.json"
            write_private_json(ai_sidecar_path, ai_result)
            manifest["ai_ranking"] = {
                "status": ai_result.get("status"),
                "mode": mode,
                "model": ai_result.get("model"),
                "thinking": ai_result.get("thinking"),
                "candidate_count": ai_result.get("candidate_count", 0),
                "duration_ms": ai_result.get("duration_ms"),
                "sidecar": str(ai_sidecar_path),
                "error": ai_result.get("error"),
            }
        body = format_report(payload, validator, mode, ai_result)
        output_path.write_text(body, encoding="utf-8")
        validate_output(body)
        title = f"Daily Germany Job Search - Combined Validated Shortlist ({today})"
        message_ts = post_result(token, title, body)
        manifest.update({"status": "posted", "message_ts": message_ts, "finished_at": now_iso()})
        write_manifest(manifest_path, manifest)
        print(json.dumps({"ok": True, "output": str(output_path), "message_ts": message_ts, "parts": len(message_ts), "manifest": str(manifest_path)}))
        return 0
    except subprocess.TimeoutExpired as exc:
        failure_ts = post_failure(token, today, output_path, f"Validator timed out after {exc.timeout} seconds.")
        manifest.update({"status": "timeout", "failure_ts": failure_ts, "finished_at": now_iso()})
        write_manifest(manifest_path, manifest)
        print(json.dumps({"ok": False, "error": "validator_timeout", "timeout": exc.timeout, "failure_ts": failure_ts}), file=sys.stderr)
        return 124
    except Exception as exc:
        try:
            failure_ts = post_failure(token, today, output_path, f"Runner failed: `{type(exc).__name__}: {exc}`")
        except Exception:
            failure_ts = None
        manifest.update({"status": "runner_failed", "error": f"{type(exc).__name__}: {exc}", "failure_ts": failure_ts, "finished_at": now_iso()})
        write_manifest(manifest_path, manifest)
        print(json.dumps({"ok": False, "error": manifest["error"], "failure_ts": failure_ts}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
