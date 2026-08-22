from __future__ import annotations

import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from commercial_capacity_service import (  # noqa: E402
    COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA,
    COMMERCIAL_CAPACITY_POLICY_ID,
    commercial_capacity_readback,
    run_commercial_capacity_evaluation,
)
from commercial_contract import get_commercial_contract  # noqa: E402
from models import (  # noqa: E402
    AdminAudit,
    Base,
    CommercialAssignment,
    CommercialCreative,
    CommercialOffer,
    CommercialReservation,
    IncentiveCampaign,
)


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _ready_contract() -> dict:
    contract = copy.deepcopy(get_commercial_contract())
    contract["legal"].update(
        {
            "seller_publication_status": "published",
            "offer_review_status": "approved",
            "rf_advertising_status": "owner_approved",
            "allowed_launch_channels": ["owned_web"],
            "launch_ready": True,
        }
    )
    return contract


def _campaign(contract: dict, *, suffix: str, objective: str = "acquisition") -> IncentiveCampaign:
    return IncentiveCampaign(
        public_id="cmp_" + suffix * 32,
        name=f"capacity-{suffix}",
        campaign_type="promo",
        target_value=f"CAP{suffix.upper()}",
        objective=objective,
        lifecycle_status="live",
        revision=1,
        commercial_revision=contract["commercial_revision"],
        legal_profile_status="owner_approved",
        channels_json='["owned_web"]',
        seller_profile_id="seller-owner-approved-v1",
        terms_revision=contract["terms_revision"],
        paid_cap=20,
        paid_conversions_count=3,
        capacity_guard_enabled=True,
        capacity_band="green",
        state_reason="ready",
        starts_at=(NOW - timedelta(days=1)).replace(tzinfo=None),
        ends_at=(NOW + timedelta(days=2)).replace(tzinfo=None),
        max_activations=20,
        activations_count=0,
        auto_disable=True,
        is_active=True,
        created_at=NOW.replace(tzinfo=None),
        updated_at=NOW.replace(tzinfo=None),
    )


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, future=True)()


def test_auto_pause_hysteresis_resume_and_exempt_objectives_are_audited() -> None:
    contract = _ready_contract()
    engine, session = _session()
    try:
        acquisition = _campaign(contract, suffix="a")
        renewal = _campaign(contract, suffix="b", objective="renewal")
        recovery = _campaign(contract, suffix="c", objective="recovery")
        session.add_all([acquisition, renewal, recovery])
        session.flush()

        dry_run = run_commercial_capacity_evaluation(
            session,
            now=NOW,
            contract=contract,
            active_units=210,
            apply=False,
        )
        assert dry_run["schema"] == COMMERCIAL_CAPACITY_AUTOMATION_SCHEMA
        assert dry_run["policy_id"] == COMMERCIAL_CAPACITY_POLICY_ID
        assert dry_run["transition_count"] == 1
        assert dry_run["transitions"][0]["action"] == "pause"
        assert acquisition.lifecycle_status == "live"
        assert session.query(AdminAudit).count() == 0

        paused = run_commercial_capacity_evaluation(
            session,
            now=NOW,
            contract=contract,
            active_units=210,
            apply=True,
        )
        assert paused["transition_count"] == 1
        assert acquisition.lifecycle_status == "paused"
        assert acquisition.state_reason == "capacity_forbidden"
        assert acquisition.is_active is False
        assert acquisition.revision == 2
        assert renewal.lifecycle_status == "live"
        assert recovery.lifecycle_status == "live"

        held = run_commercial_capacity_evaluation(
            session,
            now=NOW + timedelta(minutes=1),
            contract=contract,
            active_units=195,
            apply=True,
        )
        assert held["transitions"][0]["action"] == "hold"
        assert acquisition.lifecycle_status == "paused"
        assert acquisition.state_reason == "capacity_resume_hysteresis"
        assert acquisition.revision == 3

        resumed = run_commercial_capacity_evaluation(
            session,
            now=NOW + timedelta(minutes=2),
            contract=contract,
            active_units=194,
            apply=True,
        )
        assert resumed["transitions"][0]["action"] == "resume"
        assert acquisition.lifecycle_status == "live"
        assert acquisition.state_reason == "ready"
        assert acquisition.is_active is True
        assert acquisition.revision == 4
        assert [row.action for row in session.query(AdminAudit).order_by(AdminAudit.id)] == [
            "capacity.auto_pause",
            "capacity.auto_hold",
            "capacity.auto_resume",
        ]
    finally:
        session.close()
        engine.dispose()


def test_forecast_exposes_revision_thresholds_caps_reservations_and_paid_counts() -> None:
    contract = _ready_contract()
    for plan in contract["plans"]:
        if plan["code"] == "1_month":
            plan["capacity_cost_units"] = 2
    engine, session = _session()
    try:
        campaign = _campaign(contract, suffix="d")
        session.add(campaign)
        session.flush()
        offer = CommercialOffer(
            campaign_id=campaign.id,
            plan_code="1_month",
            status="live",
            commercial_revision=contract["commercial_revision"],
            terms_revision=contract["terms_revision"],
            currency="RUB",
            base_amount_rub=239,
            final_amount_rub=215,
            stackable_with_base_savings=False,
            paid_cap=20,
            paid_count=3,
            per_subject_paid_cap=1,
            starts_at=(NOW - timedelta(days=1)).replace(tzinfo=None),
            ends_at=(NOW + timedelta(days=1)).replace(tzinfo=None),
        )
        session.add(offer)
        session.flush()

        for index, (status, hold_offset) in enumerate(
            (("held", 5), ("bound", -5), ("held", -5)),
            start=1,
        ):
            creative = CommercialCreative(
                campaign_id=campaign.id,
                offer_id=offer.id,
                variant_code=f"v{index}",
                status="active",
                channel="owned_web",
                content_revision="copy-v1",
            )
            session.add(creative)
            session.flush()
            assignment = CommercialAssignment(
                campaign_id=campaign.id,
                offer_id=offer.id,
                creative_id=creative.id,
                subject_hmac=str(index) * 64,
                status="active",
                audience_status="eligible",
                audience_reason="ready",
                paid_count=0,
                assigned_at=NOW.replace(tzinfo=None),
                expires_at=(NOW + timedelta(days=1)).replace(tzinfo=None),
            )
            session.add(assignment)
            session.flush()
            session.add(
                CommercialReservation(
                    campaign_id=campaign.id,
                    offer_id=offer.id,
                    creative_id=creative.id,
                    assignment_id=assignment.id,
                    subject_hmac=assignment.subject_hmac,
                    commercial_revision=contract["commercial_revision"],
                    campaign_revision=campaign.revision,
                    status=status,
                    token_version=2,
                    token_sha256=str(index) * 64,
                    base_amount_rub=239,
                    final_amount_rub=215,
                    currency="RUB",
                    issued_at=NOW.replace(tzinfo=None),
                    hold_expires_at=(NOW + timedelta(minutes=hold_offset)).replace(
                        tzinfo=None
                    ),
                    offer_ends_at=(NOW + timedelta(days=1)).replace(tzinfo=None),
                )
            )
        session.flush()

        readback = commercial_capacity_readback(
            session,
            now=NOW,
            contract=contract,
            active_units=100,
        )
        assert readback["commercial_revision"] == contract["commercial_revision"]
        assert readback["contract_sha256"] == contract["contract_sha256"]
        assert readback["capacity"]["authority"] == "active_entitlement_projection"
        assert readback["forecast"] == {
            "authority": "active_entitlement_projection",
            "active_units": 100,
            "pending_reservation_units": 4,
            "projected_units_if_pending_convert": 104,
            "projected_ratio_if_pending_convert": 0.346667,
            "available_units_now": 200,
            "pause_threshold_units": 210,
            "resume_below_units": 194,
            "gate_reasons": [],
        }
        assert readback["reservation_counts"] == {"bound": 1, "held": 1}
        assert readback["campaigns"][0]["paid_cap"] == 20
        assert readback["campaigns"][0]["paid_count"] == 3
        assert readback["campaigns"][0]["reservation_counts"] == {
            "bound": 1,
            "held": 1,
        }
    finally:
        session.close()
        engine.dispose()


def test_worker_supervises_capacity_automation_with_bounded_interval() -> None:
    worker = (PORTAL_BOT_DIR / "worker.py").read_text(encoding="utf-8")

    assert "COMMERCIAL_CAPACITY_AUTOMATION_ENABLED" in worker
    assert "COMMERCIAL_CAPACITY_AUTOMATION_INTERVAL_SECONDS" in worker
    assert "run_commercial_capacity_evaluation" in worker
    assert "await asyncio.to_thread(_run_commercial_capacity_once)" in worker
    assert '"commercial_capacity_automation"' in worker
    assert "commercial_capacity_automation_job" in worker
