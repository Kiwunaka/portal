from __future__ import annotations

import hashlib
import hmac
import json
from functools import lru_cache
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "pokrov-winback-pilot-v1"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT_PATH = (
    _REPO_ROOT / "shared" / "contracts" / "marketing" / "winback-pilot.v1.json"
)
_SOURCE_PATH = _REPO_ROOT / "shared" / "winback-pilot.source.json"
_COMMERCIAL_PATH = _REPO_ROOT / "shared" / "commercial-contract.json"
_GOVERNANCE_PATH = (
    _REPO_ROOT
    / "shared"
    / "contracts"
    / "marketing"
    / "marketing-governance.v1.json"
)


class MarketingPilotContractError(RuntimeError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MarketingPilotContractError(f"invalid_contract_file:{path.name}") from exc
    if not isinstance(value, dict):
        raise MarketingPilotContractError(f"contract_object_required:{path.name}")
    return value


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_digest(path: Path) -> str:
    # Match the generator across LF and Windows CRLF checkouts. The signed
    # semantic content is unchanged by Git's local newline conversion.
    normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _validated_contract() -> dict[str, Any]:
    contract = _read_object(_CONTRACT_PATH)
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise MarketingPilotContractError("pilot_schema_mismatch")
    unsigned = dict(contract)
    observed_digest = str(unsigned.pop("contract_sha256", ""))
    if not observed_digest or not hmac.compare_digest(
        observed_digest,
        _canonical_digest(unsigned),
    ):
        raise MarketingPilotContractError("pilot_contract_digest_mismatch")
    if not hmac.compare_digest(
        str(contract.get("source_sha256") or ""),
        _file_digest(_SOURCE_PATH),
    ):
        raise MarketingPilotContractError("pilot_source_stale")
    commercial = _read_object(_COMMERCIAL_PATH)
    governance = _read_object(_GOVERNANCE_PATH)
    for field, expected in (
        ("commercial_revision", commercial.get("commercial_revision")),
        ("commercial_contract_sha256", commercial.get("contract_sha256")),
        ("marketing_governance_revision", governance.get("revision")),
        ("marketing_governance_sha256", governance.get("contract_sha256")),
    ):
        if not hmac.compare_digest(
            str(contract.get(field) or ""),
            str(expected or ""),
        ):
            raise MarketingPilotContractError(f"pilot_dependency_stale:{field}")
    if contract.get("state") != "draft_blocked":
        raise MarketingPilotContractError("repository_pilot_must_remain_blocked")
    if (contract.get("holdout") or {}).get("percentage") is not None:
        raise MarketingPilotContractError("repository_holdout_must_remain_unapproved")
    return contract


@lru_cache(maxsize=1)
def get_winback_pilot_contract() -> dict[str, Any]:
    return _validated_contract()


def clear_winback_pilot_contract_cache() -> None:
    get_winback_pilot_contract.cache_clear()
