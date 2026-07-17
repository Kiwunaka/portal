from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _sign_admin(*, tg_id: int = 9999) -> str:
    params = {
        "auth_date": str(int(datetime.now(timezone.utc).timestamp())),
        "query_id": f"intent-test-{tg_id}",
        "user": json.dumps(
            {"id": tg_id, "first_name": "Admin", "username": f"admin{tg_id}"},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    check = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
    secret = hmac.new(b"WebAppData", b"test_bot_token_123", hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def _admin_headers(*, tg_id: int = 9999) -> dict[str, str]:
    return {"X-Telegram-Init-Data": _sign_admin(tg_id=tg_id)}


def _load_api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "admin-action-intents.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "action-intent-test-secret")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999,8888")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    for name in (
        "api",
        "admin_action_intent_service",
        "admin_ops_service",
        "app_first_service",
        "account_foundation_service",
        "channel_bonus_service",
        "config",
        "control_panel",
        "db",
        "events_service",
        "free_cycle_service",
        "gift_cards_service",
        "internal_request_auth",
        "migrations",
        "models",
        "node_policy",
        "nodes_repo",
        "offers_service",
        "pay_attempts_service",
        "payment_providers",
        "points_service",
        "ru_probe_contract",
        "ru_probe_service",
        "shared_surface_facts",
        "tickets_repo",
        "transport_catalog",
        "web_auth_service",
        "worker",
    ):
        sys.modules.pop(name, None)
    return importlib.import_module("api")


def _seed_nodes(api) -> None:
    from models import Node

    session = api.SessionLocal()
    try:
        session.add_all(
            [
                Node(
                    code="nl",
                    name="Нидерланды",
                    host="nl.example.test",
                    panel_base_url="https://nl-panel.example.test",
                    panel_user="operator-secret",
                    panel_pass="SYNTHETIC-PANEL-SECRET",
                    inbound_id=1,
                    enabled=True,
                    accepting_new_clients=True,
                    is_draining=False,
                ),
                Node(
                    code="de",
                    name="Германия",
                    host="de.example.test",
                    inbound_id=1,
                    enabled=True,
                    accepting_new_clients=True,
                    is_draining=False,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def _prepare(
    client: TestClient,
    *,
    action: str = "node.disable",
    target_id: str = "nl",
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
):
    return client.post(
        "/api/admin/action-intents",
        headers=headers or _admin_headers(),
        json={
            "action": action,
            "target": {"type": "node", "id": target_id},
            "payload": {"force": False} if payload is None else payload,
        },
    )


def _execute_headers(
    intent_id: str,
    *,
    idempotency_key: str | None = None,
    confirmation_hash: str | None = None,
    tg_id: int = 9999,
) -> dict[str, str]:
    return {
        **_admin_headers(tg_id=tg_id),
        "X-Admin-Intent-Id": intent_id,
        "X-Admin-Idempotency-Key": idempotency_key or str(uuid.uuid4()),
        "X-Admin-Confirmation-SHA256": confirmation_hash
        or hashlib.sha256(b"NL").hexdigest(),
    }


def _detail_code(response) -> str:
    return str(response.json()["detail"]["code"])


def test_prepare_contract_is_frozen_redacted_and_unknown_actions_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)

    direct = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_admin_headers(),
        json={"force": False},
    )
    assert direct.status_code == 428
    assert _detail_code(direct) == "intent_required"

    unknown = _prepare(client, action="node.shell")
    assert unknown.status_code == 422
    assert _detail_code(unknown) == "unknown_action"

    response = _prepare(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {
        "ok",
        "intent_id",
        "action",
        "target",
        "risk_level",
        "preview",
        "payload_hash",
        "snapshot_hash",
        "entity_version_hash",
        "confirmation_challenge",
        "confirmation_challenge_kind",
        "expires_at",
    }
    assert body["action"] == "node.disable"
    assert body["target"] == {"type": "node", "id": "nl"}
    assert body["risk_level"] == "L3"
    assert body["confirmation_challenge"] == "NL"
    assert body["confirmation_challenge_kind"] == "exact_node_code"
    expires_at = datetime.fromisoformat(str(body["expires_at"]).replace("Z", "+00:00"))
    assert timedelta(minutes=9, seconds=55) <= expires_at - datetime.now(timezone.utc) <= timedelta(minutes=10, seconds=5)
    assert "synthetic-panel-secret" not in response.text.lower()
    assert "operator-secret" not in response.text.lower()
    assert "nl-panel.example.test" not in response.text.lower()

    from models import AdminActionIntent

    session = api.SessionLocal()
    try:
        row = session.query(AdminActionIntent).filter_by(id=body["intent_id"]).one()
        assert row.canonical_payload_json == '{"force":false}'
        assert json.loads(row.preview_snapshot_json) == body["preview"]
        assert row.payload_hash == body["payload_hash"]
        assert row.snapshot_hash == body["snapshot_hash"]
        assert row.entity_version_hash == body["entity_version_hash"]
        assert row.status == "prepared"
        assert row.client_idempotency_key is None
        assert row.admin_audit_id is None
        persisted = " ".join(
            str(value or "")
            for value in (
                row.canonical_payload_json,
                row.preview_snapshot_json,
                row.result_summary_json,
            )
        ).lower()
        assert "synthetic-panel-secret" not in persisted
        assert "operator-secret" not in persisted
    finally:
        session.close()


def test_consume_rechecks_binding_expiry_confirmation_and_entity_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)
    prepared = _prepare(client).json()
    intent_id = prepared["intent_id"]
    import admin_action_intent_service as service

    with pytest.raises(service.ActionIntentError) as actor_error:
        service.execute_action_intent(
            session_factory=api.SessionLocal,
            actor_tg_id=8888,
            intent_id=intent_id,
            idempotency_key=str(uuid.uuid4()),
            confirmation_sha256_header=hashlib.sha256(b"NL").hexdigest(),
            action="node.disable",
            target={"type": "node", "id": "nl"},
            payload={"force": False},
            audit_writer=api._add_admin_audit,
        )
    assert actor_error.value.code == "intent_mismatch"

    target_mismatch = client.post(
        "/api/admin/nodes/de/disable",
        headers=_execute_headers(intent_id),
        json={"force": False},
    )
    assert target_mismatch.status_code == 409
    assert _detail_code(target_mismatch) == "intent_mismatch"

    payload_mismatch = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id),
        json={"force": True},
    )
    assert payload_mismatch.status_code == 409
    assert _detail_code(payload_mismatch) == "intent_mismatch"

    assert service.confirmation_sha256("  Е\u0308  ") == service.confirmation_sha256("Ё")
    original_compare = service._constant_time_compare
    compare_calls: list[tuple[str, str]] = []

    def observed_compare(left: str, right: str) -> bool:
        compare_calls.append((left, right))
        return original_compare(left, right)

    monkeypatch.setattr(service, "_constant_time_compare", observed_compare)
    confirmation_mismatch = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id, confirmation_hash="0" * 64),
        json={"force": False},
    )
    assert confirmation_mismatch.status_code == 409
    assert _detail_code(confirmation_mismatch) == "confirmation_mismatch"
    assert len(compare_calls) == 1

    with pytest.raises(service.ActionIntentError) as action_error:
        service.execute_action_intent(
            session_factory=api.SessionLocal,
            actor_tg_id=9999,
            intent_id=intent_id,
            idempotency_key=str(uuid.uuid4()),
            confirmation_sha256_header=hashlib.sha256(b"NL").hexdigest(),
            action="node.enable",
            target={"type": "node", "id": "nl"},
            payload={"force": False},
            audit_writer=api._add_admin_audit,
        )
    assert action_error.value.code == "intent_mismatch"

    from models import AdminActionIntent, Node

    session = api.SessionLocal()
    try:
        row = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        frozen_preview = row.preview_snapshot_json
        node = session.query(Node).filter_by(code="nl").one()
        node.accepting_new_clients = False
        session.commit()
    finally:
        session.close()

    stale = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id),
        json={"force": False},
    )
    assert stale.status_code == 409
    assert _detail_code(stale) == "stale_intent"
    session = api.SessionLocal()
    try:
        row = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert row.preview_snapshot_json == frozen_preview
        assert row.status == "prepared"
    finally:
        session.close()

    expired_id = _prepare(client).json()["intent_id"]
    session = api.SessionLocal()
    try:
        row = session.query(AdminActionIntent).filter_by(id=expired_id).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()
    finally:
        session.close()
    expired = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(expired_id),
        json={"force": False},
    )
    assert expired.status_code == 409
    assert _detail_code(expired) == "expired_intent"
    session = api.SessionLocal()
    try:
        assert session.query(AdminActionIntent).filter_by(id=expired_id).one().status == "expired"
    finally:
        session.close()


def test_concurrent_consume_is_atomic_and_idempotency_replays_stored_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)
    intent_id = _prepare(client).json()["intent_id"]
    keys = [str(uuid.uuid4()), str(uuid.uuid4())]

    def execute(key: str):
        return client.post(
            "/api/admin/nodes/nl/disable",
            headers=_execute_headers(intent_id, idempotency_key=key),
            json={"force": False},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(execute, keys))
    assert sorted(response.status_code for response in responses) == [200, 409]
    winner_index = next(index for index, response in enumerate(responses) if response.status_code == 200)
    winner_key = keys[winner_index]
    completed = responses[winner_index].json()
    assert completed["status"] == "completed"
    assert completed["action_intent_id"] == intent_id
    assert isinstance(completed["audit_id"], int)
    loser = next(response for response in responses if response.status_code == 409)
    assert _detail_code(loser) == "intent_consumed"

    replay = execute(winner_key)
    assert replay.status_code == 200
    assert replay.json() == completed
    conflict = execute(str(uuid.uuid4()))
    assert conflict.status_code == 409
    assert _detail_code(conflict) == "intent_consumed"

    from models import AdminActionIntent, AdminAudit, Node

    session = api.SessionLocal()
    try:
        node = session.query(Node).filter_by(code="nl").one()
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        audits = session.query(AdminAudit).filter_by(action="admin_node_disable").all()
        assert (node.enabled, node.accepting_new_clients, node.is_draining) == (False, False, False)
        assert intent.status == "completed"
        assert intent.consumed_at is not None
        assert intent.client_idempotency_key == winner_key
        assert intent.admin_audit_id == audits[0].id
        assert len(audits) == 1
        safe_text = f"{intent.result_summary_json} {audits[0].meta}".lower()
        assert "synthetic-panel-secret" not in safe_text
        assert "canonical_payload" not in safe_text
    finally:
        session.close()


def test_audit_failure_rolls_back_node_and_intent_without_leaking_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)
    intent_id = _prepare(client).json()["intent_id"]

    def broken_audit(*_args, **_kwargs):
        raise RuntimeError("SYNTHETIC-PRIVATE-AUDIT-FAILURE")

    monkeypatch.setattr(api, "_add_admin_audit", broken_audit)
    response = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id),
        json={"force": False},
    )
    assert response.status_code == 503
    assert _detail_code(response) == "audit_failed"
    assert "synthetic-private-audit-failure" not in response.text.lower()

    from models import AdminActionIntent, AdminAudit, Node

    session = api.SessionLocal()
    try:
        node = session.query(Node).filter_by(code="nl").one()
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert (node.enabled, node.accepting_new_clients, node.is_draining) == (True, True, False)
        assert intent.status == "prepared"
        assert intent.client_idempotency_key is None
        assert intent.admin_audit_id is None
        assert session.query(AdminAudit).count() == 0
    finally:
        session.close()


def test_external_uncertain_result_is_audited_once_and_never_retried(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    import admin_action_intent_service as service

    external_action = "test.external"
    monkeypatch.setitem(
        service.ACTION_POLICIES,
        external_action,
        replace(
            service.ACTION_POLICIES["node.disable"],
            action=external_action,
            executor_kind="external",
        ),
    )
    client = TestClient(api.app)
    prepared_response = _prepare(client, action=external_action)
    assert prepared_response.status_code == 200, prepared_response.text
    intent_id = prepared_response.json()["intent_id"]
    idempotency_key = str(uuid.uuid4())
    attempts: list[int] = []

    def external_effect(_context):
        attempts.append(1)
        raise TimeoutError("SYNTHETIC-PRIVATE-PROVIDER-BODY")

    execute_kwargs = {
        "session_factory": api.SessionLocal,
        "actor_tg_id": 9999,
        "intent_id": intent_id,
        "idempotency_key": idempotency_key,
        "confirmation_sha256_header": hashlib.sha256(b"NL").hexdigest(),
        "action": external_action,
        "target": {"type": "node", "id": "nl"},
        "payload": {"force": False},
        "audit_writer": api._add_admin_audit,
        "external_executor": external_effect,
    }
    first = service.execute_action_intent(**execute_kwargs)
    second = service.execute_action_intent(**execute_kwargs)
    assert first == second
    assert first["status"] == "uncertain"
    assert first["action_intent_id"] == intent_id
    assert isinstance(first["audit_id"], int)
    assert attempts == [1]
    assert "synthetic-private-provider-body" not in json.dumps(first).lower()

    with pytest.raises(service.ActionIntentError) as conflict:
        service.execute_action_intent(
            **{**execute_kwargs, "idempotency_key": str(uuid.uuid4())}
        )
    assert conflict.value.code == "intent_consumed"

    from models import AdminActionIntent, AdminAudit

    session = api.SessionLocal()
    try:
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert intent.status == "uncertain"
        assert intent.admin_audit_id is not None
        assert session.query(AdminAudit).filter_by(id=intent.admin_audit_id).count() == 1
        safe_text = f"{intent.result_summary_json} {intent.external_error_hash}".lower()
        assert "synthetic-private-provider-body" not in safe_text
    finally:
        session.close()
