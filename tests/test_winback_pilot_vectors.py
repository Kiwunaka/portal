from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from commercial_pilot_service import (  # noqa: E402
    WinbackAudienceFacts,
    WinbackRuntimeContext,
    evaluate_winback_audience,
    evaluate_winback_runtime,
    sticky_holdout_allocation,
)
from marketing_pilot_contract import get_winback_pilot_contract  # noqa: E402


FIXTURE = REPO_ROOT / "tests" / "fixtures" / "winback_pilot_vectors.json"


def _read_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _now(fixture: dict) -> datetime:
    return datetime.fromisoformat(str(fixture["now"]).replace("Z", "+00:00"))


def _audience(now: datetime, changes: dict) -> WinbackAudienceFacts:
    values = {
        "paid_before": True,
        "access_expired_at": now - timedelta(days=14),
        "consented_channels": frozenset({"consented_email", "owned_telegram"}),
    }
    normalized = dict(changes)
    if "access_expired_days_ago" in normalized:
        values["access_expired_at"] = now - timedelta(
            days=int(normalized.pop("access_expired_days_ago"))
        )
    if "consented_channels" in normalized:
        normalized["consented_channels"] = frozenset(normalized["consented_channels"])
    values.update(normalized)
    return WinbackAudienceFacts(**values)


def _runtime(now: datetime, contract: dict, changes: dict) -> WinbackRuntimeContext:
    values = {
        "pilot_revision": contract["revision"],
        "pilot_contract_sha256": contract["contract_sha256"],
        "marketing_governance_revision": contract["marketing_governance_revision"],
        "marketing_governance_sha256": contract["marketing_governance_sha256"],
        "commercial_revision": contract["commercial_revision"],
        "commercial_contract_sha256": contract["commercial_contract_sha256"],
        "pilot_launch_state": "owner_approved_ready",
        "approval_record_id": "fixture-owner-approval",
        "legal_profile_state": "owner_approved",
        "channel_launch_state": "owner_approved",
        "campaign_state": "live",
        "campaign_starts_at": now - timedelta(hours=1),
        "campaign_ends_at": now + timedelta(hours=71),
        "capacity_band": "green",
        "capacity_ratio": 0.25,
        "paid_conversions_count": 0,
        "creative_count": 2,
        "holdout_percent": 20,
    }
    values.update(changes)
    return WinbackRuntimeContext(**values)


def test_fixture_covers_every_declared_suppression_and_one_eligible_control() -> None:
    fixture = _read_fixture()
    contract = get_winback_pilot_contract()
    observed = {str(row["expected_reason"]) for row in fixture["vectors"]}
    assert observed - {"ready"} == set(contract["suppression"])
    assert sum(row["expected_reason"] == "ready" for row in fixture["vectors"]) == 1


def test_fixture_vectors_are_deterministic_and_fail_closed() -> None:
    fixture = _read_fixture()
    now = _now(fixture)
    contract = get_winback_pilot_contract()
    eligible = evaluate_winback_audience(_audience(now, {}), channel="owned_app", now=now)
    holdout_subject = next(
        f"{index:064x}"
        for index in range(1, 1000)
        if sticky_holdout_allocation(
            subject_hmac=f"{index:064x}",
            pilot_id=contract["pilot_id"],
            holdout_percent=20,
        )["cohort"]
        == "holdout"
    )
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

    for row in fixture["vectors"]:
        layer = str(row["layer"])
        expected = str(row["expected_reason"])
        if layer == "audience":
            result = evaluate_winback_audience(
                _audience(now, dict(row["changes"])),
                channel=str(row.get("channel") or "owned_app"),
                now=now,
            )
        else:
            result = evaluate_winback_runtime(
                audience=eligible,
                subject_hmac=holdout_subject if layer == "runtime_holdout" else exposed_subject,
                context=_runtime(now, contract, dict(row["changes"])),
                now=now,
            )
        assert result["reason_code"] == expected, row["id"]
        if layer == "audience":
            assert (result.get("eligible") is True) == (expected == "ready"), row["id"]
        else:
            assert (result.get("exposure_allowed") is True) == (expected == "ready"), row["id"]
