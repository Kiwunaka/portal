from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import auth_session_service
from models import AccountDevice, DevicePairingCode, User


PAIRING_CODE_TTL_SECONDS = 600
PAIRING_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class DevicePairingError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)


@dataclass(frozen=True)
class IssuedPairingCode:
    row: DevicePairingCode
    code: str


@dataclass(frozen=True)
class ClaimedPairingCode:
    row: DevicePairingCode
    session: auth_session_service.IssuedDeviceSession


def _pairing_hmac_secret() -> bytes:
    value = (
        str(os.getenv("DEVICE_PAIRING_HMAC_SECRET") or "").strip()
        or str(os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
    )
    if len(value) < 16:
        raise DevicePairingError(
            "pairing_not_configured",
            "Device pairing is not configured.",
        )
    return value.encode("utf-8")


def normalize_pairing_code(value: str) -> str:
    normalized = "".join(ch for ch in str(value or "").upper() if ch.isalnum())
    if len(normalized) != 8 or any(ch not in PAIRING_CODE_ALPHABET for ch in normalized):
        raise DevicePairingError("pairing_code_invalid", "Pairing code is invalid.")
    return normalized


def format_pairing_code(value: str) -> str:
    normalized = normalize_pairing_code(value)
    return f"{normalized[:4]}-{normalized[4:]}"


def _pairing_code_hmac(value: str) -> str:
    normalized = normalize_pairing_code(value)
    return hmac.new(
        _pairing_hmac_secret(),
        f"device-pairing:v1:{normalized}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _expire_stale_codes(session, *, account_id: str | None, now: datetime) -> None:
    query = session.query(DevicePairingCode).filter(
        DevicePairingCode.status == "active",
        DevicePairingCode.expires_at <= now,
    )
    if account_id:
        query = query.filter(DevicePairingCode.account_id == str(account_id))
    for row in query.with_for_update().all():
        row.status = "expired"
        row.updated_at = now


def issue_pairing_code(
    session,
    *,
    account_id: str,
    issued_by_session_id: str | None,
    now: datetime,
    ttl_seconds: int = PAIRING_CODE_TTL_SECONDS,
) -> IssuedPairingCode:
    account_key = str(account_id or "").strip()
    if not account_key:
        raise DevicePairingError("account_not_found", "Account is missing.")
    _expire_stale_codes(session, account_id=account_key, now=now)

    active_rows = (
        session.query(DevicePairingCode)
        .filter(
            DevicePairingCode.account_id == account_key,
            DevicePairingCode.status == "active",
        )
        .order_by(DevicePairingCode.created_at.desc())
        .with_for_update()
        .all()
    )
    for stale in active_rows[2:]:
        stale.status = "cancelled"
        stale.cancelled_at = now
        stale.updated_at = now

    for _ in range(30):
        raw = "".join(secrets.choice(PAIRING_CODE_ALPHABET) for _ in range(8))
        digest = _pairing_code_hmac(raw)
        exists = session.query(DevicePairingCode.id).filter(DevicePairingCode.code_hmac == digest).first()
        if exists is not None:
            continue
        row = DevicePairingCode(
            id=str(uuid.uuid4()),
            account_id=account_key,
            code_hmac=digest,
            code_hint=raw[-4:],
            status="active",
            issued_by_session_id=(str(issued_by_session_id or "").strip()[:36] or None),
            claim_attempts=0,
            expires_at=now + timedelta(seconds=max(120, min(int(ttl_seconds), 900))),
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        return IssuedPairingCode(row=row, code=format_pairing_code(raw))
    raise DevicePairingError("pairing_code_generation_failed", "Could not create a unique pairing code.")


def list_pairing_codes(session, *, account_id: str, now: datetime, limit: int = 10) -> list[DevicePairingCode]:
    account_key = str(account_id or "").strip()
    _expire_stale_codes(session, account_id=account_key, now=now)
    return (
        session.query(DevicePairingCode)
        .filter(DevicePairingCode.account_id == account_key)
        .order_by(DevicePairingCode.created_at.desc())
        .limit(max(1, min(int(limit), 25)))
        .all()
    )


def cancel_pairing_code(session, *, account_id: str, pairing_id: str, now: datetime) -> DevicePairingCode:
    row = (
        session.query(DevicePairingCode)
        .filter(
            DevicePairingCode.id == str(pairing_id),
            DevicePairingCode.account_id == str(account_id),
        )
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise DevicePairingError("pairing_not_found", "Pairing request was not found.")
    if row.status == "active":
        row.status = "cancelled"
        row.cancelled_at = now
        row.updated_at = now
    session.flush()
    return row


def claim_pairing_code(
    session,
    *,
    code: str,
    install_id: str,
    device_name: str,
    platform: str,
    os_version: str | None,
    app_version: str | None,
    locale: str | None,
    time_zone: str | None,
    device_limit_resolver: Callable[[User], int],
    now: datetime,
) -> ClaimedPairingCode:
    normalized_code = normalize_pairing_code(code)
    row = (
        session.query(DevicePairingCode)
        .filter(DevicePairingCode.code_hmac == _pairing_code_hmac(normalized_code))
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise DevicePairingError("pairing_code_invalid", "Pairing code is invalid.")
    row.claim_attempts = int(row.claim_attempts or 0) + 1
    row.updated_at = now
    if row.status != "active":
        raise DevicePairingError("pairing_code_used", "Pairing code is no longer active.")
    if row.expires_at <= now:
        row.status = "expired"
        session.flush()
        raise DevicePairingError("pairing_code_expired", "Pairing code has expired.")

    normalized_install_id = str(install_id or "").strip()[:128]
    if len(normalized_install_id) < 8:
        raise DevicePairingError("device_invalid", "Device identifier is invalid.")
    existing_device = (
        session.query(AccountDevice)
        .filter(AccountDevice.install_id == normalized_install_id)
        .with_for_update()
        .one_or_none()
    )
    if existing_device is not None:
        if str(existing_device.account_id) != str(row.account_id):
            raise DevicePairingError("device_identity_conflict", "This device belongs to another account.")
        raise DevicePairingError("device_already_registered", "This device is already linked. Use recovery instead.")

    owner = (
        session.query(User)
        .filter(User.account_id == str(row.account_id))
        .order_by(User.tg_id.asc())
        .first()
    )
    if owner is None:
        raise DevicePairingError("account_not_found", "Pairing account is unavailable.")
    device_limit = max(1, int(device_limit_resolver(owner)))
    active_devices = int(
        session.query(AccountDevice.id)
        .filter(
            AccountDevice.account_id == str(row.account_id),
            AccountDevice.state == "active",
            AccountDevice.revoked_at.is_(None),
        )
        .count()
    )
    if active_devices >= max(1, int(device_limit)):
        raise DevicePairingError("device_limit_reached", "Device limit has been reached.")

    try:
        issued = auth_session_service.issue_authenticated_device_session(
            session,
            account_id=str(row.account_id),
            install_id=normalized_install_id,
            device_name=str(device_name or "Новое устройство").strip()[:120] or "Новое устройство",
            platform=str(platform or "device").strip()[:32] or "device",
            os_version=os_version,
            app_version=app_version,
            locale=locale,
            time_zone=time_zone,
            scope="client",
            auth_origin="device_pairing",
            now=now,
        )
    except auth_session_service.AuthSessionError as exc:
        raise DevicePairingError(str(exc.code), str(exc)) from exc

    row.status = "claimed"
    row.claimed_device_id = str(issued.device_id)
    row.claimed_at = now
    row.updated_at = now
    session.flush()
    return ClaimedPairingCode(row=row, session=issued)


def pairing_code_public_payload(row: DevicePairingCode) -> dict[str, object | None]:
    return {
        "id": str(row.id),
        "status": str(row.status),
        "code_hint": str(row.code_hint or ""),
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "claimed_at": row.claimed_at.isoformat() if row.claimed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
