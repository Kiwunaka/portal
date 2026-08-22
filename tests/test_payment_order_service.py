from __future__ import annotations

import dataclasses
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

models = importlib.import_module("models")
service = importlib.import_module("payment_order_service")
NOW = datetime(2026, 8, 21, 14, 0, 0)


@pytest.fixture()
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'payment-order.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _serialize(value: dict) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _intent(**overrides):
    values = {
        "order_id": "lavatop_site_1001_exact",
        "provider": "lavatop",
        "tg_id": 1001,
        "buyer_email": None,
        "plan_code": "1_month",
        "source": "site",
        "amount": "239.00",
        "currency": "RUB",
        "entitlement_snapshot": {
            "plan_code": "1_month",
            "duration_days": 30,
            "amount_rub": "239.00",
            "currency": "RUB",
            "source": "site",
        },
    }
    values.update(overrides)
    return service.build_payment_order_intent(**values)


def _commercial_lineage() -> dict:
    return {
        "schema": "pokrov-commercial-order-lineage-v2",
        "campaign": "cmp_" + "a" * 32,
        "campaign_revision": 3,
        "commercial_revision": "2026-08-21.1",
        "terms_revision": "terms-2026-08-21.1",
        "offer": "off_" + "b" * 32,
        "creative": "crv_" + "c" * 32,
        "variant": "pilot_a",
        "assignment": "asg_" + "d" * 32,
        "reservation": "rsv_" + "e" * 32,
        "impression": "imp_" + "f" * 32,
        "click": "clk_" + "0" * 32,
        "subject": "f" * 64,
        "base_amount_rub": 269,
        "final_amount_rub": 239,
        "currency": "RUB",
        "issued_at": 1787310000,
        "hold_expires_at": 1787310600,
        "offer_ends_at": 1787313600,
        "token_sha256": "1" * 64,
    }


def _persist(session, *, intent=None):
    return service.persist_local_order_intent(
        session,
        intent=intent or _intent(),
        metadata={
            "fulfillment": {"mode": "account_extend", "status": "pending_payment"}
        },
        serialize_meta=_serialize,
        created_at=NOW,
        campaign="release_1_2_0",
        promo_code="WELCOME20",
    )


def test_local_order_is_persisted_once_with_closed_immutable_authority(session) -> None:
    intent = _intent()
    row, created = _persist(session, intent=intent)
    session.commit()

    assert created is True
    assert row.status == "created"
    assert json.loads(row.meta_json)["order_intent"] == intent.payload()

    same_row, created_again = _persist(session, intent=intent)
    assert created_again is False
    assert same_row.id == row.id
    assert session.query(models.ExternalOrder).count() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount", "240.00"),
        ("currency", "USD"),
        ("plan_code", "3_months"),
        ("source", "bot"),
        ("tg_id", 2002),
        (
            "entitlement_snapshot",
            {
                "plan_code": "1_month",
                "duration_days": 31,
                "amount_rub": "239.00",
                "currency": "RUB",
                "source": "site",
            },
        ),
    ],
)
def test_existing_order_rejects_authority_drift(session, field: str, value) -> None:
    intent = _intent()
    row, _ = _persist(session, intent=intent)
    session.commit()

    if field == "amount":
        row.amount = float(value)
    elif field == "currency":
        row.currency = value
    elif field == "plan_code":
        row.plan_code = value
    elif field == "source":
        row.source = value
    elif field == "tg_id":
        row.tg_id = value
    else:
        changed = dataclasses.replace(intent, entitlement_snapshot=value)
        with pytest.raises(
            service.PaymentOrderIntentError, match="order_intent_conflict"
        ):
            service.assert_order_matches_intent(row, changed)
        return

    with pytest.raises(service.PaymentOrderIntentError, match="order_intent_conflict"):
        service.assert_order_matches_intent(row, intent)


def test_provider_result_is_bounded_and_does_not_persist_url_or_raw_payload(
    session,
) -> None:
    intent = _intent()
    row, _ = _persist(session, intent=intent)
    session.commit()

    service.record_provider_checkout(
        row,
        intent=intent,
        payment_url="https://pay.example/checkout?token=must-not-persist",
        remote_response={
            "id": "provider-reference-1",
            "status": "new",
            "payment_url": "https://pay.example/raw-secret",
            "request": {"email": "buyer@pokrov.test"},
            "secret": "must-not-persist",
        },
        metadata_update={"request": {"plan_code": "1_month"}},
        serialize_meta=_serialize,
    )
    session.commit()

    raw = str(row.meta_json)
    meta = json.loads(raw)
    assert row.status == "pending"
    assert meta["provider_checkout"] == {
        "remote": {"id": "provider-reference-1", "status": "new"},
        "schema": "pokrov-provider-checkout-v1",
        "status": "ready",
        "url_present": True,
    }
    assert "must-not-persist" not in raw
    assert "buyer@pokrov.test" not in raw
    assert "https://pay.example" not in raw


def test_failed_checkout_stays_non_fulfilling_and_exact_retry_reuses_order(
    session,
) -> None:
    intent = _intent()
    row, _ = _persist(session, intent=intent)
    session.commit()

    service.record_provider_checkout_failure(
        row,
        intent=intent,
        error_code="provider_checkout_error",
        serialize_meta=_serialize,
    )
    session.commit()
    assert row.status == "created"
    assert json.loads(row.meta_json)["provider_checkout"]["status"] == "error"

    same_row, created = _persist(session, intent=intent)
    assert created is False
    service.record_provider_checkout(
        same_row,
        intent=intent,
        payment_url="https://pay.example/retry",
        remote_response={"status": "new"},
        metadata_update={},
        serialize_meta=_serialize,
    )
    session.commit()
    assert same_row.id == row.id
    assert same_row.status == "pending"


def test_checkout_completion_never_regresses_terminal_local_status(session) -> None:
    intent = _intent()
    row, _ = _persist(session, intent=intent)
    row.status = "paid"
    session.commit()

    service.record_provider_checkout(
        row,
        intent=intent,
        payment_url="https://pay.example/raced-callback",
        remote_response={"status": "new"},
        metadata_update={},
        serialize_meta=_serialize,
    )
    session.commit()
    assert row.status == "paid"


def test_commercial_lineage_is_closed_hashed_v2_authority(session) -> None:
    intent = _intent(commercial_offer=_commercial_lineage())
    row, created = _persist(session, intent=intent)
    session.commit()

    stored = json.loads(row.meta_json)["order_intent"]
    assert created is True
    assert stored["schema"] == "pokrov-payment-order-intent-v2"
    assert stored["commercial_offer"] == _commercial_lineage()
    assert "offer_token" not in json.dumps(stored)

    drifted = dict(_commercial_lineage())
    drifted["final_amount_rub"] = 238
    with pytest.raises(
        service.PaymentOrderIntentError,
        match="commercial_lineage_price_mismatch",
    ):
        _intent(commercial_offer=drifted)

    extra = dict(_commercial_lineage())
    extra["buyer_email"] = "must-not-enter-lineage@example.test"
    with pytest.raises(service.PaymentOrderIntentError, match="invalid_commercial_lineage"):
        _intent(commercial_offer=extra)
