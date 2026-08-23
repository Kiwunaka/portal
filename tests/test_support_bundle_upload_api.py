import base64
import hashlib
import importlib
import json
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class _FakePanel:
    async def add_client(self, **_kwargs):
        return True

    async def close(self):
        return None


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _signed_key_set() -> str:
    return json.dumps(
        {
            "algorithm": "Ed25519",
            "key_id": "support-root-v1",
            "payload_b64": _b64(b"configured-signed-key-set"),
            "schema_version": 1,
            "signature_b64": _b64(b"s" * 64),
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "support-bundle-api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "support-bundle-session-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "support-bundle-antiabuse-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")
    monkeypatch.setenv(
        "POKROV_SUPPORT_UPLOAD_TICKET_SECRET",
        "support-bundle-upload-ticket-secret-32bytes",
    )
    monkeypatch.setenv("POKROV_SUPPORT_SIGNED_KEY_SET_JSON", _signed_key_set())
    support_mode_private = Ed25519PrivateKey.from_private_bytes(b"m" * 32)
    support_mode_private_raw = support_mode_private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", "support-root-v1")
    monkeypatch.setenv(
        "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64",
        _b64(support_mode_private_raw),
    )
    monkeypatch.setenv("POKROV_SUPPORT_MODE_CODE_SECRET", "c" * 48)
    monkeypatch.setenv(
        "POKROV_SUPPORT_BUNDLE_QUARANTINE_DIR",
        str(tmp_path / "quarantine"),
    )
    for name in [
        "api",
        "api_public_routes",
        "api_commercial_offer_routes",
        "api_observability_routes",
        "api_support_bundle_routes",
        "api_operator_observability_routes",
        "api_surface_routes",
        "api_admin_routes",
        "api_subscription_routes",
        "commercial_campaign_policy",
        "commercial_offer_service",
        "commercial_order_service",
        "commercial_attribution_service",
        "support_bundle_upload_service",
        "support_mode_service",
        "account_experience_service",
        "app_first_service",
        "account_foundation_service",
        "antiabuse_privacy_service",
        "auth_session_service",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
    ]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    api = importlib.import_module("api")
    monkeypatch.setattr(api, "ControlPanel", _FakePanel)
    return api


def test_api_redeems_case_bound_support_mode_code_once(monkeypatch, tmp_path: Path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    with api.SessionLocal() as session:
        user = session.query(api.User).one()
        ticket = api.SupportTicket(
            user_tg_id=int(user.tg_id),
            account_id=str(user.account_id or "") or None,
            environment="production",
            status="open",
            subject="Temporary support mode",
            version=1,
        )
        session.add(ticket)
        session.flush()
        spec = api.support_mode_service.normalize_issue_spec(
            {
                "allowed_categories": ["build", "events", "network", "redaction"],
                "allowed_collectors": [
                    "build_summary",
                    "network_summary",
                    "operational_events",
                    "redaction_report",
                ],
                "app_version": "1.2.0+30",
                "build_number": "candidate-local-30",
                "maximum_bundle_bytes": 1048576,
                "maximum_bundles": 2,
                "maximum_total_bytes": 1572864,
                "platform": "windows",
                "ttl_minutes": 20,
            }
        )
        issued = api.support_mode_service.issue_support_mode(
            session,
            ticket=ticket,
            spec=spec,
            actor_tg_id=9999,
        )
        activation_code = issued.activation_code
        session.commit()

    redeemed = client.post(
        "/api/client/support/mode/redeem",
        headers=auth,
        json={
            "app_version": "1.2.0+30",
            "build_number": "candidate-local-30",
            "code": activation_code,
            "platform": "windows",
        },
    )
    assert redeemed.status_code == 200, redeemed.text
    assert redeemed.json()["policy"]["key_id"] == "support-root-v1"

    replay = client.post(
        "/api/client/support/mode/redeem",
        headers=auth,
        json={
            "app_version": "1.2.0+30",
            "build_number": "candidate-local-30",
            "code": activation_code,
            "platform": "windows",
        },
    )
    assert replay.status_code == 409
    assert replay.json()["detail"]["code"] == "support_mode_code_consumed"


def _authenticated_client(api) -> tuple[TestClient, dict[str, str]]:
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": f"support-bundle-{uuid.uuid4()}",
            "device_name": "Support bundle test",
            "platform": "windows",
        },
    )
    assert started.status_code == 200
    return client, {"Authorization": f"Bearer {started.json()['session_token']}"}


def _ticket_payload(encrypted: bytes) -> dict:
    return {
        "bundle_id": "diag-0123456789abcdef01234567",
        "case_summary": "Версия 1.2.0; Windows; код CORE-START-01.",
        "content_type": "application/vnd.pokrov.support-bundle+json",
        "idempotency_key": "desktop-attempt-001",
        "sha256": hashlib.sha256(encrypted).hexdigest(),
        "size_bytes": len(encrypted),
    }


def test_api_upload_is_resumable_idempotent_and_never_unpacks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    encrypted = b'{"ciphertext_b64":"opaque-only"}'
    payload = _ticket_payload(encrypted)

    key_set = client.get("/api/client/support/bundles/key-set", headers=auth)
    assert key_set.status_code == 200
    assert key_set.json()["key_id"] == "support-root-v1"

    issued = client.post(
        "/api/client/support/bundles/upload-tickets",
        headers=auth,
        json=payload,
    )
    repeated_issue = client.post(
        "/api/client/support/bundles/upload-tickets",
        headers=auth,
        json=payload,
    )
    assert issued.status_code == 200
    assert repeated_issue.json() == issued.json()
    ticket = issued.json()
    upload_headers = {
        **auth,
        "Content-Type": "application/octet-stream",
        "X-Pokrov-Upload-Ticket": ticket["upload_ticket"],
        "X-Pokrov-Chunk-Offset": "0",
        "X-Pokrov-Chunk-Sha256": hashlib.sha256(encrypted).hexdigest(),
    }

    first_chunk = client.put(
        f"/api/client/support/bundles/uploads/{ticket['upload_id']}/chunks",
        headers=upload_headers,
        content=encrypted,
    )
    repeated_chunk = client.put(
        f"/api/client/support/bundles/uploads/{ticket['upload_id']}/chunks",
        headers=upload_headers,
        content=encrypted,
    )
    assert first_chunk.status_code == 202
    assert first_chunk.json()["complete"] is True
    assert repeated_chunk.json()["repeated"] is True

    status = client.get(
        f"/api/client/support/bundles/uploads/{ticket['upload_id']}",
        headers={
            **auth,
            "X-Pokrov-Upload-Ticket": ticket["upload_ticket"],
        },
    )
    assert status.status_code == 200
    assert status.json()["next_offset"] == len(encrypted)

    completed = client.post(
        f"/api/client/support/bundles/uploads/{ticket['upload_id']}/complete",
        headers={
            **auth,
            "X-Pokrov-Upload-Ticket": ticket["upload_ticket"],
        },
    )
    repeated_complete = client.post(
        f"/api/client/support/bundles/uploads/{ticket['upload_id']}/complete",
        headers={
            **auth,
            "X-Pokrov-Upload-Ticket": ticket["upload_ticket"],
        },
    )
    assert completed.status_code == 202
    assert completed.json()["status"] == "queued"
    assert repeated_complete.json() == completed.json()

    with api.SessionLocal() as session:
        assert session.query(api.SupportTicket).count() == 1
        assert session.query(api.SupportTicketMessage).count() == 1
        assert (
            session.query(api.support_bundle_uploads.SupportBundleUpload).count() == 1
        )
        assert session.query(api.support_bundle_uploads.SupportBundleChunk).count() == 1
    assert next((tmp_path / "quarantine").glob("*.chunk")).read_bytes() == encrypted

    source = (PORTAL_BOT_DIR / "api_support_bundle_routes.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()
    assert "support_bundle_ingest_service" not in source
    assert "zipfile" not in lowered
    assert "tarfile" not in lowered
    assert ".decrypt(" not in lowered
    assert "decryptor(" not in lowered


def test_api_rejects_cross_account_ticket_binding_and_missing_signing_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    with api.SessionLocal() as session:
        foreign = api.SupportTicket(
            user_tg_id=999_001,
            account_id="foreign-account",
            status="open",
            subject="Foreign",
        )
        session.add(foreign)
        session.commit()
        foreign_id = int(foreign.id)

    encrypted = b"opaque"
    payload = {**_ticket_payload(encrypted), "ticket_id": foreign_id}
    forbidden = client.post(
        "/api/client/support/bundles/upload-tickets",
        headers=auth,
        json=payload,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "ticket_access_denied"

    monkeypatch.delenv("POKROV_SUPPORT_UPLOAD_TICKET_SECRET")
    payload.pop("ticket_id")
    unavailable = client.post(
        "/api/client/support/bundles/upload-tickets",
        headers=auth,
        json=payload,
    )
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"]["code"] == "upload_signing_unavailable"


def test_api_requires_auth_and_rejects_unknown_ticket_fields(
    monkeypatch, tmp_path: Path
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    encrypted = b"opaque"
    payload = _ticket_payload(encrypted)

    unauthenticated = client.post(
        "/api/client/support/bundles/upload-tickets",
        json=payload,
    )
    assert unauthenticated.status_code == 401

    rejected = client.post(
        "/api/client/support/bundles/upload-tickets",
        headers=auth,
        json={**payload, "server_address": "planted.invalid"},
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "invalid_ticket_request"
    assert "planted.invalid" not in rejected.text
