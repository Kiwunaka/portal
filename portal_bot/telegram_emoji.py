from __future__ import annotations

import html
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramEmoji:
    fallback: str
    custom_emoji_id: str
    pack: str


# Curated from the public packs in Telegram Web on 2026-07-23. Keep only
# navigation symbols that remain understandable without the surrounding pack.
_CURATED_EMOJI: dict[str, TelegramEmoji] = {
    "brand": TelegramEmoji("🛡", "5197288647275071607", "FinanceEmoji"),
    "device": TelegramEmoji("💻", "5213323619911868787", "Decoration_Pack"),
    "phone": TelegramEmoji("📱", "5220069871072583573", "Decoration_Pack"),
    "free": TelegramEmoji("🆓", "5406756500108501710", "NewsEmoji"),
    "payment": TelegramEmoji("💳", "5445353829304387411", "FinanceEmoji"),
    "success": TelegramEmoji("✅", "5217497254381754877", "Decoration_Pack"),
    "support": TelegramEmoji("🆘", "5220108512893344933", "Decoration_Pack"),
    "cabinet": TelegramEmoji("🏠", "5416041192905265756", "NewsEmoji"),
    "settings": TelegramEmoji("⚙️", "5341715473882955310", "NewsEmoji"),
    "world": TelegramEmoji("🌐", "5447410659077661506", "NewsEmoji"),
    "key": TelegramEmoji("🔑", "5307843983102204243", "TONEmoji"),
    "link": TelegramEmoji("🔗", "5440410042773824003", "TONEmoji"),
    "download": TelegramEmoji("📥", "5443127283898405358", "FinanceEmoji"),
    "faq": TelegramEmoji("❓", "5436113877181941026", "NewsEmoji"),
    "warning": TelegramEmoji("⚠️", "5447644880824181073", "NewsEmoji"),
    "lightning": TelegramEmoji("⚡️", "5456140674028019486", "NewsEmoji"),
    "rocket": TelegramEmoji("🚀", "5195033767969839232", "FinanceEmoji"),
    "target": TelegramEmoji("🎯", "5461009483314517035", "TONEmoji"),
    "diamond": TelegramEmoji("💎", "5427168083074628963", "NewsEmoji"),
    "crown": TelegramEmoji("👑", "5217822164362739968", "NewsEmoji"),
    "message": TelegramEmoji("💬", "5443038326535759644", "NewsEmoji"),
    "info": TelegramEmoji("ℹ️", "5334544901428229844", "NewsEmoji"),
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _valid_custom_emoji_id(value: str | None) -> str | None:
    candidate = str(value or "").strip()
    if candidate.isdigit() and 8 <= len(candidate) <= 32:
        return candidate
    return None


def custom_emoji_enabled() -> bool:
    return _env_bool("TG_CUSTOM_EMOJI_ENABLED", default=True)


def emoji_spec(key: str) -> TelegramEmoji:
    try:
        return _CURATED_EMOJI[str(key or "").strip().lower()]
    except KeyError as exc:
        raise ValueError(f"unknown Telegram emoji key: {key!r}") from exc


def custom_emoji_id(key: str) -> str | None:
    if not custom_emoji_enabled():
        return None
    normalized = str(key or "").strip().lower()
    spec = emoji_spec(normalized)
    env_name = f"TG_EMOJI_{normalized.upper()}_ID"
    override = _valid_custom_emoji_id(os.getenv(env_name))
    if os.getenv(env_name) is not None:
        return override
    return _valid_custom_emoji_id(spec.custom_emoji_id)


def button_label(key: str, text: str, *, icon_supported: bool = True) -> str:
    spec = emoji_spec(key)
    label = str(text or "").strip()
    if icon_supported and custom_emoji_id(key):
        return label
    return f"{spec.fallback} {label}".strip()


def rich_emoji(key: str) -> str:
    spec = emoji_spec(key)
    emoji_id = custom_emoji_id(key)
    fallback = html.escape(spec.fallback)
    if not emoji_id:
        return fallback
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def curated_emoji_manifest() -> dict[str, dict[str, str]]:
    """Return a safe copy for tests and operator diagnostics."""
    return {
        key: {
            "fallback": spec.fallback,
            "custom_emoji_id": spec.custom_emoji_id,
            "pack": spec.pack,
        }
        for key, spec in _CURATED_EMOJI.items()
    }
