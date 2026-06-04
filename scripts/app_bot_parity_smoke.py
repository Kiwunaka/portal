from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


Status = str


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _missing_needles(text: str | None, needles: tuple[str, ...]) -> list[str]:
    if text is None:
        return list(needles)
    return [needle for needle in needles if needle not in text]


def _check(
    *,
    check_id: str,
    title: str,
    evidence: str,
    missing: list[str],
    required: bool = True,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "status": "PASS" if not missing else "FAIL",
        "required": required,
        "evidence": evidence,
        "missing": missing,
    }


def _manual_check(check_id: str, title: str, evidence: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "status": "MANUAL_OWNER_TEST",
        "required": False,
        "evidence": evidence,
        "missing": [],
    }


def build_report(root: str | Path, client_root: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    client_path = Path(client_root)

    api = _read_text(root_path / "portal_bot" / "api.py")
    webapp_api = _read_text(root_path / "webapp" / "src" / "lib" / "api.ts")
    bot = _read_text(root_path / "portal_bot" / "bot.py")
    helpbot = _read_text(root_path / "portal_bot" / "helpbot.py")
    runtime = _read_text(
        client_path
        / "packages"
        / "app_shell"
        / "lib"
        / "app_first_runtime_bootstrap.dart"
    )
    app_shell = _read_text(
        client_path / "packages" / "app_shell" / "lib" / "app_shell.dart"
    )

    checks: list[dict[str, Any]] = []

    platform_endpoints = (
        '/api/client/session/start-trial',
        '/api/client/profile/managed',
        '/api/redeem',
        '/api/client/cabinet-token',
        '/api/auth/cabinet-handoff/exchange',
        '/api/client/telegram/link',
        '/api/channel/subscriber/check',
        '/api/bonuses/channel/claim',
        '/api/bonuses/summary',
        '/api/bonuses/history',
        '/api/tickets',
        '/api/tickets/uploads',
        '/api/tickets/{ticket_id}',
        '/api/tickets/{ticket_id}/messages',
    )
    checks.append(
        _check(
            check_id="platform_app_first_endpoints",
            title="Platform exposes app-first account, cabinet, bonus, and ticket endpoints",
            evidence="portal_bot/api.py",
            missing=_missing_needles(api, platform_endpoints),
        )
    )

    client_adapter_contract = (
        '/api/client/session/start-trial',
        '/api/client/profile/managed',
        '/api/redeem',
        '/api/client/cabinet-token',
        '/api/client/telegram/link',
        '/api/channel/subscriber/check',
        '/api/bonuses/channel/claim',
        '/api/bonuses/summary',
        '/api/bonuses/history',
        '/api/tickets?limit=',
        '/api/tickets/$ticketId',
        '/api/tickets/$ticketId/messages',
        'AppFirstSupportTicketService',
    )
    checks.append(
        _check(
            check_id="client_app_first_adapter",
            title="Client runtime adapter calls the same app-first contracts",
            evidence="POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart",
            missing=_missing_needles(runtime, client_adapter_contract),
        )
    )

    webapp_contract = (
        '/api/auth/cabinet-handoff/exchange',
        '/api/tickets',
        '/api/tickets/uploads',
        '/api/tickets/${ticketId}',
        '/api/tickets/${ticketId}/messages',
        '/api/client/telegram/link',
    )
    checks.append(
        _check(
            check_id="webapp_cabinet_and_support",
            title="Cabinet exchanges app handoff tokens and continues support tickets",
            evidence="webapp/src/lib/api.ts",
            missing=_missing_needles(webapp_api, webapp_contract),
        )
    )

    telegram_bonus_platform = (
        '/api/client/telegram/link',
        '/api/channel/subscriber/check',
        '/api/bonuses/channel/claim',
        'channel_bonus',
    )
    telegram_bonus_client = (
        '/api/client/telegram/link',
        '/api/channel/subscriber/check',
        '/api/bonuses/channel/claim',
    )
    telegram_missing = _missing_needles(
        api, telegram_bonus_platform
    ) + _missing_needles(runtime, telegram_bonus_client)
    checks.append(
        _check(
            check_id="telegram_bonus_contract",
            title="Telegram link/check/claim stays available in platform and client",
            evidence="portal_bot/api.py + POKROV-app runtime adapter",
            missing=telegram_missing,
        )
    )

    support_platform = (
        '@app.get("/api/tickets")',
        '@app.post("/api/tickets/uploads")',
        '@app.post("/api/tickets")',
        '@app.get("/api/tickets/{ticket_id}")',
        '@app.post("/api/tickets/{ticket_id}/messages")',
    )
    support_client = (
        'abstract interface class SupportTicketService',
        'class AppFirstSupportTicketService',
        '/api/tickets?limit=',
        '/api/tickets/$ticketId',
        '/api/tickets/$ticketId/messages',
    )
    support_webapp = (
        'fetchTickets',
        'createTicket',
        'uploadTicketAttachment',
        'addTicketMessage',
    )
    support_missing = (
        _missing_needles(api, support_platform)
        + _missing_needles(runtime, support_client)
        + _missing_needles(webapp_api, support_webapp)
    )
    checks.append(
        _check(
            check_id="support_ticket_contract",
            title="App, cabinet, and bots have real ticket-backed support parity",
            evidence="portal_bot/api.py + webapp api + POKROV-app runtime adapter",
            missing=support_missing,
        )
    )

    safe_redeem_needles_api = (
        '@app.post("/api/redeem")',
        'subscription_link_not_redeem_code',
        'connect.pokrov.space',
    )
    safe_redeem_needles_app = (
        '_looksLikeSubscriptionOrProxyLink',
        'connect.pokrov.space',
        'vless://',
        'vmess://',
        'trojan://',
    )
    safe_redeem_missing = _missing_needles(
        api, safe_redeem_needles_api
    ) + _missing_needles(app_shell, safe_redeem_needles_app)
    checks.append(
        _check(
            check_id="safe_redeem_guard",
            title="Raw connection links are rejected before account restore/redeem",
            evidence="portal_bot/api.py + POKROV-app app_shell.dart",
            missing=safe_redeem_missing,
        )
    )

    bot_needles = (
        'BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot")',
        'SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or "pokrov_supportbot")',
        'Command("cabinet")',
        'Command("support")',
        'Command("redeem")',
        'gift_redeem_prompt',
    )
    helpbot_needles = (
        'Dedicated support intake bot.',
        'MAIN_BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot")',
        'ticket_new',
        'ticket_my',
    )
    bot_missing = _missing_needles(bot, bot_needles) + _missing_needles(
        helpbot, helpbot_needles
    )
    checks.append(
        _check(
            check_id="bot_entrypoints_present",
            title="Telegram bot entrypoints remain present for cabinet, support, and redeem fallback",
            evidence="portal_bot/bot.py + portal_bot/helpbot.py",
            missing=bot_missing,
        )
    )

    checks.append(
        _manual_check(
            "manual_real_telegram_parity",
            "Real Telegram bot smoke: same user can open cabinet, support, and redeem fallback",
            "Requires owner Telegram account and live bot tokens; keep as MANUAL_OWNER_TEST.",
        )
    )
    checks.append(
        _manual_check(
            "manual_live_account_parity",
            "Live account parity: app, cabinet, and bot show the same access/subscription state",
            "Requires live app session, cabinet session, and bot account; keep as MANUAL_OWNER_TEST.",
        )
    )

    failed = [check for check in checks if check["required"] and check["status"] != "PASS"]
    manual = [check for check in checks if check["status"] == "MANUAL_OWNER_TEST"]
    return {
        "ok": not failed,
        "root": str(root_path),
        "client_root": str(client_path),
        "summary": {
            "checks": len(checks),
            "passed": sum(1 for check in checks if check["status"] == "PASS"),
            "failed": len(failed),
            "manual_owner_tests": len(manual),
        },
        "checks": checks,
    }


def _print_text(report: dict[str, Any]) -> None:
    print("POKROV app/bot parity smoke")
    print(f"root: {report['root']}")
    print(f"client: {report['client_root']}")
    print(
        "summary: "
        f"{report['summary']['passed']} passed, "
        f"{report['summary']['failed']} failed, "
        f"{report['summary']['manual_owner_tests']} manual owner tests"
    )
    for check in report["checks"]:
        print(f"- {check['status']}: {check['id']} - {check['title']}")
        if check["missing"]:
            for missing in check["missing"]:
                print(f"  missing: {missing}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static app/bot/cabinet parity smoke for POKROV app-first contracts."
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Platform repository root.",
    )
    parser.add_argument(
        "--client-root",
        default=str(Path(__file__).resolve().parents[2] / "POKROV-app"),
        help="POKROV-app repository root.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)

    report = build_report(Path(args.root), Path(args.client_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
