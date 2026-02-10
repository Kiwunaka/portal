from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return int(v)


def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


class Settings:
    # Core
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = env_int("ADMIN_ID", 0)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///portal.db")

    # Public URL used in subscription links.
    # Keep defaults deploy-safe (prod works even if env is partially missing).
    HOST_DOMAIN: str = os.getenv("HOST_DOMAIN") or os.getenv("DOMAIN") or "kiwunaka.space"
    PUBLIC_API_BASE_URL: str = os.getenv("PUBLIC_API_BASE_URL", f"https://{HOST_DOMAIN}:2096")

    # Legacy single-node fallback (when `nodes` table is empty)
    LEGACY_NODE_CODE: str = os.getenv("LEGACY_NODE_CODE", "default")
    LEGACY_NODE_NAME: str = os.getenv("LEGACY_NODE_NAME", "Default")
    # Legacy single-node fallback host (kept for backward compatibility)
    # NOTE: uses the same HOST_DOMAIN default as above.
    VLESS_PORT: int = env_int("VLESS_PORT", 443)
    VLESS_SNI: str = os.getenv("VLESS_SNI", "yahoo.com")
    VLESS_PBK: str = os.getenv("VLESS_PBK", "")
    VLESS_SID: str = os.getenv("VLESS_SID", "")
    VLESS_FP: str = os.getenv("VLESS_FP", "firefox")
    VLESS_FLOW: str = os.getenv("VLESS_FLOW", "xtls-rprx-vision")

    # Panel (legacy)
    PANEL_BASE_URL: str = os.getenv("PANEL_URL", "http://127.0.0.1:15739")
    PANEL_PATH: str = os.getenv("PANEL_PATH", "")
    PANEL_USER: str = os.getenv("PANEL_USER", "admin")
    PANEL_PASS: str = os.getenv("PANEL_PASS", "")
    INBOUND_ID: int = env_int("INBOUND_ID", 4)

    # WebApp (Telegram Mini App)
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", f"https://{HOST_DOMAIN}:8444/webapp/?v=20260207")
    SUPPORT_BOT_USERNAME: str = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "portal_privacy_helpbot").lstrip("@")
    NEWS_CHANNEL_ID: str = os.getenv("NEWS_CHANNEL_ID", "@portal_news_channel")
    PAY_CHECKOUT_URL: str = os.getenv("PAY_CHECKOUT_URL", "").strip()
    WEBAPP_ENABLE_HAPTIC: bool = env_bool("WEBAPP_ENABLE_HAPTIC", default=True)
    WEBAPP_ENABLE_LOTTIE: bool = env_bool("WEBAPP_ENABLE_LOTTIE", default=True)
    WEBAPP_DEV_AUTH: bool = env_bool("WEBAPP_DEV_AUTH", default=False)
    WEBAPP_DEV_TG_ID: int = env_int("WEBAPP_DEV_TG_ID", 0)
