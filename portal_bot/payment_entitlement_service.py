from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from economy_service import rebuild_account_entitlement_projection, record_successful_payment_grant
from models import (
    Account,
    AccountIdentity,
    EntitlementGrant,
    GiftCard,
    PaymentEntitlementClaim,
)


CLAIM_STATUS_PENDING = "pending_payment"
CLAIM_STATUS_ATTACHED_PENDING = "attached_pending_payment"
CLAIM_STATUS_PAID_UNCLAIMED = "paid_unclaimed"
CLAIM_STATUS_PAID_ATTACHED = "paid_attached"
CLAIM_STATUS_FULFILLED = "fulfilled"
CLAIM_STATUS_REVERSED = "reversed"
CLAIM_STATUS_MANUAL_REVIEW = "manual_review"

_SAFE_ERROR_CODES = {
    "access_key_issue_failed",
    "account_conflict",
    "claim_definition_conflict",
    "claim_processing_failed",
    "claim_reversed",
    "durable_fulfillment_failed",
    "fallback_creator_conflict",
    "fallback_missing",
    "fallback_ownership_conflict",
    "fallback_redeemed_conflict",
    "fallback_type_conflict",
    "grant_fulfillment_failed",
    "grant_not_found",
    "manual_review",
    "order_owner_mismatch",
    "verified_email_mismatch",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now(value: datetime | None) -> datetime:
    return (value or _utcnow()).replace(tzinfo=None, microsecond=0)


def _provider(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        raise PaymentEntitlementError("provider_required")
    return normalized[:32]


def _order_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise PaymentEntitlementError("order_id_required")
    return normalized[:128]


def normalize_buyer_email(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized or "@" not in normalized or len(normalized) > 255:
        raise PaymentEntitlementError("buyer_email_required")
    return normalized


class PaymentEntitlementError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


class PaymentEntitlementNotFoundError(PaymentEntitlementError):
    pass


@dataclass(frozen=True)
class PaymentEntitlementResult:
    claim: PaymentEntitlementClaim
    code: str
    changed: bool


def _safe_error_code(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _SAFE_ERROR_CODES else "claim_processing_failed"


def _record_safe_error(row: PaymentEntitlementClaim, code: str, now: datetime) -> None:
    row.last_error = _safe_error_code(code)
    row.last_error_at = now
    row.updated_at = now


def canonical_account_id(session: Session, account_id: str) -> str:
    current = str(account_id or "").strip()
    if not current:
        raise PaymentEntitlementError("account_id_required")
    visited: set[str] = set()
    for _ in range(32):
        if current in visited:
            raise PaymentEntitlementError("account_merge_cycle")
        visited.add(current)
        account = session.query(Account).filter(Account.id == current).with_for_update().one_or_none()
        if account is None:
            raise PaymentEntitlementError("account_not_found")
        if str(account.status or "").strip().lower() != "merged" or not account.merged_into_account_id:
            return current
        current = str(account.merged_into_account_id)
    raise PaymentEntitlementError("account_merge_depth")


def _claim(
    session: Session,
    *,
    provider: str,
    order_id: str,
) -> PaymentEntitlementClaim:
    row = (
        session.query(PaymentEntitlementClaim)
        .filter(
            PaymentEntitlementClaim.provider == _provider(provider),
            PaymentEntitlementClaim.order_id == _order_id(order_id),
        )
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise PaymentEntitlementNotFoundError("claim_not_found")
    return row


def _claim_lookup(
    session: Session,
    *,
    provider: str,
    order_id: str,
) -> PaymentEntitlementClaim:
    row = (
        session.query(PaymentEntitlementClaim)
        .filter(
            PaymentEntitlementClaim.provider == _provider(provider),
            PaymentEntitlementClaim.order_id == _order_id(order_id),
        )
        .one_or_none()
    )
    if row is None:
        raise PaymentEntitlementNotFoundError("claim_not_found")
    return row


def _lock_canonical_accounts(session: Session, account_ids: set[str]) -> dict[str, str]:
    normalized = {str(value or "").strip() for value in account_ids if str(value or "").strip()}
    resolved = {account_id: canonical_account_id(session, account_id) for account_id in sorted(normalized)}
    for canonical_id in tuple(resolved.values()):
        resolved.setdefault(canonical_id, canonical_id)
    return resolved


def _lock_claim_after_accounts(
    session: Session,
    *,
    provider: str,
    order_id: str,
    account_ids: set[str],
) -> tuple[PaymentEntitlementClaim, dict[str, str]]:
    snapshot = _claim_lookup(session, provider=provider, order_id=order_id)
    raw_account_ids = set(account_ids)
    if snapshot.account_id:
        raw_account_ids.add(str(snapshot.account_id))
    canonical = _lock_canonical_accounts(session, raw_account_ids)
    row = _claim(session, provider=provider, order_id=order_id)
    if row.account_id and str(row.account_id) not in canonical:
        raise PaymentEntitlementError("claim_account_changed_retry")
    return row, canonical


def ensure_pending_claim(
    session: Session,
    *,
    provider: str,
    order_id: str,
    buyer_email: str,
    plan_code: str,
    duration_days: int,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    provider_key = _provider(provider)
    order_key = _order_id(order_id)
    email_key = normalize_buyer_email(buyer_email)
    plan_key = str(plan_code or "").strip().lower()[:32]
    days = int(duration_days or 0)
    if not plan_key or days <= 0:
        raise PaymentEntitlementError("invalid_plan")
    current_now = _now(now)
    existing = (
        session.query(PaymentEntitlementClaim)
        .filter_by(provider=provider_key, order_id=order_key)
        .with_for_update()
        .one_or_none()
    )
    if existing is not None:
        if (
            existing.buyer_email_norm != email_key
            or existing.plan_code != plan_key
            or int(existing.duration_days or 0) != days
        ):
            if existing.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                existing.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(existing, "claim_definition_conflict", current_now)
            session.flush()
            return PaymentEntitlementResult(existing, "claim_definition_conflict", True)
        return PaymentEntitlementResult(existing, "already_exists", False)
    row = PaymentEntitlementClaim(
        provider=provider_key,
        order_id=order_key,
        buyer_email_norm=email_key,
        status=CLAIM_STATUS_PENDING,
        plan_code=plan_key,
        duration_days=days,
        created_at=current_now,
        updated_at=current_now,
    )
    session.add(row)
    session.flush()
    return PaymentEntitlementResult(row, "created", True)


def mark_paid(
    session: Session,
    *,
    provider: str,
    order_id: str,
    paid_at: datetime | None = None,
) -> PaymentEntitlementResult:
    row = _claim(session, provider=provider, order_id=order_id)
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    current_now = _now(paid_at)
    changed = row.paid_at is None
    row.paid_at = row.paid_at or current_now
    if row.status != CLAIM_STATUS_FULFILLED:
        next_status = CLAIM_STATUS_PAID_ATTACHED if row.account_id else CLAIM_STATUS_PAID_UNCLAIMED
        changed = changed or row.status != next_status
        row.status = next_status
    row.updated_at = current_now
    session.flush()
    return PaymentEntitlementResult(row, "paid" if changed else "already_paid", changed)


def record_claim_error(
    session: Session,
    *,
    provider: str,
    order_id: str,
    error_code: str,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    row = _claim(session, provider=provider, order_id=order_id)
    if row.status in {CLAIM_STATUS_MANUAL_REVIEW, CLAIM_STATUS_REVERSED} and row.last_error and row.last_error_at:
        return PaymentEntitlementResult(row, str(row.last_error), False)
    _record_safe_error(row, error_code, _now(now))
    session.flush()
    return PaymentEntitlementResult(row, row.last_error, True)


def _verified_email_identity(session: Session, *, email: str, lock: bool) -> AccountIdentity | None:
    query = (
        session.query(AccountIdentity)
        .filter(
            AccountIdentity.kind == "email",
            AccountIdentity.provider == "email",
            AccountIdentity.subject_norm == email,
            AccountIdentity.verified_at.isnot(None),
            AccountIdentity.disabled_at.is_(None),
        )
    )
    if lock:
        query = query.with_for_update()
    return query.one_or_none()


def _attach(
    session: Session,
    *,
    row: PaymentEntitlementClaim,
    account_id: str,
    now: datetime,
    canonical_accounts: dict[str, str],
    conflict_to_manual_review: bool = True,
) -> PaymentEntitlementResult:
    target_raw = str(account_id or "").strip()
    target_account_id = canonical_accounts.get(target_raw)
    if not target_account_id:
        raise PaymentEntitlementError("account_lock_required")
    if row.account_id:
        existing_account_id = canonical_accounts.get(str(row.account_id))
        if not existing_account_id:
            raise PaymentEntitlementError("claim_account_changed_retry")
        row.account_id = existing_account_id
        if existing_account_id != target_account_id:
            if conflict_to_manual_review and row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
                _record_safe_error(row, "account_conflict", now)
                session.flush()
                return PaymentEntitlementResult(row, "account_conflict", True)
            return PaymentEntitlementResult(row, "account_conflict", False)
        return PaymentEntitlementResult(row, "already_attached", False)
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    row.account_id = target_account_id
    row.attached_at = row.attached_at or now
    row.status = CLAIM_STATUS_PAID_ATTACHED if row.paid_at else CLAIM_STATUS_ATTACHED_PENDING
    row.updated_at = now
    session.flush()
    return PaymentEntitlementResult(row, "attached", True)


def attach_by_verified_email(
    session: Session,
    *,
    provider: str,
    order_id: str,
    buyer_email: str,
    account_id: str,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    current_now = _now(now)
    email_key = normalize_buyer_email(buyer_email)
    identity_snapshot = _verified_email_identity(session, email=email_key, lock=False)
    account_ids = {str(account_id)}
    if identity_snapshot is not None:
        account_ids.add(str(identity_snapshot.account_id))
    row, canonical_accounts = _lock_claim_after_accounts(
        session,
        provider=provider,
        order_id=order_id,
        account_ids=account_ids,
    )
    target_account_id = canonical_accounts.get(str(account_id).strip())
    if not target_account_id:
        raise PaymentEntitlementError("account_lock_required")
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    if row.account_id:
        existing_account_id = canonical_accounts.get(str(row.account_id))
        if not existing_account_id:
            raise PaymentEntitlementError("claim_account_changed_retry")
        if existing_account_id != target_account_id:
            if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, "account_conflict", current_now)
            session.flush()
            return PaymentEntitlementResult(row, "account_conflict", True)
    identity = _verified_email_identity(session, email=email_key, lock=True)
    identity_account_id = canonical_accounts.get(str(identity.account_id)) if identity is not None else None
    if email_key != row.buyer_email_norm or identity_account_id != target_account_id:
        if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
            row.status = CLAIM_STATUS_MANUAL_REVIEW
        _record_safe_error(row, "verified_email_mismatch", current_now)
        session.flush()
        return PaymentEntitlementResult(row, "verified_email_mismatch", True)
    return _attach(
        session,
        row=row,
        account_id=str(account_id),
        now=current_now,
        canonical_accounts=canonical_accounts,
    )


def _fulfill_locked_claim(
    session: Session,
    *,
    row: PaymentEntitlementClaim,
    account_key: str,
    legacy_tg_id: int | None,
    now: datetime,
) -> PaymentEntitlementResult:
    if row.status == CLAIM_STATUS_FULFILLED and row.grant_id:
        return PaymentEntitlementResult(row, "already_fulfilled", False)
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    if row.paid_at is None:
        return PaymentEntitlementResult(row, "payment_pending", False)
    if not row.account_id:
        return PaymentEntitlementResult(row, "claim_unattached", False)
    row.account_id = account_key
    try:
        payment = record_successful_payment_grant(
            session,
            account_id=account_key,
            legacy_tg_id=int(legacy_tg_id) if legacy_tg_id is not None else None,
            provider=str(row.provider),
            order_id=str(row.order_id),
            plan_code=str(row.plan_code),
            duration_days=max(1, int(row.duration_days)),
            paid_at=row.paid_at,
        )
    except Exception:
        _record_safe_error(row, "grant_fulfillment_failed", now)
        session.flush()
        raise
    row.grant_id = str(payment.grant.id)
    row.status = CLAIM_STATUS_FULFILLED
    row.fulfilled_at = row.fulfilled_at or now
    row.updated_at = now
    session.flush()
    return PaymentEntitlementResult(row, "fulfilled", True)


def fulfill_attached_paid_claim(
    session: Session,
    *,
    provider: str,
    order_id: str,
    legacy_tg_id: int | None = None,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    snapshot = _claim_lookup(session, provider=provider, order_id=order_id)
    if not snapshot.account_id:
        row = _claim(session, provider=provider, order_id=order_id)
        return PaymentEntitlementResult(row, "claim_unattached", False)
    row, canonical_accounts = _lock_claim_after_accounts(
        session,
        provider=provider,
        order_id=order_id,
        account_ids={str(snapshot.account_id)},
    )
    account_key = canonical_accounts.get(str(row.account_id))
    if not account_key:
        raise PaymentEntitlementError("claim_account_changed_retry")
    return _fulfill_locked_claim(
        session,
        row=row,
        account_key=account_key,
        legacy_tg_id=legacy_tg_id,
        now=_now(now or row.paid_at),
    )


def mark_paid_and_fulfill_attached_claim(
    session: Session,
    *,
    provider: str,
    order_id: str,
    buyer_email: str,
    plan_code: str,
    duration_days: int,
    paid_at: datetime | None = None,
    legacy_tg_id: int | None = None,
) -> PaymentEntitlementResult:
    snapshot = _claim_lookup(session, provider=provider, order_id=order_id)
    if not snapshot.account_id:
        return PaymentEntitlementResult(snapshot, "claim_unattached", False)
    current_now = _now(paid_at)
    row, canonical_accounts = _lock_claim_after_accounts(
        session,
        provider=provider,
        order_id=order_id,
        account_ids={str(snapshot.account_id)},
    )
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    definition_matches = (
        row.buyer_email_norm == normalize_buyer_email(buyer_email)
        and row.plan_code == str(plan_code or "").strip().lower()[:32]
        and int(row.duration_days or 0) == int(duration_days or 0)
    )
    if not definition_matches:
        if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
            row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, "claim_definition_conflict", current_now)
            session.flush()
        return PaymentEntitlementResult(row, "claim_definition_conflict", row.status == CLAIM_STATUS_MANUAL_REVIEW)
    row.paid_at = row.paid_at or current_now
    if row.status != CLAIM_STATUS_FULFILLED:
        row.status = CLAIM_STATUS_PAID_ATTACHED
    row.updated_at = current_now
    account_key = canonical_accounts.get(str(row.account_id))
    if not account_key:
        raise PaymentEntitlementError("claim_account_changed_retry")
    return _fulfill_locked_claim(
        session,
        row=row,
        account_key=account_key,
        legacy_tg_id=legacy_tg_id,
        now=current_now,
    )


def ensure_fallback_gift_card(
    session: Session,
    *,
    provider: str,
    order_id: str,
    gift_code: str,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    snapshot = _claim_lookup(session, provider=provider, order_id=order_id)
    if snapshot.account_id:
        row, canonical_accounts = _lock_claim_after_accounts(
            session,
            provider=provider,
            order_id=order_id,
            account_ids={str(snapshot.account_id)},
        )
    else:
        row = _claim(session, provider=provider, order_id=order_id)
        canonical_accounts = {}
    if row.fallback_gift_card_id:
        card = (
            session.query(GiftCard)
            .filter(GiftCard.id == int(row.fallback_gift_card_id))
            .with_for_update()
            .one_or_none()
        )
        if card is None:
            if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, "fallback_missing", _now(now))
            session.flush()
            return PaymentEntitlementResult(row, "fallback_missing", True)
        conflict_code = ""
        if int(card.created_by or 0) != 0:
            conflict_code = "fallback_creator_conflict"
        elif str(card.card_type or "").strip().lower() != str(row.plan_code or "").strip().lower():
            conflict_code = "fallback_type_conflict"
        elif (
            (card.redeemed_by is not None or card.redeemed_at is not None)
            and row.status != CLAIM_STATUS_FULFILLED
        ):
            conflict_code = "fallback_redeemed_conflict"
        if conflict_code:
            if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, conflict_code, _now(now))
            session.flush()
            return PaymentEntitlementResult(row, conflict_code, True)
        return PaymentEntitlementResult(row, "fallback_already_exists", False)
    if row.status in {CLAIM_STATUS_REVERSED, CLAIM_STATUS_MANUAL_REVIEW}:
        return PaymentEntitlementResult(row, row.status, False)
    if row.paid_at is None:
        return PaymentEntitlementResult(row, "payment_pending", False)
    normalized_code = str(gift_code or "").strip().upper()[:32]
    if not normalized_code:
        raise PaymentEntitlementError("gift_code_required")
    card = (
        session.query(GiftCard)
        .filter(GiftCard.code == normalized_code)
        .with_for_update()
        .one_or_none()
    )
    if card is not None:
        current_now = _now(now)
        linked_claim = (
            session.query(PaymentEntitlementClaim)
            .filter(
                PaymentEntitlementClaim.fallback_gift_card_id == int(card.id),
                PaymentEntitlementClaim.id != int(row.id),
            )
            .with_for_update()
            .one_or_none()
        )
        conflict_code = ""
        if linked_claim is not None:
            conflict_code = "fallback_ownership_conflict"
        elif int(card.created_by or 0) != 0:
            conflict_code = "fallback_creator_conflict"
        elif str(card.card_type or "").strip().lower() != str(row.plan_code or "").strip().lower():
            conflict_code = "fallback_type_conflict"
        elif card.redeemed_by is not None or card.redeemed_at is not None:
            conflict_code = "fallback_redeemed_conflict"
        if conflict_code:
            if row.status not in {CLAIM_STATUS_FULFILLED, CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, conflict_code, current_now)
            session.flush()
            return PaymentEntitlementResult(row, conflict_code, True)
        row.fallback_gift_card_id = int(card.id)
        row.updated_at = current_now
        session.flush()
        return PaymentEntitlementResult(row, "fallback_linked_existing", True)
    card = GiftCard(code=normalized_code, card_type=str(row.plan_code), created_by=0, created_at=_now(now))
    session.add(card)
    session.flush()
    row.fallback_gift_card_id = int(card.id)
    row.updated_at = _now(now)
    session.flush()
    return PaymentEntitlementResult(row, "fallback_created", True)


def reverse_claim(
    session: Session,
    *,
    provider: str,
    order_id: str,
    reason: str,
    reversed_at: datetime | None = None,
) -> PaymentEntitlementResult:
    snapshot = _claim_lookup(session, provider=provider, order_id=order_id)
    if snapshot.account_id:
        row, canonical_accounts = _lock_claim_after_accounts(
            session,
            provider=provider,
            order_id=order_id,
            account_ids={str(snapshot.account_id)},
        )
    else:
        row = _claim(session, provider=provider, order_id=order_id)
        canonical_accounts = {}
    if row.reversed_at is not None:
        return PaymentEntitlementResult(row, "already_reversed", False)
    current_now = _now(reversed_at)
    reason_key = str(reason or "provider_reversal").strip().lower()[:64] or "provider_reversal"
    if row.fallback_gift_card_id is not None:
        fallback = (
            session.query(GiftCard)
            .filter(GiftCard.id == int(row.fallback_gift_card_id))
            .with_for_update()
            .one_or_none()
        )
        if fallback is None:
            row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, "fallback_missing", current_now)
            session.flush()
            return PaymentEntitlementResult(row, "fallback_missing", True)
    if row.grant_id:
        grant = session.query(EntitlementGrant).filter(EntitlementGrant.id == row.grant_id).with_for_update().one_or_none()
        if grant is None:
            if row.status not in {CLAIM_STATUS_REVERSED}:
                row.status = CLAIM_STATUS_MANUAL_REVIEW
            _record_safe_error(row, "grant_not_found", current_now)
            session.flush()
            return PaymentEntitlementResult(row, "grant_not_found", True)
        if grant.reversed_at is None:
            grant.status = "reversed"
            grant.reversed_at = current_now
            grant.reversal_reason = reason_key
            grant.updated_at = current_now
        if row.account_id:
            account_key = canonical_accounts.get(str(row.account_id))
            if not account_key:
                raise PaymentEntitlementError("claim_account_changed_retry")
            row.account_id = account_key
            rebuild_account_entitlement_projection(session, account_id=account_key, now=current_now)
    row.status = CLAIM_STATUS_REVERSED
    row.reversed_at = current_now
    row.reversal_reason = reason_key
    row.updated_at = current_now
    session.flush()
    return PaymentEntitlementResult(row, "reversed", True)


def redeem_payment_fallback(
    session: Session,
    *,
    gift_card_id: int,
    account_id: str,
    legacy_tg_id: int | None,
    now: datetime | None = None,
) -> PaymentEntitlementResult:
    snapshot = (
        session.query(PaymentEntitlementClaim)
        .filter(PaymentEntitlementClaim.fallback_gift_card_id == int(gift_card_id))
        .one_or_none()
    )
    if snapshot is None:
        raise PaymentEntitlementNotFoundError("payment_fallback_not_found")
    current_now = _now(now)
    canonical_accounts = _lock_canonical_accounts(
        session,
        {str(account_id), str(snapshot.account_id or "")},
    )
    row = (
        session.query(PaymentEntitlementClaim)
        .filter(
            PaymentEntitlementClaim.id == int(snapshot.id),
            PaymentEntitlementClaim.fallback_gift_card_id == int(gift_card_id),
        )
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise PaymentEntitlementNotFoundError("payment_fallback_not_found")
    if row.status == CLAIM_STATUS_REVERSED:
        return PaymentEntitlementResult(row, "claim_reversed", False)
    if row.status == CLAIM_STATUS_MANUAL_REVIEW:
        return PaymentEntitlementResult(row, "manual_review", False)
    attached = _attach(
        session,
        row=row,
        account_id=account_id,
        now=current_now,
        canonical_accounts=canonical_accounts,
        conflict_to_manual_review=False,
    )
    if attached.code == "account_conflict":
        return attached
    account_key = canonical_accounts.get(str(row.account_id))
    if not account_key:
        raise PaymentEntitlementError("claim_account_changed_retry")
    fulfilled = _fulfill_locked_claim(
        session,
        row=row,
        account_key=account_key,
        legacy_tg_id=legacy_tg_id,
        now=current_now,
    )
    if fulfilled.code in {"fulfilled", "already_fulfilled"} and legacy_tg_id is not None:
        card = session.query(GiftCard).filter(GiftCard.id == int(gift_card_id)).with_for_update().one_or_none()
        if card is not None and card.redeemed_by is None:
            card.redeemed_by = int(legacy_tg_id)
            card.redeemed_at = current_now
            session.flush()
    return fulfilled
