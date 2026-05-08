#!/usr/bin/env python3
"""Smoke check for client app links exposed by /api/client/apps."""

from __future__ import annotations

import argparse
import json
import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
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

    play_url = str(android.get("play_url", "") or "").strip()
    android_primary = str(android.get("apk_url", "") or "").strip() or str(android.get("mirror_url", "") or "").strip()
    windows_primary = str(windows.get("exe_url", "") or "").strip() or str(windows.get("mirror_url", "") or "").strip()

    if play_url:
        failures.append("android Play URL must be empty for outside-store public beta")
    if not android_primary:
        failures.append("android release URL is missing")
    if not windows_primary:
        failures.append("windows release URL is missing")
    if not docs_url:
        failures.append("docs_url is missing")

    for key in ("apk_url", "mirror_url"):
        failures.extend(_release_artifact_url_failures(f"android.{key}", android.get(key, ""), suffix=".apk"))
    for key in ("exe_url", "mirror_url"):
        failures.extend(_release_artifact_url_failures(f"windows.{key}", windows.get(key, ""), suffix=".exe"))
    failures.extend(_docs_url_failures("docs_url", docs_url))
    return failures


def _release_artifact_url_failures(key: str, raw_url: object, *, suffix: str) -> list[str]:
    url = str(raw_url or "").strip()
    if not url:
        return []
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return [f"{key} must be an https URL"]
    host = str(parsed.hostname or "").lower()
    path = str(parsed.path or "").lower()
    if host != "github.com" or "/releases/download/" not in path or not path.endswith(suffix):
        return [f"{key} must point to a GitHub Releases {suffix} artifact"]
    return []


def _docs_url_failures(key: str, raw_url: object) -> list[str]:
    url = str(raw_url or "").strip()
    if not url:
        return []
    parsed = urlparse(url)
    path = str(parsed.path or "")
    if (
        parsed.scheme.lower() != "https"
        or str(parsed.hostname or "").lower() != "pokrov.space"
        or not (path == "/install" or path.startswith("/install/"))
    ):
        return [f"{key} must point to https://pokrov.space/install/"]
    return []


def _provider_readiness_failures(payload: dict) -> list[str]:
    rows = payload.get("providers", [])
    blocked = bool(payload.get("blocked")) or payload.get("ok") is False
    if blocked:
        reasons = payload.get("blocked_reasons", [])
        reason_rows = [str(item or "").strip() for item in reasons if str(item or "").strip()] if isinstance(reasons, list) else []
        if rows:
            return ["blocked RUB payment provider catalog must not expose providers"]
        if not reason_rows:
            return ["blocked RUB payment provider catalog must include blocked_reasons"]
        return []

    rows = payload.get("providers", [])
    if not isinstance(rows, list) or not rows:
        return ["no enabled RUB payment providers"]

    provider_codes: list[str] = []
    enabled_codes: list[str] = []
    invalid_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            invalid_rows += 1
            continue
        code = str(row.get("code", "") or "").strip().lower()
        label = str(row.get("label", "") or "").strip()
        enabled = row.get("enabled", True)
        if not code or not label:
            invalid_rows += 1
            continue
        provider_codes.append(code)
        if enabled is not False:
            enabled_codes.append(code)

    if invalid_rows:
        return ["RUB payment provider catalog contains invalid provider rows"]
    if provider_codes != ["lavatop"]:
        return [f"public beta paid checkout must expose only Lava.top; got {', '.join(provider_codes)}"]
    if enabled_codes != ["lavatop"]:
        return ["public beta Lava.top provider must be enabled"]
    return []


def _parse_json(result: HttpResult, *, endpoint: str) -> dict:
    try:
        payload = json.loads(result.body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{endpoint} returned non-JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{endpoint} returned non-object JSON payload")
    return payload


def _load_apps_json(path: str) -> dict:
    payload_path = Path(path)
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{payload_path} contains invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{payload_path} must contain a JSON object shaped like /api/client/apps")
    return _normalize_apps_payload(payload)


def _normalize_apps_payload(payload: dict) -> dict:
    if "downloads" not in payload and "runtime_env" not in payload:
        return payload

    downloads = payload.get("downloads", {}) if isinstance(payload.get("downloads"), dict) else {}
    android = downloads.get("android", {}) if isinstance(downloads.get("android"), dict) else {}
    windows = downloads.get("windows", {}) if isinstance(downloads.get("windows"), dict) else {}
    runtime_env = payload.get("runtime_env", {}) if isinstance(payload.get("runtime_env"), dict) else {}

    def _first(*values: object) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    return {
        "android": {
            "play_url": _first(android.get("play_url"), runtime_env.get("APP_ANDROID_PLAY_URL")),
            "apk_url": _first(android.get("apk_url"), runtime_env.get("APP_ANDROID_APK_URL")),
            "mirror_url": _first(android.get("mirror_url"), runtime_env.get("APP_ANDROID_MIRROR_URL")),
        },
        "windows": {
            "exe_url": _first(windows.get("exe_url"), runtime_env.get("APP_WINDOWS_EXE_URL")),
            "mirror_url": _first(windows.get("mirror_url"), runtime_env.get("APP_WINDOWS_MIRROR_URL")),
        },
        "docs_url": _first(downloads.get("docs_url"), payload.get("docs_url"), runtime_env.get("APP_DOCS_URL")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check /api/client/apps and referenced download links.")
    parser.add_argument("--base-url", default=os.getenv("PORTAL_API_BASE_URL", "https://127.0.0.1"), help="API base URL")
    parser.add_argument("--init-data", default=os.getenv("TELEGRAM_INIT_DATA", ""), help="Telegram initData for auth")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    parser.add_argument("--check-providers", action="store_true", help="Also validate /api/payments/providers public-beta policy")
    parser.add_argument("--require-release-handoff", action="store_true", help="Require Android, Windows and docs URLs to be present")
    parser.add_argument(
        "--apps-json",
        default="",
        help="Validate a staged /api/client/apps JSON payload directly instead of calling live /api/client/apps. This is URL-only pre-sync evidence.",
    )
    parser.add_argument(
        "--policy-only",
        action="store_true",
        help="Validate payload shape and release URL policy without probing referenced URLs. This does not prove artifacts are reachable.",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if args.apps_json:
        try:
            payload = _load_apps_json(args.apps_json)
        except ValueError as exc:
            print(f"[FAIL] {exc}")
            return 2
        print(f"[OK] staged /api/client/apps payload loaded from {args.apps_json}")
        if args.check_providers:
            print("[WARN] --check-providers is ignored in --apps-json URL-only mode")
    else:
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

    urls_to_check = list(_iter_urls(payload))
    checked = 0
    if args.policy_only:
        print(f"[WARN] --policy-only skipped URL reachability probes for {len(urls_to_check)} referenced URLs")
    else:
        for key, url in urls_to_check:
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

    if not urls_to_check:
        print("[WARN] /api/client/apps contains no URLs to check")

    if args.check_providers and not args.apps_json:
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
