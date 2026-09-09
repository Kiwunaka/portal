from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import and_, or_

from models import AntiAbuseAction, AntiAbuseCase, AntiAbuseEvent, SecurityEvent, User


RAW_IP_MAX_HOURS = 72
FULL_IP_HMAC_MAX_DAYS = 7
PREFIX_IP_HMAC_MAX_DAYS = 90
RETENTION_SWEEP_MAX_SECONDS = 3600
RETENTION_COUNT_KEYS = (
    "antiabuse_raw_ip",
    "antiabuse_full_hmac",
    "antiabuse_prefix_hmac",
    "security_event_ip",
    "user_last_ip",
    "client_network_metadata",
)


class AntiAbusePolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class IpHmacCandidate:
    version: int
    full_hmac: str
    prefix_hmac: str


@dataclass(frozen=True)
class InstallHmacCandidate:
    version: int
    install_hmac: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bounded_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(str(os.getenv(name, str(default))).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _hmac_version() -> int:
    return _bounded_env_int("ANTIABUSE_HMAC_VERSION", 1, minimum=1, maximum=2_147_483_647)


def _hmac_secret() -> str:
    return str(os.getenv("ANTIABUSE_HMAC_SECRET") or "").strip()


def _normalize_ip(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def _ip_prefix(normalized_ip: str) -> str:
    address = ipaddress.ip_address(normalized_ip)
    prefix_length = 24 if address.version == 4 else 64
    return str(ipaddress.ip_network(f"{address}/{prefix_length}", strict=False))


def _privacy_hmac(*, secret: str, purpose: str, version: int, value: str) -> str:
    payload = f"pokrov-antiabuse:{purpose}:v{int(version)}:{value}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _configured_hmac_secrets() -> list[tuple[int, str]]:
    current_version = _hmac_version()
    secrets_by_version: dict[int, str] = {}
    current_secret = _hmac_secret()
    if current_secret:
        secrets_by_version[current_version] = current_secret
    prefix = "ANTIABUSE_HMAC_SECRET_V"
    for key, raw_secret in os.environ.items():
        if not key.startswith(prefix):
            continue
        try:
            version = int(key[len(prefix) :])
        except ValueError:
            continue
        secret = str(raw_secret or "").strip()
        if not secret or version < 1 or version >= current_version:
            continue
        secrets_by_version[version] = secret
    return sorted(secrets_by_version.items(), reverse=True)


def ip_hmac_candidates(raw_ip: str | None) -> list[IpHmacCandidate]:
    normalized_ip = _normalize_ip(raw_ip)
    if not normalized_ip:
        return []

    normalized_prefix = _ip_prefix(normalized_ip)
    return [
        IpHmacCandidate(
            version=version,
            full_hmac=_privacy_hmac(
                secret=secret,
                purpose="ip-full",
                version=version,
                value=normalized_ip,
            ),
            prefix_hmac=_privacy_hmac(
                secret=secret,
                purpose="ip-prefix",
                version=version,
                value=normalized_prefix,
            ),
        )
        for version, secret in _configured_hmac_secrets()
    ]


def install_hmac_candidates(install_id: str | None) -> list[InstallHmacCandidate]:
    normalized_install = str(install_id or "").strip()[:128]
    if not normalized_install:
        return []
    return [
        InstallHmacCandidate(
            version=version,
            install_hmac=_privacy_hmac(
                secret=secret,
                purpose="install-id",
                version=version,
                value=normalized_install,
            ),
        )
        for version, secret in _configured_hmac_secrets()
    ]


def _safe_metadata(metadata: dict[str, Any] | None) -> str | None:
    safe: dict[str, Any] = {}
    for raw_key, raw_value in list(dict(metadata or {}).items())[:20]:
        key = str(raw_key or "").strip()[:64]
        if not key:
            continue
        if any(marker in key.lower() for marker in ("token", "secret", "password", "authorization", "api_key")):
            safe[key] = "[redacted]"
        elif raw_value is None or isinstance(raw_value, (bool, int, float)):
            safe[key] = raw_value
        else:
            safe[key] = str(raw_value)[:240]
    if not safe:
        return None
    return json.dumps(safe, ensure_ascii=False, separators=(",", ":"))


def _safe_reasons(reasons: Iterable[str] | None) -> str | None:
    source = [reasons] if isinstance(reasons, str) else list(reasons or [])
    values = [str(reason or "").strip()[:64] for reason in source]
    values = [value for value in values if value][:20]
    if not values:
        return None
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def record_antiabuse_event(
    session,
    *,
    event_kind: str,
    source: str,
    occurred_at: datetime | None = None,
    account_id: str | None = None,
    device_id: str | None = None,
    session_id: str | None = None,
    install_id: str | None = None,
    raw_ip: str | None = None,
    risk_score: float = 0.0,
    reasons: Iterable[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AntiAbuseEvent:
    now = occurred_at or _utcnow()
    normalized_ip = _normalize_ip(raw_ip)
    normalized_install = str(install_id or "").strip()[:128]
    secret = _hmac_secret()
    version = _hmac_version() if secret else None

    ip_full_hmac = None
    ip_prefix_hmac = None
    install_hmac = None
    if secret and version is not None:
        if normalized_ip:
            ip_full_hmac = _privacy_hmac(
                secret=secret,
                purpose="ip-full",
                version=version,
                value=normalized_ip,
            )
            ip_prefix_hmac = _privacy_hmac(
                secret=secret,
                purpose="ip-prefix",
                version=version,
                value=_ip_prefix(normalized_ip),
            )
        if normalized_install:
            install_hmac = _privacy_hmac(
                secret=secret,
                purpose="install-id",
                version=version,
                value=normalized_install,
            )

    raw_retention_hours = _bounded_env_int(
        "ANTIABUSE_RAW_IP_RETENTION_HOURS",
        RAW_IP_MAX_HOURS,
        minimum=1,
        maximum=RAW_IP_MAX_HOURS,
    )
    raw_retention_seconds = raw_retention_hours * 3600
    raw_storage_seconds = max(1, raw_retention_seconds - RETENTION_SWEEP_MAX_SECONDS)
    row = AntiAbuseEvent(
        id=str(uuid.uuid4()),
        account_id=str(account_id or "").strip()[:36] or None,
        device_id=str(device_id or "").strip()[:36] or None,
        session_id=str(session_id or "").strip()[:36] or None,
        event_kind=str(event_kind or "").strip()[:40] or "security_signal",
        source=str(source or "").strip()[:32] or "backend",
        occurred_at=now,
        install_hmac=install_hmac,
        raw_ip=normalized_ip,
        raw_ip_expires_at=now + timedelta(seconds=raw_storage_seconds) if normalized_ip else None,
        ip_full_hmac=ip_full_hmac,
        ip_prefix_hmac=ip_prefix_hmac,
        hmac_version=version,
        risk_score=max(0.0, min(100.0, float(risk_score or 0.0))),
        reasons_json=_safe_reasons(reasons),
        metadata_json=_safe_metadata(metadata),
        created_at=now,
    )
    session.add(row)
    return row


def _null_limited(query, *, field_name: str, limit: int) -> int:
    rows = query.with_for_update(skip_locked=True).limit(limit).all()
    for row in rows:
        setattr(row, field_name, None)
    return len(rows)


def _retention_queries(session, *, now: datetime) -> dict[str, tuple[Any, str]]:
    raw_hours = _bounded_env_int(
        "ANTIABUSE_RAW_IP_RETENTION_HOURS",
        RAW_IP_MAX_HOURS,
        minimum=1,
        maximum=RAW_IP_MAX_HOURS,
    )
    full_days = _bounded_env_int(
        "ANTIABUSE_FULL_IP_HMAC_RETENTION_DAYS",
        FULL_IP_HMAC_MAX_DAYS,
        minimum=1,
        maximum=FULL_IP_HMAC_MAX_DAYS,
    )
    prefix_days = _bounded_env_int(
        "ANTIABUSE_PREFIX_HMAC_RETENTION_DAYS",
        PREFIX_IP_HMAC_MAX_DAYS,
        minimum=1,
        maximum=PREFIX_IP_HMAC_MAX_DAYS,
    )
    raw_cutoff = now - timedelta(seconds=max(1, raw_hours * 3600 - RETENTION_SWEEP_MAX_SECONDS))
    full_cutoff = now - timedelta(seconds=max(1, full_days * 86400 - RETENTION_SWEEP_MAX_SECONDS))
    prefix_cutoff = now - timedelta(seconds=max(1, prefix_days * 86400 - RETENTION_SWEEP_MAX_SECONDS))

    return {
        "client_network_metadata": (
            session.query(AntiAbuseEvent)
            .filter(
                AntiAbuseEvent.event_kind == "client_network_context",
                AntiAbuseEvent.metadata_json.is_not(None),
                AntiAbuseEvent.occurred_at <= raw_cutoff,
            )
            .order_by(AntiAbuseEvent.occurred_at.asc(), AntiAbuseEvent.id.asc()),
            "metadata_json",
        ),
        "antiabuse_raw_ip": (
            session.query(AntiAbuseEvent)
            .filter(AntiAbuseEvent.raw_ip.is_not(None))
            .filter(
                or_(
                    AntiAbuseEvent.raw_ip_expires_at <= now,
                    and_(AntiAbuseEvent.raw_ip_expires_at.is_(None), AntiAbuseEvent.occurred_at <= raw_cutoff),
                )
            )
            .order_by(AntiAbuseEvent.occurred_at.asc(), AntiAbuseEvent.id.asc()),
            "raw_ip",
        ),
        "antiabuse_full_hmac": (
            session.query(AntiAbuseEvent)
            .filter(AntiAbuseEvent.ip_full_hmac.is_not(None), AntiAbuseEvent.occurred_at <= full_cutoff)
            .order_by(AntiAbuseEvent.occurred_at.asc(), AntiAbuseEvent.id.asc()),
            "ip_full_hmac",
        ),
        "antiabuse_prefix_hmac": (
            session.query(AntiAbuseEvent)
            .filter(AntiAbuseEvent.ip_prefix_hmac.is_not(None), AntiAbuseEvent.occurred_at <= prefix_cutoff)
            .order_by(AntiAbuseEvent.occurred_at.asc(), AntiAbuseEvent.id.asc()),
            "ip_prefix_hmac",
        ),
        "security_event_ip": (
            session.query(SecurityEvent)
            .filter(SecurityEvent.client_ip.is_not(None), SecurityEvent.created_at <= raw_cutoff)
            .order_by(SecurityEvent.created_at.asc(), SecurityEvent.id.asc()),
            "client_ip",
        ),
        "user_last_ip": (
            session.query(User)
            .filter(User.app_last_ip.is_not(None))
            .filter(or_(User.app_last_seen_at.is_(None), User.app_last_seen_at <= raw_cutoff))
            .order_by(User.app_last_seen_at.asc(), User.tg_id.asc()),
            "app_last_ip",
        ),
    }


def cleanup_antiabuse_retention(
    session,
    *,
    now: datetime | None = None,
    batch_limit: int = 1000,
) -> dict[str, int]:
    current = now or _utcnow()
    limit = max(1, min(10_000, int(batch_limit or 1)))
    counts = {
        key: _null_limited(query, field_name=field_name, limit=limit)
        for key, (query, field_name) in _retention_queries(session, now=current).items()
    }
    session.flush()
    return counts


def retention_backlog_counts(session, *, now: datetime | None = None) -> dict[str, int]:
    current = now or _utcnow()
    return {
        key: int(query.order_by(None).count())
        for key, (query, _field_name) in _retention_queries(session, now=current).items()
    }


def antiabuse_retention_status(session, *, now: datetime | None = None) -> dict[str, Any]:
    """Return bounded policy/backlog facts without exposing HMAC material."""
    current = now or _utcnow()
    return {
        "policy": {
            "raw_ip_hours": _bounded_env_int(
                "ANTIABUSE_RAW_IP_RETENTION_HOURS",
                RAW_IP_MAX_HOURS,
                minimum=1,
                maximum=RAW_IP_MAX_HOURS,
            ),
            "full_ip_hmac_days": _bounded_env_int(
                "ANTIABUSE_FULL_IP_HMAC_RETENTION_DAYS",
                FULL_IP_HMAC_MAX_DAYS,
                minimum=1,
                maximum=FULL_IP_HMAC_MAX_DAYS,
            ),
            "prefix_ip_hmac_days": _bounded_env_int(
                "ANTIABUSE_PREFIX_HMAC_RETENTION_DAYS",
                PREFIX_IP_HMAC_MAX_DAYS,
                minimum=1,
                maximum=PREFIX_IP_HMAC_MAX_DAYS,
            ),
            "disposition": "null_expired_raw_and_hmac_fields_keep_audit_rows",
        },
        "backlog": retention_backlog_counts(session, now=current),
    }


def read_retention_backlog(session_factory, *, now: datetime | None = None) -> dict[str, int]:
    session = session_factory()
    try:
        return retention_backlog_counts(session, now=now)
    finally:
        session.close()


def drain_antiabuse_retention(
    session_factory,
    *,
    now: datetime | None = None,
    batch_limit: int = 1000,
    max_batches: int = 0,
) -> dict[str, Any]:
    current = now or _utcnow()
    batch_cap = max(0, min(10_000, int(max_batches or 0)))
    totals = {key: 0 for key in RETENTION_COUNT_KEYS}
    changed_batches = 0
    while True:
        session = session_factory()
        try:
            counts = cleanup_antiabuse_retention(
                session,
                now=current,
                batch_limit=batch_limit,
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        if not any(counts.values()):
            break
        changed_batches += 1
        for key in RETENTION_COUNT_KEYS:
            totals[key] += int(counts.get(key, 0) or 0)
        if batch_cap and changed_batches >= batch_cap:
            break

    remaining = read_retention_backlog(session_factory, now=current)
    return {
        "status": "drained" if not any(remaining.values()) else "backlog_remaining",
        "changed_batches": changed_batches,
        "cleared": totals,
        "remaining": remaining,
    }


def set_operator_hard_lock(
    session,
    *,
    case_id: str,
    locked: bool,
    operator_tg_id: int,
    reason: str,
    now: datetime | None = None,
) -> AntiAbuseAction:
    actor_id = int(operator_tg_id or 0)
    if actor_id <= 0:
        raise AntiAbusePolicyError("hard lock requires an explicit operator identity")
    normalized_reason = str(reason or "").strip()[:255]
    if not normalized_reason:
        raise AntiAbusePolicyError("hard lock requires an operator reason")

    row = (
        session.query(AntiAbuseCase)
        .filter(AntiAbuseCase.id == str(case_id or "").strip())
        .with_for_update()
        .first()
    )
    if row is None:
        raise AntiAbusePolicyError("antiabuse case not found")

    current = now or _utcnow()
    row.hard_lock = bool(locked)
    row.assigned_operator_tg_id = actor_id
    row.updated_at = current
    action = AntiAbuseAction(
        id=str(uuid.uuid4()),
        case_id=str(row.id),
        account_id=str(row.account_id or "").strip()[:36] or None,
        action_kind="hard_lock_enabled" if locked else "hard_lock_disabled",
        actor_kind="operator",
        actor_tg_id=actor_id,
        reason=normalized_reason,
        created_at=current,
    )
    session.add(action)
    session.flush()
    return action
