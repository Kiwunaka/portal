from __future__ import annotations

import hashlib
import base64
import importlib
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from portal_bot.tests.test_app_first_api import _load_api


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_payload(envelope: dict) -> dict:
    raw = str(envelope["payload_b64"])
    return json.loads(base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4)))


def _start_trial(client: TestClient, install_id: str = "install-emergency-123") -> str:
    response = client.post(
        "/api/client/session/start-trial",
        headers={"X-Forwarded-For": "198.51.100.87"},
        json={
            "install_id": install_id,
            "device_name": "Emergency test",
            "platform": "android",
            "os_version": "15",
            "app_version": "1.0.4",
            "locale": "ru",
            "time_zone": "Europe/Moscow",
            "trial_days": 5,
        },
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _stage_catalog(api, crypto) -> tuple[str, list[str]]:
    source = importlib.import_module("emergency_catalog_source")
    service = importlib.import_module("emergency_catalog_service")
    now = datetime.now(timezone.utc)
    materials = []
    for index in range(1, 5):
        line = (
            f"vless://{index:08x}-1111-4111-8111-{index:012x}"
            f"@reserve-{index}.example.com:443?type=tcp&security=reality"
            f"&pbk={'A' * 43}&sid={index:08x}&sni=cover-{index}.example.com"
            "&fp=chrome&flow=xtls-rprx-vision&encryption=none"
        )
        parsed = source.parse_emergency_source(line)
        assert not parsed.rejected
        materials.append(parsed.accepted[0])
    expected_digest = hashlib.sha256(b"POKROV emergency probe payload v1\n").hexdigest()
    probes = {
        item.stable_id: service.EndpointProbeResult(
            authenticated=True,
            payload_ok=True,
            payload_sha256=expected_digest,
            exit_country="DE",
            latency_ms=30 + index,
            verified_at=now,
            verification_source="controlled_core",
        )
        for index, item in enumerate(materials)
    }
    with api.SessionLocal() as db:
        snapshot = service.stage_snapshot(
            db,
            materials=materials,
            source_revision="a" * 40,
            source_digest="b" * 64,
            crypto=crypto,
            probes=probes,
            expected_payload_sha256=expected_digest,
            now=now,
        ).snapshot
        promoted = service.promote_snapshot(
            db,
            snapshot_id=snapshot.id,
            crypto=crypto,
            now=now,
        )
        db.commit()
        return promoted.snapshot.catalog_version, [item.stable_id for item in materials]


def _install_owned_hops(api) -> None:
    with api.SessionLocal() as db:
        for code, host in (("de", "de-owned.example.com"), ("ru", "ru-owned.example.com")):
            db.add(
                api.Node(
                    code=code,
                    name=f"Owned {code.upper()}",
                    host=host,
                    vless_port=443,
                    reality_sni="www.microsoft.com",
                    reality_pbk="B" * 43,
                    reality_sid="0123456789abcdef",
                    fingerprint="chrome",
                    flow="xtls-rprx-vision",
                    panel_base_url=f"https://{host}:8444",
                    panel_path="/panel/",
                    panel_user="unused",
                    panel_pass="unused",
                    inbound_id=1,
                    access_role="paid",
                    enabled=True,
                    is_healthy=True,
                )
            )
        db.commit()


def test_emergency_probe_payload_is_exact_and_cache_safe(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "request_public_ip", lambda request: "198.51.100.10")
    monkeypatch.setattr(api, "lookup_country_code", lambda value: "DE")
    with TestClient(api.app) as client:
        response = client.get("/api/emergency-probe/payload-v1")

    assert response.status_code == 200
    assert response.content == b"POKROV emergency probe payload v1\n"
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["x-pokrov-probe-schema"] == "pokrov-emergency-probe-payload-v1"
    assert response.headers["x-content-sha256"] == hashlib.sha256(response.content).hexdigest()
    assert response.headers["x-pokrov-exit-country"] == "DE"
    assert response.headers["cache-control"] == "no-store"


def test_authenticated_trial_gets_signed_safe_catalog_and_exact_direct_profile(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("EMERGENCY_CATALOG_SIGNING_KEY_ID", "emergency-test-v1")
    monkeypatch.setenv("EMERGENCY_CATALOG_MATERIAL_KEY_B64", _b64url(b"m" * 32))
    monkeypatch.setenv("EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64", _b64url(b"s" * 32))
    api = _load_api(monkeypatch, tmp_path)
    crypto_module = importlib.import_module("emergency_catalog_crypto")
    crypto = crypto_module.EmergencyCatalogCrypto.from_environment()
    with TestClient(api.app) as client:
        token = _start_trial(client)
        _install_owned_hops(api)
        catalog_version, reserve_ids = _stage_catalog(api, crypto)
        headers = {"Authorization": f"Bearer {token}"}

        no_country = client.get("/api/client/emergency-network/catalog", headers=headers)
        catalog_response = client.get(
            "/api/client/emergency-network/catalog?manual_limited_network=true",
            headers=headers,
        )
        assert no_country.status_code == 200
        assert no_country.json()["available"] is False
        assert no_country.json()["reason"] == "not_eligible"
        assert catalog_response.status_code == 200
        assert catalog_response.json()["available"] is True
        envelope = catalog_response.json()["envelope"]
        catalog_payload = _decode_payload(envelope)
        payload_bytes = base64.urlsafe_b64decode(
            envelope["payload_b64"] + "=" * ((4 - len(envelope["payload_b64"]) % 4) % 4)
        )
        crypto.verify_bytes(payload_bytes, envelope["signature_b64"])
        assert catalog_payload["catalog_revision"] == catalog_version
        assert catalog_payload["access"]["state"] == "trial_premium"
        assert catalog_payload["eligibility"]["source"] == "manual_limited_network"
        assert len(catalog_payload["items"]) == 4
        assert {item["id"] for item in catalog_payload["items"]} == set(reserve_ids)
        assert catalog_payload["items"][0]["modes"] == [
            "reserve_direct",
            "reserve_foreign",
            "reserve_ru_foreign",
        ]
        assert "outbound" not in json.dumps(catalog_payload)
        assert "reserve-1.example.com" not in json.dumps(catalog_payload)

        profile_response = client.post(
            "/api/client/emergency-network/profile",
            headers=headers,
            json={
                "catalog_revision": catalog_version,
                "reserve_id": reserve_ids[0],
                "chain_mode": "reserve_direct",
                "manual_limited_network": True,
            },
        )
        assert profile_response.status_code == 200, profile_response.text
        profile_envelope = profile_response.json()["envelope"]
        profile_payload = _decode_payload(profile_envelope)
        profile_bytes = base64.urlsafe_b64decode(
            profile_envelope["payload_b64"]
            + "=" * ((4 - len(profile_envelope["payload_b64"]) % 4) % 4)
        )
        crypto.verify_bytes(profile_bytes, profile_envelope["signature_b64"])
        assert profile_payload["catalog_revision"] == catalog_version
        assert profile_payload["reserve_id"] == reserve_ids[0]
        assert profile_payload["warp"] is False
        assert profile_payload["quick_settings_eligible"] is False
        assert profile_payload["config_payload"]["route"]["final"] == "POKROV emergency reserve"
        assert all(
            "detour" not in item
            for item in profile_payload["config_payload"]["outbounds"]
            if item.get("type") == "vless"
        )

        bundle_response = client.post(
            "/api/client/emergency-network/offline-bundle",
            headers=headers,
            json={"manual_limited_network": True},
        )
        assert bundle_response.status_code == 200, bundle_response.text
        assert bundle_response.headers["cache-control"] == "no-store"
        bundle = bundle_response.json()
        assert bundle["schemaVersion"] == "pokrov-emergency-offline-bundle-v1"
        assert _decode_payload(bundle["catalogEnvelope"])["catalog_revision"] == catalog_version
        assert len(bundle["profileEnvelopes"]) == 12
        assert {
            (item["reserveId"], item["chainMode"])
            for item in bundle["profileEnvelopes"]
        } == {
            (reserve_id, mode)
            for reserve_id in reserve_ids
            for mode in ("reserve_direct", "reserve_foreign", "reserve_ru_foreign")
        }
        for item in bundle["profileEnvelopes"]:
            payload = _decode_payload(item["envelope"])
            assert payload["catalog_revision"] == catalog_version
            assert payload["reserve_id"] == item["reserveId"]
            assert payload["chain_mode"] == item["chainMode"]

        for mode, expected_detours, expected_final in (
            (
                "reserve_foreign",
                {"POKROV owned foreign": "POKROV emergency reserve"},
                "POKROV owned foreign",
            ),
            (
                "reserve_ru_foreign",
                {
                    "POKROV owned RU": "POKROV emergency reserve",
                    "POKROV owned foreign": "POKROV owned RU",
                },
                "POKROV owned foreign",
            ),
        ):
            response = client.post(
                "/api/client/emergency-network/profile",
                headers=headers,
                json={
                    "catalog_revision": catalog_version,
                    "reserve_id": reserve_ids[0],
                    "chain_mode": mode,
                    "manual_limited_network": True,
                },
            )
            assert response.status_code == 200, response.text
            config = _decode_payload(response.json()["envelope"])["config_payload"]
            proxies = {
                item["tag"]: item
                for item in config["outbounds"]
                if item.get("type") == "vless"
            }
            assert config["route"]["final"] == expected_final
            assert config["route"]["rule_set"][0]["download_detour"] == expected_final
            assert {
                tag: item["detour"] for tag, item in proxies.items() if "detour" in item
            } == expected_detours
            assert all("domain_resolver" not in proxies[tag] for tag in expected_detours)


def test_emergency_profile_fails_closed_for_wrong_catalog_and_request_shape(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EMERGENCY_CATALOG_SIGNING_KEY_ID", "emergency-test-v1")
    monkeypatch.setenv("EMERGENCY_CATALOG_MATERIAL_KEY_B64", _b64url(b"m" * 32))
    monkeypatch.setenv("EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64", _b64url(b"s" * 32))
    api = _load_api(monkeypatch, tmp_path)
    crypto = importlib.import_module("emergency_catalog_crypto").EmergencyCatalogCrypto.from_environment()
    with TestClient(api.app) as client:
        token = _start_trial(client, "install-emergency-456")
        _catalog_version, reserve_ids = _stage_catalog(api, crypto)
        headers = {"Authorization": f"Bearer {token}"}
        wrong = client.post(
            "/api/client/emergency-network/profile",
            headers=headers,
            json={
                "catalog_revision": "emg-" + "f" * 32,
                "reserve_id": reserve_ids[0],
                "chain_mode": "reserve_direct",
                "manual_limited_network": True,
            },
        )
        extra = client.post(
            "/api/client/emergency-network/profile",
            headers=headers,
            json={
                "catalog_revision": "emg-" + "f" * 32,
                "reserve_id": reserve_ids[0],
                "chain_mode": "reserve_direct",
                "manual_limited_network": True,
                "warp": True,
            },
        )
    assert wrong.status_code == 409
    assert extra.status_code == 422
