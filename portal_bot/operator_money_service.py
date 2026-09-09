"""Privacy-bounded payment, entitlement, promo and program read models."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_

try:
    from .admin_ops_service import free_tier_summary, free_tier_user_rows
    from .free_cycle_service import FREE_STANDARD_QUOTA_BYTES
    from .models import (
        AccessKey,
        AdminActionIntent,
        AppSetting,
        EntitlementGrant,
        ExternalOrder,
        ExternalPaymentEvent,
        GiftCard,
        PaymentEntitlementClaim,
        PaymentEntitlementOutbox,
        ProgramApplication,
        PromoCode,
        PromoUsage,
        User,
    )
    from .payment_entitlement_outbox import payment_entitlement_outbox_health
    from .shared_surface_facts import get_access_matrix, get_tariff_catalog
except ImportError:
    from admin_ops_service import free_tier_summary, free_tier_user_rows
    from free_cycle_service import FREE_STANDARD_QUOTA_BYTES
    from models import (
        AccessKey,
        AdminActionIntent,
        AppSetting,
        EntitlementGrant,
        ExternalOrder,
        ExternalPaymentEvent,
        GiftCard,
        PaymentEntitlementClaim,
        PaymentEntitlementOutbox,
        ProgramApplication,
        PromoCode,
        PromoUsage,
        User,
    )
    from payment_entitlement_outbox import payment_entitlement_outbox_health
    from shared_surface_facts import get_access_matrix, get_tariff_catalog


PAYMENT_PROBLEM_STATUSES = frozenset(
    {
        "created",
        "pending",
        "pending_verification",
        "manual_review",
        "failed",
        "cancelled",
        "refunded",
        "chargeback",
    }
)
FULFILLED_CLAIM_STATUSES = frozenset({"fulfilled", "reversed"})
PROGRAM_STATUSES = frozenset(
    {"submitted", "under_review", "approved", "rejected", "rewarded", "cancelled"}
)
PROGRAM_KINDS = frozenset({"competitor_switch", "research", "team_pack"})


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _opaque_ref(kind: str, *values: object) -> str:
    material = "\x1f".join(["pokrov-money-v1", kind, *(str(value or "") for value in values)])
    return f"{kind}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:20]}"


def _json_object(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _require_production(environment: str) -> None:
    if str(environment or "").strip().lower() != "production":
        raise LookupError("money_environment_unavailable")


def _period_bounds(period: str, *, now: datetime) -> tuple[str, datetime, datetime]:
    normalized = str(period or "7d").strip().lower()
    if normalized == "today":
        return "today", now.replace(hour=0, minute=0, second=0, microsecond=0), now
    if normalized == "30d":
        return "30d", now - timedelta(days=30), now
    return "7d", now - timedelta(days=7), now


def _event_view(row: ExternalPaymentEvent) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "event_ref": _opaque_ref("payment_event", row.provider, row.event_type, row.external_id),
        "provider": str(row.provider or "")[:32],
        "event_type": str(row.event_type or "")[:24],
        "external_id": _opaque_ref("provider_event", row.provider, row.external_id),
        "order_id": str(row.order_id or "")[:128] or None,
        "signature_ok": bool(row.signature_ok),
        "processed_ok": bool(row.processed_ok),
        "created_at": _iso(row.created_at),
    }


def _claim_for_order(session, order: ExternalOrder) -> PaymentEntitlementClaim | None:
    return (
        session.query(PaymentEntitlementClaim)
        .filter(
            PaymentEntitlementClaim.provider == str(order.provider or "").strip().lower(),
            PaymentEntitlementClaim.order_id == str(order.order_id or "").strip(),
        )
        .one_or_none()
    )


def _grant_for_claim(session, claim: PaymentEntitlementClaim | None) -> EntitlementGrant | None:
    if claim is None or not str(claim.grant_id or "").strip():
        return None
    return session.query(EntitlementGrant).filter(EntitlementGrant.id == str(claim.grant_id)).one_or_none()


def _outbox_for_claim(session, claim: PaymentEntitlementClaim | None) -> PaymentEntitlementOutbox | None:
    if claim is None:
        return None
    return (
        session.query(PaymentEntitlementOutbox)
        .filter(PaymentEntitlementOutbox.aggregate_id == str(claim.id))
        .order_by(PaymentEntitlementOutbox.created_at.desc())
        .first()
    )


def _claim_view(claim: PaymentEntitlementClaim | None) -> dict[str, Any] | None:
    if claim is None:
        return None
    return {
        "claim_ref": _opaque_ref("claim", claim.provider, claim.order_id),
        "status": str(claim.status or "")[:32],
        "plan_code": str(claim.plan_code or "")[:32],
        "duration_days": int(claim.duration_days or 0),
        "account_ref": _opaque_ref("account", claim.account_id) if claim.account_id else None,
        "grant_ref": _opaque_ref("grant", claim.grant_id) if claim.grant_id else None,
        "paid_at": _iso(claim.paid_at),
        "attached_at": _iso(claim.attached_at),
        "fulfilled_at": _iso(claim.fulfilled_at),
        "reversed_at": _iso(claim.reversed_at),
        "reversal_reason": str(claim.reversal_reason or "")[:64] or None,
        "last_error_present": bool(str(claim.last_error or "").strip()),
        "last_error_sha256": (
            hashlib.sha256(str(claim.last_error).encode("utf-8")).hexdigest()
            if str(claim.last_error or "").strip()
            else None
        ),
        "last_error_at": _iso(claim.last_error_at),
        "updated_at": _iso(claim.updated_at),
    }


def _grant_view(grant: EntitlementGrant | None) -> dict[str, Any] | None:
    if grant is None:
        return None
    return {
        "grant_ref": _opaque_ref("grant", grant.id),
        "account_ref": _opaque_ref("account", grant.account_id),
        "source": str(grant.source or "")[:40],
        "status": str(grant.status or "")[:24],
        "grant_kind": str(grant.grant_kind or "")[:32],
        "plan_code": str(grant.plan_code or "")[:32] or None,
        "starts_at": _iso(grant.starts_at),
        "expires_at": _iso(grant.expires_at),
        "activated_at": _iso(grant.activated_at),
        "reversed_at": _iso(grant.reversed_at),
        "reversal_reason": str(grant.reversal_reason or "")[:64] or None,
        "provider": str(grant.provider or "")[:32] or None,
        "order_ref": (
            _opaque_ref("order", grant.provider, grant.external_order_id)
            if grant.external_order_id
            else None
        ),
        "created_at": _iso(grant.created_at),
        "updated_at": _iso(grant.updated_at),
    }


def _outbox_view(row: PaymentEntitlementOutbox | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "outbox_ref": _opaque_ref("outbox", row.id),
        "status": str(row.status or "")[:24],
        "attempts": int(row.attempts or 0),
        "last_error_code": str(row.last_error_code or "")[:64] or None,
        "terminal_reason": str(row.terminal_reason or "")[:64] or None,
        "next_run_at": _iso(row.next_run_at),
        "delivered_at": _iso(row.delivered_at),
        "updated_at": _iso(row.updated_at),
    }


def _payment_events(session, order: ExternalOrder, *, limit: int = 50) -> list[ExternalPaymentEvent]:
    return (
        session.query(ExternalPaymentEvent)
        .filter(
            ExternalPaymentEvent.provider == str(order.provider or ""),
            ExternalPaymentEvent.order_id == str(order.order_id or ""),
        )
        .order_by(ExternalPaymentEvent.created_at.desc(), ExternalPaymentEvent.id.desc())
        .limit(max(1, min(int(limit), 100)))
        .all()
    )


def payment_problem_reasons(
    order: ExternalOrder,
    *,
    events: list[ExternalPaymentEvent],
    claim: PaymentEntitlementClaim | None,
    now: datetime,
) -> list[str]:
    status = str(order.status or "created").strip().lower()
    reasons: list[str] = []
    if status in {"created", "pending", "pending_verification"} and order.created_at:
        if order.created_at <= now - timedelta(minutes=30):
            reasons.append("pending_too_long")
    if status == "manual_review":
        reasons.append("manual_review")
    if status in {"failed", "cancelled"}:
        reasons.append("payment_failed")
    if status in {"refunded", "chargeback"}:
        reasons.append("refund_or_reversal")
    if any(not bool(event.signature_ok) for event in events):
        reasons.append("signature_failed")
    if events and any(not bool(event.processed_ok) for event in events):
        reasons.append("callback_failed")
    if status == "paid" and (claim is None or str(claim.status or "") not in FULFILLED_CLAIM_STATUSES):
        reasons.append("paid_without_entitlement")
    if claim is not None and str(claim.status or "") == "manual_review":
        reasons.append("entitlement_manual_review")
    return list(dict.fromkeys(reasons))


def payment_order_view(session, order: ExternalOrder, *, now: datetime | None = None) -> dict[str, Any]:
    current = now or _now()
    events = _payment_events(session, order)
    claim = _claim_for_order(session, order)
    grant = _grant_for_claim(session, claim)
    outbox = _outbox_for_claim(session, claim)
    user = None
    if order.tg_id is not None:
        user = session.query(User).filter(User.tg_id == int(order.tg_id)).one_or_none()
    account_id = str(getattr(user, "account_id", "") or getattr(claim, "account_id", "") or "")
    return {
        "id": int(order.id),
        "order_id": str(order.order_id or "")[:128],
        "order_ref": _opaque_ref("order", order.provider, order.order_id),
        "provider": str(order.provider or "")[:32],
        "tg_id": int(order.tg_id) if order.tg_id is not None else None,
        "account_ref": _opaque_ref("account", account_id) if account_id else None,
        "user": (
            {
                "tg_id": int(user.tg_id),
                "username": str(user.username or "")[:100] or None,
                "display_name": str(getattr(user, "display_name", "") or "")[:160] or None,
                "status": str(getattr(user, "sub_type", "") or "unknown")[:24].lower(),
            }
            if user is not None
            else None
        ),
        "plan_code": str(order.plan_code or "")[:32] or None,
        "amount": float(order.amount or 0.0),
        "currency": str(order.currency or "RUB")[:16],
        "status": str(order.status or "created")[:24],
        "source": str(order.source or "")[:32] or None,
        "campaign": str(order.campaign or "")[:64] or None,
        "promo_code": str(order.promo_code or "")[:32] or None,
        "created_at": _iso(order.created_at),
        "paid_at": _iso(order.paid_at),
        "event_count": len(events),
        "last_event": _event_view(events[0]) if events else None,
        "problem_reasons": payment_problem_reasons(order, events=events, claim=claim, now=current),
        "lineage": {
            "claim": _claim_view(claim),
            "grant": _grant_view(grant),
            "outbox": _outbox_view(outbox),
        },
    }


def _order_quote_view(order: ExternalOrder) -> dict[str, Any] | None:
    intent = _json_object(order.meta_json).get("order_intent")
    if not isinstance(intent, dict) or intent.get("schema") not in {
        "pokrov-payment-order-intent-v1", "pokrov-payment-order-intent-v2"
    }:
        return None
    offer = intent.get("commercial_offer")
    commercial = offer if isinstance(offer, dict) else {}
    # Only immutable commercial terms; owner, subject, token and provider data stay private.
    def field(source: dict[str, Any], key: str, limit: int) -> str | None:
        value = source.get(key)
        return str(value)[:limit] if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None
    return {
        "source": "stored_order_intent",
        "plan_code": field(intent, "plan_code", 32),
        "amount": field(intent, "amount", 32),
        "currency": field(intent, "currency", 16),
        "campaign": field(commercial, "campaign", 64),
        "campaign_revision": field(commercial, "campaign_revision", 20),
        "commercial_revision": field(commercial, "commercial_revision", 64),
        "terms_revision": field(commercial, "terms_revision", 64),
        "base_amount_rub": field(commercial, "base_amount_rub", 32),
        "hold_expires_at": field(commercial, "hold_expires_at", 32),
    }


def payment_summary(session, *, environment: str, period: str, now: datetime | None = None) -> dict[str, Any]:
    _require_production(environment)
    current = now or _now()
    label, from_dt, to_dt = _period_bounds(period, now=current)
    paid_time = func.coalesce(ExternalOrder.paid_at, ExternalOrder.created_at)
    revenue_rows = (
        session.query(
            ExternalOrder.currency,
            func.count(ExternalOrder.id),
            func.sum(func.coalesce(ExternalOrder.amount, 0.0)),
        )
        .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
        .filter(paid_time >= from_dt, paid_time <= to_dt)
        .group_by(ExternalOrder.currency)
        .all()
    )
    by_currency = [
        {
            "currency": str(currency or "RUB")[:16],
            "paid_count": int(count or 0),
            "revenue": round(float(amount or 0.0), 2),
        }
        for currency, count, amount in revenue_rows
    ]
    primary = next((row for row in by_currency if row["currency"].upper() == "RUB"), None)
    primary = primary or (by_currency[0] if by_currency else {"currency": "RUB", "paid_count": 0, "revenue": 0.0})
    status_counts = {
        str(status or "created"): int(count or 0)
        for status, count in (
            session.query(ExternalOrder.status, func.count(ExternalOrder.id))
            .filter(ExternalOrder.created_at >= from_dt, ExternalOrder.created_at <= to_dt)
            .group_by(ExternalOrder.status)
            .all()
        )
    }
    candidates = (
        session.query(ExternalOrder)
        .filter(ExternalOrder.created_at >= from_dt, ExternalOrder.created_at <= to_dt)
        .filter(
            or_(
                func.lower(func.coalesce(ExternalOrder.status, "")).in_(sorted(PAYMENT_PROBLEM_STATUSES)),
                func.lower(func.coalesce(ExternalOrder.status, "")) == "paid",
            )
        )
        .order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc())
        .limit(100)
        .all()
    )
    viewed = [payment_order_view(session, row, now=current) for row in candidates]
    problems = [row for row in viewed if row["problem_reasons"]][:25]
    reason_counts: dict[str, int] = {}
    for row in viewed:
        for reason in row["problem_reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    attention = {
        "pending_count": sum(reason_counts.get(code, 0) for code in ("pending_too_long",)),
        "manual_review_count": sum(
            reason_counts.get(code, 0) for code in ("manual_review", "entitlement_manual_review")
        ),
        "failed_count": sum(
            reason_counts.get(code, 0)
            for code in ("payment_failed", "callback_failed", "signature_failed", "refund_or_reversal")
        ),
        "problem_count": len(problems),
    }
    return {
        "generated_at": _iso(current),
        "period": {"key": label, "from": _iso(from_dt), "to": _iso(to_dt)},
        "revenue": {
            "currency": primary["currency"],
            "paid_count": int(primary["paid_count"]),
            "amount": float(primary["revenue"]),
            "by_currency": by_currency,
        },
        "status_counts": status_counts,
        "attention": attention,
        "mismatch_queues": reason_counts,
        "abandoned": {
            "buy_clicks": None,
            "checkout_started": None,
            "paid": int(primary["paid_count"]),
            "buy_click_not_paid": None,
            "checkout_not_paid": None,
            "note": "Telemetry is diagnostic only; signed callbacks and entitlement records own payment truth.",
        },
        "problem_orders": problems,
    }


def payment_orders(
    session,
    *,
    environment: str,
    status: str = "",
    provider: str = "",
    query_text: str = "",
    limit: int = 100,
    offset: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    _require_production(environment)
    query = session.query(ExternalOrder)
    normalized_status = str(status or "").strip().lower()
    normalized_provider = str(provider or "").strip().lower()
    normalized_query = str(query_text or "").strip()
    if normalized_status:
        query = query.filter(func.lower(func.coalesce(ExternalOrder.status, "")) == normalized_status)
    if normalized_provider:
        query = query.filter(func.lower(func.coalesce(ExternalOrder.provider, "")) == normalized_provider)
    if normalized_query:
        filters = [
            ExternalOrder.order_id.ilike(f"%{normalized_query}%"),
            ExternalOrder.provider.ilike(f"%{normalized_query}%"),
            ExternalOrder.plan_code.ilike(f"%{normalized_query}%"),
        ]
        if normalized_query.isdigit():
            filters.append(ExternalOrder.tg_id == int(normalized_query))
        query = query.filter(or_(*filters))
    bounded_limit = max(1, min(int(limit), 250))
    bounded_offset = max(0, int(offset))
    total = int(query.count() or 0)
    rows = (
        query.order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc())
        .offset(bounded_offset)
        .limit(bounded_limit)
        .all()
    )
    return {
        "orders": [payment_order_view(session, row, now=now) for row in rows],
        "total": total,
        "limit": bounded_limit,
        "offset": bounded_offset,
    }


def payment_360(
    session,
    *,
    environment: str,
    provider: str,
    order_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    _require_production(environment)
    order = (
        session.query(ExternalOrder)
        .filter(
            func.lower(ExternalOrder.provider) == str(provider or "").strip().lower(),
            ExternalOrder.order_id == str(order_id or "").strip(),
        )
        .one_or_none()
    )
    if order is None:
        return None
    result = payment_order_view(session, order, now=now)
    result["quote"] = _order_quote_view(order)
    result["events"] = [_event_view(row) for row in _payment_events(session, order)]
    result["commands"] = [
        {
            "intent_ref": _opaque_ref("intent", row.id),
            "action": str(row.action or "")[:64],
            "status": str(row.status or "")[:24],
            "created_at": _iso(row.created_at),
            "consumed_at": _iso(row.consumed_at),
        }
        for row in (
            session.query(AdminActionIntent)
            .filter(
                AdminActionIntent.target_type == "payment",
                AdminActionIntent.target_id == str(order.id),
            )
            .order_by(AdminActionIntent.created_at.desc())
            .limit(25)
            .all()
        )
    ]
    return result


def _gift_code_view(row: GiftCard) -> dict[str, Any]:
    code = str(row.code or "")
    return {
        "gift_ref": _opaque_ref("gift", row.id, code),
        "code_hint": f"{code[:3]}…{code[-3:]}" if len(code) > 7 else "issued",
        "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest() if code else None,
        "card_type": str(row.card_type or "")[:20],
        "redeemed": row.redeemed_at is not None,
        "created_at": _iso(row.created_at),
        "redeemed_at": _iso(row.redeemed_at),
    }


def access_overview(session, *, environment: str, now: datetime | None = None) -> dict[str, Any]:
    _require_production(environment)
    current = now or _now()
    grant_counts = {
        f"{str(status or 'unknown')}:{str(kind or 'unknown')}": int(count or 0)
        for status, kind, count in (
            session.query(EntitlementGrant.status, EntitlementGrant.grant_kind, func.count(EntitlementGrant.id))
            .group_by(EntitlementGrant.status, EntitlementGrant.grant_kind)
            .all()
        )
    }
    claim_counts = {
        str(status or "unknown"): int(count or 0)
        for status, count in (
            session.query(PaymentEntitlementClaim.status, func.count(PaymentEntitlementClaim.id))
            .group_by(PaymentEntitlementClaim.status)
            .all()
        )
    }
    key_counts = {
        f"{str(state or 'unknown')}:{str(source or 'unknown')}": int(count or 0)
        for state, source, count in (
            session.query(AccessKey.state, AccessKey.source, func.count(AccessKey.id))
            .group_by(AccessKey.state, AccessKey.source)
            .all()
        )
    }
    recent_grants = (
        session.query(EntitlementGrant)
        .order_by(EntitlementGrant.created_at.desc(), EntitlementGrant.id.desc())
        .limit(100)
        .all()
    )
    gifts = session.query(GiftCard).order_by(GiftCard.created_at.desc(), GiftCard.id.desc()).limit(100).all()
    tariff = get_tariff_catalog()
    return {
        "generated_at": _iso(current),
        "authority": {
            "payments": "signed_callback_plus_external_orders",
            "entitlements": "account_entitlement_grants",
            "provisioning": "payment_entitlement_outbox",
            "telemetry_confirms_payment": False,
        },
        "claim_counts": claim_counts,
        "grant_counts": grant_counts,
        "outbox": payment_entitlement_outbox_health(session, now=current),
        "access_key_counts": key_counts,
        "recent_grants": [_grant_view(row) for row in recent_grants],
        "gift_codes": [_gift_code_view(row) for row in gifts],
        "plans": [
            {
                "code": str(row.get("code") or "")[:32],
                "label": str(row.get("label") or "")[:80],
                "duration_days": int(row.get("duration_days") or 0),
                "device_limit": int(row.get("device_limit") or 0),
                "is_public": bool(row.get("is_public", True)),
            }
            for row in list(tariff.get("plans") or [])
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        ],
    }


def free_archive(
    session,
    *,
    environment: str,
    query_text: str = "",
    limit: int = 500,
    offset: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    _require_production(environment)
    current = now or _now()
    matrix = get_access_matrix()
    facts = dict(matrix.get("free_tier") or {})
    limit_gb = int(FREE_STANDARD_QUOTA_BYTES // (1024**3))
    cycle_days = int(facts.get("cycle_days") or 30)
    rows, total = free_tier_user_rows(
        s=session,
        now=current,
        free_limit_gb=limit_gb,
        cycle_days=cycle_days,
        limit=max(1, min(int(limit), 1000)),
        offset=max(0, int(offset)),
        q=query_text,
    )
    summary = free_tier_summary(
        s=session,
        now=current,
        free_limit_gb=limit_gb,
        cycle_days=cycle_days,
    )
    return {
        "generated_at": _iso(current),
        "summary": summary,
        "facts": {
            "enabled": bool(facts.get("enabled", False)),
            "status": str(facts.get("status") or "retired_pending_replacement")[:48],
            "node_pool": str(facts.get("location_code") or "")[:32] or None,
            "traffic_limit_gb": limit_gb,
            "cycle_days": cycle_days,
            "speed_limit_mbps": int(facts.get("speed_limit_mbps") or 50),
            "soft_mode_speed_limit_mbps": int(facts.get("soft_mode_speed_limit_mbps") or 2),
            "device_limit": int(facts.get("device_limit") or 1),
            "source": "shared_access_matrix",
        },
        "users": rows,
        "total": int(total or 0),
    }


def promo_rows(session, *, environment: str, limit: int = 200) -> list[dict[str, Any]]:
    _require_production(environment)
    usage = {
        str(code or "").upper(): int(count or 0)
        for code, count in (
            session.query(PromoUsage.promo_code, func.count(PromoUsage.id))
            .group_by(PromoUsage.promo_code)
            .all()
        )
    }
    rows = session.query(PromoCode).order_by(PromoCode.created_at.desc(), PromoCode.id.desc()).limit(max(1, min(int(limit), 500))).all()
    return [
        {
            "code": str(row.code or "").upper()[:20],
            "promo_type": str(row.promo_type or "")[:10],
            "value": int(row.value or 0),
            "uses_left": int(row.uses_left or 0),
            "used_count": usage.get(str(row.code or "").upper(), 0),
            "expires_at": _iso(row.expires_at),
            "created_at": _iso(row.created_at),
        }
        for row in rows
    ]


def bonus_configuration(session, *, environment: str) -> dict[str, Any]:
    _require_production(environment)

    def setting(key: str) -> dict[str, Any]:
        row = session.query(AppSetting).filter(AppSetting.key == key).one_or_none()
        return _json_object(row.value_json) if row is not None else {}

    wheel = setting("wheel_config")
    loyalty = setting("loyalty_config")
    weights = wheel.get("weights") if isinstance(wheel.get("weights"), list) else []
    tiers = loyalty.get("tiers") if isinstance(loyalty.get("tiers"), list) else []
    return {
        "wheel": {
            "preset": str(wheel.get("preset") or "paid_fortnightly_v3")[:48],
            "cooldown_hours": max(1, min(int(wheel.get("cooldown_hours") or 336), 2160)),
            "weights": [
                {
                    "kind": str(row.get("kind") or "days")[:24],
                    "value": int(row.get("value") or row.get("days") or 0),
                    "weight": int(row.get("weight") or 0),
                }
                for row in weights
                if isinstance(row, dict)
            ],
        },
        "loyalty": {
            "enabled": bool(loyalty.get("enabled", True)),
            "tiers": [
                {
                    "days": int(row.get("days") or 0),
                    "bonus_days": int(row.get("bonus_days") or 0),
                    "perk": str(row.get("perk") or "")[:64],
                }
                for row in tiers
                if isinstance(row, dict)
            ],
        },
    }


def program_view(row: ProgramApplication) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "account_ref": _opaque_ref("account", row.account_id),
        "kind": str(row.kind or "")[:32],
        "status": str(row.status or "")[:24],
        "source_name": str(row.source_name or "")[:100] or None,
        "seats": int(row.seats) if row.seats is not None else None,
        "summary": str(row.summary or "")[:2000],
        "contact": str(row.contact or "")[:160] or None,
        "operator_note": str(row.operator_note or "")[:1000] or None,
        "reward_days": int(row.reward_days or 0),
        "rewarded": bool(row.reward_grant_id),
        "reward_grant_ref": _opaque_ref("grant", row.reward_grant_id) if row.reward_grant_id else None,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
        "reviewed_at": _iso(row.reviewed_at),
    }


def program_applications(
    session,
    *,
    environment: str,
    status: str = "",
    kind: str = "",
    limit: int = 200,
) -> list[dict[str, Any]]:
    _require_production(environment)
    query = session.query(ProgramApplication)
    normalized_status = str(status or "").strip().lower()
    normalized_kind = str(kind or "").strip().lower()
    if normalized_status:
        if normalized_status not in PROGRAM_STATUSES:
            raise ValueError("program_status_invalid")
        query = query.filter(ProgramApplication.status == normalized_status)
    if normalized_kind:
        if normalized_kind not in PROGRAM_KINDS:
            raise ValueError("program_kind_invalid")
        query = query.filter(ProgramApplication.kind == normalized_kind)
    rows = query.order_by(ProgramApplication.created_at.desc()).limit(max(1, min(int(limit), 300))).all()
    return [program_view(row) for row in rows]


__all__ = [
    "access_overview",
    "bonus_configuration",
    "free_archive",
    "payment_360",
    "payment_order_view",
    "payment_orders",
    "payment_problem_reasons",
    "payment_summary",
    "program_applications",
    "program_view",
    "promo_rows",
]
