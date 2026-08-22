"""Application boundary for immutable local payment orders.

The local order is the authority for fulfillment. Provider responses may move
checkout state forward, but they must never redefine the purchased entitlement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Callable, Mapping

from sqlalchemy.orm import Session


_MONEY_QUANTUM = Decimal("0.01")
_INTENT_SCHEMA = "pokrov-payment-order-intent-v1"
_COMMERCIAL_INTENT_SCHEMA = "pokrov-payment-order-intent-v2"
_COMMERCIAL_LINEAGE_SCHEMA = "pokrov-commercial-order-lineage-v2"
_COMMERCIAL_LINEAGE_FIELDS = {
    "schema",
    "campaign",
    "campaign_revision",
    "commercial_revision",
    "terms_revision",
    "offer",
    "creative",
    "variant",
    "assignment",
    "reservation",
    "impression",
    "click",
    "subject",
    "base_amount_rub",
    "final_amount_rub",
    "currency",
    "issued_at",
    "hold_expires_at",
    "offer_ends_at",
    "token_sha256",
}
_CHECKOUT_SCHEMA = "pokrov-provider-checkout-v1"
_REMOTE_SAFE_FIELDS = {
    "id": "id",
    "orderid": "order_id",
    "order_id": "order_id",
    "invoiceid": "invoice_id",
    "invoice_id": "invoice_id",
    "status": "status",
    "state": "state",
}


class PaymentOrderIntentError(RuntimeError):
    """Raised when an existing local order does not match its original intent."""


def _external_order_model() -> type[Any]:
    # Isolated API tests reload the model module between runtimes. Resolve the
    # mapped class at the transaction boundary instead of retaining a stale one.
    try:
        from .models import ExternalOrder
    except ImportError:
        from models import ExternalOrder

    return ExternalOrder


def _money(value: Any) -> str:
    try:
        amount = Decimal(str(value)).quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PaymentOrderIntentError("invalid_order_amount") from exc
    if not amount.is_finite() or amount < 0:
        raise PaymentOrderIntentError("invalid_order_amount")
    return format(amount, ".2f")


def _text(value: Any, *, limit: int, lower: bool = False, upper: bool = False) -> str:
    normalized = str(value or "").strip()[:limit]
    if lower:
        normalized = normalized.lower()
    if upper:
        normalized = normalized.upper()
    return normalized


def _canonical_entitlement(value: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = {
        "plan_code": _text(value.get("plan_code"), limit=32, lower=True),
        "duration_days": max(1, int(value.get("duration_days") or 0)),
        "amount_rub": _money(value.get("amount_rub")),
        "currency": _text(value.get("currency"), limit=16, upper=True),
        "source": _text(value.get("source"), limit=32, lower=True),
    }
    if not all((snapshot["plan_code"], snapshot["currency"], snapshot["source"])):
        raise PaymentOrderIntentError("invalid_entitlement_snapshot")
    return snapshot


def _canonical_commercial_lineage(value: Mapping[str, Any]) -> dict[str, Any]:
    if set(value) != _COMMERCIAL_LINEAGE_FIELDS:
        raise PaymentOrderIntentError("invalid_commercial_lineage")
    try:
        campaign_revision = int(value.get("campaign_revision"))
        base_amount = int(value.get("base_amount_rub"))
        final_amount = int(value.get("final_amount_rub"))
        issued_at = int(value.get("issued_at"))
        hold_expires_at = int(value.get("hold_expires_at"))
        offer_ends_at = int(value.get("offer_ends_at"))
    except (TypeError, ValueError) as exc:
        raise PaymentOrderIntentError("invalid_commercial_lineage") from exc
    snapshot = {
        "schema": _text(value.get("schema"), limit=64),
        "campaign": _text(value.get("campaign"), limit=36, lower=True),
        "campaign_revision": campaign_revision,
        "commercial_revision": _text(value.get("commercial_revision"), limit=32),
        "terms_revision": _text(value.get("terms_revision"), limit=64),
        "offer": _text(value.get("offer"), limit=36, lower=True),
        "creative": _text(value.get("creative"), limit=36, lower=True),
        "variant": _text(value.get("variant"), limit=32),
        "assignment": _text(value.get("assignment"), limit=36, lower=True),
        "reservation": _text(value.get("reservation"), limit=36, lower=True),
        "impression": _text(value.get("impression"), limit=36, lower=True),
        "click": _text(value.get("click"), limit=36, lower=True),
        "subject": _text(value.get("subject"), limit=64, lower=True),
        "base_amount_rub": base_amount,
        "final_amount_rub": final_amount,
        "currency": _text(value.get("currency"), limit=16, upper=True),
        "issued_at": issued_at,
        "hold_expires_at": hold_expires_at,
        "offer_ends_at": offer_ends_at,
        "token_sha256": _text(value.get("token_sha256"), limit=64, lower=True),
    }
    required_text = (
        "campaign",
        "commercial_revision",
        "terms_revision",
        "offer",
        "creative",
        "variant",
        "assignment",
        "reservation",
        "impression",
        "click",
        "subject",
        "currency",
        "token_sha256",
    )
    if (
        snapshot["schema"] != _COMMERCIAL_LINEAGE_SCHEMA
        or any(not snapshot[field] for field in required_text)
        or campaign_revision <= 0
        or base_amount <= 0
        or final_amount <= 0
        or final_amount >= base_amount
        or issued_at <= 0
        or hold_expires_at <= issued_at
        or hold_expires_at > offer_ends_at
        or len(snapshot["subject"]) != 64
        or len(snapshot["token_sha256"]) != 64
        or not snapshot["impression"].startswith("imp_")
        or not snapshot["click"].startswith("clk_")
    ):
        raise PaymentOrderIntentError("invalid_commercial_lineage")
    return snapshot


def _owner(*, tg_id: int | None, buyer_email: str | None) -> dict[str, Any]:
    if tg_id is not None and int(tg_id) > 0:
        return {"kind": "telegram", "tg_id": int(tg_id)}
    email = _text(buyer_email, limit=320, lower=True)
    if not email:
        raise PaymentOrderIntentError("missing_order_owner")
    return {
        "kind": "email",
        "email_sha256": hashlib.sha256(email.encode("utf-8")).hexdigest(),
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True)
class PaymentOrderIntent:
    order_id: str
    provider: str
    tg_id: int | None
    plan_code: str
    source: str
    amount: str
    currency: str
    owner: Mapping[str, Any]
    entitlement_snapshot: Mapping[str, Any]
    commercial_offer: Mapping[str, Any] | None = None

    def payload(self) -> dict[str, Any]:
        authority = {
            "schema": _COMMERCIAL_INTENT_SCHEMA if self.commercial_offer is not None else _INTENT_SCHEMA,
            "order_id": self.order_id,
            "provider": self.provider,
            "tg_id": self.tg_id,
            "plan_code": self.plan_code,
            "source": self.source,
            "amount": self.amount,
            "currency": self.currency,
            "owner": dict(self.owner),
            "entitlement_snapshot": dict(self.entitlement_snapshot),
        }
        if self.commercial_offer is not None:
            authority["commercial_offer"] = dict(self.commercial_offer)
        authority["sha256"] = hashlib.sha256(
            _canonical_json(authority).encode("utf-8")
        ).hexdigest()
        return authority


def build_payment_order_intent(
    *,
    order_id: str,
    provider: str,
    tg_id: int | None,
    buyer_email: str | None,
    plan_code: str,
    source: str,
    amount: Any,
    currency: str,
    entitlement_snapshot: Mapping[str, Any],
    commercial_offer: Mapping[str, Any] | None = None,
) -> PaymentOrderIntent:
    normalized = PaymentOrderIntent(
        order_id=_text(order_id, limit=128),
        provider=_text(provider, limit=32, lower=True),
        tg_id=int(tg_id) if tg_id is not None and int(tg_id) > 0 else None,
        plan_code=_text(plan_code, limit=32, lower=True),
        source=_text(source, limit=32, lower=True),
        amount=_money(amount),
        currency=_text(currency, limit=16, upper=True),
        owner=_owner(tg_id=tg_id, buyer_email=buyer_email),
        entitlement_snapshot=_canonical_entitlement(entitlement_snapshot),
        commercial_offer=(
            _canonical_commercial_lineage(commercial_offer)
            if commercial_offer is not None
            else None
        ),
    )
    if not all(
        (
            normalized.order_id,
            normalized.provider,
            normalized.plan_code,
            normalized.source,
            normalized.currency,
        )
    ):
        raise PaymentOrderIntentError("invalid_order_intent")
    if dict(normalized.entitlement_snapshot) != {
        "plan_code": normalized.plan_code,
        "duration_days": int(normalized.entitlement_snapshot["duration_days"]),
        "amount_rub": normalized.amount,
        "currency": normalized.currency,
        "source": normalized.source,
    }:
        raise PaymentOrderIntentError("entitlement_snapshot_mismatch")
    if normalized.commercial_offer is not None:
        commercial_amount = _money(normalized.commercial_offer["final_amount_rub"])
        if (
            commercial_amount != normalized.amount
            or str(normalized.commercial_offer["currency"]) != normalized.currency
        ):
            raise PaymentOrderIntentError("commercial_lineage_price_mismatch")
    return normalized


def _row_meta(row: Any) -> dict[str, Any]:
    try:
        value = json.loads(str(row.meta_json or "{}"))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def assert_order_matches_intent(row: Any, intent: PaymentOrderIntent) -> None:
    scalar_actual = {
        "order_id": _text(row.order_id, limit=128),
        "provider": _text(row.provider, limit=32, lower=True),
        "tg_id": int(row.tg_id) if row.tg_id is not None else None,
        "plan_code": _text(row.plan_code, limit=32, lower=True),
        "source": _text(row.source, limit=32, lower=True),
        "amount": _money(row.amount),
        "currency": _text(row.currency, limit=16, upper=True),
    }
    scalar_expected = {
        "order_id": intent.order_id,
        "provider": intent.provider,
        "tg_id": intent.tg_id,
        "plan_code": intent.plan_code,
        "source": intent.source,
        "amount": intent.amount,
        "currency": intent.currency,
    }
    stored_intent = _row_meta(row).get("order_intent")
    if scalar_actual != scalar_expected or stored_intent != intent.payload():
        raise PaymentOrderIntentError("order_intent_conflict")


def persist_local_order_intent(
    session: Session,
    *,
    intent: PaymentOrderIntent,
    metadata: Mapping[str, Any],
    serialize_meta: Callable[[dict[str, Any]], str],
    created_at: datetime,
    campaign: str | None = None,
    acquisition_session_id: str | None = None,
    promo_code: str | None = None,
) -> tuple[Any, bool]:
    external_order = _external_order_model()
    row = (
        session.query(external_order)
        .filter(
            external_order.provider == intent.provider,
            external_order.order_id == intent.order_id,
        )
        .first()
    )
    if row is not None:
        assert_order_matches_intent(row, intent)
        return row, False

    prepared_meta = dict(metadata)
    prepared_meta["order_intent"] = intent.payload()
    row = external_order(
        order_id=intent.order_id,
        tg_id=intent.tg_id,
        provider=intent.provider,
        plan_code=intent.plan_code,
        source=intent.source,
        campaign=_text(campaign, limit=64) or None,
        acquisition_session_id=_text(acquisition_session_id, limit=36) or None,
        promo_code=_text(promo_code, limit=32, upper=True) or None,
        meta_json=serialize_meta(prepared_meta),
        amount=float(Decimal(intent.amount)),
        currency=intent.currency,
        status="created",
        created_at=created_at,
    )
    session.add(row)
    return row, True


def _safe_remote_fields(remote: Mapping[str, Any] | None) -> dict[str, str]:
    safe: dict[str, str] = {}
    for raw_key, raw_value in dict(remote or {}).items():
        key = _REMOTE_SAFE_FIELDS.get(str(raw_key).strip().lower())
        if not key or isinstance(raw_value, (dict, list, tuple, set)):
            continue
        value = _text(raw_value, limit=128)
        if value:
            safe[key] = value
    return safe


def record_provider_checkout(
    row: Any,
    *,
    intent: PaymentOrderIntent,
    payment_url: str,
    remote_response: Mapping[str, Any] | None,
    metadata_update: Mapping[str, Any],
    serialize_meta: Callable[[dict[str, Any]], str],
) -> None:
    assert_order_matches_intent(row, intent)
    if not _text(payment_url, limit=4096):
        raise PaymentOrderIntentError("missing_payment_url")
    meta = _row_meta(row)
    meta.update(dict(metadata_update))
    meta["provider_checkout"] = {
        "schema": _CHECKOUT_SCHEMA,
        "status": "ready",
        "url_present": True,
        "remote": _safe_remote_fields(remote_response),
    }
    row.meta_json = serialize_meta(meta)
    if str(row.status or "").strip().lower() in {"created", "failed"}:
        row.status = "pending"


def record_provider_checkout_failure(
    row: Any,
    *,
    intent: PaymentOrderIntent,
    error_code: str,
    serialize_meta: Callable[[dict[str, Any]], str],
) -> None:
    assert_order_matches_intent(row, intent)
    meta = _row_meta(row)
    meta["provider_checkout"] = {
        "schema": _CHECKOUT_SCHEMA,
        "status": "error",
        "error_code": _text(error_code, limit=64, lower=True) or "provider_error",
        "url_present": False,
    }
    row.meta_json = serialize_meta(meta)
