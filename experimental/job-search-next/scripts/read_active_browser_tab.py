#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

from common import DATA_ROOT, write_json, write_text


CHROME_FAMILY = {
    "Google Chrome",
    "Brave Browser",
    "Arc",
    "Microsoft Edge",
    "Chromium",
}
SAFARI_FAMILY = {"Safari"}
SUPPORTED_BROWSERS = CHROME_FAMILY | SAFARI_FAMILY


def run_osascript(lines: list[str], args: list[str] | None = None) -> str:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    if args:
        command.extend(args)
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "osascript failed")
    return result.stdout.strip()


def frontmost_app() -> str:
    return run_osascript(
        ['tell application "System Events" to get name of first application process whose frontmost is true']
    )


def detect_browser(explicit_browser: str | None = None) -> str:
    if explicit_browser:
        return explicit_browser
    app_name = frontmost_app()
    if app_name not in SUPPORTED_BROWSERS:
        raise RuntimeError(f"Frontmost app is `{app_name}`, which is not a supported browser.")
    return app_name


def window_count(browser: str) -> int:
    output = run_osascript([f'tell application "{browser}" to get count of windows'])
    return int(output or "0")


def active_tab_identity(browser: str) -> dict[str, str]:
    if browser in CHROME_FAMILY:
        output = run_osascript(
            [
                f'tell application "{browser}"',
                "set tabTitle to title of active tab of front window",
                "set tabUrl to URL of active tab of front window",
                "return tabTitle & linefeed & tabUrl",
                "end tell",
            ]
        )
    else:
        output = run_osascript(
            [
                f'tell application "{browser}"',
                "set tabTitle to name of current tab of front window",
                "set tabUrl to URL of current tab of front window",
                "return tabTitle & linefeed & tabUrl",
                "end tell",
            ]
        )
    lines = output.splitlines()
    title = lines[0] if lines else ""
    url = lines[1] if len(lines) > 1 else ""
    return {"title": title, "url": url}


def execute_javascript(browser: str, javascript: str) -> str:
    if browser in CHROME_FAMILY:
        lines = [
            "on run argv",
            "set jsCode to item 1 of argv",
            f'tell application "{browser}"',
            "return execute active tab of front window javascript jsCode",
            "end tell",
            "end run",
        ]
    else:
        lines = [
            "on run argv",
            "set jsCode to item 1 of argv",
            f'tell application "{browser}"',
            "return do JavaScript jsCode in current tab of front window",
            "end tell",
            "end run",
        ]
    return run_osascript(lines, [javascript])


def form_snapshot_js() -> str:
    return r"""
(() => {
  const visible = (el) => {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style && style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
  };
  const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const labelText = (el) => {
    const labels = [];
    if (el.id) {
      document.querySelectorAll(`label[for="${el.id}"]`).forEach((item) => labels.push(clean(item.textContent)));
    }
    if (el.closest('label')) {
      labels.push(clean(el.closest('label').textContent));
    }
    const ariaLabel = clean(el.getAttribute('aria-label'));
    if (ariaLabel) labels.push(ariaLabel);
    const labelledBy = clean(el.getAttribute('aria-labelledby'));
    if (labelledBy) {
      labelledBy.split(/\s+/).forEach((id) => {
        const node = document.getElementById(id);
        if (node) labels.push(clean(node.textContent));
      });
    }
    return [...new Set(labels.filter(Boolean))].join(' | ');
  };
  const fieldPayload = [...document.querySelectorAll('input, textarea, select')]
    .filter((el) => visible(el))
    .slice(0, 40)
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: el.type || el.tagName.toLowerCase(),
      name: clean(el.name),
      id: clean(el.id),
      placeholder: clean(el.placeholder),
      label: labelText(el),
      required: !!el.required || el.getAttribute('aria-required') === 'true',
      autocomplete: clean(el.autocomplete),
      options: el.tagName.toLowerCase() === 'select'
        ? [...el.options].slice(0, 8).map((opt) => clean(opt.textContent)).filter(Boolean)
        : [],
    }));
  const buttonPayload = [...document.querySelectorAll('button, input[type="submit"], input[type="button"]')]
    .filter((el) => visible(el))
    .slice(0, 20)
    .map((el) => clean(el.innerText || el.value || el.textContent));
  const headings = [...document.querySelectorAll('h1, h2, h3')]
    .filter((el) => visible(el))
    .slice(0, 8)
    .map((el) => clean(el.textContent))
    .filter(Boolean);
  return JSON.stringify({
    title: document.title,
    url: window.location.href,
    headings,
    fields: fieldPayload,
    buttons: buttonPayload,
  });
})()
""".strip()


def read_active_tab(browser: str, extract_form: bool = False) -> dict[str, Any]:
    count = window_count(browser)
    if count == 0:
        return {
            "status": "no_active_browser_window",
            "browser": browser,
            "window_count": 0,
            "title": "",
            "url": "",
            "form_snapshot": None,
            "error": f"{browser} is frontmost but has no open browser window.",
        }

    identity = active_tab_identity(browser)
    form_snapshot = None
    error = ""
    if extract_form:
        try:
            raw_payload = execute_javascript(browser, form_snapshot_js())
            form_snapshot = json.loads(raw_payload) if raw_payload else None
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return {
        "status": "ok",
        "browser": browser,
        "window_count": count,
        "title": identity["title"],
        "url": identity["url"],
        "form_snapshot": form_snapshot,
        "error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser")
    parser.add_argument("--extract-form", action="store_true")
    parser.add_argument("--output-name")
    parser.add_argument("--json-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        browser = detect_browser(args.browser)
        payload = read_active_tab(browser, extract_form=args.extract_form)
    except Exception as exc:  # noqa: BLE001
        payload = {
            "status": "error",
            "browser": args.browser or "",
            "window_count": 0,
            "title": "",
            "url": "",
            "form_snapshot": None,
            "error": str(exc),
        }

    if args.output_name:
        json_path = DATA_ROOT / f"{args.output_name}.json"
        md_path = DATA_ROOT / f"{args.output_name}.md"
        write_json(json_path, payload)
        md_lines = [
            "# Active Browser Tab Snapshot",
            "",
            f"- Status: `{payload['status']}`",
            f"- Browser: `{payload['browser'] or 'unknown'}`",
            f"- Title: {payload['title'] or '(none)' }",
            f"- URL: {payload['url'] or '(none)' }",
        ]
        if payload["error"]:
            md_lines.append(f"- Error: `{payload['error']}`")
        if payload["form_snapshot"]:
            md_lines.extend(
                [
                    "",
                    "## Visible Form Fields",
                    "",
                ]
            )
            for field in payload["form_snapshot"].get("fields", []):
                label = field.get("label") or field.get("name") or field.get("placeholder") or field.get("type")
                md_lines.append(f"- `{label}` ({field.get('tag')} / {field.get('type')})")
        write_text(md_path, "\n".join(md_lines) + "\n")

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(f"status={payload['status']} browser={payload['browser']} title={payload['title']} url={payload['url']}")
        if payload["error"]:
            print(f"error={payload['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
