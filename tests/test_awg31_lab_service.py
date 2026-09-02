from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import awg31_lab_service as awg31_lab_service_module  # noqa: E402
from awg31_lab_service import (  # noqa: E402
    AWG31_CONTRACT_ID,
    AWG31_CONTRACT_SHA256,
    AWG31_ENDPOINT_REVISION,
    Awg31LabError,
    awg31_lab_rollout_access,
    build_managed_awg31_lab_config,
    default_awg31_lab_config,
    replace_awg31_lab_material,
    validate_awg31_endpoint,
)
from admin_action_intent_service import (  # noqa: E402
    ACTION_POLICIES,
    _normalize_awg31_lab_material_payload,
    _sanitize_awg31_lab_material_result,
    action_policy_route_keys,
)
from models import Awg2LabMaterial, Awg31LabMaterial, Base  # noqa: E402
from network_rollout import normalized_network_rollout_config, resolved_client_policy  # noqa: E402
from transport_catalog import (  # noqa: E402
    AWG31_LAB,
    LEGACY_REALITY_FALLBACK,
    node_transport_profiles,
)


def _endpoint() -> dict[str, object]:
    return {
        "useIntegratedTun": False,
        "contract_id": AWG31_CONTRACT_ID,
        "private_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "address": ["10.67.0.2/32", "fd67::2/128"],
        "mtu": 1408,
        "jc": 6,
        "jmin": 48,
        "jmax": 96,
        "s1": 16,
        "s2": 16,
        "s3": 16,
        "s4": 16,
        "h1": "1100001-1100099",
        "h2": "1200001-1200099",
        "h3": "1300001-1300099",
        "h4": "1400001-1400099",
        "i1": "<t><r 16><b 0xdeadbeef>",
        "i2": "",
        "i3": "",
        "i4": "",
        "i5": "",
        "header_protection_key": "AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI=",
        "content_padding_addition": "16-96",
        "rekey_after_time": "90-150",
        "rekey_timeout": "4-8",
        "reject_after_time": "180-240",
        "keepalive_timeout": "8-14",
        "max_handshake_attempts": "12-24",
        "random_trailers": True,
        "peers": [
            {
                "address": "192.0.2.31",
                "port": 51831,
                "public_key": "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=",
                "allowed_ips": ["0.0.0.0/0", "::/0"],
                "persistent_keepalive_interval_range": "22-30",
            }
        ],
    }


def _rollout(*, enabled: bool = True, killed: bool = False, digest: str = AWG31_CONTRACT_SHA256):
    return normalized_network_rollout_config(
        {
            "version": "2026-08-26",
            "cohort_overrides": {
                "awg31-owner-lab": {
                    "install_ids": ["owner-device"],
                    "platforms": ["windows"],
                    "transport_profile": AWG31_LAB,
                }
            },
            AWG31_LAB: {
                "enabled": enabled,
                "kill_switch_engaged": killed,
                "allowlist_install_ids": ["owner-device"],
                "allowlist_tg_ids": [1001],
                "allowlist_node_codes": ["pl"],
                "allowed_platforms": ["android", "windows"],
                "contract_id": AWG31_CONTRACT_ID,
                "contract_sha256": digest,
                "generation": "awg31-lab-v1",
                "endpoint_revision": AWG31_ENDPOINT_REVISION,
                "server_record_id": "pokrov-awg31-pl-01",
                "server_owner": "pokrov",
                "server_state": "ready",
                "material_max_age_hours": 168,
            },
        }
    )


@pytest.fixture()
def db_session(monkeypatch):
    monkeypatch.setenv("AWG31_LAB_MATERIAL_SECRET", "synthetic-awg31-lab-test-secret")
    monkeypatch.setattr(
        awg31_lab_service_module,
        "_utcnow",
        lambda: datetime(2026, 8, 26, 10, 1, 0),
    )
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_awg31_rollout_is_disabled_and_killed_by_default() -> None:
    config = default_awg31_lab_config()

    assert config["enabled"] is False
    assert config["kill_switch_engaged"] is True
    assert "endpoint" not in config
    assert not awg31_lab_rollout_access(
        config,
        install_id="owner-device",
        tg_ids=[1001],
        platform="windows",
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("contract_id", "pokrov.awg2.endpoint.v1", "contract_id_invalid"),
        ("useIntegratedTun", True, "integrated_tun_forbidden"),
        ("s4", 11, "padding_invalid"),
        ("header_protection_key", "AA==", "header_protection_key_invalid"),
        ("i1", "<r 8>\nprivate_key=00", "instruction_invalid"),
        ("content_padding_addition", "0-513", "content_padding_addition_invalid"),
    ],
)
def test_awg31_endpoint_validation_fails_closed(field: str, value: object, code: str) -> None:
    endpoint = _endpoint()
    endpoint[field] = value

    with pytest.raises(Awg31LabError, match=code):
        validate_awg31_endpoint(endpoint)


def test_separate_encrypted_material_can_issue_exact_managed_profile(db_session) -> None:
    row = replace_awg31_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg31-lab-v1",
        endpoint_revision=AWG31_ENDPOINT_REVISION,
        server_record_id="pokrov-awg31-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
        now=datetime(2026, 8, 26, 10, 0, 0),
    )
    db_session.commit()
    rollout = _rollout()
    user = SimpleNamespace(tg_id=1001, app_install_id="owner-device", app_platform="windows")

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )
    config = build_managed_awg31_lab_config(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        rollout_value=rollout[AWG31_LAB],
        title="POKROV",
        now=datetime(2026, 8, 26, 10, 1, 0),
    )

    assert policy["transport_profile"] == AWG31_LAB
    assert policy["transport_kind"] == "awg31"
    assert policy["profile_revision"] == "2026-08-26:awg31_lab:awg31-lab-v1"
    assert config["endpoints"][0]["contract_id"] == AWG31_CONTRACT_ID
    assert config["endpoints"][0]["header_protection_key"] == _endpoint()["header_protection_key"]
    assert config["dns"]["strategy"] == "ipv4_only"
    assert config["_meta"]["transport_contract"] == {
        "id": AWG31_CONTRACT_ID,
        "sha256": AWG31_CONTRACT_SHA256,
        "profile": AWG31_LAB,
        "state": "enabled",
        "generation": "awg31-lab-v1",
    }
    assert row.endpoint_ciphertext.startswith("gAAAA")
    assert _endpoint()["private_key"] not in row.endpoint_ciphertext
    assert db_session.query(Awg2LabMaterial).count() == 0
    assert db_session.query(Awg31LabMaterial).count() == 1


@pytest.mark.parametrize(
    "rollout",
    [_rollout(enabled=False), _rollout(killed=True), _rollout(digest="0" * 64)],
    ids=["disabled", "killed", "stale-contract"],
)
def test_awg31_policy_rolls_back_before_profile_issuance(db_session, rollout) -> None:
    replace_awg31_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg31-lab-v1",
        endpoint_revision=AWG31_ENDPOINT_REVISION,
        server_record_id="pokrov-awg31-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
    )
    db_session.commit()
    user = SimpleNamespace(tg_id=1001, app_install_id="owner-device", app_platform="windows")

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )

    assert policy["transport_profile"] == LEGACY_REALITY_FALLBACK


def test_node_catalog_drops_raw_awg31_profiles() -> None:
    node = SimpleNamespace(
        inbound_id=1,
        host="legacy.example.test",
        vless_port=443,
        reality_sni="www.example.test",
        reality_pbk="pbk",
        reality_sid="sid",
        fingerprint="firefox",
        flow="xtls-rprx-vision",
        transport_profiles_json=json.dumps(
            [{"name": AWG31_LAB, "enabled": True, "private_key": "must-not-enter-node-catalog"}]
        ),
    )

    profiles = node_transport_profiles(node)

    assert [item["name"] for item in profiles] == [LEGACY_REALITY_FALLBACK]
    assert "must-not-enter-node-catalog" not in json.dumps(profiles)


def test_admin_intent_and_result_expose_only_fingerprints_and_safe_metadata() -> None:
    payload = {
        "tg_id": 1001,
        "install_id": "owner-device",
        "generation": "awg31-lab-v1",
        "endpoint_revision": AWG31_ENDPOINT_REVISION,
        "server_record_id": "pokrov-awg31-pl-01",
        "node_code": "pl",
        "endpoint": _endpoint(),
    }

    normalized = _normalize_awg31_lab_material_payload(payload)
    safe_result = _sanitize_awg31_lab_material_result(
        {
            "ok": True,
            "material": {
                "id": 8,
                "tg_id": 1001,
                "install_id": "owner-device",
                "generation": "awg31-lab-v1",
                "endpoint_revision": AWG31_ENDPOINT_REVISION,
                "server_record_id": "pokrov-awg31-pl-01",
                "node_code": "pl",
                "material_hash": "e" * 64,
                "state": "ready",
                "is_active": True,
            },
        }
    )
    serialized = json.dumps({"normalized": normalized, "result": safe_result})

    assert normalized["endpoint"]["sha256"]
    assert "install_id_sha256" in safe_result["material"]
    assert "install_id" not in safe_result["material"]
    assert _endpoint()["private_key"] not in serialized
    assert "192.0.2.31" not in serialized


def test_admin_material_route_is_l3_intent_guarded() -> None:
    policy = ACTION_POLICIES["awg31_lab_material.replace"]

    assert policy.risk_level == "L3"
    assert policy.challenge_kind == "exact_tg_id"
    assert (
        "PUT",
        "/api/admin/client/awg31-lab/material",
    ) in action_policy_route_keys()
