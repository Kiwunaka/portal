from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from models import (
    Account,
    AccountDevice,
    AccountIdentity,
    AccountMergeReview,
    AppSetting,
    AntiAbuseAction,
    AntiAbuseCase,
    AntiAbuseEvent,
    AuthSession,
    ConnectionEvidence,
    EntitlementGrant,
    ExternalOrder,
    PayAttempt,
    PaymentEntitlementClaim,
    ReferralRelationship,
    ReferralTransition,
    RecoveryCode,
    SupportAttachment,
    SupportTicket,
    User,
    WebEmailIdentity,
)


ACCOUNT_NAMESPACE = uuid.UUID("754cf326-fde1-4fd8-b77a-5524c9fc9f43")
DEVICE_NAMESPACE = uuid.UUID("0bf5675b-2c53-4056-a01a-53378ad08cf2")
GRANT_NAMESPACE = uuid.UUID("737979ec-a0a8-4d3a-b468-41723fa1bf21")
REVIEW_NAMESPACE = uuid.UUID("8c5c3d45-b3d7-474d-b540-f80505e78935")

SYNTHETIC_EMAIL_ACCOUNT_MIN = 8_000_000_000_000
ACCOUNT_FOUNDATION_BACKFILL_KEY = "migration.account_foundation.v1"
ACCOUNT_FOUNDATION_BACKFILL_LOCK = "pokrov_account_foundation_backfill"
ACCOUNT_FOUNDATION_STARTUP_LOCK = "pokrov_account_foundation_startup_v1"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class AccountBackfillReport:
    users_seen: int = 0
    accounts_created: int = 0
    accounts_merged: int = 0
    identities_created: int = 0
    devices_created: int = 0
    grants_created: int = 0
    reviews_created: int = 0


class _Counter:
    def __init__(self, *, users_seen: int) -> None:
        self.users_seen = users_seen
        self.accounts_created = 0
        self.accounts_merged = 0
        self.identities_created = 0
        self.devices_created = 0
        self.grants_created = 0
        self.reviews_created = 0

    def freeze(self) -> AccountBackfillReport:
        return AccountBackfillReport(
            users_seen=self.users_seen,
            accounts_created=self.accounts_created,
            accounts_merged=self.accounts_merged,
            identities_created=self.identities_created,
            devices_created=self.devices_created,
            grants_created=self.grants_created,
            reviews_created=self.reviews_created,
        )


class _DisjointSet:
    def __init__(self, values: Iterable[int]) -> None:
        self._parent = {int(value): int(value) for value in values}

    def find(self, value: int) -> int:
        parent = self._parent[value]
        if parent != value:
            self._parent[value] = self.find(parent)
        return self._parent[value]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        canonical_root = min(left_root, right_root)
        other_root = max(left_root, right_root)
        self._parent[other_root] = canonical_root


def _account_id_for_legacy_user(tg_id: int) -> str:
    return str(uuid.uuid5(ACCOUNT_NAMESPACE, f"legacy-user:{int(tg_id)}"))


def _device_id_for_install(install_id: str) -> str:
    return str(uuid.uuid5(DEVICE_NAMESPACE, f"install:{install_id.strip()}"))


def _grant_id_for_user(tg_id: int) -> str:
    return str(uuid.uuid5(GRANT_NAMESPACE, f"legacy-user:{int(tg_id)}:snapshot-v1"))


def _clean(value: object | None) -> str:
    return str(value or "").strip()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _create_review(
    session: Session,
    counter: _Counter,
    *,
    reason_code: str,
    subject_hint: str,
    account_id: str | None,
    conflicting_account_id: str | None,
    details: dict[str, object],
    now: datetime,
) -> AccountMergeReview:
    fingerprint_source = "|".join(
        [
            reason_code,
            subject_hint,
            account_id or "",
            conflicting_account_id or "",
        ]
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    existing = session.query(AccountMergeReview).filter_by(fingerprint=fingerprint).first()
    if existing is not None:
        existing.updated_at = now
        return existing
    review = AccountMergeReview(
        id=str(uuid.uuid5(REVIEW_NAMESPACE, fingerprint)),
        fingerprint=fingerprint,
        account_id=account_id,
        conflicting_account_id=conflicting_account_id,
        reason_code=reason_code,
        status="open",
        subject_hint=subject_hint[:255],
        details_json=_json(details),
        created_at=now,
        updated_at=now,
    )
    session.add(review)
    counter.reviews_created += 1
    return review


def _acquire_postgres_advisory_lock(
    session: Session,
    lock_key: str,
    *,
    shared: bool = False,
) -> None:
    dialect = str(session.get_bind().dialect.name or "")
    if dialect == "postgresql":
        function_name = "pg_advisory_xact_lock_shared" if shared else "pg_advisory_xact_lock"
        session.execute(
            text(f"SELECT {function_name}(hashtext(:lock_key))"),
            {"lock_key": str(lock_key)},
        )


def _acquire_account_foundation_projection_locks(
    session: Session,
    users: Iterable[User],
    *,
    shared_global: bool,
) -> None:
    for tg_id in sorted({int(user.tg_id) for user in users}):
        _acquire_postgres_advisory_lock(
            session,
            f"pokrov_account_foundation_user:{tg_id}",
        )
    _acquire_postgres_advisory_lock(
        session,
        ACCOUNT_FOUNDATION_BACKFILL_LOCK,
        shared=shared_global,
    )


def _merge_duplicate_identity_state(
    target: AccountIdentity,
    source: AccountIdentity,
    *,
    now: datetime,
) -> None:
    verified_values = [value for value in (target.verified_at, source.verified_at) if value is not None]
    disabled_values = [value for value in (target.disabled_at, source.disabled_at) if value is not None]
    target.verified_at = min(verified_values) if verified_values else None
    target.disabled_at = min(disabled_values) if disabled_values else None
    target.updated_at = now


def _trial_merge_rank(grant: EntitlementGrant) -> tuple[int, datetime, str]:
    status = str(grant.status or "").strip().lower()
    priority = {
        "active": 0,
        "reserved": 1,
        "expired": 2,
        "reversed": 3,
        "superseded": 4,
    }.get(status, 5)
    effective_at = {
        "active": grant.activated_at or grant.starts_at,
        "reserved": grant.reserved_at,
        "expired": grant.activated_at or grant.starts_at or grant.expires_at,
        "reversed": grant.reversed_at or grant.activated_at or grant.starts_at,
        "superseded": grant.reversed_at or grant.activated_at or grant.starts_at,
    }.get(status) or grant.created_at or datetime.max
    return priority, effective_at, str(grant.id)


def _reconcile_account_trial_grants(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    trials = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id.in_([source_account_id, target_account_id]),
            EntitlementGrant.source == "premium_trial",
        )
        .order_by(EntitlementGrant.id.asc())
        .with_for_update()
        .all()
    )
    if len(trials) <= 1:
        return
    winner = min(trials, key=_trial_merge_rank)
    for duplicate in trials:
        if duplicate.id == winner.id:
            continue
        try:
            metadata = json.loads(str(duplicate.metadata_json or "{}"))
            if not isinstance(metadata, dict):
                metadata = {}
        except Exception:
            metadata = {}
        metadata["account_merge"] = {
            "superseded_by_grant_id": str(winner.id),
            "source_account_id": str(source_account_id),
            "target_account_id": str(target_account_id),
            "previous_status": str(duplicate.status or ""),
            "previous_reversal_reason": str(duplicate.reversal_reason or "") or None,
            "previous_reversed_at": duplicate.reversed_at.isoformat() if duplicate.reversed_at else None,
        }
        duplicate.source = "premium_trial_superseded"
        duplicate.status = "superseded"
        duplicate.reversed_at = duplicate.reversed_at or now
        duplicate.reversal_reason = "account_merge_duplicate"
        duplicate.metadata_json = _json(metadata)
        duplicate.updated_at = now
    session.flush()


def _grant_is_effective(grant: EntitlementGrant) -> bool:
    return str(grant.status or "").lower() in {"active", "grace"} and grant.reversed_at is None


def _channel_merge_rank(grant: EntitlementGrant) -> tuple[int, int, int, datetime, str]:
    return (
        1 if _grant_is_effective(grant) else 0,
        1 if str(grant.source) == "telegram_channel_grandfathered" else 0,
        int(grant.duration_days or 0),
        grant.expires_at or datetime.min,
        str(grant.id),
    )


def _reconcile_account_channel_grants(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    authority_sources = ("telegram_channel", "telegram_channel_grandfathered")
    rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id.in_([source_account_id, target_account_id]),
            EntitlementGrant.source.in_(authority_sources),
        )
        .order_by(EntitlementGrant.created_at.asc(), EntitlementGrant.id.asc())
        .with_for_update()
        .all()
    )
    if not rows:
        return
    winner = max(rows, key=_channel_merge_rank)
    winner.account_id = target_account_id
    for duplicate in rows:
        if duplicate.id == winner.id:
            continue
        metadata = {}
        try:
            parsed = json.loads(duplicate.metadata_json or "{}")
            if isinstance(parsed, dict):
                metadata = parsed
        except Exception:
            metadata = {}
        metadata["account_merge"] = {
            "previous_source": str(duplicate.source),
            "winner_grant_id": str(winner.id),
        }
        duplicate.source = "telegram_channel_superseded"
        duplicate.status = "superseded"
        duplicate.reversed_at = duplicate.reversed_at or now
        duplicate.reversal_reason = "account_merge_duplicate"
        duplicate.metadata_json = _json(metadata)
        duplicate.updated_at = now
    session.flush()


def _reward_merge_rank(grant: EntitlementGrant) -> tuple[int, datetime, int, datetime, str]:
    return (
        1 if _grant_is_effective(grant) else 0,
        grant.expires_at or datetime.min,
        int(grant.duration_days or 0),
        grant.updated_at or grant.created_at or datetime.min,
        str(grant.id),
    )


def _supersede_referral_grant(
    grant: EntitlementGrant,
    *,
    winner: EntitlementGrant,
    superseded_source: str,
    now: datetime,
) -> None:
    try:
        metadata = json.loads(str(grant.metadata_json or "{}"))
        if not isinstance(metadata, dict):
            metadata = {}
    except (TypeError, ValueError):
        metadata = {}
    metadata["account_merge"] = {
        "winner_grant_id": str(winner.id),
        "previous_idempotency_key": str(grant.idempotency_key),
        "previous_source": str(grant.source),
        "previous_status": str(grant.status),
    }
    grant.idempotency_key = f"referral-merge-superseded:v1:{grant.id}"[:160]
    grant.source = superseded_source
    grant.status = "superseded"
    grant.reversed_at = grant.reversed_at or now
    grant.reversal_reason = "account_merge_duplicate"
    grant.metadata_json = _json(metadata)
    grant.updated_at = now


def _dedupe_referral_grant_candidates(
    session: Session,
    *,
    candidates: list[EntitlementGrant],
    canonical_key: str,
    canonical_account_id: str | None,
    superseded_source: str,
    now: datetime,
) -> EntitlementGrant | None:
    unique = {str(row.id): row for row in candidates}
    if not unique:
        return None
    winner = max(unique.values(), key=_reward_merge_rank)
    for row in unique.values():
        if row.id != winner.id:
            _supersede_referral_grant(
                row,
                winner=winner,
                superseded_source=superseded_source,
                now=now,
            )
    session.flush()
    winner.idempotency_key = canonical_key[:160]
    if canonical_account_id is not None:
        winner.account_id = canonical_account_id
    winner.updated_at = now
    session.flush()
    return winner


def _reconcile_semantic_referral_grants(
    session: Session,
    *,
    canonical: ReferralRelationship,
    duplicate: ReferralRelationship,
    source_account_id: str,
    target_account_id: str,
    same_referrer: bool,
    now: datetime,
) -> None:
    friend_pointer_ids = {
        str(value)
        for value in (canonical.friend_grant_id, duplicate.friend_grant_id)
        if value
    }
    friend_rows = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id.in_([source_account_id, target_account_id]),
            EntitlementGrant.source == "referral_friend",
        )
        .with_for_update()
        .all()
    )
    if friend_pointer_ids:
        friend_rows.extend(
            session.query(EntitlementGrant)
            .filter(
                EntitlementGrant.id.in_(sorted(friend_pointer_ids)),
                EntitlementGrant.source == "referral_friend",
            )
            .with_for_update()
            .all()
        )
    friend_winner = _dedupe_referral_grant_candidates(
        session,
        candidates=friend_rows,
        canonical_key=f"referral-friend:v1:{target_account_id}",
        canonical_account_id=target_account_id,
        superseded_source="referral_friend_superseded",
        now=now,
    )
    if friend_winner is not None:
        canonical.friend_grant_id = str(friend_winner.id)
        duplicate.friend_grant_id = str(friend_winner.id)

    if not same_referrer:
        session.flush()
        return
    referrer_pointer_ids = {
        str(value)
        for value in (canonical.referrer_grant_id, duplicate.referrer_grant_id)
        if value
    }
    referrer_rows: list[EntitlementGrant] = []
    if referrer_pointer_ids:
        referrer_rows.extend(
            session.query(EntitlementGrant)
            .filter(
                EntitlementGrant.id.in_(sorted(referrer_pointer_ids)),
                EntitlementGrant.source == "referral_referrer",
            )
            .with_for_update()
            .all()
        )
    referrer_rows.extend(
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.source == "referral_referrer",
            EntitlementGrant.idempotency_key.in_(
                [
                    f"referral-referrer:v1:{source_account_id}",
                    f"referral-referrer:v1:{target_account_id}",
                ]
            ),
        )
        .with_for_update()
        .all()
    )
    referrer_winner = _dedupe_referral_grant_candidates(
        session,
        candidates=referrer_rows,
        canonical_key=f"referral-referrer:v1:{target_account_id}",
        canonical_account_id=str(canonical.referrer_account_id),
        superseded_source="referral_referrer_superseded",
        now=now,
    )
    if referrer_winner is not None:
        canonical.referrer_grant_id = str(referrer_winner.id)
        duplicate.referrer_grant_id = str(referrer_winner.id)
        from economy_service import rebuild_account_entitlement_projection

        rebuild_account_entitlement_projection(
            session,
            account_id=str(canonical.referrer_account_id),
            now=now,
        )
    session.flush()


_REFERRAL_STATUS_RANK = {"rejected": 0, "linked": 1, "holding": 2, "rewarded": 3}
_REFERRAL_REVIEW_RANK = {"clear": 0, "wait": 1, "reject": 2}
_TRANSITION_STATUS_RANK = {"superseded": 0, "linked": 1, "holding": 2, "released": 3, "rejected": 3}


def _relationship_rank(row: ReferralRelationship) -> tuple[int, int, datetime, str]:
    return (
        _REFERRAL_STATUS_RANK.get(str(row.status or "").lower(), -1),
        sum(
            value is not None
            for value in (
                row.friend_evidence_id,
                row.friend_grant_id,
                row.first_payment_key,
                row.referrer_grant_id,
            )
        ),
        row.updated_at or row.created_at or datetime.min,
        str(row.id),
    )


def _transition_metadata(row: ReferralTransition) -> dict[str, object]:
    try:
        value = json.loads(str(row.metadata_json or "{}"))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _supersede_transition(
    row: ReferralTransition,
    *,
    target_account_id: str,
    winner_id: str | None,
    now: datetime,
) -> None:
    metadata = _transition_metadata(row)
    metadata["account_merge"] = {
        "previous_key": str(row.transition_key),
        "previous_status": str(row.status),
        "superseded_by_transition_id": winner_id,
    }
    row.transition_key = f"referral-merge-superseded:v1:{target_account_id}:{row.id}"[:160]
    row.status = "superseded"
    row.metadata_json = _json(metadata)


def _reconcile_transition_keys(
    session: Session,
    *,
    relationship: ReferralRelationship,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    rows = (
        session.query(ReferralTransition)
        .filter_by(relationship_id=str(relationship.id))
        .order_by(ReferralTransition.occurred_at.asc(), ReferralTransition.id.asc())
        .with_for_update()
        .all()
    )
    groups: dict[str, list[ReferralTransition]] = {}
    for row in rows:
        row.referred_account_id = target_account_id
        row.referrer_account_id = str(relationship.referrer_account_id)
        desired = str(row.transition_key).replace(source_account_id, target_account_id)
        groups.setdefault(desired, []).append(row)
    for desired, candidates in groups.items():
        winner = max(
            candidates,
            key=lambda row: (
                _TRANSITION_STATUS_RANK.get(str(row.status or "").lower(), -1),
                row.occurred_at or datetime.min,
                str(row.id),
            ),
        )
        for row in candidates:
            if row.id != winner.id:
                _supersede_transition(
                    row,
                    target_account_id=target_account_id,
                    winner_id=str(winner.id),
                    now=now,
                )
        session.flush()
        winner.transition_key = desired[:160]
    session.flush()


def _merge_same_referrer_fields(target: ReferralRelationship, source: ReferralRelationship, *, now: datetime) -> None:
    for field in ("friend_evidence_id", "friend_grant_id", "referrer_grant_id"):
        if getattr(target, field) is None and getattr(source, field) is not None:
            setattr(target, field, getattr(source, field))
    for field in ("friend_granted_at", "referrer_granted_at"):
        values = [value for value in (getattr(target, field), getattr(source, field)) if value is not None]
        setattr(target, field, max(values) if values else None)
    payment_rows = [row for row in (target, source) if row.first_payment_key and row.first_payment_at]
    if payment_rows:
        first = min(payment_rows, key=lambda row: (row.first_payment_at, str(row.first_payment_key)))
        target.first_payment_key = first.first_payment_key
        target.first_payment_at = first.first_payment_at
        holds = [row.hold_until for row in payment_rows if row.hold_until is not None]
        target.hold_until = max(holds) if holds else None
    target.status = max((target, source), key=_relationship_rank).status
    target.review_status = max(
        (str(target.review_status or "clear"), str(source.review_status or "clear")),
        key=lambda value: _REFERRAL_REVIEW_RANK.get(value.lower(), -1),
    )
    target.updated_at = max(value for value in (target.updated_at, source.updated_at, now) if value is not None)


def _relationship_snapshot(row: ReferralRelationship, *, payment: tuple[object, object, object] | None = None) -> dict[str, object]:
    payment_key, payment_at, hold_until = payment or (
        row.first_payment_key,
        row.first_payment_at,
        row.hold_until,
    )
    return {
        "relationship_id": str(row.id),
        "referred_account_id": str(row.referred_account_id),
        "referrer_account_id": str(row.referrer_account_id),
        "source": str(row.source),
        "status": str(row.status),
        "review_status": str(row.review_status),
        "friend_evidence_id": row.friend_evidence_id,
        "friend_grant_id": row.friend_grant_id,
        "friend_granted_at": friend_at.isoformat() if (friend_at := row.friend_granted_at) else None,
        "first_payment_key": payment_key,
        "first_payment_at": payment_at.isoformat() if isinstance(payment_at, datetime) else None,
        "hold_until": hold_until.isoformat() if isinstance(hold_until, datetime) else None,
        "referrer_grant_id": row.referrer_grant_id,
        "referrer_granted_at": reward_at.isoformat() if (reward_at := row.referrer_granted_at) else None,
    }


def _record_relationship_merge_snapshot(
    session: Session,
    *,
    canonical: ReferralRelationship,
    superseded: ReferralRelationship,
    superseded_payment: tuple[object, object, object],
    target_before: dict[str, object],
    source_before: dict[str, object],
    target_account_id: str,
    now: datetime,
) -> None:
    key = f"referral-merge-snapshot:v1:{target_account_id}:{superseded.id}"[:160]
    if session.query(ReferralTransition.id).filter_by(transition_key=key).first():
        return
    session.add(
        ReferralTransition(
            id=str(uuid.uuid4()),
            relationship_id=str(superseded.id),
            referred_account_id=str(superseded.referred_account_id),
            referrer_account_id=str(superseded.referrer_account_id),
            transition_key=key,
            transition_kind="relationship_merge_superseded",
            status="superseded",
            occurred_at=now,
            metadata_json=_json(
                {
                    "canonical": _relationship_snapshot(canonical),
                    "superseded": _relationship_snapshot(superseded, payment=superseded_payment),
                    "target_before": target_before,
                    "source_before": source_before,
                }
            ),
            created_at=now,
        )
    )


def _reconcile_referral_relationships(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    source = (
        session.query(ReferralRelationship)
        .filter_by(referred_account_id=source_account_id)
        .with_for_update()
        .first()
    )
    target = (
        session.query(ReferralRelationship)
        .filter_by(referred_account_id=target_account_id)
        .with_for_update()
        .first()
    )
    if source is None:
        return
    if str(source.status or "").lower() in {"superseded", "rejected"}:
        return
    if target is None:
        source.referred_account_id = target_account_id
        source.updated_at = now
        _reconcile_transition_keys(
            session,
            relationship=source,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            now=now,
        )
        return

    source_payment = (source.first_payment_key, source.first_payment_at, source.hold_until)
    target_before = _relationship_snapshot(target)
    source_before = _relationship_snapshot(source, payment=source_payment)
    if source.first_payment_key:
        source.first_payment_key = None
        source.first_payment_at = None
        source.hold_until = None
        session.flush()
    if str(source.referrer_account_id) == str(target.referrer_account_id):
        _merge_same_referrer_fields(target, source, now=now)
        payment_rows = [
            value
            for value in (
                (target.first_payment_key, target.first_payment_at, target.hold_until),
                source_payment,
            )
            if value[0] and value[1]
        ]
        if payment_rows:
            payment_key, payment_at, _hold = min(payment_rows, key=lambda value: (value[1], str(value[0])))
            target.first_payment_key = payment_key
            target.first_payment_at = payment_at
            holds = [value[2] for value in payment_rows if value[2] is not None]
            target.hold_until = max(holds) if holds else None
        _reconcile_semantic_referral_grants(
            session,
            canonical=target,
            duplicate=source,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            same_referrer=True,
            now=now,
        )
        _record_relationship_merge_snapshot(
            session,
            canonical=target,
            superseded=source,
            superseded_payment=source_payment,
            target_before=target_before,
            source_before=source_before,
            target_account_id=target_account_id,
            now=now,
        )
    else:
        winner = max((target, source), key=_relationship_rank)
        if winner.id == source.id:
            for field in (
                "referrer_account_id",
                "source",
                "status",
                "review_status",
                "friend_evidence_id",
                "friend_grant_id",
                "friend_granted_at",
                "first_payment_key",
                "first_payment_at",
                "hold_until",
                "referrer_grant_id",
                "referrer_granted_at",
            ):
                setattr(target, field, getattr(source, field))
            target.first_payment_key = source_payment[0]
            target.first_payment_at = source_payment[1]
            target.hold_until = source_payment[2]
        target.review_status = max(
            (str(target.review_status or "clear"), str(source.review_status or "clear"), "wait"),
            key=lambda value: _REFERRAL_REVIEW_RANK.get(value.lower(), -1),
        )
        _reconcile_semantic_referral_grants(
            session,
            canonical=target,
            duplicate=source,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            same_referrer=False,
            now=now,
        )
        _record_relationship_merge_snapshot(
            session,
            canonical=target,
            superseded=source,
            superseded_payment=source_payment,
            target_before=target_before,
            source_before=source_before,
            target_account_id=target_account_id,
            now=now,
        )
        _create_review(
            session,
            _Counter(users_seen=0),
            reason_code="referral_merge_conflict",
            subject_hint=f"referral:{source_account_id}",
            account_id=target_account_id,
            conflicting_account_id=source_account_id,
            details={
                "target_referrer_account_id": str(target.referrer_account_id),
                "source_referrer_account_id": str(source.referrer_account_id),
                "winner_relationship_id": str(winner.id),
            },
            now=now,
        )
    _supersede_relationship(session, source, reason="account_merge_duplicate", now=now)
    session.flush()


def _supersede_relationship(session: Session, row: ReferralRelationship, *, reason: str, now: datetime) -> None:
    row.status = "superseded"
    row.review_status = "review"
    row.updated_at = now
    key = f"referral-relationship-superseded:v1:{row.id}:{reason}"[:160]
    if session.query(ReferralTransition.id).filter_by(transition_key=key).first() is None:
        session.add(
            ReferralTransition(
                id=str(uuid.uuid4()),
                relationship_id=str(row.id),
                referred_account_id=str(row.referred_account_id),
                referrer_account_id=str(row.referrer_account_id),
                transition_key=key,
                transition_kind="relationship_superseded",
                status="superseded",
                occurred_at=now,
                metadata_json=_json({"reason": reason}),
                created_at=now,
            )
        )
    session.flush()


def _sanitize_referral_graph(session: Session, *, now: datetime) -> None:
    while True:
        rows = (
            session.query(ReferralRelationship)
            .filter(~ReferralRelationship.status.in_(["superseded", "rejected"]))
            .order_by(ReferralRelationship.id.asc())
            .with_for_update()
            .all()
        )
        self_rows = [row for row in rows if str(row.referred_account_id) == str(row.referrer_account_id)]
        if self_rows:
            for row in self_rows:
                _supersede_relationship(session, row, reason="account_merge_self_referral", now=now)
            continue
        by_referred = {str(row.referred_account_id): row for row in rows}
        cycle: list[ReferralRelationship] | None = None
        for start in sorted(by_referred):
            path: list[str] = []
            positions: dict[str, int] = {}
            cursor = start
            while cursor in by_referred:
                if cursor in positions:
                    cycle = [by_referred[key] for key in path[positions[cursor] :]]
                    break
                positions[cursor] = len(path)
                path.append(cursor)
                cursor = str(by_referred[cursor].referrer_account_id)
            if cycle:
                break
        if not cycle:
            return
        loser = min(cycle, key=_relationship_rank)
        _supersede_relationship(session, loser, reason="account_merge_cycle", now=now)


def _rewrite_referrer_edges_for_merge(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    rows = (
        session.query(ReferralRelationship)
        .filter(
            ReferralRelationship.referrer_account_id == source_account_id,
            ~ReferralRelationship.status.in_(["superseded", "rejected"]),
        )
        .order_by(ReferralRelationship.id.asc())
        .with_for_update()
        .all()
    )
    for row in rows:
        referred_id = str(row.referred_account_id)
        if referred_id == target_account_id:
            _supersede_relationship(session, row, reason="account_merge_self_referral", now=now)
            continue
        cursor = target_account_id
        visited: set[str] = set()
        creates_cycle = False
        while cursor and cursor not in visited:
            if cursor == referred_id:
                creates_cycle = True
                break
            visited.add(cursor)
            parent = (
                session.query(ReferralRelationship)
                .filter(
                    ReferralRelationship.referred_account_id == cursor,
                    ReferralRelationship.id != row.id,
                    ~ReferralRelationship.status.in_(["superseded", "rejected"]),
                )
                .first()
            )
            cursor = str(parent.referrer_account_id) if parent is not None else ""
        if creates_cycle:
            _supersede_relationship(session, row, reason="account_merge_cycle", now=now)
            continue
        old_referrer = str(row.referrer_account_id)
        row.referrer_account_id = target_account_id
        row.updated_at = now
        session.query(ReferralTransition).filter_by(relationship_id=str(row.id)).update(
            {ReferralTransition.referrer_account_id: target_account_id},
            synchronize_session=False,
        )
        key = f"referral-referrer-merged:v1:{row.id}:{source_account_id}:{target_account_id}"[:160]
        if session.query(ReferralTransition.id).filter_by(transition_key=key).first() is None:
            session.add(
                ReferralTransition(
                    id=str(uuid.uuid4()),
                    relationship_id=str(row.id),
                    referred_account_id=referred_id,
                    referrer_account_id=target_account_id,
                    transition_key=key,
                    transition_kind="referrer_account_merged",
                    status=str(row.status),
                    occurred_at=now,
                    metadata_json=_json({"previous_referrer_account_id": old_referrer}),
                    created_at=now,
                )
            )
        session.flush()


def _move_account_owned_rows(
    session: Session,
    *,
    source_account_id: str,
    target_account_id: str,
    now: datetime,
) -> None:
    _reconcile_account_trial_grants(
        session,
        source_account_id=source_account_id,
        target_account_id=target_account_id,
        now=now,
    )
    _reconcile_account_channel_grants(
        session,
        source_account_id=source_account_id,
        target_account_id=target_account_id,
        now=now,
    )
    _reconcile_referral_relationships(
        session,
        source_account_id=source_account_id,
        target_account_id=target_account_id,
        now=now,
    )
    identities = session.query(AccountIdentity).filter_by(account_id=source_account_id).all()
    for identity in identities:
        duplicate = (
            session.query(AccountIdentity)
            .filter(
                AccountIdentity.account_id == target_account_id,
                AccountIdentity.kind == identity.kind,
                AccountIdentity.provider == identity.provider,
                AccountIdentity.subject_norm == identity.subject_norm,
            )
            .first()
        )
        if duplicate is not None:
            _merge_duplicate_identity_state(duplicate, identity, now=now)
            session.delete(identity)
        else:
            identity.account_id = target_account_id

    for model in (
        AccountDevice,
        AuthSession,
        RecoveryCode,
        ConnectionEvidence,
        EntitlementGrant,
        AntiAbuseEvent,
        AntiAbuseCase,
        AntiAbuseAction,
        PaymentEntitlementClaim,
    ):
        session.query(model).filter(model.account_id == source_account_id).update(
            {model.account_id: target_account_id},
            synchronize_session=False,
        )

    session.query(SupportTicket).filter(SupportTicket.account_id == source_account_id).update(
        {SupportTicket.account_id: target_account_id},
        synchronize_session="fetch",
    )
    session.query(SupportAttachment).filter(
        SupportAttachment.owner_account_id == source_account_id
    ).update(
        {SupportAttachment.owner_account_id: target_account_id},
        synchronize_session="fetch",
    )

    _rewrite_referrer_edges_for_merge(
        session,
        source_account_id=source_account_id,
        target_account_id=target_account_id,
        now=now,
    )
    session.flush()
    _sanitize_referral_graph(session, now=now)
    from economy_service import normalize_account_payment_history

    normalize_account_payment_history(session, account_id=target_account_id, now=now)


def _ensure_identity(
    session: Session,
    counter: _Counter,
    *,
    account_id: str,
    kind: str,
    provider: str,
    subject_norm: str,
    verified_at: datetime | None,
    metadata: dict[str, object],
    now: datetime,
) -> None:
    subject = subject_norm.strip().lower() if kind == "email" else subject_norm.strip()
    if not subject:
        return
    existing = (
        session.query(AccountIdentity)
        .filter_by(kind=kind, provider=provider, subject_norm=subject)
        .first()
    )
    if existing is not None:
        if existing.account_id != account_id:
            _create_review(
                session,
                counter,
                reason_code="identity_account_conflict",
                subject_hint=f"{kind}:{provider}:{subject}",
                account_id=account_id,
                conflicting_account_id=str(existing.account_id),
                details={"kind": kind, "provider": provider},
                now=now,
            )
        elif verified_at is not None and existing.verified_at is None:
            existing.verified_at = verified_at
            existing.updated_at = now
        return
    session.add(
        AccountIdentity(
            account_id=account_id,
            kind=kind,
            provider=provider,
            subject_norm=subject,
            verified_at=verified_at,
            metadata_json=_json(metadata),
            created_at=now,
            updated_at=now,
        )
    )
    counter.identities_created += 1


def _ensure_device(
    session: Session,
    counter: _Counter,
    *,
    user: User,
    account_id: str,
    now: datetime,
) -> None:
    install_id = _clean(user.app_install_id)
    if not install_id:
        return
    existing = session.query(AccountDevice).filter_by(install_id=install_id).first()
    if existing is not None and existing.account_id != account_id:
        _create_review(
            session,
            counter,
            reason_code="install_account_conflict",
            subject_hint=f"install:{install_id}",
            account_id=account_id,
            conflicting_account_id=str(existing.account_id),
            details={"legacy_tg_id": int(user.tg_id)},
            now=now,
        )
        return
    first_seen_at = user.created_at or user.app_last_seen_at or now
    last_seen_at = user.app_last_seen_at or user.created_at or now
    if existing is None:
        existing = AccountDevice(
            id=_device_id_for_install(install_id),
            account_id=account_id,
            install_id=install_id,
            first_seen_at=first_seen_at,
            created_at=now,
        )
        session.add(existing)
        counter.devices_created += 1
    existing.label = _clean(user.app_device_name) or None
    existing.platform = _clean(user.app_platform) or None
    existing.os_version = _clean(user.app_os_version) or None
    existing.app_version = _clean(user.app_version) or None
    existing.locale = _clean(user.app_locale) or None
    existing.time_zone = _clean(user.app_timezone) or None
    existing.route_mode = _clean(user.route_mode) or None
    existing.selected_apps_json = user.route_selected_apps_json
    existing.requires_elevated_privileges = user.route_requires_elevated_privileges
    existing.last_seen_at = last_seen_at
    existing.updated_at = now


def _ensure_legacy_grant(
    session: Session,
    counter: _Counter,
    *,
    user: User,
    account_id: str,
    now: datetime,
    include_legacy_payment_authority: bool = True,
) -> None:
    idempotency_key = f"legacy-user:{int(user.tg_id)}:snapshot-v1"
    snapshot_metadata: dict[str, object] = {
        "first_purchase_done": bool(user.first_purchase_done),
        "sub_type": _clean(user.sub_type),
        "trial_used": bool(user.trial_used),
    }
    if user.channel_bonus_claimed_at is not None:
        snapshot_metadata["projection_components"] = {
            "telegram_channel_grandfathered": {
                "claimed_at": user.channel_bonus_claimed_at.isoformat(),
                "expires_at": user.channel_bonus_expires_at.isoformat() if user.channel_bonus_expires_at else None,
                "active": bool(user.channel_bonus_active),
                "revoked_at": user.channel_bonus_revoked_at.isoformat() if user.channel_bonus_revoked_at else None,
            }
        }
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=idempotency_key).first()
    if existing is not None:
        existing.account_id = account_id
        try:
            existing_metadata = json.loads(str(existing.metadata_json or "{}"))
            if not isinstance(existing_metadata, dict):
                existing_metadata = {}
        except (TypeError, ValueError):
            existing_metadata = {}
        for key, value in snapshot_metadata.items():
            if key != "projection_components":
                existing_metadata[key] = value
        incoming_components = snapshot_metadata.get("projection_components")
        if isinstance(incoming_components, dict):
            stored_components = existing_metadata.get("projection_components")
            if not isinstance(stored_components, dict):
                stored_components = {}
            for component_key, component_value in incoming_components.items():
                stored_component = stored_components.get(component_key)
                if isinstance(stored_component, dict) and isinstance(component_value, dict):
                    stored_component.update(component_value)
                    stored_components[component_key] = stored_component
                else:
                    stored_components[component_key] = component_value
            existing_metadata["projection_components"] = stored_components
        existing.metadata_json = _json(existing_metadata)
        existing.updated_at = now
    else:
        plan_code = _clean(user.current_plan_code) or _clean(user.sub_type).lower() or "legacy"
        session.add(
            EntitlementGrant(
                id=_grant_id_for_user(int(user.tg_id)),
                account_id=account_id,
                legacy_tg_id=int(user.tg_id),
                idempotency_key=idempotency_key,
                source="legacy_snapshot",
                status="active" if bool(user.is_active) else "inactive",
                grant_kind="access_snapshot",
                plan_code=plan_code,
                starts_at=user.created_at,
                expires_at=user.expiry_at,
                provider="legacy_user",
                metadata_json=_json(snapshot_metadata),
                created_at=now,
                updated_at=now,
            )
        )
        counter.grants_created += 1
    if include_legacy_payment_authority:
        _ensure_legacy_payment_authority(session, counter, user=user, account_id=account_id, now=now)


def _historical_payment_key(provider: str, order_id: str) -> str:
    digest = hashlib.sha256(str(order_id).encode("utf-8")).hexdigest()
    return f"provider-payment:v1:{str(provider).strip().lower()}:{digest}"


def _corroborated_account_payments(
    session: Session,
    *,
    account_id: str,
    now: datetime,
) -> list[dict[str, object]]:
    tg_ids = [int(row[0]) for row in session.query(User.tg_id).filter(User.account_id == account_id).all()]
    if not tg_ids:
        return []
    legacy_paid_projection = bool(
        session.query(User.tg_id)
        .filter(User.account_id == account_id, User.sub_type == "PAID")
        .first()
    )
    payments: list[dict[str, object]] = []
    external_rows = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.tg_id.in_(tg_ids),
            ExternalOrder.status == "paid",
            ExternalOrder.order_id.isnot(None),
            ExternalOrder.provider.isnot(None),
        )
        .all()
    )
    for row in external_rows:
        provider = _clean(row.provider).lower()
        order_id = _clean(row.order_id)
        if provider and order_id:
            fulfilled_status = ""
            try:
                metadata = json.loads(str(row.meta_json or "{}"))
                fulfillment = metadata.get("fulfillment", {}) if isinstance(metadata, dict) else {}
                if isinstance(fulfillment, dict):
                    fulfilled_status = _clean(fulfillment.get("status")).lower()
            except (TypeError, ValueError):
                pass
            paid_at = row.paid_at or row.created_at
            if fulfilled_status:
                projection_already_applied = fulfilled_status in {"account_extended", "applied", "fulfilled"}
            else:
                projection_already_applied = bool(
                    legacy_paid_projection and paid_at is not None and paid_at < now
                )
            payments.append(
                {
                    "provider": provider,
                    "order_id": order_id,
                    "plan_code": _clean(row.plan_code) or "historical_paid",
                    "paid_at": paid_at,
                    "legacy_tg_id": int(row.tg_id) if row.tg_id is not None else None,
                    "record_type": "external_order",
                    "projection_already_applied": projection_already_applied,
                }
            )
    return sorted(
        payments,
        key=lambda row: (
            row.get("paid_at") or datetime.max,
            str(row.get("provider") or ""),
            str(row.get("order_id") or ""),
        ),
    )


def _ensure_ambiguous_stars_payment_markers(
    session: Session,
    counter: _Counter,
    *,
    account_id: str,
    now: datetime,
) -> None:
    tg_ids = [int(row[0]) for row in session.query(User.tg_id).filter(User.account_id == account_id).all()]
    if not tg_ids:
        return
    rows = (
        session.query(PayAttempt)
        .filter(
            PayAttempt.tg_id.in_(tg_ids),
            PayAttempt.status == "paid",
            PayAttempt.amount_stars > 0,
            PayAttempt.paid_at.isnot(None),
        )
        .all()
    )
    for row in rows:
        key = f"legacy-stars-payment-marker:v1:{int(row.id)}"
        marker = session.query(EntitlementGrant).filter_by(idempotency_key=key).first()
        if marker is None:
            marker = EntitlementGrant(
                id=str(uuid.uuid5(GRANT_NAMESPACE, key)),
                account_id=account_id,
                legacy_tg_id=int(row.tg_id),
                idempotency_key=key,
                source="legacy_stars_payment_marker",
                status="manual_review",
                grant_kind="audit_marker",
                plan_code=_clean(row.plan_code) or "stars_paid",
                activated_at=row.paid_at,
                duration_days=0,
                provider="stars",
                external_order_id=_clean(row.invoice_payload) or f"pay-attempt:{int(row.id)}",
                metadata_json=_json(
                    {
                        "payment_confirmed": True,
                        "projection_already_applied": False,
                        "review_reason": "missing_per_order_fulfillment_evidence",
                    }
                ),
                created_at=row.paid_at or now,
                updated_at=now,
            )
            session.add(marker)
            counter.grants_created += 1
        else:
            marker.account_id = account_id
            marker.updated_at = now


def _ensure_legacy_payment_authority(
    session: Session,
    counter: _Counter,
    *,
    user: User,
    account_id: str,
    now: datetime,
) -> None:
    _ensure_ambiguous_stars_payment_markers(session, counter, account_id=account_id, now=now)
    unsafe_key = f"provider-payment-legacy:v1:{account_id}"
    unsafe = session.query(EntitlementGrant).filter_by(idempotency_key=unsafe_key).first()
    if unsafe is not None:
        unsafe.source = "legacy_first_purchase_marker"
        unsafe.status = "manual_review"
        unsafe.grant_kind = "audit_marker"
        unsafe.provider = "legacy_flag"
        unsafe.metadata_json = _json({"corroborated": False, "migrated_from_unsafe_fact": True})
        unsafe.updated_at = now

    corroborated = _corroborated_account_payments(session, account_id=account_id, now=now)
    if corroborated:
        for index, payment in enumerate(corroborated):
            provider = str(payment["provider"])
            order_id = str(payment["order_id"])
            key = _historical_payment_key(provider, order_id)
            fact = session.query(EntitlementGrant).filter_by(idempotency_key=key).first()
            if fact is None:
                fact = EntitlementGrant(
                    id=str(uuid.uuid5(GRANT_NAMESPACE, key)),
                    account_id=account_id,
                    legacy_tg_id=payment.get("legacy_tg_id"),
                    idempotency_key=key,
                    source="provider_payment",
                    status="recorded",
                    grant_kind="payment_fact",
                    plan_code=str(payment.get("plan_code") or "historical_paid")[:32],
                    activated_at=payment.get("paid_at") or now,
                    duration_days=0,
                    provider=provider[:32],
                    external_order_id=order_id[:160],
                    metadata_json=_json(
                        {
                            "is_first_payment": index == 0,
                            "backfilled": True,
                            "corroborated": True,
                            "record_type": payment.get("record_type"),
                            "projection_already_applied": bool(payment.get("projection_already_applied")),
                        }
                    ),
                    created_at=payment.get("paid_at") or now,
                    updated_at=now,
                )
                session.add(fact)
                counter.grants_created += 1
            else:
                fact.account_id = account_id
                try:
                    metadata = json.loads(str(fact.metadata_json or "{}"))
                except (TypeError, ValueError):
                    metadata = {}
                if not isinstance(metadata, dict):
                    metadata = {}
                if str(fact.grant_kind or "") == "paid_access":
                    metadata["projection_already_applied"] = True
                elif payment.get("projection_already_applied"):
                    metadata["projection_already_applied"] = True
                fact.metadata_json = _json(metadata)
        from economy_service import normalize_account_payment_history

        normalize_account_payment_history(session, account_id=account_id, now=now)
        return

    if not bool(user.first_purchase_done):
        return
    marker_key = f"legacy-first-purchase-marker:v1:{int(user.tg_id)}"
    marker = session.query(EntitlementGrant).filter_by(idempotency_key=marker_key).first()
    if marker is None:
        session.add(
            EntitlementGrant(
                id=str(uuid.uuid5(GRANT_NAMESPACE, marker_key)),
                account_id=account_id,
                legacy_tg_id=int(user.tg_id),
                idempotency_key=marker_key,
                source="legacy_first_purchase_marker",
                status="manual_review",
                grant_kind="audit_marker",
                plan_code=_clean(user.current_plan_code) or "legacy_flag",
                activated_at=user.created_at or now,
                duration_days=0,
                provider="legacy_flag",
                metadata_json=_json({"corroborated": False, "first_purchase_done": True}),
                created_at=user.created_at or now,
                updated_at=now,
            )
        )
        counter.grants_created += 1
    else:
        marker.account_id = account_id
        marker.updated_at = now


def _ensure_grandfathered_channel_grant(
    session: Session,
    counter: _Counter,
    *,
    user: User,
    now: datetime,
) -> None:
    if user.channel_bonus_claimed_at is None or not user.account_id:
        return
    from economy_service import backfill_grandfathered_channel_grant

    before = (
        session.query(EntitlementGrant.id)
        .filter(
            EntitlementGrant.account_id == str(user.account_id),
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
        )
        .first()
    )
    grant = backfill_grandfathered_channel_grant(session, user=user, now=now)
    if before is None and grant is not None:
        counter.grants_created += 1


def _load_account_component_users(
    session: Session,
    seed_tg_ids: Iterable[int],
) -> list[User]:
    component_ids = {int(value) for value in seed_tg_ids if int(value) > 0}
    users_by_tg_id: dict[int, User] = {}
    while component_ids:
        query = (
            session.query(User)
            .filter(
                or_(
                    User.tg_id.in_(sorted(component_ids)),
                    User.linked_telegram_id.in_(sorted(component_ids)),
                )
            )
            .order_by(User.tg_id.asc())
        )
        rows = query.all()
        expanded_ids = set(component_ids)
        for row in rows:
            row_tg_id = int(row.tg_id)
            users_by_tg_id[row_tg_id] = row
            expanded_ids.add(row_tg_id)
            linked_tg_id = int(row.linked_telegram_id or 0)
            if linked_tg_id > 0:
                expanded_ids.add(linked_tg_id)
        if expanded_ids == component_ids:
            break
        component_ids = expanded_ids
    return [users_by_tg_id[tg_id] for tg_id in sorted(users_by_tg_id)]


def _lock_account_component_users(session: Session, seed_tg_ids: Iterable[int]) -> list[User]:
    """Discover first, then lock the complete component in one numeric order."""

    with session.no_autoflush:
        discovered = _load_account_component_users(session, seed_tg_ids)
        discovered_ids = sorted(int(user.tg_id) for user in discovered)
        if not discovered_ids:
            return []
        locked = (
            session.query(User)
            .filter(User.tg_id.in_(discovered_ids))
            .order_by(User.tg_id.asc())
            .with_for_update()
            .all()
        )
        confirmed = _load_account_component_users(session, seed_tg_ids)
    confirmed_ids = sorted(int(user.tg_id) for user in confirmed)
    if confirmed_ids != discovered_ids:
        raise RuntimeError("account component changed during lock acquisition")
    return locked


def ensure_user_account_foundation(
    session: Session,
    user: User,
    *,
    now: datetime | None = None,
    include_legacy_payment_authority: bool = True,
) -> AccountBackfillReport:
    """Synchronize one newly created or updated legacy user into the additive model."""

    effective_now = now or _utcnow()
    with session.no_autoflush:
        linked_telegram_id = int(user.linked_telegram_id or 0)
        reverse_link = (
            session.query(User.tg_id)
            .filter(User.linked_telegram_id == int(user.tg_id))
            .order_by(User.tg_id.asc())
            .first()
        )
    if linked_telegram_id > 0 or reverse_link is not None:
        component_seeds = {int(user.tg_id)}
        if linked_telegram_id > 0:
            component_seeds.add(linked_telegram_id)
        return backfill_account_foundation(
            session,
            now=effective_now,
            legacy_tg_ids=component_seeds,
            pending_seed_user=user,
        )

    with session.no_autoflush:
        (
            session.query(User.tg_id)
            .filter(User.tg_id == int(user.tg_id))
            .with_for_update()
            .first()
        )
    _acquire_account_foundation_projection_locks(
        session,
        [user],
        shared_global=True,
    )

    counter = _Counter(users_seen=1)
    account_id = _clean(user.account_id) or _account_id_for_legacy_user(int(user.tg_id))
    account = session.query(Account).filter_by(id=account_id).first()
    if account is not None and account.status == "merged" and account.merged_into_account_id:
        account_id = str(account.merged_into_account_id)
        account = session.query(Account).filter_by(id=account_id).first()
    if account is None:
        account = Account(
            id=account_id,
            status="active",
            created_source="runtime_projection",
            created_at=user.created_at or effective_now,
            updated_at=effective_now,
        )
        session.add(account)
        counter.accounts_created += 1
    else:
        account.updated_at = effective_now
    user.account_id = account_id
    session.flush()

    _ensure_identity(
        session,
        counter,
        account_id=account_id,
        kind="legacy_user",
        provider="pokrov",
        subject_norm=str(int(user.tg_id)),
        verified_at=user.created_at,
        metadata={"legacy_tg_id": int(user.tg_id)},
        now=effective_now,
    )
    if 0 < int(user.tg_id) < SYNTHETIC_EMAIL_ACCOUNT_MIN:
        _ensure_identity(
            session,
            counter,
            account_id=account_id,
            kind="telegram",
            provider="telegram",
            subject_norm=str(int(user.tg_id)),
            verified_at=user.created_at,
            metadata={"source": "direct_telegram_user"},
            now=effective_now,
        )
    if linked_telegram_id > 0:
        _ensure_identity(
            session,
            counter,
            account_id=account_id,
            kind="telegram",
            provider="telegram",
            subject_norm=str(linked_telegram_id),
            verified_at=user.linked_telegram_linked_at,
            metadata={"source": "linked_telegram_id"},
            now=effective_now,
        )
    _ensure_device(session, counter, user=user, account_id=account_id, now=effective_now)
    _ensure_legacy_grant(
        session,
        counter,
        user=user,
        account_id=account_id,
        now=effective_now,
        include_legacy_payment_authority=include_legacy_payment_authority,
    )
    _ensure_grandfathered_channel_grant(session, counter, user=user, now=effective_now)

    for email_identity in (
        session.query(WebEmailIdentity)
        .filter(WebEmailIdentity.linked_tg_id == int(user.tg_id))
        .order_by(WebEmailIdentity.id.asc())
        .all()
    ):
        _ensure_identity(
            session,
            counter,
            account_id=account_id,
            kind="email",
            provider="email",
            subject_norm=_clean(email_identity.email_norm).lower(),
            verified_at=email_identity.verified_at if bool(email_identity.is_verified) else None,
            metadata={"legacy_email_identity_id": int(email_identity.id)},
            now=effective_now,
        )

    session.flush()
    return counter.freeze()


def backfill_account_foundation(
    session: Session,
    *,
    now: datetime | None = None,
    legacy_tg_ids: Iterable[int] | None = None,
    pending_seed_user: User | None = None,
) -> AccountBackfillReport:
    """Build additive account projections without deleting legacy ownership rows."""

    effective_now = now or _utcnow()
    with session.no_autoflush:
        users = (
            _lock_account_component_users(session, legacy_tg_ids)
            if legacy_tg_ids is not None
            else session.query(User).order_by(User.tg_id.asc()).with_for_update().all()
        )
        if pending_seed_user is not None and pending_seed_user in session.new:
            users_by_tg_id = {int(component_user.tg_id): component_user for component_user in users}
            users_by_tg_id.setdefault(int(pending_seed_user.tg_id), pending_seed_user)
            users = [users_by_tg_id[tg_id] for tg_id in sorted(users_by_tg_id)]
    _acquire_account_foundation_projection_locks(
        session,
        users,
        shared_global=False,
    )
    counter = _Counter(users_seen=len(users))
    if not users:
        return counter.freeze()

    users_by_tg_id = {int(user.tg_id): user for user in users}
    groups = _DisjointSet(users_by_tg_id)
    for user in users:
        linked_telegram_id = int(user.linked_telegram_id or 0)
        if linked_telegram_id in users_by_tg_id:
            groups.union(int(user.tg_id), linked_telegram_id)

    components: dict[int, list[User]] = {}
    for user in users:
        components.setdefault(groups.find(int(user.tg_id)), []).append(user)

    account_id_by_tg_id: dict[int, str] = {}
    for component_users in components.values():
        existing_ids = sorted({_clean(user.account_id) for user in component_users if _clean(user.account_id)})
        existing_accounts = {
            str(account.id): account
            for account in (
                session.query(Account).filter(Account.id.in_(existing_ids)).all()
                if existing_ids
                else []
            )
        }
        deterministic_id = _account_id_for_legacy_user(min(int(user.tg_id) for user in component_users))
        target_account_id = deterministic_id if deterministic_id in existing_ids else (
            existing_ids[0] if existing_ids else deterministic_id
        )
        target_account = existing_accounts.get(target_account_id)
        if target_account is None:
            target_account = Account(
                id=target_account_id,
                status="active",
                created_source="legacy_backfill",
                created_at=min((user.created_at or effective_now) for user in component_users),
                updated_at=effective_now,
            )
            session.add(target_account)
            counter.accounts_created += 1
        else:
            target_account.updated_at = effective_now

        component_accounts = [*existing_accounts.values()]
        if target_account not in component_accounts:
            component_accounts.append(target_account)
        statuses = {_clean(account.status).lower() for account in component_accounts}
        restrictive_statuses = sorted(statuses - {"", "active", "merged"})
        if "blocked" in statuses:
            target_account.status = "blocked"
        elif restrictive_statuses:
            target_account.status = restrictive_statuses[0]
        else:
            target_account.status = "active"
        target_account.auth_epoch = max(int(account.auth_epoch or 0) for account in component_accounts)
        target_account.merged_into_account_id = None

        for source_account_id in existing_ids:
            if source_account_id == target_account_id:
                continue
            source_account = existing_accounts.get(source_account_id)
            if source_account is not None:
                if source_account.status != "merged" or source_account.merged_into_account_id != target_account_id:
                    counter.accounts_merged += 1
                source_account.status = "merged"
                source_account.merged_into_account_id = target_account_id
                source_account.updated_at = effective_now
            _move_account_owned_rows(
                session,
                source_account_id=source_account_id,
                target_account_id=target_account_id,
                now=effective_now,
            )

        for user in component_users:
            user.account_id = target_account_id
            account_id_by_tg_id[int(user.tg_id)] = target_account_id

    session.flush()

    for user in users:
        account_id = account_id_by_tg_id[int(user.tg_id)]
        _ensure_identity(
            session,
            counter,
            account_id=account_id,
            kind="legacy_user",
            provider="pokrov",
            subject_norm=str(int(user.tg_id)),
            verified_at=user.created_at,
            metadata={"legacy_tg_id": int(user.tg_id)},
            now=effective_now,
        )
        if 0 < int(user.tg_id) < SYNTHETIC_EMAIL_ACCOUNT_MIN:
            _ensure_identity(
                session,
                counter,
                account_id=account_id,
                kind="telegram",
                provider="telegram",
                subject_norm=str(int(user.tg_id)),
                verified_at=user.created_at,
                metadata={"source": "direct_telegram_user"},
                now=effective_now,
            )
        linked_telegram_id = int(user.linked_telegram_id or 0)
        if linked_telegram_id > 0:
            _ensure_identity(
                session,
                counter,
                account_id=account_id,
                kind="telegram",
                provider="telegram",
                subject_norm=str(linked_telegram_id),
                verified_at=user.linked_telegram_linked_at,
                metadata={"source": "linked_telegram_id"},
                now=effective_now,
            )
        _ensure_device(session, counter, user=user, account_id=account_id, now=effective_now)
        _ensure_legacy_grant(session, counter, user=user, account_id=account_id, now=effective_now)
        _ensure_grandfathered_channel_grant(session, counter, user=user, now=effective_now)

    email_identities_query = session.query(WebEmailIdentity)
    if legacy_tg_ids is not None:
        email_identities_query = email_identities_query.filter(
            WebEmailIdentity.linked_tg_id.in_(sorted(account_id_by_tg_id))
        )
    for email_identity in email_identities_query.order_by(WebEmailIdentity.id.asc()).all():
        account_id = account_id_by_tg_id.get(int(email_identity.linked_tg_id))
        if account_id is None:
            _create_review(
                session,
                counter,
                reason_code="orphan_email_identity",
                subject_hint=f"email:{_clean(email_identity.email_norm).lower()}",
                account_id=None,
                conflicting_account_id=None,
                details={"legacy_email_identity_id": int(email_identity.id)},
                now=effective_now,
            )
            continue
        _ensure_identity(
            session,
            counter,
            account_id=account_id,
            kind="email",
            provider="email",
            subject_norm=_clean(email_identity.email_norm).lower(),
            verified_at=email_identity.verified_at if bool(email_identity.is_verified) else None,
            metadata={"legacy_email_identity_id": int(email_identity.id)},
            now=effective_now,
        )

    session.flush()
    return counter.freeze()


def run_account_foundation_backfill_once(
    session: Session,
    *,
    now: datetime | None = None,
) -> AccountBackfillReport:
    """Run the legacy projection once per database, not once per service process."""

    effective_now = now or _utcnow()
    _acquire_postgres_advisory_lock(session, ACCOUNT_FOUNDATION_STARTUP_LOCK)
    marker = session.query(AppSetting).filter_by(key=ACCOUNT_FOUNDATION_BACKFILL_KEY).first()
    if marker is not None:
        try:
            payload = json.loads(str(marker.value_json or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        if payload.get("status") == "complete" and int(payload.get("version") or 0) == 1:
            missing_account = (
                session.query(User.tg_id)
                .filter(User.account_id.is_(None))
                .order_by(User.tg_id.asc())
                .first()
            )
            if missing_account is None:
                return AccountBackfillReport()

    report = backfill_account_foundation(
        session,
        now=effective_now,
    )
    payload = _json(
        {
            "completed_at": effective_now.isoformat(),
            "report": {
                "accounts_created": report.accounts_created,
                "accounts_merged": report.accounts_merged,
                "devices_created": report.devices_created,
                "grants_created": report.grants_created,
                "identities_created": report.identities_created,
                "reviews_created": report.reviews_created,
                "users_seen": report.users_seen,
            },
            "status": "complete",
            "version": 1,
        }
    )
    if marker is None:
        marker = AppSetting(
            key=ACCOUNT_FOUNDATION_BACKFILL_KEY,
            value_json=payload,
            updated_at=effective_now,
        )
        session.add(marker)
    else:
        marker.value_json = payload
        marker.updated_at = effective_now
    session.flush()
    return report
