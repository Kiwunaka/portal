from __future__ import annotations

import argparse
import json
import shlex
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from node_access import DEFAULT_PASSWORDS, connect_node


EXPECTED_PUBLIC_COMMANDS = ["start", "cabinet", "support", "promo", "redeem"]
EXPECTED_WEBAPP_MENU_URL_PREFIX = "https://app.pokrov.space/"
EXPECTED_WEBAPP_MENU_TEXT = "POKROV"


def expected_public_command_payload() -> list[dict[str, str]]:
    return [
        {"command": "start", "description": "Открыть главное меню"},
        {"command": "cabinet", "description": "Открыть кабинет"},
        {"command": "support", "description": "Написать в поддержку"},
        {"command": "promo", "description": "Активировать промокод"},
        {"command": "redeem", "description": "Активировать ключ доступа"},
    ]


def _remote_env_probe_script(*, unit: str) -> str:
    return f"""python3 - <<'PY'
import json
import subprocess

unit = {unit!r}
pid_raw = subprocess.run(
    ["systemctl", "show", unit, "-p", "MainPID", "--value"],
    check=False,
    capture_output=True,
    text=True,
).stdout.strip()
try:
    pid = int(pid_raw)
except Exception:
    pid = 0
env = {{}}
if pid > 0:
    try:
        for item in open(f"/proc/{{pid}}/environ", "rb").read().split(b"\\0"):
            if b"=" not in item:
                continue
            key, value = item.split(b"=", 1)
            key_text = key.decode("utf-8", "replace")
            if key_text == "BOT_TOKEN":
                env[key_text] = value.decode("utf-8", "replace")
    except Exception:
        pass
print(json.dumps({{"unit": unit, "pid_present": bool(pid > 0), "env": env}}, ensure_ascii=False))
PY"""


def _status(name: str, status: str, *, missing: list[str] | None = None, note: str = "", **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "status": status,
        "missing": list(missing or []),
    }
    if note:
        row["note"] = note
    row.update(extra)
    return row


def _actual_command_names(commands_payload: dict[str, Any]) -> list[str]:
    return [item["command"] for item in _actual_command_payload(commands_payload)]


def _actual_command_payload(commands_payload: dict[str, Any]) -> list[dict[str, str]]:
    result = commands_payload.get("result")
    if not isinstance(result, list):
        return []
    commands: list[dict[str, str]] = []
    for item in result:
        if isinstance(item, dict):
            command = str(item.get("command") or "").strip()
            if command:
                commands.append({"command": command, "description": str(item.get("description") or "")})
    return commands


def _menu_web_app_url(menu_payload: dict[str, Any]) -> str:
    result = menu_payload.get("result")
    if not isinstance(result, dict):
        return ""
    web_app = result.get("web_app")
    if not isinstance(web_app, dict):
        return ""
    return str(web_app.get("url") or "").strip()


def _menu_button_ok(*, menu_api_ok: bool, menu_type: str, web_app_url: str) -> bool:
    if not menu_api_ok:
        return False
    if menu_type in {"commands", "default"}:
        return True
    if menu_type != "web_app":
        return False
    normalized = web_app_url.rstrip("/") + "/" if web_app_url else ""
    return normalized.startswith(EXPECTED_WEBAPP_MENU_URL_PREFIX)


def expected_webapp_menu_button_payload() -> dict[str, Any]:
    return {
        "type": "web_app",
        "text": EXPECTED_WEBAPP_MENU_TEXT,
        "web_app": {"url": EXPECTED_WEBAPP_MENU_URL_PREFIX},
    }


def build_report(
    *,
    pid_present: bool,
    token_present: bool,
    commands_payload: dict[str, Any] | None,
    menu_payload: dict[str, Any] | None,
    source_unit: str = "portal-bot",
    applied: bool = False,
    apply_checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(
        _status(
            "brain_bot_runtime_token",
            "PASS" if pid_present and token_present else "BLOCKED_BY_ACCESS",
            missing=[] if pid_present and token_present else [f"{source_unit} BOT_TOKEN"],
            note="Token presence is read from the live brain process and never written to the report.",
        )
    )
    checks.extend(apply_checks or [])

    if not pid_present or not token_present:
        return {
            "ok": False,
            "classification": "BLOCKED_BY_ACCESS",
            "mode": "brain_telegram_bot_menu",
            "source_unit": source_unit,
            "pid_present": bool(pid_present),
            "token_present": bool(token_present),
            "applied": bool(applied),
            "checks": checks,
        }

    commands_payload = commands_payload or {}
    command_api_ok = bool(commands_payload.get("ok"))
    actual_command_payload = _actual_command_payload(commands_payload)
    actual_commands = _actual_command_names(commands_payload)
    commands_match = actual_commands == EXPECTED_PUBLIC_COMMANDS
    descriptions_match = actual_command_payload == expected_public_command_payload()
    checks.append(
        _status(
            "telegram_get_my_commands",
            "PASS" if command_api_ok else "EXTERNAL_DEPENDENCY",
            missing=[] if command_api_ok else ["Telegram getMyCommands response ok=true"],
            error_code=commands_payload.get("error_code"),
            description=str(commands_payload.get("description") or "")[:240],
        )
    )
    checks.append(
        _status(
            "public_command_menu",
            "PASS" if commands_match else "FAIL",
            missing=[] if commands_match else EXPECTED_PUBLIC_COMMANDS,
            expected=EXPECTED_PUBLIC_COMMANDS,
            actual=actual_commands,
        )
    )
    checks.append(
        _status(
            "public_command_descriptions",
            "PASS" if descriptions_match else "FAIL",
            missing=[] if descriptions_match else ["expected Russian command descriptions"],
            expected=expected_public_command_payload(),
            actual=actual_command_payload,
        )
    )

    menu_payload = menu_payload or {}
    menu_api_ok = bool(menu_payload.get("ok"))
    menu_type = ""
    if isinstance(menu_payload.get("result"), dict):
        menu_type = str(menu_payload["result"].get("type") or "")
    web_app_url = _menu_web_app_url(menu_payload)
    menu_ok = _menu_button_ok(menu_api_ok=menu_api_ok, menu_type=menu_type, web_app_url=web_app_url)
    checks.append(
        _status(
            "telegram_chat_menu_button",
            "PASS" if menu_ok else "EXTERNAL_DEPENDENCY",
            missing=[] if menu_ok else ["Telegram chat menu button type commands/default or web_app app.pokrov.space"],
            actual_type=menu_type or None,
            actual_url=web_app_url or None,
            error_code=menu_payload.get("error_code"),
            description=str(menu_payload.get("description") or "")[:240],
        )
    )

    ok = all(check["status"] == "PASS" for check in checks)
    classification = "PASS" if ok else ("EXTERNAL_DEPENDENCY" if any(c["status"] == "EXTERNAL_DEPENDENCY" for c in checks) else "FAIL")
    return {
        "ok": ok,
        "classification": classification,
        "mode": "brain_telegram_bot_menu",
        "source_unit": source_unit,
        "pid_present": bool(pid_present),
        "token_present": bool(token_present),
        "applied": bool(applied),
        "checks": checks,
    }


def telegram_api_request(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body or "{}")
            parsed["http_status"] = int(response.status)
            return parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body or "{}")
        except Exception:
            parsed = {"ok": False, "description": body[:240]}
        parsed["http_status"] = int(exc.code)
        return parsed
    except Exception as exc:
        return {"ok": False, "error_code": "request_error", "description": str(exc)[:240]}


def fetch_brain_bot_env(*, brain_ip: str, ssh_user: str, ssh_port: int, passwords: str, source_unit: str) -> dict[str, Any]:
    ssh, _auth_method = connect_node(
        code="brain",
        host=brain_ip,
        user=ssh_user,
        port=int(ssh_port),
        passwords_path=Path(passwords),
    )
    try:
        command = "bash -lc " + shlex.quote(_remote_env_probe_script(unit=source_unit))
        _stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
    finally:
        ssh.close()
    if code != 0:
        raise RuntimeError((err or out or "brain bot env probe failed").strip())
    return json.loads(out or "{}")


def run_check(
    *,
    token: str,
    api_request: Callable[[str, str, dict[str, Any] | None], dict[str, Any]] = telegram_api_request,
    apply: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    apply_checks: list[dict[str, Any]] = []
    if apply:
        set_commands = api_request(token, "setMyCommands", {"commands": expected_public_command_payload()})
        apply_checks.append(
            _status(
                "telegram_set_my_commands",
                "PASS" if set_commands.get("ok") else "EXTERNAL_DEPENDENCY",
                missing=[] if set_commands.get("ok") else ["Telegram setMyCommands response ok=true"],
                error_code=set_commands.get("error_code"),
                description=str(set_commands.get("description") or "")[:240],
            )
        )
        set_menu = api_request(token, "setChatMenuButton", {"menu_button": expected_webapp_menu_button_payload()})
        apply_checks.append(
            _status(
                "telegram_set_chat_menu_button",
                "PASS" if set_menu.get("ok") else "EXTERNAL_DEPENDENCY",
                missing=[] if set_menu.get("ok") else ["Telegram setChatMenuButton response ok=true"],
                error_code=set_menu.get("error_code"),
                description=str(set_menu.get("description") or "")[:240],
            )
        )
    commands = api_request(token, "getMyCommands", None)
    menu = api_request(token, "getChatMenuButton", None)
    return commands, menu, apply_checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the live Telegram public bot command menu without printing BOT_TOKEN.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--source-unit", default="portal-bot")
    parser.add_argument("--output", default="")
    parser.add_argument("--apply", action="store_true", help="Apply the expected commands/menu before verifying.")
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
    commands_payload: dict[str, Any] | None = None
    menu_payload: dict[str, Any] | None = None
    apply_checks: list[dict[str, Any]] = []
    if token:
        commands_payload, menu_payload, apply_checks = run_check(token=token, apply=bool(args.apply))
    report = build_report(
        pid_present=bool(payload.get("pid_present")),
        token_present=bool(token),
        commands_payload=commands_payload,
        menu_payload=menu_payload,
        source_unit=str(payload.get("unit") or args.source_unit),
        applied=bool(args.apply),
        apply_checks=apply_checks,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
