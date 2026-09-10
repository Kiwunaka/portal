from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from commercial_contract import get_commercial_contract  # noqa: E402
from commercial_offer_service import commercial_subject_binding  # noqa: E402
from commercial_promo_surface_service import (  # noqa: E402
    commercial_winback_promo_slots,
    validate_commercial_promo_event_lineage,
)
from marketing_pilot_contract import get_winback_pilot_contract  # noqa: E402
from models import (  # noqa: E402
    Base,
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    IncentiveCampaign,
    Node,
)


NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SECRET = "commercial-promo-surface-secret-at-least-32-bytes"


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    session.add(Node(
        code="test-paid", access_role="paid", last_health_at=NOW.replace(tzinfo=None),
        cpu_percent=20, network_tx_mbps_1m=10, packet_loss_percent=0,
    ))
    session.flush()
    return engine, session


def _approved_pilot() -> dict:
    pilot = copy.deepcopy(get_winback_pilot_contract())
    pilot["state"] = "owner_approved_ready"
    return pilot


def _ready_commercial_contract(*, channels: list[str] | None = None) -> dict:
    contract = copy.deepcopy(get_commercial_contract())
    contract["legal"].update(
        {
            "seller_publication_status": "published",
            "offer_review_status": "approved",
            "allowed_launch_channels": channels or ["owned_app"],
            "launch_ready": True,
        }
    )
    return contract


def _pilot_metadata(pilot: dict) -> str:
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
                "approval_record_id": "owner-approval-test-011d",
                "holdout_percent": 1,
            }
        },
        sort_keys=True,
    )


def _seed(
    session,
    *,
    pilot: dict,
    contract: dict,
    tg_id: int = 7711,
    channel: str = "owned_app",
) -> dict:
    campaign = IncentiveCampaign(
        public_id="cmp_" + "a" * 32,
        name="Release 1.2 winback",
        campaign_type="promo",
        target_value="WIN10",
        objective="winback",
        lifecycle_status="live",
        revision=1,
        commercial_revision=contract["commercial_revision"],
        legal_profile_status="owner_approved",
        channels_json=json.dumps([channel]),
        seller_profile_id="seller-owner-approved-v1",
        terms_revision=contract["terms_revision"],
        paid_cap=20,
        paid_conversions_count=0,
        capacity_guard_enabled=True,
        capacity_band="green",
        state_reason="ready",
        segment="expired_paid_7_30d",
        starts_at=NOW - timedelta(hours=1),
        ends_at=NOW + timedelta(hours=71),
        is_active=True,
        metadata_json=_pilot_metadata(pilot),
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(campaign)
    session.flush()
    offer = CommercialOffer(
        public_id="off_" + "b" * 32,
        campaign_id=campaign.id,
        plan_code="3_months",
        status="live",
        commercial_revision=contract["commercial_revision"],
        terms_revision=contract["terms_revision"],
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
        variant_code="a",
        status="live",
        channel=channel,
        content_revision="winback-2026-08-22.1-a",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(creative)
    session.flush()
    assignment = CommercialAssignment(
        public_id="asg_" + "d" * 32,
        campaign_id=campaign.id,
        offer_id=offer.id,
        creative_id=creative.id,
        subject_hmac=commercial_subject_binding(
            campaign_public_id=campaign.public_id,
            subject_kind="telegram",
            subject_value=str(tg_id),
            secret=SECRET,
        ),
        status="active",
        audience_status="eligible",
        audience_reason="ready",
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
        "offer": offer,
        "creative": creative,
        "assignment": assignment,
    }


def test_repository_draft_contract_never_surfaces_live_campaign(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMMERCIAL_OFFER_HMAC_SECRET", SECRET)
    engine, session = _session()
    try:
        pilot = _approved_pilot()
        _seed(session, pilot=pilot, contract=_ready_commercial_contract())
        slots = commercial_winback_promo_slots(
            session,
            tg_id=7711,
            access_state="expired_or_blocked",
            checkout_base_url="https://pay.pokrov.space/checkout/",
            issue_checkout_ticket=lambda **_: "ticket",
            now=NOW,
        )
        assert slots == []
    finally:
        session.close()
        engine.dispose()


def test_approved_assignment_surfaces_exact_lineage_and_checkout_touch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMMERCIAL_OFFER_HMAC_SECRET", SECRET)
    engine, session = _session()
    captured: list[dict] = []
    try:
        pilot = _approved_pilot()
        seeded = _seed(session, pilot=pilot, contract=_ready_commercial_contract())

        def issue(**kwargs):
            captured.append(dict(kwargs))
            return "server-issued-checkout-ticket"

        slots = commercial_winback_promo_slots(
            session,
            tg_id=7711,
            access_state="expired_or_blocked",
            checkout_base_url="https://pay.pokrov.space/checkout/",
            issue_checkout_ticket=issue,
            now=NOW,
            pilot_contract=pilot,
            commercial_contract=_ready_commercial_contract(),
        )
        assert len(slots) == 1
        slot = slots[0]
        assert slot["campaign_id"] == seeded["campaign"].public_id
        assert slot["offer_id"] == seeded["offer"].public_id
        assert slot["creative_id"] == seeded["creative"].public_id
        assert slot["assignment_id"] == seeded["assignment"].public_id
        assert slot["variant"] == "a"
        assert slot["impression_id"] == "imp_" + "d" * 32
        assert slot["click_id"] == "clk_" + "d" * 32
        assert slot["pilot_contract_sha256"] == pilot["contract_sha256"]
        assert slot["base_price_rub"] == 669
        assert slot["final_price_rub"] == 602
        assert slot["remaining_quota_lower_bound"] == 20
        assert slot["terms_url"] == "https://pokrov.space/offer/"
        assert "checkout_ticket=server-issued-checkout-ticket" in slot["cta_href"]
        assert captured == [
            {
                "tg_id": 7711,
                "plan_code": "3_months",
                "promo_code": "WIN10",
                "campaign_key": seeded["campaign"].public_id,
                "source": "app",
                "impression_public_id": slot["impression_id"],
                "click_public_id": slot["click_id"],
            }
        ]

        lineage = validate_commercial_promo_event_lineage(
            session,
            tg_id=7711,
            meta={key: slot[key] for key in (
                "pilot_id",
                "pilot_revision",
                "pilot_contract_sha256",
                "commercial_revision",
                "campaign_id",
                "offer_id",
                "creative_id",
                "variant",
                "assignment_id",
                "impression_id",
                "click_id",
            )},
            pilot_contract=pilot,
        )
        assert lineage is not None
        assert lineage["assignment_id"] == slot["assignment_id"]
    finally:
        session.close()
        engine.dispose()


def test_owned_cabinet_surface_uses_webapp_slot_and_bound_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMMERCIAL_OFFER_HMAC_SECRET", SECRET)
    engine, session = _session()
    captured: list[dict] = []
    try:
        pilot = _approved_pilot()
        contract = _ready_commercial_contract(channels=["owned_cabinet"])
        _seed(session, pilot=pilot, contract=contract, channel="owned_cabinet")

        slots = commercial_winback_promo_slots(
            session,
            tg_id=7711,
            access_state="expired_or_blocked",
            surface="webapp",
            checkout_base_url="https://pay.pokrov.space/checkout/",
            issue_checkout_ticket=lambda **kwargs: captured.append(dict(kwargs)) or "ticket",
            now=NOW,
            pilot_contract=pilot,
            commercial_contract=contract,
        )

        assert len(slots) == 1
        assert slots[0]["slot_id"] == "webapp.subscription.contextual"
        assert slots[0]["placement"] == "subscription_contextual"
        assert captured[0]["source"] == "webapp"
    finally:
        session.close()
        engine.dispose()


def test_exhausted_offer_quota_never_issues_checkout_ticket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMMERCIAL_OFFER_HMAC_SECRET", SECRET)
    engine, session = _session()
    captured: list[dict] = []
    try:
        pilot = _approved_pilot()
        seeded = _seed(session, pilot=pilot, contract=_ready_commercial_contract())
        seeded["offer"].paid_count = seeded["offer"].paid_cap
        session.commit()

        slots = commercial_winback_promo_slots(
            session,
            tg_id=7711,
            access_state="expired_or_blocked",
            checkout_base_url="https://pay.pokrov.space/checkout/",
            issue_checkout_ticket=lambda **kwargs: captured.append(dict(kwargs)) or "ticket",
            now=NOW,
            pilot_contract=pilot,
            commercial_contract=_ready_commercial_contract(),
        )

        assert slots == []
        assert captured == []
    finally:
        session.close()
        engine.dispose()


def test_lineage_validation_rejects_partial_stale_and_wrong_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMMERCIAL_OFFER_HMAC_SECRET", SECRET)
    engine, session = _session()
    try:
        pilot = _approved_pilot()
        _seed(session, pilot=pilot, contract=_ready_commercial_contract())
        with pytest.raises(ValueError, match="commercial_promo_lineage_incomplete"):
            validate_commercial_promo_event_lineage(
                session,
                tg_id=7711,
                meta={"campaign_id": "cmp_" + "a" * 32},
                pilot_contract=pilot,
            )
        complete = {
            "pilot_id": pilot["pilot_id"],
            "pilot_revision": pilot["revision"],
            "pilot_contract_sha256": pilot["contract_sha256"],
            "commercial_revision": pilot["commercial_revision"],
            "campaign_id": "cmp_" + "a" * 32,
            "offer_id": "off_" + "b" * 32,
            "creative_id": "crv_" + "c" * 32,
            "variant": "a",
            "assignment_id": "asg_" + "d" * 32,
            "impression_id": "imp_" + "d" * 32,
            "click_id": "clk_" + "d" * 32,
        }
        with pytest.raises(ValueError, match="commercial_promo_lineage_stale"):
            validate_commercial_promo_event_lineage(
                session,
                tg_id=7711,
                meta={**complete, "pilot_revision": "stale"},
                pilot_contract=pilot,
            )
        with pytest.raises(ValueError, match="commercial_promo_lineage_conflict"):
            validate_commercial_promo_event_lineage(
                session,
                tg_id=7712,
                meta=complete,
                pilot_contract=pilot,
            )
    finally:
        session.close()
        engine.dispose()
