from __future__ import annotations

from urllib.parse import urlparse

from config import Settings
from shared_surface_facts import get_public_urls


def _canonical_connect_base_url() -> str:
    public_urls = get_public_urls()
    surfaces = public_urls.get("surfaces", {})
    return _safe_public_url(str(surfaces.get("connect") or "").strip()) or "https://connect.pokrov.space"


def _safe_public_url(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}".rstrip("/")
    return text.rstrip("/")


def public_connect_base_url() -> str:
    configured = _safe_public_url(getattr(Settings, "PUBLIC_CONNECT_URL", ""))
    if configured:
        return configured
    domain = str(getattr(Settings, "PUBLIC_CONNECT_DOMAIN", "") or "").strip()
    if domain:
        return f"https://{domain}".rstrip("/")
    return _canonical_connect_base_url()


def public_connect_host() -> str:
    configured = urlparse(public_connect_base_url())
    if configured.hostname:
        return configured.hostname.lower()
    canonical = urlparse(_canonical_connect_base_url())
    if canonical.hostname:
        return canonical.hostname.lower()
    return "connect.pokrov.space"


def build_subscription_url(token_or_id: str | int) -> str:
    target = str(token_or_id or "").strip()
    if not target or target.isdigit():
        return ""
    return f"{public_connect_base_url()}/s8Kx2mP7qR4wT/{target}"
