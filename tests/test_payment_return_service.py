from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from portal_bot.models import Base, CommercialReservation, ExternalOrder
from portal_bot.payment_return_service import (
    PaymentReturnTokenError,
    inspect_payment_return_token,
    issue_payment_return_token,
    payment_return_status,
)


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
SECRET = "payment-return-test-secret"


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _order(session, *, status: str = "pending", meta: dict | None = None) -> ExternalOrder:
    row = ExternalOrder(
        provider="lavatop",
        order_id="order-123",
        plan_code="1_month",
        source="site",
        amount=239.0,
        currency="RUB",
        status=status,
        meta_json=json.dumps(meta or {}),
        created_at=NOW,
    )
    session.add(row)
    session.commit()
    return row


def _token(*, now: datetime = NOW, ttl_seconds: int = 3600) -> str:
    return issue_payment_return_token(
        provider="lavatop",
        order_id="order-123",
        surface="cabinet",
        secret=SECRET,
        now=now,
        ttl_seconds=ttl_seconds,
    )


def test_return_token_is_exact_identity_free_and_tamper_evident() -> None:
    token = _token()
    inspected = inspect_payment_return_token(token, secret=SECRET, now=NOW)

    assert inspected == {
        "provider": "lavatop",
        "order_id": "order-123",
        "surface": "cabinet",
        "issued_at": int(NOW.timestamp()),
        "expires_at": int((NOW + timedelta(hours=1)).timestamp()),
        "expired": False,
    }
    assert all(marker not in token for marker in ("email", "telegram", "account", "device"))

    prefix, payload, signature = token.split(".")
    tampered_payload = ("A" if payload[0] != "A" else "B") + payload[1:]
    with pytest.raises(PaymentReturnTokenError, match="payment_return_token_invalid"):
        inspect_payment_return_token(
            f"{prefix}.{tampered_payload}.{signature}", secret=SECRET, now=NOW
        )


@pytest.mark.parametrize(
    ("order_status", "state", "reason", "terminal", "can_retry"),
    [
        ("pending", "processing", "payment_processing", False, False),
        ("pending_verification", "processing", "payment_verification_pending", False, False),
        ("paid", "paid", "payment_confirmed", True, False),
        ("failed", "failed", "payment_failed", True, True),
        ("cancelled", "cancelled", "payment_cancelled", True, True),
        ("manual_review", "manual_review", "payment_manual_review", True, False),
        ("refunded", "failed", "payment_reversed", True, True),
        ("chargeback", "failed", "payment_reversed", True, True),
    ],
)
def test_return_status_maps_provider_state_to_closed_consumer_contract(
    order_status: str,
    state: str,
    reason: str,
    terminal: bool,
    can_retry: bool,
) -> None:
    engine, session = _session()
    try:
        _order(session, status=order_status)
        result = payment_return_status(session, token=_token(), secret=SECRET, now=NOW)
        assert result["state"] == state
        assert result["reason_code"] == reason
        assert result["terminal"] is terminal
        assert result["can_retry"] is can_retry
        assert result["next_poll_seconds"] == (0 if terminal else 2)
    finally:
        session.close()
        engine.dispose()


def test_return_status_revalidates_expired_commercial_reservation() -> None:
    engine, session = _session()
    try:
        reservation_id = "rsv_" + "1" * 32
        _order(
            session,
            meta={"order_intent": {"commercial_offer": {"reservation": reservation_id}}},
        )
        session.add(
            CommercialReservation(
                public_id=reservation_id,
                campaign_id=1,
                offer_id=1,
                creative_id=1,
                assignment_id=1,
                subject_hmac="a" * 64,
                commercial_revision="2026-08-20.1",
                campaign_revision=1,
                status="bound",
                token_version=2,
                token_sha256="b" * 64,
                impression_public_id="imp_" + "2" * 32,
                click_public_id="clk_" + "3" * 32,
                base_amount_rub=239,
                final_amount_rub=199,
                currency="RUB",
                issued_at=NOW - timedelta(minutes=20),
                hold_expires_at=NOW - timedelta(minutes=10),
                offer_ends_at=NOW + timedelta(days=1),
                bound_order_id="order-123",
                created_at=NOW - timedelta(minutes=20),
                updated_at=NOW - timedelta(minutes=20),
            )
        )
        session.commit()

        result = payment_return_status(session, token=_token(), secret=SECRET, now=NOW)
        assert result["state"] == "expired"
        assert result["reason_code"] == "commercial_reservation_expired"
        assert result["can_retry"] is True
    finally:
        session.close()
        engine.dispose()


def test_expired_return_token_closes_without_order_lookup() -> None:
    engine, session = _session()
    try:
        result = payment_return_status(
            session,
            token=_token(now=NOW - timedelta(hours=2), ttl_seconds=3600),
            secret=SECRET,
            now=NOW,
        )
        assert result["state"] == "expired"
        assert result["reason_code"] == "payment_return_token_expired"
    finally:
        session.close()
        engine.dispose()
