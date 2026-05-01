#!/usr/bin/env python3
"""Twice-daily Scroll Mile -> Render bridge.

Reads #lifetimeMiles from the Scroll Mile dashboard using Playwright + a
persistent Chromium profile that has the Scroll Mile extension installed,
then POSTs the value to the deployed API.

Required env vars:
  BRIDGE_URL              e.g. https://scroll-climber-api.onrender.com/api/external-progress
  EXTERNAL_PROGRESS_TOKEN must match the token configured on the API
  USER_DATA_DIR           absolute path to a Chrome user-data dir that has the
                          Scroll Mile extension loaded
Optional:
  EXTENSION_ID            override default Scroll Mile extension id
  BROWSER_CHANNEL         Playwright browser channel (default: chrome)
  HEADLESS                "1" to run headless (default 0; extensions are most
                          reliable with a visible window)
  TIMEOUT_MS              navigation/wait timeout, default 20000
  SKIP_SSL_VERIFY         "1" disables TLS certificate verification for POST.
                          Use only if your local Python cert store is broken.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.request
from typing import Optional

from playwright.sync_api import sync_playwright

DEFAULT_EXTENSION_ID = "kdeibhcngffpofgiaglnbhfpiocffihh"
DASHBOARD_PATH = "dashboard.html"

LABELED_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:mi|mile|miles)\b", re.IGNORECASE)
DECIMAL_RE = re.compile(r"\b(\d+\.\d{2,})\b")


def parse_miles(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = text.replace(",", "")
    m = LABELED_RE.search(cleaned)
    if not m:
        m = DECIMAL_RE.search(cleaned)
    if not m:
        return None
    try:
        value = float(m.group(1))
    except ValueError:
        return None
    return value if value >= 0 else None


def post_miles(bridge_url: str, token: str, miles: float, skip_ssl_verify: bool) -> dict:
    body = json.dumps(
        {
            "miles": miles,
            "source": "launchd-sync",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        bridge_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Bridge-Token": token,
        },
    )
    ssl_context = None
    if skip_ssl_verify:
        ssl_context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        return json.loads(resp.read().decode("utf-8"))


def read_lifetime_miles(
    user_data_dir: str,
    extension_id: str,
    headless: bool,
    timeout_ms: int,
    browser_channel: str,
) -> Optional[float]:
    target_url = f"chrome-extension://{extension_id}/{DASHBOARD_PATH}"
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            channel=browser_channel,
            ignore_default_args=["--disable-extensions"],
            args=[
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )
        try:
            page = browser_context.new_page()
            page.set_default_timeout(timeout_ms)
            page.goto(target_url, wait_until="domcontentloaded")
            try:
                page.wait_for_selector("#lifetimeMiles", timeout=timeout_ms)
            except Exception:
                pass
            text = page.text_content("#lifetimeMiles") or ""
            if not text.strip():
                text = page.evaluate("() => document.body && document.body.innerText || ''")
            return parse_miles(text)
        finally:
            browser_context.close()


def main() -> int:
    bridge_url = os.environ.get("BRIDGE_URL", "").strip()
    token = os.environ.get("EXTERNAL_PROGRESS_TOKEN", "").strip()
    user_data_dir = os.environ.get("USER_DATA_DIR", "").strip()
    extension_id = os.environ.get("EXTENSION_ID", DEFAULT_EXTENSION_ID).strip()
    browser_channel = os.environ.get("BROWSER_CHANNEL", "chrome").strip() or "chrome"
    headless = os.environ.get("HEADLESS", "0") == "1"
    skip_ssl_verify = os.environ.get("SKIP_SSL_VERIFY", "0") == "1"
    try:
        timeout_ms = int(os.environ.get("TIMEOUT_MS", "20000"))
    except ValueError:
        timeout_ms = 20000

    missing = [name for name, val in (
        ("BRIDGE_URL", bridge_url),
        ("EXTERNAL_PROGRESS_TOKEN", token),
        ("USER_DATA_DIR", user_data_dir),
    ) if not val]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 2

    miles = read_lifetime_miles(user_data_dir, extension_id, headless, timeout_ms, browser_channel)
    if miles is None:
        print("Could not read #lifetimeMiles from dashboard", file=sys.stderr)
        return 3

    try:
        result = post_miles(bridge_url, token, miles, skip_ssl_verify)
    except Exception as exc:
        print(f"POST failed: {exc}", file=sys.stderr)
        return 4

    print(json.dumps({"miles": miles, "server": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
