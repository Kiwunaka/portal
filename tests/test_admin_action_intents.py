from __future__ import annotations

import asyncio
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
from sqlalchemy.exc import IntegrityError


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
        "news_draft_service",
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


def test_news_draft_requires_guarded_editor_approval_and_cannot_publish_twice(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import LiveUpdate, NewsDraft

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        draft = NewsDraft(
            source_name="Хабр · сетевые технологии",
            source_url="https://habr.com/ru/articles/123456/",
            source_title="Как изменилась работа сетей",
            source_item_sha256="a" * 64,
            fetch_run_id="run-news-1",
            source_published_at=now - timedelta(hours=1),
            status="pending",
            discovered_at=now,
        )
        session.add(draft)
        session.commit()
        draft_id = int(draft.id)
    finally:
        session.close()
    client = TestClient(api.app)
    listing = client.get(
        "/api/admin/news-drafts?status=pending&limit=20",
        headers=_admin_headers(),
    )
    assert listing.status_code == 200, listing.text
    assert listing.json()["counts"]["pending"] == 1
    assert listing.json()["drafts"][0]["source_title"] == "Как изменилась работа сетей"
    assert "source_item_sha256" not in listing.text
    payload = {
        "source_draft_id": draft_id,
        "title": "Что изменилось в работе сетей",
        "summary": "Коротко объясняем изменение и его практический смысл для пользователей POKROV.",
        "link": "https://habr.com/ru/articles/123456/",
        "is_active": True,
        "sort_order": 100,
    }
    direct = client.post(
        "/api/admin/live-updates", headers=_admin_headers(), json=payload
    )
    assert direct.status_code == 428
    prepared = _prepare(
        client,
        action="live_update.create",
        target_type="live_update",
        target_id="new",
        payload=payload,
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["preview"]["after"]["source_draft_id"] == draft_id

    completed = client.post(
        "/api/admin/live-updates",
        headers=_execute_headers(
            str(prepared.json()["intent_id"]),
            confirmation_hash=hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest(),
        ),
        json=payload,
    )
    assert completed.status_code == 200, completed.text

    session = api.SessionLocal()
    try:
        saved_draft = session.query(NewsDraft).filter(NewsDraft.id == draft_id).one()
        update = session.query(LiveUpdate).one()
        assert saved_draft.status == "approved"
        assert saved_draft.live_update_id == update.id
        assert saved_draft.reviewed_by_tg_id == 9999
        assert update.title == payload["title"]
        assert update.is_active is True
    finally:
        session.close()
    repeated = _prepare(
        client,
        action="live_update.create",
        target_type="live_update",
        target_id="new",
        payload=payload,
    )
    assert repeated.status_code == 409


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


def test_revenue_promos_and_referrals_use_exact_server_previews_and_atomic_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminAudit, Event, PromoCode, ReferralBonusQueue, User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add(
            PromoCode(
                code="WELCOME20",
                promo_type="discount",
                value=20,
                uses_left=90,
                expires_at=now + timedelta(days=14),
            )
        )
        session.add_all(
            [
                User(
                    tg_id=4101,
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                    referral_count=0,
                ),
                User(
                    tg_id=4102,
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=now + timedelta(days=30),
                ),
            ]
        )
        session.add(
            ReferralBonusQueue(
                order_id="safe-order-ref-4102",
                referrer_tg_id=4101,
                referred_tg_id=4102,
                queued_at=now - timedelta(hours=8),
                ready_at=now - timedelta(hours=1),
                status="pending",
                meta='{"provider_payload":"SYNTHETIC-RAW-REFERRAL-META"}',
            )
        )
        session.add(
            Event(
                tg_id=4102,
                event_name="connected_ok",
                source="app",
                created_at=now - timedelta(hours=2),
            )
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    create_payload = {
        "code": "SUMMER26",
        "promo_type": "days",
        "value": 7,
        "uses_left": 100,
        "expires_at": "2026-09-01T00:00:00",
    }
    direct_calls = [
        client.post("/api/admin/promos", headers=_admin_headers(), json=create_payload),
        client.patch(
            "/api/admin/promos/WELCOME20",
            headers=_admin_headers(),
            json={"value": 25, "expires_at": "2026-09-15T00:00:00"},
        ),
        client.delete("/api/admin/promos/WELCOME20", headers=_admin_headers()),
        client.post(
            "/api/admin/referrals/process",
            headers=_admin_headers(),
            json={"limit": 100, "force_without_activity": False},
        ),
    ]
    assert all(response.status_code == 428 for response in direct_calls)
    assert all(_detail_code(response) == "intent_required" for response in direct_calls)

    promo_payload = {"value": 25, "expires_at": "2026-09-15T00:00:00"}
    promo = _prepare(
        client,
        action="promo.update",
        target_type="promo",
        target_id="WELCOME20",
        payload=promo_payload,
    )
    assert promo.status_code == 200, promo.text
    assert promo.json()["preview"]["before"]["promo_code"] == "WELCOME20"
    assert promo.json()["preview"]["before"]["value"] == 20
    assert promo.json()["preview"]["after"]["value"] == 25
    assert promo.json()["preview"]["after"]["expires_at"] == "2026-09-15T00:00:00"

    delete = _prepare(
        client,
        action="promo.delete",
        target_type="promo",
        target_id="WELCOME20",
        payload={},
    )
    assert delete.status_code == 200, delete.text
    assert delete.json()["risk_level"] == "L3"
    assert delete.json()["confirmation_challenge"] == "WELCOME20"

    referral_payload = {"limit": 100, "force_without_activity": False}
    referral = _prepare(
        client,
        action="referral.process",
        target_type="referral_queue",
        target_id="ready",
        payload=referral_payload,
    )
    assert referral.status_code == 200, referral.text
    referral_body = referral.json()
    assert referral_body["preview"]["before"]["selection_count"] == 1
    assert referral_body["preview"]["before"]["decision_basis"] == "reward_ready"
    assert referral_body["preview"]["before"]["order_id"] == "safe-order-ref-4102"
    assert "SYNTHETIC-RAW-REFERRAL-META" not in json.dumps(
        referral_body, ensure_ascii=False
    )

    confirmation_hash = hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest()
    promo_done = client.patch(
        "/api/admin/promos/WELCOME20",
        headers=_execute_headers(
            str(promo.json()["intent_id"]),
            confirmation_hash=confirmation_hash,
        ),
        json=promo_payload,
    )
    assert promo_done.status_code == 200, promo_done.text
    referral_done = client.post(
        "/api/admin/referrals/process",
        headers=_execute_headers(
            str(referral_body["intent_id"]),
            confirmation_hash=confirmation_hash,
        ),
        json=referral_payload,
    )
    assert referral_done.status_code == 200, referral_done.text
    assert referral_done.json()["rewarded"] == 1

    session = api.SessionLocal()
    try:
        promo_row = session.query(PromoCode).filter_by(code="WELCOME20").one()
        assert promo_row.value == 25
        queue = session.query(ReferralBonusQueue).one()
        assert queue.status == "rewarded"
        audits = {
            row.action: json.loads(row.meta or "{}")
            for row in session.query(AdminAudit)
            .filter(
                AdminAudit.action.in_(["admin_promo_update", "admin_referrals_process"])
            )
            .all()
        }
        assert set(audits) == {"admin_promo_update", "admin_referrals_process"}
        assert audits["admin_promo_update"]["from_code"] == "WELCOME20"
        assert audits["admin_referrals_process"]["queue_ids"] == [int(queue.id)]
        assert "safe-order-ref-4102" not in json.dumps(
            audits["admin_referrals_process"]
        )
        assert "SYNTHETIC-RAW-REFERRAL-META" not in json.dumps(audits)
    finally:
        session.close()


def _prepare(
    client: TestClient,
    *,
    action: str = "node.disable",
    target_type: str = "node",
    target_id: str = "nl",
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
):
    return client.post(
        "/api/admin/action-intents",
        headers=headers or _admin_headers(),
        json={
            "action": action,
            "target": {"type": target_type, "id": target_id},
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


def _execute_node_action(
    client: TestClient,
    *,
    action: str,
    intent_id: str,
    payload: dict[str, object],
    idempotency_key: str | None = None,
    confirmation: str = "ПОДТВЕРДИТЬ",
):
    command = action.split(".", 1)[1]
    return client.post(
        f"/api/admin/nodes/nl/{command}",
        headers=_execute_headers(
            intent_id,
            idempotency_key=idempotency_key,
            confirmation_hash=hashlib.sha256(confirmation.encode("utf-8")).hexdigest(),
        ),
        json=payload,
    )


def _detail_code(response) -> str:
    return str(response.json()["detail"]["code"])


def _run(coroutine):
    return asyncio.run(coroutine)


def test_prepare_contract_is_frozen_redacted_and_unknown_actions_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)

    for command, payload in (
        ("drain", {"force": False}),
        ("undrain", {"force": False}),
        ("enable", {"force": False}),
        ("disable", {"force": False}),
        ("resync", {"limit": 50, "dry_run": False}),
    ):
        direct = client.post(
            f"/api/admin/nodes/nl/{command}",
            headers=_admin_headers(),
            json=payload,
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
    assert (
        timedelta(minutes=9, seconds=55)
        <= expires_at - datetime.now(timezone.utc)
        <= timedelta(minutes=10, seconds=5)
    )
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


def test_all_node_policies_execute_once_with_atomic_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)

    class EmptyPanel:
        login_calls = 0

        async def login(self):
            EmptyPanel.login_calls += 1
            return True

        async def close(self):
            return True

    monkeypatch.setattr(api, "ControlPanel", EmptyPanel)
    cases = (
        ("node.drain", {"force": False}, "ПОДТВЕРДИТЬ", (True, False, True)),
        ("node.undrain", {"force": False}, "ПОДТВЕРДИТЬ", (True, True, False)),
        ("node.disable", {"force": False}, "NL", (False, False, False)),
        ("node.enable", {"force": False}, "ПОДТВЕРДИТЬ", (True, True, False)),
    )
    for action, payload, confirmation, expected_lifecycle in cases:
        prepared = _prepare(client, action=action, payload=payload)
        assert prepared.status_code == 200, prepared.text
        intent_id = str(prepared.json()["intent_id"])
        idempotency_key = str(uuid.uuid4())
        completed = _execute_node_action(
            client,
            action=action,
            intent_id=intent_id,
            payload=payload,
            idempotency_key=idempotency_key,
            confirmation=confirmation,
        )
        assert completed.status_code == 200, completed.text
        body = completed.json()
        assert body["status"] == "completed"
        assert body["action_intent_id"] == intent_id
        assert isinstance(body["audit_id"], int)
        node = body["node"]
        assert (
            node["enabled"],
            node["accepting_new_clients"],
            node["is_draining"],
        ) == expected_lifecycle
        replay = _execute_node_action(
            client,
            action=action,
            intent_id=intent_id,
            payload=payload,
            idempotency_key=idempotency_key,
            confirmation=confirmation,
        )
        assert replay.json() == body

    resync_payload = {"limit": 50, "dry_run": False}
    prepared = _prepare(client, action="node.resync", payload=resync_payload)
    assert prepared.status_code == 200, prepared.text
    intent_id = str(prepared.json()["intent_id"])
    idempotency_key = str(uuid.uuid4())
    completed = _execute_node_action(
        client,
        action="node.resync",
        intent_id=intent_id,
        payload=resync_payload,
        idempotency_key=idempotency_key,
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["result"] == {
        "changed": 0,
        "count": 0,
        "failed": 0,
        "skipped": 0,
    }
    assert (
        _execute_node_action(
            client,
            action="node.resync",
            intent_id=intent_id,
            payload=resync_payload,
            idempotency_key=idempotency_key,
        ).json()
        == completed.json()
    )
    assert EmptyPanel.login_calls == 1

    from models import AdminActionIntent, AdminAudit

    session = api.SessionLocal()
    try:
        intents = session.query(AdminActionIntent).all()
        assert len(intents) == 5
        assert all(row.status == "completed" for row in intents)
        assert session.query(AdminAudit).count() == 5
    finally:
        session.close()


def test_resync_freezes_redacted_selection_and_uncertain_result_never_retries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)

    from models import AdminActionIntent, AdminAudit, Node, User, UserNode

    recipient_ids = (700_001, 700_002)
    private_values = (
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "recipient-one@example.test",
        "recipient-two@example.test",
    )

    def add_recipient(index: int) -> None:
        session = api.SessionLocal()
        try:
            source = session.query(Node).filter_by(code="nl").one()
            user = User(
                tg_id=recipient_ids[index],
                uuid=private_values[index],
                email=private_values[index + 2],
                username=f"private-recipient-{index}",
                sub_type="PAID",
                current_plan_code="1_month",
                expiry_at=datetime.now(timezone.utc).replace(tzinfo=None)
                + timedelta(days=30),
                is_active=True,
            )
            session.add(user)
            session.flush()
            session.add(
                UserNode(
                    tg_id=int(user.tg_id),
                    node_id=int(source.id),
                    client_uuid=str(user.uuid),
                    panel_email=str(user.email),
                )
            )
            session.commit()
        finally:
            session.close()

    add_recipient(0)
    client = TestClient(api.app)
    payload = {"limit": 50, "dry_run": False}
    first = _prepare(client, action="node.resync", payload=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["preview"]["selection"]["count"] == 1
    assert len(first_body["preview"]["selection"]["hash"]) == 64
    assert all(value.lower() not in first.text.lower() for value in private_values)
    assert all(str(value) not in first.text for value in recipient_ids)

    add_recipient(1)
    stale = _execute_node_action(
        client,
        action="node.resync",
        intent_id=str(first_body["intent_id"]),
        payload=payload,
        confirmation="ПОДТВЕРДИТЬ",
    )
    assert stale.status_code == 409
    assert _detail_code(stale) == "stale_intent"

    attempts: list[int] = []

    class UncertainPanel:
        async def login(self):
            return True

        async def close(self):
            return True

        async def ensure_user_on_all_nodes(self, **_kwargs):
            attempts.append(1)
            raise RuntimeError("SYNTHETIC-PRIVATE-PANEL-FAILURE")

    monkeypatch.setattr(api, "ControlPanel", UncertainPanel)
    prepared = _prepare(client, action="node.resync", payload=payload)
    assert prepared.status_code == 200, prepared.text
    prepared_body = prepared.json()
    assert prepared_body["preview"]["selection"]["count"] == 2
    intent_id = str(prepared_body["intent_id"])
    idempotency_key = str(uuid.uuid4())
    uncertain = _execute_node_action(
        client,
        action="node.resync",
        intent_id=intent_id,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    assert uncertain.status_code == 200, uncertain.text
    result = uncertain.json()
    assert result["status"] == "uncertain"
    assert result["result_code"] == "external_exception"
    assert result["action_intent_id"] == intent_id
    assert isinstance(result["audit_id"], int)
    assert (
        _execute_node_action(
            client,
            action="node.resync",
            intent_id=intent_id,
            payload=payload,
            idempotency_key=idempotency_key,
        ).json()
        == result
    )
    assert attempts == [1]

    session = api.SessionLocal()
    try:
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        audit = session.query(AdminAudit).filter_by(id=intent.admin_audit_id).one()
        safe_text = " ".join(
            (
                intent.canonical_payload_json,
                intent.preview_snapshot_json,
                str(intent.result_summary_json or ""),
                str(audit.meta or ""),
            )
        ).lower()
        assert all(value.lower() not in safe_text for value in private_values)
        assert all(str(value) not in safe_text for value in recipient_ids)
        audit_meta = json.loads(str(audit.meta))
        assert (
            audit_meta["selection_hash"]
            == prepared_body["preview"]["selection"]["hash"]
        )
        assert audit_meta["selected_count"] == 2
        assert audit_meta["outcome"] == "uncertain"
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
        _run(
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
        )
    assert actor_error.value.code == "intent_mismatch"
    assert actor_error.value.intent_id is None

    target_mismatch = client.post(
        "/api/admin/nodes/de/disable",
        headers=_execute_headers(intent_id),
        json={"force": False},
    )
    assert target_mismatch.status_code == 409
    assert _detail_code(target_mismatch) == "intent_mismatch"
    assert target_mismatch.json()["detail"]["intent_id"] == intent_id

    payload_mismatch = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id),
        json={"force": True},
    )
    assert payload_mismatch.status_code == 409
    assert _detail_code(payload_mismatch) == "intent_mismatch"
    assert payload_mismatch.json()["detail"]["intent_id"] == intent_id

    assert service.confirmation_sha256("  Е\u0308  ") == service.confirmation_sha256(
        "Ё"
    )
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
    assert confirmation_mismatch.json()["detail"]["intent_id"] == intent_id
    assert len(compare_calls) == 1

    with pytest.raises(service.ActionIntentError) as action_error:
        _run(
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
        )
    assert action_error.value.code == "intent_mismatch"
    assert action_error.value.intent_id == intent_id

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
    assert stale.json()["detail"]["intent_id"] == intent_id
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
    assert expired.json()["detail"]["intent_id"] == expired_id
    session = api.SessionLocal()
    try:
        assert (
            session.query(AdminActionIntent).filter_by(id=expired_id).one().status
            == "expired"
        )
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
    winner_index = next(
        index for index, response in enumerate(responses) if response.status_code == 200
    )
    winner_key = keys[winner_index]
    completed = responses[winner_index].json()
    assert completed["status"] == "completed"
    assert completed["action_intent_id"] == intent_id
    assert isinstance(completed["audit_id"], int)
    loser = next(response for response in responses if response.status_code == 409)
    assert _detail_code(loser) == "intent_consumed"
    assert loser.json()["detail"]["intent_id"] == intent_id
    assert loser.json()["detail"]["audit_id"] == completed["audit_id"]

    replay = execute(winner_key)
    assert replay.status_code == 200
    assert replay.json() == completed
    conflict = execute(str(uuid.uuid4()))
    assert conflict.status_code == 409
    assert _detail_code(conflict) == "intent_consumed"
    assert conflict.json()["detail"]["intent_id"] == intent_id
    assert conflict.json()["detail"]["audit_id"] == completed["audit_id"]

    from models import AdminActionIntent, AdminAudit, Node

    session = api.SessionLocal()
    try:
        node = session.query(Node).filter_by(code="nl").one()
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        audits = session.query(AdminAudit).filter_by(action="admin_node_disable").all()
        assert (node.enabled, node.accepting_new_clients, node.is_draining) == (
            False,
            False,
            False,
        )
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
    assert response.json()["detail"]["intent_id"] == intent_id
    assert "synthetic-private-audit-failure" not in response.text.lower()

    from models import AdminActionIntent, AdminAudit, Node

    session = api.SessionLocal()
    try:
        node = session.query(Node).filter_by(code="nl").one()
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert (node.enabled, node.accepting_new_clients, node.is_draining) == (
            True,
            True,
            False,
        )
        assert intent.status == "prepared"
        assert intent.client_idempotency_key is None
        assert intent.admin_audit_id is None
        assert session.query(AdminAudit).count() == 0
    finally:
        session.close()


def test_mapping_guard_rejects_new_assignment_after_nonforce_disable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)
    intent_id = _prepare(client).json()["intent_id"]
    disabled = client.post(
        "/api/admin/nodes/nl/disable",
        headers=_execute_headers(intent_id),
        json={"force": False},
    )
    assert disabled.status_code == 200, disabled.text

    from models import Node, UserNode

    session = api.SessionLocal()
    try:
        node = session.query(Node).filter_by(code="nl").one()
        session.add(
            UserNode(
                tg_id=777000,
                node_id=int(node.id),
                client_uuid=str(uuid.uuid4()),
                panel_email="guard-test@example.test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.query(UserNode).filter_by(node_id=int(node.id)).count() == 0
    finally:
        session.close()


def test_external_executor_outcomes_are_async_bounded_finalized_and_not_retried(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    import admin_action_intent_service as service
    from models import Node

    session = api.SessionLocal()
    try:
        session.add_all(
            [
                Node(
                    code="pl",
                    name="Польша",
                    host="pl.example.test",
                    inbound_id=1,
                    enabled=True,
                    accepting_new_clients=True,
                    is_draining=False,
                ),
                Node(
                    code="it",
                    name="Италия",
                    host="it.example.test",
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

    def prepare_intent(node_code: str = "nl") -> str:
        response = _prepare(
            client,
            action=external_action,
            target_id=node_code,
        )
        assert response.status_code == 200, response.text
        return str(response.json()["intent_id"])

    def execute(
        intent_id: str,
        idempotency_key: str,
        executor,
        *,
        timeout: float = 1.0,
        node_code: str = "nl",
    ) -> dict:
        return _run(
            service.execute_action_intent(
                session_factory=api.SessionLocal,
                actor_tg_id=9999,
                intent_id=intent_id,
                idempotency_key=idempotency_key,
                confirmation_sha256_header=hashlib.sha256(
                    node_code.upper().encode("utf-8")
                ).hexdigest(),
                action=external_action,
                target={"type": "node", "id": node_code},
                payload={"force": False},
                audit_writer=api._add_admin_audit,
                external_executor=executor,
                external_timeout_seconds=timeout,
            )
        )

    async_attempts: list[int] = []
    provider_reference = "SYNTHETIC-PRIVATE-PROVIDER-JOB"

    async def async_success(_context):
        async_attempts.append(1)
        await asyncio.sleep(0)
        return {
            "ok": True,
            "code": "provider_completed",
            "changed": 1,
            "job_id": provider_reference,
        }

    completed_id = prepare_intent()
    completed_key = str(uuid.uuid4())
    completed = execute(completed_id, completed_key, async_success)
    assert completed["status"] == "completed"
    assert completed["result_code"] == "provider_completed"
    assert completed["result"]["changed"] == 1
    assert len(completed["result"]["external_reference_hash"]) == 64
    assert provider_reference.lower() not in json.dumps(completed).lower()
    assert async_attempts == [1]

    negative_attempts: list[int] = []

    def sync_negative(_context):
        negative_attempts.append(1)
        return {"ok": False, "code": "provider_rejected", "failed": 1}

    failed_id = prepare_intent()
    failed_key = str(uuid.uuid4())
    failed = execute(failed_id, failed_key, sync_negative)
    assert failed["status"] == "failed"
    assert failed["result_code"] == "provider_rejected"
    assert execute(failed_id, failed_key, sync_negative) == failed
    assert negative_attempts == [1]

    timeout_attempts: list[int] = []

    async def hangs(_context):
        timeout_attempts.append(1)
        await asyncio.sleep(1)
        return {"ok": True, "code": "too_late"}

    timeout_id = prepare_intent("de")
    timeout_key = str(uuid.uuid4())
    timed_out = execute(
        timeout_id,
        timeout_key,
        hangs,
        timeout=0.01,
        node_code="de",
    )
    assert timed_out["status"] == "uncertain"
    assert timed_out["result_code"] == "external_timeout"
    assert (
        execute(
            timeout_id,
            timeout_key,
            hangs,
            timeout=0.01,
            node_code="de",
        )
        == timed_out
    )
    assert timeout_attempts == [1]

    malformed_secret = "SYNTHETIC-PRIVATE-MALFORMED-BODY"
    malformed_id = prepare_intent("pl")
    malformed = execute(
        malformed_id,
        str(uuid.uuid4()),
        lambda _context: {"message": malformed_secret},
        node_code="pl",
    )
    assert malformed["status"] == "uncertain"
    assert malformed["result_code"] == "external_result_malformed"

    exception_secret = "SYNTHETIC-PRIVATE-PROVIDER-BODY"
    exception_attempts: list[int] = []

    def raises_private(_context):
        exception_attempts.append(1)
        raise RuntimeError(exception_secret)

    exception_id = prepare_intent("it")
    exception_key = str(uuid.uuid4())
    raised = execute(
        exception_id,
        exception_key,
        raises_private,
        node_code="it",
    )
    assert raised["status"] == "uncertain"
    assert raised["result_code"] == "external_exception"
    assert (
        execute(
            exception_id,
            exception_key,
            raises_private,
            node_code="it",
        )
        == raised
    )
    assert exception_attempts == [1]

    stale_id = prepare_intent()
    stale_key = str(uuid.uuid4())
    session = api.SessionLocal()
    try:
        from models import AdminActionIntent

        intent = session.query(AdminActionIntent).filter_by(id=stale_id).one()
        audit = api._add_admin_audit(
            session=session,
            actor_tg_id=9999,
            action="admin_node_disable",
            meta={"action_intent_id": stale_id, "outcome": "executing"},
        )
        executing = {
            "ok": True,
            "status": "executing",
            "action_intent_id": stale_id,
            "audit_id": int(audit.id),
        }
        intent.status = "executing"
        intent.client_idempotency_key = stale_key
        intent.consumed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        intent.admin_audit_id = int(audit.id)
        intent.result_code = "executing"
        intent.result_summary_json = json.dumps(executing, separators=(",", ":"))
        intent.result_hash = "e" * 64
        intent.updated_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        session.commit()
    finally:
        session.close()

    stale_effect_calls: list[int] = []

    def stale_effect(_context):
        stale_effect_calls.append(1)
        return {"ok": True, "code": "must_not_run"}

    stale = execute(stale_id, stale_key, stale_effect)
    assert stale["status"] == "uncertain"
    assert stale["result_code"] == "external_execution_stale"
    assert execute(stale_id, stale_key, stale_effect) == stale
    assert stale_effect_calls == []

    with pytest.raises(service.ActionIntentError) as conflict:
        execute(
            exception_id,
            str(uuid.uuid4()),
            raises_private,
            node_code="it",
        )
    assert conflict.value.code == "intent_consumed"
    assert conflict.value.intent_id == exception_id
    assert conflict.value.audit_id == raised["audit_id"]

    from models import AdminActionIntent, AdminAudit

    session = api.SessionLocal()
    try:
        expected = {
            completed_id: "completed",
            failed_id: "failed",
            timeout_id: "uncertain",
            malformed_id: "uncertain",
            exception_id: "uncertain",
            stale_id: "uncertain",
        }
        for persisted in session.query(AdminActionIntent).filter(
            AdminActionIntent.id.in_(expected)
        ):
            assert persisted.status == expected[persisted.id]
            audit = (
                session.query(AdminAudit).filter_by(id=persisted.admin_audit_id).one()
            )
            audit_meta = json.loads(audit.meta)
            assert audit_meta["outcome"] == persisted.status
            assert audit_meta["result_code"] == persisted.result_code
            assert audit_meta["result_hash"] == persisted.result_hash
        safe_text = " ".join(
            f"{row.result_summary_json} {row.external_error_hash}"
            for row in session.query(AdminActionIntent).filter(
                AdminActionIntent.id.in_(expected)
            )
        ).lower()
        safe_text += (
            " "
            + " ".join(
                str(row.meta or "")
                for row in session.query(AdminAudit).filter(
                    AdminAudit.id.in_(
                        session.query(AdminActionIntent.admin_audit_id).filter(
                            AdminActionIntent.id.in_(expected)
                        )
                    )
                )
            ).lower()
        )
        assert provider_reference.lower() not in safe_text
        assert malformed_secret.lower() not in safe_text
        assert exception_secret.lower() not in safe_text
    finally:
        session.close()


def test_client_and_ticket_mutation_routes_require_action_intent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    cases = (
        (
            "POST",
            "/api/admin/users/manual",
            {"display_name": "Ручной пользователь", "days": 30},
        ),
        ("POST", "/api/admin/users/1001/manual/extend", {"days": 30}),
        ("POST", "/api/admin/users/1001/manual-extend", {"days": 30}),
        ("POST", "/api/admin/users/1001/manual/block", {"blocked": True}),
        ("POST", "/api/admin/users/1001/manual/regenerate-token", {}),
        ("POST", "/api/admin/users/1001/migration-code", {}),
        ("POST", "/api/admin/users/1001/safe-delete", {"confirm": True}),
        ("POST", "/api/admin/users/1001/delete-test-user", {}),
        ("POST", "/api/admin/users/1001/keys/nl/toggle", {"enable": False}),
        ("POST", "/api/admin/users/1001/keys/nl/reset-traffic", {}),
        ("POST", "/api/admin/users/1001/keys/nl/resync-subid", {}),
        (
            "PUT",
            "/api/admin/users/1001/key-limits/nl",
            {"hard_cap_gb": 100, "apply_now": False},
        ),
        ("POST", "/api/admin/users/1001/loyalty/grant", {"tier_days": 30}),
        ("POST", "/api/admin/users/1001/presets/run", {"preset": "extend_1d"}),
        (
            "POST",
            "/api/admin/users/keys/bulk-action",
            {
                "action": "disable",
                "segment": "custom",
                "tg_ids": [1001],
                "dry_run": True,
            },
        ),
        ("POST", "/api/admin/users/1001/message", {"text": "Проверка"}),
        (
            "POST",
            "/api/admin/tickets/7/reply",
            {"body": "Проверили, доступ восстановлен."},
        ),
        ("POST", "/api/admin/tickets/7/status", {"status": "closed"}),
        ("POST", "/api/admin/keys/17/rotate", {"reason": "operator"}),
    )

    for method, path, body in cases:
        response = client.request(method, path, json=body, headers=_admin_headers())
        assert response.status_code == 428, f"{method} {path}: {response.text}"
        assert _detail_code(response) == "intent_required"


def test_operator_migration_code_is_one_time_and_not_persisted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, DevicePairingCode, User

    session = api.SessionLocal()
    try:
        session.add(
            User(
                tg_id=8123,
                username="legacy-owner",
                sub_type="PAID",
                is_active=True,
                expiry_at=datetime.now(timezone.utc).replace(tzinfo=None)
                + timedelta(days=30),
            )
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    prepared = _prepare(
        client,
        action="user.migration_code",
        target_type="user",
        target_id="8123",
        payload={},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["confirmation_challenge"] == "8123"
    intent_id = str(prepared.json()["intent_id"])
    idempotency_key = str(uuid.uuid4())
    headers = _execute_headers(
        intent_id,
        idempotency_key=idempotency_key,
        confirmation_hash=hashlib.sha256(b"8123").hexdigest(),
    )
    issued = client.post(
        "/api/admin/users/8123/migration-code",
        headers=headers,
        json={},
    )
    assert issued.status_code == 200, issued.text
    pairing_code = str(issued.json()["pairing_code"])
    assert len(pairing_code) == 9
    assert pairing_code[4] == "-"

    replay = client.post(
        "/api/admin/users/8123/migration-code",
        headers=headers,
        json={},
    )
    assert replay.status_code == 200, replay.text
    assert "pairing_code" not in replay.json()

    session = api.SessionLocal()
    try:
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert pairing_code not in str(intent.result_summary_json or "")
        assert session.query(DevicePairingCode).count() == 1
        user = session.query(User).filter_by(tg_id=8123).one()
        assert str(user.account_id or "")
    finally:
        session.close()


def test_provider_quota_mutations_require_intent_freeze_version_and_keep_alerts_l1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    client = TestClient(api.app)
    private_note = "SYNTHETIC-PRIVATE-PROVIDER-NOTE"
    create_payload = {
        "node_code": "de",
        "included_gb": 80,
        "reset_day": 1,
        "timezone": "UTC",
        "warning_ratio": 0.8,
        "critical_ratio": 0.95,
        "enabled": True,
        "notes": private_note,
    }
    for method, path, body in (
        ("POST", "/api/admin/provider-quotas", create_payload),
        ("PATCH", "/api/admin/provider-quotas/nl", {"included_gb": 120}),
        ("DELETE", "/api/admin/provider-quotas/nl", {}),
    ):
        unguarded = client.request(method, path, headers=_admin_headers(), json=body)
        assert unguarded.status_code == 428, unguarded.text
        assert _detail_code(unguarded) == "intent_required"

    from models import (
        AdminActionIntent,
        AdminAudit,
        NodeHealthSample,
        OpsAlert,
        ProviderTrafficQuota,
        ProviderTrafficQuotaAudit,
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add(
            ProviderTrafficQuota(
                node_code="nl",
                included_bytes=100 * (1024**3),
                reset_day=1,
                timezone="UTC",
                warning_ratio=0.8,
                critical_ratio=0.95,
                enabled=True,
                notes=None,
                updated_by=9999,
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=1),
            )
        )
        session.add_all(
            [
                NodeHealthSample(
                    node_code="nl",
                    sampled_at=now - timedelta(days=1),
                    total_traffic_bytes=10 * (1024**3),
                ),
                NodeHealthSample(
                    node_code="nl",
                    sampled_at=now - timedelta(hours=1),
                    total_traffic_bytes=40 * (1024**3),
                ),
            ]
        )
        session.add(
            OpsAlert(
                fingerprint="provider_quota:nl:test",
                source="provider_quota",
                severity="warning",
                status="active",
                title="Лимит NL",
                body="Без сырых данных провайдера",
                node_code="nl",
                first_seen_at=now - timedelta(hours=2),
                last_seen_at=now,
                created_at=now - timedelta(hours=2),
                updated_at=now,
            )
        )
        session.commit()
        alert_id = int(
            session.query(OpsAlert)
            .filter_by(fingerprint="provider_quota:nl:test")
            .one()
            .id
        )
    finally:
        session.close()

    create_existing = _prepare(
        client,
        action="provider_quota.create",
        target_type="provider_quota",
        target_id="nl",
        payload={**create_payload, "node_code": "nl"},
    )
    assert create_existing.status_code == 409, create_existing.text
    assert _detail_code(create_existing) == "target_exists"

    create_prepared = _prepare(
        client,
        action="provider_quota.create",
        target_type="provider_quota",
        target_id="de",
        payload=create_payload,
    )
    assert create_prepared.status_code == 200, create_prepared.text
    assert create_prepared.json()["risk_level"] == "L2"
    assert create_prepared.json()["confirmation_challenge"] == "ПОДТВЕРДИТЬ"
    assert private_note not in create_prepared.text
    create_headers = _execute_headers(
        str(create_prepared.json()["intent_id"]),
        confirmation_hash=hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest(),
    )
    mismatched_create = client.post(
        "/api/admin/provider-quotas",
        headers=create_headers,
        json={**create_payload, "included_gb": 81},
    )
    assert mismatched_create.status_code == 409, mismatched_create.text
    assert _detail_code(mismatched_create) == "intent_mismatch"

    created = client.post(
        "/api/admin/provider-quotas",
        headers=_execute_headers(
            str(create_prepared.json()["intent_id"]),
            confirmation_hash=hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest(),
        ),
        json=create_payload,
    )
    assert created.status_code == 200, created.text
    assert created.json()["quota"]["included_gb"] == 80.0
    assert created.json()["quota"]["notes_present"] is True
    assert created.json()["quota"]["notes_length"] == len(private_note)
    assert "notes" not in created.json()["quota"]
    assert private_note not in created.text

    create_again = _prepare(
        client,
        action="provider_quota.create",
        target_type="provider_quota",
        target_id="de",
        payload=create_payload,
    )
    assert create_again.status_code == 409, create_again.text
    assert _detail_code(create_again) == "target_exists"

    update_payload = {
        "included_gb": 120,
        "reset_day": 1,
        "timezone": "UTC",
        "warning_ratio": 0.82,
        "critical_ratio": 0.96,
        "enabled": True,
        "notes": private_note,
    }
    prepared = _prepare(
        client,
        action="provider_quota.update",
        target_type="provider_quota",
        target_id="nl",
        payload=update_payload,
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()["preview"]
    assert preview["before"]["included_gb"] == 100.0
    assert preview["after"]["included_gb"] == 120.0
    assert "projected_exhaustion_at" in preview["after"]
    assert private_note not in prepared.text

    session = api.SessionLocal()
    try:
        quota = session.query(ProviderTrafficQuota).filter_by(node_code="nl").one()
        quota.included_bytes = 110 * (1024**3)
        quota.updated_at = now + timedelta(seconds=1)
        session.commit()
    finally:
        session.close()

    confirmation_hash = hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest()
    stale = client.patch(
        "/api/admin/provider-quotas/nl",
        headers=_execute_headers(
            str(prepared.json()["intent_id"]), confirmation_hash=confirmation_hash
        ),
        json=update_payload,
    )
    assert stale.status_code == 409, stale.text
    assert _detail_code(stale) == "stale_intent"

    fresh = _prepare(
        client,
        action="provider_quota.update",
        target_type="provider_quota",
        target_id="nl",
        payload=update_payload,
    )
    completed = client.patch(
        "/api/admin/provider-quotas/nl",
        headers=_execute_headers(
            str(fresh.json()["intent_id"]), confirmation_hash=confirmation_hash
        ),
        json=update_payload,
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["quota"]["included_gb"] == 120.0
    assert completed.json()["quota"]["notes_present"] is True
    assert "notes" not in completed.json()["quota"]
    assert private_note not in completed.text

    delete_preview = _prepare(
        client,
        action="provider_quota.delete",
        target_type="provider_quota",
        target_id="nl",
        payload={},
    )
    assert delete_preview.status_code == 200, delete_preview.text
    assert delete_preview.json()["risk_level"] == "L3"
    assert delete_preview.json()["confirmation_challenge"] == "NL"
    assert delete_preview.json()["preview"]["before"]["node_status"] == "active"

    wrong_delete = client.request(
        "DELETE",
        "/api/admin/provider-quotas/nl",
        headers=_execute_headers(
            str(delete_preview.json()["intent_id"]),
            confirmation_hash=hashlib.sha256(b"DE").hexdigest(),
        ),
        json={},
    )
    assert wrong_delete.status_code == 409, wrong_delete.text
    assert _detail_code(wrong_delete) == "confirmation_mismatch"

    delete_fresh = _prepare(
        client,
        action="provider_quota.delete",
        target_type="provider_quota",
        target_id="nl",
        payload={},
    )
    assert delete_fresh.status_code == 200, delete_fresh.text
    deleted = client.request(
        "DELETE",
        "/api/admin/provider-quotas/nl",
        headers=_execute_headers(
            str(delete_fresh.json()["intent_id"]),
            confirmation_hash=hashlib.sha256(b"NL").hexdigest(),
        ),
        json={},
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["deleted"] is True

    acknowledged = client.post(
        f"/api/admin/alerts/{alert_id}/ack", headers=_admin_headers()
    )
    silenced = client.post(
        f"/api/admin/alerts/{alert_id}/silence",
        headers=_admin_headers(),
        json={"minutes": 60},
    )
    assert acknowledged.status_code == 200, acknowledged.text
    assert silenced.status_code == 200, silenced.text

    session = api.SessionLocal()
    try:
        assert (
            session.query(ProviderTrafficQuota).filter_by(node_code="nl").count() == 0
        )
        quota = session.query(ProviderTrafficQuota).filter_by(node_code="de").one()
        assert quota.included_bytes == 80 * (1024**3)
        assert quota.notes == private_note
        provider_audits = (
            session.query(ProviderTrafficQuotaAudit)
            .order_by(ProviderTrafficQuotaAudit.id.asc())
            .all()
        )
        assert [(row.node_code, row.action) for row in provider_audits] == [
            ("de", "create"),
            ("nl", "update"),
            ("nl", "delete"),
        ]
        for audit in provider_audits:
            persisted = f"{audit.before_json or ''} {audit.after_json or ''}"
            assert private_note not in persisted
            for raw_snapshot in (audit.before_json, audit.after_json):
                if raw_snapshot is None:
                    continue
                snapshot = json.loads(raw_snapshot)
                assert "notes" not in snapshot
                assert set(snapshot) >= {
                    "notes_present",
                    "notes_length",
                    "notes_sha256",
                }
                assert len(snapshot["notes_sha256"]) == 64
        guarded_admin_audits = (
            session.query(AdminAudit)
            .filter(
                AdminAudit.action.in_(
                    [
                        "admin_provider_quota_create",
                        "admin_provider_quota_update",
                        "admin_provider_quota_delete",
                    ]
                )
            )
            .all()
        )
        guarded_admin_actions = sorted(row.action for row in guarded_admin_audits)
        assert guarded_admin_actions == [
            "admin_provider_quota_create",
            "admin_provider_quota_delete",
            "admin_provider_quota_update",
        ]
        assert all(
            private_note not in str(row.meta or "") for row in guarded_admin_audits
        )
        assert (
            session.query(AdminAudit).filter_by(action="admin_ops_alert_ack").count()
            == 1
        )
        assert (
            session.query(AdminAudit)
            .filter_by(action="admin_ops_alert_silence")
            .count()
            == 1
        )
        intent = (
            session.query(AdminActionIntent)
            .filter_by(id=fresh.json()["intent_id"])
            .one()
        )
        assert private_note not in intent.canonical_payload_json
        assert json.loads(intent.canonical_payload_json)["included_bytes"] == 120 * (
            1024**3
        )
        create_intent = (
            session.query(AdminActionIntent)
            .filter_by(id=create_prepared.json()["intent_id"])
            .one()
        )
        assert private_note not in create_intent.canonical_payload_json
    finally:
        session.close()


def test_provider_quota_admin_audit_failure_rolls_back_whole_guarded_transaction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    _seed_nodes(api)
    from models import (
        AdminActionIntent,
        AdminAudit,
        ProviderTrafficQuota,
        ProviderTrafficQuotaAudit,
    )

    client = TestClient(api.app)
    payload = {
        "node_code": "de",
        "included_gb": 80,
        "reset_day": 1,
        "timezone": "UTC",
        "warning_ratio": 0.8,
        "critical_ratio": 0.95,
        "enabled": True,
        "notes": "SAFE-OPERATOR-NOTE",
    }
    prepared = _prepare(
        client,
        action="provider_quota.create",
        target_type="provider_quota",
        target_id="de",
        payload=payload,
    )
    assert prepared.status_code == 200, prepared.text
    intent_id = str(prepared.json()["intent_id"])
    confirmation_hash = hashlib.sha256("ПОДТВЕРДИТЬ".encode("utf-8")).hexdigest()
    original_add_admin_audit = api._add_admin_audit

    def fail_admin_audit(**_kwargs):
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr(api, "_add_admin_audit", fail_admin_audit)
    failed = client.post(
        "/api/admin/provider-quotas",
        headers=_execute_headers(intent_id, confirmation_hash=confirmation_hash),
        json=payload,
    )
    assert failed.status_code == 503, failed.text
    assert _detail_code(failed) == "audit_failed"

    session = api.SessionLocal()
    try:
        assert session.query(ProviderTrafficQuota).count() == 0
        assert session.query(ProviderTrafficQuotaAudit).count() == 0
        assert session.query(AdminAudit).count() == 0
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert intent.status == "prepared"
        assert intent.consumed_at is None
    finally:
        session.close()

    monkeypatch.setattr(api, "_add_admin_audit", original_add_admin_audit)
    completed = client.post(
        "/api/admin/provider-quotas",
        headers=_execute_headers(intent_id, confirmation_hash=confirmation_hash),
        json=payload,
    )
    assert completed.status_code == 200, completed.text

    session = api.SessionLocal()
    try:
        assert (
            session.query(ProviderTrafficQuota).filter_by(node_code="de").count() == 1
        )
        assert (
            session.query(ProviderTrafficQuotaAudit)
            .filter_by(node_code="de", action="create")
            .count()
            == 1
        )
        assert (
            session.query(AdminAudit)
            .filter_by(action="admin_provider_quota_create")
            .count()
            == 1
        )
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        assert intent.status == "completed"
        assert intent.admin_audit_id is not None
    finally:
        session.close()


def test_private_message_and_bulk_selection_persist_only_hashes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, AdminAudit, User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add_all(
            [
                User(
                    tg_id=tg_id,
                    uuid=f"00000000-0000-4000-8000-{tg_id:012d}",
                    email=f"task14-{tg_id}@example.test",
                    sub_type="PAID",
                    current_plan_code="1_month",
                    created_at=now,
                    expiry_at=now + timedelta(days=30),
                    is_active=True,
                    sub_token=f"task14-token-{tg_id}",
                )
                for tg_id in (1001, 1002)
            ]
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    private_message = "SYNTHETIC-PRIVATE-TASK14-MESSAGE"
    prepared = _prepare(
        client,
        action="user.message",
        target_type="user",
        target_id="1001",
        payload={"text": private_message},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["confirmation_challenge"] == "ОТПРАВИТЬ"

    attempts: list[tuple[int, str]] = []

    async def uncertain_send(chat_id: int, text: str) -> bool:
        attempts.append((chat_id, text))
        raise RuntimeError(f"private provider failure: {private_message}")

    monkeypatch.setattr(api, "_telegram_send_message", uncertain_send)
    intent_id = str(prepared.json()["intent_id"])
    idempotency_key = str(uuid.uuid4())
    headers = _execute_headers(
        intent_id,
        idempotency_key=idempotency_key,
        confirmation_hash=hashlib.sha256("ОТПРАВИТЬ".encode("utf-8")).hexdigest(),
    )
    mismatch = client.post(
        "/api/admin/users/1001/message",
        headers=headers,
        json={"text": f"{private_message}-changed"},
    )
    assert mismatch.status_code == 409
    assert _detail_code(mismatch) == "intent_mismatch"
    assert attempts == []

    uncertain = client.post(
        "/api/admin/users/1001/message",
        headers=headers,
        json={"text": private_message},
    )
    assert uncertain.status_code == 200, uncertain.text
    assert uncertain.json()["status"] == "uncertain"
    assert uncertain.json()["result_code"] == "external_exception"
    replay = client.post(
        "/api/admin/users/1001/message",
        headers=headers,
        json={"text": private_message},
    )
    assert replay.json() == uncertain.json()
    assert attempts == [(1001, private_message)]

    bulk_payload = {
        "action": "disable",
        "segment": "all_active",
        "tg_ids": [1001, 1002],
        "q": "",
        "limit": 100,
        "dry_run": True,
        "force": False,
        "node_codes": [],
    }
    bulk = _prepare(
        client,
        action="user.bulk_key_action",
        target_type="users",
        target_id="bulk",
        payload=bulk_payload,
    )
    assert bulk.status_code == 200, bulk.text
    assert bulk.json()["confirmation_challenge"] == "1002"
    assert bulk.json()["preview"]["before"]["selected_count"] == 2

    session = api.SessionLocal()
    try:
        session.add(
            User(
                tg_id=1003,
                uuid="00000000-0000-4000-8000-000000001003",
                email="task14-1003@example.test",
                sub_type="PAID",
                current_plan_code="1_month",
                created_at=now,
                expiry_at=now + timedelta(days=30),
                is_active=True,
                sub_token="task14-token-1003",
            )
        )
        session.commit()
    finally:
        session.close()

    db_calls: list[int] = []
    original_db_executor = api._execute_admin_client_action_db

    def tracked_db_executor(*args, **kwargs):
        db_calls.append(1)
        return original_db_executor(*args, **kwargs)

    monkeypatch.setattr(api, "_execute_admin_client_action_db", tracked_db_executor)
    stale_bulk = client.post(
        "/api/admin/users/keys/bulk-action",
        headers=_execute_headers(
            str(bulk.json()["intent_id"]),
            confirmation_hash=hashlib.sha256(b"1002").hexdigest(),
        ),
        json=bulk_payload,
    )
    assert stale_bulk.status_code == 409
    assert _detail_code(stale_bulk) == "stale_intent"
    assert db_calls == []

    session = api.SessionLocal()
    try:
        message_intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        audit = (
            session.query(AdminAudit).filter_by(id=message_intent.admin_audit_id).one()
        )
        persisted_message = " ".join(
            (
                message_intent.canonical_payload_json,
                message_intent.preview_snapshot_json,
                str(message_intent.result_summary_json or ""),
                str(audit.meta or ""),
            )
        )
        assert private_message not in persisted_message
        canonical_message = json.loads(message_intent.canonical_payload_json)
        assert canonical_message["text"]["length"] == len(private_message)
        assert len(canonical_message["text"]["sha256"]) == 64

        bulk_intent = (
            session.query(AdminActionIntent)
            .filter_by(id=bulk.json()["intent_id"])
            .one()
        )
        canonical_bulk = json.loads(bulk_intent.canonical_payload_json)
        assert "tg_ids" not in canonical_bulk
        assert canonical_bulk["tg_ids_count"] == 2
        assert len(canonical_bulk["tg_ids_hash"]) == 64
        persisted_preview = json.loads(bulk_intent.preview_snapshot_json)
        assert set(persisted_preview["before"]) == {"selected_count", "selection_hash"}
        assert persisted_preview["before"]["selected_count"] == 2
        assert set(persisted_preview["after"]) == {"action_title", "dry_run"}
    finally:
        session.close()


def test_broadcast_executes_only_frozen_recipients_and_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, AdminAudit, AdminBroadcastRecipientPlan, User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add_all(
            [
                User(
                    tg_id=tg_id,
                    uuid=f"00000000-0000-4000-8000-{tg_id:012d}",
                    email=f"broadcast-{tg_id}@example.test",
                    sub_type="PAID",
                    created_at=now,
                    expiry_at=now + timedelta(days=30),
                    is_active=is_active,
                    sub_token=f"broadcast-token-{tg_id}",
                )
                for tg_id, is_active in ((7101, True), (7102, True), (7103, False))
            ]
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    text = "Плановые работы"
    payload = {"segment": "all_active", "limit": 100, "tg_ids": [], "text": text}
    prepared = _prepare(
        client,
        action="broadcast.send",
        target_type="broadcast",
        target_id="broadcast",
        payload=payload,
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()
    assert preview["risk_level"] == "L3"
    assert preview["confirmation_challenge"] == "ОТПРАВИТЬ"
    assert preview["preview"]["before"]["recipient_count"] == 2
    assert len(preview["preview"]["before"]["recipient_hash"]) == 64
    assert (
        preview["preview"]["after"]["message_sha256"]
        == hashlib.sha256(text.encode("utf-8")).hexdigest()
    )
    intent_id = str(preview["intent_id"])

    session = api.SessionLocal()
    try:
        session.query(User).filter_by(tg_id=7103).one().is_active = True
        session.commit()
    finally:
        session.close()

    deliveries: list[tuple[int, str, bool | None]] = []

    async def send(
        chat_id: int,
        message: str,
        *,
        disable_web_page_preview: bool | None = None,
    ):
        from telegram_delivery_service import TelegramDeliveryResult

        deliveries.append((chat_id, message, disable_web_page_preview))
        return TelegramDeliveryResult(
            sent=True,
            reason_code="sent",
            retryable=False,
            duration_ms=12,
            http_status=200,
            message_id=chat_id,
        )

    monkeypatch.setattr(api, "_telegram_send_message_detailed", send)
    idempotency_key = str(uuid.uuid4())
    headers = _execute_headers(
        intent_id,
        idempotency_key=idempotency_key,
        confirmation_hash=hashlib.sha256("ОТПРАВИТЬ".encode("utf-8")).hexdigest(),
    )
    changed = client.post(
        "/api/admin/broadcast",
        headers=headers,
        json={**payload, "text": "Другой текст", "dry_run": False},
    )
    assert changed.status_code == 409
    assert _detail_code(changed) == "payload_mismatch"
    assert deliveries == []

    sent = client.post(
        "/api/admin/broadcast",
        headers=headers,
        json={**payload, "dry_run": False},
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "completed"
    assert sent.json()["attempted"] == 2
    assert sent.json()["sent"] == 2
    assert sent.json()["failed"] == 0
    assert deliveries == [(7101, text, True), (7102, text, True)]

    replay = client.post(
        "/api/admin/broadcast",
        headers=headers,
        json={**payload, "dry_run": False},
    )
    assert replay.json() == sent.json()
    assert deliveries == [(7101, text, True), (7102, text, True)]

    session = api.SessionLocal()
    try:
        intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
        canonical = json.loads(intent.canonical_payload_json)
        assert set(canonical) == {
            "segment",
            "limit",
            "requested_tg_ids_hash",
            "message_sha256",
            "message_length",
        }
        assert (
            canonical["message_sha256"]
            == hashlib.sha256(text.encode("utf-8")).hexdigest()
        )
        assert canonical["message_length"] == len(text)
        assert (
            session.query(AdminBroadcastRecipientPlan)
            .filter_by(intent_id=intent_id)
            .count()
            == 2
        )
        audit = session.query(AdminAudit).filter_by(id=intent.admin_audit_id).one()
        persisted_public = " ".join(
            (
                intent.canonical_payload_json,
                intent.preview_snapshot_json,
                str(intent.result_summary_json or ""),
                str(audit.meta or ""),
            )
        )
        assert text not in persisted_public
        assert all(str(tg_id) not in persisted_public for tg_id in (7101, 7102, 7103))
        audit_meta = json.loads(audit.meta or "{}")
        assert audit_meta["recipient_count"] == 2
        assert len(audit_meta["recipient_hash"]) == 64
    finally:
        session.close()


def test_warp_material_intent_persists_fingerprints_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add(
            User(
                tg_id=7301,
                uuid="00000000-0000-4000-8000-000000007301",
                email="warp-guard@example.test",
                sub_type="PAID",
                created_at=now,
                expiry_at=now + timedelta(days=30),
                is_active=True,
                sub_token="warp-guard-token",
                app_install_id="install-warp-7301",
            )
        )
        session.commit()
    finally:
        session.close()

    private_key = "SYNTHETIC-WARP-PRIVATE-MATERIAL"
    account_token = "SYNTHETIC-WARP-ACCOUNT-TOKEN"
    payload = {
        "tg_id": 7301,
        "install_id": "install-warp-7301",
        "source": "operator_provisioned",
        "mode": "proxy_over_warp",
        "wireguard_config": {"private_key": private_key, "address": "172.16.0.2/32"},
        "account": {"token": account_token},
    }
    client = TestClient(api.app)
    prepared = _prepare(
        client,
        action="warp_material.replace",
        target_type="warp_material",
        target_id="7301",
        payload=payload,
    )

    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["risk_level"] == "L3"
    assert prepared.json()["confirmation_challenge"] == "7301"
    session = api.SessionLocal()
    try:
        intent = (
            session.query(AdminActionIntent)
            .filter_by(id=prepared.json()["intent_id"])
            .one()
        )
        persisted = " ".join(
            (intent.canonical_payload_json, intent.preview_snapshot_json)
        )
        assert private_key not in persisted
        assert account_token not in persisted
        assert "install-warp-7301" not in persisted
        canonical = json.loads(intent.canonical_payload_json)
        assert len(canonical["wireguard_config"]["sha256"]) == 64
        assert len(canonical["account"]["sha256"]) == 64
    finally:
        session.close()

    headers = _execute_headers(
        str(prepared.json()["intent_id"]),
        idempotency_key=str(uuid.uuid4()),
        confirmation_hash=hashlib.sha256("7301".encode("utf-8")).hexdigest(),
    )
    executed = client.put(
        "/api/admin/client/warp/material",
        headers=headers,
        json=payload,
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["material"]["install_id"] == "install-warp-7301"

    session = api.SessionLocal()
    try:
        intent = (
            session.query(AdminActionIntent)
            .filter_by(id=prepared.json()["intent_id"])
            .one()
        )
        durable = str(intent.result_summary_json or "")
        assert "install-warp-7301" not in durable
        assert private_key not in durable
        assert account_token not in durable
        persisted_result = json.loads(durable)
        assert len(persisted_result["material"]["install_id_sha256"]) == 64
    finally:
        session.close()


def test_issued_codes_survive_lost_response_without_entering_intent_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminActionIntent, GiftCard

    client = TestClient(api.app)
    plan_code = str(api._default_plan_catalog()[0]["code"])
    cases = (
        (
            "access_key.issue",
            "access_key_batch",
            plan_code,
            "/api/admin/access-keys/issue",
            {"plan_code": plan_code, "quantity": 2},
            "issued",
            "key",
        ),
        (
            "gift_code.create",
            "gift_code",
            "mini",
            "/api/admin/gift-codes",
            {"card_type": "mini"},
            "gift_code",
            "code",
        ),
    )

    for action, target_type, target_id, path, payload, result_key, code_key in cases:
        prepared = _prepare(
            client,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload,
        )
        assert prepared.status_code == 200, prepared.text
        intent_id = str(prepared.json()["intent_id"])
        headers = _execute_headers(
            intent_id,
            idempotency_key=str(uuid.uuid4()),
            confirmation_hash=hashlib.sha256(target_id.encode("utf-8")).hexdigest(),
        )

        first = client.post(path, headers=headers, json=payload)
        assert first.status_code == 200, first.text
        replay = client.post(path, headers=headers, json=payload)
        assert replay.status_code == 200, replay.text
        assert replay.json() == first.json()

        raw_result = first.json()[result_key]
        codes = (
            [str(item[code_key]) for item in raw_result]
            if isinstance(raw_result, list)
            else [str(raw_result[code_key])]
        )
        assert all(codes)

        status = client.get(
            f"/api/admin/action-intents/{intent_id}",
            headers=_admin_headers(),
        )
        assert status.status_code == 200, status.text
        status_text = status.text
        assert all(code not in status_text for code in codes)
        assert "_issued_card_ids" not in status_text

        session = api.SessionLocal()
        try:
            intent = session.query(AdminActionIntent).filter_by(id=intent_id).one()
            durable = str(intent.result_summary_json or "")
            assert all(code not in durable for code in codes)
            assert "issued_fingerprints" in durable
            assert session.query(GiftCard).filter(
                GiftCard.code.in_(codes), GiftCard.created_by == 9999
            ).count() == len(codes)
        finally:
            session.close()


def test_broadcast_timeout_is_uncertain_and_same_idempotency_does_not_resend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add(
            User(
                tg_id=7201,
                uuid="00000000-0000-4000-8000-000000007201",
                email="broadcast-timeout@example.test",
                sub_type="PAID",
                created_at=now,
                expiry_at=now + timedelta(days=30),
                is_active=True,
                sub_token="broadcast-timeout-token",
            )
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    text = "Сетевая проверка"
    payload = {"segment": "custom", "limit": 10, "tg_ids": [7201], "text": text}
    prepared = _prepare(
        client,
        action="broadcast.send",
        target_type="broadcast",
        target_id="broadcast",
        payload=payload,
    )
    assert prepared.status_code == 200, prepared.text
    intent_id = str(prepared.json()["intent_id"])
    attempts = 0

    async def timeout_send(
        _chat_id: int,
        _message: str,
        *,
        disable_web_page_preview: bool | None = None,
    ):
        assert disable_web_page_preview is True
        nonlocal attempts
        attempts += 1
        raise TimeoutError("synthetic network timeout")

    monkeypatch.setattr(api, "_telegram_send_message_detailed", timeout_send)
    key = str(uuid.uuid4())
    headers = _execute_headers(
        intent_id,
        idempotency_key=key,
        confirmation_hash=hashlib.sha256("ОТПРАВИТЬ".encode("utf-8")).hexdigest(),
    )
    uncertain = client.post(
        "/api/admin/broadcast",
        headers=headers,
        json={**payload, "dry_run": False},
    )
    assert uncertain.status_code == 200, uncertain.text
    assert uncertain.json()["status"] == "uncertain"
    assert uncertain.json()["result_code"] == "external_timeout"

    replay = client.post(
        "/api/admin/broadcast",
        headers=headers,
        json={**payload, "dry_run": False},
    )
    assert replay.json() == uncertain.json()
    assert attempts == 1

    status = client.get(
        f"/api/admin/action-intents/{intent_id}",
        headers=_admin_headers(),
    )
    assert status.status_code == 200, status.text
    assert status.json() == uncertain.json()


def test_broadcast_retry_freezes_only_retryable_failures_and_never_resends_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    from models import AdminBroadcastDeliveryAttempt, User
    from telegram_delivery_service import TelegramDeliveryResult

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = api.SessionLocal()
    try:
        session.add_all(
            [
                User(
                    tg_id=tg_id,
                    uuid=f"00000000-0000-4000-8000-{tg_id:012d}",
                    email=f"broadcast-retry-{tg_id}@example.test",
                    sub_type="PAID",
                    created_at=now,
                    expiry_at=now + timedelta(days=30),
                    is_active=True,
                    sub_token=f"broadcast-retry-token-{tg_id}",
                )
                for tg_id in (7301, 7302)
            ]
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(api.app)
    text = "Проверка доставки"
    payload = {"segment": "custom", "limit": 10, "tg_ids": [7301, 7302], "text": text}
    prepared = _prepare(
        client,
        action="broadcast.send",
        target_type="broadcast",
        target_id="broadcast",
        payload=payload,
    )
    root_intent_id = str(prepared.json()["intent_id"])
    calls: list[int] = []

    async def first_delivery(chat_id: int, _message: str, **_kwargs):
        calls.append(chat_id)
        if chat_id == 7301:
            return TelegramDeliveryResult(
                sent=True,
                reason_code="sent",
                retryable=False,
                duration_ms=10,
                http_status=200,
                message_id=101,
            )
        return TelegramDeliveryResult(
            sent=False,
            reason_code="rate_limited",
            retryable=True,
            duration_ms=20,
            http_status=429,
            telegram_error_code=429,
        )

    monkeypatch.setattr(api, "_telegram_send_message_detailed", first_delivery)
    first = client.post(
        "/api/admin/broadcast",
        headers=_execute_headers(
            root_intent_id,
            idempotency_key=str(uuid.uuid4()),
            confirmation_hash=hashlib.sha256("ОТПРАВИТЬ".encode("utf-8")).hexdigest(),
        ),
        json={**payload, "dry_run": False},
    )
    assert first.status_code == 200, first.text
    assert first.json()["sent"] == 1
    assert first.json()["failed"] == 1
    assert first.json()["retryable_failed"] == 1
    assert first.json()["reason_counts"] == {"rate_limited": 1}

    retry_payload = {
        "segment": "retry_failed",
        "limit": 1000,
        "tg_ids": [],
        "retry_intent_id": root_intent_id,
        "text": text,
    }
    retry_prepared = _prepare(
        client,
        action="broadcast.send",
        target_type="broadcast",
        target_id="broadcast",
        payload=retry_payload,
    )
    assert retry_prepared.status_code == 200, retry_prepared.text
    assert retry_prepared.json()["preview"]["before"]["recipient_count"] == 1
    retry_intent_id = str(retry_prepared.json()["intent_id"])

    async def retry_delivery(chat_id: int, _message: str, **_kwargs):
        calls.append(chat_id)
        return TelegramDeliveryResult(
            sent=True,
            reason_code="sent",
            retryable=False,
            duration_ms=15,
            http_status=200,
            message_id=102,
        )

    monkeypatch.setattr(api, "_telegram_send_message_detailed", retry_delivery)
    retried = client.post(
        "/api/admin/broadcast",
        headers=_execute_headers(
            retry_intent_id,
            idempotency_key=str(uuid.uuid4()),
            confirmation_hash=hashlib.sha256("ОТПРАВИТЬ".encode("utf-8")).hexdigest(),
        ),
        json={**retry_payload, "dry_run": False},
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["sent"] == 1
    assert retried.json()["failed"] == 0
    assert calls == [7301, 7302, 7302]

    retry_again = _prepare(
        client,
        action="broadcast.send",
        target_type="broadcast",
        target_id="broadcast",
        payload=retry_payload,
    )
    assert retry_again.status_code == 409
    assert _detail_code(retry_again) == "empty_selection"

    session = api.SessionLocal()
    try:
        attempts = (
            session.query(AdminBroadcastDeliveryAttempt)
            .order_by(
                AdminBroadcastDeliveryAttempt.tg_id,
                AdminBroadcastDeliveryAttempt.attempt_number,
            )
            .all()
        )
        assert [(row.tg_id, row.attempt_number, row.status) for row in attempts] == [
            (7301, 1, "sent"),
            (7302, 1, "failed"),
            (7302, 2, "sent"),
        ]
        assert {row.campaign_intent_id for row in attempts} == {root_intent_id}
    finally:
        session.close()
