from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "brain_telegram_bot_profile_check.py"
    spec = importlib.util.spec_from_file_location("brain_telegram_bot_profile_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _passing_payloads(module):
    return {
        "name_payload": {"ok": True, "result": {"name": module.BOT_PROFILE_NAME}},
        "short_description_payload": {"ok": True, "result": {"short_description": module.BOT_PROFILE_SHORT_DESCRIPTION}},
        "description_payload": {"ok": True, "result": {"description": module.BOT_PROFILE_DESCRIPTION}},
        "commands_payload": {"ok": True, "result": module.expected_public_command_payload()},
        "menu_payload": {"ok": True, "result": module.expected_webapp_menu_button_payload()},
    }


def test_build_report_passes_expected_profile_and_keeps_similar_bots_manual() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        source_unit="portal-bot",
        similar_bots_manual=module.manual_similar_bots_payload(
            present="absent",
            count=0,
            screenshot_path="docs/audit-artifacts/telegram-similar-bots/2026-07-08.png",
        ),
        **_passing_payloads(module),
    )

    assert report["ok"] is True
    assert report["classification"] == "PASS"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["bot_profile_name"]["status"] == "PASS"
    assert checks["telegram_similar_bots_manual"]["status"] == "MANUAL_OWNER_TEST"


def test_build_report_detects_profile_and_menu_drift() -> None:
    module = _load_module()
    payloads = _passing_payloads(module)
    payloads["name_payload"] = {"ok": True, "result": {"name": "POKROV"}}
    payloads["description_payload"] = {"ok": True, "result": {"description": "old"}}
    payloads["menu_payload"] = {"ok": True, "result": {"type": "commands"}}

    report = module.build_report(
        pid_present=True,
        token_present=True,
        similar_bots_manual=module.manual_similar_bots_payload(present="unknown"),
        **payloads,
    )

    assert report["ok"] is False
    assert report["classification"] == "FAIL"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["bot_profile_name"]["status"] == "FAIL"
    assert checks["bot_profile_description"]["status"] == "FAIL"
    assert checks["telegram_chat_menu_button"]["status"] == "FAIL"


def test_missing_brain_token_is_blocked_without_secret_values() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=False,
        name_payload=None,
        short_description_payload=None,
        description_payload=None,
        commands_payload=None,
        menu_payload=None,
    )

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    serialized = module.json.dumps(report)
    assert "BOT_TOKEN=" not in serialized
    assert "secret" not in serialized.lower()


def test_run_check_apply_uses_expected_profile_methods_without_leaking_token() -> None:
    module = _load_module()
    calls: list[tuple[str, str, object]] = []

    def fake_api(token: str, method: str, payload: dict | None = None) -> dict:
        calls.append((token, method, payload))
        responses = {
            "getMyName": {"ok": True, "result": {"name": module.BOT_PROFILE_NAME}},
            "getMyShortDescription": {"ok": True, "result": {"short_description": module.BOT_PROFILE_SHORT_DESCRIPTION}},
            "getMyDescription": {"ok": True, "result": {"description": module.BOT_PROFILE_DESCRIPTION}},
            "getMyCommands": {"ok": True, "result": module.expected_public_command_payload()},
            "getChatMenuButton": {"ok": True, "result": module.expected_webapp_menu_button_payload()},
        }
        return responses.get(method, {"ok": True, "result": True})

    name, short_description, description, commands, menu, apply_checks = module.run_check(
        token="live-secret-token",
        api_request=fake_api,
        apply=True,
    )

    assert name["ok"] is True
    assert short_description["ok"] is True
    assert description["ok"] is True
    assert commands["ok"] is True
    assert menu["ok"] is True
    assert [check["status"] for check in apply_checks] == ["PASS", "PASS", "PASS", "PASS", "PASS"]
    assert [call[1] for call in calls] == [
        "setMyName",
        "setMyShortDescription",
        "setMyDescription",
        "setMyCommands",
        "setChatMenuButton",
        "getMyName",
        "getMyShortDescription",
        "getMyDescription",
        "getMyCommands",
        "getChatMenuButton",
    ]
    serialized_checks = module.json.dumps(apply_checks, ensure_ascii=False)
    assert "live-secret-token" not in serialized_checks
    assert calls[0][2] == {"name": module.BOT_PROFILE_NAME}
    assert calls[1][2] == {"short_description": module.BOT_PROFILE_SHORT_DESCRIPTION}
    assert calls[2][2] == {"description": module.BOT_PROFILE_DESCRIPTION}
