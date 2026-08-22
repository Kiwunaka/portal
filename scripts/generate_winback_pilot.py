from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO_ROOT / "shared" / "winback-pilot.source.json"
COMMERCIAL_PATH = REPO_ROOT / "shared" / "commercial-contract.json"
GOVERNANCE_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "marketing"
    / "marketing-governance.v1.json"
)
OUTPUT_PATH = (
    REPO_ROOT / "shared" / "contracts" / "marketing" / "winback-pilot.v1.json"
)
DOC_PATH = REPO_ROOT / "docs" / "generated" / "winback-pilot.md"
SOURCE_SCHEMA = "pokrov-winback-pilot-source-v1"
OUTPUT_SCHEMA = "pokrov-winback-pilot-v1"
REVISION_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.[1-9][0-9]*$")
ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
PLAN_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{1,31}$")


class WinbackPilotError(ValueError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WinbackPilotError(f"invalid_json:{path.relative_to(REPO_ROOT)}") from exc
    if not isinstance(value, dict):
        raise WinbackPilotError(f"object_required:{path.relative_to(REPO_ROOT)}")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _closed(value: Mapping[str, Any], keys: set[str], *, field: str) -> None:
    unknown = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if unknown:
        raise WinbackPilotError(f"unknown_keys:{field}:{','.join(unknown)}")
    if missing:
        raise WinbackPilotError(f"missing_keys:{field}:{','.join(missing)}")


def _text(value: object, *, field: str, limit: int = 256) -> str:
    normalized = str(value or "").strip()
    if not normalized or len(normalized) > limit:
        raise WinbackPilotError(f"invalid_text:{field}")
    return normalized


def _identifier(value: object, *, field: str) -> str:
    normalized = _text(value, field=field, limit=64).lower()
    if ID_RE.fullmatch(normalized) is None:
        raise WinbackPilotError(f"invalid_identifier:{field}")
    return normalized


def _plan_code(value: object, *, field: str) -> str:
    normalized = _text(value, field=field, limit=32).lower()
    if PLAN_CODE_RE.fullmatch(normalized) is None:
        raise WinbackPilotError(f"invalid_plan_code:{field}")
    return normalized


def _exact_int(value: object, expected: int, *, field: str) -> int:
    if type(value) is not int or int(value) != expected:
        raise WinbackPilotError(f"invalid_value:{field}")
    return expected


def _exact_bool(value: object, expected: bool, *, field: str) -> bool:
    if type(value) is not bool or value is not expected:
        raise WinbackPilotError(f"invalid_value:{field}")
    return expected


def build_contract(
    source: Mapping[str, Any],
    commercial: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    _closed(
        source,
        {
            "schema_version",
            "pilot_id",
            "revision",
            "state",
            "objective",
            "legal_profile_id",
            "channels",
            "audience",
            "offer",
            "creatives",
            "holdout",
            "capacity",
            "suppression",
            "primary_metric",
            "guardrails",
            "decision",
            "external_gates",
        },
        field="source",
    )
    if source.get("schema_version") != SOURCE_SCHEMA:
        raise WinbackPilotError("source_schema_mismatch")
    pilot_id = _identifier(source.get("pilot_id"), field="pilot_id")
    revision = _text(source.get("revision"), field="revision", limit=32)
    if REVISION_RE.fullmatch(revision) is None:
        raise WinbackPilotError("invalid_revision")
    if source.get("state") != "draft_blocked" or source.get("objective") != "winback":
        raise WinbackPilotError("pilot_must_remain_draft_blocked")

    profile_id = _identifier(source.get("legal_profile_id"), field="legal_profile_id")
    profiles = {
        str(item.get("profile_id") or ""): item
        for item in list(governance.get("profiles") or [])
        if isinstance(item, Mapping)
    }
    profile = profiles.get(profile_id)
    if not isinstance(profile, Mapping):
        raise WinbackPilotError("legal_profile_unknown")
    if "blocked" not in str(profile.get("campaign_launch_state") or ""):
        raise WinbackPilotError("repository_profile_must_remain_blocked")
    channels = sorted(
        {_identifier(item, field="channels") for item in list(source.get("channels") or [])}
    )
    if not channels or set(channels) - set(profile.get("allowed_channels") or []):
        raise WinbackPilotError("pilot_channel_not_allowed_by_profile")

    audience = source.get("audience")
    if not isinstance(audience, Mapping):
        raise WinbackPilotError("audience_object_required")
    _closed(
        audience,
        {
            "paid_before",
            "expired_min_days",
            "expired_max_days",
            "current_access_required",
            "refund_dispute_required",
            "unresolved_payment_required",
            "unresolved_support_required",
        },
        field="audience",
    )
    normalized_audience = {
        "paid_before": _exact_bool(audience.get("paid_before"), True, field="audience.paid_before"),
        "expired_min_days": _exact_int(audience.get("expired_min_days"), 7, field="audience.expired_min_days"),
        "expired_max_days": _exact_int(audience.get("expired_max_days"), 30, field="audience.expired_max_days"),
        "current_access_required": _exact_bool(audience.get("current_access_required"), False, field="audience.current_access_required"),
        "refund_dispute_required": _exact_bool(audience.get("refund_dispute_required"), False, field="audience.refund_dispute_required"),
        "unresolved_payment_required": _exact_bool(audience.get("unresolved_payment_required"), False, field="audience.unresolved_payment_required"),
        "unresolved_support_required": _exact_bool(audience.get("unresolved_support_required"), False, field="audience.unresolved_support_required"),
    }

    offer = source.get("offer")
    if not isinstance(offer, Mapping):
        raise WinbackPilotError("offer_object_required")
    _closed(
        offer,
        {
            "plan_codes",
            "discount_percent",
            "duration_hours",
            "paid_cap",
            "per_subject_paid_cap",
            "stacking_allowed",
        },
        field="offer",
    )
    plan_codes = sorted({_plan_code(item, field="offer.plan_codes") for item in list(offer.get("plan_codes") or [])})
    if plan_codes != ["3_months", "6_months"]:
        raise WinbackPilotError("pilot_plan_codes_must_be_3_and_6_months")
    plan_map = {
        str(item.get("code") or ""): item
        for item in list(commercial.get("plans") or [])
        if isinstance(item, Mapping)
    }
    discount = _exact_int(offer.get("discount_percent"), 10, field="offer.discount_percent")
    offer_plans: list[dict[str, Any]] = []
    for code in plan_codes:
        plan = plan_map.get(code)
        if not isinstance(plan, Mapping) or plan.get("is_active") is not True:
            raise WinbackPilotError(f"commercial_plan_unavailable:{code}")
        base = int(plan.get("amount_rub") or 0)
        if base <= 0:
            raise WinbackPilotError(f"commercial_plan_price_invalid:{code}")
        offer_plans.append(
            {
                "plan_code": code,
                "base_amount_rub": base,
                "final_amount_rub": max(1, int(round(base * (100 - discount) / 100))),
                "capacity_cost_units": int(plan.get("capacity_cost_units") or 0),
            }
        )
    normalized_offer = {
        "plans": offer_plans,
        "discount_percent": discount,
        "duration_hours": _exact_int(offer.get("duration_hours"), 72, field="offer.duration_hours"),
        "paid_cap": _exact_int(offer.get("paid_cap"), 20, field="offer.paid_cap"),
        "per_subject_paid_cap": _exact_int(offer.get("per_subject_paid_cap"), 1, field="offer.per_subject_paid_cap"),
        "stacking_allowed": _exact_bool(offer.get("stacking_allowed"), False, field="offer.stacking_allowed"),
    }

    creatives: list[dict[str, str]] = []
    for index, raw in enumerate(source.get("creatives") or []):
        if not isinstance(raw, Mapping):
            raise WinbackPilotError("creative_object_required")
        _closed(raw, {"variant", "title_ru", "body_ru"}, field=f"creatives.{index}")
        creatives.append(
            {
                "variant": _identifier(raw.get("variant"), field=f"creatives.{index}.variant"),
                "title_ru": _text(raw.get("title_ru"), field=f"creatives.{index}.title_ru"),
                "body_ru": _text(raw.get("body_ru"), field=f"creatives.{index}.body_ru"),
            }
        )
    if len(creatives) != 2 or {item["variant"] for item in creatives} != {"a", "b"}:
        raise WinbackPilotError("exactly_two_creatives_required")

    holdout = source.get("holdout")
    if not isinstance(holdout, Mapping):
        raise WinbackPilotError("holdout_object_required")
    _closed(holdout, {"allocation_algorithm", "percentage", "decision_state"}, field="holdout")
    if holdout.get("percentage") is not None or holdout.get("decision_state") != "blocked_owner_decision_required":
        raise WinbackPilotError("holdout_owner_decision_must_remain_open")
    normalized_holdout = {
        "allocation_algorithm": _text(holdout.get("allocation_algorithm"), field="holdout.allocation_algorithm"),
        "percentage": None,
        "decision_state": "blocked_owner_decision_required",
    }

    capacity = source.get("capacity")
    commercial_capacity = commercial.get("capacity_policy")
    if not isinstance(capacity, Mapping) or not isinstance(commercial_capacity, Mapping):
        raise WinbackPilotError("capacity_contract_required")
    _closed(capacity, {"allowed_bands", "pause_at_ratio", "resume_below_ratio", "limit_units"}, field="capacity")
    normalized_capacity = {
        "allowed_bands": sorted({_identifier(item, field="capacity.allowed_bands") for item in list(capacity.get("allowed_bands") or [])}),
        "pause_at_ratio": float(capacity.get("pause_at_ratio") or 0),
        "resume_below_ratio": float(capacity.get("resume_below_ratio") or 0),
        "limit_units": int(capacity.get("limit_units") or 0),
    }
    expected_capacity = {
        "allowed_bands": sorted(commercial_capacity.get("acquisition_allowed_bands") or []),
        "pause_at_ratio": float(commercial_capacity.get("pause_at_ratio") or 0),
        "resume_below_ratio": float(commercial_capacity.get("resume_below_ratio") or 0),
        "limit_units": int(commercial_capacity.get("limit_units") or 0),
    }
    if normalized_capacity != expected_capacity:
        raise WinbackPilotError("pilot_capacity_mismatch")

    decision = source.get("decision")
    if not isinstance(decision, Mapping):
        raise WinbackPilotError("decision_object_required")
    _closed(
        decision,
        {"minimum_observation_days", "ctr_can_select_winner", "scale_requires_owner_approval", "maximum_next_paid_cap"},
        field="decision",
    )
    normalized_decision = {
        "minimum_observation_days": _exact_int(decision.get("minimum_observation_days"), 30, field="decision.minimum_observation_days"),
        "ctr_can_select_winner": _exact_bool(decision.get("ctr_can_select_winner"), False, field="decision.ctr_can_select_winner"),
        "scale_requires_owner_approval": _exact_bool(decision.get("scale_requires_owner_approval"), True, field="decision.scale_requires_owner_approval"),
        "maximum_next_paid_cap": _exact_int(decision.get("maximum_next_paid_cap"), 50, field="decision.maximum_next_paid_cap"),
    }

    contract: dict[str, Any] = {
        "schema_version": OUTPUT_SCHEMA,
        "pilot_id": pilot_id,
        "revision": revision,
        "state": "draft_blocked",
        "objective": "winback",
        "legal_profile_id": profile_id,
        "channels": channels,
        "audience": normalized_audience,
        "offer": normalized_offer,
        "creatives": sorted(creatives, key=lambda item: item["variant"]),
        "holdout": normalized_holdout,
        "capacity": normalized_capacity,
        "suppression": sorted({_identifier(item, field="suppression") for item in list(source.get("suppression") or [])}),
        "primary_metric": _identifier(source.get("primary_metric"), field="primary_metric"),
        "guardrails": sorted({_identifier(item, field="guardrails") for item in list(source.get("guardrails") or [])}),
        "decision": normalized_decision,
        "external_gates": sorted({_identifier(item, field="external_gates") for item in list(source.get("external_gates") or [])}),
        "commercial_revision": _text(commercial.get("commercial_revision"), field="commercial_revision", limit=32),
        "commercial_contract_sha256": _text(commercial.get("contract_sha256"), field="commercial_contract_sha256", limit=64),
        "marketing_governance_revision": _text(governance.get("revision"), field="marketing_governance_revision", limit=32),
        "marketing_governance_sha256": _text(governance.get("contract_sha256"), field="marketing_governance_sha256", limit=64),
        "source_contract": "shared/winback-pilot.source.json",
        "source_sha256": _file_digest(SOURCE_PATH),
    }
    contract["contract_sha256"] = _digest(contract)
    return contract


def render_document(contract: Mapping[str, Any]) -> str:
    lines = [
        "# Generated winback pilot contract",
        "",
        "Generated by `scripts/generate_winback_pilot.py`. Do not edit by hand.",
        "",
        f"- pilot: `{contract['pilot_id']}`",
        f"- revision: `{contract['revision']}`",
        f"- state: `{contract['state']}`",
        f"- contract SHA-256: `{contract['contract_sha256']}`",
        f"- commercial revision: `{contract['commercial_revision']}`",
        f"- marketing governance: `{contract['marketing_governance_revision']}`",
        f"- primary metric: `{contract['primary_metric']}`",
        "",
        "The repository contract is intentionally launch-blocked. Holdout percentage, legal/channel approval, consent, provider/deployment and live-capacity evidence remain owner/operator gates.",
        "",
    ]
    return "\n".join(lines)


def _write_or_check(path: Path, expected: str, *, check: bool) -> None:
    if check:
        try:
            actual = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise WinbackPilotError(f"missing_generated_output:{path}") from exc
        if actual != expected:
            raise WinbackPilotError(f"stale_generated_output:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the bounded POKROV winback pilot contract.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        contract = build_contract(
            _read_object(SOURCE_PATH),
            _read_object(COMMERCIAL_PATH),
            _read_object(GOVERNANCE_PATH),
        )
        _write_or_check(OUTPUT_PATH, json.dumps(contract, ensure_ascii=False, indent=2) + "\n", check=bool(args.check))
        _write_or_check(DOC_PATH, render_document(contract), check=bool(args.check))
    except WinbackPilotError as exc:
        print(f"FAIL winback-pilot {exc}")
        return 1
    print(
        "PASS winback-pilot "
        f"revision={contract['revision']} sha256={contract['contract_sha256']} state={contract['state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
