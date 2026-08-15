from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from portal_bot.emergency_catalog_crypto import EmergencyCatalogCrypto
from portal_bot.emergency_eligibility_service import EmergencyEligibility
from portal_bot.emergency_profile_service import (
    EmergencyProfileError,
    OWNED_FOREIGN_TAG,
    OWNED_RU_TAG,
    RESERVE_TAG,
    build_emergency_singbox_config,
    build_profile_payload,
    build_safe_catalog_payload,
    validate_emergency_singbox_config,
)


NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def _outbound(*, host: str, user: str, grpc: bool = False) -> dict:
    outbound = {
        "type": "vless",
        "server": host,
        "server_port": 443,
        "uuid": user,
        "packet_encoding": "xudp",
        "tls": {
            "enabled": True,
            "server_name": "www.microsoft.com",
            "utls": {"enabled": True, "fingerprint": "chrome"},
            "reality": {
                "enabled": True,
                "public_key": "A" * 43,
                "short_id": "0123456789abcdef",
            },
        },
    }
    if grpc:
        outbound["transport"] = {"type": "grpc", "service_name": "reserve"}
    else:
        outbound["flow"] = "xtls-rprx-vision"
    return outbound


def _eligibility() -> EmergencyEligibility:
    return EmergencyEligibility(
        True,
        True,
        True,
        "cached_server_country",
        "RU",
        NOW + timedelta(hours=20),
    )


def test_signed_envelope_verifies_exact_payload_bytes_and_rejects_tamper() -> None:
    crypto = EmergencyCatalogCrypto.generate_for_tests()
    envelope = crypto.signed_envelope({"type": "test", "value": 7})
    payload = base64.urlsafe_b64decode(
        str(envelope["payload_b64"]) + "=" * ((4 - len(str(envelope["payload_b64"])) % 4) % 4)
    )
    assert json.loads(payload) == {"type": "test", "value": 7}
    crypto.verify_bytes(payload, str(envelope["signature_b64"]))
    with pytest.raises(Exception):
        crypto.verify_bytes(payload + b" ", str(envelope["signature_b64"]))


def test_safe_catalog_is_device_bound_bounded_and_contains_no_material() -> None:
    ids = [f"emg_{value:024x}" for value in range(1, 5)]
    catalog = {
        "catalog_version": "emg-" + "a" * 32,
        "expires_at": (NOW + timedelta(hours=30)).isoformat().replace("+00:00", "Z"),
        "endpoints": [
            {
                "stable_id": stable_id,
                "transport": "tcp",
                "outbound": _outbound(host=f"198.51.100.{index}", user=f"secret-{index}"),
            }
            for index, stable_id in enumerate(ids, start=1)
        ],
    }
    rows = {
        stable_id: SimpleNamespace(
            probe_state="healthy",
            exit_country="DE",
            latency_ms=40 + index,
            verification_source="synthetic_bs" if index == 1 else "controlled_core",
            verified_at=NOW - timedelta(minutes=index),
        )
        for index, stable_id in enumerate(ids, start=1)
    }
    result = build_safe_catalog_payload(
        catalog=catalog,
        endpoint_rows=rows,
        install_id="install-12345678",
        access_state="trial_premium",
        access_expiry=NOW + timedelta(days=5),
        eligibility=_eligibility(),
        supported_modes=("reserve_direct", "reserve_foreign"),
        now=NOW,
    )
    encoded = json.dumps(result)
    assert "198.51.100" not in encoded
    assert "secret-" not in encoded
    assert result["offline_valid_until"] == (NOW + timedelta(hours=6)).isoformat().replace(
        "+00:00", "Z"
    )
    assert result["items"][0]["verification"] == "synthetic_bs"
    assert result["items"][1]["verification"] == "ordinary"
    assert result["items"][0]["modes"] == ["reserve_direct", "reserve_foreign"]


def test_safe_catalog_distinguishes_failed_probe_from_stale_healthy_probe() -> None:
    ids = [f"emg_{value:024x}" for value in range(1, 5)]
    catalog = {
        "catalog_version": "emg-" + "a" * 32,
        "expires_at": (NOW + timedelta(hours=30)).isoformat().replace("+00:00", "Z"),
        "endpoints": [
            {
                "stable_id": stable_id,
                "transport": "tcp",
                "outbound": _outbound(host=f"198.51.100.{index}", user=f"secret-{index}"),
            }
            for index, stable_id in enumerate(ids, start=1)
        ],
    }
    rows = {
        ids[0]: SimpleNamespace(
            probe_state="unavailable",
            exit_country="DE",
            latency_ms=0,
            verification_source="controlled_core",
            verified_at=NOW - timedelta(minutes=1),
        ),
        **{
            stable_id: SimpleNamespace(
                probe_state="healthy",
                exit_country="DE",
                latency_ms=60,
                verification_source="controlled_core",
                verified_at=NOW - timedelta(hours=25),
            )
            for stable_id in ids[1:]
        },
    }
    result = build_safe_catalog_payload(
        catalog=catalog,
        endpoint_rows=rows,
        install_id="install-12345678",
        access_state="trial_premium",
        access_expiry=NOW + timedelta(days=5),
        eligibility=_eligibility(),
        supported_modes=("reserve_direct",),
        now=NOW,
    )
    assert result["items"][0]["status"] == "unavailable"
    assert {item["status"] for item in result["items"][1:]} == {"stale"}


@pytest.mark.parametrize(
    ("mode", "expected_final", "expected_detours"),
    [
        ("reserve_direct", RESERVE_TAG, {}),
        ("reserve_foreign", OWNED_FOREIGN_TAG, {OWNED_FOREIGN_TAG: RESERVE_TAG}),
        (
            "reserve_ru_foreign",
            OWNED_FOREIGN_TAG,
            {OWNED_RU_TAG: RESERVE_TAG, OWNED_FOREIGN_TAG: OWNED_RU_TAG},
        ),
    ],
)
def test_exact_reserve_first_chain_shapes(mode, expected_final, expected_detours) -> None:
    config = build_emergency_singbox_config(
        reserve_outbound=_outbound(host="reserve.example", user="reserve-user", grpc=True),
        chain_mode=mode,
        foreign_outbound=_outbound(host="foreign.example", user="owned-user"),
        ru_outbound=_outbound(host="ru.example", user="owned-user"),
    )
    proxies = {
        item["tag"]: item for item in config["outbounds"] if item.get("type") == "vless"
    }
    assert config["route"]["final"] == expected_final
    assert config["route"]["rule_set"][0]["download_detour"] == expected_final
    assert config["route"]["rules"] == [
        {"rule_set": ["geoip-ru"], "outbound": "direct"},
        {"protocol": "dns", "outbound": "dns-out"},
        {"ip_is_private": True, "outbound": "direct"},
    ]
    assert {tag: item["detour"] for tag, item in proxies.items() if "detour" in item} == expected_detours
    assert "domain_resolver" not in proxies[RESERVE_TAG]
    for tag in expected_detours:
        assert "domain_resolver" not in proxies[tag]
    assert proxies[RESERVE_TAG]["transport"]["type"] == "grpc"
    assert "flow" not in proxies[RESERVE_TAG]
    assert proxies[RESERVE_TAG]["tls"]["reality"]["enabled"] is True
    assert config["_meta"]["warp"] is False
    assert config["_meta"]["quick_settings_eligible"] is False


def test_validator_rejects_duplicate_cycle_depth_four_and_warp() -> None:
    valid = build_emergency_singbox_config(
        reserve_outbound=_outbound(host="reserve.example", user="reserve-user"),
        chain_mode="reserve_direct",
    )
    duplicate = json.loads(json.dumps(valid))
    duplicate["outbounds"].append(dict(duplicate["outbounds"][0]))
    with pytest.raises(EmergencyProfileError, match="profile_outbound_tag_invalid"):
        validate_emergency_singbox_config(duplicate)

    cycle = json.loads(json.dumps(valid))
    cycle["outbounds"][0]["detour"] = RESERVE_TAG
    with pytest.raises(EmergencyProfileError, match="profile_detour_invalid"):
        validate_emergency_singbox_config(cycle)

    depth = json.loads(json.dumps(valid))
    root = depth["outbounds"][0]
    root["tag"] = "a"
    depth["outbounds"][:1] = [
        root,
        {**_outbound(host="b.example", user="b"), "tag": "b", "detour": "a"},
        {**_outbound(host="c.example", user="c"), "tag": "c", "detour": "b"},
        {**_outbound(host="d.example", user="d"), "tag": "d", "detour": "c"},
    ]
    depth["route"]["final"] = "d"
    with pytest.raises(EmergencyProfileError, match="profile_detour_depth_exceeded"):
        validate_emergency_singbox_config(depth)

    warp = json.loads(json.dumps(valid))
    warp["outbounds"][0]["warp"] = {"enabled": True}
    with pytest.raises(EmergencyProfileError, match="profile_warp_forbidden"):
        validate_emergency_singbox_config(warp)


def test_profile_payload_is_bound_to_access_catalog_and_device() -> None:
    config = build_emergency_singbox_config(
        reserve_outbound=_outbound(host="reserve.example", user="reserve-user"),
        chain_mode="reserve_direct",
    )
    payload = build_profile_payload(
        catalog_revision="emg-" + "b" * 32,
        reserve_id="emg_" + "c" * 24,
        chain_mode="reserve_direct",
        install_id="install-12345678",
        access_state="paid_unlimited",
        access_expiry=NOW + timedelta(days=30),
        eligibility=_eligibility(),
        catalog_expiry=NOW + timedelta(hours=30),
        config_payload=config,
        now=NOW,
    )
    assert payload["type"] == "pokrov.emergency.profile"
    assert payload["route_scope"] == "all_except_ru"
    assert payload["warp"] is False
    assert payload["quick_settings_eligible"] is False
    assert payload["offline_valid_until"] == (NOW + timedelta(hours=6)).isoformat().replace(
        "+00:00", "Z"
    )
    assert len(payload["device_binding"]) == 64


def test_profile_payload_rejects_chain_metadata_that_does_not_match_topology() -> None:
    config = build_emergency_singbox_config(
        reserve_outbound=_outbound(host="reserve.example", user="reserve-user"),
        chain_mode="reserve_direct",
    )
    with pytest.raises(EmergencyProfileError, match="profile_topology_invalid"):
        build_profile_payload(
            catalog_revision="emg-" + "b" * 32,
            reserve_id="emg_" + "c" * 24,
            chain_mode="reserve_foreign",
            install_id="install-12345678",
            access_state="paid_unlimited",
            access_expiry=NOW + timedelta(days=30),
            eligibility=_eligibility(),
            catalog_expiry=NOW + timedelta(hours=30),
            config_payload=config,
            now=NOW,
        )


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda config: config["route"]["rules"].insert(
                0,
                {"protocol": "bittorrent", "outbound": "direct"},
            ),
            "profile_ru_route_invalid",
        ),
        (
            lambda config: config["route"]["rule_set"][0].update(
                {"url": "https://example.com/rules/geoip-ru.srs"}
            ),
            "profile_ru_route_invalid",
        ),
        (
            lambda config: config["outbounds"].append(
                {"type": "direct", "tag": "extra-direct"}
            ),
            "profile_topology_invalid",
        ),
        (
            lambda config: config["dns"]["servers"][1].update(
                {"detour": "direct"}
            ),
            "profile_dns_route_invalid",
        ),
    ],
)
def test_validator_rejects_extra_bypass_unowned_ruleset_and_dns_leak(
    mutation,
    code,
) -> None:
    config = build_emergency_singbox_config(
        reserve_outbound=_outbound(host="reserve.example", user="reserve-user"),
        chain_mode="reserve_direct",
    )
    mutation(config)

    with pytest.raises(EmergencyProfileError, match=code):
        validate_emergency_singbox_config(config)
