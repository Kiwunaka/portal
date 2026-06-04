from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = ROOT.parent / "POKROV-app"
SCRIPT_PATH = ROOT / "scripts" / "app_bot_parity_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("app_bot_parity_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_bot_parity_static_smoke_is_green_for_current_contracts():
    smoke = _load_smoke_module()

    report = smoke.build_report(ROOT, CLIENT_ROOT)

    assert report["ok"] is True
    checks = {check["id"]: check for check in report["checks"]}
    for check_id in (
        "platform_app_first_endpoints",
        "client_app_first_adapter",
        "webapp_cabinet_and_support",
        "telegram_bonus_contract",
        "support_ticket_contract",
        "safe_redeem_guard",
        "bot_entrypoints_present",
    ):
        assert checks[check_id]["status"] == "PASS"

    assert checks["manual_real_telegram_parity"]["status"] == "MANUAL_OWNER_TEST"
    assert checks["manual_live_account_parity"]["status"] == "MANUAL_OWNER_TEST"
