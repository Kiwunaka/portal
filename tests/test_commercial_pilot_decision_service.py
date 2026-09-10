from __future__ import annotations

import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from commercial_pilot_decision_service import (  # noqa: E402
    WINBACK_DECISION_STATES,
    build_winback_decision_pack,
    build_winback_postmortem,
)
from marketing_pilot_contract import get_winback_pilot_contract  # noqa: E402
from scripts.generate_winback_postmortem import generate_postmortem  # noqa: E402


NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def _pilot(*, approved: bool) -> dict:
    value = copy.deepcopy(get_winback_pilot_contract())
    value["state"] = "owner_approved_ready" if approved else "draft_blocked"
    return value


def _campaign(*, ended_days_ago: int = 31) -> dict:
    return {
        "public_id": "cmp_" + "a" * 32,
        "revision": 4,
        "lifecycle_status": "ended",
        "ends_at": NOW - timedelta(days=ended_days_ago),
    }


def _guardrails(**changes) -> dict:
    value = {
        "legal_capacity_policy": {"activation_allowed": True, "blocking_reasons": []},
        "quota": {"paid_conversions": 20, "paid_cap": 50, "remaining": 30},
        "payment_errors": {"state": "ready", "count": 0, "order_count": 20},
        "support": {"state": "ready", "ticket_count": 0, "p0_p1_count": 0},
        "incidents": {"state": "ready", "count": 0, "confirmed_open_count": 0},
        "promo_telemetry": {
            "state": "advisory_only",
            "counts": {"promo_impression": 100, "promo_click": 50},
            "can_select_winner": False,
        },
    }
    value.update(changes)
    return value


def _attribution(*, mature: bool = True) -> dict:
    return {
        "variant_cohorts": (
            [
                {
                    "campaign_id": "cmp_" + "a" * 32,
                    "variant": "a",
                    "cohort": "exposed",
                    "metric_state": "ready",
                    "matured_paid_conversions": 10,
                    "net_revenue_30d_rub": 5400,
                    "paid_capacity_units": 10,
                    "net_revenue_30d_per_capacity_unit": 540.0,
                },
                {
                    "campaign_id": "cmp_" + "a" * 32,
                    "variant": "b",
                    "cohort": "exposed",
                    "metric_state": "ready",
                    "matured_paid_conversions": 10,
                    "net_revenue_30d_rub": 4800,
                    "paid_capacity_units": 10,
                    "net_revenue_30d_per_capacity_unit": 480.0,
                },
            ]
            if mature
            else []
        ),
        "holdout": {
            "state": "insufficient_data",
            "reason": "holdout_outcomes_require_separate_identity_free_observation_projection",
            "fabricated_zero": False,
        },
    }


def test_decision_vocabulary_is_closed_and_draft_is_automatic_stop() -> None:
    assert WINBACK_DECISION_STATES == {
        "stop",
        "continue_collecting",
        "keep",
        "change_copy",
        "change_audience",
        "change_benefit",
        "disable",
        "owner_review_scale_50",
    }
    pack = build_winback_decision_pack(
        campaign=_campaign(),
        attribution=_attribution(),
        guardrails=_guardrails(),
        now=NOW,
        pilot_contract=_pilot(approved=False),
        holdout_evidence={"state": "ready", "subjects": 100},
    )
    assert pack["recommendation"] == "stop"
    assert pack["automatic_stop_reasons"] == ["pilot_not_owner_approved"]
    assert pack["winner"] is None
    assert pack["scale_automatic"] is False


def test_decision_returns_insufficient_collection_without_matured_or_holdout_evidence() -> None:
    pack = build_winback_decision_pack(
        campaign=_campaign(ended_days_ago=3),
        attribution=_attribution(mature=False),
        guardrails=_guardrails(),
        now=NOW,
        pilot_contract=_pilot(approved=True),
    )
    assert pack["recommendation"] == "continue_collecting"
    assert pack["primary_metric"]["state"] == "insufficient_data"
    assert pack["primary_metric"]["value"] is None
    assert pack["holdout"]["fabricated_zero"] is False
    assert pack["winner"] is None


def test_matured_server_metric_can_only_request_owner_scale_review() -> None:
    pack = build_winback_decision_pack(
        campaign=_campaign(),
        attribution=_attribution(),
        guardrails=_guardrails(),
        now=NOW,
        pilot_contract=_pilot(approved=True),
        holdout_evidence={
            "state": "ready",
            "subjects": 20,
            "net_revenue_30d_per_capacity_unit": 300.0,
        },
    )
    assert pack["recommendation"] == "owner_review_scale_50"
    assert pack["winner"] == {
        "variant": "a",
        "metric": "net_revenue_30d_per_capacity_unit",
        "value": 540.0,
        "basis": "matured_server_payment_and_capacity_projection",
    }
    assert pack["winner_can_be_selected_from_ctr"] is False
    assert pack["maximum_owner_review_paid_cap"] == 50
    assert pack["scale_automatic"] is False
    postmortem = build_winback_postmortem(pack)
    assert postmortem["winner_state"] == "ready"
    assert postmortem["winner"]["variant"] == "a"
    assert postmortem["scale_requires_owner_approval"] is True


@pytest.mark.parametrize(
    ("scenario", "recommendation"),
    [("missing_variant", "continue_collecting"), ("tie", "keep"), ("window_open", "continue_collecting")],
)
def test_winner_requires_a_complete_unambiguous_comparison(scenario: str, recommendation: str) -> None:
    attribution = _attribution()
    if scenario == "missing_variant":
        attribution["variant_cohorts"].pop()
    elif scenario == "tie":
        attribution["variant_cohorts"][1]["net_revenue_30d_rub"] = 5400
        attribution["variant_cohorts"][1]["net_revenue_30d_per_capacity_unit"] = 540.0
    pack = build_winback_decision_pack(
        campaign=_campaign(ended_days_ago=3 if scenario == "window_open" else 31),
        attribution=attribution,
        guardrails=_guardrails(),
        now=NOW,
        pilot_contract=_pilot(approved=True),
        holdout_evidence={"state": "ready", "subjects": 20},
    )
    assert pack["winner"] is None
    assert pack["recommendation"] == recommendation
    assert build_winback_postmortem(pack)["winner"] is None


def test_incident_and_p0_p1_support_force_stop_and_postmortem_refuses_winner() -> None:
    pack = build_winback_decision_pack(
        campaign=_campaign(),
        attribution=_attribution(),
        guardrails=_guardrails(
            incidents={"state": "ready", "count": 1, "confirmed_open_count": 1},
            support={"state": "ready", "ticket_count": 1, "p0_p1_count": 1},
        ),
        now=NOW,
        pilot_contract=_pilot(approved=True),
        holdout_evidence={"state": "ready", "subjects": 20},
    )
    assert pack["recommendation"] == "stop"
    assert pack["winner"] is None
    assert pack["automatic_stop_reasons"] == [
        "incident_guard_failed",
        "p0_p1_support_guard_failed",
    ]
    postmortem = build_winback_postmortem(pack)
    assert postmortem["winner_state"] == "insufficient_data"
    assert postmortem["winner"] is None
    assert postmortem["impressions_clicks_ctr_can_select_winner"] is False
    assert postmortem["first_payments_can_select_winner"] is False


def test_machine_readable_generator_refuses_click_only_winner(tmp_path: Path) -> None:
    pack = build_winback_decision_pack(
        campaign=_campaign(ended_days_ago=3),
        attribution=_attribution(mature=False),
        guardrails=_guardrails(),
        now=NOW,
        pilot_contract=_pilot(approved=True),
    )
    path = tmp_path / "decision.json"
    path.write_text(json.dumps(pack), encoding="utf-8")
    postmortem = generate_postmortem(json.loads(path.read_text(encoding="utf-8")))
    assert postmortem["winner_state"] == "insufficient_data"
    assert postmortem["winner"] is None
    assert "winner_requires_matured_net_revenue_30d_per_capacity_unit" in postmortem["refusal_reasons"]
