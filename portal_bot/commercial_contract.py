from __future__ import annotations

import hashlib
import hmac
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "pokrov-commercial-contract-v1"
COMMERCIAL_REVISION_HEADER = "X-Pokrov-Commercial-Revision"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHARED_ROOT = _REPO_ROOT / "shared"
_CONTRACT_PATH = _SHARED_ROOT / "commercial-contract.json"
_PRODUCT_PATH = _SHARED_ROOT / "product-facts.json"
_TARIFF_PATH = _SHARED_ROOT / "tariff-catalog.json"


class CommercialContractError(RuntimeError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CommercialContractError(f"invalid_contract_file:{path.name}") from exc
    if not isinstance(value, dict):
        raise CommercialContractError(f"contract_object_required:{path.name}")
    return value


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validated_contract() -> dict[str, Any]:
    contract = _read_object(_CONTRACT_PATH)
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise CommercialContractError("commercial_schema_mismatch")
    expected_contract_digest = str(contract.get("contract_sha256") or "")
    unsigned = dict(contract)
    unsigned.pop("contract_sha256", None)
    if not expected_contract_digest or not hmac.compare_digest(
        expected_contract_digest,
        _canonical_digest(unsigned),
    ):
        raise CommercialContractError("commercial_contract_digest_mismatch")
    source_digests = contract.get("source_sha256")
    if not isinstance(source_digests, dict):
        raise CommercialContractError("commercial_source_digest_missing")
    for key, path in (("product_facts", _PRODUCT_PATH), ("tariff_catalog", _TARIFF_PATH)):
        expected = str(source_digests.get(key) or "")
        actual = _canonical_digest(_read_object(path))
        if not expected or not hmac.compare_digest(expected, actual):
            raise CommercialContractError(f"commercial_source_stale:{key}")
    revision = str(contract.get("commercial_revision") or "").strip()
    if not revision:
        raise CommercialContractError("commercial_revision_missing")
    return contract


@lru_cache(maxsize=1)
def get_commercial_contract() -> dict[str, Any]:
    return _validated_contract()


def commercial_revision() -> str:
    return str(get_commercial_contract()["commercial_revision"])


def commercial_contract_sha256() -> str:
    return str(get_commercial_contract()["contract_sha256"])


def commercial_plan_map() -> dict[str, dict[str, Any]]:
    return {
        str(item.get("code") or ""): dict(item)
        for item in list(get_commercial_contract().get("plans") or [])
        if isinstance(item, dict) and str(item.get("code") or "")
    }


def assert_plan_projection_matches_contract(plans: Sequence[Mapping[str, Any]]) -> None:
    expected = commercial_plan_map()
    actual: dict[str, tuple[int, int, int]] = {}
    for raw in plans:
        code = str(raw.get("code") or "").strip().lower()
        if not code or code in actual:
            raise CommercialContractError("commercial_plan_projection_invalid")
        actual[code] = (
            int(raw.get("amount_rub") or 0),
            int(raw.get("days") or raw.get("duration_days") or 0),
            int(raw.get("device_limit") or 0),
        )
    expected_values = {
        code: (
            int(item.get("amount_rub") or 0),
            int(item.get("duration_days") or 0),
            int(item.get("device_limit") or 0),
        )
        for code, item in expected.items()
        if item.get("is_active") is True and item.get("public_visibility") != "hidden"
    }
    if actual != expected_values:
        raise CommercialContractError("commercial_plan_projection_mismatch")


def commercial_health_snapshot() -> dict[str, Any]:
    contract = get_commercial_contract()
    legal_launch_state = "ready" if bool((contract.get("legal") or {}).get("launch_ready")) else "blocked"
    return {
        "schema_version": str(contract["schema_version"]),
        "commercial_revision": str(contract["commercial_revision"]),
        "catalog_version": str(contract["catalog_version"]),
        "contract_sha256": str(contract["contract_sha256"]),
        "price_authority": str(contract["price_authority"]),
        "promo_authority": str(contract["promo_authority"]),
        "plan_count": len(list(contract.get("plans") or [])),
        "legal_launch_state": legal_launch_state,
        "source_consistency": "consistent",
    }


def clear_commercial_contract_cache() -> None:
    get_commercial_contract.cache_clear()
