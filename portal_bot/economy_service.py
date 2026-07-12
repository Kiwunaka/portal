from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from models import AccountDevice, ConnectionEvidence, EntitlementGrant, User


TRIAL_RESERVATION_DAYS = 7
TRIAL_DURATION_DAYS = 5
TRIAL_SOURCE = "premium_trial"
TRIAL_EVIDENCE_KIND = "observer_connection"
FREE_CYCLE_DAYS = max(1, int(os.getenv("FREE_CYCLE_DAYS", "30")))


@dataclass(frozen=True)
class TrialActivationResult:
    grant: EntitlementGrant | None
    activated_now: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _safe_iso(value: datetime | None) -> str | None:
    return value.replace(microsecond=0).isoformat() if value else None


def _trial_key(*, account_id: str, device_id: str) -> str:
    return f"premium-trial:v1:{account_id}:{device_id}"


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def observer_evidence_key(*, identity_key: str, node_id: int, observed_at: datetime) -> str:
    stable_identity = str(identity_key or "").strip()
    if not stable_identity:
        raise ValueError("identity_key is required")
    canonical_observed_at = _naive_utc(observed_at)
    canonical = (
        f"v2|{TRIAL_EVIDENCE_KIND}|node:{int(node_id)}|identity:{stable_identity}|"
        f"observed:{canonical_observed_at.isoformat()}"
    )
    return f"observer:v2:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _trial_query(session, *, account_id: str):
    return session.query(EntitlementGrant).filter(
        EntitlementGrant.account_id == str(account_id),
        EntitlementGrant.source == TRIAL_SOURCE,
        EntitlementGrant.grant_kind == "premium_trial",
    )


def _users_for_account(session, account_id: str) -> list[User]:
    return session.query(User).filter(User.account_id == str(account_id)).order_by(User.tg_id.asc()).all()


def _has_other_active_access(session, *, account_id: str, trial_id: str, now: datetime) -> bool:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.id != str(trial_id),
            EntitlementGrant.status == "active",
            EntitlementGrant.reversed_at.is_(None),
            or_(EntitlementGrant.expires_at.is_(None), EntitlementGrant.expires_at > now),
        )
        .all()
    )
    return any(str(row.plan_code or "").strip().lower() not in {"", "free", "free_monthly", "trial"} for row in rows)


def _projection_has_other_active_access(session, *, account_id: str, now: datetime) -> bool:
    for user in _users_for_account(session, account_id):
        if not bool(user.is_active):
            continue
        if user.expiry_at is not None and user.expiry_at <= now:
            continue
        sub_type = str(user.sub_type or "").strip().upper()
        plan_code = str(user.current_plan_code or "").strip().lower()
        if sub_type == "FREE" and plan_code in {"", "free", "free_monthly", "trial"}:
            continue
        return True
    return False


def _project_reserved_trial(session, *, account_id: str, reservation_expires_at: datetime) -> None:
    for user in _users_for_account(session, account_id):
        current_plan = str(user.current_plan_code or "").strip().lower()
        current_type = str(user.sub_type or "").strip().upper()
        if current_type not in {"", "FREE"} and current_plan != "trial":
            continue
        user.sub_type = "FREE"
        user.current_plan_code = "trial"
        user.expiry_at = reservation_expires_at
        user.is_active = True
        user.trial_used = True


def _project_active_trial(session, *, account_id: str, expires_at: datetime) -> None:
    for user in _users_for_account(session, account_id):
        current_plan = str(user.current_plan_code or "").strip().lower()
        current_type = str(user.sub_type or "").strip().upper()
        if current_type not in {"", "FREE"} and current_plan != "trial":
            continue
        user.sub_type = "FREE"
        user.current_plan_code = "trial"
        user.expiry_at = expires_at
        user.is_active = True
        user.trial_used = True


def _mark_user_became_free(user: User, *, now: datetime) -> None:
    user.free_cycle_anchor_at = now
    user.free_cycle_last_reset_at = now
    user.free_cycle_next_reset_at = now + timedelta(days=FREE_CYCLE_DAYS)


def reserve_trial(session, *, account_id: str, device_id: str, now: datetime | None = None) -> EntitlementGrant:
    current_now = (now or _utcnow()).replace(microsecond=0)
    account_key = str(account_id or "").strip()
    device_key = str(device_id or "").strip()
    if not account_key or not device_key:
        raise ValueError("account_id and device_id are required")
    device = (
        session.query(AccountDevice)
        .filter(AccountDevice.id == device_key, AccountDevice.account_id == account_key)
        .with_for_update()
        .one_or_none()
    )
    if device is None:
        raise ValueError("device does not belong to account")

    account_trial = (
        _trial_query(session, account_id=account_key)
        .order_by(EntitlementGrant.created_at.asc())
        .with_for_update()
        .first()
    )
    if account_trial is not None:
        return account_trial

    idempotency_key = _trial_key(account_id=account_key, device_id=device_key)
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=idempotency_key).with_for_update().first()
    if existing is not None:
        return existing

    reservation_expires_at = current_now + timedelta(days=TRIAL_RESERVATION_DAYS)
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_key,
        legacy_tg_id=None,
        idempotency_key=idempotency_key,
        source=TRIAL_SOURCE,
        status="reserved",
        grant_kind="premium_trial",
        plan_code="trial",
        starts_at=None,
        expires_at=None,
        reserved_at=current_now,
        reservation_expires_at=reservation_expires_at,
        activated_at=None,
        duration_days=TRIAL_DURATION_DAYS,
        activation_evidence_id=None,
        provider="internal_economy",
        created_at=current_now,
        updated_at=current_now,
    )
    try:
        with session.begin_nested():
            session.add(grant)
            session.flush()
    except IntegrityError:
        winner = (
            _trial_query(session, account_id=account_key)
            .order_by(EntitlementGrant.created_at.asc())
            .with_for_update()
            .first()
        )
        if winner is None:
            raise
        return winner
    _project_reserved_trial(session, account_id=account_key, reservation_expires_at=reservation_expires_at)
    return grant


def record_connection_evidence(
    session,
    *,
    account_id: str,
    device_id: str | None,
    node_id: int,
    evidence_kind: str,
    observed_at: datetime,
    evidence_key: str,
) -> ConnectionEvidence:
    if str(evidence_kind or "") != TRIAL_EVIDENCE_KIND:
        raise ValueError("unsupported activation evidence kind")
    stable_key = str(evidence_key or "").strip()[:160]
    if not stable_key:
        raise ValueError("evidence_key is required")
    existing = session.query(ConnectionEvidence).filter_by(evidence_key=stable_key).first()
    if existing is not None:
        return existing

    row = ConnectionEvidence(
        id=str(uuid.uuid4()),
        account_id=str(account_id),
        device_id=str(device_id) if device_id else None,
        node_id=int(node_id),
        evidence_kind=TRIAL_EVIDENCE_KIND,
        observed_at=_naive_utc(observed_at),
        evidence_key=stable_key,
        created_at=_utcnow(),
    )
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
    except IntegrityError:
        return session.query(ConnectionEvidence).filter_by(evidence_key=stable_key).one()
    return row


def activate_reserved_trial(session, *, account_id: str, evidence: ConnectionEvidence) -> TrialActivationResult:
    if evidence.account_id != str(account_id) or evidence.evidence_kind != TRIAL_EVIDENCE_KIND:
        raise ValueError("evidence does not authorize this account")
    grant = (
        _trial_query(session, account_id=str(account_id))
        .filter(EntitlementGrant.status.in_(["reserved", "active"]))
        .order_by(EntitlementGrant.created_at.asc())
        .with_for_update()
        .first()
    )
    if grant is None or grant.status == "active":
        return TrialActivationResult(grant=grant, activated_now=False)
    observed_at = evidence.observed_at.replace(microsecond=0)
    if not grant.reserved_at or not grant.reservation_expires_at:
        return TrialActivationResult(grant=None, activated_now=False)
    if observed_at < grant.reserved_at or observed_at > grant.reservation_expires_at:
        return TrialActivationResult(grant=None, activated_now=False)

    expires_at = observed_at + timedelta(days=int(grant.duration_days or TRIAL_DURATION_DAYS))
    grant.status = "active"
    grant.starts_at = observed_at
    grant.activated_at = observed_at
    grant.expires_at = expires_at
    grant.activation_evidence_id = str(evidence.id)
    grant.updated_at = _utcnow()
    _project_active_trial(session, account_id=str(account_id), expires_at=expires_at)
    return TrialActivationResult(grant=grant, activated_now=True)


def read_trial_projection(session, *, account_id: str, now: datetime | None = None) -> dict[str, Any]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    grant = _trial_query(session, account_id=str(account_id)).order_by(EntitlementGrant.created_at.asc()).first()
    if grant is None:
        return {
            "state": "none",
            "reserved_at": None,
            "reservation_expires_at": None,
            "activated_at": None,
            "expires_at": None,
            "duration_days": TRIAL_DURATION_DAYS,
        }
    state = str(grant.status or "")
    if state == "reserved" and grant.reservation_expires_at and grant.reservation_expires_at <= current_now:
        state = "expired"
    if state == "active" and grant.expires_at and grant.expires_at <= current_now:
        state = "expired"
    return {
        "state": state,
        "reserved_at": _safe_iso(grant.reserved_at),
        "reservation_expires_at": _safe_iso(grant.reservation_expires_at),
        "activated_at": _safe_iso(grant.activated_at),
        "expires_at": _safe_iso(grant.expires_at),
        "duration_days": int(grant.duration_days or TRIAL_DURATION_DAYS),
    }


def expire_stale_trial_reservations(session, *, now: datetime | None = None) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.source == TRIAL_SOURCE,
            EntitlementGrant.grant_kind == "premium_trial",
            EntitlementGrant.status == "reserved",
            EntitlementGrant.reservation_expires_at.isnot(None),
            EntitlementGrant.reservation_expires_at <= current_now,
        )
        .order_by(EntitlementGrant.reservation_expires_at.asc(), EntitlementGrant.id.asc())
        .with_for_update()
        .all()
    )
    projected_free = 0
    preserved_other_access = 0
    for grant in rows:
        grant.status = "expired"
        grant.updated_at = current_now
        if _has_other_active_access(
            session,
            account_id=grant.account_id,
            trial_id=grant.id,
            now=current_now,
        ) or _projection_has_other_active_access(session, account_id=grant.account_id, now=current_now):
            preserved_other_access += 1
            continue
        for user in _users_for_account(session, grant.account_id):
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = current_now + timedelta(days=FREE_CYCLE_DAYS)
            user.is_active = True
            _mark_user_became_free(user, now=current_now)
        projected_free += 1
    return {
        "expired": len(rows),
        "projected_free": projected_free,
        "preserved_other_access": preserved_other_access,
    }
