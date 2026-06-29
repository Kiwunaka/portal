from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from test_smart_connect_api import _add_node, _auth_headers, _load_api, _rollout_payload, _start_trial, _utcnow


def test_client_subscription_preview_returns_order_without_raw_config(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=_rollout_payload())
        db.commit()
    finally:
        db.close()

    now = _utcnow()
    _add_node(api, code="pl", health_score=98.0, weight=110, last_health_at=now)
    _add_node(api, code="de", health_score=96.0, weight=105, last_health_at=now)
    _add_node(api, code="nl-free", health_score=99.0, weight=999, last_health_at=now)

    start_body = _start_trial(client, install_id="install-sub-preview")
    response = client.get("/api/client/subscription/preview?format=vless", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["client_format"] == "vless_raw"
    assert body["node_order"] == ["pl", "de"]
    assert "config_payload" not in body
    assert "sub_token" not in body


def test_client_subscription_preview_uses_provisioned_nodes_when_evidence_exists(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)

    db = api.SessionLocal()
    try:
        api._set_app_setting_json(s=db, key="network_rollout_config", value=_rollout_payload())
        db.commit()
    finally:
        db.close()

    now = _utcnow()
    pl_id = _add_node(api, code="pl", health_score=98.0, weight=110, last_health_at=now)
    _add_node(api, code="de", health_score=96.0, weight=105, last_health_at=now)

    start_body = _start_trial(client, install_id="install-sub-preview-provisioned")
    from models import User, UserNode

    db = api.SessionLocal()
    try:
        user = db.query(User).filter(User.sub_token.isnot(None)).one()
        db.add(UserNode(tg_id=int(user.tg_id), node_id=int(pl_id), client_uuid=str(user.uuid), panel_email=str(user.email)))
        db.commit()
    finally:
        db.close()

    response = client.get("/api/client/subscription/preview?format=vless", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    assert response.json()["node_order"] == ["pl"]
