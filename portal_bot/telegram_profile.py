from __future__ import annotations

from typing import Any


BOT_PROFILE_NAME = "POKROV VPN"
BOT_PROFILE_SHORT_DESCRIPTION = "POKROV VPN для Android и Windows. 5 дней без карты."
BOT_PROFILE_DESCRIPTION = (
    "POKROV VPN (ВПН) для Android и Windows.\n\n"
    "5 дней бесплатно без карты. Установите приложение, войдите в аккаунт и нажмите «Подключить».\n\n"
    "Поддержка: @pokrov_supportbot\n"
    "Отзывы: @pokrov_feedbackbot\n"
    "Новости: @pokrov_vpn"
)

BOT_PROFILE_NAME_LIMIT = 64
BOT_PROFILE_SHORT_DESCRIPTION_LIMIT = 120
BOT_PROFILE_DESCRIPTION_LIMIT = 512

TELEGRAM_PROFILE_WEBAPP_MENU_TEXT = "POKROV"
TELEGRAM_PROFILE_WEBAPP_MENU_URL = "https://app.pokrov.space/"

OFFICIAL_TELEGRAM_USERNAMES = (
    "@pokrov_vpnbot",
    "@pokrov_supportbot",
    "@pokrov_feedbackbot",
    "@pokrov_vpn",
)


def expected_profile_payload() -> dict[str, str]:
    return {
        "name": BOT_PROFILE_NAME,
        "short_description": BOT_PROFILE_SHORT_DESCRIPTION,
        "description": BOT_PROFILE_DESCRIPTION,
    }


def expected_public_command_payload() -> list[dict[str, str]]:
    return [
        {"command": "start", "description": "Открыть главное меню"},
        {"command": "cabinet", "description": "Открыть кабинет"},
        {"command": "support", "description": "Написать в поддержку"},
        {"command": "help", "description": "Открыть частые вопросы"},
        {"command": "promo", "description": "Активировать промокод"},
        {"command": "redeem", "description": "Активировать ключ доступа"},
    ]


def expected_public_command_names() -> list[str]:
    return [item["command"] for item in expected_public_command_payload()]


def expected_webapp_menu_button_payload() -> dict[str, Any]:
    return {
        "type": "web_app",
        "text": TELEGRAM_PROFILE_WEBAPP_MENU_TEXT,
        "web_app": {"url": TELEGRAM_PROFILE_WEBAPP_MENU_URL},
    }


def validate_profile_spec() -> list[str]:
    errors: list[str] = []
    if len(BOT_PROFILE_NAME) > BOT_PROFILE_NAME_LIMIT:
        errors.append("name exceeds Telegram Bot API 64 character limit")
    if len(BOT_PROFILE_SHORT_DESCRIPTION) > BOT_PROFILE_SHORT_DESCRIPTION_LIMIT:
        errors.append("short_description exceeds Telegram Bot API 120 character limit")
    if len(BOT_PROFILE_DESCRIPTION) > BOT_PROFILE_DESCRIPTION_LIMIT:
        errors.append("description exceeds Telegram Bot API 512 character limit")

    required_fragments = (
        "POKROV VPN",
        "Android",
        "Windows",
        "5 дней",
        "без карты",
        "@pokrov_supportbot",
        "@pokrov_feedbackbot",
        "@pokrov_vpn",
    )
    combined = "\n".join(expected_profile_payload().values())
    for fragment in required_fragments:
        if fragment not in combined:
            errors.append(f"profile copy is missing {fragment!r}")
    return errors
