from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func

from account_security_errors import EmailOtpError
from account_foundation_service import ensure_user_account_foundation
from config import env_bool, env_int
from email_delivery_service import deliver_auth_message as deliver_email_auth_message
from free_cycle_service import mark_user_became_free, project_user_to_expired
from models import User, WebEmailIdentity, WebEmailToken
from node_policy import free_tier_enabled


EMAIL_AUTH_DEBUG_ECHO = env_bool("EMAIL_AUTH_DEBUG_ECHO", default=False)
EMAIL_AUTH_PASSWORD_MIN_LENGTH = max(8, env_int("EMAIL_AUTH_PASSWORD_MIN_LENGTH", 10))
EMAIL_AUTH_VERIFY_TTL_SECONDS = max(300, env_int("EMAIL_AUTH_VERIFY_TTL_SECONDS", 3600))
EMAIL_AUTH_RESET_TTL_SECONDS = max(300, env_int("EMAIL_AUTH_RESET_TTL_SECONDS", 1800))
EMAIL_AUTH_LOGIN_OTP_TTL_SECONDS = 300
EMAIL_AUTH_PASSWORD_HASH_ITERATIONS = max(100_000, env_int("EMAIL_AUTH_PASSWORD_HASH_ITERATIONS", 600_000))
WEB_EMAIL_ACCOUNT_TG_ID_BASE = max(8_000_000_000_000, env_int("WEB_EMAIL_ACCOUNT_TG_ID_BASE", 8_000_000_000_000))
APP_ACCOUNT_TG_ID_BASE = max(9_000_000_000_000, env_int("APP_ACCOUNT_TG_ID_BASE", 9_000_000_000_000))
FREE_ACCOUNT_LIFETIME_DAYS = max(3650, env_int("AUTO_FREE_DAYS", 3650))

EMAIL_TOKEN_KIND_VERIFY = "verify"
EMAIL_TOKEN_KIND_RESET = "reset"
EMAIL_TOKEN_KIND_LOGIN_OTP = "login_otp"

_EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


class EmailAuthError(RuntimeError):
    pass


class DuplicateEmailIdentityError(EmailAuthError):
    pass


class InvalidEmailCredentialsError(EmailAuthError):
    pass


class InvalidEmailTokenError(EmailAuthError):
    pass


class InvalidEmailInputError(EmailAuthError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _token_secret() -> str:
    return (
        str(os.getenv("EMAIL_AUTH_TOKEN_SECRET") or "").strip()
        or str(os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
        or str(os.getenv("BOT_TOKEN") or "").strip()
    )


def email_login_otp_configured() -> bool:
    return bool(_token_secret())


def _hash_token(raw_token: str) -> str:
    raw = str(raw_token or "").strip()
    secret = _token_secret()
    if secret:
        return hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def validate_email_input(value: str) -> str:
    normalized = normalize_email(value)
    if not normalized or len(normalized) > 200 or not _EMAIL_RE.match(normalized):
        raise InvalidEmailInputError("Invalid email address")
    return normalized


def validate_password_input(password: str) -> str:
    raw = str(password or "")
    if len(raw) < EMAIL_AUTH_PASSWORD_MIN_LENGTH:
        raise InvalidEmailInputError("Password is too short")
    if len(raw) > 200:
        raise InvalidEmailInputError("Password is too long")
    return raw


def _hash_password(password: str) -> str:
    raw = validate_password_input(password)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw.encode("utf-8"),
        salt.encode("ascii"),
        EMAIL_AUTH_PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${EMAIL_AUTH_PASSWORD_HASH_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    raw = str(password or "")
    encoded = str(password_hash or "").strip()
    try:
        scheme, iterations_raw, salt, expected = encoded.split("$", 3)
        iterations = int(iterations_raw)
    except Exception:
        return False
    if scheme != "pbkdf2_sha256" or not salt or not expected:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return hmac.compare_digest(digest, expected)


def _next_email_account_tg_id(session) -> int:
    current = (
        session.query(func.max(User.tg_id))
        .filter(User.tg_id >= int(WEB_EMAIL_ACCOUNT_TG_ID_BASE))
        .filter(User.tg_id < int(APP_ACCOUNT_TG_ID_BASE))
        .scalar()
    )
    if current is None:
        return int(WEB_EMAIL_ACCOUNT_TG_ID_BASE)
    return int(current) + 1


def ensure_email_account_user(
    session,
    *,
    linked_tg_id: int | None,
    email_norm: str,
    display_name: str | None = None,
) -> User:
    now = _utcnow()
    target_tg_id = int(linked_tg_id or 0)
    if target_tg_id > 0:
        row = session.query(User).filter(User.tg_id == target_tg_id).first()
        if row:
            if display_name is not None and not str(getattr(row, "display_name", "") or "").strip():
                row.display_name = str(display_name).strip()[:100] or None
            return row

    target_tg_id = _next_email_account_tg_id(session)
    free_enabled = free_tier_enabled()
    row = User(
        tg_id=int(target_tg_id),
        username=None,
        uuid=str(uuid.uuid4()),
        email=f"EMAIL_{int(target_tg_id)}",
        sub_type="FREE",
        current_plan_code="free_monthly" if free_enabled else "free_retired",
        created_at=now,
        expiry_at=now + timedelta(days=FREE_ACCOUNT_LIFETIME_DAYS) if free_enabled else now,
        is_active=True,
        stars_paid=0,
        total_gb=0,
        trial_used=False,
        tos_accepted=False,
        sub_token=secrets.token_urlsafe(32),
        display_name=(str(display_name or "").strip()[:100] or email_norm.split("@", 1)[0][:100] or None),
    )
    if free_enabled:
        mark_user_became_free(row, now=now)
    else:
        project_user_to_expired(row, now=now, source="email_account_without_free")
    session.add(row)
    session.flush()
    return row


def _invalidate_unused_tokens(session, *, identity_id: int, token_kind: str) -> None:
    session.query(WebEmailToken).filter(
        WebEmailToken.identity_id == int(identity_id),
        WebEmailToken.token_kind == str(token_kind),
        WebEmailToken.used_at.is_(None),
    ).delete(synchronize_session=False)


def _issue_one_time_token(session, *, identity_id: int, token_kind: str, ttl_seconds: int) -> str:
    now = _utcnow()
    raw_token = secrets.token_urlsafe(32)
    token = WebEmailToken(
        identity_id=int(identity_id),
        token_kind=str(token_kind),
        token_hash=_hash_token(raw_token),
        expires_at=now + timedelta(seconds=max(300, int(ttl_seconds))),
        created_at=now,
    )
    session.add(token)
    session.flush()
    return raw_token


def _login_otp_hash(*, identity_id: int, code: str) -> str:
    secret = _token_secret()
    if not secret:
        raise EmailOtpError("email_otp_not_configured")
    payload = f"email-login-otp:{int(identity_id)}:{str(code or '').strip()}"
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_login_otp(
    session,
    *,
    email: str,
    now: datetime | None = None,
) -> tuple[WebEmailIdentity | None, str | None]:
    email_norm = validate_email_input(email)
    identity = (
        session.query(WebEmailIdentity)
        .filter(
            WebEmailIdentity.email_norm == email_norm,
            WebEmailIdentity.is_verified == True,
        )
        .first()
    )
    if identity is None:
        return None, None

    effective_now = now or _utcnow()
    _invalidate_unused_tokens(
        session,
        identity_id=int(identity.id),
        token_kind=EMAIL_TOKEN_KIND_LOGIN_OTP,
    )
    for _ in range(20):
        code = f"{secrets.randbelow(1_000_000):06d}"
        token_hash = _login_otp_hash(identity_id=int(identity.id), code=code)
        if session.query(WebEmailToken.id).filter(WebEmailToken.token_hash == token_hash).first():
            continue
        session.add(
            WebEmailToken(
                identity_id=int(identity.id),
                token_kind=EMAIL_TOKEN_KIND_LOGIN_OTP,
                token_hash=token_hash,
                expires_at=effective_now + timedelta(seconds=EMAIL_AUTH_LOGIN_OTP_TTL_SECONDS),
                created_at=effective_now,
            )
        )
        session.flush()
        return identity, code
    raise EmailOtpError("email_otp_generation_failed")


def consume_login_otp(
    session,
    *,
    email: str,
    code: str,
    now: datetime | None = None,
) -> WebEmailIdentity:
    email_norm = validate_email_input(email)
    normalized_code = str(code or "").strip()
    if len(normalized_code) != 6 or not normalized_code.isdigit():
        raise EmailOtpError("email_otp_invalid")

    identity = (
        session.query(WebEmailIdentity)
        .filter(
            WebEmailIdentity.email_norm == email_norm,
            WebEmailIdentity.is_verified == True,
        )
        .first()
    )
    if identity is None:
        raise EmailOtpError("email_otp_invalid")

    effective_now = now or _utcnow()
    token = (
        session.query(WebEmailToken)
        .filter(
            WebEmailToken.identity_id == int(identity.id),
            WebEmailToken.token_kind == EMAIL_TOKEN_KIND_LOGIN_OTP,
            WebEmailToken.token_hash
            == _login_otp_hash(identity_id=int(identity.id), code=normalized_code),
        )
        .with_for_update()
        .first()
    )
    if token is None or token.used_at is not None:
        raise EmailOtpError("email_otp_invalid")
    if token.expires_at <= effective_now:
        raise EmailOtpError("email_otp_expired")

    token.used_at = effective_now
    identity.last_login_at = effective_now
    identity.updated_at = effective_now
    session.flush()
    return identity


def register_email_identity(
    session,
    *,
    email: str,
    password: str,
    linked_tg_id: int | None = None,
    display_name: str | None = None,
) -> tuple[WebEmailIdentity, str]:
    email_norm = validate_email_input(email)
    display_name_norm = str(display_name or "").strip()[:100] or None
    existing = session.query(WebEmailIdentity).filter(WebEmailIdentity.email_norm == email_norm).first()
    if existing and bool(existing.is_verified):
        raise DuplicateEmailIdentityError("Email is already registered")

    user = ensure_email_account_user(
        session,
        linked_tg_id=linked_tg_id,
        email_norm=email_norm,
        display_name=display_name_norm,
    )
    password_hash = _hash_password(password)
    now = _utcnow()

    if existing:
        existing.email = email_norm
        existing.email_norm = email_norm
        existing.password_hash = password_hash
        existing.linked_tg_id = int(user.tg_id)
        existing.is_verified = False
        existing.verified_at = None
        existing.updated_at = now
        identity = existing
    else:
        identity = WebEmailIdentity(
            email=email_norm,
            email_norm=email_norm,
            password_hash=password_hash,
            linked_tg_id=int(user.tg_id),
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        session.add(identity)
        session.flush()

    ensure_user_account_foundation(session, user, now=now)

    _invalidate_unused_tokens(session, identity_id=int(identity.id), token_kind=EMAIL_TOKEN_KIND_VERIFY)
    raw_token = _issue_one_time_token(
        session,
        identity_id=int(identity.id),
        token_kind=EMAIL_TOKEN_KIND_VERIFY,
        ttl_seconds=EMAIL_AUTH_VERIFY_TTL_SECONDS,
    )
    return identity, raw_token


def _consume_token(session, *, raw_token: str, token_kind: str) -> tuple[WebEmailToken, WebEmailIdentity]:
    token_hash = _hash_token(raw_token)
    now = _utcnow()
    token = session.query(WebEmailToken).filter(
        WebEmailToken.token_hash == token_hash,
        WebEmailToken.token_kind == str(token_kind),
    ).first()
    if not token:
        raise InvalidEmailTokenError("Invalid token")
    if token.used_at is not None or token.expires_at <= now:
        raise InvalidEmailTokenError("Token has expired")
    identity = session.query(WebEmailIdentity).filter(WebEmailIdentity.id == int(token.identity_id)).first()
    if not identity:
        raise InvalidEmailTokenError("Identity was not found")
    token.used_at = now
    return token, identity


def verify_email_identity(session, *, token: str) -> WebEmailIdentity:
    token_row, identity = _consume_token(session, raw_token=token, token_kind=EMAIL_TOKEN_KIND_VERIFY)
    now = _utcnow()
    identity.is_verified = True
    identity.verified_at = now
    identity.updated_at = now
    token_row.used_at = now
    user = session.query(User).filter(User.tg_id == int(identity.linked_tg_id)).first()
    if user is not None:
        ensure_user_account_foundation(session, user, now=now)
    return identity


def authenticate_email_identity(session, *, email: str, password: str) -> WebEmailIdentity:
    email_norm = validate_email_input(email)
    identity = session.query(WebEmailIdentity).filter(WebEmailIdentity.email_norm == email_norm).first()
    if not identity or not bool(identity.is_verified):
        raise InvalidEmailCredentialsError("Invalid email or password")
    if not verify_password(password, str(identity.password_hash or "")):
        raise InvalidEmailCredentialsError("Invalid email or password")
    identity.last_login_at = _utcnow()
    identity.updated_at = identity.last_login_at
    return identity


def start_password_reset(session, *, email: str) -> tuple[WebEmailIdentity | None, str | None]:
    email_norm = validate_email_input(email)
    identity = session.query(WebEmailIdentity).filter(
        WebEmailIdentity.email_norm == email_norm,
        WebEmailIdentity.is_verified == True,
    ).first()
    if not identity:
        return None, None
    _invalidate_unused_tokens(session, identity_id=int(identity.id), token_kind=EMAIL_TOKEN_KIND_RESET)
    raw_token = _issue_one_time_token(
        session,
        identity_id=int(identity.id),
        token_kind=EMAIL_TOKEN_KIND_RESET,
        ttl_seconds=EMAIL_AUTH_RESET_TTL_SECONDS,
    )
    return identity, raw_token


def finish_password_reset(session, *, token: str, password: str) -> WebEmailIdentity:
    token_row, identity = _consume_token(session, raw_token=token, token_kind=EMAIL_TOKEN_KIND_RESET)
    now = _utcnow()
    identity.password_hash = _hash_password(password)
    identity.updated_at = now
    identity.last_login_at = now
    token_row.used_at = now
    return identity


def get_verified_identity_for_user(session, *, tg_id: int) -> WebEmailIdentity | None:
    return (
        session.query(WebEmailIdentity)
        .filter(
            WebEmailIdentity.linked_tg_id == int(tg_id),
            WebEmailIdentity.is_verified == True,
        )
        .order_by(WebEmailIdentity.verified_at.desc(), WebEmailIdentity.id.desc())
        .first()
    )


def build_debug_payload(*, verify_token: str | None = None, reset_token: str | None = None) -> dict[str, str] | None:
    if not EMAIL_AUTH_DEBUG_ECHO:
        return None
    debug: dict[str, str] = {}
    if verify_token:
        debug["verify_token"] = str(verify_token)
    if reset_token:
        debug["reset_token"] = str(reset_token)
    return debug or None


async def deliver_auth_message(
    *,
    kind: str,
    email: str,
    token: str,
    linked_tg_id: int | None = None,
) -> dict[str, Any]:
    return await deliver_email_auth_message(
        kind=kind,
        email=email,
        token=token,
        linked_tg_id=linked_tg_id,
    )
