from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import AccountExperienceState, ConnectionEvidence


CURRENT_ONBOARDING_VERSION = 1
ONBOARDING_PENDING = "pending"
ONBOARDING_COMPLETED = "completed"
ONBOARDING_SKIPPED = "skipped"
ONBOARDING_FINAL_STATUSES = frozenset({ONBOARDING_COMPLETED, ONBOARDING_SKIPPED})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _safe_iso(value: datetime | None) -> str | None:
    return value.replace(microsecond=0).isoformat() if value else None


def _earliest(*values: datetime | None) -> datetime | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _state_row(session: Session, *, account_id: str, lock: bool = False) -> AccountExperienceState | None:
    query = session.query(AccountExperienceState).filter_by(account_id=str(account_id))
    if lock:
        query = query.with_for_update()
    return query.first()


def _ensure_state(
    session: Session,
    *,
    account_id: str,
    now: datetime,
) -> AccountExperienceState:
    account_key = str(account_id or "").strip()
    if not account_key:
        raise ValueError("account_id is required")
    row = _state_row(session, account_id=account_key, lock=True)
    if row is not None:
        return row
    candidate = AccountExperienceState(
        account_id=account_key,
        onboarding_version=CURRENT_ONBOARDING_VERSION,
        onboarding_status=ONBOARDING_PENDING,
        created_at=now,
        updated_at=now,
    )
    try:
        with session.begin_nested():
            session.add(candidate)
            session.flush()
        return candidate
    except IntegrityError:
        # Runtime self-report and observer evidence can arrive together. The
        # unique account row is the lock; reuse the concurrent winner.
        row = _state_row(session, account_id=account_key, lock=True)
        if row is None:
            raise
        return row


def set_onboarding_status(
    session: Session,
    *,
    account_id: str,
    status: str,
    now: datetime | None = None,
) -> AccountExperienceState:
    normalized = str(status or "").strip().lower()
    if normalized not in ONBOARDING_FINAL_STATUSES:
        raise ValueError("unsupported onboarding status")
    current_now = now or _utcnow()
    row = _ensure_state(session, account_id=str(account_id), now=current_now)
    row.onboarding_version = CURRENT_ONBOARDING_VERSION
    row.onboarding_status = normalized
    row.onboarding_updated_at = current_now
    row.updated_at = current_now
    session.flush()
    return row


def record_first_connection_reported(
    session: Session,
    *,
    account_id: str,
    reported_at: datetime | None = None,
) -> AccountExperienceState:
    current_now = reported_at or _utcnow()
    row = _ensure_state(session, account_id=str(account_id), now=current_now)
    row.first_connection_reported_at = _earliest(row.first_connection_reported_at, current_now)
    row.updated_at = current_now
    session.flush()
    return row


def record_first_connection_verified(
    session: Session,
    *,
    account_id: str,
    verified_at: datetime,
) -> AccountExperienceState:
    row = _ensure_state(session, account_id=str(account_id), now=verified_at)
    row.first_connection_verified_at = _earliest(row.first_connection_verified_at, verified_at)
    row.updated_at = _utcnow()
    session.flush()
    return row


def build_experience_snapshot(
    session: Session,
    *,
    account_id: str,
    app_identity_known: bool,
) -> dict[str, Any]:
    account_key = str(account_id or "").strip()
    row = _state_row(session, account_id=account_key) if account_key else None
    evidence_at = None
    if account_key:
        evidence_at = (
            session.query(func.min(ConnectionEvidence.observed_at))
            .filter(ConnectionEvidence.account_id == account_key)
            .scalar()
        )

    onboarding_version = int(getattr(row, "onboarding_version", CURRENT_ONBOARDING_VERSION) or 0)
    onboarding_status = str(getattr(row, "onboarding_status", ONBOARDING_PENDING) or ONBOARDING_PENDING)
    reported_at = getattr(row, "first_connection_reported_at", None)
    verified_at = _earliest(getattr(row, "first_connection_verified_at", None), evidence_at)
    connection_state = "verified" if verified_at else "reported" if reported_at else "none"
    connected_once = connection_state != "none"

    return {
        "onboarding": {
            "version": onboarding_version,
            "status": onboarding_status,
            "should_show": bool(
                not connected_once
                and (
                    onboarding_version < CURRENT_ONBOARDING_VERSION
                    or onboarding_status == ONBOARDING_PENDING
                )
            ),
            "updated_at": _safe_iso(getattr(row, "onboarding_updated_at", None)),
        },
        "first_connection": {
            "state": connection_state,
            "reported_at": _safe_iso(reported_at),
            "verified_at": _safe_iso(verified_at),
        },
        "next_step": (
            "complete"
            if connected_once
            else "connect"
            if app_identity_known
            else "install"
        ),
    }


_ONBOARDING_STATUS_RANK = {
    ONBOARDING_PENDING: 0,
    ONBOARDING_SKIPPED: 1,
    ONBOARDING_COMPLETED: 2,
}


def reconcile_account_merge(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    source = _state_row(session, account_id=str(source_account_id), lock=True)
    if source is None:
        return
    target = _state_row(session, account_id=str(target_account_id), lock=True)
    if target is None:
        source.account_id = str(target_account_id)
        source.updated_at = now
        session.flush()
        return

    source_status = str(source.onboarding_status or ONBOARDING_PENDING)
    target_status = str(target.onboarding_status or ONBOARDING_PENDING)
    if _ONBOARDING_STATUS_RANK.get(source_status, 0) > _ONBOARDING_STATUS_RANK.get(target_status, 0):
        target.onboarding_status = source_status
        target.onboarding_updated_at = source.onboarding_updated_at
    elif source_status == target_status:
        target.onboarding_updated_at = _earliest(target.onboarding_updated_at, source.onboarding_updated_at)
    target.onboarding_version = max(int(target.onboarding_version or 0), int(source.onboarding_version or 0))
    target.first_connection_reported_at = _earliest(
        target.first_connection_reported_at,
        source.first_connection_reported_at,
    )
    target.first_connection_verified_at = _earliest(
        target.first_connection_verified_at,
        source.first_connection_verified_at,
    )
    target.created_at = _earliest(target.created_at, source.created_at) or now
    target.updated_at = now
    session.delete(source)
    session.flush()
