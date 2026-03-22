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


def _release_handoff_failures(payload: dict) -> list[str]:
    android = payload.get("android", {}) or {}
    windows = payload.get("windows", {}) or {}
    docs_url = str(payload.get("docs_url", "") or "").strip()
    failures: list[str] = []

    android_primary = str(android.get("play_url", "") or "").strip() or str(android.get("apk_url", "") or "").strip()
    windows_primary = str(windows.get("exe_url", "") or "").strip()

    if not android_primary:
        failures.append("android release URL is missing")
    if not windows_primary:
        failures.append("windows release URL is missing")
    if not docs_url:
        failures.append("docs_url is missing")
    return failures


def _provider_readiness_failures(payload: dict) -> list[str]:
    rows = payload.get("providers", [])
    if not isinstance(rows, list) or not rows:
        return ["no enabled RUB payment providers"]

    valid_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code", "") or "").strip()
        label = str(row.get("label", "") or "").strip()
        enabled = row.get("enabled", True)
        if code and label and enabled is not False:
            valid_rows += 1

    if valid_rows == 0:
        return ["no valid RUB payment providers in catalog"]
    return []


def _parse_json(result: HttpResult, *, endpoint: str) -> dict:
    try:
        payload = json.loads(result.body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{endpoint} returned non-JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{endpoint} returned non-object JSON payload")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check /api/client/apps and referenced download links.")
    parser.add_argument("--base-url", default=os.getenv("PORTAL_API_BASE_URL", "https://127.0.0.1"), help="API base URL")
    parser.add_argument("--init-data", default=os.getenv("TELEGRAM_INIT_DATA", ""), help="Telegram initData for auth")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    parser.add_argument("--check-providers", action="store_true", help="Also validate /api/payments/providers readiness")
    parser.add_argument("--require-release-handoff", action="store_true", help="Require Android, Windows and docs URLs to be present")
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
        payload = _parse_json(apps_resp, endpoint="/api/client/apps")
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 2

    print(f"[OK] /api/client/apps -> {apps_resp.status}")

    failures = 0
    if args.require_release_handoff:
        for failure in _release_handoff_failures(payload):
            failures += 1
            print(f"[FAIL] release handoff: {failure}")
        if failures == 0:
            print("[OK] release handoff URLs are present")

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

    if args.check_providers:
        try:
            providers_resp = _request(
                f"{base_url}/api/payments/providers",
                timeout=args.timeout,
                insecure=args.insecure,
            )
        except URLError as exc:
            print(f"[FAIL] /api/payments/providers request error: {exc}")
            return 2

        if not _is_ok(providers_resp.status):
            print(f"[FAIL] /api/payments/providers -> {providers_resp.status}: {providers_resp.body[:200]!r}")
            return 2

        try:
            providers_payload = _parse_json(providers_resp, endpoint="/api/payments/providers")
        except ValueError as exc:
            print(f"[FAIL] {exc}")
            return 2

        provider_failures = _provider_readiness_failures(providers_payload)
        if provider_failures:
            for failure in provider_failures:
                failures += 1
                print(f"[FAIL] providers: {failure}")
        else:
            print(f"[OK] /api/payments/providers -> {providers_resp.status}")

    if failures:
        print(f"[FAIL] {failures} smoke checks failed")
        return 1

    print("[OK] smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
