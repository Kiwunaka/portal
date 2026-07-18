from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from account_security_errors import AccountRecoveryError
from auth_session_service import (
    APP_FRESH_AUTH_MAX_AGE_SECONDS,
    AuthSessionError,
    IssuedDeviceSession,
    issue_authenticated_device_session,
    promote_recovery_session,
    require_fresh_session,
)
from config import env_int
from models import (
    AccessKey,
    Account,
    AccountDevice,
    AntiAbuseEvent,
    AuthSession,
    NodeProvisioningJob,
    RecoveryCode,
    User,
)


RECOVERY_CODE_HMAC_VERSION = max(1, env_int("RECOVERY_CODE_HMAC_VERSION", 1))
RECOVERY_SESSION_TTL_SECONDS = 900
_RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_RECOVERY_CODE_RE = re.compile(r"^PKR-([A-Z2-9]{4})-([A-Z2-9]{4})-([A-Z2-9]{4})$")


@dataclass(frozen=True)
class IssuedRecoveryCode:
    code_id: str
    code: str
    code_hint: str
    version: int


@dataclass(frozen=True)
class RecoveryExchange:
    code_id: str
    session: IssuedDeviceSession


@dataclass(frozen=True)
class AccessReissueResult:
    mode: str
    session: IssuedDeviceSession
    provisioning_status: str
    provisioning_job_ids: tuple[int, ...]
    revoked_devices: int


def _recovery_secret(version: int) -> bytes:
    explicit = str(os.getenv(f"RECOVERY_CODE_HMAC_SECRET_V{int(version)}") or "").strip()
    current = str(os.getenv("RECOVERY_CODE_HMAC_SECRET") or "").strip()
    compatibility = str(os.getenv("WEBAPP_SESSION_SECRET") or "").strip()
    value = explicit or (current if int(version) == int(RECOVERY_CODE_HMAC_VERSION) else "") or compatibility
    if not value:
        raise AccountRecoveryError("recovery_not_configured")
    return value.encode("utf-8")


def normalize_recovery_code(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if _RECOVERY_CODE_RE.fullmatch(normalized) is None:
        raise AccountRecoveryError("recovery_code_invalid")
    return normalized


def _code_hmac(code: str, *, version: int) -> str:
    return hmac.new(
        _recovery_secret(version),
        f"pokrov-recovery-v{int(version)}:{code}".encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def _new_code() -> str:
    chunks = ["".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(4)) for _ in range(3)]
    return "PKR-" + "-".join(chunks)


def _translate_session_error(exc: AuthSessionError) -> AccountRecoveryError:
    return AccountRecoveryError(exc.code, message=exc.message)


def rotate_recovery_code(
    session: Session,
    *,
    account_id: str,
    actor_session_id: str,
    now: datetime,
) -> IssuedRecoveryCode:
    try:
        require_fresh_session(
            session,
            account_id=str(account_id),
            session_id=str(actor_session_id),
            now=now,
            allowed_scopes={"client"},
            fresh_auth_max_age_seconds=APP_FRESH_AUTH_MAX_AGE_SECONDS,
        )
    except AuthSessionError as exc:
        raise _translate_session_error(exc) from exc

    active_rows = (
        session.query(RecoveryCode)
        .filter(
            RecoveryCode.account_id == str(account_id),
            RecoveryCode.status == "active",
        )
        .with_for_update()
        .all()
    )
    for _ in range(30):
        raw_code = _new_code()
        digest = _code_hmac(raw_code, version=RECOVERY_CODE_HMAC_VERSION)
        if session.query(RecoveryCode.id).filter(RecoveryCode.code_hmac == digest).first():
            continue
        row = RecoveryCode(
            id=str(uuid.uuid4()),
            account_id=str(account_id),
            version=int(RECOVERY_CODE_HMAC_VERSION),
            code_hmac=digest,
            code_hint=f"PKR-****-****-{raw_code[-4:]}",
            status="active",
            created_at=now,
        )
        session.add(row)
        session.flush()
        for previous in active_rows:
            previous.status = "revoked"
            previous.revoked_at = now
            previous.replaced_by_code_id = str(row.id)
        session.flush()
        return IssuedRecoveryCode(
            code_id=str(row.id),
            code=raw_code,
            code_hint=str(row.code_hint),
            version=int(row.version),
        )
    raise AccountRecoveryError("recovery_code_generation_failed")


def exchange_recovery_code(
    session: Session,
    *,
    code: str,
    install_id: str,
    device_name: str,
    platform: str,
    now: datetime,
    os_version: str | None = None,
    app_version: str | None = None,
    locale: str | None = None,
    time_zone: str | None = None,
) -> RecoveryExchange:
    normalized = normalize_recovery_code(code)
    hint = f"PKR-****-****-{normalized[-4:]}"
    candidates = (
        session.query(RecoveryCode)
        .filter(RecoveryCode.status == "active", RecoveryCode.code_hint == hint)
        .all()
    )
    matched: RecoveryCode | None = None
    for candidate in candidates:
        try:
            expected = _code_hmac(normalized, version=int(candidate.version or 1))
        except AccountRecoveryError:
            continue
        if hmac.compare_digest(str(candidate.code_hmac or ""), expected):
            matched = candidate
            break
    if matched is None:
        raise AccountRecoveryError("recovery_code_invalid")

    account = (
        session.query(Account)
        .filter(Account.id == str(matched.account_id))
        .with_for_update()
        .first()
    )
    if account is None or str(account.status or "").strip().lower() != "active":
        raise AccountRecoveryError("account_unavailable")
    locked = (
        session.query(RecoveryCode)
        .filter(RecoveryCode.id == str(matched.id))
        .with_for_update()
        .first()
    )
    if locked is None or str(locked.status or "") != "active":
        raise AccountRecoveryError("recovery_code_invalid")
    expected = _code_hmac(normalized, version=int(locked.version or 1))
    if not hmac.compare_digest(str(locked.code_hmac or ""), expected):
        raise AccountRecoveryError("recovery_code_invalid")

    locked.status = "used"
    locked.used_at = now
    try:
        issued = issue_authenticated_device_session(
            session,
            account_id=str(account.id),
            install_id=str(install_id),
            device_name=str(device_name),
            platform=str(platform),
            os_version=os_version,
            app_version=app_version,
            locale=locale,
            time_zone=time_zone,
            scope="recovery",
            auth_origin="recovery_code",
            access_ttl_seconds=RECOVERY_SESSION_TTL_SECONDS,
            refresh_ttl_seconds=RECOVERY_SESSION_TTL_SECONDS,
            now=now,
        )
    except AuthSessionError as exc:
        raise _translate_session_error(exc) from exc
    session.flush()
    return RecoveryExchange(code_id=str(locked.id), session=issued)


def _queue_access_key_rotations(
    session: Session,
    *,
    account_id: str,
    user_ids: list[int],
    mode: str,
    now: datetime,
) -> tuple[int, ...]:
    keys = (
        session.query(AccessKey)
        .filter(AccessKey.tg_id.in_(user_ids), AccessKey.state.in_(["active", "rotation_requested"]))
        .with_for_update()
        .all()
        if user_ids
        else []
    )
    job_ids: list[int] = []
    for key in keys:
        existing = (
            session.query(NodeProvisioningJob)
            .filter(
                NodeProvisioningJob.key_id == int(key.id),
                NodeProvisioningJob.job_type == "rotate_access_key",
                NodeProvisioningJob.status.in_(["queued", "running"]),
            )
            .first()
        )
        if existing is not None:
            job_ids.append(int(existing.id))
            continue
        key.state = "rotation_requested"
        key.updated_at = now
        job = NodeProvisioningJob(
            tg_id=int(key.tg_id),
            key_id=int(key.id),
            node_code=str(key.node_code or "") or None,
            job_type="rotate_access_key",
            status="queued",
            desired_state_json=json.dumps(
                {
                    "reason": "self_service_recovery",
                    "mode": mode,
                    "account_id": str(account_id),
                    "pool_code": str(key.pool_code or ""),
                },
                ensure_ascii=True,
                separators=(",", ":"),
            ),
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.flush()
        job_ids.append(int(job.id))
    return tuple(job_ids)


def complete_access_reissue(
    session: Session,
    *,
    account_id: str,
    recovery_session_id: str,
    mode: str,
    device_limit: int,
    now: datetime,
) -> AccessReissueResult:
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode not in {"vpn_credentials", "account_lockdown"}:
        raise AccountRecoveryError("reissue_mode_invalid")

    discovered = (
        session.query(AuthSession.id, AuthSession.device_id)
        .filter(
            AuthSession.id == str(recovery_session_id),
            AuthSession.account_id == str(account_id),
            AuthSession.scope == "recovery",
            AuthSession.revoked_at.is_(None),
            AuthSession.access_expires_at > now,
        )
        .first()
    )
    if discovered is None:
        raise AccountRecoveryError("recovery_session_invalid")

    users = (
        session.query(User)
        .filter(User.account_id == str(account_id))
        .order_by(User.tg_id.asc())
        .with_for_update()
        .all()
    )
    if not users:
        raise AccountRecoveryError("account_unavailable")
    account = (
        session.query(Account)
        .filter(Account.id == str(account_id))
        .with_for_update()
        .first()
    )
    if account is None or str(account.status or "").strip().lower() != "active":
        raise AccountRecoveryError("account_unavailable")
    if normalized_mode == "vpn_credentials":
        recovery_device = (
            session.query(AccountDevice)
            .filter(
                AccountDevice.id == str(discovered.device_id or ""),
                AccountDevice.account_id == str(account_id),
            )
            .with_for_update()
            .first()
        )
        if recovery_device is None or recovery_device.revoked_at is not None:
            raise AccountRecoveryError("recovery_session_invalid")
        active_devices = (
            session.query(AccountDevice.id)
            .filter(
                AccountDevice.account_id == str(account_id),
                AccountDevice.state == "active",
                AccountDevice.revoked_at.is_(None),
            )
            .count()
        )
        projected_devices = int(active_devices)
        if str(recovery_device.state or "").strip().lower() != "active":
            projected_devices += 1
        if projected_devices > max(1, int(device_limit)):
            raise AccountRecoveryError("device_limit_reached")
    try:
        issued, revoked_devices = promote_recovery_session(
            session,
            account_id=str(account_id),
            recovery_session_id=str(recovery_session_id),
            lockdown=normalized_mode == "account_lockdown",
            now=now,
        )
    except AuthSessionError as exc:
        code = "recovery_session_invalid" if exc.code in {"session_revoked", "session_not_found"} else exc.code
        raise AccountRecoveryError(code, message=exc.message) from exc

    for user in users:
        user.sub_token = secrets.token_urlsafe(32)
    user_ids = [int(user.tg_id) for user in users]
    job_ids = _queue_access_key_rotations(
        session,
        account_id=str(account_id),
        user_ids=user_ids,
        mode=normalized_mode,
        now=now,
    )
    session.add(
        AntiAbuseEvent(
            id=str(uuid.uuid4()),
            account_id=str(account_id),
            device_id=str(issued.device_id),
            session_id=str(recovery_session_id),
            event_kind="access_reissue",
            source="self_service_recovery",
            occurred_at=now,
            risk_score=0.0,
            reasons_json=json.dumps([normalized_mode], ensure_ascii=True),
            metadata_json=json.dumps(
                {
                    "mode": normalized_mode,
                    "queued_key_rotations": len(job_ids),
                    "revoked_devices": int(revoked_devices),
                },
                ensure_ascii=True,
                separators=(",", ":"),
            ),
            created_at=now,
        )
    )
    session.flush()
    return AccessReissueResult(
        mode=normalized_mode,
        session=issued,
        provisioning_status="pending" if job_ids else "not_required",
        provisioning_job_ids=job_ids,
        revoked_devices=int(revoked_devices),
    )
