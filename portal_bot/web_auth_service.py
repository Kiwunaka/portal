from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


SESSION_TTL_SECONDS = max(300, int(os.getenv("WEBAPP_SESSION_TTL_SECONDS", "86400")))


def _secret() -> str:
    return (
        os.getenv("WEBAPP_SESSION_SECRET")
        or os.getenv("TELEGRAM_WEB_LOGIN_SECRET")
        or os.getenv("BOT_TOKEN")
        or ""
    ).strip()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - (len(data) % 4)) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _sign(text: str) -> str:
    secret = _secret()
    if not secret:
        return ""
    return hmac.new(secret.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()


def create_web_session_token(*, tg_id: int, username: str | None = None) -> str:
    now = int(time.time())
    payload = {
        "id": int(tg_id),
        "username": (username or "").strip() or None,
        "iat": now,
        "exp": now + SESSION_TTL_SECONDS,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    sig = _sign(body)
    if not sig:
        return ""
    return f"{body}.{sig}"


def verify_web_session_token(token: str) -> dict[str, Any] | None:
    raw = (token or "").strip()
    if "." not in raw:
        return None
    body, sig = raw.rsplit(".", 1)
    expected = _sign(body)
    if not expected or not hmac.compare_digest(expected, sig):
        return None
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        tg_id = int(payload.get("id") or 0)
        exp = int(payload.get("exp") or 0)
    except Exception:
        return None
    if tg_id <= 0 or exp <= int(time.time()):
        return None
    return {"id": tg_id, "username": payload.get("username")}


def verify_telegram_login_payload(*, payload: dict[str, Any], bot_token: str, max_age_seconds: int = 86400) -> dict[str, Any] | None:
    """
    Verification for Telegram Login Widget payload.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    data = {str(k): str(v) for k, v in (payload or {}).items() if k != "hash" and v is not None}
    check_hash = str((payload or {}).get("hash") or "").strip()
    if not check_hash or not bot_token:
        return None
    try:
        auth_date = int(data.get("auth_date") or 0)
    except Exception:
        return None
    now = int(time.time())
    if auth_date <= 0 or now - auth_date > max(60, int(max_age_seconds)):
        return None
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    calc = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, check_hash):
        return None
    try:
        tg_id = int(data.get("id") or 0)
    except Exception:
        return None
    if tg_id <= 0:
        return None
    return {
        "id": tg_id,
        "username": (data.get("username") or "").strip() or None,
        "first_name": (data.get("first_name") or "").strip() or None,
        "last_name": (data.get("last_name") or "").strip() or None,
        "photo_url": (data.get("photo_url") or "").strip() or None,
        "auth_date": auth_date,
    }
