from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "brain_runtime_app_download_smoke.py"
    spec = importlib.util.spec_from_file_location("brain_runtime_app_download_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _base_remote_payload() -> dict:
    return {
        "unit": "portal-bot",
        "api_base_url": "https://api.pokrov.space",
        "tg_id": 1,
        "signed_init_data_origin": "brain_runtime_bot_token",
        "checks": [
            {"name": "brain_bot_runtime_token", "status": "PASS", "missing": []},
            {"name": "api_health", "status": "PASS", "missing": [], "http_status": 200},
            {"name": "api_client_apps_signed_init_data", "status": "PASS", "missing": [], "http_status": 200},
            {"name": "api_payment_providers", "status": "PASS", "missing": [], "http_status": 200},
        ],
        "client_apps": {
            "android": {
                "play_url": "",
                "apk_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
            },
            "windows": {
                "exe_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
            },
            "docs_url": "https://pokrov.space/install/",
        },
        "payment_providers": {
            "ok": False,
            "blocked": True,
            "providers": [],
            "blocked_reasons": ["paid_checkout_launch_evidence_missing"],
        },
    }


def test_build_report_passes_signed_init_runtime_links_with_blocked_provider_catalog() -> None:
    module = _load_module()

    report = module.build_report(remote_payload=_base_remote_payload())

    assert report["ok"] is True
    assert report["classification"] == "PASS"
    assert report["runtime_app_download_smoke_passed"] is True
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["runtime_client_apps_release_handoff"]["status"] == "PASS"
    assert checks["runtime_payment_provider_policy"]["status"] == "PASS"


def test_build_report_blocks_when_runtime_links_are_not_synced() -> None:
    module = _load_module()
    payload = _base_remote_payload()
    payload["client_apps"] = {
        "android": {"play_url": "", "apk_url": "", "mirror_url": ""},
        "windows": {"exe_url": "", "mirror_url": ""},
        "docs_url": "https://pokrov.space/install/",
    }

    report = module.build_report(remote_payload=payload)

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    checks = {check["name"]: check for check in report["checks"]}
    assert "android release URL is missing" in checks["runtime_client_apps_release_handoff"]["missing"]
    assert "windows release URL is missing" in checks["runtime_client_apps_release_handoff"]["missing"]


def test_build_report_rejects_non_lavatop_green_provider_catalog() -> None:
    module = _load_module()
    payload = _base_remote_payload()
    payload["payment_providers"] = {
        "ok": True,
        "blocked": False,
        "providers": [{"code": "freekassa", "label": "FreeKassa", "enabled": True}],
    }

    report = module.build_report(remote_payload=payload)

    assert report["ok"] is False
    assert report["classification"] == "FAIL"
    checks = {check["name"]: check for check in report["checks"]}
    assert "Lava.top" in checks["runtime_payment_provider_policy"]["missing"][0]


def test_build_report_accepts_lavatop_only_green_provider_catalog() -> None:
    module = _load_module()
    payload = _base_remote_payload()
    payload["payment_providers"] = {
        "ok": True,
        "blocked": False,
        "providers": [{"code": "lavatop", "label": "Lava.top", "enabled": True}],
    }

    report = module.build_report(remote_payload=payload)

    assert report["ok"] is True
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["runtime_payment_provider_policy"]["status"] == "PASS"


def test_report_does_not_serialize_token_or_init_data() -> None:
    module = _load_module()

    report = module.build_report(remote_payload=_base_remote_payload())
    serialized = json.dumps(report)

    assert "BOT_TOKEN" not in serialized
    assert "TELEGRAM_INIT_DATA" not in serialized
    assert "hash=" not in serialized
    assert "secret" not in serialized.lower()
    assert '"tg_id"' not in serialized
    assert '"synthetic_tg_id": "redacted"' in serialized
