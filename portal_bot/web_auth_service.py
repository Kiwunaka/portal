from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

import aiohttp
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


TELEGRAM_OAUTH_AUTHORIZE_URL = "https://oauth.telegram.org/auth"
TELEGRAM_OAUTH_TOKEN_URL = "https://oauth.telegram.org/token"
TELEGRAM_OAUTH_JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
TELEGRAM_OAUTH_ISSUER = "https://oauth.telegram.org"
TELEGRAM_OAUTH_SCOPES = os.getenv("TELEGRAM_OAUTH_SCOPES", "openid profile telegram:bot_access").strip() or "openid profile"
TELEGRAM_OAUTH_STATE_TTL_SECONDS = max(120, int(os.getenv("TELEGRAM_OAUTH_STATE_TTL_SECONDS", "900")))
TELEGRAM_OAUTH_CLOCK_SKEW_SECONDS = max(0, int(os.getenv("TELEGRAM_OAUTH_CLOCK_SKEW_SECONDS", "60")))
_JWKS_CACHE_SECONDS_DEFAULT = max(60, int(os.getenv("TELEGRAM_OAUTH_JWKS_CACHE_SECONDS", "3600")))
_jwks_cache: dict[str, Any] = {"value": None, "expires_at": 0}

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


def _clean_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _telegram_oidc_client_id() -> str:
    explicit = str(
        os.getenv("TELEGRAM_OAUTH_CLIENT_ID")
        or os.getenv("TELEGRAM_OIDC_CLIENT_ID")
        or ""
    ).strip()
    if explicit:
        return explicit
    bot_token = str(os.getenv("BOT_TOKEN") or "").strip()
    prefix = bot_token.split(":", 1)[0].strip()
    return prefix if prefix.isdigit() else ""


def _telegram_oidc_client_secret() -> str:
    return str(
        os.getenv("TELEGRAM_OAUTH_CLIENT_SECRET")
        or os.getenv("TELEGRAM_OIDC_CLIENT_SECRET")
        or ""
    ).strip()


def _telegram_oidc_redirect_uri() -> str:
    raw = str(
        os.getenv("TELEGRAM_OAUTH_REDIRECT_URI")
        or os.getenv("TELEGRAM_OIDC_REDIRECT_URI")
        or os.getenv("WEBAPP_URL")
        or "https://app.pokrov.space/"
    ).strip()
    parsed = urlsplit(raw)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    path = parsed.path or "/"
    if not netloc:
        raise RuntimeError("Telegram OAuth redirect URI is not configured")
    return urlunsplit((scheme, netloc, path, "", ""))


def _require_telegram_oidc_config() -> tuple[str, str, str]:
    client_id = _telegram_oidc_client_id()
    client_secret = _telegram_oidc_client_secret()
    redirect_uri = _telegram_oidc_redirect_uri()
    if not client_id:
        raise RuntimeError("Telegram OAuth client ID is not configured")
    if not client_secret:
        raise RuntimeError("Telegram OAuth client secret is not configured")
    return client_id, client_secret, redirect_uri


def _pkce_verifier() -> str:
    verifier = secrets.token_urlsafe(32).replace("-", "A").replace("_", "B")
    return verifier if len(verifier) >= 43 else verifier.ljust(43, "x")


def _pkce_challenge(verifier: str) -> str:
    return _b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def create_telegram_oidc_state_token(*, redirect_uri: str, code_verifier: str | None = None) -> str:
    verifier = str(code_verifier or _pkce_verifier()).strip()
    if len(verifier) < 43:
        verifier = verifier.ljust(43, "x")
    now = int(time.time())
    payload = {
        "t": "to",
        "c": secrets.token_urlsafe(12),
        "v": verifier,
        "e": now + TELEGRAM_OAUTH_STATE_TTL_SECONDS,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    sig = _sign(body)
    if not sig:
        return ""
    return f"{body}.{sig}"


def verify_telegram_oidc_state_token(token: str) -> dict[str, Any] | None:
    raw = str(token or "").strip()
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
    token_type = str(payload.get("type") or payload.get("t") or "")
    if token_type not in {"telegram_oidc", "to"}:
        return None
    try:
        exp = int(payload.get("exp") or payload.get("e") or 0)
    except Exception:
        return None
    redirect_uri = str(payload.get("redirect_uri") or payload.get("r") or "").strip()
    if not redirect_uri:
        try:
            redirect_uri = _telegram_oidc_redirect_uri()
        except RuntimeError:
            return None
    verifier = str(payload.get("code_verifier") or payload.get("v") or "").strip()
    if exp <= int(time.time()) or not redirect_uri or len(verifier) < 43:
        return None
    return {
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
        "csrf": str(payload.get("csrf") or payload.get("c") or "").strip(),
    }


def build_telegram_oidc_authorize_url() -> dict[str, str]:
    client_id, _client_secret, redirect_uri = _require_telegram_oidc_config()
    state_token = create_telegram_oidc_state_token(redirect_uri=redirect_uri)
    if not state_token:
        raise RuntimeError("Telegram OAuth state signing is not configured")
    verified_state = verify_telegram_oidc_state_token(state_token)
    if not verified_state:
        raise RuntimeError("Telegram OAuth state validation failed")
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": TELEGRAM_OAUTH_SCOPES,
            "state": state_token,
            "code_challenge": _pkce_challenge(str(verified_state["code_verifier"])),
            "code_challenge_method": "S256",
        }
    )
    return {
        "auth_url": f"{TELEGRAM_OAUTH_AUTHORIZE_URL}?{query}",
        "redirect_uri": redirect_uri,
        "state": state_token,
    }


def _jwt_json(segment: str) -> dict[str, Any]:
    decoded = _b64url_decode(segment)
    parsed = json.loads(decoded.decode("utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def _jwk_cache_ttl(headers: "aiohttp.typedefs.LooseHeaders") -> int:
    cache_control = str(headers.get("Cache-Control") or headers.get("cache-control") or "").strip()
    match = re.search(r"max-age=(\d+)", cache_control)
    if match:
        try:
            return max(60, int(match.group(1)))
        except Exception:
            return _JWKS_CACHE_SECONDS_DEFAULT
    return _JWKS_CACHE_SECONDS_DEFAULT


async def fetch_telegram_oidc_jwks(*, force: bool = False) -> dict[str, Any]:
    now = int(time.time())
    cached_value = _jwks_cache.get("value")
    cached_exp = int(_jwks_cache.get("expires_at") or 0)
    if not force and cached_value and cached_exp > now:
        return cached_value

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(TELEGRAM_OAUTH_JWKS_URL) as response:
            if response.status != 200:
                text = (await response.text()).strip()
                raise RuntimeError(text or f"Telegram JWKS request failed: {response.status}")
            payload = await response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("Telegram JWKS payload is invalid")
            _jwks_cache["value"] = payload
            _jwks_cache["expires_at"] = now + _jwk_cache_ttl(response.headers)
            return payload


def validate_telegram_oidc_id_token(*, id_token: str, client_id: str, jwks: dict[str, Any]) -> dict[str, Any]:
    parts = str(id_token or "").split(".")
    if len(parts) != 3:
        raise ValueError("Telegram ID token is invalid")
    header_b64, payload_b64, signature_b64 = parts
    header = _jwt_json(header_b64)
    claims = _jwt_json(payload_b64)
    if str(header.get("alg") or "") != "RS256":
        raise ValueError("Telegram ID token uses an unsupported algorithm")
    kid = str(header.get("kid") or "").strip()
    if not kid:
        raise ValueError("Telegram ID token is missing a key id")

    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list):
        raise ValueError("Telegram JWKS payload is invalid")
    jwk = next((row for row in keys if isinstance(row, dict) and str(row.get("kid") or "") == kid), None)
    if not jwk:
        raise ValueError("Telegram signing key was not found")
    if str(jwk.get("kty") or "") != "RSA":
        raise ValueError("Telegram signing key type is unsupported")

    try:
        n = int.from_bytes(_b64url_decode(str(jwk.get("n") or "")), "big")
        e = int.from_bytes(_b64url_decode(str(jwk.get("e") or "")), "big")
        public_key = rsa.RSAPublicNumbers(e=e, n=n).public_key()
        public_key.verify(
            _b64url_decode(signature_b64),
            f"{header_b64}.{payload_b64}".encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature as exc:
        raise ValueError("Telegram ID token signature is invalid") from exc
    except Exception as exc:
        raise ValueError("Telegram signing key is invalid") from exc

    now = int(time.time())
    try:
        exp = int(claims.get("exp") or 0)
        iat = int(claims.get("iat") or 0)
    except Exception as exc:
        raise ValueError("Telegram ID token claims are invalid") from exc
    if exp <= now - TELEGRAM_OAUTH_CLOCK_SKEW_SECONDS:
        raise ValueError("Telegram ID token has expired")
    if iat > now + TELEGRAM_OAUTH_CLOCK_SKEW_SECONDS:
        raise ValueError("Telegram ID token is not valid yet")
    if str(claims.get("iss") or "") != TELEGRAM_OAUTH_ISSUER:
        raise ValueError("Telegram ID token issuer is invalid")
    aud = claims.get("aud")
    valid_aud = False
    if isinstance(aud, str):
        valid_aud = aud == str(client_id)
    elif isinstance(aud, list):
        valid_aud = str(client_id) in {str(item) for item in aud}
    if not valid_aud:
        raise ValueError("Telegram ID token audience is invalid")
    try:
        tg_id = int(claims.get("id") or claims.get("sub") or 0)
    except Exception as exc:
        raise ValueError("Telegram ID token user is invalid") from exc
    if tg_id <= 0:
        raise ValueError("Telegram ID token user is invalid")

    verified = dict(claims)
    verified["id"] = tg_id
    verified["preferred_username"] = str(claims.get("preferred_username") or "").strip() or None
    return verified


async def exchange_telegram_oidc_code(*, code: str, state_token: str) -> dict[str, Any]:
    client_id, client_secret, _redirect_uri = _require_telegram_oidc_config()
    verified_state = verify_telegram_oidc_state_token(state_token)
    if not verified_state:
        raise ValueError("Telegram OAuth state is invalid or expired")

    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic "
        + base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii"),
    }
    token_body = urlencode(
        {
            "grant_type": "authorization_code",
            "code": str(code or "").strip(),
            "redirect_uri": str(verified_state["redirect_uri"]),
            "client_id": client_id,
            "code_verifier": str(verified_state["code_verifier"]),
        }
    )

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            TELEGRAM_OAUTH_TOKEN_URL,
            data=token_body,
            headers=token_headers,
        ) as response:
            if response.status != 200:
                text = (await response.text()).strip()
                raise RuntimeError(text or f"Telegram token exchange failed: {response.status}")
            token_payload = await response.json()
            if not isinstance(token_payload, dict):
                raise RuntimeError("Telegram token response is invalid")

    id_token = str(token_payload.get("id_token") or "").strip()
    if not id_token:
        raise RuntimeError("Telegram token response is missing id_token")
    jwks = await fetch_telegram_oidc_jwks()
    return validate_telegram_oidc_id_token(
        id_token=id_token,
        client_id=client_id,
        jwks=jwks,
    )


def create_web_session_token(
    *,
    tg_id: int,
    username: str | None = None,
    auth_type: str | None = None,
    auth_origin: str | None = None,
    email: str | None = None,
    ttl_seconds: int | None = None,
    purpose: str | None = None,
    account_id: str | None = None,
    session_id: str | None = None,
    device_id: str | None = None,
    auth_epoch: int | None = None,
    device_credential_version: int | None = None,
    scope: str | None = None,
    token_id: str | None = None,
) -> str:
    now = int(time.time())
    ttl = int(SESSION_TTL_SECONDS)
    if ttl_seconds is not None:
        try:
            ttl = max(60, int(ttl_seconds))
        except Exception:
            ttl = int(SESSION_TTL_SECONDS)
    payload = {
        "id": int(tg_id),
        "username": (username or "").strip() or None,
        "auth_type": (auth_type or "").strip() or None,
        "auth_origin": (auth_origin or "").strip() or None,
        "email": (email or "").strip().lower() or None,
        "purpose": (purpose or "").strip() or None,
        "account_id": (account_id or "").strip() or None,
        "session_id": (session_id or "").strip() or None,
        "device_id": (device_id or "").strip() or None,
        "auth_epoch": int(auth_epoch) if auth_epoch is not None else None,
        "device_credential_version": (
            int(device_credential_version) if device_credential_version is not None else None
        ),
        "scope": (scope or "").strip() or None,
        "token_id": (token_id or "").strip() or None,
        "iat": now,
        "exp": now + ttl,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    sig = _sign(body)
    if not sig:
        return ""
    return f"{body}.{sig}"


def inspect_web_session_token(token: str) -> tuple[dict[str, Any] | None, str | None]:
    raw = (token or "").strip()
    if "." not in raw:
        return None, "malformed"
    body, sig = raw.rsplit(".", 1)
    expected = _sign(body)
    if not expected or not hmac.compare_digest(expected, sig):
        return None, "bad_signature"
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except Exception:
        return None, "malformed"
    if not isinstance(payload, dict):
        return None, "malformed"
    try:
        tg_id = int(payload.get("id") or 0)
        exp = int(payload.get("exp") or 0)
    except Exception:
        return None, "malformed"
    if tg_id <= 0:
        return None, "invalid_user"
    if exp <= int(time.time()):
        return None, "expired"
    return {
        "id": tg_id,
        "username": payload.get("username"),
        "auth_type": payload.get("auth_type"),
        "auth_origin": payload.get("auth_origin"),
        "email": payload.get("email"),
        "purpose": payload.get("purpose"),
        "account_id": payload.get("account_id"),
        "session_id": payload.get("session_id"),
        "device_id": payload.get("device_id"),
        "auth_epoch": payload.get("auth_epoch"),
        "device_credential_version": payload.get("device_credential_version"),
        "scope": payload.get("scope"),
        "token_id": payload.get("token_id"),
    }, None


def verify_web_session_token(token: str) -> dict[str, Any] | None:
    payload, _reason = inspect_web_session_token(token)
    return payload


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
