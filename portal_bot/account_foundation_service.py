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
    RecoveryCode,
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
    ):
        session.query(model).filter(model.account_id == source_account_id).update(
            {model.account_id: target_account_id},
            synchronize_session=False,
        )


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
) -> None:
    idempotency_key = f"legacy-user:{int(user.tg_id)}:snapshot-v1"
    existing = session.query(EntitlementGrant).filter_by(idempotency_key=idempotency_key).first()
    if existing is not None:
        existing.account_id = account_id
        return
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
            metadata_json=_json(
                {
                    "first_purchase_done": bool(user.first_purchase_done),
                    "sub_type": _clean(user.sub_type),
                    "trial_used": bool(user.trial_used),
                }
            ),
            created_at=now,
            updated_at=now,
        )
    )
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
    _ensure_legacy_grant(session, counter, user=user, account_id=account_id, now=effective_now)

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
