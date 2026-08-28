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

from hy2_lab_service import (  # noqa: E402
    HY2_CONTRACT_ID,
    HY2_CONTRACT_SHA256,
    HY2_ENDPOINT_REVISION,
    Hy2LabError,
    build_managed_hy2_lab_config,
    default_hy2_lab_config,
    hy2_lab_rollout_access,
    replace_hy2_lab_material,
    validate_hy2_endpoint,
)
from admin_action_intent_service import (  # noqa: E402
    ACTION_POLICIES,
    _normalize_hy2_lab_material_payload,
    _sanitize_hy2_lab_material_result,
    action_policy_route_keys,
)
from models import Base, Hy2LabMaterial  # noqa: E402
from network_rollout import (  # noqa: E402
    normalized_network_rollout_config,
    resolved_client_policy,
)
from transport_catalog import HY2_LAB, LEGACY_REALITY_FALLBACK, node_transport_profiles  # noqa: E402


def _endpoint() -> dict[str, object]:
    return {
        "server": "hy2.example.invalid",
        "server_port": 443,
        "password": "synthetic-password",
        "up_mbps": 10,
        "down_mbps": 50,
        "obfs": {
            "type": "salamander",
            "password": "synthetic-obfs-password",
        },
        "tls": {
            "enabled": True,
            "server_name": "hy2.example.invalid",
            "insecure": False,
            "alpn": ["h3"],
        },
    }


def _rollout(
    *,
    enabled: bool = True,
    killed: bool = False,
    digest: str = HY2_CONTRACT_SHA256,
) -> dict[str, object]:
    return normalized_network_rollout_config(
        {
            "version": "2026-08-28",
            "cohort_overrides": {
                "hy2-owner-lab": {
                    "install_ids": ["owner-device"],
                    "platforms": ["android"],
                    "transport_profile": HY2_LAB,
                }
            },
            HY2_LAB: {
                "enabled": enabled,
                "kill_switch_engaged": killed,
                "allowlist_install_ids": ["owner-device"],
                "allowlist_tg_ids": [1001],
                "allowlist_node_codes": ["lab"],
                "allowed_platforms": ["android", "windows"],
                "contract_id": HY2_CONTRACT_ID,
                "contract_sha256": digest,
                "generation": "hy2-lab-v1",
                "endpoint_revision": HY2_ENDPOINT_REVISION,
                "server_record_id": "pokrov-hy2-lab-01",
                "server_owner": "pokrov",
                "server_state": "ready",
                "material_max_age_hours": 168,
            },
        }
    )


@pytest.fixture()
def db_session(monkeypatch):
    monkeypatch.setenv("HY2_LAB_MATERIAL_SECRET", "synthetic-hy2-lab-test-secret")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_hy2_rollout_is_disabled_and_killed_by_default() -> None:
    config = default_hy2_lab_config()

    assert config["enabled"] is False
    assert config["kill_switch_engaged"] is True
    assert "endpoint" not in config
    assert not hy2_lab_rollout_access(
        config,
        install_id="owner-device",
        tg_ids=[1001],
        platform="android",
    )


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda value: value.update(server_ports=["443", "8443"]), "endpoint_fields_invalid"),
        (lambda value: value.update(server="2001:db8::1"), "server_invalid"),
        (lambda value: value.update(password="short"), "password_invalid"),
        (lambda value: value["tls"].update(insecure=True), "tls_verification_required"),
        (lambda value: value["tls"].update(alpn=["h2"]), "tls_alpn_invalid"),
        (lambda value: value["obfs"].update(type="unknown"), "obfs_type_invalid"),
    ],
)
def test_hy2_endpoint_validation_fails_closed(mutate, code: str) -> None:
    endpoint = _endpoint()
    mutate(endpoint)

    with pytest.raises(Hy2LabError, match=code):
        validate_hy2_endpoint(endpoint)


def test_encrypted_material_can_issue_exact_managed_profile(db_session) -> None:
    row = replace_hy2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="hy2-lab-v1",
        endpoint_revision=HY2_ENDPOINT_REVISION,
        server_record_id="pokrov-hy2-lab-01",
        node_code="lab",
        endpoint=_endpoint(),
        now=datetime(2026, 8, 28, 10, 0, 0),
    )
    db_session.commit()
    rollout = _rollout()
    user = SimpleNamespace(
        tg_id=1001,
        app_install_id="owner-device",
        app_platform="android",
    )

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )
    config = build_managed_hy2_lab_config(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        rollout_value=rollout[HY2_LAB],
        title="POKROV",
        now=datetime(2026, 8, 28, 10, 1, 0),
    )

    assert policy["transport_profile"] == HY2_LAB
    assert policy["transport_kind"] == "hysteria2"
    assert policy["profile_revision"] == "2026-08-28:hy2_lab:hy2-lab-v1"
    outbound = config["outbounds"][0]
    assert outbound["type"] == "hysteria2"
    assert outbound["server_port"] == 443
    assert outbound["tls"] == _endpoint()["tls"]
    assert "server_ports" not in outbound
    assert "hop_interval" not in outbound
    assert config["inbounds"] == []
    assert config["_meta"]["transport_contract"] == {
        "id": HY2_CONTRACT_ID,
        "sha256": HY2_CONTRACT_SHA256,
        "profile": HY2_LAB,
        "state": "enabled",
        "generation": "hy2-lab-v1",
    }
    assert row.endpoint_ciphertext.startswith("gAAAA")
    assert _endpoint()["password"] not in row.endpoint_ciphertext
    assert db_session.query(Hy2LabMaterial).count() == 1


@pytest.mark.parametrize(
    "rollout",
    [_rollout(enabled=False), _rollout(killed=True), _rollout(digest="0" * 64)],
    ids=["disabled", "killed", "stale-contract"],
)
def test_hy2_policy_rolls_back_before_profile_issuance(db_session, rollout) -> None:
    replace_hy2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="hy2-lab-v1",
        endpoint_revision=HY2_ENDPOINT_REVISION,
        server_record_id="pokrov-hy2-lab-01",
        node_code="lab",
        endpoint=_endpoint(),
    )
    db_session.commit()
    user = SimpleNamespace(
        tg_id=1001,
        app_install_id="owner-device",
        app_platform="android",
    )

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )

    assert policy["transport_profile"] == LEGACY_REALITY_FALLBACK


def test_node_catalog_drops_raw_hy2_profiles() -> None:
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
            [
                {
                    "name": HY2_LAB,
                    "enabled": True,
                    "password": "must-not-enter-node-catalog",
                }
            ]
        ),
    )

    profiles = node_transport_profiles(node)

    assert [item["name"] for item in profiles] == [LEGACY_REALITY_FALLBACK]
    assert "must-not-enter-node-catalog" not in json.dumps(profiles)


def test_admin_intent_and_result_expose_only_fingerprints_and_safe_metadata() -> None:
    payload = {
        "tg_id": 1001,
        "install_id": "owner-device",
        "generation": "hy2-lab-v1",
        "endpoint_revision": HY2_ENDPOINT_REVISION,
        "server_record_id": "pokrov-hy2-lab-01",
        "node_code": "lab",
        "endpoint": _endpoint(),
    }

    normalized = _normalize_hy2_lab_material_payload(payload)
    safe_result = _sanitize_hy2_lab_material_result(
        {
            "ok": True,
            "material": {
                "id": 8,
                "tg_id": 1001,
                "install_id": "owner-device",
                "generation": "hy2-lab-v1",
                "endpoint_revision": HY2_ENDPOINT_REVISION,
                "server_record_id": "pokrov-hy2-lab-01",
                "node_code": "lab",
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
    assert _endpoint()["password"] not in serialized
    assert _endpoint()["server"] not in serialized


def test_admin_material_route_is_l3_intent_guarded() -> None:
    policy = ACTION_POLICIES["hy2_lab_material.replace"]

    assert policy.risk_level == "L3"
    assert policy.challenge_kind == "exact_tg_id"
    assert (
        "PUT",
        "/api/admin/client/hy2-lab/material",
    ) in action_policy_route_keys()
