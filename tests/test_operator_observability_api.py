from __future__ import annotations

import hashlib
import importlib
import sys
import uuid
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class _FakePanel:
    async def add_client(self, **_kwargs):
        return True

    async def close(self):
        return None


def _load_api(monkeypatch, tmp_path: Path):
    database = tmp_path / "operator-api.db"
    accepted = tmp_path / "accepted"
    quarantine = tmp_path / "quarantine"
    accepted.mkdir()
    quarantine.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "operator-api-session-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "operator-api-antiabuse-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")
    monkeypatch.setenv("POKROV_SUPPORT_BUNDLE_L2_TG_IDS", "2002")
    monkeypatch.setenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR", str(accepted))
    monkeypatch.setenv("POKROV_SUPPORT_BUNDLE_QUARANTINE_DIR", str(quarantine))
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
        "operator_observability_service",
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
    return api, accepted


def _seed_bundle(api, accepted: Path) -> tuple[str, bytes]:
    models = importlib.import_module("models")
    payload = b"opaque encrypted operator API object"
    upload_id = str(uuid.uuid4())
    session = api.SessionLocal()
    try:
        ticket = api.SupportTicket(user_tg_id=1001, subject="Diagnostics")
        session.add(ticket)
        session.flush()
        session.add(
            models.SupportBundleUpload(
                upload_id=upload_id,
                ticket_id=ticket.id,
                owner_tg_id=1001,
                owner_account_id=str(uuid.uuid4()),
                owner_binding_hash=hashlib.sha256(upload_id.encode()).hexdigest(),
                idempotency_key=f"attempt-{upload_id}",
                bundle_id=f"diag-{uuid.uuid4().hex[:24]}",
                expected_size_bytes=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                content_type="application/vnd.pokrov.support-bundle+json",
                received_size_bytes=len(payload),
                status="validated",
                object_name=f"{upload_id}.pokrov-support",
                diagnostic_profile="standard",
                app_version="1.2.0",
                build_number="45",
                platform="windows",
                architecture="x86_64",
                last_phase="verify",
                last_error_code="CORE-START-01",
                proof_outcome="failed",
                observed_attempts=2,
                expires_at=datetime(2026, 8, 21, 13, 0, 0),
                completed_at=datetime(2026, 8, 21, 12, 0, 0),
                validated_at=datetime(2026, 8, 21, 12, 1, 0),
            )
        )
        session.commit()
    finally:
        session.close()
    (accepted / f"{upload_id}.pokrov-support").write_bytes(payload)
    return upload_id, payload


def test_l1_summary_cannot_issue_or_use_raw_bundle_access(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api, accepted = _load_api(monkeypatch, tmp_path)
    upload_id, _payload = _seed_bundle(api, accepted)
    client = TestClient(api.app)

    unauthenticated = client.get(f"/api/admin/support/bundles/{upload_id}/summary")
    assert unauthenticated.status_code in {401, 403}

    monkeypatch.setattr(api, "_require_admin", lambda _header: {"id": 1001})
    summary = client.get(f"/api/admin/support/bundles/{upload_id}/summary")
    assert summary.status_code == 200
    assert summary.json()["operator_role"] == "l1"
    assert "object_name" not in summary.text
    assert "owner_tg_id" not in summary.text

    denied = client.post(
        f"/api/admin/support/bundles/{upload_id}/access-grants",
        json={"reason_code": "customer_case"},
    )
    assert denied.status_code == 403
    raw_denied = client.get(
        f"/api/admin/support/bundles/{upload_id}/content",
        headers={"X-Pokrov-Support-Grant": "x" * 43},
    )
    assert raw_denied.status_code == 403


def test_l2_ciphertext_grant_is_header_bound_single_use_and_audited(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api, accepted = _load_api(monkeypatch, tmp_path)
    upload_id, payload = _seed_bundle(api, accepted)
    monkeypatch.setattr(api, "_require_admin", lambda _header: {"id": 2002})
    client = TestClient(api.app)

    issued = client.post(
        f"/api/admin/support/bundles/{upload_id}/access-grants",
        json={"reason_code": "release_validation"},
    )
    assert issued.status_code == 200
    token = issued.json()["access_grant"]
    downloaded = client.get(
        f"/api/admin/support/bundles/{upload_id}/content",
        headers={"X-Pokrov-Support-Grant": token},
    )
    assert downloaded.status_code == 200
    assert downloaded.content == payload
    assert downloaded.headers["cache-control"] == "no-store"
    assert token.encode("ascii") not in downloaded.request.url.query

    replay = client.get(
        f"/api/admin/support/bundles/{upload_id}/content",
        headers={"X-Pokrov-Support-Grant": token},
    )
    assert replay.status_code == 403
    held = client.post(
        f"/api/admin/support/bundles/{upload_id}/retention-hold",
        json={"hold": True, "reason_code": "incident_review"},
    )
    assert held.status_code == 200
    assert held.json()["bundle"]["retention_hold"] is True

    session = api.SessionLocal()
    try:
        models = importlib.import_module("models")
        audits = (
            session.query(models.SupportBundleAccessAudit)
            .order_by(models.SupportBundleAccessAudit.id)
            .all()
        )
        assert [row.action for row in audits] == [
            "grant_issued",
            "downloaded",
            "retention_hold_set",
        ]
        assert all(row.actor_tg_id == 2002 for row in audits)
        assert all(row.retention_hold for row in audits)
    finally:
        session.close()


def test_operator_release_health_and_known_issue_routes_are_observational(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api, _accepted = _load_api(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "_require_admin", lambda _header: {"id": 2002})
    client = TestClient(api.app)
    issue = {
        "candidate_label": "pokrov-1.2.0-beta.45",
        "issue_code": "REL-120",
        "app_version": "1.2.0",
        "build_number": "45",
        "platform": "windows",
        "severity": "error",
        "status": "open",
        "title": "Windows startup regression",
        "safe_summary": "Some Windows starts fail before the connection phase.",
        "error_code": "CORE-001",
        "incident_ref": "incident:INC-120",
        "release_ref": "release:pokrov-1.2.0-beta.45",
    }

    created = client.post("/api/admin/observability/known-issues", json=issue)
    listed = client.get(
        "/api/admin/observability/known-issues",
        params={"candidate_label": issue["candidate_label"]},
    )
    health = client.get("/api/admin/observability/release-health")
    assert created.status_code == 200
    assert listed.json()["issues"] == [created.json()["issue"]]
    assert health.status_code == 200
    assert health.json()["groups"] == []
