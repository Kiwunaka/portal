from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


class RequiredPayload(BaseModel):
    count: int


def _load_api(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'portal-test.db').as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "antiabuse-api-test-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")
    monkeypatch.setenv("API_CORS_ALLOWED_ORIGINS", "https://client.pokrov.test")
    for name in (
        "api",
        "account_experience_service",
        "app_first_service",
        "account_foundation_service",
        "antiabuse_privacy_service",
        "auth_session_service",
        "config",
        "db",
        "economy_service",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "channel_bonus_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
    ):
        monkeypatch.setitem(sys.modules, name, None)
        monkeypatch.delitem(sys.modules, name, raising=False)
    return importlib.import_module("api")


def test_controlled_errors_receive_safe_canonical_auth_header(monkeypatch, tmp_path):
    api = _load_api(monkeypatch, tmp_path)

    @api.app.get("/__test/error-header/plain-auth")
    def plain_auth():
        raise HTTPException(status_code=401, detail="Authentication required")

    @api.app.get("/__test/error-header/structured")
    def structured():
        raise HTTPException(status_code=400, detail={"code": "Domain_Code"})

    @api.app.get("/__test/error-header/explicit")
    def explicit():
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={
                "X-POKROV-Auth-Error": "existing_contract_code",
                "Retry-After": "17",
                "WWW-Authenticate": "Bearer",
                "Cache-Control": "no-store",
                "Content-Range": "bytes 0-0/1",
            },
        )

    @api.app.get("/__test/error-header/invalid-code")
    def invalid_code():
        raise HTTPException(status_code=401, detail={"code": "x" * 65})

    @api.app.get("/__test/error-header/unavailable")
    def unavailable():
        secret = "provider-secret-must-not-leak"
        try:
            raise RuntimeError(secret)
        except RuntimeError as error:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable",
            ) from error

    @api.app.post("/__test/error-header/validation-body")
    def validation_body(payload: RequiredPayload):
        return {"count": payload.count}

    @api.app.get("/__test/error-header/validation-query")
    def validation_query(page: int):
        return {"page": page}

    client = TestClient(api.app)

    plain_auth_response = client.get("/__test/error-header/plain-auth")
    assert plain_auth_response.status_code == 401
    assert plain_auth_response.headers["X-POKROV-Auth-Error"] == "auth_required"
    assert plain_auth_response.json() == {"detail": "Authentication required"}

    structured_response = client.get("/__test/error-header/structured")
    assert structured_response.status_code == 400
    assert structured_response.headers["X-POKROV-Auth-Error"] == "domain_code"
    assert structured_response.json() == {"detail": {"code": "Domain_Code"}}

    explicit_response = client.get("/__test/error-header/explicit")
    assert explicit_response.status_code == 401
    assert explicit_response.headers["X-POKROV-Auth-Error"] == "existing_contract_code"
    assert explicit_response.headers["Retry-After"] == "17"
    assert explicit_response.headers["WWW-Authenticate"] == "Bearer"
    assert explicit_response.headers["Cache-Control"] == "no-store"
    assert explicit_response.headers["Content-Range"] == "bytes 0-0/1"

    invalid_code_response = client.get("/__test/error-header/invalid-code")
    assert invalid_code_response.status_code == 401
    assert invalid_code_response.headers["X-POKROV-Auth-Error"] == "auth_required"
    assert "x" * 65 not in invalid_code_response.headers.values()

    missing_response = client.get("/__test/error-header/missing")
    assert missing_response.status_code == 404
    assert missing_response.headers["X-POKROV-Auth-Error"] == "resource_not_found"

    unavailable_response = client.get("/__test/error-header/unavailable")
    assert unavailable_response.status_code == 503
    assert unavailable_response.headers["X-POKROV-Auth-Error"] == "service_unavailable"
    assert unavailable_response.json() == {"detail": "Service temporarily unavailable"}
    assert "provider-secret-must-not-leak" not in unavailable_response.text
    assert "provider-secret-must-not-leak" not in unavailable_response.headers.values()

    validation_body_response = client.post("/__test/error-header/validation-body", json={})
    assert validation_body_response.status_code == 422
    assert validation_body_response.headers["content-type"].startswith("application/json")
    assert validation_body_response.headers["X-POKROV-Auth-Error"] == "request_invalid"
    assert isinstance(validation_body_response.json()["detail"], list)

    validation_query_response = client.get("/__test/error-header/validation-query?page=not-a-number")
    assert validation_query_response.status_code == 422
    assert validation_query_response.headers["content-type"].startswith("application/json")
    assert validation_query_response.headers["X-POKROV-Auth-Error"] == "request_invalid"
    assert isinstance(validation_query_response.json()["detail"], list)

    cors_response = client.get(
        "/__test/error-header/plain-auth",
        headers={"Origin": "https://client.pokrov.test"},
    )
    assert cors_response.status_code == 401
    assert cors_response.headers["Access-Control-Allow-Origin"] == "https://client.pokrov.test"
    assert cors_response.headers["X-POKROV-Auth-Error"] == "auth_required"
    assert _header_values(cors_response.headers["Access-Control-Expose-Headers"]) == {
        "x-pokrov-auth-error"
    }


def _header_values(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}
