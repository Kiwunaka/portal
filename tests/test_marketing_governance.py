from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import generate_marketing_governance as generator  # noqa: E402
import validate_marketing_governance as validator  # noqa: E402


def _source() -> dict:
    return json.loads(generator.SOURCE_PATH.read_text(encoding="utf-8"))


def _catalog() -> dict:
    return json.loads(generator.CATALOG_PATH.read_text(encoding="utf-8"))


def test_generated_contract_is_current_and_hash_bound() -> None:
    expected = generator.build_contract(_source(), _catalog())
    actual = json.loads(generator.OUTPUT_PATH.read_text(encoding="utf-8"))
    assert actual == expected
    unsigned = dict(actual)
    digest = unsigned.pop("contract_sha256")
    assert digest == generator._digest(unsigned)
    assert actual["default_campaign_launch_state"].startswith("blocked_")


def test_claim_evidence_mismatch_fails_closed() -> None:
    source = copy.deepcopy(_source())
    source["claims"][0]["evidence"][0]["equals"] = 6
    with pytest.raises(
        generator.MarketingGovernanceError,
        match="claim_evidence_mismatch",
    ):
        generator.build_contract(source, _catalog())


def test_sample_legal_approval_is_forbidden() -> None:
    source = copy.deepcopy(_source())
    source["profiles"][1]["approval"] = {
        "approval_id": "sample",
        "reviewer": "sample",
    }
    with pytest.raises(
        generator.MarketingGovernanceError,
        match="sample_legal_approval_forbidden",
    ):
        generator.build_contract(source, _catalog())


def test_trust_led_and_absolute_claim_scanner() -> None:
    contract = json.loads(generator.OUTPUT_PATH.read_text(encoding="utf-8"))
    assert validator.scan_text(
        "Проверьте подключение до оплаты",
        patterns=contract["prohibited_claim_patterns"],
        markers=contract["trust_led_forbidden_markers"],
    ) == []
    assert any(
        issue.startswith("trust_led_marker:")
        for issue in validator.scan_text(
            "YouTube — одной кнопкой",
            patterns=contract["prohibited_claim_patterns"],
            markers=contract["trust_led_forbidden_markers"],
        )
    )
    assert any(
        issue.startswith("prohibited_claim:")
        for issue in validator.scan_text(
            "Гарантированный доступ",
            patterns=contract["prohibited_claim_patterns"],
        )
    )


def test_repository_marketing_governance_is_fail_closed_and_current() -> None:
    assert validator.validate_repository() == []


def test_schema_is_closed_and_loadable() -> None:
    schema_path = (
        REPO_ROOT
        / "shared"
        / "contracts"
        / "marketing"
        / "marketing-governance.v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["profiles"]["items"]["additionalProperties"] is False
    assert schema["properties"]["claims"]["items"]["additionalProperties"] is False
