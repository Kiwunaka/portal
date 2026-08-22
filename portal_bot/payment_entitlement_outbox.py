"""Transactional outbox for applied provider-payment entitlements."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import func
from sqlalchemy.orm import Session


EVENT_TYPE = "payment_entitlement.applied"
SCHEMA_VERSION = 1
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DELIVERED = "delivered"
STATUS_DEAD_LETTER = "dead_letter"
_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "event_type",
        "grant_id",
        "provider",
        "order_id",
    }
)


class PaymentEntitlementOutboxError(RuntimeError):
    def __init__(self, code: str):
        self.code = str(code or "outbox_error").strip().lower()[:64] or "outbox_error"
        super().__init__(self.code)


@dataclass(frozen=True)
class OutboxClaim:
    row_id: str
    token: str
    attempts: int


def _models() -> Any:
    try:
        from . import models
    except ImportError:
        import models

    return models


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(tzinfo=None)


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _idempotency_key(provider: str, order_id: str) -> str:
    authority = f"{str(provider).strip().lower()}\0{str(order_id).strip()}"
    digest = hashlib.sha256(authority.encode("utf-8")).hexdigest()
    return f"payment-entitlement:v1:{digest}"


def _event_payload(grant: Any, *, provider: str, order_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "event_type": EVENT_TYPE,
        "grant_id": str(grant.id or "").strip(),
        "provider": str(provider or "").strip().lower()[:32],
        "order_id": str(order_id or "").strip()[:160],
    }
    if not all(
        (
            payload["grant_id"],
            payload["provider"],
            payload["order_id"],
        )
    ):
        raise PaymentEntitlementOutboxError("outbox_grant_incomplete")
    if str(grant.source or "") != "provider_payment":
        raise PaymentEntitlementOutboxError("outbox_grant_source_invalid")
    if (
        str(grant.status or "") != "active"
        or str(grant.grant_kind or "") != "paid_access"
    ):
        raise PaymentEntitlementOutboxError("outbox_grant_state_invalid")
    serialized = _compact(payload)
    if len(serialized.encode("utf-8")) > 2048:
        raise PaymentEntitlementOutboxError("outbox_payload_too_large")
    return payload


def ensure_payment_entitlement_outbox(
    session: Session,
    *,
    grant: Any,
    provider: str,
    order_id: str,
    now: datetime,
) -> Any:
    models = _models()
    payload = _event_payload(grant, provider=provider, order_id=order_id)
    payload_json = _compact(payload)
    stable_key = _idempotency_key(str(payload["provider"]), str(payload["order_id"]))
    existing = (
        session.query(models.PaymentEntitlementOutbox)
        .filter_by(idempotency_key=stable_key)
        .one_or_none()
    )
    if existing is not None:
        if (
            str(existing.aggregate_id) != str(grant.id)
            or int(existing.schema_version or 0) != SCHEMA_VERSION
            or str(existing.event_type) != EVENT_TYPE
            or str(existing.payload_json) != payload_json
        ):
            raise PaymentEntitlementOutboxError("outbox_idempotency_conflict")
        return existing

    current_now = _naive_utc(now)
    row = models.PaymentEntitlementOutbox(
        id=str(uuid.uuid4()),
        idempotency_key=stable_key,
        aggregate_type="payment_entitlement",
        aggregate_id=str(grant.id),
        event_type=EVENT_TYPE,
        schema_version=SCHEMA_VERSION,
        payload_json=payload_json,
        status=STATUS_PENDING,
        attempts=0,
        next_run_at=current_now,
        created_at=current_now,
        updated_at=current_now,
    )
    session.add(row)
    session.flush()
    return row


def _validate_payload(row: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(row.payload_json or ""))
    except (TypeError, ValueError) as exc:
        raise PaymentEntitlementOutboxError("outbox_payload_invalid") from exc
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS:
        raise PaymentEntitlementOutboxError("outbox_payload_invalid")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("event_type") != EVENT_TYPE
    ):
        raise PaymentEntitlementOutboxError("outbox_schema_invalid")
    if str(payload.get("grant_id") or "") != str(row.aggregate_id or ""):
        raise PaymentEntitlementOutboxError("outbox_aggregate_mismatch")
    if not all(
        str(payload.get(key) or "").strip()
        for key in ("grant_id", "provider", "order_id")
    ):
        raise PaymentEntitlementOutboxError("outbox_payload_invalid")
    return payload


def dispatch_to_provisioning_queue(
    session: Session, payload: Mapping[str, Any], *, now: datetime
) -> None:
    try:
        from .node_provisioning_service import enqueue_payment_entitlement_sync
    except ImportError:
        from node_provisioning_service import enqueue_payment_entitlement_sync

    models = _models()
    grant = session.get(models.EntitlementGrant, str(payload["grant_id"]))
    if grant is None:
        raise PaymentEntitlementOutboxError("outbox_grant_missing")
    enqueue_payment_entitlement_sync(
        session,
        account_id=str(grant.account_id),
        entitlement_grant_id=str(payload["grant_id"]),
        provider=str(payload["provider"]),
        order_id=str(payload["order_id"]),
        now=_naive_utc(now),
    )


def _recover_stale(
    session_factory: Callable[[], Session],
    *,
    now: datetime,
    stale_after_seconds: int,
    max_attempts: int,
    limit: int,
) -> dict[str, int]:
    models = _models()
    recovered = 0
    dead_letter = 0
    cutoff = now - timedelta(seconds=max(1, int(stale_after_seconds)))
    with session_factory() as session:
        rows = (
            session.query(models.PaymentEntitlementOutbox)
            .filter(
                models.PaymentEntitlementOutbox.status == STATUS_PROCESSING,
                models.PaymentEntitlementOutbox.claimed_at <= cutoff,
            )
            .order_by(models.PaymentEntitlementOutbox.claimed_at.asc())
            .limit(max(1, int(limit)))
            .all()
        )
        for row in rows:
            if int(row.attempts or 0) >= max_attempts:
                row.status = STATUS_DEAD_LETTER
                row.terminal_reason = "stale_claim_max_attempts"
                dead_letter += 1
            else:
                row.status = STATUS_PENDING
                row.next_run_at = now
                recovered += 1
            row.claim_token = None
            row.claimed_at = None
            row.updated_at = now
        session.commit()
    return {"recovered": recovered, "dead_letter": dead_letter}


def backfill_payment_entitlement_outbox_once(
    session_factory: Callable[[], Session],
    *,
    now: datetime,
    limit: int,
) -> dict[str, int]:
    models = _models()
    bounded_limit = max(1, min(100, int(limit)))
    with session_factory() as session:
        grant_ids = [
            str(row[0])
            for row in (
                session.query(models.EntitlementGrant.id)
                .outerjoin(
                    models.PaymentEntitlementOutbox,
                    models.PaymentEntitlementOutbox.aggregate_id
                    == models.EntitlementGrant.id,
                )
                .filter(
                    models.EntitlementGrant.source == "provider_payment",
                    models.EntitlementGrant.status == "active",
                    models.EntitlementGrant.grant_kind == "paid_access",
                    models.EntitlementGrant.provider.isnot(None),
                    models.EntitlementGrant.external_order_id.isnot(None),
                    models.PaymentEntitlementOutbox.id.is_(None),
                )
                .order_by(models.EntitlementGrant.created_at.asc())
                .limit(bounded_limit)
                .all()
            )
        ]
    created = 0
    rejected = 0
    for grant_id in grant_ids:
        with session_factory() as session:
            grant = session.get(models.EntitlementGrant, grant_id)
            if grant is None:
                continue
            try:
                ensure_payment_entitlement_outbox(
                    session,
                    grant=grant,
                    provider=str(grant.provider or ""),
                    order_id=str(grant.external_order_id or ""),
                    now=now,
                )
                session.commit()
                created += 1
            except PaymentEntitlementOutboxError:
                session.rollback()
                rejected += 1
    return {"backfilled": created, "backfill_rejected": rejected}


def _claim_one(
    session_factory: Callable[[], Session], *, now: datetime
) -> OutboxClaim | None:
    models = _models()
    for _ in range(3):
        with session_factory() as session:
            candidate = (
                session.query(models.PaymentEntitlementOutbox.id)
                .filter(
                    models.PaymentEntitlementOutbox.status == STATUS_PENDING,
                    models.PaymentEntitlementOutbox.next_run_at <= now,
                )
                .order_by(
                    models.PaymentEntitlementOutbox.next_run_at.asc(),
                    models.PaymentEntitlementOutbox.id.asc(),
                )
                .first()
            )
            if candidate is None:
                return None
            row_id = str(candidate[0])
            token = uuid.uuid4().hex
            updated = (
                session.query(models.PaymentEntitlementOutbox)
                .filter(
                    models.PaymentEntitlementOutbox.id == row_id,
                    models.PaymentEntitlementOutbox.status == STATUS_PENDING,
                    models.PaymentEntitlementOutbox.next_run_at <= now,
                )
                .update(
                    {
                        models.PaymentEntitlementOutbox.status: STATUS_PROCESSING,
                        models.PaymentEntitlementOutbox.attempts: models.PaymentEntitlementOutbox.attempts
                        + 1,
                        models.PaymentEntitlementOutbox.claimed_at: now,
                        models.PaymentEntitlementOutbox.claim_token: token,
                        models.PaymentEntitlementOutbox.updated_at: now,
                    },
                    synchronize_session=False,
                )
            )
            session.commit()
            if updated == 1:
                row = session.get(models.PaymentEntitlementOutbox, row_id)
                return OutboxClaim(
                    row_id=row_id, token=token, attempts=int(row.attempts)
                )
    return None


def _finalize_failure(
    session_factory: Callable[[], Session],
    *,
    claim: OutboxClaim,
    now: datetime,
    error_code: str,
    max_attempts: int,
    terminal: bool,
) -> str:
    models = _models()
    with session_factory() as session:
        row = (
            session.query(models.PaymentEntitlementOutbox)
            .filter(
                models.PaymentEntitlementOutbox.id == claim.row_id,
                models.PaymentEntitlementOutbox.status == STATUS_PROCESSING,
                models.PaymentEntitlementOutbox.claim_token == claim.token,
            )
            .one_or_none()
        )
        if row is None:
            return "claim_lost"
        code = (
            str(error_code or "dispatch_failed").strip().lower()[:64]
            or "dispatch_failed"
        )
        row.last_error_code = code
        row.claim_token = None
        row.claimed_at = None
        row.updated_at = now
        if terminal or int(row.attempts or 0) >= max_attempts:
            row.status = STATUS_DEAD_LETTER
            row.terminal_reason = code
            outcome = STATUS_DEAD_LETTER
        else:
            row.status = STATUS_PENDING
            delay = min(3600, 2 ** min(12, max(1, int(row.attempts or 1))))
            row.next_run_at = now + timedelta(seconds=delay)
            outcome = "retryable"
        session.commit()
        return outcome


def _dispatch_one(
    session_factory: Callable[[], Session],
    *,
    claim: OutboxClaim,
    now: datetime,
    dispatcher: Callable[[Session, Mapping[str, Any]], None] | None,
) -> str:
    models = _models()
    with session_factory() as session:
        row = (
            session.query(models.PaymentEntitlementOutbox)
            .filter(
                models.PaymentEntitlementOutbox.id == claim.row_id,
                models.PaymentEntitlementOutbox.status == STATUS_PROCESSING,
                models.PaymentEntitlementOutbox.claim_token == claim.token,
            )
            .one_or_none()
        )
        if row is None:
            return "claim_lost"
        payload = _validate_payload(row)
        if dispatcher is None:
            dispatch_to_provisioning_queue(session, payload, now=now)
        else:
            dispatcher(session, payload)
        row.status = STATUS_DELIVERED
        row.delivered_at = now
        row.claimed_at = None
        row.claim_token = None
        row.last_error_code = None
        row.terminal_reason = None
        row.updated_at = now
        session.commit()
        return STATUS_DELIVERED


def run_payment_entitlement_outbox_once(
    session_factory: Callable[[], Session],
    *,
    now: datetime,
    batch_limit: int = 20,
    max_attempts: int = 5,
    stale_after_seconds: int = 300,
    dispatcher: Callable[[Session, Mapping[str, Any]], None] | None = None,
) -> dict[str, int]:
    current_now = _naive_utc(now)
    limit = max(1, min(100, int(batch_limit)))
    attempts_limit = max(1, min(20, int(max_attempts)))
    counters = {
        "backfilled": 0,
        "backfill_rejected": 0,
        "recovered": 0,
        "claimed": 0,
        "delivered": 0,
        "retryable": 0,
        "dead_letter": 0,
        "claim_lost": 0,
    }
    backfill = backfill_payment_entitlement_outbox_once(
        session_factory,
        now=current_now,
        limit=limit,
    )
    counters["backfilled"] += int(backfill["backfilled"])
    counters["backfill_rejected"] += int(backfill["backfill_rejected"])
    recovery = _recover_stale(
        session_factory,
        now=current_now,
        stale_after_seconds=stale_after_seconds,
        max_attempts=attempts_limit,
        limit=limit,
    )
    counters["recovered"] += int(recovery["recovered"])
    counters["dead_letter"] += int(recovery["dead_letter"])
    for _ in range(limit):
        claim = _claim_one(session_factory, now=current_now)
        if claim is None:
            break
        counters["claimed"] += 1
        try:
            outcome = _dispatch_one(
                session_factory,
                claim=claim,
                now=current_now,
                dispatcher=dispatcher,
            )
        except PaymentEntitlementOutboxError as exc:
            outcome = _finalize_failure(
                session_factory,
                claim=claim,
                now=current_now,
                error_code=exc.code,
                max_attempts=attempts_limit,
                terminal=True,
            )
        except Exception:
            outcome = _finalize_failure(
                session_factory,
                claim=claim,
                now=current_now,
                error_code="outbox_dispatch_failed",
                max_attempts=attempts_limit,
                terminal=False,
            )
        counters[outcome if outcome in counters else "claim_lost"] += 1
    return counters


def payment_entitlement_outbox_health(
    session: Session, *, now: datetime
) -> dict[str, int]:
    models = _models()
    current_now = _naive_utc(now)
    counts = {
        status: int(
            session.query(func.count(models.PaymentEntitlementOutbox.id))
            .filter(models.PaymentEntitlementOutbox.status == status)
            .scalar()
            or 0
        )
        for status in (
            STATUS_PENDING,
            STATUS_PROCESSING,
            STATUS_DELIVERED,
            STATUS_DEAD_LETTER,
        )
    }
    oldest = (
        session.query(func.min(models.PaymentEntitlementOutbox.created_at))
        .filter(
            models.PaymentEntitlementOutbox.status.in_(
                [STATUS_PENDING, STATUS_PROCESSING]
            )
        )
        .scalar()
    )
    counts["oldest_open_age_seconds"] = (
        max(0, int((current_now - oldest).total_seconds())) if oldest is not None else 0
    )
    return counts
