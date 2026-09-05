from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import awg2_lab_service as awg2_lab_service_module  # noqa: E402
from awg2_lab_service import (  # noqa: E402
    AWG2_CONTRACT_ID,
    AWG2_CONTRACT_SHA256,
    AWG2_ENDPOINT_REVISION,
    Awg2LabError,
    awg2_lab_rollout_access,
    build_managed_awg2_lab_config,
    default_awg2_lab_config,
    replace_awg2_lab_material,
    validate_awg2_endpoint,
)
from admin_action_intent_service import (  # noqa: E402
    _normalize_awg2_lab_material_payload,
    _sanitize_awg2_lab_material_result,
)
from models import Awg2LabMaterial, Base  # noqa: E402
from network_rollout import normalized_network_rollout_config, resolved_client_policy  # noqa: E402
from transport_catalog import AWG2_LAB, LEGACY_REALITY_FALLBACK, node_transport_profiles  # noqa: E402


def _endpoint(*, mtu: int = 1408) -> dict[str, object]:
    return {
        "useIntegratedTun": False,
        "private_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "address": ["10.66.0.2/32", "fd66::2/128"],
        "mtu": mtu,
        "jc": 4,
        "jmin": 40,
        "jmax": 70,
        "s1": 0,
        "s2": 0,
        "s3": 0,
        "s4": 0,
        "h1": "1000001",
        "h2": "1000002",
        "h3": "1000003",
        "h4": "1000004",
        "peers": [
            {
                "address": "192.0.2.10",
                "port": 51820,
                "public_key": "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=",
                "allowed_ips": ["0.0.0.0/0", "::/0"],
                "persistent_keepalive_interval": 25,
            }
        ],
    }


def _rollout(
    *, enabled: bool = True, killed: bool = False, digest: str = AWG2_CONTRACT_SHA256
) -> dict[str, object]:
    return normalized_network_rollout_config(
        {
            "version": "2026-08-22",
            "cohort_overrides": {
                "awg2-owner-lab": {
                    "install_ids": ["owner-device"],
                    "platforms": ["windows"],
                    "transport_profile": AWG2_LAB,
                }
            },
            AWG2_LAB: {
                "enabled": enabled,
                "kill_switch_engaged": killed,
                "allowlist_install_ids": ["owner-device"],
                "allowlist_tg_ids": [1001],
                "allowlist_node_codes": ["pl"],
                "allowed_platforms": ["android", "windows"],
                "contract_id": AWG2_CONTRACT_ID,
                "contract_sha256": digest,
                "generation": "awg2-lab-v1",
                "endpoint_revision": AWG2_ENDPOINT_REVISION,
                "server_record_id": "pokrov-awg2-pl-01",
                "server_owner": "pokrov",
                "server_state": "ready",
                "material_max_age_hours": 168,
            },
        }
    )


@pytest.fixture()
def db_session(monkeypatch):
    monkeypatch.setenv("AWG2_LAB_MATERIAL_SECRET", "synthetic-awg2-lab-test-secret")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_awg2_rollout_is_disabled_and_killed_by_default() -> None:
    config = default_awg2_lab_config()

    assert config["enabled"] is False
    assert config["kill_switch_engaged"] is True
    assert "endpoint" not in config
    assert "private_key" not in json.dumps(config)
    assert not awg2_lab_rollout_access(
        config,
        install_id="owner-device",
        tg_ids=[1001],
        platform="windows",
    )


def test_material_secret_never_falls_back_to_shared_application_secrets(
    monkeypatch, db_session
) -> None:
    monkeypatch.delenv("AWG2_LAB_MATERIAL_SECRET", raising=False)
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "must-not-encrypt-awg2")
    monkeypatch.setenv("BOT_TOKEN", "must-not-encrypt-awg2-either")

    with pytest.raises(Awg2LabError, match="material_secret_unavailable"):
        replace_awg2_lab_material(
            db_session,
            tg_id=1001,
            install_id="owner-device",
            generation="awg2-lab-v1",
            endpoint_revision=AWG2_ENDPOINT_REVISION,
            server_record_id="pokrov-awg2-pl-01",
            node_code="pl",
            endpoint=_endpoint(),
        )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("useIntegratedTun", True, "integrated_tun_forbidden"),
        ("mtu", 1500, "mtu_invalid"),
        ("private_key", "not-a-key", "private_key_invalid"),
        ("h1", "0", "header_invalid"),
    ],
)
def test_awg2_endpoint_validation_fails_closed(
    field: str, value: object, code: str
) -> None:
    endpoint = _endpoint()
    endpoint[field] = value

    with pytest.raises(Awg2LabError, match=code):
        validate_awg2_endpoint(endpoint)


def test_device_material_is_encrypted_and_exact_contract_can_issue_managed_profile(
    db_session,
) -> None:
    material_now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = replace_awg2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg2-lab-v1",
        endpoint_revision=AWG2_ENDPOINT_REVISION,
        server_record_id="pokrov-awg2-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
        now=material_now,
    )
    db_session.commit()
    rollout = _rollout()
    user = SimpleNamespace(
        tg_id=1001, app_install_id="owner-device", app_platform="windows"
    )

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )
    config = build_managed_awg2_lab_config(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        rollout_value=rollout[AWG2_LAB],
        title="POKROV",
        now=material_now + timedelta(minutes=1),
    )

    assert policy["transport_profile"] == AWG2_LAB
    assert policy["transport_kind"] == "awg2"
    assert policy["engine_hint"] == "singbox"
    assert policy["profile_revision"] == "2026-08-22:awg2_lab:awg2-lab-v1"
    assert config["endpoints"][0]["type"] == "awg"
    assert config["endpoints"][0]["useIntegratedTun"] is False
    assert config["dns"]["strategy"] == "ipv4_only"
    assert config["_meta"]["transport_contract"] == {
        "id": AWG2_CONTRACT_ID,
        "sha256": AWG2_CONTRACT_SHA256,
        "profile": AWG2_LAB,
        "state": "enabled",
        "generation": "awg2-lab-v1",
    }
    assert row.endpoint_ciphertext.startswith("gAAAA")
    assert _endpoint()["private_key"] not in row.endpoint_ciphertext


@pytest.mark.parametrize(
    "rollout",
    [
        _rollout(enabled=False),
        _rollout(killed=True),
        _rollout(digest="0" * 64),
    ],
    ids=["disabled", "killed", "stale-contract"],
)
def test_awg2_policy_rolls_back_before_profile_issuance(db_session, rollout) -> None:
    replace_awg2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg2-lab-v1",
        endpoint_revision=AWG2_ENDPOINT_REVISION,
        server_record_id="pokrov-awg2-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
    )
    db_session.commit()
    user = SimpleNamespace(
        tg_id=1001, app_install_id="owner-device", app_platform="windows"
    )

    policy = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )

    assert policy["transport_profile"] == LEGACY_REALITY_FALLBACK


def test_missing_or_stale_material_rolls_back(db_session) -> None:
    rollout = _rollout()
    user = SimpleNamespace(
        tg_id=1001, app_install_id="owner-device", app_platform="windows"
    )
    missing = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )
    replace_awg2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg2-lab-v1",
        endpoint_revision=AWG2_ENDPOINT_REVISION,
        server_record_id="pokrov-awg2-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
        now=datetime.now() - timedelta(days=8),
    )
    db_session.commit()
    stale = resolved_client_policy(
        session=db_session,
        user=user,
        install_id="owner-device",
        rollout_config=rollout,
    )

    assert missing["transport_profile"] == LEGACY_REALITY_FALLBACK
    assert stale["transport_profile"] == LEGACY_REALITY_FALLBACK


def test_node_catalog_drops_raw_awg2_profiles() -> None:
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
                    "name": AWG2_LAB,
                    "enabled": True,
                    "kind": "awg",
                    "private_key": "must-not-enter-node-catalog",
                }
            ]
        ),
    )

    profiles = node_transport_profiles(node)

    assert [item["name"] for item in profiles] == [LEGACY_REALITY_FALLBACK]
    assert "must-not-enter-node-catalog" not in json.dumps(profiles)


def test_material_table_contains_only_ciphertext_not_plain_endpoint(db_session) -> None:
    replace_awg2_lab_material(
        db_session,
        tg_id=1001,
        install_id="owner-device",
        generation="awg2-lab-v1",
        endpoint_revision=AWG2_ENDPOINT_REVISION,
        server_record_id="pokrov-awg2-pl-01",
        node_code="pl",
        endpoint=_endpoint(),
    )
    db_session.commit()

    row = db_session.query(Awg2LabMaterial).one()
    serialized = json.dumps(
        {column.name: getattr(row, column.name) for column in row.__table__.columns},
        default=str,
    )
    assert _endpoint()["private_key"] not in serialized
    assert "192.0.2.10" not in serialized


def test_admin_intent_and_result_expose_only_fingerprints_and_safe_metadata() -> None:
    payload = {
        "tg_id": 1001,
        "install_id": "owner-device",
        "generation": "awg2-lab-v1",
        "endpoint_revision": AWG2_ENDPOINT_REVISION,
        "server_record_id": "pokrov-awg2-pl-01",
        "node_code": "pl",
        "endpoint": _endpoint(),
    }

    normalized = _normalize_awg2_lab_material_payload(payload)
    safe_result = _sanitize_awg2_lab_material_result(
        {
            "ok": True,
            "material": {
                "id": 7,
                "tg_id": 1001,
                "install_id": "owner-device",
                "generation": "awg2-lab-v1",
                "endpoint_revision": AWG2_ENDPOINT_REVISION,
                "server_record_id": "pokrov-awg2-pl-01",
                "node_code": "pl",
                "material_hash": "f" * 64,
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
    assert "192.0.2.10" not in serialized


def test_awg2_issuance_never_labels_unvalidated_rotation_with_old_generation(
    db_session, monkeypatch,
) -> None:
    now = datetime(2026, 9, 6, 0, 0, 0)
    options = dict(
        tg_id=1001,
        install_id="owner-device",
        endpoint_revision=AWG2_ENDPOINT_REVISION,
        server_record_id="pokrov-awg2-pl-01",
        node_code="pl",
        now=now,
    )
    first = replace_awg2_lab_material(
        db_session, generation="awg2-lab-v1", endpoint=_endpoint(), **options,
    )
    checked_snapshot = SimpleNamespace(**{
        column.name: getattr(first, column.name) for column in first.__table__.columns
    })
    rotated_endpoint = _endpoint()
    rotated_endpoint["peers"][0]["port"] += 1
    rotated = replace_awg2_lab_material(
        db_session, generation="awg2-lab-v2", endpoint=rotated_endpoint, **options,
    )
    reads = iter((checked_snapshot, rotated))
    monkeypatch.setattr(
        awg2_lab_service_module, "_active_material", lambda *args, **kwargs: next(reads),
    )
    try:
        config = build_managed_awg2_lab_config(
            db_session, tg_id=1001, install_id="owner-device",
            rollout_value=_rollout()[AWG2_LAB], title="POKROV", now=now,
        )
    except Awg2LabError as error:
        assert error.code == "material_not_ready"
    else:
        # Either reject the incompatible rotation or issue the checked row;
        # never expose its endpoint under the previous generation metadata.
        assert config["endpoints"][0]["peers"][0]["port"] == _endpoint()["peers"][0]["port"]
