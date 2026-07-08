from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from brain_telegram_bot_menu_check import (  # noqa: E402
    _actual_command_names,
    _actual_command_payload,
    _status,
    fetch_brain_bot_env,
    telegram_api_request,
)
from node_access import DEFAULT_PASSWORDS  # noqa: E402
from telegram_profile import (  # noqa: E402
    BOT_PROFILE_DESCRIPTION,
    BOT_PROFILE_NAME,
    BOT_PROFILE_SHORT_DESCRIPTION,
    TELEGRAM_PROFILE_WEBAPP_MENU_TEXT,
    TELEGRAM_PROFILE_WEBAPP_MENU_URL,
    expected_public_command_names,
    expected_public_command_payload,
    expected_webapp_menu_button_payload,
)


def _result_field(payload: dict[str, Any], field: str) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        return ""
    return str(result.get(field) or "").strip()


def _menu_web_app(payload: dict[str, Any]) -> tuple[str, str, str]:
    result = payload.get("result")
    if not isinstance(result, dict):
        return "", "", ""
    menu_type = str(result.get("type") or "").strip()
    text = str(result.get("text") or "").strip()
    web_app = result.get("web_app")
    url = str(web_app.get("url") or "").strip() if isinstance(web_app, dict) else ""
    return menu_type, text, url


def _normalized_url(value: str) -> str:
    value = str(value or "").strip()
    return value.rstrip("/") + "/" if value else ""


def manual_similar_bots_payload(
    *,
    present: str = "unknown",
    count: int | None = None,
    screenshot_path: str = "",
    neighbors: list[str] | None = None,
) -> dict[str, Any]:
    normalized_present = str(present or "unknown").strip().lower()
    if normalized_present not in {"unknown", "present", "absent"}:
        normalized_present = "unknown"
    payload: dict[str, Any] = {
        "present": normalized_present,
        "count": int(count) if count is not None and int(count) >= 0 else None,
        "screenshot_path": str(screenshot_path or "").strip(),
        "neighbors": [str(item).strip()[:80] for item in (neighbors or []) if str(item).strip()],
    }
    return payload


def _manual_similar_bots_check(payload: dict[str, Any] | None) -> dict[str, Any]:
    manual = payload or manual_similar_bots_payload()
    missing: list[str] = []
    if manual.get("present") == "unknown":
        missing.append("weekly Telegram profile screenshot")
    if manual.get("present") == "present" and manual.get("count") is None:
        missing.append("similar bots count")
    return _status(
        "telegram_similar_bots_manual",
        "MANUAL_OWNER_TEST",
        missing=missing,
        note="Telegram Similar bots is automatic and cannot be forced or queried by bot-token Bot API.",
        manual=manual,
    )


def _api_check(name: str, payload: dict[str, Any], method: str) -> dict[str, Any]:
    api_ok = bool(payload.get("ok"))
    return _status(
        name,
        "PASS" if api_ok else "EXTERNAL_DEPENDENCY",
        missing=[] if api_ok else [f"Telegram {method} response ok=true"],
        error_code=payload.get("error_code"),
        description=str(payload.get("description") or "")[:240],
    )


def _exact_text_check(*, name: str, expected: str, actual: str) -> dict[str, Any]:
    return _status(
        name,
        "PASS" if actual == expected else "FAIL",
        missing=[] if actual == expected else [f"expected {name}"],
        expected=expected,
        actual=actual,
    )


def _menu_check(menu_payload: dict[str, Any]) -> dict[str, Any]:
    menu_type, text, url = _menu_web_app(menu_payload)
    expected_url = TELEGRAM_PROFILE_WEBAPP_MENU_URL
    ok = (
        bool(menu_payload.get("ok"))
        and menu_type == "web_app"
        and text == TELEGRAM_PROFILE_WEBAPP_MENU_TEXT
        and _normalized_url(url) == _normalized_url(expected_url)
    )
    return _status(
        "telegram_chat_menu_button",
        "PASS" if ok else "FAIL",
        missing=[] if ok else ["web_app menu button POKROV -> https://app.pokrov.space/"],
        expected=expected_webapp_menu_button_payload(),
        actual={"type": menu_type, "text": text, "web_app": {"url": url}} if menu_type or text or url else None,
        error_code=menu_payload.get("error_code"),
        description=str(menu_payload.get("description") or "")[:240],
    )


def build_report(
    *,
    pid_present: bool,
    token_present: bool,
    name_payload: dict[str, Any] | None,
    short_description_payload: dict[str, Any] | None,
    description_payload: dict[str, Any] | None,
    commands_payload: dict[str, Any] | None,
    menu_payload: dict[str, Any] | None,
    source_unit: str = "portal-bot",
    applied: bool = False,
    apply_checks: list[dict[str, Any]] | None = None,
    similar_bots_manual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        _status(
            "brain_bot_runtime_token",
            "PASS" if pid_present and token_present else "BLOCKED_BY_ACCESS",
            missing=[] if pid_present and token_present else [f"{source_unit} BOT_TOKEN"],
            note="Token presence is read from the live brain process and never written to the report.",
        )
    ]
    checks.extend(apply_checks or [])
    checks.append(_manual_similar_bots_check(similar_bots_manual))

    if not pid_present or not token_present:
        return {
            "ok": False,
            "classification": "BLOCKED_BY_ACCESS",
            "mode": "brain_telegram_bot_profile",
            "source_unit": source_unit,
            "pid_present": bool(pid_present),
            "token_present": bool(token_present),
            "applied": bool(applied),
            "checks": checks,
        }

    name_payload = name_payload or {}
    short_description_payload = short_description_payload or {}
    description_payload = description_payload or {}
    commands_payload = commands_payload or {}
    menu_payload = menu_payload or {}

    checks.append(_api_check("telegram_get_my_name", name_payload, "getMyName"))
    checks.append(_exact_text_check(name="bot_profile_name", expected=BOT_PROFILE_NAME, actual=_result_field(name_payload, "name")))

    checks.append(_api_check("telegram_get_my_short_description", short_description_payload, "getMyShortDescription"))
    checks.append(
        _exact_text_check(
            name="bot_profile_short_description",
            expected=BOT_PROFILE_SHORT_DESCRIPTION,
            actual=_result_field(short_description_payload, "short_description"),
        )
    )

    checks.append(_api_check("telegram_get_my_description", description_payload, "getMyDescription"))
    checks.append(
        _exact_text_check(
            name="bot_profile_description",
            expected=BOT_PROFILE_DESCRIPTION,
            actual=_result_field(description_payload, "description"),
        )
    )

    command_api_ok = bool(commands_payload.get("ok"))
    actual_command_payload = _actual_command_payload(commands_payload)
    actual_commands = _actual_command_names(commands_payload)
    checks.append(_api_check("telegram_get_my_commands", commands_payload, "getMyCommands"))
    checks.append(
        _status(
            "public_command_menu",
            "PASS" if actual_commands == expected_public_command_names() else "FAIL",
            missing=[] if actual_commands == expected_public_command_names() else expected_public_command_names(),
            expected=expected_public_command_names(),
            actual=actual_commands,
        )
    )
    checks.append(
        _status(
            "public_command_descriptions",
            "PASS" if command_api_ok and actual_command_payload == expected_public_command_payload() else "FAIL",
            missing=[] if command_api_ok and actual_command_payload == expected_public_command_payload() else ["expected Russian command descriptions"],
            expected=expected_public_command_payload(),
            actual=actual_command_payload,
        )
    )
    checks.append(_api_check("telegram_get_chat_menu_button", menu_payload, "getChatMenuButton"))
    checks.append(_menu_check(menu_payload))

    blocking_statuses = [check["status"] for check in checks if check["status"] != "MANUAL_OWNER_TEST"]
    ok = all(status == "PASS" for status in blocking_statuses)
    if ok:
        classification = "PASS"
    elif any(status == "EXTERNAL_DEPENDENCY" for status in blocking_statuses):
        classification = "EXTERNAL_DEPENDENCY"
    else:
        classification = "FAIL"
    return {
        "ok": ok,
        "classification": classification,
        "mode": "brain_telegram_bot_profile",
        "source_unit": source_unit,
        "pid_present": bool(pid_present),
        "token_present": bool(token_present),
        "applied": bool(applied),
        "checks": checks,
    }


def run_check(
    *,
    token: str,
    api_request: Callable[[str, str, dict[str, Any] | None], dict[str, Any]] = telegram_api_request,
    apply: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    apply_checks: list[dict[str, Any]] = []
    if apply:
        apply_calls = [
            ("telegram_set_my_name", "setMyName", {"name": BOT_PROFILE_NAME}),
            ("telegram_set_my_short_description", "setMyShortDescription", {"short_description": BOT_PROFILE_SHORT_DESCRIPTION}),
            ("telegram_set_my_description", "setMyDescription", {"description": BOT_PROFILE_DESCRIPTION}),
            ("telegram_set_my_commands", "setMyCommands", {"commands": expected_public_command_payload()}),
            ("telegram_set_chat_menu_button", "setChatMenuButton", {"menu_button": expected_webapp_menu_button_payload()}),
        ]
        for check_name, method, payload in apply_calls:
            response = api_request(token, method, payload)
            apply_checks.append(
                _status(
                    check_name,
                    "PASS" if response.get("ok") else "EXTERNAL_DEPENDENCY",
                    missing=[] if response.get("ok") else [f"Telegram {method} response ok=true"],
                    error_code=response.get("error_code"),
                    description=str(response.get("description") or "")[:240],
                )
            )

    name = api_request(token, "getMyName", None)
    short_description = api_request(token, "getMyShortDescription", None)
    description = api_request(token, "getMyDescription", None)
    commands = api_request(token, "getMyCommands", None)
    menu = api_request(token, "getChatMenuButton", None)
    return name, short_description, description, commands, menu, apply_checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/apply the live Telegram public bot profile without printing BOT_TOKEN.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--source-unit", default="portal-bot")
    parser.add_argument("--output", default="")
    parser.add_argument("--apply", action="store_true", help="Apply the expected profile, commands, and menu before verifying.")
    parser.add_argument("--similar-bots-present", choices=("unknown", "present", "absent"), default="unknown")
    parser.add_argument("--similar-bots-count", type=int, default=None)
    parser.add_argument("--similar-bots-screenshot", default="")
    parser.add_argument("--similar-bots-neighbor", action="append", default=[])
    args = parser.parse_args(argv)

    payload = fetch_brain_bot_env(
        brain_ip=args.brain_ip,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        passwords=args.passwords,
        source_unit=args.source_unit,
    )
    env = dict(payload.get("env") or {})
    token = str(env.get("BOT_TOKEN") or "").strip()
    name_payload: dict[str, Any] | None = None
    short_description_payload: dict[str, Any] | None = None
    description_payload: dict[str, Any] | None = None
    commands_payload: dict[str, Any] | None = None
    menu_payload: dict[str, Any] | None = None
    apply_checks: list[dict[str, Any]] = []
    if token:
        name_payload, short_description_payload, description_payload, commands_payload, menu_payload, apply_checks = run_check(
            token=token,
            apply=bool(args.apply),
        )

    report = build_report(
        pid_present=bool(payload.get("pid_present")),
        token_present=bool(token),
        name_payload=name_payload,
        short_description_payload=short_description_payload,
        description_payload=description_payload,
        commands_payload=commands_payload,
        menu_payload=menu_payload,
        source_unit=str(payload.get("unit") or args.source_unit),
        applied=bool(args.apply),
        apply_checks=apply_checks,
        similar_bots_manual=manual_similar_bots_payload(
            present=args.similar_bots_present,
            count=args.similar_bots_count,
            screenshot_path=args.similar_bots_screenshot,
            neighbors=list(args.similar_bots_neighbor or []),
        ),
    )
    encoded = json.dumps(report, ensure_ascii=True, indent=2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
