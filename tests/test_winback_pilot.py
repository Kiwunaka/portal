from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
PORTAL_ROOT = REPO_ROOT / "portal_bot"
for root in (SCRIPTS_ROOT, PORTAL_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

import generate_winback_pilot as generator  # noqa: E402
from commercial_pilot_service import (  # noqa: E402
    WinbackAudienceFacts,
    WinbackRuntimeContext,
    campaign_pilot_metadata,
    evaluate_campaign_pilot_binding,
    evaluate_winback_audience,
    evaluate_winback_runtime,
    sticky_holdout_allocation,
)
from marketing_pilot_contract import (  # noqa: E402
    clear_winback_pilot_contract_cache,
    get_winback_pilot_contract,
)


NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _audience(**changes) -> WinbackAudienceFacts:
    values = {
        "paid_before": True,
        "access_expired_at": NOW - timedelta(days=14),
        "consented_channels": frozenset({"consented_email", "owned_telegram"}),
    }
    values.update(changes)
    return WinbackAudienceFacts(**values)


def _runtime(contract: dict, **changes) -> WinbackRuntimeContext:
    values = {
        "pilot_revision": contract["revision"],
        "pilot_contract_sha256": contract["contract_sha256"],
        "marketing_governance_revision": contract["marketing_governance_revision"],
        "marketing_governance_sha256": contract["marketing_governance_sha256"],
        "commercial_revision": contract["commercial_revision"],
        "commercial_contract_sha256": contract["commercial_contract_sha256"],
        "pilot_launch_state": "owner_approved_ready",
        "approval_record_id": "legal-owner-approval-2026-08-22",
        "legal_profile_state": "owner_approved",
        "channel_launch_state": "owner_approved",
        "campaign_state": "live",
        "campaign_starts_at": NOW - timedelta(hours=1),
        "campaign_ends_at": NOW + timedelta(hours=71),
        "capacity_band": "green",
        "capacity_ratio": 0.25,
        "paid_conversions_count": 0,
        "creative_count": 2,
        "holdout_percent": 20,
    }
    values.update(changes)
    return WinbackRuntimeContext(**values)


def test_generated_pilot_is_current_exact_and_launch_blocked() -> None:
    expected = generator.build_contract(
        _read(generator.SOURCE_PATH),
        _read(generator.COMMERCIAL_PATH),
        _read(generator.GOVERNANCE_PATH),
    )
    actual = _read(generator.OUTPUT_PATH)
    assert actual == expected
    assert actual["state"] == "draft_blocked"
    assert actual["holdout"]["percentage"] is None
    assert actual["offer"] == {
        "plans": [
            {
                "plan_code": "3_months",
                "base_amount_rub": 669,
                "final_amount_rub": 602,
                "capacity_cost_units": 1,
            },
            {
                "plan_code": "6_months",
                "base_amount_rub": 1199,
                "final_amount_rub": 1079,
                "capacity_cost_units": 1,
            },
        ],
        "discount_percent": 10,
        "duration_hours": 72,
        "paid_cap": 20,
        "per_subject_paid_cap": 1,
        "stacking_allowed": False,
    }
    assert len(actual["creatives"]) == 2
    assert actual["decision"]["ctr_can_select_winner"] is False
    schema = _read(
        REPO_ROOT
        / "shared"
        / "contracts"
        / "marketing"
        / "winback-pilot.v1.schema.json"
    )
    assert schema["additionalProperties"] is False
    assert schema["properties"]["offer"]["additionalProperties"] is False
    assert schema["properties"]["holdout"]["properties"]["percentage"] == {
        "type": "null"
    }


def test_generator_rejects_scope_expansion_and_fake_approval() -> None:
    source = _read(generator.SOURCE_PATH)
    commercial = _read(generator.COMMERCIAL_PATH)
    governance = _read(generator.GOVERNANCE_PATH)
    expanded = copy.deepcopy(source)
    expanded["offer"]["plan_codes"].append("12_months")
    with pytest.raises(generator.WinbackPilotError, match="3_and_6_months"):
        generator.build_contract(expanded, commercial, governance)
    approved = copy.deepcopy(source)
    approved["holdout"]["percentage"] = 20
    with pytest.raises(generator.WinbackPilotError, match="holdout_owner_decision"):
        generator.build_contract(approved, commercial, governance)


def test_runtime_adapter_validates_dependency_and_source_digests() -> None:
    clear_winback_pilot_contract_cache()
    contract = get_winback_pilot_contract()
    assert contract["schema_version"] == "pokrov-winback-pilot-v1"
    assert contract["contract_sha256"] == _read(generator.OUTPUT_PATH)["contract_sha256"]


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"paid_before": False}, "paid_history_missing"),
        ({"current_access_active": True}, "current_access_active"),
        ({"access_expired_at": None}, "access_expiry_missing"),
        ({"access_expired_at": NOW - timedelta(days=6, hours=23)}, "expired_window_mismatch"),
        ({"access_expired_at": NOW - timedelta(days=30, seconds=1)}, "expired_window_mismatch"),
        ({"refund_dispute_open": True}, "refund_dispute_open"),
        ({"unresolved_payment": True}, "unresolved_payment"),
        ({"unresolved_support": True}, "unresolved_support"),
        ({"payment_already_consumed": True}, "payment_already_consumed"),
        ({"owner_suppressed": True}, "owner_suppressed"),
    ],
)
def test_audience_suppression_reasons_are_closed(changes: dict, reason: str) -> None:
    result = evaluate_winback_audience(_audience(**changes), channel="owned_app", now=NOW)
    assert result["eligible"] is False
    assert reason in result["blocking_reasons"]


def test_audience_window_is_inclusive_and_consent_is_channel_specific() -> None:
    for days in (7, 30):
        result = evaluate_winback_audience(
            _audience(access_expired_at=NOW - timedelta(days=days)),
            channel="owned_app",
            now=NOW,
        )
        assert result["eligible"] is True
    blocked = evaluate_winback_audience(
        _audience(consented_channels=frozenset()),
        channel="consented_email",
        now=NOW,
    )
    assert blocked["blocking_reasons"] == ["channel_consent_missing"]


def test_holdout_allocation_is_sticky_and_has_no_identity_output() -> None:
    subject = "a" * 64
    first = sticky_holdout_allocation(
        subject_hmac=subject,
        pilot_id="release_1_2_winback_paid_7_30d",
        holdout_percent=20,
    )
    second = sticky_holdout_allocation(
        subject_hmac=subject,
        pilot_id="release_1_2_winback_paid_7_30d",
        holdout_percent=20,
    )
    assert first == second
    assert set(first) == {"cohort", "bucket", "threshold", "algorithm"}
    assert subject not in json.dumps(first)


def test_runtime_requires_exact_binding_approval_holdout_capacity_and_window() -> None:
    contract = get_winback_pilot_contract()
    audience = evaluate_winback_audience(_audience(), channel="owned_app", now=NOW)
    exposed_subject = next(
        f"{index:064x}"
        for index in range(1, 1000)
        if sticky_holdout_allocation(
            subject_hmac=f"{index:064x}",
            pilot_id=contract["pilot_id"],
            holdout_percent=20,
        )["cohort"]
        == "exposed"
    )
    ready = evaluate_winback_runtime(
        audience=audience,
        subject_hmac=exposed_subject,
        context=_runtime(contract),
        now=NOW,
    )
    assert ready["exposure_allowed"] is True
    assert ready["reason_code"] == "ready"

    cases = (
        ({"pilot_contract_sha256": "0" * 64}, "pilot_binding_stale"),
        ({"approval_record_id": ""}, "pilot_owner_approval_missing"),
        ({"holdout_percent": None}, "pilot_holdout_decision_missing"),
        ({"legal_profile_state": "pending"}, "legal_or_channel_blocked"),
        ({"campaign_ends_at": NOW + timedelta(hours=72)}, "pilot_window_invalid"),
        ({"capacity_band": "orange", "capacity_ratio": 0.7}, "capacity_blocked"),
        ({"paid_conversions_count": 20}, "paid_cap_reached"),
        ({"creative_count": 3}, "creative_count_invalid"),
    )
    for changes, reason in cases:
        result = evaluate_winback_runtime(
            audience=audience,
            subject_hmac=exposed_subject,
            context=_runtime(contract, **changes),
            now=NOW,
        )
        assert result["exposure_allowed"] is False
        assert reason in result["blocking_reasons"]


def test_campaign_metadata_binding_is_fail_closed_and_exact() -> None:
    contract = get_winback_pilot_contract()
    metadata = {
        "marketing_pilot": {
            "pilot_revision": contract["revision"],
            "pilot_contract_sha256": contract["contract_sha256"],
            "marketing_governance_revision": contract["marketing_governance_revision"],
            "marketing_governance_sha256": contract["marketing_governance_sha256"],
            "commercial_revision": contract["commercial_revision"],
            "commercial_contract_sha256": contract["commercial_contract_sha256"],
            "pilot_launch_state": "owner_approved_ready",
            "approval_record_id": "owner-approved-1",
            "holdout_percent": 20,
        }
    }
    row = {
        "objective": "winback",
        "paid_cap": 20,
        "channels": ["owned_app"],
        "starts_at": NOW,
        "ends_at": NOW + timedelta(hours=72),
        "metadata": metadata,
    }
    assert campaign_pilot_metadata(metadata) == metadata["marketing_pilot"]
    assert evaluate_campaign_pilot_binding(row) == []
    assert evaluate_campaign_pilot_binding({**row, "metadata": {}}) == [
        "pilot_binding_missing"
    ]
    stale = copy.deepcopy(row)
    stale["metadata"]["marketing_pilot"]["pilot_contract_sha256"] = "f" * 64
    assert evaluate_campaign_pilot_binding(stale) == ["pilot_binding_stale"]
