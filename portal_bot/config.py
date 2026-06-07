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
    PLATFORM_BRAND: str = (os.getenv("PLATFORM_BRAND") or "POKROV").strip()
    CLIENT_BRAND: str = (os.getenv("CLIENT_BRAND") or "POKROV Network").strip()
    MAIN_BOT_USERNAME: str = (os.getenv("MAIN_BOT_USERNAME") or os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
    CONTACT_EMAIL: str = (os.getenv("CONTACT_EMAIL") or "support@pokrov.space").strip()
    ENTERPRISE_EMAIL: str = (os.getenv("ENTERPRISE_EMAIL") or "enterprise@pokrov.space").strip()

    # Public domains:
    # - API/callbacks/subscription live on PUBLIC_API_DOMAIN.
    # - Marketing + WebApp live on PUBLIC_WEB_DOMAIN.
    PUBLIC_API_DOMAIN: str = (
        os.getenv("PUBLIC_API_DOMAIN")
        or os.getenv("HOST_DOMAIN")
        or os.getenv("DOMAIN")
        or "api.pokrov.space"
    )
    PUBLIC_WEB_DOMAIN: str = (os.getenv("PUBLIC_WEB_DOMAIN") or "pokrov.space").strip()
    PUBLIC_CONNECT_DOMAIN: str = (os.getenv("PUBLIC_CONNECT_DOMAIN") or "connect.pokrov.space").strip()

    # Backward-compatible alias used by older scripts.
    HOST_DOMAIN: str = PUBLIC_API_DOMAIN
    PUBLIC_API_BASE_URL: str = os.getenv("PUBLIC_API_BASE_URL", f"https://{PUBLIC_API_DOMAIN}")
    PUBLIC_CONNECT_URL: str = os.getenv("PUBLIC_CONNECT_URL", f"https://{PUBLIC_CONNECT_DOMAIN}").strip()
    PUBLIC_PAY_DOMAIN: str = (os.getenv("PUBLIC_PAY_DOMAIN") or "pay.pokrov.space").strip()
    PUBLIC_PAY_BASE_URL: str = os.getenv("PUBLIC_PAY_BASE_URL", f"https://{PUBLIC_PAY_DOMAIN}").strip()

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
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://app.pokrov.space/?v=20260320")
    WEBAPP_SESSION_SECRET: str = os.getenv("WEBAPP_SESSION_SECRET", "").strip()
    SUPPORT_BOT_USERNAME: str = (os.getenv("SUPPORT_BOT_USERNAME") or os.getenv("SUPPORT_USERNAME") or "pokrov_supportbot").lstrip("@")
    FEEDBACK_BOT_USERNAME: str = (
        os.getenv("FEEDBACK_BOT_USERNAME")
        or os.getenv("FEEDBACK_USERNAME")
        or "pokrov_feedbackbot"
    ).lstrip("@")
    NEWS_CHANNEL_ID: str = os.getenv("NEWS_CHANNEL_ID", "@pokrov_vpn")
    NEWS_CHANNEL_URL: str = (os.getenv("NEWS_CHANNEL_URL") or "https://t.me/pokrov_vpn").strip()
    PAY_CHECKOUT_URL: str = os.getenv("PAY_CHECKOUT_URL", f"{PUBLIC_PAY_BASE_URL}/checkout").strip()
    PAY_SUCCESS_URL: str = os.getenv("PAY_SUCCESS_URL", f"{PUBLIC_PAY_BASE_URL}/success").strip()
    PAY_FAIL_URL: str = os.getenv("PAY_FAIL_URL", f"{PUBLIC_PAY_BASE_URL}/fail").strip()
    PAY_RESULT_BASE_PATH: str = os.getenv("PAY_RESULT_BASE_PATH", "/api/payments/result").strip()
    PAY_REFUND_BASE_PATH: str = os.getenv("PAY_REFUND_BASE_PATH", "/api/payments/refund").strip()
    PAY_CHARGEBACK_BASE_PATH: str = os.getenv("PAY_CHARGEBACK_BASE_PATH", "/api/payments/chargeback").strip()
    FREEKASSA_SIGNING_SECRET: str = os.getenv("FREEKASSA_SIGNING_SECRET", "").strip()
    RUB_CHECKOUT_ENABLED: bool = env_bool("RUB_CHECKOUT_ENABLED", default=False)
    BOT_RUB_BUTTON_ENABLED: bool = env_bool("BOT_RUB_BUTTON_ENABLED", default=False)
    CHANNEL_SPEED_BUMP_ENABLED: bool = env_bool("CHANNEL_SPEED_BUMP_ENABLED", default=False)
    CHECKOUT_WIDGET_ENABLED: bool = env_bool("CHECKOUT_WIDGET_ENABLED", default=False)
    CHECKOUT_TICKET_SECRET: str = os.getenv("CHECKOUT_TICKET_SECRET", "").strip()
    CHECKOUT_TICKET_TTL_SECONDS: int = env_int("CHECKOUT_TICKET_TTL_SECONDS", 900)
    FREE_SPEED_BUMP_UNSUB_KBPS: int = env_int("FREE_SPEED_BUMP_UNSUB_KBPS", 1250)
    CHANNEL_SUBSCRIBER_CAMPAIGN_KEY: str = os.getenv("CHANNEL_SUBSCRIBER_CAMPAIGN_KEY", "channel_subscriber_v1").strip()

    FK_SITE_SHOP_ID: str = os.getenv("FK_SITE_SHOP_ID", "").strip()
    FK_SITE_API_KEY: str = os.getenv("FK_SITE_API_KEY", "").strip()
    FK_SITE_SECRET_WORD_1: str = os.getenv("FK_SITE_SECRET_WORD_1", "").strip()
    FK_SITE_SECRET_WORD_2: str = os.getenv("FK_SITE_SECRET_WORD_2", "").strip()
    FK_BOT_SHOP_ID: str = os.getenv("FK_BOT_SHOP_ID", "").strip()
    FK_BOT_API_KEY: str = os.getenv("FK_BOT_API_KEY", "").strip()
    FK_BOT_SECRET_WORD_1: str = os.getenv("FK_BOT_SECRET_WORD_1", "").strip()
    FK_BOT_SECRET_WORD_2: str = os.getenv("FK_BOT_SECRET_WORD_2", "").strip()
    FK_API_BASE_URL: str = os.getenv("FK_API_BASE_URL", "https://api.fk.life/v1").strip()
    FK_NOTIFY_IP_ALLOWLIST: str = os.getenv("FK_NOTIFY_IP_ALLOWLIST", "").strip()

    APP_ANDROID_PLAY_URL: str = os.getenv("APP_ANDROID_PLAY_URL", "").strip()
    APP_ANDROID_APK_URL: str = os.getenv("APP_ANDROID_APK_URL", "").strip()
    APP_ANDROID_MIRROR_URL: str = os.getenv("APP_ANDROID_MIRROR_URL", "").strip()
    APP_WINDOWS_EXE_URL: str = os.getenv("APP_WINDOWS_EXE_URL", "").strip()
    APP_WINDOWS_MIRROR_URL: str = os.getenv("APP_WINDOWS_MIRROR_URL", "").strip()
    APP_DOCS_URL: str = os.getenv("APP_DOCS_URL", "").strip()
    APP_RELEASE_CHANNEL: str = os.getenv("APP_RELEASE_CHANNEL", "beta").strip()
    APP_ANDROID_VERSION: str = os.getenv("APP_ANDROID_VERSION", "").strip()
    APP_ANDROID_MIN_SUPPORTED_VERSION: str = os.getenv("APP_ANDROID_MIN_SUPPORTED_VERSION", "").strip()
    APP_ANDROID_SHA256: str = os.getenv("APP_ANDROID_SHA256", "").strip()
    APP_ANDROID_SIZE_BYTES: int = env_int("APP_ANDROID_SIZE_BYTES", 0)
    APP_ANDROID_RELEASE_NOTES: str = os.getenv("APP_ANDROID_RELEASE_NOTES", "").strip()
    APP_ANDROID_RELEASE_NOTES_URL: str = os.getenv("APP_ANDROID_RELEASE_NOTES_URL", "").strip()
    APP_ANDROID_PUBLISHED_AT: str = os.getenv("APP_ANDROID_PUBLISHED_AT", "").strip()
    APP_WINDOWS_VERSION: str = os.getenv("APP_WINDOWS_VERSION", "").strip()
    APP_WINDOWS_MIN_SUPPORTED_VERSION: str = os.getenv("APP_WINDOWS_MIN_SUPPORTED_VERSION", "").strip()
    APP_WINDOWS_SHA256: str = os.getenv("APP_WINDOWS_SHA256", "").strip()
    APP_WINDOWS_SIZE_BYTES: int = env_int("APP_WINDOWS_SIZE_BYTES", 0)
    APP_WINDOWS_RELEASE_NOTES: str = os.getenv("APP_WINDOWS_RELEASE_NOTES", "").strip()
    APP_WINDOWS_RELEASE_NOTES_URL: str = os.getenv("APP_WINDOWS_RELEASE_NOTES_URL", "").strip()
    APP_WINDOWS_PUBLISHED_AT: str = os.getenv("APP_WINDOWS_PUBLISHED_AT", "").strip()
    WEBAPP_ENABLE_HAPTIC: bool = env_bool("WEBAPP_ENABLE_HAPTIC", default=True)
    WEBAPP_ENABLE_LOTTIE: bool = env_bool("WEBAPP_ENABLE_LOTTIE", default=True)
    WEBAPP_DEV_AUTH: bool = env_bool("WEBAPP_DEV_AUTH", default=False)
    WEBAPP_DEV_TG_ID: int = env_int("WEBAPP_DEV_TG_ID", 0)
