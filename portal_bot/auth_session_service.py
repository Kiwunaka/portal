from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from models import Account, AccountDevice, AuthSession, User
from web_auth_service import create_web_session_token


def _env_seconds(name: str, default: int, *, minimum: int) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return max(minimum, default)


APP_ACCESS_TOKEN_TTL_SECONDS = _env_seconds("APP_ACCESS_TOKEN_TTL_SECONDS", 900, minimum=300)
APP_REFRESH_TOKEN_TTL_SECONDS = _env_seconds("APP_REFRESH_TOKEN_TTL_SECONDS", 30 * 86400, minimum=86400)
APP_FRESH_AUTH_MAX_AGE_SECONDS = _env_seconds("APP_FRESH_AUTH_MAX_AGE_SECONDS", 600, minimum=60)


class AuthSessionError(ValueError):
    def __init__(
        self,
        code: str,
        *,
        message: str | None = None,
        security_state_changed: bool = False,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.security_state_changed = security_state_changed


@dataclass(frozen=True)
class IssuedDeviceSession:
    access_token: str
    refresh_token: str
    session_id: str
    refresh_family_id: str
    account_id: str
    legacy_account_id: str
    device_id: str
    access_expires_at: datetime
    refresh_expires_at: datetime

    def response_payload(self, *, now: datetime) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "session_token": self.access_token,
            "token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": "Bearer",
            "expires_in": max(0, int((self.access_expires_at - now).total_seconds())),
            "refresh_expires_in": max(0, int((self.refresh_expires_at - now).total_seconds())),
            "session_id": self.session_id,
            "refresh_family_id": self.refresh_family_id,
            "account_id": self.legacy_account_id,
            "canonical_account_id": self.account_id,
            "device_id": self.device_id,
            "access_expires_at": self.access_expires_at.isoformat() + "Z",
            "refresh_expires_at": self.refresh_expires_at.isoformat() + "Z",
        }


def _refresh_token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_refresh_token() -> str:
    return "pkr_rt_" + secrets.token_urlsafe(48)


def _active_account(session: Session, account_id: str, *, lock: bool = False) -> Account:
    query = session.query(Account).filter(Account.id == str(account_id))
    if lock:
        query = query.with_for_update()
    account = query.first()
    if account is None:
        raise AuthSessionError("account_not_found")
    if str(account.status or "").strip().lower() != "active":
        raise AuthSessionError("account_unavailable")
    return account


def _active_device(
    session: Session,
    *,
    account_id: str,
    device_id: str | None = None,
    install_id: str | None = None,
    lock: bool = False,
    require_active: bool = True,
) -> AccountDevice:
    query = session.query(AccountDevice).filter(AccountDevice.account_id == str(account_id))
    if device_id:
        query = query.filter(AccountDevice.id == str(device_id))
    elif install_id:
        query = query.filter(AccountDevice.install_id == str(install_id))
    else:
        raise AuthSessionError("device_not_found")
    if lock:
        query = query.with_for_update()
    device = query.first()
    if device is None:
        raise AuthSessionError("device_not_found")
    if require_active and (
        str(device.state or "").strip().lower() != "active" or device.revoked_at is not None
    ):
        raise AuthSessionError("device_revoked")
    return device


def _device_user(session: Session, *, account_id: str, install_id: str) -> User:
    user = (
        session.query(User)
        .filter(User.account_id == str(account_id), User.app_install_id == str(install_id))
        .order_by(User.tg_id.asc())
        .first()
    )
    if user is None:
        user = (
            session.query(User)
            .filter(User.account_id == str(account_id))
            .order_by(User.tg_id.asc())
            .first()
        )
    if user is None:
        raise AuthSessionError("device_identity_missing")
    return user


def _mint_session(
    session: Session,
    *,
    user: User,
    account: Account,
    device: AccountDevice,
    now: datetime,
    access_ttl_seconds: int,
    refresh_expires_at: datetime,
    refresh_family_id: str,
    scope: str,
    auth_origin: str,
    fresh_auth_at: datetime | None,
) -> IssuedDeviceSession:
    session_id = str(uuid.uuid4())
    refresh_token = _new_refresh_token()
    access_expires_at = min(
        now + timedelta(seconds=max(300, int(access_ttl_seconds))),
        refresh_expires_at,
    )
    access_token = create_web_session_token(
        tg_id=int(user.tg_id),
        username=str(user.username or "").strip() or None,
        auth_type="app",
        auth_origin=auth_origin,
        ttl_seconds=max(300, int(access_ttl_seconds)),
        purpose="app_access",
        account_id=str(account.id),
        session_id=session_id,
        device_id=str(device.id),
        auth_epoch=int(account.auth_epoch or 0),
        device_credential_version=int(device.credential_version or 1),
        scope=scope,
    )
    if not access_token:
        raise AuthSessionError("session_not_configured")

    row = AuthSession(
        id=session_id,
        account_id=str(account.id),
        device_id=str(device.id),
        refresh_family_id=str(refresh_family_id),
        refresh_token_hash=_refresh_token_hash(refresh_token),
        scope=scope,
        auth_origin=auth_origin,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
        fresh_auth_at=fresh_auth_at,
        created_at=now,
    )
    session.add(row)
    session.flush()
    return IssuedDeviceSession(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session_id,
        refresh_family_id=str(refresh_family_id),
        account_id=str(account.id),
        legacy_account_id=str(int(user.tg_id)),
        device_id=str(device.id),
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


def issue_device_session(
    session: Session,
    *,
    user: User,
    install_id: str,
    now: datetime,
    access_ttl_seconds: int = APP_ACCESS_TOKEN_TTL_SECONDS,
    refresh_ttl_seconds: int = APP_REFRESH_TOKEN_TTL_SECONDS,
    scope: str = "client",
    auth_origin: str = "app_bootstrap",
    fresh_auth_at: datetime | None = None,
) -> IssuedDeviceSession:
    account_id = str(user.account_id or "").strip()
    if not account_id:
        raise AuthSessionError("account_not_found")
    account = _active_account(session, account_id, lock=True)
    device = _active_device(
        session,
        account_id=account_id,
        install_id=str(install_id or "").strip(),
        lock=True,
    )
    existing = (
        session.query(AuthSession.id)
        .filter(AuthSession.device_id == str(device.id))
        .order_by(AuthSession.created_at.asc())
        .first()
    )
    if existing is not None:
        raise AuthSessionError(
            "device_recovery_required",
            message="This device already has session history; use refresh or account recovery.",
        )
    return _mint_session(
        session,
        user=user,
        account=account,
        device=device,
        now=now,
        access_ttl_seconds=access_ttl_seconds,
        refresh_expires_at=now + timedelta(seconds=max(86400, int(refresh_ttl_seconds))),
        refresh_family_id=str(uuid.uuid4()),
        scope=str(scope or "client")[:64],
        auth_origin=str(auth_origin or "app_bootstrap")[:32],
        fresh_auth_at=fresh_auth_at,
    )


def issue_authenticated_device_session(
    session: Session,
    *,
    account_id: str,
    install_id: str,
    device_name: str,
    platform: str,
    now: datetime,
    os_version: str | None = None,
    app_version: str | None = None,
    locale: str | None = None,
    time_zone: str | None = None,
    scope: str = "client",
    auth_origin: str = "email_otp",
    access_ttl_seconds: int = APP_ACCESS_TOKEN_TTL_SECONDS,
    refresh_ttl_seconds: int = APP_REFRESH_TOKEN_TTL_SECONDS,
) -> IssuedDeviceSession:
    normalized_install_id = str(install_id or "").strip()[:128]
    if not normalized_install_id:
        raise AuthSessionError("device_not_found")

    account = _active_account(session, str(account_id), lock=True)
    device = (
        session.query(AccountDevice)
        .filter(AccountDevice.install_id == normalized_install_id)
        .with_for_update()
        .first()
    )
    if device is not None and str(device.account_id) != str(account.id):
        raise AuthSessionError("device_identity_conflict")

    target_state = "recovery" if str(scope or "").strip() == "recovery" else "active"
    if device is None:
        device = AccountDevice(
            id=str(uuid.uuid4()),
            account_id=str(account.id),
            install_id=normalized_install_id,
            label=str(device_name or "Recovered device").strip()[:120] or "Recovered device",
            platform=str(platform or "device").strip()[:32] or "device",
            os_version=str(os_version or "").strip()[:64] or None,
            app_version=str(app_version or "").strip()[:32] or None,
            locale=str(locale or "").strip()[:32] or None,
            time_zone=str(time_zone or "").strip()[:64] or None,
            state=target_state,
            credential_version=1,
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
            updated_at=now,
        )
        session.add(device)
        session.flush()
    else:
        prior_sessions = (
            session.query(AuthSession)
            .filter(AuthSession.device_id == str(device.id))
            .with_for_update()
            .all()
        )
        for row in prior_sessions:
            if row.revoked_at is None:
                row.revoked_at = now
                row.revoke_reason = "fresh_auth_replaced"
        device.credential_version = int(device.credential_version or 1) + 1
        device.state = target_state
        device.revoked_at = None
        device.revoke_reason = None
        device.label = str(device_name or device.label or "Recovered device").strip()[:120]
        device.platform = str(platform or device.platform or "device").strip()[:32]
        device.os_version = str(os_version or device.os_version or "").strip()[:64] or None
        device.app_version = str(app_version or device.app_version or "").strip()[:32] or None
        device.locale = str(locale or device.locale or "").strip()[:32] or None
        device.time_zone = str(time_zone or device.time_zone or "").strip()[:64] or None
        device.last_seen_at = now
        device.updated_at = now

    user = _device_user(session, account_id=str(account.id), install_id=normalized_install_id)
    return _mint_session(
        session,
        user=user,
        account=account,
        device=device,
        now=now,
        access_ttl_seconds=max(300, int(access_ttl_seconds)),
        refresh_expires_at=now + timedelta(seconds=max(300, int(refresh_ttl_seconds))),
        refresh_family_id=str(uuid.uuid4()),
        scope=str(scope or "client")[:64],
        auth_origin=str(auth_origin or "email_otp")[:32],
        fresh_auth_at=now,
    )


def _revoke_refresh_family(session: Session, *, row: AuthSession, now: datetime) -> None:
    family = (
        session.query(AuthSession)
        .filter(AuthSession.refresh_family_id == str(row.refresh_family_id))
        .with_for_update()
        .all()
    )
    if row.reuse_detected_at is None:
        row.reuse_detected_at = now
    for member in family:
        if member.revoked_at is None:
            member.revoked_at = now
            member.revoke_reason = "refresh_reuse_detected"
    session.flush()


def rotate_device_session(
    session: Session,
    *,
    refresh_token: str,
    now: datetime,
    access_ttl_seconds: int = APP_ACCESS_TOKEN_TTL_SECONDS,
) -> IssuedDeviceSession:
    raw_refresh = str(refresh_token or "").strip()
    if not raw_refresh:
        raise AuthSessionError("refresh_token_invalid")
    discovered = (
        session.query(AuthSession.id, AuthSession.account_id, AuthSession.device_id)
        .filter(AuthSession.refresh_token_hash == _refresh_token_hash(raw_refresh))
        .first()
    )
    if discovered is None:
        raise AuthSessionError("refresh_token_invalid")
    account = _active_account(session, str(discovered.account_id), lock=True)
    device = _active_device(
        session,
        account_id=str(discovered.account_id),
        device_id=str(discovered.device_id or ""),
        lock=True,
        require_active=False,
    )
    row = (
        session.query(AuthSession)
        .filter(
            AuthSession.id == str(discovered.id),
            AuthSession.refresh_token_hash == _refresh_token_hash(raw_refresh),
        )
        .with_for_update()
        .first()
    )
    if row is None:
        raise AuthSessionError("refresh_token_invalid")
    if str(row.account_id) != str(account.id) or str(row.device_id or "") != str(device.id):
        raise AuthSessionError("session_state_changed")
    if row.replaced_by_session_id or row.reuse_detected_at is not None:
        _revoke_refresh_family(session, row=row, now=now)
        raise AuthSessionError("refresh_reuse_detected", security_state_changed=True)
    if row.revoked_at is not None:
        raise AuthSessionError("session_revoked")
    if row.refresh_expires_at <= now:
        row.revoked_at = now
        row.revoke_reason = "refresh_expired"
        session.flush()
        raise AuthSessionError("refresh_expired", security_state_changed=True)
    allowed_device_states = {"active"}
    if str(row.scope or "") == "recovery":
        allowed_device_states.add("recovery")
    if str(device.state or "").strip().lower() not in allowed_device_states or device.revoked_at is not None:
        raise AuthSessionError("device_revoked")
    user = _device_user(session, account_id=str(account.id), install_id=str(device.install_id))
    replacement = _mint_session(
        session,
        user=user,
        account=account,
        device=device,
        now=now,
        access_ttl_seconds=access_ttl_seconds,
        refresh_expires_at=row.refresh_expires_at,
        refresh_family_id=str(row.refresh_family_id),
        scope=str(row.scope or "client"),
        auth_origin=str(row.auth_origin or "app_refresh"),
        fresh_auth_at=row.fresh_auth_at,
    )
    row.replaced_by_session_id = replacement.session_id
    row.last_used_at = now
    session.flush()
    return replacement


def _required_string_claim(payload: dict[str, Any], name: str) -> str:
    value = str(payload.get(name) or "").strip()
    if not value:
        raise AuthSessionError("session_claims_invalid")
    return value


def _required_int_claim(payload: dict[str, Any], name: str) -> int:
    try:
        return int(payload.get(name))
    except (TypeError, ValueError):
        raise AuthSessionError("session_claims_invalid") from None


def validate_access_session(
    session: Session,
    *,
    payload: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    session_id = _required_string_claim(payload, "session_id")
    account_id = _required_string_claim(payload, "account_id")
    device_id = _required_string_claim(payload, "device_id")
    row = session.query(AuthSession).filter(AuthSession.id == session_id).first()
    if row is None:
        raise AuthSessionError("session_not_found")
    if str(row.account_id) != account_id or str(row.device_id or "") != device_id:
        raise AuthSessionError("session_claims_invalid")
    if row.revoked_at is not None:
        raise AuthSessionError("session_revoked")

    token_scope = str(payload.get("scope") or "")
    row_scope = str(row.scope or "")
    derived_cabinet_scope = row_scope == "client" and token_scope == "cabinet_session"
    if token_scope != row_scope and not derived_cabinet_scope:
        raise AuthSessionError("session_scope_changed")
    if row.access_expires_at <= now and not derived_cabinet_scope:
        raise AuthSessionError("access_expired")

    account = _active_account(session, account_id)
    if _required_int_claim(payload, "auth_epoch") != int(account.auth_epoch or 0):
        raise AuthSessionError("session_epoch_changed")
    recovery_scope = token_scope == "recovery"
    device = _active_device(
        session,
        account_id=account_id,
        device_id=device_id,
        require_active=not recovery_scope,
    )
    if recovery_scope and (
        str(device.state or "").strip().lower() not in {"active", "recovery"}
        or device.revoked_at is not None
    ):
        raise AuthSessionError("device_revoked")
    if _required_int_claim(payload, "device_credential_version") != int(device.credential_version or 1):
        raise AuthSessionError("device_credential_changed")
    tg_id = _required_int_claim(payload, "id")
    user = session.query(User.tg_id).filter(User.tg_id == tg_id, User.account_id == account_id).first()
    if user is None:
        raise AuthSessionError("session_identity_changed")
    return dict(payload)


def revoke_session(
    session: Session,
    *,
    account_id: str,
    session_id: str,
    now: datetime,
    reason: str = "user_logout",
) -> AuthSession:
    _active_account(session, str(account_id), lock=True)
    row = (
        session.query(AuthSession)
        .filter(AuthSession.id == str(session_id), AuthSession.account_id == str(account_id))
        .with_for_update()
        .first()
    )
    if row is None:
        raise AuthSessionError("session_not_found")
    family = (
        session.query(AuthSession)
        .filter(AuthSession.refresh_family_id == str(row.refresh_family_id))
        .with_for_update()
        .all()
    )
    for member in family:
        if member.revoked_at is None:
            member.revoked_at = now
            member.revoke_reason = str(reason or "user_logout")[:64]
    session.flush()
    return row


def revoke_device(
    session: Session,
    *,
    account_id: str,
    device_id: str,
    actor_session_id: str,
    now: datetime,
    fresh_auth_max_age_seconds: int = APP_FRESH_AUTH_MAX_AGE_SECONDS,
    reason: str = "device_revoked",
) -> AccountDevice:
    account = _active_account(session, str(account_id), lock=True)
    actor = (
        session.query(AuthSession)
        .filter(AuthSession.id == str(actor_session_id), AuthSession.account_id == str(account.id))
        .with_for_update()
        .first()
    )
    if actor is None or actor.revoked_at is not None:
        raise AuthSessionError("session_revoked")
    fresh_after = now - timedelta(seconds=max(60, int(fresh_auth_max_age_seconds)))
    if actor.fresh_auth_at is None or actor.fresh_auth_at < fresh_after:
        raise AuthSessionError("fresh_auth_required")

    device = (
        session.query(AccountDevice)
        .filter(AccountDevice.id == str(device_id), AccountDevice.account_id == str(account.id))
        .with_for_update()
        .first()
    )
    if device is None:
        raise AuthSessionError("device_not_found")
    already_revoked = str(device.state or "").strip().lower() == "revoked" or device.revoked_at is not None
    if not already_revoked:
        device.state = "revoked"
        device.revoked_at = now
        device.revoke_reason = str(reason or "device_revoked")[:64]
        device.credential_version = int(device.credential_version or 1) + 1
        device.updated_at = now
    rows = session.query(AuthSession).filter(AuthSession.device_id == str(device.id)).with_for_update().all()
    for row in rows:
        if row.revoked_at is None:
            row.revoked_at = now
            row.revoke_reason = "device_revoked"
    session.flush()
    return device


def require_fresh_session(
    session: Session,
    *,
    account_id: str,
    session_id: str,
    now: datetime,
    allowed_scopes: set[str] | None = None,
    fresh_auth_max_age_seconds: int = APP_FRESH_AUTH_MAX_AGE_SECONDS,
) -> AuthSession:
    account = _active_account(session, str(account_id), lock=True)
    row = (
        session.query(AuthSession)
        .filter(AuthSession.id == str(session_id), AuthSession.account_id == str(account.id))
        .with_for_update()
        .first()
    )
    if row is None or row.revoked_at is not None or row.access_expires_at <= now:
        raise AuthSessionError("session_revoked")
    scopes = {str(item).strip() for item in (allowed_scopes or {"client", "recovery"}) if str(item).strip()}
    if str(row.scope or "") not in scopes:
        raise AuthSessionError("session_scope_changed")
    fresh_after = now - timedelta(seconds=max(60, int(fresh_auth_max_age_seconds)))
    if row.fresh_auth_at is None or row.fresh_auth_at < fresh_after:
        raise AuthSessionError("fresh_auth_required")
    return row


def mark_session_fresh(
    session: Session,
    *,
    account_id: str,
    session_id: str,
    now: datetime,
) -> AuthSession:
    account = _active_account(session, str(account_id), lock=True)
    row = (
        session.query(AuthSession)
        .filter(AuthSession.id == str(session_id), AuthSession.account_id == str(account.id))
        .with_for_update()
        .first()
    )
    if row is None or row.revoked_at is not None or row.access_expires_at <= now:
        raise AuthSessionError("session_revoked")
    if str(row.scope or "") not in {"client", "recovery"}:
        raise AuthSessionError("session_scope_changed")
    row.fresh_auth_at = now
    row.last_used_at = now
    session.flush()
    return row


def promote_recovery_session(
    session: Session,
    *,
    account_id: str,
    recovery_session_id: str,
    lockdown: bool,
    now: datetime,
) -> tuple[IssuedDeviceSession, int]:
    account = _active_account(session, str(account_id), lock=True)
    discovered = (
        session.query(AuthSession.device_id)
        .filter(
            AuthSession.id == str(recovery_session_id),
            AuthSession.account_id == str(account.id),
        )
        .first()
    )
    if discovered is None or not str(discovered.device_id or ""):
        raise AuthSessionError("recovery_session_invalid")
    device = _active_device(
        session,
        account_id=str(account.id),
        device_id=str(discovered.device_id),
        lock=True,
        require_active=False,
    )
    if str(device.state or "").strip().lower() not in {"active", "recovery"} or device.revoked_at is not None:
        raise AuthSessionError("device_revoked")
    recovery = (
        session.query(AuthSession)
        .filter(
            AuthSession.id == str(recovery_session_id),
            AuthSession.account_id == str(account.id),
            AuthSession.device_id == str(device.id),
        )
        .with_for_update()
        .first()
    )
    if (
        recovery is None
        or recovery.revoked_at is not None
        or recovery.access_expires_at <= now
        or str(recovery.scope or "") != "recovery"
    ):
        raise AuthSessionError("recovery_session_invalid")
    if recovery.fresh_auth_at is None:
        raise AuthSessionError("fresh_auth_required")

    revoked_devices = 0
    if lockdown:
        other_devices = (
            session.query(AccountDevice)
            .filter(
                AccountDevice.account_id == str(account.id),
                AccountDevice.id != str(device.id),
            )
            .with_for_update()
            .all()
        )
        for other in other_devices:
            if str(other.state or "").strip().lower() != "revoked" or other.revoked_at is None:
                other.state = "revoked"
                other.revoked_at = now
                other.revoke_reason = "account_lockdown"
                other.credential_version = int(other.credential_version or 1) + 1
                other.updated_at = now
                revoked_devices += 1
        account.auth_epoch = int(account.auth_epoch or 0) + 1
        account.updated_at = now

    device.state = "active"
    device.revoked_at = None
    device.revoke_reason = None
    device.last_seen_at = now
    device.updated_at = now

    session_rows = (
        session.query(AuthSession)
        .filter(AuthSession.account_id == str(account.id))
        .with_for_update()
        .all()
    )
    for row in session_rows:
        same_family = str(row.refresh_family_id) == str(recovery.refresh_family_id)
        if (lockdown or same_family) and row.revoked_at is None:
            row.revoked_at = now
            row.revoke_reason = "account_lockdown" if lockdown else "recovery_reissued"

    user = _device_user(session, account_id=str(account.id), install_id=str(device.install_id))
    issued = _mint_session(
        session,
        user=user,
        account=account,
        device=device,
        now=now,
        access_ttl_seconds=APP_ACCESS_TOKEN_TTL_SECONDS,
        refresh_expires_at=now + timedelta(seconds=APP_REFRESH_TOKEN_TTL_SECONDS),
        refresh_family_id=str(uuid.uuid4()),
        scope="client",
        auth_origin="recovery_reissue",
        fresh_auth_at=now,
    )
    session.flush()
    return issued, revoked_devices
