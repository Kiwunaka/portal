from __future__ import annotations

import importlib
import json
import sys
import time
from base64 import urlsafe_b64encode
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-oidc-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("BOT_TOKEN", "777000:test-bot-token")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_ID", "777000")
    monkeypatch.setenv("TELEGRAM_OAUTH_CLIENT_SECRET", "telegram-oidc-secret")
    monkeypatch.setenv("TELEGRAM_OAUTH_REDIRECT_URI", "https://app.pokrov.test/")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("WEBAPP_URL", "https://app.pokrov.test/?v=20260322")

    for name in [
        "api",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")
    web_auth_service = importlib.import_module("web_auth_service")
    return api, web_auth_service


def _b64url(data: bytes) -> str:
    return urlsafe_b64encode(data).decode("ascii").rstrip("=")


def test_oidc_start_returns_authorize_url_with_signed_state(monkeypatch, tmp_path):
    api, web_auth_service = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    response = client.get("/api/auth/telegram/oidc/start")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["mode"] == "oidc"

    parsed = urlparse(payload["auth_url"])
    assert parsed.scheme == "https"
    assert parsed.netloc == "oauth.telegram.org"
    assert parsed.path == "/auth"

    query = parse_qs(parsed.query)
    assert query["client_id"] == ["777000"]
    assert query["redirect_uri"] == ["https://app.pokrov.test/"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid profile telegram:bot_access"]
    assert query["code_challenge_method"] == ["S256"]

    state = query["state"][0]
    assert len(state) <= 240

    verified = web_auth_service.verify_telegram_oidc_state_token(state)
    assert verified is not None
    assert verified["redirect_uri"] == "https://app.pokrov.test/"
    assert len(str(verified["code_verifier"])) >= 43


def test_oidc_finish_issues_web_session_token(monkeypatch, tmp_path):
    api, web_auth_service = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    state_token = web_auth_service.create_telegram_oidc_state_token(
        redirect_uri="https://app.pokrov.test/",
    )

    async def fake_exchange_telegram_oidc_code(*, code: str, state_token: str):
        assert code == "oidc-code-123"
        assert state_token
        return {"id": 424242, "preferred_username": "pokrov_user"}

    monkeypatch.setattr(api, "exchange_telegram_oidc_code", fake_exchange_telegram_oidc_code)

    finish = client.post(
        "/api/auth/telegram/oidc/finish",
        json={"code": "oidc-code-123", "state": state_token},
    )

    assert finish.status_code == 200, finish.text
    payload = finish.json()
    assert payload["ok"] is True
    assert payload["user"]["id"] == 424242
    assert payload["user"]["username"] == "pokrov_user"
    assert payload["token"]

    session = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {payload['token']}"},
    )
    assert session.status_code == 200, session.text
    session_payload = session.json()
    assert session_payload["user"]["id"] == 424242
    assert session_payload["user"]["username"] == "pokrov_user"


def test_validate_telegram_oidc_id_token_accepts_valid_signature(monkeypatch, tmp_path):
    _api, web_auth_service = _load_api(monkeypatch, tmp_path)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "alg": "RS256",
                "n": _b64url(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")),
                "e": _b64url(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")),
            }
        ]
    }
    now = int(time.time())
    header = _b64url(b'{"alg":"RS256","kid":"test-key-id","typ":"JWT"}')
    claims = _b64url(
        json.dumps(
            {
                "iss": "https://oauth.telegram.org",
                "aud": "777000",
                "sub": "909090",
                "iat": now - 5,
                "exp": now + 3600,
                "id": 909090,
                "preferred_username": "pokrov_user",
            },
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signing_input = f"{header}.{claims}".encode("ascii")
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    id_token = f"{header}.{claims}.{_b64url(signature)}"

    verified = web_auth_service.validate_telegram_oidc_id_token(
        id_token=id_token,
        client_id="777000",
        jwks=jwks,
    )

    assert verified["id"] == 909090
    assert verified["preferred_username"] == "pokrov_user"
