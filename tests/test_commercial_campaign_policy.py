from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from commercial_campaign_policy import (  # noqa: E402
    CAMPAIGN_CHANNELS,
    CAMPAIGN_LEGAL_PROFILE_STATUSES,
    CAMPAIGN_LIFECYCLE_STATUSES,
    CAMPAIGN_OBJECTIVES,
    CAMPAIGN_POLICY_REASONS,
    CAMPAIGN_STATE_REASONS,
    active_entitlement_capacity_units,
    capacity_snapshot,
    evaluate_campaign_policy,
)
from commercial_contract import get_commercial_contract  # noqa: E402
from models import Base, EntitlementGrant  # noqa: E402
from migrations import run_migrations  # noqa: E402


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _ready_contract() -> dict:
    contract = copy.deepcopy(get_commercial_contract())
    contract["legal"].update(
        {
            "seller_publication_status": "published",
            "offer_review_status": "approved",
            "rf_advertising_status": "owner_approved",
            "allowed_launch_channels": ["owned_web", "rf_advertising"],
            "launch_ready": True,
        }
    )
    return contract


def _campaign(**overrides) -> dict:
    contract = _ready_contract()
    value = {
        "public_id": "cmp_" + "a" * 32,
        "objective": "acquisition",
        "lifecycle_status": "live",
        "revision": 1,
        "commercial_revision": contract["commercial_revision"],
        "legal_profile_status": "owner_approved",
        "channels": ["owned_web"],
        "seller_profile_id": "seller-owner-approved-v1",
        "terms_revision": contract["terms_revision"],
        "paid_cap": 25,
        "paid_conversions_count": 0,
        "capacity_guard_enabled": True,
        "capacity_band": "green",
        "state_reason": "ready",
        "starts_at": NOW - timedelta(days=1),
        "ends_at": NOW + timedelta(days=1),
    }
    value.update(overrides)
    return value


def test_campaign_policy_vocabularies_are_closed_and_disjoint_where_required() -> None:
    assert CAMPAIGN_OBJECTIVES == {
        "acquisition",
        "winback",
        "retention",
        "renewal",
        "recovery",
    }
    assert {"draft", "live", "paused", "killed"} <= CAMPAIGN_LIFECYCLE_STATUSES
    assert CAMPAIGN_LEGAL_PROFILE_STATUSES == {
        "missing",
        "pending_owner_review",
        "owner_approved",
        "rejected",
    }
    assert "rf_advertising" in CAMPAIGN_CHANNELS
    assert "owner_killed" in CAMPAIGN_STATE_REASONS
    assert "capacity_resume_hysteresis" in CAMPAIGN_POLICY_REASONS
    assert {"owned_app", "owned_cabinet", "consented_email"} <= CAMPAIGN_CHANNELS
    assert "pilot_binding_missing" in CAMPAIGN_POLICY_REASONS


def test_winback_campaign_is_blocked_without_exact_pilot_binding() -> None:
    contract = _ready_contract()
    contract["legal"]["allowed_launch_channels"] = ["owned_app"]
    decision = evaluate_campaign_policy(
        _campaign(
            objective="winback",
            channels=["owned_app"],
            starts_at=NOW,
            ends_at=NOW + timedelta(hours=72),
            paid_cap=20,
        ),
        active_units=10,
        contract=contract,
        now=NOW + timedelta(hours=1),
    )
    assert decision["activation_allowed"] is False
    assert "pilot_binding_missing" in decision["blocking_reasons"]


def test_repository_contract_blocks_live_campaign_without_claiming_legal_readiness() -> None:
    decision = evaluate_campaign_policy(
        _campaign(),
        active_units=0,
        contract=get_commercial_contract(),
        now=NOW,
    )

    assert decision["activation_allowed"] is False
    assert decision["effective_status"] == "blocked"
    assert decision["reason_code"] == "legal_launch_blocked"
    assert "offer_not_approved" in decision["blocking_reasons"]
    assert "channel_not_allowed" in decision["blocking_reasons"]


def test_owner_approved_ready_contract_allows_bounded_campaign_only() -> None:
    contract = _ready_contract()
    decision = evaluate_campaign_policy(
        _campaign(),
        active_units=149,
        contract=contract,
        now=NOW,
    )

    assert decision["activation_allowed"] is True
    assert decision["effective_status"] == "live"
    assert decision["reason_code"] == "ready"
    assert decision["capacity"]["band"] == "green"
    assert decision["capacity"]["limit_units"] == 300

    no_cap = evaluate_campaign_policy(
        _campaign(paid_cap=0),
        active_units=149,
        contract=contract,
        now=NOW,
    )
    assert no_cap["activation_allowed"] is False
    assert "paid_cap_missing" in no_cap["blocking_reasons"]


def test_capacity_bands_hysteresis_and_renewal_recovery_exemption() -> None:
    contract = _ready_contract()
    assert capacity_snapshot(active_units=149, contract=contract).band == "green"
    assert capacity_snapshot(active_units=150, contract=contract).band == "yellow"
    assert capacity_snapshot(active_units=210, contract=contract).band == "orange"
    assert capacity_snapshot(active_units=255, contract=contract).band == "red"
    assert capacity_snapshot(active_units=300, contract=contract).band == "hold"

    blocked = evaluate_campaign_policy(
        _campaign(), active_units=210, contract=contract, now=NOW
    )
    assert "capacity_forbidden" in blocked["blocking_reasons"]

    hysteresis = evaluate_campaign_policy(
        _campaign(),
        active_units=195,
        contract=contract,
        now=NOW,
        resuming_from_capacity_pause=True,
    )
    assert "capacity_resume_hysteresis" in hysteresis["blocking_reasons"]

    resumed = evaluate_campaign_policy(
        _campaign(),
        active_units=194,
        contract=contract,
        now=NOW,
        resuming_from_capacity_pause=True,
    )
    assert resumed["activation_allowed"] is True

    for objective in ("renewal", "recovery"):
        exempt = evaluate_campaign_policy(
            _campaign(objective=objective, capacity_guard_enabled=False),
            active_units=300,
            contract=contract,
            now=NOW,
        )
        assert exempt["activation_allowed"] is True
        assert exempt["capacity_exempt"] is True


def test_active_entitlement_capacity_counts_distinct_active_accounts() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    try:
        for grant_id, account_id, status, reversed_at, expires_at in (
            ("g1", "account-a", "active", None, NOW + timedelta(days=1)),
            ("g2", "account-a", "grace", None, NOW + timedelta(days=2)),
            ("g3", "account-b", "active", None, None),
            ("g4", "account-c", "active", NOW, NOW + timedelta(days=1)),
            ("g5", "account-d", "active", None, NOW - timedelta(seconds=1)),
            ("g6", "account-e", "reserved", None, NOW + timedelta(days=1)),
        ):
            session.add(
                EntitlementGrant(
                    id=grant_id,
                    account_id=account_id,
                    idempotency_key=f"capacity:{grant_id}",
                    source="test",
                    status=status,
                    grant_kind="paid_access",
                    starts_at=NOW - timedelta(days=1),
                    expires_at=expires_at,
                    reversed_at=reversed_at,
                    metadata_json=json.dumps({"test": True}),
                )
            )
        session.flush()
        assert active_entitlement_capacity_units(session, now=NOW) == 2
    finally:
        session.close()
        engine.dispose()


def test_legacy_incentive_campaign_table_receives_additive_policy_columns() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE incentive_campaigns"))
        connection.execute(
            text(
                """
                CREATE TABLE incentive_campaigns (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name VARCHAR(120) NOT NULL,
                  campaign_type VARCHAR(16) NOT NULL,
                  target_value VARCHAR(64) NOT NULL,
                  segment VARCHAR(32) DEFAULT 'all_active',
                  starts_at DATETIME,
                  ends_at DATETIME,
                  max_activations INTEGER DEFAULT -1,
                  activations_count INTEGER DEFAULT 0,
                  auto_disable BOOLEAN DEFAULT 1,
                  is_active BOOLEAN DEFAULT 1,
                  created_by BIGINT,
                  metadata_json TEXT,
                  created_at DATETIME NOT NULL,
                  updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                "INSERT INTO incentive_campaigns "
                "(name, campaign_type, target_value, is_active, created_at, updated_at) "
                "VALUES ('legacy', 'promo', 'LEGACY10', 1, :now, :now)"
            ),
            {"now": NOW.replace(tzinfo=None)},
        )

    run_migrations(engine)
    columns = {item["name"] for item in inspect(engine).get_columns("incentive_campaigns")}
    assert {
        "public_id",
        "objective",
        "lifecycle_status",
        "revision",
        "commercial_revision",
        "legal_profile_status",
        "channels_json",
        "seller_profile_id",
        "terms_revision",
        "paid_cap",
        "paid_conversions_count",
        "capacity_guard_enabled",
        "capacity_band",
        "state_reason",
        "last_policy_evaluated_at",
        "killed_at",
    } <= columns
    unique_indexes = {
        item["name"] for item in inspect(engine).get_indexes("incentive_campaigns") if item["unique"]
    }
    assert "uq_incentive_campaigns_public_id" in unique_indexes
    with engine.connect() as connection:
        legacy = connection.execute(
            text(
                "SELECT is_active, lifecycle_status, state_reason "
                "FROM incentive_campaigns WHERE target_value='LEGACY10'"
            )
        ).one()
    assert tuple(legacy) == (0, "draft", "legacy_unclassified")
    engine.dispose()
