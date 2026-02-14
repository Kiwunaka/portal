#!/usr/bin/env python3
"""Smoke check for client app links exposed by /api/client/apps."""

from __future__ import annotations

import argparse
import json
import os
import ssl
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class HttpResult:
    status: int
    final_url: str
    body: str


def _request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, timeout: int = 15, insecure: bool = False) -> HttpResult:
    req = Request(url=url, headers=headers or {}, method=method)
    context = ssl._create_unverified_context() if insecure else None
    try:
        with urlopen(req, timeout=timeout, context=context) as resp:
            body_bytes = resp.read(1024)
            return HttpResult(status=int(resp.getcode() or 0), final_url=resp.geturl(), body=body_bytes.decode("utf-8", errors="replace"))
    except HTTPError as exc:
        body_bytes = exc.read(512)
        return HttpResult(status=int(exc.code or 0), final_url=exc.geturl(), body=body_bytes.decode("utf-8", errors="replace"))


def _is_ok(status: int) -> bool:
    return 200 <= status < 400


def _probe_artifact(url: str, *, timeout: int, insecure: bool) -> tuple[bool, str]:
    head = _request(url, method="HEAD", timeout=timeout, insecure=insecure)
    if _is_ok(head.status):
        return True, f"HEAD {head.status} -> {head.final_url}"

    if head.status in {403, 405, 501}:
        get = _request(
            url,
            method="GET",
            headers={"Range": "bytes=0-0", "Cache-Control": "no-cache"},
            timeout=timeout,
            insecure=insecure,
        )
        if _is_ok(get.status):
            return True, f"GET {get.status} -> {get.final_url}"
        return False, f"GET failed with {get.status} ({get.body[:120]!r})"

    return False, f"HEAD failed with {head.status} ({head.body[:120]!r})"


def _iter_urls(payload: dict) -> Iterable[tuple[str, str]]:
    mapping = {
        "android.play_url": payload.get("android", {}).get("play_url", ""),
        "android.apk_url": payload.get("android", {}).get("apk_url", ""),
        "android.mirror_url": payload.get("android", {}).get("mirror_url", ""),
        "windows.exe_url": payload.get("windows", {}).get("exe_url", ""),
        "windows.mirror_url": payload.get("windows", {}).get("mirror_url", ""),
        "docs_url": payload.get("docs_url", ""),
    }
    for key, value in mapping.items():
        val = str(value or "").strip()
        if val:
            yield key, val


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check /api/client/apps and referenced download links.")
    parser.add_argument("--base-url", default=os.getenv("PORTAL_API_BASE_URL", "https://127.0.0.1"), help="API base URL")
    parser.add_argument("--init-data", default=os.getenv("TELEGRAM_INIT_DATA", ""), help="Telegram initData for auth")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        health = _request(f"{base_url}/api/health", timeout=args.timeout, insecure=args.insecure)
    except URLError as exc:
        print(f"[FAIL] /api/health request error: {exc}")
        return 2

    if not _is_ok(health.status):
        print(f"[FAIL] /api/health -> {health.status}")
        return 2
    print(f"[OK] /api/health -> {health.status}")

    init_data = (args.init_data or "").strip()
    if not init_data:
        print("[FAIL] --init-data (or TELEGRAM_INIT_DATA) is required for /api/client/apps")
        return 2

    try:
        apps_resp = _request(
            f"{base_url}/api/client/apps",
            headers={"X-Telegram-Init-Data": init_data},
            timeout=args.timeout,
            insecure=args.insecure,
        )
    except URLError as exc:
        print(f"[FAIL] /api/client/apps request error: {exc}")
        return 2

    if not _is_ok(apps_resp.status):
        print(f"[FAIL] /api/client/apps -> {apps_resp.status}: {apps_resp.body[:200]!r}")
        return 2

    try:
        payload = json.loads(apps_resp.body)
    except json.JSONDecodeError as exc:
        print(f"[FAIL] /api/client/apps returned non-JSON payload: {exc}")
        return 2

    print(f"[OK] /api/client/apps -> {apps_resp.status}")

    failures = 0
    checked = 0
    for key, url in _iter_urls(payload):
        checked += 1
        try:
            ok, details = _probe_artifact(url, timeout=args.timeout, insecure=args.insecure)
        except URLError as exc:
            ok = False
            details = f"request error: {exc}"

        if ok:
            print(f"[OK] {key}: {details}")
        else:
            failures += 1
            print(f"[FAIL] {key}: {details}")

    if checked == 0:
        print("[WARN] /api/client/apps contains no URLs to check")

    if failures:
        print(f"[FAIL] {failures} URL checks failed")
        return 1

    print("[OK] smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
