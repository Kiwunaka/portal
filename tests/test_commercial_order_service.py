from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import commercial_offer_service as offer_service  # noqa: E402
import commercial_order_service as order_service  # noqa: E402
import commercial_attribution_service as attribution_service  # noqa: E402
import economy_service  # noqa: E402
import payment_order_service  # noqa: E402
from commercial_contract import get_commercial_contract  # noqa: E402
from marketing_pilot_contract import get_winback_pilot_contract  # noqa: E402
from acquisition_service import handoff_token_hash  # noqa: E402
from migrations import run_migrations  # noqa: E402
from models import (  # noqa: E402
    Base,
    Account,
    AcquisitionHandoff,
    AcquisitionSession,
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    CommercialReservation,
    CommercialConversion,
    EntitlementGrant,
    ExternalOrder,
    IncentiveCampaign,
    PromoCode,
)


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
SECRET = "commercial-order-test-secret-at-least-32-bytes"


def _pilot_metadata() -> str:
    pilot = get_winback_pilot_contract()
    return json.dumps(
        {
            "marketing_pilot": {
                "pilot_revision": pilot["revision"],
                "pilot_contract_sha256": pilot["contract_sha256"],
                "marketing_governance_revision": pilot["marketing_governance_revision"],
                "marketing_governance_sha256": pilot["marketing_governance_sha256"],
                "commercial_revision": pilot["commercial_revision"],
                "commercial_contract_sha256": pilot["commercial_contract_sha256"],
                "pilot_launch_state": "owner_approved_ready",
                "approval_record_id": "test-owner-approval",
                "holdout_percent": 20,
            }
        },
        sort_keys=True,
    )


def _contract() -> dict:
    value = copy.deepcopy(get_commercial_contract())
    value["legal"].update(
        {
            "seller_publication_status": "published",
            "offer_review_status": "approved",
            "allowed_launch_channels": ["owned_web"],
            "launch_ready": True,
        }
    )
    return value


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed(session, *, tg_id: int = 1001, suffix: str = "a") -> dict:
    commercial = _contract()
    campaign = session.query(IncentiveCampaign).filter_by(public_id="cmp_" + "a" * 32).one_or_none()
    promo = session.query(PromoCode).filter_by(code="WIN10").one_or_none()
    if campaign is None:
        campaign = IncentiveCampaign(
            public_id="cmp_" + "a" * 32,
            name="Winback 10",
            campaign_type="promo",
            target_value="WIN10",
            objective="winback",
            lifecycle_status="live",
            revision=3,
            commercial_revision=commercial["commercial_revision"],
            legal_profile_status="owner_approved",
            channels_json=json.dumps(["owned_web"]),
            seller_profile_id="seller-owner-approved-v1",
            terms_revision=commercial["terms_revision"],
            paid_cap=20,
            paid_conversions_count=0,
            capacity_guard_enabled=True,
            capacity_band="green",
            state_reason="ready",
            segment="expired_paid_7_30d",
            starts_at=NOW - timedelta(hours=1),
            ends_at=NOW + timedelta(hours=71),
            is_active=True,
            metadata_json=_pilot_metadata(),
            created_at=NOW,
            updated_at=NOW,
        )
        promo = PromoCode(
            code="WIN10",
            promo_type="discount",
            value=10,
            uses_left=20,
            expires_at=NOW + timedelta(hours=71),
            created_at=NOW,
        )
        session.add_all([campaign, promo])
        session.flush()
    offer = session.query(CommercialOffer).filter_by(campaign_id=campaign.id).one_or_none()
    if offer is None:
        offer = CommercialOffer(
            public_id="off_" + "b" * 32,
            campaign_id=campaign.id,
            plan_code="3_months",
            status="live",
            commercial_revision=commercial["commercial_revision"],
            terms_revision=commercial["terms_revision"],
            currency="RUB",
            base_amount_rub=669,
            final_amount_rub=602,
            stackable_with_base_savings=True,
            paid_cap=20,
            paid_count=0,
            per_subject_paid_cap=1,
            starts_at=NOW - timedelta(minutes=30),
            ends_at=NOW + timedelta(hours=71),
            created_at=NOW,
            updated_at=NOW,
        )
        session.add(offer)
        session.flush()
    creative = session.query(CommercialCreative).filter_by(offer_id=offer.id).one_or_none()
    if creative is None:
        creative = CommercialCreative(
            public_id="crv_" + "c" * 32,
            campaign_id=campaign.id,
            offer_id=offer.id,
            variant_code="pilot_a",
            status="live",
            channel="owned_web",
            content_revision="creative-2026-08-21.1",
            created_at=NOW,
            updated_at=NOW,
        )
        session.add(creative)
        session.flush()
    subject = offer_service.commercial_subject_binding(
        campaign_public_id=str(campaign.public_id),
        subject_kind="telegram",
        subject_value=str(tg_id),
        secret=SECRET,
    )
    assignment = CommercialAssignment(
        public_id="asg_" + suffix * 32,
        campaign_id=campaign.id,
        offer_id=offer.id,
        creative_id=creative.id,
        subject_hmac=subject,
        status="active",
        audience_status="eligible",
        audience_reason="expired_paid_7_30d",
        paid_count=0,
        assigned_at=NOW,
        expires_at=NOW + timedelta(hours=71),
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(assignment)
    session.commit()
    return {
        "campaign": campaign,
        "promo": promo,
        "offer": offer,
        "creative": creative,
        "assignment": assignment,
        "tg_id": tg_id,
    }


def _preview(session, seeded: dict) -> dict:
    value = offer_service.preview_commercial_offer(
        session,
        plan_code="3_months",
        promo_code="WIN10",
        channel="owned_web",
        subject_kind="telegram",
        subject_value=str(seeded["tg_id"]),
        secret=SECRET,
        contract=_contract(),
        now=NOW,
        hold_ttl_seconds=600,
    )
    session.commit()
    assert value["valid"] is True
    return value


def _bind(session, token: str, *, tg_id: int, candidate: str = "fk_site_1001_exact") -> dict:
    return order_service.bind_commercial_offer_to_order(
        session,
        offer_token=token,
        provider="freekassa",
        candidate_order_id=candidate,
        plan_code="3_months",
        currency="RUB",
        tg_id=tg_id,
        secret=SECRET,
        contract=_contract(),
        now=NOW + timedelta(minutes=1),
    )


def _persist_order(session, binding: dict, *, tg_id: int) -> ExternalOrder:
    intent = payment_order_service.build_payment_order_intent(
        order_id=binding["order_id"],
        provider="freekassa",
        tg_id=tg_id,
        buyer_email=None,
        plan_code="3_months",
        source="site",
        amount=binding["final_amount_rub"],
        currency="RUB",
        entitlement_snapshot={
            "plan_code": "3_months",
            "duration_days": 90,
            "amount_rub": binding["final_amount_rub"],
            "currency": "RUB",
            "source": "site",
        },
        commercial_offer=binding["lineage"],
    )
    row, _ = payment_order_service.persist_local_order_intent(
        session,
        intent=intent,
        metadata={"fulfillment": {"mode": "account_extend", "status": "pending_payment"}},
        serialize_meta=lambda value: json.dumps(value, sort_keys=True),
        created_at=NOW,
        campaign=binding["campaign_key"],
        promo_code=binding["promo_code"],
    )
    session.commit()
    return row


def test_bind_persists_exact_lineage_and_exact_retry_reuses_order(db) -> None:
    seeded = _seed(db)
    preview = _preview(db, seeded)
    binding = _bind(db, preview["offer_token"], tg_id=seeded["tg_id"])
    row = _persist_order(db, binding, tg_id=seeded["tg_id"])

    reservation = db.query(CommercialReservation).one()
    stored_intent = json.loads(row.meta_json)["order_intent"]
    assert reservation.status == "bound"
    assert reservation.bound_order_id == row.order_id == binding["order_id"]
    assert stored_intent["schema"] == "pokrov-payment-order-intent-v2"
    assert stored_intent["commercial_offer"] == binding["lineage"]
    assert stored_intent["amount"] == "602.00"
    assert preview["offer_token"] not in row.meta_json

    retry = _bind(
        db,
        preview["offer_token"],
        tg_id=seeded["tg_id"],
        candidate="fk_site_1001_must_not_replace",
    )
    assert retry["order_preexisting"] is True
    assert retry["order_id"] == row.order_id
    assert db.query(ExternalOrder).count() == 1

    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_subject_mismatch"):
        _bind(db, preview["offer_token"], tg_id=2002)
    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_order_binding_conflict"):
        order_service.bind_commercial_offer_to_order(
            db,
            offer_token=preview["offer_token"],
            provider="lavatop",
            candidate_order_id="lavatop_site_1001_new",
            plan_code="3_months",
            currency="RUB",
            tg_id=seeded["tg_id"],
            secret=SECRET,
            contract=_contract(),
            now=NOW + timedelta(minutes=1),
        )


def test_binding_revalidates_price_revision_legal_and_expiry(db) -> None:
    seeded = _seed(db)
    preview = _preview(db, seeded)
    seeded["offer"].final_amount_rub = 601
    db.commit()
    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_price_stale"):
        _bind(db, preview["offer_token"], tg_id=seeded["tg_id"])
    seeded["offer"].final_amount_rub = 602
    seeded["campaign"].revision = 4
    db.commit()
    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_lineage_conflict"):
        _bind(db, preview["offer_token"], tg_id=seeded["tg_id"])
    seeded["campaign"].revision = 3
    db.commit()
    blocked = get_commercial_contract()
    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_campaign_blocked"):
        order_service.bind_commercial_offer_to_order(
            db,
            offer_token=preview["offer_token"],
            provider="freekassa",
            candidate_order_id="fk_site_1001_blocked",
            plan_code="3_months",
            currency="RUB",
            tg_id=seeded["tg_id"],
            secret=SECRET,
            contract=blocked,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(order_service.CommercialOrderBindingError, match="offer_token_expired"):
        order_service.bind_commercial_offer_to_order(
            db,
            offer_token=preview["offer_token"],
            provider="freekassa",
            candidate_order_id="fk_site_1001_expired",
            plan_code="3_months",
            currency="RUB",
            tg_id=seeded["tg_id"],
            secret=SECRET,
            contract=_contract(),
            now=NOW + timedelta(minutes=10),
        )
    assert db.query(CommercialReservation).one().status == "expired"


def test_paid_consumption_is_idempotent_and_refund_keeps_original_lineage(db) -> None:
    seeded = _seed(db)
    preview = _preview(db, seeded)
    binding = _bind(db, preview["offer_token"], tg_id=seeded["tg_id"])
    row = _persist_order(db, binding, tg_id=seeded["tg_id"])
    original_intent = json.loads(row.meta_json)["order_intent"]

    first = order_service.consume_commercial_reservation_for_paid_order(
        db,
        provider="freekassa",
        order_id=row.order_id,
        now=NOW + timedelta(minutes=2),
    )
    db.commit()
    second = order_service.consume_commercial_reservation_for_paid_order(
        db,
        provider="freekassa",
        order_id=row.order_id,
        now=NOW + timedelta(minutes=3),
    )
    db.commit()

    assert (first, second) == ("consumed", "already_consumed")
    assert seeded["campaign"].paid_conversions_count == 1
    assert seeded["offer"].paid_count == 1
    assert seeded["assignment"].paid_count == 1
    assert db.query(CommercialReservation).one().status == "consumed"

    row.status = "refunded"
    db.commit()
    assert json.loads(row.meta_json)["order_intent"] == original_intent
    assert seeded["campaign"].paid_conversions_count == 1


def test_only_failed_provider_orders_release_due_bound_reservations(db) -> None:
    seeded = _seed(db)
    preview = _preview(db, seeded)
    binding = _bind(db, preview["offer_token"], tg_id=seeded["tg_id"])
    row = _persist_order(db, binding, tg_id=seeded["tg_id"])
    meta = json.loads(row.meta_json)
    meta["provider_checkout"] = {"schema": "pokrov-provider-checkout-v1", "status": "ready"}
    row.meta_json = json.dumps(meta, sort_keys=True)
    db.commit()

    kept = order_service.expire_failed_commercial_reservations(
        db,
        now=NOW + timedelta(minutes=10),
    )
    db.commit()
    assert kept == 0
    assert db.query(CommercialReservation).one().status == "bound"

    meta["provider_checkout"] = {
        "schema": "pokrov-provider-checkout-v1",
        "status": "error",
        "error_code": "provider_checkout_error",
    }
    row.meta_json = json.dumps(meta, sort_keys=True)
    db.commit()
    released = order_service.expire_failed_commercial_reservations(
        db,
        now=NOW + timedelta(minutes=10),
    )
    db.commit()
    reservation = db.query(CommercialReservation).one()
    assert released == 1
    assert reservation.status == "expired"
    assert reservation.released_at is not None
    assert json.loads(row.meta_json)["order_intent"]["commercial_offer"] == binding["lineage"]


def test_acquisition_handoff_touch_ids_reach_token_and_immutable_order_lineage(db) -> None:
    seeded = _seed(db)
    acquisition = AcquisitionSession(
        id="acquisition-touch-lineage-000000001",
        session_key_hash="9" * 64,
        first_source="owned",
        first_channel="site",
        first_entry_route="/offer",
        last_source="owned",
        last_channel="site",
        last_entry_route="/checkout",
        created_at=NOW,
        first_touch_at=NOW,
        last_touch_at=NOW,
        expires_at=NOW + timedelta(hours=2),
    )
    raw_handle = "acquisition-touch-handle-" + "x" * 32
    handoff = AcquisitionHandoff(
        id="acquisition-handoff-touch-00000001",
        token_hash=handoff_token_hash(raw_handle),
        acquisition_session_id=acquisition.id,
        purpose="checkout",
        impression_public_id="imp_" + "1" * 32,
        click_public_id="clk_" + "2" * 32,
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    seeded["assignment"].subject_hmac = offer_service.commercial_subject_binding(
        campaign_public_id=str(seeded["campaign"].public_id),
        subject_kind="acquisition_session",
        subject_value=acquisition.id,
        secret=SECRET,
    )
    db.add_all([acquisition, handoff])
    db.commit()
    preview = offer_service.preview_commercial_offer(
        db,
        plan_code="3_months",
        promo_code="WIN10",
        channel="owned_web",
        subject_kind="acquisition_session",
        subject_value=acquisition.id,
        impression_public_id=handoff.impression_public_id,
        click_public_id=handoff.click_public_id,
        secret=SECRET,
        contract=_contract(),
        now=NOW,
        hold_ttl_seconds=600,
    )
    db.commit()
    token = offer_service.verify_commercial_offer_token(
        preview["offer_token"],
        secret=SECRET,
        now=NOW,
    )
    binding = order_service.bind_commercial_offer_to_order(
        db,
        offer_token=preview["offer_token"],
        provider="freekassa",
        candidate_order_id="fk_acquisition_touch_lineage",
        plan_code="3_months",
        currency="RUB",
        tg_id=seeded["tg_id"],
        acquisition_handle=raw_handle,
        secret=SECRET,
        contract=_contract(),
        now=NOW + timedelta(minutes=1),
    )
    row = _persist_order(db, binding, tg_id=seeded["tg_id"])
    db.refresh(handoff)
    assert token["impression"] == handoff.impression_public_id == binding["lineage"]["impression"]
    assert token["click"] == handoff.click_public_id == binding["lineage"]["click"]
    assert handoff.bound_order_id == row.order_id
    assert handoff.consumed_at is not None
    assert json.loads(row.meta_json)["order_intent"]["commercial_offer"] == binding["lineage"]


def test_serialized_bindings_cannot_exceed_paid_caps(db) -> None:
    first_seed = _seed(db, tg_id=1001, suffix="d")
    first_preview = _preview(db, first_seed)
    second_seed = _seed(db, tg_id=1002, suffix="e")
    second_preview = _preview(db, second_seed)
    first_seed["offer"].paid_cap = 1
    db.commit()

    first = _bind(db, first_preview["offer_token"], tg_id=1001)
    _persist_order(db, first, tg_id=1001)
    with pytest.raises(order_service.CommercialOrderBindingError, match="commercial_quota_reached"):
        _bind(
            db,
            second_preview["offer_token"],
            tg_id=1002,
            candidate="fk_site_1002_rejected",
        )


def test_additive_migration_enforces_one_commercial_reservation_per_order() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE commercial_reservations")
    run_migrations(engine)
    indexes = {item["name"]: item for item in inspect(engine).get_indexes("commercial_reservations")}
    assert indexes["ux_commercial_reservations_bound_order_id"]["unique"] == 1
    engine.dispose()


def _paid_commercial_order(db, *, order_id: str = "fk_site_1001_attribution") -> tuple[dict, ExternalOrder]:
    seeded = _seed(db)
    preview = _preview(db, seeded)
    binding = _bind(db, preview["offer_token"], tg_id=seeded["tg_id"], candidate=order_id)
    row = _persist_order(db, binding, tg_id=seeded["tg_id"])
    paid_at = NOW + timedelta(minutes=2)
    row.status = "paid"
    row.paid_at = paid_at
    db.add(
        Account(
            id="account-attribution-000000000000001",
            status="active",
            created_source="test",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    db.add(
        EntitlementGrant(
            id="grant-attribution-0000000000000001",
            account_id="account-attribution-000000000000001",
            legacy_tg_id=seeded["tg_id"],
            idempotency_key=f"provider:freekassa:{order_id}",
            source="provider_payment",
            status="active",
            grant_kind="paid_access",
            plan_code="3_months",
            starts_at=paid_at,
            expires_at=paid_at + timedelta(days=90),
            provider="freekassa",
            external_order_id=order_id,
            created_at=paid_at,
            updated_at=paid_at,
        )
    )
    db.flush()
    assert order_service.consume_commercial_reservation_for_paid_order(
        db,
        provider="freekassa",
        order_id=order_id,
        now=paid_at,
    ) == "consumed"
    db.commit()
    return binding, row


def test_commercial_projection_uses_payment_and_observer_authorities_idempotently(db) -> None:
    binding, row = _paid_commercial_order(db)
    paid = db.query(CommercialConversion).filter_by(stage="paid").one()
    assert paid.gross_amount_rub == 602
    assert paid.refund_amount_rub == 0
    assert paid.impression_public_id == binding["lineage"]["impression"]
    assert paid.click_public_id == binding["lineage"]["click"]
    assert paid.evidence_kind == "signed_payment_callback"

    d7_at = row.paid_at + timedelta(days=8)
    d7 = economy_service.record_connection_evidence(
        db,
        account_id="account-attribution-000000000000001",
        device_id="device-must-not-enter-projection",
        node_id=42,
        evidence_kind="observer_connection",
        observed_at=d7_at,
        evidence_key="observer:test:attribution:d7",
    )
    replay = economy_service.record_connection_evidence(
        db,
        account_id="account-attribution-000000000000001",
        device_id="device-must-not-enter-projection",
        node_id=42,
        evidence_kind="observer_connection",
        observed_at=d7_at,
        evidence_key="observer:test:attribution:d7",
    )
    assert replay.id == d7.id
    assert {
        item.stage
        for item in db.query(CommercialConversion).filter(
            CommercialConversion.stage.in_(["first_verified_connect", "retained_d7"])
        )
    } == {"first_verified_connect", "retained_d7"}

    d30_at = row.paid_at + timedelta(days=31)
    economy_service.record_connection_evidence(
        db,
        account_id="account-attribution-000000000000001",
        device_id=None,
        node_id=43,
        evidence_kind="observer_connection",
        observed_at=d30_at,
        evidence_key="observer:test:attribution:d30",
    )

    row.status = "refunded"
    reversed_row = attribution_service.record_commercial_reversal_projection(
        db,
        order=row,
        reversal_kind="refund",
        occurred_at=d30_at + timedelta(hours=1),
    )
    replay_reversal = attribution_service.record_commercial_reversal_projection(
        db,
        order=row,
        reversal_kind="chargeback",
        occurred_at=d30_at + timedelta(hours=2),
    )
    db.commit()
    assert reversed_row.id == replay_reversal.id
    assert replay_reversal.reversal_kind == "chargeback"
    assert replay_reversal.refund_amount_rub == 602
    assert db.query(CommercialConversion).count() == 5

    readback = attribution_service.commercial_attribution_read_model(
        db,
        from_dt=NOW,
        to_dt=d30_at + timedelta(days=1),
        now=d30_at + timedelta(days=1),
    )
    assert readback["authority"]["telemetry_is_payment_truth"] is False
    assert readback["retention_windows"] == {
        "retained_d7": "paid_at+[7d,14d)",
        "retained_d30": "paid_at+[30d,37d)",
    }
    assert readback["summary"] == {
        "gross_revenue_rub": 602,
        "refund_revenue_rub": 602,
        "net_revenue_rub": 0,
        "paid_conversions": 1,
        "first_verified_connects": 1,
        "retained_d7": 1,
        "retained_d30": 1,
        "renewals": 0,
        "paid_capacity_units": 1,
    }
    assert readback["primary_metric"] == {
        "name": "net_revenue_30d_per_capacity_unit",
        "state": "ready",
        "value": 602.0,
        "net_revenue_30d_rub": 602,
        "paid_capacity_units": 1,
        "maturity_cutoff": "2026-08-23T12:02:00Z",
        "minimum_observation_days": 30,
        "reason": None,
    }
    assert readback["variant_cohorts"][0]["metric_state"] == "ready"
    assert readback["variant_cohorts"][0]["net_revenue_30d_per_capacity_unit"] == 602.0
    assert readback["holdout"]["state"] == "insufficient_data"
    assert readback["holdout"]["fabricated_zero"] is False
    projected_columns = set(CommercialConversion.__table__.c.keys())
    assert not {
        "account_id",
        "tg_id",
        "email",
        "device_id",
        "node_id",
        "token_sha256",
        "provider_payload",
        "entitlement_secret",
    } & projected_columns


def test_commercial_renewal_stage_requires_prior_server_payment_grant(db) -> None:
    db.add(
        EntitlementGrant(
            id="grant-attribution-prior-0000000000001",
            account_id="account-attribution-000000000000001",
            legacy_tg_id=1001,
            idempotency_key="provider:freekassa:prior-order",
            source="provider_payment",
            status="expired",
            grant_kind="paid_access",
            plan_code="1_month",
            starts_at=NOW - timedelta(days=40),
            expires_at=NOW - timedelta(days=10),
            provider="freekassa",
            external_order_id="prior-order",
            created_at=NOW - timedelta(days=40),
            updated_at=NOW - timedelta(days=10),
        )
    )
    db.flush()
    _binding, _row = _paid_commercial_order(db, order_id="fk_site_1001_renewal")
    stages = {
        item.stage
        for item in db.query(CommercialConversion)
        .filter_by(order_id="fk_site_1001_renewal")
        .all()
    }
    assert stages == {"paid", "renewal"}


def test_additive_migration_creates_identity_free_commercial_projection() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE commercial_conversions")
        connection.exec_driver_sql("DROP TABLE commercial_reservations")
    run_migrations(engine)
    schema = inspect(engine)
    assert "commercial_conversions" in schema.get_table_names()
    conversion_columns = {item["name"] for item in schema.get_columns("commercial_conversions")}
    assert {
        "provider",
        "order_id",
        "stage",
        "impression_public_id",
        "click_public_id",
        "gross_amount_rub",
        "refund_amount_rub",
        "evidence_kind",
        "evidence_ref",
    } <= conversion_columns
    assert not {"account_id", "tg_id", "email", "device_id", "node_id"} & conversion_columns
    indexes = {item["name"]: item for item in schema.get_indexes("commercial_conversions")}
    unique_constraints = {
        item["name"] for item in schema.get_unique_constraints("commercial_conversions")
    }
    assert "uq_commercial_conversion_order_stage" in unique_constraints
    assert "ix_commercial_conversions_campaign_stage_time" in indexes
    reservation_columns = {
        item["name"] for item in schema.get_columns("commercial_reservations")
    }
    assert {"impression_public_id", "click_public_id"} <= reservation_columns
    engine.dispose()
