"""Identity-free consumer payment-return state.

The signed token is read-only capability material. It can reveal only the
closed consumer state of one exact local order; it cannot mutate payment or
entitlement state and is never accepted by fulfillment paths.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


PAYMENT_RETURN_TOKEN_SCHEMA = "pokrov-payment-return-token-v1"
PAYMENT_RETURN_TOKEN_VERSION = 1
PAYMENT_RETURN_TOKEN_PREFIX = "prt1"
PAYMENT_RETURN_SURFACES = frozenset({"marketing", "cabinet"})
PAYMENT_RETURN_STATES = frozenset(
    {"processing", "paid", "failed", "cancelled", "manual_review", "expired"}
)


class PaymentReturnTokenError(RuntimeError):
    """Raised for malformed, untrusted or unavailable return tokens."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except Exception as exc:
        raise PaymentReturnTokenError("payment_return_token_malformed") from exc


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _secret(secret: str | bytes | None = None) -> bytes:
    if isinstance(secret, bytes):
        resolved = secret
    else:
        resolved = str(
            secret
            or os.getenv("PAYMENT_RETURN_HMAC_SECRET")
            or os.getenv("CHECKOUT_TICKET_SECRET")
            or os.getenv("WEBAPP_SESSION_SECRET")
            or ""
        ).encode("utf-8")
    if not resolved:
        raise PaymentReturnTokenError("payment_return_signing_unavailable")
    return resolved


def payment_return_signing_ready(*, secret: str | bytes | None = None) -> bool:
    try:
        _secret(secret)
    except PaymentReturnTokenError:
        return False
    return True


def issue_payment_return_token(
    *,
    provider: str,
    order_id: str,
    surface: str,
    secret: str | bytes | None = None,
    now: datetime | None = None,
    ttl_seconds: int | None = None,
) -> str:
    current = _as_utc(now or _utcnow())
    normalized_provider = str(provider or "").strip().lower()[:32]
    normalized_order = str(order_id or "").strip()[:128]
    normalized_surface = str(surface or "").strip().lower()
    if (
        not normalized_provider
        or not normalized_order
        or normalized_surface not in PAYMENT_RETURN_SURFACES
    ):
        raise PaymentReturnTokenError("payment_return_token_invalid")
    lifetime = max(
        300,
        min(
            30 * 24 * 60 * 60,
            int(
                ttl_seconds
                if ttl_seconds is not None
                else os.getenv("PAYMENT_RETURN_TOKEN_TTL_SECONDS") or 7 * 24 * 60 * 60
            ),
        ),
    )
    payload = {
        "schema": PAYMENT_RETURN_TOKEN_SCHEMA,
        "version": PAYMENT_RETURN_TOKEN_VERSION,
        "provider": normalized_provider,
        "order": normalized_order,
        "surface": normalized_surface,
        "issued_at": int(current.timestamp()),
        "expires_at": int((current + timedelta(seconds=lifetime)).timestamp()),
    }
    encoded = _b64_encode(_canonical_json(payload))
    signature = _b64_encode(
        hmac.new(
            _secret(secret),
            f"{PAYMENT_RETURN_TOKEN_PREFIX}.{encoded}".encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    return f"{PAYMENT_RETURN_TOKEN_PREFIX}.{encoded}.{signature}"


def inspect_payment_return_token(
    token: str,
    *,
    secret: str | bytes | None = None,
    now: datetime | None = None,
    allow_expired: bool = False,
) -> dict[str, Any]:
    raw = str(token or "").strip()
    if len(raw) > 1200:
        raise PaymentReturnTokenError("payment_return_token_malformed")
    parts = raw.split(".")
    if len(parts) != 3 or parts[0] != PAYMENT_RETURN_TOKEN_PREFIX:
        raise PaymentReturnTokenError("payment_return_token_malformed")
    expected = hmac.new(
        _secret(secret),
        f"{parts[0]}.{parts[1]}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    supplied = _b64_decode(parts[2])
    if not hmac.compare_digest(expected, supplied):
        raise PaymentReturnTokenError("payment_return_token_invalid")
    try:
        payload = json.loads(_b64_decode(parts[1]).decode("utf-8"))
    except Exception as exc:
        raise PaymentReturnTokenError("payment_return_token_malformed") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "version",
        "provider",
        "order",
        "surface",
        "issued_at",
        "expires_at",
    }:
        raise PaymentReturnTokenError("payment_return_token_invalid")
    try:
        issued_at = int(payload["issued_at"])
        expires_at = int(payload["expires_at"])
    except (TypeError, ValueError) as exc:
        raise PaymentReturnTokenError("payment_return_token_invalid") from exc
    provider = str(payload.get("provider") or "").strip().lower()
    order_id = str(payload.get("order") or "").strip()
    surface = str(payload.get("surface") or "").strip().lower()
    current_epoch = int(_as_utc(now or _utcnow()).timestamp())
    if (
        payload.get("schema") != PAYMENT_RETURN_TOKEN_SCHEMA
        or int(payload.get("version") or 0) != PAYMENT_RETURN_TOKEN_VERSION
        or not provider
        or len(provider) > 32
        or not order_id
        or len(order_id) > 128
        or surface not in PAYMENT_RETURN_SURFACES
        or issued_at <= 0
        or expires_at <= issued_at
        or expires_at - issued_at > 30 * 24 * 60 * 60
        or issued_at > current_epoch + 60
    ):
        raise PaymentReturnTokenError("payment_return_token_invalid")
    expired = expires_at <= current_epoch
    if expired and not allow_expired:
        raise PaymentReturnTokenError("payment_return_token_expired")
    return {
        "provider": provider,
        "order_id": order_id,
        "surface": surface,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "expired": expired,
    }


def _row_meta(row: Any) -> dict[str, Any]:
    try:
        value = json.loads(str(row.meta_json or "{}"))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _commercial_reservation_id(row: Any) -> str:
    intent = _row_meta(row).get("order_intent")
    lineage = intent.get("commercial_offer") if isinstance(intent, dict) else None
    return str(lineage.get("reservation") or "").strip().lower() if isinstance(lineage, dict) else ""


def _consumer_state(
    session: Any,
    row: Any,
    *,
    now: datetime,
) -> tuple[str, str]:
    raw_status = str(row.status or "").strip().lower()
    if raw_status == "paid":
        return "paid", "payment_confirmed"
    if raw_status == "manual_review":
        return "manual_review", "payment_manual_review"
    if raw_status == "cancelled":
        return "cancelled", "payment_cancelled"
    if raw_status in {"failed"}:
        return "failed", "payment_failed"
    if raw_status in {"refunded", "chargeback"}:
        return "failed", "payment_reversed"
    if raw_status not in {"created", "pending", "pending_verification"}:
        return "manual_review", "payment_state_unknown"

    reservation_public_id = _commercial_reservation_id(row)
    if reservation_public_id:
        try:
            from .models import CommercialReservation
        except ImportError:
            from models import CommercialReservation

        reservation = (
            session.query(CommercialReservation)
            .filter(CommercialReservation.public_id == reservation_public_id)
            .first()
        )
        if reservation is None:
            return "manual_review", "commercial_reservation_missing"
        reservation_status = str(reservation.status or "").strip().lower()
        if reservation_status in {"expired", "released"}:
            return "expired", "commercial_reservation_expired"
        if (
            reservation_status in {"held", "bound"}
            and _as_utc(reservation.hold_expires_at) <= now
        ):
            return "expired", "commercial_reservation_expired"

    pending_ttl = max(
        300,
        min(
            30 * 24 * 60 * 60,
            int(os.getenv("PAYMENT_RETURN_PENDING_TTL_SECONDS") or 72 * 60 * 60),
        ),
    )
    if _as_utc(row.created_at) + timedelta(seconds=pending_ttl) <= now:
        return "expired", "payment_session_expired"
    if raw_status == "pending_verification":
        return "processing", "payment_verification_pending"
    return "processing", "payment_processing"


def payment_return_status(
    session: Any,
    *,
    token: str,
    secret: str | bytes | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _as_utc(now or _utcnow())
    inspected = inspect_payment_return_token(
        token,
        secret=secret,
        now=current,
        allow_expired=True,
    )
    if bool(inspected["expired"]):
        state, reason = "expired", "payment_return_token_expired"
    else:
        try:
            from .models import ExternalOrder
        except ImportError:
            from models import ExternalOrder

        row = (
            session.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == inspected["provider"],
                ExternalOrder.order_id == inspected["order_id"],
            )
            .first()
        )
        if row is None:
            raise PaymentReturnTokenError("payment_return_order_missing")
        state, reason = _consumer_state(session, row, now=current)
    terminal = state != "processing"
    return {
        "ok": True,
        "state": state,
        "reason_code": reason,
        "surface": inspected["surface"],
        "provider": inspected["provider"],
        "server_time": current.isoformat().replace("+00:00", "Z"),
        "next_poll_seconds": 0 if terminal else 2,
        "terminal": terminal,
        "support_required": state == "manual_review",
        "can_retry": state in {"failed", "cancelled", "expired"},
    }
