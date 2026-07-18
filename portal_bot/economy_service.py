from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from free_cycle_service import FREE_CYCLE_DAYS, queue_free_profile_reentry
from models import (
    AccessKey,
    Account,
    AccountDevice,
    ConnectionEvidence,
    EntitlementGrant,
    ReferralBonusQueue,
    ReferralRelationship,
    ReferralTransition,
    User,
)


TRIAL_RESERVATION_DAYS = 7
TRIAL_DURATION_DAYS = 5
TRIAL_SOURCE = "premium_trial"
TRIAL_EVIDENCE_KIND = "observer_connection"
PRE_FIRST_PAYMENT_PREMIUM_CAP_DAYS = 15
CHANNEL_GRANT_DAYS = 5
GRANDFATHERED_CHANNEL_GRANT_DAYS = 10
FRIEND_GRANT_DAYS = 5
CHANNEL_GRACE_HOURS = 24
REFERRER_HOLD_HOURS = 72
REFERRER_GRANT_DAYS = 15


@dataclass(frozen=True)
class TrialActivationResult:
    grant: EntitlementGrant | None
    activated_now: bool


@dataclass(frozen=True)
class PaymentGrantResult:
    grant: EntitlementGrant
    is_first_payment: bool
    relationship: ReferralRelationship | None


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


def _mark_user_became_free(session, user: User, *, now: datetime) -> None:
    queue_free_profile_reentry(session, user=user, source="economy_projection", now=now)


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
        reserved_trial = _trial_query(session, account_id=str(account_id)).filter_by(status="reserved").first()
        if reserved_trial is None and session.query(ReferralRelationship.id).filter_by(referred_account_id=str(account_id)).first():
            activate_referred_friend_reward(session, account_id=str(account_id), evidence=existing, now=existing.observed_at)
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
        row = session.query(ConnectionEvidence).filter_by(evidence_key=stable_key).one()
    reserved_trial = _trial_query(session, account_id=str(account_id)).filter_by(status="reserved").first()
    if reserved_trial is None and session.query(ReferralRelationship.id).filter_by(referred_account_id=str(account_id)).first():
        activate_referred_friend_reward(session, account_id=str(account_id), evidence=row, now=row.observed_at)
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
    if session.query(ReferralRelationship.id).filter_by(referred_account_id=str(account_id)).first():
        activate_referred_friend_reward(session, account_id=str(account_id), evidence=evidence, now=observed_at)
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
            _mark_user_became_free(session, user, now=current_now)
        projected_free += 1
    return {
        "expired": len(rows),
        "projected_free": projected_free,
        "preserved_other_access": preserved_other_access,
    }


def _grant_metadata(grant: EntitlementGrant) -> dict[str, Any]:
    try:
        value = json.loads(str(grant.metadata_json or "{}"))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _set_grant_metadata(grant: EntitlementGrant, value: dict[str, Any]) -> None:
    grant.metadata_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _account_first_payment_done(session, *, account_id: str) -> bool:
    return bool(
        session.query(EntitlementGrant.id)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source == "provider_payment",
            EntitlementGrant.status.in_(["active", "recorded", "expired"]),
        )
        .first()
    )


def _prepayment_granted_days(session, *, account_id: str) -> int:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source.in_(
                [TRIAL_SOURCE, "telegram_channel", "telegram_channel_grandfathered", "referral_friend"]
            ),
            EntitlementGrant.status.in_(["reserved", "active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
        )
        .all()
    )
    return sum(max(0, int(row.duration_days or 0)) for row in rows)


def _available_prepayment_days(session, *, account_id: str, requested_days: int) -> int:
    requested = max(0, int(requested_days))
    if _account_first_payment_done(session, account_id=account_id):
        return requested
    used = _prepayment_granted_days(session, account_id=account_id)
    return min(requested, max(0, PRE_FIRST_PAYMENT_PREMIUM_CAP_DAYS - used))


def _legacy_snapshot_policy(grant: EntitlementGrant) -> str | None:
    if str(grant.source or "").strip().lower() != "legacy_snapshot":
        return None
    metadata = _grant_metadata(grant)
    sub_type = str(metadata.get("sub_type") or "").strip().upper()
    plan_code = str(grant.plan_code or "").strip().lower()
    if sub_type in {"FREE", "PAID", "TRIAL", "BONUS"}:
        return sub_type
    if plan_code in {"free", "free_monthly"} or plan_code.startswith("free_"):
        return "FREE"
    if "trial" in plan_code:
        return "TRIAL"
    if any(token in plan_code for token in ("bonus", "referral", "channel")):
        return "BONUS"
    if plan_code and plan_code not in {"legacy", "unknown"}:
        return "PAID"
    return None


def _is_explicit_premium_contribution(grant: EntitlementGrant) -> bool:
    return str(grant.grant_kind or "").strip().lower() in {
        "paid_access",
        "premium_trial",
        "premium_bonus",
    }


def _is_premium_contribution(grant: EntitlementGrant) -> bool:
    return _is_explicit_premium_contribution(grant) or _legacy_snapshot_policy(grant) in {
        "PAID",
        "TRIAL",
        "BONUS",
    }


def _active_legacy_snapshots(session, *, account_id: str, now: datetime) -> list[EntitlementGrant]:
    return (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source == "legacy_snapshot",
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at > now,
        )
        .order_by(EntitlementGrant.expires_at.desc(), EntitlementGrant.created_at.asc(), EntitlementGrant.id.asc())
        .with_for_update()
        .all()
    )


def _legacy_snapshot_baselines(
    session,
    *,
    account_id: str,
    now: datetime,
) -> tuple[EntitlementGrant | None, datetime | None]:
    snapshots = _active_legacy_snapshots(session, account_id=account_id, now=now)
    premium = next((row for row in snapshots if _legacy_snapshot_policy(row) in {"PAID", "TRIAL", "BONUS"}), None)
    free_expiry = max(
        [row.expires_at for row in snapshots if _legacy_snapshot_policy(row) == "FREE" and row.expires_at],
        default=None,
    )
    return premium, free_expiry


def _premium_projection_end(session, *, account_id: str, now: datetime) -> datetime:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at > now,
        )
        .all()
    )
    expiries = [row.expires_at for row in rows if _is_premium_contribution(row) and row.expires_at is not None]
    return max([now, *expiries])


def _project_additive_days(session, *, account_id: str, days: int, now: datetime) -> tuple[datetime, datetime]:
    users = _users_for_account(session, account_id)
    if not users:
        raise ValueError("account has no compatibility user projection")
    baseline = _premium_projection_end(session, account_id=account_id, now=now)
    projected = baseline + timedelta(days=max(0, int(days)))
    for user in users:
        user.expiry_at = projected
        user.is_active = True
    return baseline, projected


def _canonical_account_id(session, account_id: str) -> str:
    account_key = str(account_id or "").strip()
    visited: set[str] = set()
    while account_key and account_key not in visited:
        visited.add(account_key)
        account = session.query(Account).filter_by(id=account_key).with_for_update().one_or_none()
        if account is None:
            raise ValueError("account_not_found")
        if str(account.status or "").lower() != "merged" or not account.merged_into_account_id:
            return account_key
        account_key = str(account.merged_into_account_id)
    raise ValueError("invalid_account_merge_chain")


def _projection_baseline_key(account_id: str) -> str:
    return f"compatibility-projection:v1:{account_id}"


def _ensure_projection_baseline_grant(session, *, account_id: str, now: datetime) -> EntitlementGrant | None:
    users = _users_for_account(session, account_id)
    future_expiries = [
        user.expiry_at
        for user in users
        if str(user.sub_type or "").upper() == "PAID"
        and user.expiry_at is not None
        and user.expiry_at > now
    ]
    if not future_expiries:
        return None
    projection_expiry = max(future_expiries)
    represented_rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.expires_at.isnot(None),
        )
        .all()
    )
    represented_expiry = max(
        [
            row.expires_at
            for row in represented_rows
            if _is_premium_contribution(row) and row.expires_at is not None
        ],
        default=None,
    )
    if represented_expiry is not None and represented_expiry >= projection_expiry:
        return None
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=_projection_baseline_key(account_id)).first()
    if existing is not None:
        if existing.expires_at is None or existing.expires_at < projection_expiry:
            existing.expires_at = projection_expiry
            existing.updated_at = now
        return existing
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=str(account_id),
        idempotency_key=_projection_baseline_key(account_id),
        source="compatibility_projection",
        status="active",
        grant_kind="paid_access",
        plan_code=next(
            (
                str(user.current_plan_code)
                for user in users
                if str(user.current_plan_code or "").strip()
            ),
            "legacy",
        ),
        starts_at=now,
        expires_at=projection_expiry,
        activated_at=now,
        duration_days=max(0, int((projection_expiry - now).total_seconds() // 86400)),
        provider="compatibility_projection",
        created_at=now,
        updated_at=now,
    )
    _set_grant_metadata(grant, {"duration_seconds": int((projection_expiry - now).total_seconds())})
    session.add(grant)
    session.flush()
    return grant


def _active_projection_grants(session, *, account_id: str, now: datetime) -> list[EntitlementGrant]:
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.starts_at.isnot(None),
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at > now,
        )
        .order_by(EntitlementGrant.starts_at.asc(), EntitlementGrant.created_at.asc(), EntitlementGrant.id.asc())
        .with_for_update()
        .all()
    )
    return [row for row in rows if _is_explicit_premium_contribution(row)]


def _grant_projects_paid_policy(grant: EntitlementGrant) -> bool:
    return grant.grant_kind == "paid_access"


def rebuild_account_entitlement_projection(session, *, account_id: str, now: datetime | None = None) -> datetime:
    current_now = (now or _utcnow()).replace(microsecond=0)
    account_key = _canonical_account_id(session, account_id)
    users = _users_for_account(session, account_key)
    legacy_premium, legacy_free_expiry = _legacy_snapshot_baselines(
        session,
        account_id=account_key,
        now=current_now,
    )
    grants = _active_projection_grants(session, account_id=account_key, now=current_now)
    remaining: list[tuple[EntitlementGrant, timedelta]] = []
    cursor = max(current_now, legacy_premium.expires_at) if legacy_premium is not None else current_now
    for grant in grants:
        interval_start = max(current_now, cursor, grant.starts_at or current_now)
        interval_end = grant.expires_at or interval_start
        if interval_end > interval_start:
            remaining.append((grant, interval_end - interval_start))

    for grant, duration in remaining:
        grant.starts_at = cursor
        cursor += duration
        grant.expires_at = cursor
        grant.updated_at = current_now

    paid_grants = [
        grant
        for grant, _duration in remaining
        if _grant_projects_paid_policy(grant)
    ]
    bonus_grants = [
        grant
        for grant, _duration in remaining
        if grant.grant_kind in {"premium_bonus", "premium_trial"}
    ]
    latest_paid = max(paid_grants, key=lambda row: (row.activated_at or row.created_at, row.id), default=None)
    latest_bonus = max(bonus_grants, key=lambda row: (row.activated_at or row.created_at, row.id), default=None)
    legacy_policy = _legacy_snapshot_policy(legacy_premium) if legacy_premium is not None else None
    premium_active = cursor > current_now
    for user in users:
        was_free_monthly = (
            str(user.sub_type or "").strip().upper() == "FREE"
            and str(user.current_plan_code or "").strip().lower() in {"", "free", "free_monthly"}
        )
        user.is_active = True
        if latest_paid is not None or legacy_policy == "PAID":
            user.expiry_at = cursor
            user.sub_type = "PAID"
            user.current_plan_code = str(
                (latest_paid.plan_code if latest_paid is not None else legacy_premium.plan_code)
                or user.current_plan_code
                or "paid"
            )
        elif premium_active and (latest_bonus is not None or legacy_policy in {"BONUS", "TRIAL"}):
            user.expiry_at = cursor
            user.sub_type = "BONUS"
            user.current_plan_code = str(
                (latest_bonus.plan_code if latest_bonus is not None else legacy_premium.plan_code) or "bonus"
            )
        elif str(user.sub_type or "").upper() not in {"MANUAL", "VIP", "PRO"}:
            user.expiry_at = max(
                current_now,
                user.free_cycle_next_reset_at or current_now,
                legacy_free_expiry or current_now,
            )
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            if not was_free_monthly:
                _mark_user_became_free(session, user, now=current_now)
    tg_ids = [int(user.tg_id) for user in users]
    if tg_ids:
        for key in session.query(AccessKey).filter(AccessKey.tg_id.in_(tg_ids), AccessKey.state == "active").all():
            key.pool_code = "premium_pool" if premium_active else "free_pool"
            key.updated_at = current_now
    session.flush()
    return cursor


def rebuild_due_entitlement_projections(session, *, now: datetime | None = None) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    due_rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
            EntitlementGrant.expires_at.isnot(None),
            EntitlementGrant.expires_at <= current_now,
        )
        .all()
    )
    account_ids = [str(row.account_id) for row in due_rows if _is_premium_contribution(row)]
    rebuilt = 0
    expired = 0
    for account_id in sorted(set(account_ids)):
        rows = (
            session.query(EntitlementGrant)
            .filter(
                EntitlementGrant.account_id == account_id,
                EntitlementGrant.status == "active",
                EntitlementGrant.reversed_at.is_(None),
                EntitlementGrant.expires_at.isnot(None),
                EntitlementGrant.expires_at <= current_now,
            )
            .with_for_update()
            .all()
        )
        for row in rows:
            if not _is_premium_contribution(row):
                continue
            row.status = "expired"
            row.updated_at = current_now
            expired += 1
        rebuild_account_entitlement_projection(session, account_id=account_id, now=current_now)
        rebuilt += 1
    session.flush()
    return {"rebuilt": rebuilt, "expired": expired}


def _provider_payment_key(provider: str, order_id: str) -> str:
    provider_key = str(provider or "").strip().lower()
    order_key = str(order_id or "").strip()
    if not provider_key or not order_key:
        raise ValueError("provider and order_id are required")
    digest = hashlib.sha256(order_key.encode("utf-8")).hexdigest()
    return f"provider-payment:v1:{provider_key}:{digest}"


def _provider_order_key(grant: EntitlementGrant) -> str:
    return f"{str(grant.provider or '').strip().lower()}:{str(grant.external_order_id or '').strip()}"[:160]


def normalize_account_payment_history(
    session,
    *,
    account_id: str,
    now: datetime | None = None,
) -> tuple[EntitlementGrant | None, ReferralRelationship | None]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    account_key = _canonical_account_id(session, account_id)
    facts = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.source == "provider_payment",
            EntitlementGrant.status.in_(["active", "recorded", "expired"]),
        )
        .with_for_update()
        .all()
    )
    facts.sort(
        key=lambda row: (
            _naive_utc(row.activated_at or row.created_at or datetime.max),
            str(row.external_order_id or ""),
            str(row.provider or ""),
            str(row.id),
        )
    )
    first = facts[0] if facts else None
    for fact in facts:
        metadata = _grant_metadata(fact)
        metadata["is_first_payment"] = first is not None and fact.id == first.id
        if str(fact.grant_kind or "") == "paid_access":
            metadata["projection_already_applied"] = True
        _set_grant_metadata(fact, metadata)
        fact.updated_at = current_now

    relationship = (
        session.query(ReferralRelationship)
        .filter_by(referred_account_id=account_key)
        .with_for_update()
        .one_or_none()
    )
    if first is None or relationship is None:
        session.flush()
        return first, relationship

    payment_key = _provider_order_key(first)
    paid_at = _naive_utc(first.activated_at or first.created_at or current_now)
    if not relationship.first_payment_key:
        relationship = queue_first_payment_referrer_reward(
            session,
            referred_account_id=account_key,
            payment_key=payment_key,
            paid_at=paid_at,
        )
    relationship.first_payment_key = payment_key
    relationship.first_payment_at = paid_at
    relationship.hold_until = paid_at + timedelta(hours=REFERRER_HOLD_HOURS)
    if str(relationship.status or "").lower() in {"linked", "holding"}:
        relationship.status = "holding"
    relationship.updated_at = current_now
    transition_key = f"referral-payment-normalized:v1:{relationship.id}:{first.id}"[:160]
    _record_referral_transition(
        session,
        relationship=relationship,
        transition_key=transition_key,
        transition_kind="first_payment_normalized",
        status=str(relationship.status),
        occurred_at=current_now,
        metadata={
            "payment_key": payment_key,
            "paid_at": paid_at.isoformat(),
            "hold_until": relationship.hold_until.isoformat(),
        },
    )
    session.flush()
    return first, relationship


def record_successful_payment_grant(
    session,
    *,
    account_id: str,
    legacy_tg_id: int | None,
    provider: str,
    order_id: str,
    plan_code: str,
    duration_days: int,
    paid_at: datetime,
) -> PaymentGrantResult:
    current_paid_at = _naive_utc(paid_at)
    account_key = _canonical_account_id(session, account_id)
    stable_key = _provider_payment_key(provider, order_id)
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=stable_key).with_for_update().one_or_none()
    if existing is not None:
        existing_account_key = _canonical_account_id(session, str(existing.account_id))
        if existing_account_key != account_key:
            raise ValueError("payment_account_mismatch")
        existing.account_id = account_key
        metadata = _grant_metadata(existing)
        _first, relationship = normalize_account_payment_history(
            session,
            account_id=account_key,
            now=current_paid_at,
        )
        metadata = _grant_metadata(existing)
        if str(existing.grant_kind or "") == "payment_fact":
            if bool(metadata.get("projection_already_applied")):
                projected_expiry = rebuild_account_entitlement_projection(
                    session,
                    account_id=account_key,
                    now=current_paid_at,
                )
                for user in _users_for_account(session, account_key):
                    user.first_purchase_done = True
                    user.expiry_at = projected_expiry
                    user.is_active = True
                session.flush()
                return PaymentGrantResult(
                    grant=existing,
                    is_first_payment=bool(metadata.get("is_first_payment")),
                    relationship=relationship,
                )
            _ensure_projection_baseline_grant(session, account_id=account_key, now=current_paid_at)
            starts_at, expires_at = _project_additive_days(
                session,
                account_id=account_key,
                days=max(1, int(duration_days)),
                now=current_paid_at,
            )
            existing.status = "active"
            existing.grant_kind = "paid_access"
            existing.plan_code = str(plan_code or existing.plan_code or "paid")[:32]
            existing.starts_at = starts_at
            existing.expires_at = expires_at
            existing.activated_at = existing.activated_at or current_paid_at
            existing.duration_days = max(1, int(duration_days))
            existing.legacy_tg_id = int(legacy_tg_id) if legacy_tg_id is not None else existing.legacy_tg_id
            existing.updated_at = current_paid_at
            metadata["fulfilled_from_backfilled_fact"] = True
            metadata["projection_already_applied"] = True
            _set_grant_metadata(existing, metadata)
            _first, relationship = normalize_account_payment_history(
                session,
                account_id=account_key,
                now=current_paid_at,
            )
            metadata = _grant_metadata(existing)
            for user in _users_for_account(session, account_key):
                user.first_purchase_done = True
                user.sub_type = "PAID"
                user.current_plan_code = str(existing.plan_code or "paid")
                user.expiry_at = expires_at
                user.is_active = True
            session.flush()
            return PaymentGrantResult(
                grant=existing,
                is_first_payment=bool(metadata.get("is_first_payment")),
                relationship=relationship,
            )
        projected_expiry = rebuild_account_entitlement_projection(
            session,
            account_id=account_key,
            now=current_paid_at,
        )
        for user in _users_for_account(session, account_key):
            user.first_purchase_done = True
            user.sub_type = "PAID"
            user.current_plan_code = str(existing.plan_code or user.current_plan_code or "paid")
            user.expiry_at = projected_expiry
            user.is_active = True
        _first, relationship = normalize_account_payment_history(
            session,
            account_id=account_key,
            now=current_paid_at,
        )
        metadata = _grant_metadata(existing)
        return PaymentGrantResult(
            grant=existing,
            is_first_payment=bool(metadata.get("is_first_payment")),
            relationship=relationship,
        )

    _ensure_projection_baseline_grant(session, account_id=account_key, now=current_paid_at)
    previous = (
        session.query(EntitlementGrant.id)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.source == "provider_payment",
            EntitlementGrant.status.in_(["active", "recorded", "expired"]),
        )
        .with_for_update()
        .first()
    )
    is_first = previous is None
    starts_at, expires_at = _project_additive_days(
        session,
        account_id=account_key,
        days=max(1, int(duration_days)),
        now=current_paid_at,
    )
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_key,
        legacy_tg_id=int(legacy_tg_id) if legacy_tg_id is not None else None,
        idempotency_key=stable_key,
        source="provider_payment",
        status="active",
        grant_kind="paid_access",
        plan_code=str(plan_code or "paid")[:32],
        starts_at=starts_at,
        expires_at=expires_at,
        activated_at=current_paid_at,
        duration_days=max(1, int(duration_days)),
        provider=str(provider or "").strip().lower()[:32],
        external_order_id=str(order_id or "")[:160],
        created_at=current_paid_at,
        updated_at=current_paid_at,
    )
    _set_grant_metadata(
        grant,
        {
            "is_first_payment": is_first,
            "projection_already_applied": True,
            "provider_order_id": str(order_id),
        },
    )
    session.add(grant)
    session.flush()

    first, relationship = normalize_account_payment_history(
        session,
        account_id=account_key,
        now=current_paid_at,
    )
    is_first = first is not None and first.id == grant.id
    for user in _users_for_account(session, account_key):
        user.first_purchase_done = True
        user.sub_type = "PAID"
        user.current_plan_code = str(plan_code or "paid")[:32]
        user.is_active = True
    session.flush()
    return PaymentGrantResult(grant=grant, is_first_payment=is_first, relationship=relationship)


def grant_channel_bonus(
    session,
    *,
    account_id: str,
    legacy_tg_id: int | None,
    telegram_id: int,
    now: datetime | None = None,
) -> EntitlementGrant:
    current_now = (now or _utcnow()).replace(microsecond=0)
    account_key = str(account_id or "").strip()
    if not account_key or int(telegram_id or 0) <= 0:
        raise ValueError("account_id and telegram_id are required")
    existing = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_key,
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
        )
        .order_by(EntitlementGrant.created_at.asc())
        .with_for_update()
        .first()
    )
    if existing is not None:
        return existing

    _ensure_projection_baseline_grant(session, account_id=account_key, now=current_now)
    days = _available_prepayment_days(session, account_id=account_key, requested_days=CHANNEL_GRANT_DAYS)
    if days != CHANNEL_GRANT_DAYS:
        raise ValueError("pre_first_payment_premium_cap")
    starts_at, expires_at = _project_additive_days(
        session,
        account_id=account_key,
        days=days,
        now=current_now,
    )
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_key,
        legacy_tg_id=int(legacy_tg_id) if legacy_tg_id is not None else None,
        idempotency_key=f"channel-grant:v2:{account_key}",
        source="telegram_channel",
        status="active",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=starts_at,
        expires_at=expires_at,
        activated_at=current_now,
        duration_days=days,
        provider="telegram_membership",
        created_at=current_now,
        updated_at=current_now,
    )
    _set_grant_metadata(grant, {"telegram_id": int(telegram_id), "version": 2})
    session.add(grant)
    for user in _users_for_account(session, account_key):
        if str(user.sub_type or "").upper() != "PAID":
            user.sub_type = "BONUS"
            user.current_plan_code = "channel_bonus"
        user.channel_bonus_claimed_at = user.channel_bonus_claimed_at or current_now
        user.channel_bonus_active = True
        user.channel_bonus_expires_at = expires_at
        user.channel_bonus_revoked_at = None
    rebuild_account_entitlement_projection(session, account_id=account_key, now=current_now)
    session.flush()
    return grant


def _split_grandfathered_channel_from_legacy_snapshot(
    session,
    *,
    user: User,
    channel_grant: EntitlementGrant,
    now: datetime,
) -> None:
    component_expiry = channel_grant.expires_at
    component_start = channel_grant.starts_at
    if component_expiry is None or component_start is None:
        return
    snapshots = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(channel_grant.account_id),
            EntitlementGrant.source == "legacy_snapshot",
            EntitlementGrant.legacy_tg_id == int(user.tg_id),
        )
        .with_for_update()
        .all()
    )
    for snapshot in snapshots:
        metadata = _grant_metadata(snapshot)
        components = metadata.get("projection_components")
        if not isinstance(components, dict):
            components = {}
        component = components.get("telegram_channel_grandfathered")
        if not isinstance(component, dict):
            component = {
                "claimed_at": _safe_iso(user.channel_bonus_claimed_at),
                "expires_at": _safe_iso(user.channel_bonus_expires_at),
                "active": bool(user.channel_bonus_active),
                "revoked_at": _safe_iso(user.channel_bonus_revoked_at),
            }
        if str(component.get("expires_at") or "") != _safe_iso(component_expiry):
            continue
        if snapshot.expires_at == component_start:
            continue
        if snapshot.expires_at != component_expiry:
            continue
        component["aggregate_expires_at"] = _safe_iso(component_expiry)
        component["baseline_expires_at"] = _safe_iso(component_start)
        component["split_grant_id"] = str(channel_grant.id)
        component["split_at"] = _safe_iso(now)
        components["telegram_channel_grandfathered"] = component
        metadata["projection_components"] = components
        snapshot.expires_at = component_start
        snapshot.updated_at = now
        _set_grant_metadata(snapshot, metadata)
    session.flush()


def backfill_grandfathered_channel_grant(
    session,
    *,
    user: User,
    now: datetime | None = None,
) -> EntitlementGrant | None:
    account_id = str(user.account_id or "").strip()
    claimed_at = user.channel_bonus_claimed_at
    if not account_id or claimed_at is None:
        return None
    current_now = (now or _utcnow()).replace(microsecond=0)
    existing = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == account_id,
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
        )
        .order_by(EntitlementGrant.created_at.asc())
        .first()
    )
    if existing is not None:
        _split_grandfathered_channel_from_legacy_snapshot(
            session,
            user=user,
            channel_grant=existing,
            now=current_now,
        )
        return existing
    expires_at = user.channel_bonus_expires_at or user.expiry_at
    if expires_at is None:
        expires_at = claimed_at + timedelta(days=GRANDFATHERED_CHANNEL_GRANT_DAYS)
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_id,
        legacy_tg_id=int(user.tg_id),
        idempotency_key=f"channel-grant:v1-grandfathered:{account_id}",
        source="telegram_channel_grandfathered",
        status="active" if bool(user.channel_bonus_active) else "reversed",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=expires_at - timedelta(days=GRANDFATHERED_CHANNEL_GRANT_DAYS),
        expires_at=expires_at,
        activated_at=claimed_at,
        duration_days=GRANDFATHERED_CHANNEL_GRANT_DAYS,
        provider="legacy_channel_projection",
        reversed_at=user.channel_bonus_revoked_at,
        reversal_reason="legacy_channel_projection" if user.channel_bonus_revoked_at else None,
        created_at=claimed_at,
        updated_at=current_now,
    )
    _set_grant_metadata(grant, {"grandfathered": True, "projection_preserved": True})
    session.add(grant)
    session.flush()
    _split_grandfathered_channel_from_legacy_snapshot(
        session,
        user=user,
        channel_grant=grant,
        now=current_now,
    )
    return grant


def grant_referred_friend_bonus(
    session,
    *,
    account_id: str,
    evidence: ConnectionEvidence,
    now: datetime | None = None,
) -> EntitlementGrant:
    account_key = str(account_id or "").strip()
    if not account_key or str(evidence.account_id) != account_key or evidence.evidence_kind != TRIAL_EVIDENCE_KIND:
        raise ValueError("canonical server connection evidence is required")
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=f"referral-friend:v1:{account_key}").first()
    if existing is not None:
        return existing
    current_now = (now or evidence.observed_at or _utcnow()).replace(microsecond=0)
    _ensure_projection_baseline_grant(session, account_id=account_key, now=current_now)
    days = _available_prepayment_days(session, account_id=account_key, requested_days=FRIEND_GRANT_DAYS)
    if days != FRIEND_GRANT_DAYS:
        raise ValueError("pre_first_payment_premium_cap")
    starts_at, expires_at = _project_additive_days(session, account_id=account_key, days=days, now=current_now)
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_key,
        idempotency_key=f"referral-friend:v1:{account_key}",
        source="referral_friend",
        status="active",
        grant_kind="premium_bonus",
        plan_code="referral_friend",
        starts_at=starts_at,
        expires_at=expires_at,
        activated_at=evidence.observed_at,
        duration_days=days,
        activation_evidence_id=evidence.id,
        provider="internal_economy",
        created_at=current_now,
        updated_at=current_now,
    )
    session.add(grant)
    session.flush()
    rebuild_account_entitlement_projection(session, account_id=account_key, now=current_now)
    return grant


def begin_channel_loss_grace(session, *, account_id: str, now: datetime | None = None) -> datetime:
    current_now = (now or _utcnow()).replace(microsecond=0)
    grant = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
            EntitlementGrant.status.in_(["active", "grace"]),
            EntitlementGrant.reversed_at.is_(None),
        )
        .with_for_update()
        .first()
    )
    if grant is None:
        raise ValueError("active channel grant not found")
    metadata = _grant_metadata(grant)
    if grant.status != "grace":
        metadata["grace_started_at"] = current_now.isoformat()
        metadata["grace_until"] = (current_now + timedelta(hours=CHANNEL_GRACE_HOURS)).isoformat()
        grant.status = "grace"
        grant.updated_at = current_now
        _set_grant_metadata(grant, metadata)
    return datetime.fromisoformat(str(metadata["grace_started_at"]))


def cancel_channel_loss_grace(session, *, account_id: str, now: datetime | None = None) -> bool:
    grant = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == str(account_id),
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
            EntitlementGrant.status == "grace",
        )
        .with_for_update()
        .first()
    )
    if grant is None:
        return False
    metadata = _grant_metadata(grant)
    metadata.pop("grace_started_at", None)
    metadata.pop("grace_until", None)
    grant.status = "active"
    grant.updated_at = (now or _utcnow()).replace(microsecond=0)
    _set_grant_metadata(grant, metadata)
    return True


def reverse_due_channel_grants(session, *, now: datetime | None = None) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    rows = session.query(EntitlementGrant).filter(EntitlementGrant.status == "grace").with_for_update().all()
    reversed_count = 0
    waiting = 0
    for grant in rows:
        metadata = _grant_metadata(grant)
        grace_until_raw = str(metadata.get("grace_until") or "")
        if not grace_until_raw:
            waiting += 1
            continue
        grace_until = datetime.fromisoformat(grace_until_raw)
        if current_now < grace_until:
            waiting += 1
            continue
        remaining_to_interval_end = max(timedelta(0), (grant.expires_at or current_now) - current_now)
        unused = min(
            timedelta(days=max(0, int(grant.duration_days or 0))),
            remaining_to_interval_end,
        )
        for user in _users_for_account(session, str(grant.account_id)):
            user.channel_bonus_active = False
            user.channel_bonus_revoked_at = current_now
        grant.status = "reversed"
        grant.reversed_at = current_now
        grant.reversal_reason = "channel_membership_lost"
        grant.updated_at = current_now
        metadata["unused_seconds_reversed"] = int(unused.total_seconds())
        _set_grant_metadata(grant, metadata)
        rebuild_account_entitlement_projection(session, account_id=str(grant.account_id), now=current_now)
        reversed_count += 1
    session.flush()
    return {"reversed": reversed_count, "waiting": waiting}


def _record_referral_transition(
    session,
    *,
    relationship: ReferralRelationship,
    transition_key: str,
    transition_kind: str,
    status: str,
    occurred_at: datetime,
    metadata: dict[str, Any] | None = None,
) -> ReferralTransition:
    existing = session.query(ReferralTransition).filter_by(transition_key=str(transition_key)).first()
    if existing is not None:
        return existing
    row = ReferralTransition(
        id=str(uuid.uuid4()),
        relationship_id=str(relationship.id),
        referred_account_id=str(relationship.referred_account_id),
        referrer_account_id=str(relationship.referrer_account_id),
        transition_key=str(transition_key)[:160],
        transition_kind=str(transition_kind),
        status=str(status),
        occurred_at=occurred_at,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        created_at=occurred_at,
    )
    session.add(row)
    session.flush()
    return row


def create_referral_relationship(
    session,
    *,
    referred_account_id: str,
    referrer_account_id: str,
    source: str,
    now: datetime | None = None,
) -> ReferralRelationship:
    referred_id = str(referred_account_id or "").strip()
    referrer_id = str(referrer_account_id or "").strip()
    if not referred_id or not referrer_id:
        raise ValueError("referral accounts are required")
    if referred_id == referrer_id:
        raise ValueError("self_referral")
    if session.query(Account.id).filter(Account.id == referred_id).first() is None:
        raise ValueError("referred_account_not_found")
    if session.query(Account.id).filter(Account.id == referrer_id).first() is None:
        raise ValueError("referrer_account_not_found")

    existing = session.query(ReferralRelationship).filter_by(referred_account_id=referred_id).first()
    if existing is not None:
        if str(existing.referrer_account_id) != referrer_id:
            raise ValueError("referrer_already_set")
        return existing

    cursor = referrer_id
    visited: set[str] = set()
    while cursor and cursor not in visited:
        if cursor == referred_id:
            raise ValueError("referral_cycle")
        visited.add(cursor)
        parent = session.query(ReferralRelationship).filter_by(referred_account_id=cursor).first()
        cursor = str(parent.referrer_account_id) if parent is not None else ""

    current_now = (now or _utcnow()).replace(microsecond=0)
    relationship = ReferralRelationship(
        id=str(uuid.uuid4()),
        referred_account_id=referred_id,
        referrer_account_id=referrer_id,
        source=str(source or "unknown")[:32],
        status="linked",
        review_status="clear",
        created_at=current_now,
        updated_at=current_now,
    )
    session.add(relationship)
    session.flush()
    _record_referral_transition(
        session,
        relationship=relationship,
        transition_key=f"referral-linked:v1:{referred_id}",
        transition_kind="relationship_linked",
        status="linked",
        occurred_at=current_now,
        metadata={"source": relationship.source},
    )
    return relationship


def activate_referred_friend_reward(
    session,
    *,
    account_id: str,
    evidence: ConnectionEvidence | None,
    now: datetime | None = None,
) -> EntitlementGrant:
    account_key = str(account_id or "").strip()
    if evidence is None or str(evidence.account_id) != account_key:
        raise ValueError("connection_evidence is required")
    relationship = (
        session.query(ReferralRelationship)
        .filter_by(referred_account_id=account_key)
        .with_for_update()
        .one_or_none()
    )
    if relationship is None:
        raise ValueError("referral_relationship_not_found")
    if relationship.friend_grant_id:
        existing = session.query(EntitlementGrant).filter_by(id=str(relationship.friend_grant_id)).one_or_none()
        if existing is not None:
            return existing
    grant = grant_referred_friend_bonus(session, account_id=account_key, evidence=evidence, now=now)
    relationship.friend_evidence_id = str(evidence.id)
    relationship.friend_grant_id = str(grant.id)
    relationship.friend_granted_at = evidence.observed_at
    relationship.updated_at = (now or evidence.observed_at).replace(microsecond=0)
    _record_referral_transition(
        session,
        relationship=relationship,
        transition_key=f"referral-friend-released:v1:{account_key}",
        transition_kind="friend_reward_released",
        status="released",
        occurred_at=relationship.updated_at,
        metadata={"evidence_id": str(evidence.id), "grant_id": str(grant.id)},
    )
    session.flush()
    return grant


def _valid_first_payment_key(payment_key: str) -> bool:
    value = str(payment_key or "").strip().lower()
    return value.startswith(
        ("lavatop:", "freekassa:", "cardlink:", "pally:", "platima:", "stars:", "payment:")
    )


def queue_first_payment_referrer_reward(
    session,
    *,
    referred_account_id: str,
    payment_key: str,
    paid_at: datetime,
) -> ReferralRelationship:
    account_key = str(referred_account_id or "").strip()
    stable_payment_key = str(payment_key or "").strip()[:160]
    if not _valid_first_payment_key(stable_payment_key):
        raise ValueError("first_payment authority is required")
    relationship = (
        session.query(ReferralRelationship)
        .filter_by(referred_account_id=account_key)
        .with_for_update()
        .one_or_none()
    )
    if relationship is None:
        raise ValueError("referral_relationship_not_found")
    if relationship.first_payment_key:
        if str(relationship.first_payment_key) != stable_payment_key:
            raise ValueError("first_payment already recorded")
        return relationship
    canonical_paid_at = _naive_utc(paid_at)
    relationship.first_payment_key = stable_payment_key
    relationship.first_payment_at = canonical_paid_at
    relationship.hold_until = canonical_paid_at + timedelta(hours=REFERRER_HOLD_HOURS)
    relationship.status = "holding"
    relationship.updated_at = canonical_paid_at
    _record_referral_transition(
        session,
        relationship=relationship,
        transition_key=f"referral-first-payment:v1:{account_key}",
        transition_kind="first_payment_held",
        status="holding",
        occurred_at=canonical_paid_at,
        metadata={"payment_key": stable_payment_key, "hold_until": relationship.hold_until.isoformat()},
    )
    session.flush()
    return relationship


def migrate_pending_legacy_referral_queue(
    session,
    *,
    now: datetime | None = None,
    limit: int = 100,
) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    rows = (
        session.query(ReferralBonusQueue)
        .filter(
            ReferralBonusQueue.status == "pending",
            ReferralBonusQueue.ready_at <= current_now,
        )
        .order_by(ReferralBonusQueue.id.asc())
        .limit(max(1, min(int(limit), 1000)))
        .with_for_update()
        .all()
    )
    migrated = 0
    retryable = 0
    for row in rows:
        try:
            with session.begin_nested():
                referrer = session.query(User).filter_by(tg_id=int(row.referrer_tg_id)).one_or_none()
                referred = session.query(User).filter_by(tg_id=int(row.referred_tg_id)).one_or_none()
                if referrer is None or referred is None:
                    raise ValueError("legacy_referral_user_missing")

                from account_foundation_service import ensure_user_account_foundation

                ensure_user_account_foundation(session, referrer, now=current_now)
                ensure_user_account_foundation(session, referred, now=current_now)
                session.flush()
                referrer_account_id = _canonical_account_id(session, str(referrer.account_id or ""))
                referred_account_id = _canonical_account_id(session, str(referred.account_id or ""))
                if referrer_account_id == referred_account_id:
                    raise ValueError("legacy_referral_self_reference")

                existing = (
                    session.query(ReferralRelationship)
                    .filter_by(referred_account_id=referred_account_id)
                    .with_for_update()
                    .one_or_none()
                )
                if existing is not None and str(existing.referrer_account_id) != referrer_account_id:
                    raise ValueError("legacy_referral_referrer_conflict")
                relationship = existing or create_referral_relationship(
                    session,
                    referred_account_id=referred_account_id,
                    referrer_account_id=referrer_account_id,
                    source="legacy_referral_queue",
                    now=row.queued_at,
                )
                payment_key = (
                    "payment:legacy-referral:"
                    + hashlib.sha256(str(row.order_id).encode("utf-8")).hexdigest()
                )
                legacy_paid_at = row.queued_at
                if legacy_paid_at.tzinfo is not None:
                    legacy_paid_at = legacy_paid_at.astimezone(timezone.utc).replace(tzinfo=None)
                if not relationship.first_payment_key:
                    relationship = queue_first_payment_referrer_reward(
                        session,
                        referred_account_id=referred_account_id,
                        payment_key=payment_key,
                        paid_at=legacy_paid_at,
                    )
                    relationship.first_payment_at = legacy_paid_at
                    relationship.hold_until = legacy_paid_at + timedelta(hours=REFERRER_HOLD_HOURS)
                elif (
                    str(relationship.first_payment_key).startswith("payment:")
                    and relationship.first_payment_at is not None
                    and legacy_paid_at < relationship.first_payment_at
                ):
                    relationship.first_payment_key = payment_key
                    relationship.first_payment_at = legacy_paid_at
                    relationship.hold_until = legacy_paid_at + timedelta(hours=REFERRER_HOLD_HOURS)
                    if str(relationship.status or "").lower() in {"linked", "holding"}:
                        relationship.status = "holding"
                    relationship.updated_at = current_now
                migration_key = f"legacy-referral-queue-migrated:v1:{int(row.id)}"
                _record_referral_transition(
                    session,
                    relationship=relationship,
                    transition_key=migration_key,
                    transition_kind="legacy_queue_migrated",
                    status=str(relationship.status),
                    occurred_at=current_now,
                    metadata={
                        "legacy_queue_id": int(row.id),
                        "legacy_order_hash": hashlib.sha256(str(row.order_id).encode("utf-8")).hexdigest(),
                        "legacy_queued_at": row.queued_at.isoformat(),
                        "legacy_ready_at": row.ready_at.isoformat(),
                        "canonical_payment_key": str(relationship.first_payment_key or payment_key),
                    },
                )
                row_meta = {}
                try:
                    parsed_meta = json.loads(str(row.meta or "{}"))
                    if isinstance(parsed_meta, dict):
                        row_meta = parsed_meta
                except (TypeError, ValueError):
                    pass
                row_meta["account_migration"] = {
                    "relationship_id": str(relationship.id),
                    "referred_account_id": referred_account_id,
                    "referrer_account_id": referrer_account_id,
                    "migrated_at": _safe_iso(current_now),
                }
                row.meta = json.dumps(row_meta, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                row.status = "superseded_account"
                row.processed_at = current_now
                session.flush()
            migrated += 1
        except (TypeError, ValueError, IntegrityError) as exc:
            row_meta = {}
            try:
                parsed_meta = json.loads(str(row.meta or "{}"))
                if isinstance(parsed_meta, dict):
                    row_meta = parsed_meta
            except (TypeError, ValueError):
                pass
            retry_state = row_meta.get("account_migration_retry")
            if not isinstance(retry_state, dict):
                retry_state = {}
            try:
                previous_attempts = max(0, int(retry_state.get("attempts") or 0))
            except (TypeError, ValueError):
                previous_attempts = 0
            attempts = previous_attempts + 1
            retry_hours = min(24, 2 ** min(attempts - 1, 4))
            retry_state.update(
                {
                    "attempts": attempts,
                    "last_attempt_at": _safe_iso(current_now),
                    "next_attempt_at": _safe_iso(current_now + timedelta(hours=retry_hours)),
                    "reason": str(exc)[:80] if isinstance(exc, ValueError) else "legacy_referral_integrity_conflict",
                }
            )
            row_meta["account_migration_retry"] = retry_state
            row.meta = json.dumps(row_meta, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            row.ready_at = current_now + timedelta(hours=retry_hours)
            session.flush()
            retryable += 1
    return {"seen": len(rows), "migrated": migrated, "retryable": retryable}


def _grant_referrer_reward(
    session,
    *,
    relationship: ReferralRelationship,
    now: datetime,
) -> EntitlementGrant:
    key = f"referral-referrer:v1:{relationship.referred_account_id}"
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=key).first()
    if existing is not None:
        return existing
    _ensure_projection_baseline_grant(
        session,
        account_id=str(relationship.referrer_account_id),
        now=now,
    )
    starts_at, expires_at = _project_additive_days(
        session,
        account_id=str(relationship.referrer_account_id),
        days=REFERRER_GRANT_DAYS,
        now=now,
    )
    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=str(relationship.referrer_account_id),
        idempotency_key=key,
        source="referral_referrer",
        status="active",
        grant_kind="premium_bonus",
        plan_code="referral_referrer",
        starts_at=starts_at,
        expires_at=expires_at,
        activated_at=now,
        duration_days=REFERRER_GRANT_DAYS,
        provider="internal_economy",
        external_order_id=str(relationship.first_payment_key or ""),
        created_at=now,
        updated_at=now,
    )
    session.add(grant)
    session.flush()
    rebuild_account_entitlement_projection(
        session,
        account_id=str(relationship.referrer_account_id),
        now=now,
    )
    return grant


def release_due_referrer_rewards(session, *, now: datetime | None = None) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    rows = (
        session.query(ReferralRelationship)
        .filter(ReferralRelationship.status == "holding")
        .order_by(ReferralRelationship.created_at.asc())
        .with_for_update()
        .all()
    )
    released = 0
    waiting = 0
    rejected = 0
    for relationship in rows:
        review = str(relationship.review_status or "clear").lower()
        if review == "reject":
            relationship.status = "rejected"
            relationship.updated_at = current_now
            _record_referral_transition(
                session,
                relationship=relationship,
                transition_key=f"referral-referrer-rejected:v1:{relationship.referred_account_id}",
                transition_kind="referrer_reward_rejected",
                status="rejected",
                occurred_at=current_now,
            )
            rejected += 1
            continue
        if review == "wait" or relationship.hold_until is None or current_now < relationship.hold_until:
            waiting += 1
            continue
        grant = _grant_referrer_reward(session, relationship=relationship, now=current_now)
        relationship.referrer_grant_id = str(grant.id)
        relationship.referrer_granted_at = current_now
        relationship.status = "rewarded"
        relationship.updated_at = current_now
        _record_referral_transition(
            session,
            relationship=relationship,
            transition_key=f"referral-referrer-released:v1:{relationship.referred_account_id}",
            transition_kind="referrer_reward_released",
            status="released",
            occurred_at=current_now,
            metadata={"grant_id": str(grant.id)},
        )
        released += 1
    session.flush()
    return {"released": released, "waiting": waiting, "rejected": rejected}
