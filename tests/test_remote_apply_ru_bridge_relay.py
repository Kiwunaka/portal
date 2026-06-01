from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "remote_apply_ru_bridge_relay.py"
    spec = importlib.util.spec_from_file_location("remote_apply_ru_bridge_relay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_build_bridge_xray_config_allows_only_non_us_targets() -> None:
    module = _load_module()

    config = module.build_bridge_xray_config(
        client_uuids=[
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        ],
        allowed_targets=[
            {"code": "pl", "host": "82.40.38.84", "port": 443},
            {"code": "nl", "host": "82.24.195.93", "port": 443},
            {"code": "us", "host": "82.21.92.142", "port": 443},
        ],
        private_key="private-redacted",
        server_names=["www.yandex.ru", "yandex.ru"],
        short_ids=["ab12cd34"],
        exclude_codes={"us"},
    )

    inbound = next(item for item in config["inbounds"] if item["tag"] == "ru-bridge-reality")
    assert inbound["port"] == 443
    assert len(inbound["settings"]["clients"]) == 2
    assert inbound["streamSettings"]["realitySettings"]["privateKey"] == "private-redacted"

    allow_rule = config["routing"]["rules"][0]
    assert allow_rule["inboundTag"] == ["ru-bridge-reality"]
    assert allow_rule["ip"] == ["82.40.38.84", "82.24.195.93"]
    assert allow_rule["port"] == "443"

    block_rule = config["routing"]["rules"][1]
    assert block_rule["outboundTag"] == "ru-bridge-block"
    assert all("82.21.92.142" not in str(rule) for rule in config["routing"]["rules"])


def test_rollout_patch_uses_public_bridge_metadata_without_private_key() -> None:
    module = _load_module()

    patch = module.build_rollout_ru_bridge_patch(
        endpoint_host="176.123.166.119",
        public_key="public-key",
        short_id="ab12cd34",
        excluded_node_codes=["us"],
    )

    bridge = patch["ru_bridge_relay"]
    assert bridge["enabled"] is True
    assert bridge["endpoint_host"] == "176.123.166.119"
    assert bridge["reality_public_key"] == "public-key"
    assert bridge["reality_short_id"] == "ab12cd34"
    assert bridge["excluded_node_codes"] == ["us"]
    assert "private" not in str(patch).lower()
