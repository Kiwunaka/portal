from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "brain_telegram_bot_menu_check.py"
    spec = importlib.util.spec_from_file_location("brain_telegram_bot_menu_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_report_passes_expected_public_command_menu() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        commands_payload={
            "ok": True,
            "result": module.expected_public_command_payload(),
        },
        menu_payload={"ok": True, "result": {"type": "commands"}},
    )

    assert report["ok"] is True
    assert report["classification"] == "PASS"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["public_command_menu"]["actual"] == module.EXPECTED_PUBLIC_COMMANDS
    assert checks["public_command_descriptions"]["status"] == "PASS"


def test_build_report_accepts_app_first_webapp_menu_button() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        commands_payload={
            "ok": True,
            "result": module.expected_public_command_payload(),
        },
        menu_payload={
            "ok": True,
            "result": {
                "type": "web_app",
                "text": "POKROV",
                "web_app": {"url": "https://app.pokrov.space/"},
            },
        },
    )

    assert report["ok"] is True
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["telegram_chat_menu_button"]["status"] == "PASS"
    assert checks["telegram_chat_menu_button"]["actual_type"] == "web_app"
    assert checks["telegram_chat_menu_button"]["actual_url"] == "https://app.pokrov.space/"


def test_build_report_rejects_unknown_webapp_menu_button() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        commands_payload={
            "ok": True,
            "result": module.expected_public_command_payload(),
        },
        menu_payload={
            "ok": True,
            "result": {
                "type": "web_app",
                "text": "POKROV",
                "web_app": {"url": "https://example.invalid/"},
            },
        },
    )

    assert report["ok"] is False
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["telegram_chat_menu_button"]["status"] == "EXTERNAL_DEPENDENCY"
    assert "web_app app.pokrov.space" in checks["telegram_chat_menu_button"]["missing"][0]


def test_build_report_fails_when_cabinet_or_support_commands_are_missing() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        commands_payload={"ok": True, "result": [{"command": "start"}, {"command": "promo"}]},
        menu_payload={"ok": True, "result": {"type": "commands"}},
    )

    assert report["ok"] is False
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["public_command_menu"]["status"] == "FAIL"
    assert "cabinet" in checks["public_command_menu"]["missing"]
    assert "support" in checks["public_command_menu"]["missing"]


def test_build_report_fails_when_public_command_descriptions_are_not_russian() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=True,
        commands_payload={
            "ok": True,
            "result": [{"command": command, "description": command} for command in module.EXPECTED_PUBLIC_COMMANDS],
        },
        menu_payload={"ok": True, "result": {"type": "commands"}},
    )

    assert report["ok"] is False
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["public_command_menu"]["status"] == "PASS"
    assert checks["public_command_descriptions"]["status"] == "FAIL"


def test_missing_brain_token_is_blocked_without_secret_values() -> None:
    module = _load_module()

    report = module.build_report(
        pid_present=True,
        token_present=False,
        commands_payload=None,
        menu_payload=None,
    )

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    serialized = module.json.dumps(report)
    assert "BOT_TOKEN=" not in serialized
    assert "secret" not in serialized.lower()


def test_run_check_apply_uses_expected_commands_without_leaking_token() -> None:
    module = _load_module()
    calls: list[tuple[str, str, object]] = []

    def fake_api(token: str, method: str, payload: dict | None = None) -> dict:
        calls.append((token, method, payload))
        if method == "getMyCommands":
            return {
                "ok": True,
                "result": module.expected_public_command_payload(),
            }
        if method == "getChatMenuButton":
            return {"ok": True, "result": {"type": "commands"}}
        return {"ok": True, "result": True}

    commands, menu, apply_checks = module.run_check(token="live-secret-token", api_request=fake_api, apply=True)

    assert commands["ok"] is True
    assert menu["ok"] is True
    assert [check["status"] for check in apply_checks] == ["PASS", "PASS"]
    assert [call[1] for call in calls] == [
        "setMyCommands",
        "setChatMenuButton",
        "getMyCommands",
        "getChatMenuButton",
    ]
    set_commands_payload = calls[0][2]
    assert isinstance(set_commands_payload, dict)
    descriptions = [item["description"] for item in set_commands_payload["commands"]]
    assert descriptions == [
        "Попробовать VPN бесплатно",
        "Доступ, устройства и тарифы",
        "VPN не работает? Получить помощь",
        "Инструкции и низкая скорость",
        "Получить скидку по промокоду",
        "Включить оплаченный доступ",
    ]
    set_menu_payload = calls[1][2]
    assert isinstance(set_menu_payload, dict)
    assert set_menu_payload == {"menu_button": module.expected_webapp_menu_button_payload()}
    serialized_checks = module.json.dumps(apply_checks)
    assert "live-secret-token" not in serialized_checks
