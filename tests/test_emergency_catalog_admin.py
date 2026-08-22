from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _sign_init_data(*, bot_token: str, tg_id: int = 9999) -> str:
    params = {
        "auth_date": str(int(datetime.now(timezone.utc).timestamp())),
        "query_id": "emergency-admin-test",
        "user": json.dumps({"id": tg_id, "first_name": "Admin"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def _load_api(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'admin.db').as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "emergency-admin-secret")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.delenv("EMERGENCY_CATALOG_WORKER_ENABLED", raising=False)
    for name in list(sys.modules):
        if name in {
            "api",
            "api_admin_routes",
            "api_observability_routes",
            "api_support_bundle_routes",
            "api_operator_observability_routes",
            "api_public_routes",
            "api_commercial_offer_routes",
            "api_subscription_routes",
            "api_surface_routes",
            "commercial_campaign_policy",
            "commercial_offer_service",
            "commercial_order_service",
            "commercial_attribution_service",
            "config",
            "db",
            "migrations",
            "models",
            "module_slices",
            "observability_ingest",
            "request_correlation",
        } or name.startswith("emergency_catalog"):
            sys.modules.pop(name, None)
    return importlib.import_module("api")


def _headers() -> dict[str, str]:
    return {"X-Telegram-Init-Data": _sign_init_data(bot_token="test_bot_token_123")}


def _snapshot(models, *, status: str, offset: int):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return models.EmergencyCatalogSnapshot(
        id=str(uuid.uuid4()),
        catalog_version=f"emg-admin-{offset}",
        contract_version="pokrov-emergency-vless-reality-v1",
        source_revision=f"{offset:x}" * 40,
        source_digest=f"{offset:x}" * 64,
        status=status,
        candidate_count=6,
        healthy_count=5,
        active_endpoint_count=4 if status != "staging" else 0,
        catalog_ciphertext="secret-material" if status != "staging" else None,
        catalog_hash="f" * 64 if status != "staging" else None,
        signature_b64="secret-signature" if status != "staging" else None,
        signing_key_id="test-key" if status != "staging" else None,
        activated_at=now if status != "staging" else None,
        created_at=now,
        updated_at=now,
    )


def test_admin_status_is_authenticated_redacted_and_mutations_require_intent(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    models = importlib.import_module("models")
    crypto_module = importlib.import_module("emergency_catalog_crypto")
    service_module = importlib.import_module("emergency_catalog_service")
    crypto = crypto_module.EmergencyCatalogCrypto.generate_for_tests(key_id="admin-preview-v1")
    monkeypatch.setattr(
        crypto_module.EmergencyCatalogCrypto,
        "from_environment",
        classmethod(lambda cls: crypto),
    )
    active = _snapshot(models, status="active", offset=10)
    staging = _snapshot(models, status="staging", offset=11)
    superseded = _snapshot(models, status="superseded", offset=12)
    active_id, staging_id, superseded_id = active.id, staging.id, superseded.id
    active_payload = {
        "schema_version": service_module.CATALOG_SCHEMA_VERSION,
        "catalog_version": active.catalog_version,
        "endpoints": [{"stable_id": f"stable-{index}"} for index in range(1, 5)],
    }
    active.catalog_ciphertext = crypto.encrypt_json(active_payload)
    active.catalog_hash = crypto_module.catalog_sha256(active_payload)
    active.signature_b64 = crypto.sign(active_payload)
    active.signing_key_id = crypto.key_id
    with api.SessionLocal() as session:
        session.add_all((active, staging, superseded))
        session.flush()
        for index, state in enumerate(("healthy", "healthy", "pending", "unavailable"), start=1):
            session.add(
                models.EmergencyCatalogEndpoint(
                    snapshot_id=staging_id,
                    stable_id=f"stable-{index}",
                    ordinal=index,
                    transport="tcp",
                    endpoint_host_hash="raw-host-hash-must-not-leak",
                    material_ciphertext="raw-vless-material-must-not-leak",
                    material_hash="a" * 64,
                    probe_state=state,
                    authenticated=state == "healthy",
                    payload_ok=state == "healthy",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
        session.commit()

    client = TestClient(api.app)
    assert client.get("/api/admin/emergency-network/status").status_code in {401, 403}
    response = client.get("/api/admin/emergency-network/status", headers=_headers())

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["worker"]["configuration_state"] == "disabled"
    assert payload["active"]["snapshot_id"] == active_id
    assert payload["distribution"]["snapshot_id"] == active_id
    assert payload["probe_summary"] == {
        "snapshot_id": staging_id,
        "pending": 1,
        "healthy": 2,
        "unavailable": 1,
        "total": 4,
    }
    assert payload["snapshot_counts"] == {"active": 1, "staging": 1, "superseded": 1}
    assert [item["snapshot_id"] for item in payload["rollback_candidates"]] == [superseded_id]
    assert "raw-vless-material" not in response.text
    assert "raw-host-hash" not in response.text
    assert "secret-material" not in response.text
    assert "secret-signature" not in response.text

    monkeypatch.setenv("EMERGENCY_CATALOG_WORKER_ENABLED", "1")
    invalid_worker = client.get("/api/admin/emergency-network/status", headers=_headers())
    assert invalid_worker.status_code == 200, invalid_worker.text
    assert invalid_worker.json()["worker"] == {
        "enabled": True,
        "configuration_state": "invalid",
        "interval_seconds": None,
        "probe_concurrency": None,
    }
    assert "probe_adapter_missing_or_invalid" not in invalid_worker.text

    cases = (
        ("emergency_catalog.stage", "emergency_catalog", "global", "/api/admin/emergency-network/stage"),
        ("emergency_catalog.promote", "emergency_snapshot", staging_id, f"/api/admin/emergency-network/snapshots/{staging_id}/promote"),
        ("emergency_catalog.disable", "emergency_snapshot", active_id, f"/api/admin/emergency-network/snapshots/{active_id}/disable"),
        ("emergency_catalog.rollback", "emergency_snapshot", superseded_id, f"/api/admin/emergency-network/snapshots/{superseded_id}/rollback"),
    )
    for action, target_type, target_id, endpoint in cases:
        prepared = client.post(
            "/api/admin/action-intents",
            headers=_headers(),
            json={"action": action, "target": {"type": target_type, "id": target_id}, "payload": {}},
        )
        assert prepared.status_code == 200, prepared.text
        if action == "emergency_catalog.promote":
            assert "safe_delta" in prepared.json()["preview"]["after"]
        if action == "emergency_catalog.disable":
            assert "офлайн-кэш" in " ".join(prepared.json()["preview"]["warnings"])
        guarded = client.post(endpoint, headers=_headers(), json={})
        assert guarded.status_code == 428, guarded.text
        assert guarded.json()["detail"]["code"] == "intent_required"
