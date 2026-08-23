from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = REPO_ROOT / "shared"
PRODUCT_FACTS_PATH = SHARED_ROOT / "product-facts.json"
TARIFF_CATALOG_PATH = SHARED_ROOT / "tariff-catalog.json"
OUTPUT_PATH = SHARED_ROOT / "commercial-contract.json"
DOC_PATH = REPO_ROOT / "docs" / "generated" / "commercial-contract.md"
SCHEMA_VERSION = "pokrov-commercial-contract-v1"
REVISION_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.[1-9][0-9]*$")
LEGAL_STATES = frozenset({"approved", "blocked_unpublished", "blocked_unapproved", "blocked_no_owner_legal_decision"})


class CommercialContractError(ValueError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CommercialContractError(f"invalid_json:{path.name}") from exc
    if not isinstance(value, dict):
        raise CommercialContractError(f"object_required:{path.name}")
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


def _text(value: object, *, field: str, limit: int = 128) -> str:
    normalized = str(value or "").strip()
    if not normalized or len(normalized) > limit:
        raise CommercialContractError(f"invalid_text:{field}")
    return normalized


def _positive_int(value: object, *, field: str) -> int:
    if type(value) is not int or int(value) <= 0:
        raise CommercialContractError(f"positive_integer_required:{field}")
    return int(value)


def _nonnegative_int(value: object, *, field: str) -> int:
    if type(value) is not int or int(value) < 0:
        raise CommercialContractError(f"nonnegative_integer_required:{field}")
    return int(value)


def _iso_datetime(value: object, *, field: str) -> str:
    normalized = _text(value, field=field, limit=64)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CommercialContractError(f"invalid_datetime:{field}") from exc
    if parsed.tzinfo is None:
        raise CommercialContractError(f"timezone_required:{field}")
    return normalized


def _legal_contract(product: dict[str, Any]) -> dict[str, Any]:
    legal = product.get("legal")
    if not isinstance(legal, dict):
        raise CommercialContractError("object_required:product.legal")
    seller_status = _text(legal.get("seller_publication_status"), field="legal.seller_publication_status")
    offer_status = _text(legal.get("offer_review_status"), field="legal.offer_review_status")
    rf_status = _text(legal.get("rf_advertising_status"), field="legal.rf_advertising_status")
    if seller_status not in LEGAL_STATES or offer_status not in LEGAL_STATES or rf_status not in LEGAL_STATES:
        raise CommercialContractError("invalid_legal_status")
    channels = legal.get("allowed_launch_channels")
    if not isinstance(channels, list) or any(not isinstance(item, str) or not item.strip() for item in channels):
        raise CommercialContractError("invalid_legal_channels")
    return {
        "offer_path": _text(legal.get("offer_path"), field="legal.offer_path"),
        "privacy_path": _text(legal.get("privacy_path"), field="legal.privacy_path"),
        "seller_publication_status": seller_status,
        "offer_review_status": offer_status,
        "rf_advertising_status": rf_status,
        "allowed_launch_channels": sorted({item.strip().lower() for item in channels}),
        "launch_ready": bool(
            seller_status == "approved"
            and offer_status == "approved"
            and rf_status == "approved"
            and channels
        ),
    }


def _capacity_contract(catalog: dict[str, Any]) -> dict[str, Any]:
    policy = catalog.get("capacity_policy")
    if not isinstance(policy, dict):
        raise CommercialContractError("object_required:capacity_policy")
    limit_units = _positive_int(policy.get("limit_units"), field="capacity_policy.limit_units")
    if limit_units != 300:
        raise CommercialContractError("capacity_limit_must_be_300")
    pause_at = float(policy.get("pause_at_ratio", -1))
    resume_below = float(policy.get("resume_below_ratio", -1))
    if not (0 < resume_below < pause_at <= 1):
        raise CommercialContractError("invalid_capacity_hysteresis")
    allowed = policy.get("acquisition_allowed_bands")
    bands = policy.get("bands")
    if not isinstance(allowed, list) or not isinstance(bands, list) or not bands:
        raise CommercialContractError("invalid_capacity_bands")
    normalized_bands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in bands:
        if not isinstance(raw, dict):
            raise CommercialContractError("invalid_capacity_band")
        code = _text(raw.get("code"), field="capacity_policy.band.code", limit=16).lower()
        if code in seen:
            raise CommercialContractError("duplicate_capacity_band")
        seen.add(code)
        minimum = float(raw.get("minimum_ratio", -1))
        maximum_raw = raw.get("maximum_ratio")
        maximum = None if maximum_raw is None else float(maximum_raw)
        if minimum < 0 or (maximum is not None and maximum < minimum):
            raise CommercialContractError("invalid_capacity_band_range")
        normalized_bands.append(
            {"code": code, "minimum_ratio": minimum, "maximum_ratio": maximum}
        )
    normalized_allowed = [str(item).strip().lower() for item in allowed]
    if not normalized_allowed or any(item not in seen for item in normalized_allowed):
        raise CommercialContractError("unknown_allowed_capacity_band")
    return {
        "limit_units": limit_units,
        "unit_authority": _text(policy.get("unit_authority"), field="capacity_policy.unit_authority"),
        "acquisition_allowed_bands": normalized_allowed,
        "pause_at_ratio": pause_at,
        "resume_below_ratio": resume_below,
        "renewal_exempt": policy.get("renewal_exempt") is True,
        "bands": normalized_bands,
    }


def build_contract(product: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    revision = _text(catalog.get("commercial_revision"), field="commercial_revision", limit=32)
    if REVISION_RE.fullmatch(revision) is None:
        raise CommercialContractError("invalid_commercial_revision")
    if catalog.get("pricing_preview") is not None:
        raise CommercialContractError("static_pricing_preview_forbidden")
    currency = _text(catalog.get("default_currency"), field="default_currency", limit=8).upper()
    if currency != "RUB":
        raise CommercialContractError("unsupported_commercial_currency")

    raw_plans = catalog.get("plans")
    if not isinstance(raw_plans, list) or not raw_plans:
        raise CommercialContractError("plans_required")
    plans: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for raw in raw_plans:
        if not isinstance(raw, dict):
            raise CommercialContractError("invalid_plan")
        code = _text(raw.get("code"), field="plan.code", limit=32).lower()
        if code in seen_codes:
            raise CommercialContractError("duplicate_plan_code")
        seen_codes.add(code)
        amount = _positive_int(raw.get("amount_rub"), field=f"plan.{code}.amount_rub")
        base_saving = _nonnegative_int(
            raw.get("base_saving_percent"), field=f"plan.{code}.base_saving_percent"
        )
        campaign_saving = _nonnegative_int(
            raw.get("temporary_campaign_saving_percent"),
            field=f"plan.{code}.temporary_campaign_saving_percent",
        )
        if campaign_saving != 0:
            raise CommercialContractError("static_campaign_saving_forbidden")
        plans.append(
            {
                "code": code,
                "label": _text(raw.get("label"), field=f"plan.{code}.label"),
                "amount_rub": amount,
                "duration_days": _positive_int(
                    raw.get("duration_days"), field=f"plan.{code}.duration_days"
                ),
                "device_limit": _positive_int(
                    raw.get("device_limit"), field=f"plan.{code}.device_limit"
                ),
                "base_saving_percent": base_saving,
                "temporary_campaign_saving_percent": campaign_saving,
                "capacity_cost_units": _positive_int(
                    raw.get("capacity_cost_units"), field=f"plan.{code}.capacity_cost_units"
                ),
                "renewal_policy": _text(
                    raw.get("renewal_policy"), field=f"plan.{code}.renewal_policy"
                ),
                "is_active": raw.get("is_active") is True,
                "public_visibility": _text(
                    raw.get("public_visibility"), field=f"plan.{code}.public_visibility"
                ),
                "sort_order": _nonnegative_int(
                    raw.get("sort_order"), field=f"plan.{code}.sort_order"
                ),
            }
        )
    plans.sort(key=lambda item: (int(item["sort_order"]), str(item["code"])))

    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "commercial_revision": revision,
        "effective_from": _iso_datetime(catalog.get("effective_from"), field="effective_from"),
        "terms_revision": _text(catalog.get("terms_revision"), field="terms_revision", limit=64),
        "currency": currency,
        "catalog_version": _text(catalog.get("catalog_version"), field="catalog_version"),
        "price_authority": _text(catalog.get("price_authority"), field="price_authority"),
        "promo_authority": _text(catalog.get("promo_authority"), field="promo_authority"),
        "campaign_saving_authority": _text(
            catalog.get("campaign_saving_authority"), field="campaign_saving_authority"
        ),
        "legal": _legal_contract(product),
        "capacity_policy": _capacity_contract(catalog),
        "plans": plans,
        "source_contracts": {
            "product_facts": "shared/product-facts.json",
            "tariff_catalog": "shared/tariff-catalog.json",
        },
        "source_sha256": {
            "product_facts": _digest(product),
            "tariff_catalog": _digest(catalog),
        },
    }
    contract["contract_sha256"] = _digest(contract)
    return contract


def render_document(contract: dict[str, Any]) -> str:
    legal = contract["legal"]
    capacity = contract["capacity_policy"]
    lines = [
        "# Generated Commercial Contract",
        "",
        "Generated by `scripts/generate_commercial_contract.py`. Do not edit by hand.",
        "",
        f"- schema: `{contract['schema_version']}`",
        f"- commercial revision: `{contract['commercial_revision']}`",
        f"- effective from: `{contract['effective_from']}`",
        f"- terms revision: `{contract['terms_revision']}`",
        f"- contract SHA-256: `{contract['contract_sha256']}`",
        f"- legal launch ready: `{str(bool(legal['launch_ready'])).lower()}`",
        f"- capacity limit: `{capacity['limit_units']}` units",
        "",
        "| Plan | Base RUB | Days | Devices | Base saving | Campaign saving | Capacity units |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for plan in contract["plans"]:
        lines.append(
            "| `{code}` | {amount_rub} | {duration_days} | {device_limit} | {base_saving_percent}% | "
            "{temporary_campaign_saving_percent}% | {capacity_cost_units} |".format(**plan)
        )
    lines.extend(
        [
            "",
            "Static campaign savings are zero by contract. Promo and temporary offer pricing is server-authoritative.",
            "Seller publication, offer review, RF advertising qualification, deployment, CDN and public readback remain external evidence gates.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_or_check(path: Path, expected: str, *, check: bool) -> None:
    if check:
        try:
            actual = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CommercialContractError(f"missing_generated_output:{path}") from exc
        if actual != expected:
            raise CommercialContractError(f"stale_generated_output:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the deterministic shared commercial contract.")
    parser.add_argument("--check", action="store_true", help="Fail when generated outputs are stale.")
    args = parser.parse_args()
    try:
        product = _read_object(PRODUCT_FACTS_PATH)
        catalog = _read_object(TARIFF_CATALOG_PATH)
        contract = build_contract(product, catalog)
        contract_text = json.dumps(contract, ensure_ascii=False, indent=2) + "\n"
        document_text = render_document(contract)
        _write_or_check(OUTPUT_PATH, contract_text, check=bool(args.check))
        _write_or_check(DOC_PATH, document_text, check=bool(args.check))
    except CommercialContractError as exc:
        print(f"FAIL commercial-contract {exc}")
        return 1
    print(
        "PASS commercial-contract "
        f"revision={contract['commercial_revision']} sha256={contract['contract_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
