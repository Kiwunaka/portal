from __future__ import annotations

import json

from portal_bot.happ_ios_subscription_service import render_happ_ios_profiles


TEST_UUID = "11111111-1111-4111-8111-111111111111"


def _material(prefix: str) -> dict:
    return {
        "host": f"{prefix}.example.test",
        "port": 443,
        "tls_server_name": "www.example.test",
        "reality_public_key": f"fake-public-key-{prefix}",
        "reality_short_id": f"fake-short-id-{prefix}",
        "fingerprint": "chrome",
        "flow": "xtls-rprx-vision",
    }


def test_renders_direct_and_real_bridge_profiles_in_deterministic_order() -> None:
    result = render_happ_ios_profiles(
        user_uuid=TEST_UUID,
        destinations=[
            {
                "code": "de",
                "label": "🇩🇪 Германия",
                **_material("de"),
                "bridges": [
                    {
                        "id": "mini",
                        "label": "Белые списки",
                        **_material("bridge-one"),
                    },
                    {
                        "id": "ru-spb",
                        "label": "Белые списки тип 2",
                        **_material("bridge-two"),
                    },
                ],
            },
            {
                "code": "us",
                "label": "🇺🇸 США",
                **_material("us"),
                "bridges": [],
            },
        ],
    )

    assert [row["remarks"] for row in result.profiles] == [
        "🇩🇪 Германия · Обычный",
        "🇩🇪 Германия · БС",
        "🇩🇪 Германия · БС 2",
        "🇺🇸 США · Обычный",
    ]
    assert result.exclusions == []

    direct = result.profiles[0]
    assert [row["tag"] for row in direct["outbounds"]] == ["proxy", "direct", "block"]
    assert "proxySettings" not in direct["outbounds"][0]

    bridged = result.profiles[1]
    assert [row["tag"] for row in bridged["outbounds"]] == [
        "proxy",
        "bridge",
        "direct",
        "block",
    ]
    destination = bridged["outbounds"][0]
    assert destination["settings"]["vnext"][0]["address"] == "de.example.test"
    assert destination["proxySettings"] == {"tag": "bridge", "transportLayer": True}
    assert bridged["outbounds"][1]["settings"]["vnext"][0]["address"] == "bridge-one.example.test"
    assert bridged["dns"]["servers"][0]["tag"] == "dns-remote"
    assert bridged["routing"]["rules"][0] == {
        "type": "field",
        "inboundTag": ["dns-remote"],
        "outboundTag": "proxy",
    }
    assert all(len(row["remarks"]) <= 30 for row in result.profiles)
    assert "detour" not in json.dumps(result.profiles, ensure_ascii=False)
    assert "rule_set" not in json.dumps(result.profiles, ensure_ascii=False)


def test_invalid_bridge_is_omitted_without_secret_values_in_summary() -> None:
    invalid_bridge = {
        "id": "mini",
        "label": "Белые списки",
        **_material("bridge-secret-host"),
        "reality_public_key": "",
    }
    result = render_happ_ios_profiles(
        user_uuid=TEST_UUID,
        destinations=[
            {
                "code": "de",
                "label": "🇩🇪 Германия",
                **_material("de-secret-host"),
                "bridges": [invalid_bridge],
            }
        ],
    )

    assert [row["remarks"] for row in result.profiles] == ["🇩🇪 Германия · Обычный"]
    assert result.exclusions == [
        {"node_code": "de", "mode": "mini", "reason": "invalid_bridge"}
    ]
    safe_summary = json.dumps(result.exclusions, ensure_ascii=False)
    assert "bridge-secret-host" not in safe_summary
    assert "fake-short-id" not in safe_summary


def test_invalid_destination_and_uuid_fail_closed() -> None:
    invalid_destination = render_happ_ios_profiles(
        user_uuid=TEST_UUID,
        destinations=[
            {
                "code": "de",
                "label": "🇩🇪 Германия",
                **_material("de"),
                "host": "",
            }
        ],
    )
    assert invalid_destination.profiles == []
    assert invalid_destination.exclusions == [
        {"node_code": "de", "mode": "direct", "reason": "invalid_destination"}
    ]

    invalid_uuid = render_happ_ios_profiles(
        user_uuid="not-a-uuid",
        destinations=[],
    )
    assert invalid_uuid.profiles == []
    assert invalid_uuid.exclusions == [
        {"node_code": "all", "mode": "all", "reason": "invalid_user_uuid"}
    ]
