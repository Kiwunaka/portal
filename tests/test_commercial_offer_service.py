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
from acquisition_service import handoff_token_hash  # noqa: E402
from commercial_contract import get_commercial_contract  # noqa: E402
from marketing_pilot_contract import get_winback_pilot_contract  # noqa: E402
from migrations import run_migrations  # noqa: E402
from models import (  # noqa: E402
    AcquisitionHandoff,
    AcquisitionSession,
    Base,
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    CommercialReservation,
    IncentiveCampaign,
    PromoCode,
)


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
SECRET = "commercial-offer-test-secret-at-least-32-bytes"


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


def _ready_contract() -> dict:
    contract = copy.deepcopy(get_commercial_contract())
    contract["legal"].update(
        {
            "seller_publication_status": "published",
            "offer_review_status": "approved",
            "allowed_launch_channels": ["owned_web"],
            "launch_ready": True,
        }
    )
    return contract


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, future=True)()


def _seed_offer(
    session,
    *,
    contract: dict | None = None,
    subject_kind: str = "acquisition_session",
    subject_value: str = "session-safe-id",
) -> dict:
    commercial = contract or _ready_contract()
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
    subject_hmac = offer_service.commercial_subject_binding(
        campaign_public_id=str(campaign.public_id),
        subject_kind=subject_kind,
        subject_value=subject_value,
        secret=SECRET,
    )
    assignment = CommercialAssignment(
        public_id="asg_" + "d" * 32,
        campaign_id=campaign.id,
        offer_id=offer.id,
        creative_id=creative.id,
        subject_hmac=subject_hmac,
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
    }


def _preview(session, *, contract: dict | None = None, now: datetime = NOW) -> dict:
    return offer_service.preview_commercial_offer(
        session,
        plan_code="3_months",
        promo_code="WIN10",
        channel="owned_web",
        subject_kind="acquisition_session",
        subject_value="session-safe-id",
        secret=SECRET,
        contract=contract or _ready_contract(),
        now=now,
        hold_ttl_seconds=600,
    )


def test_offer_vocabularies_and_models_are_closed_and_campaign_owned() -> None:
    assert offer_service.OFFER_STATUSES == {"draft", "review", "live", "paused", "ended", "killed"}
    assert offer_service.RESERVATION_STATUSES == {"held", "bound", "consumed", "expired", "released"}
    assert {"ready", "promo_unknown", "legal_blocked", "capacity_blocked", "reservation_expired"} <= offer_service.OFFER_PREVIEW_REASONS
    assert CommercialOffer.__table__.c.campaign_id.foreign_keys
    assert CommercialCreative.__table__.c.campaign_id.foreign_keys
    assert CommercialAssignment.__table__.c.campaign_id.foreign_keys
    assert CommercialReservation.__table__.c.campaign_id.foreign_keys


def test_preview_returns_exact_server_price_signed_binding_and_bounded_quota() -> None:
    engine, session = _session()
    try:
        seeded = _seed_offer(session)
        result = _preview(session)
        session.commit()

        assert result["valid"] is True
        assert result["reason_code"] == "ready"
        assert result["base_price_rub"] == 669
        assert result["final_price_rub"] == 602
        assert result["benefit_rub"] == 67
        assert result["benefit_percent"] == 10
        assert result["remaining_quota_lower_bound"] == 19
        assert result["terms_url"] == "https://pokrov.space/offer/"
        assert result["commercial_revision"] == _ready_contract()["commercial_revision"]
        assert result["offer_ends_at"] == "2026-08-24T11:00:00Z"
        assert result["hold_expires_at"] == "2026-08-21T12:10:00Z"

        payload = offer_service.verify_commercial_offer_token(
            result["offer_token"], secret=SECRET, now=NOW
        )
        assert set(payload) == offer_service.OFFER_TOKEN_FIELDS
        assert payload["subject"] == seeded["assignment"].subject_hmac
        assert payload["campaign"] == seeded["campaign"].public_id
        assert payload["campaign_revision"] == 3
        assert payload["offer"] == seeded["offer"].public_id
        assert payload["creative"] == seeded["creative"].public_id
        assert payload["assignment"] == seeded["assignment"].public_id
        assert payload["schema"] == "pokrov-commercial-offer-token-v2"
        assert payload["version"] == 2
        assert payload["impression"] == result["impression_id"]
        assert payload["click"] == result["click_id"]
        assert not ({"email", "tg_id", "account_id", "install_id", "checkout_url", "provider_secret"} & set(payload))
        assert "session-safe-id" not in result["offer_token"]
        stored = session.query(CommercialReservation).one()
        assert stored.token_sha256 != result["offer_token"]
        assert len(stored.token_sha256) == 64
        assert stored.impression_public_id == result["impression_id"]
        assert stored.click_public_id == result["click_id"]
    finally:
        session.close()
        engine.dispose()


def test_refresh_reuses_absolute_hold_and_expiry_cannot_be_extended() -> None:
    engine, session = _session()
    try:
        seeded = _seed_offer(session)
        seeded["offer"].paid_cap = 1
        session.commit()
        first = _preview(session)
        session.commit()
        refreshed = _preview(session, now=NOW + timedelta(minutes=2))
        session.commit()

        assert refreshed["valid"] is True
        assert refreshed["reservation_id"] == first["reservation_id"]
        assert refreshed["hold_expires_at"] == first["hold_expires_at"]
        assert first["remaining_quota_lower_bound"] == 0
        assert refreshed["remaining_quota_lower_bound"] == 0
        assert session.query(CommercialReservation).count() == 1

        expired = _preview(session, now=NOW + timedelta(minutes=10))
        session.commit()
        assert expired["valid"] is False
        assert expired["reason_code"] == "reservation_expired"
        assert expired["final_price_rub"] == expired["base_price_rub"] == 669
        assert expired["offer_token"] is None
        assert session.query(CommercialReservation).one().status == "expired"
        assert session.query(CommercialReservation).count() == 1
    finally:
        session.close()
        engine.dispose()


def test_token_mutation_and_expiry_fail_closed() -> None:
    engine, session = _session()
    try:
        _seed_offer(session)
        token = _preview(session)["offer_token"]
        prefix, payload, signature = token.split(".")
        replacement = "A" if payload[0] != "A" else "B"
        mutated = f"{prefix}.{replacement}{payload[1:]}.{signature}"
        with pytest.raises(offer_service.CommercialOfferTokenError, match="offer_token_signature_invalid"):
            offer_service.verify_commercial_offer_token(mutated, secret=SECRET, now=NOW)
        with pytest.raises(offer_service.CommercialOfferTokenError, match="offer_token_expired"):
            offer_service.verify_commercial_offer_token(
                token,
                secret=SECRET,
                now=NOW + timedelta(minutes=10),
            )
        payload_value = offer_service.verify_commercial_offer_token(
            token, secret=SECRET, now=NOW
        )
        payload_value["hold_expires_at"] = payload_value["issued_at"] + 901
        payload_value["offer_ends_at"] = payload_value["hold_expires_at"]
        oversized = offer_service.sign_commercial_offer_token(
            payload_value, secret=SECRET
        )
        with pytest.raises(offer_service.CommercialOfferTokenError, match="offer_token_time_invalid"):
            offer_service.verify_commercial_offer_token(
                oversized,
                secret=SECRET,
                now=NOW,
            )
    finally:
        session.close()
        engine.dispose()


def test_invalid_promo_legal_capacity_audience_and_stale_price_return_base_without_token(
    monkeypatch,
) -> None:
    engine, session = _session()
    try:
        seeded = _seed_offer(session)
        unknown = offer_service.preview_commercial_offer(
            session,
            plan_code="3_months",
            promo_code="NOPE",
            subject_kind="acquisition_session",
            subject_value="session-safe-id",
            secret=SECRET,
            contract=_ready_contract(),
            now=NOW,
        )
        assert (unknown["reason_code"], unknown["final_price_rub"], unknown["offer_token"]) == (
            "promo_unknown",
            669,
            None,
        )

        legal = _preview(session, contract=get_commercial_contract())
        assert legal["reason_code"] == "legal_blocked"

        monkeypatch.setattr(offer_service, "active_entitlement_capacity_units", lambda *_args, **_kwargs: 210)
        capacity = _preview(session)
        assert capacity["reason_code"] == "capacity_blocked"
        monkeypatch.setattr(offer_service, "active_entitlement_capacity_units", lambda *_args, **_kwargs: 0)

        seeded["promo"].expires_at = NOW
        session.commit()
        expired_promo = _preview(session)
        assert expired_promo["reason_code"] == "promo_expired"
        seeded["promo"].expires_at = NOW + timedelta(hours=2)
        seeded["offer"].commercial_revision = "stale-revision"
        session.commit()
        stale_revision = _preview(session)
        assert stale_revision["reason_code"] == "offer_revision_stale"
        seeded["offer"].commercial_revision = _ready_contract()["commercial_revision"]
        seeded["offer"].stackable_with_base_savings = False
        session.commit()
        non_stackable = _preview(session)
        assert non_stackable["reason_code"] == "offer_non_stackable"
        seeded["offer"].stackable_with_base_savings = True
        seeded["offer"].paid_count = seeded["offer"].paid_cap
        session.commit()
        quota = _preview(session)
        assert quota["reason_code"] == "quota_reached"
        seeded["offer"].paid_count = 0
        seeded["assignment"].audience_status = "blocked"
        session.commit()
        audience = _preview(session)
        assert audience["reason_code"] == "audience_blocked"
        seeded["assignment"].audience_status = "eligible"
        seeded["offer"].base_amount_rub = 670
        session.commit()
        stale_price = _preview(session)
        assert stale_price["reason_code"] == "offer_price_mismatch"
        for result in (
            legal,
            capacity,
            expired_promo,
            stale_revision,
            non_stackable,
            quota,
            audience,
            stale_price,
        ):
            assert result["final_price_rub"] == result["base_price_rub"] == 669
            assert result["offer_token"] is None
    finally:
        session.close()
        engine.dispose()


def test_acquisition_handle_resolves_to_opaque_session_subject_only() -> None:
    engine, session = _session()
    try:
        raw_handle = "acquisition-handoff-test-token-1234567890"
        acquisition = AcquisitionSession(
            id="11111111-2222-3333-4444-555555555555",
            session_key_hash="a" * 64,
            first_source="owned",
            first_channel="site",
            first_entry_route="/",
            last_source="owned",
            last_channel="site",
            last_entry_route="/",
            created_at=NOW,
            first_touch_at=NOW,
            last_touch_at=NOW,
            expires_at=NOW + timedelta(hours=1),
        )
        handoff = AcquisitionHandoff(
            id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            token_hash=handoff_token_hash(raw_handle),
            acquisition_session_id=acquisition.id,
            purpose="checkout",
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=20),
        )
        session.add_all([acquisition, handoff])
        session.commit()

        kind, value = offer_service.resolve_acquisition_offer_subject(
            session, raw_handle=raw_handle, now=NOW
        )
        assert (kind, value) == ("acquisition_session", acquisition.id)
        assert handoff.impression_public_id.startswith("imp_")
        assert handoff.click_public_id.startswith("clk_")
        binding = offer_service.commercial_subject_binding(
            campaign_public_id="cmp_" + "f" * 32,
            subject_kind=kind,
            subject_value=value,
            secret=SECRET,
        )
        assert len(binding) == 64
        assert value not in binding
    finally:
        session.close()
        engine.dispose()


def test_additive_migration_creates_offer_lineage_tables_and_unique_reservation_owner() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for table in (
            "commercial_reservations",
            "commercial_assignments",
            "commercial_creatives",
            "commercial_offers",
        ):
            connection.exec_driver_sql(f"DROP TABLE {table}")

    run_migrations(engine)
    schema = inspect(engine)
    assert {
        "commercial_offers",
        "commercial_creatives",
        "commercial_assignments",
        "commercial_reservations",
    } <= set(schema.get_table_names())
    reservation_columns = {
        item["name"] for item in schema.get_columns("commercial_reservations")
    }
    assert {
        "subject_hmac",
        "commercial_revision",
        "campaign_revision",
        "hold_expires_at",
        "offer_ends_at",
        "token_sha256",
        "bound_order_id",
        "impression_public_id",
        "click_public_id",
    } <= reservation_columns
    unique_constraints = {
        item["name"] for item in schema.get_unique_constraints("commercial_reservations")
    }
    assert "uq_commercial_reservation_assignment" in unique_constraints
    engine.dispose()
