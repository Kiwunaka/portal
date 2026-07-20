from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "client-ui-api-additions.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "client-ui-api-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PAY_CHECKOUT_URL", "https://pay.pokrov.space/checkout/")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999")
    monkeypatch.setenv("SUPPORT_AI_ENABLED", "0")

    for name in [
        "api",
        "app_first_service",
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
        "shared_surface_facts",
        "transport_catalog",
        "node_policy",
        "support_ai_service",
        "support_agent_context",
        "support_agent_grounding",
        "support_agent_harness",
        "support_agent_knowledge",
        "support_agent_policy",
        "support_agent_provider",
        "support_agent_safety",
        "support_agent_service",
        "support_agent_sessions",
        "support_agent_state",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")

    class _FakePanel:
        async def login(self):
            return True

        async def close(self):
            return None

        async def add_client(self, **kwargs):
            return True

        async def get_node_online_summaries(self, *, node_codes=None):
            return {
                str(code): {"online_keys_now": 0, "online_connections_now": 0}
                for code in (node_codes or [])
            }

    api.ControlPanel = _FakePanel
    return api


def _rollout_payload() -> dict[str, object]:
    return {
        "version": "2026-06-22",
        "defaults": {
            "routing_mode_default": "all_except_ru",
            "transport_profile": "legacy_reality_fallback",
            "dns_policy": "ru_direct_split",
            "ip_version_preference": "ipv4_only",
        },
        "carrier_overrides": {},
        "cohort_overrides": {},
        "operator_lab": {"enabled": False},
        "package_catalog_feed": {"version": "2026-06-22"},
        "routing_rules_feed": {"version": "2026-06-22"},
        "support_recovery_order": ["app", "web", "telegram"],
    }


def _transport_profiles() -> str:
    return json.dumps(
        [
            {
                "name": "legacy_reality_fallback",
                "enabled": True,
                "kind": "reality",
                "inbound_id": 1,
                "host": "example.test",
                "port": 443,
                "tls_server_name": "www.example.test",
                "reality_public_key": "pbk",
                "reality_short_id": "sid",
                "fingerprint": "firefox",
                "flow": "xtls-rprx-vision",
            }
        ]
    )


def _add_node(
    api,
    *,
    code: str,
    health_score: float = 95.0,
    cpu_percent: float = 30.0,
    panel_latency_ms: int | None = 40,
    is_healthy: bool = True,
    enabled: bool = True,
    last_health_at: datetime | None = None,
) -> None:
    from models import Node

    s = api.SessionLocal()
    try:
        node = Node(
            code=code,
            name=code.upper(),
            host=f"{code}.example.test",
            vless_port=443,
            reality_sni="www.example.test",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            panel_base_url=f"https://{code}.example.test:8444",
            panel_path="xui",
            panel_user="u",
            panel_pass="p",
            inbound_id=1,
            enabled=enabled,
            accepting_new_clients=True,
            is_draining=False,
            weight=100,
            health_score=health_score,
            is_healthy=is_healthy,
            cpu_percent=cpu_percent,
            panel_latency_ms=panel_latency_ms,
            last_health_at=last_health_at or _utcnow(),
            transport_profiles_json=_transport_profiles(),
        )
        s.add(node)
        s.commit()
    finally:
        s.close()


def _seed_rollout(api) -> None:
    s = api.SessionLocal()
    try:
        api._set_app_setting_json(s=s, key="network_rollout_config", value=_rollout_payload())
        s.commit()
    finally:
        s.close()


def _start_trial(client: TestClient, *, install_id: str, platform: str = "windows") -> dict[str, object]:
    response = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": install_id,
            "device_name": "Windows 11",
            "platform": platform,
            "os_version": "11",
            "app_version": "1.0.0-beta.2",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(start_body: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {start_body['session_token']}"}


def test_client_locations_catalog_exposes_searchable_real_node_catalog(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)

    now = _utcnow()
    _add_node(api, code="nl-ams-01", health_score=94.0, cpu_percent=31.0, panel_latency_ms=38, last_health_at=now)
    _add_node(api, code="de-fra-01", health_score=91.0, cpu_percent=42.0, panel_latency_ms=52, last_health_at=now)
    _add_node(api, code="nl-free", health_score=89.0, cpu_percent=58.0, panel_latency_ms=71, last_health_at=now)
    _add_node(api, code="old-node", health_score=98.0, cpu_percent=20.0, last_health_at=now - timedelta(hours=3))

    start_body = _start_trial(client, install_id="locations-catalog-device")
    response = client.get("/api/client/locations?platform=windows&q=ams", headers=_auth_headers(start_body))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["auto"]["enabled"] is True
    assert body["freePoolCode"] == "nl-free"
    assert body["query"] == "ams"
    assert body["search"]["matched"] >= 1
    assert body["countries"]

    all_cities = [
        city
        for country in body["countries"]
        for city in country["cities"]
    ]
    amsterdam = next(city for city in all_cities if city["code"] == "nl-ams-01")
    assert amsterdam["city"] == "Amsterdam"
    assert amsterdam["countryCode"] == "nl"
    assert amsterdam["premium"] is True
    assert amsterdam["healthScore"] == 0.94
    assert amsterdam["latencyMs"] == 38
    assert amsterdam["load"] == 0.31
    assert "old-node" not in {city["code"] for city in all_cities}


def test_client_account_devices_notifications_push_and_subscription_contract(monkeypatch, tmp_path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    start_body = _start_trial(client, install_id="account-p1-device")
    headers = _auth_headers(start_body)

    subscription = client.get("/api/client/subscription", headers=headers)
    assert subscription.status_code == 200, subscription.text
    sub_body = subscription.json()
    assert sub_body["lane"] == "trialPremium"
    assert sub_body["daysLeft"] == 5
    assert sub_body["autoRenew"] is False
    assert sub_body["renewUrl"].startswith("https://pay.pokrov.space/checkout/")
    assert sub_body["plans"]
    assert {"id", "title", "price"} <= set(sub_body["plans"][0])

    devices = client.get("/api/client/devices", headers=headers)
    assert devices.status_code == 200, devices.text
    device_body = devices.json()
    assert len(device_body["items"]) == 1
    assert device_body["items"][0]["id"] == "account-p1-device"
    assert device_body["items"][0]["current"] is True
    revoke_current = client.delete("/api/client/devices/account-p1-device", headers=headers)
    assert revoke_current.status_code == 409

    notifications = client.get("/api/client/notifications", headers=headers)
    assert notifications.status_code == 200, notifications.text
    inbox = notifications.json()
    assert "items" in inbox
    assert "unreadCount" in inbox
    assert inbox["nextCursor"] is None

    mark_read = client.post(
        "/api/client/notifications/read",
        headers=headers,
        json={"ids": ["access.trial"]},
    )
    assert mark_read.status_code == 200, mark_read.text
    assert mark_read.json()["ok"] is True

    push = client.post(
        "/api/client/push/register",
        headers=headers,
        json={"platform": "windows", "provider": "poll", "token": "local-test-token"},
    )
    assert push.status_code == 200, push.text
    push_body = push.json()
    assert push_body["ok"] is True
    assert push_body["provider"] == "poll"
    assert push_body["tokenHash"] == hashlib.sha256(b"local-test-token").hexdigest()


def test_client_support_assistant_and_ticket_presence_contract(monkeypatch, tmp_path, caplog) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    _seed_rollout(api)
    _add_node(api, code="nl-ams-01")

    from support_ai_service import SupportAIConfig
    from support_agent_grounding import SupportGroundingEngine
    from support_agent_harness import SupportAgentHarness
    from support_agent_knowledge import SupportKnowledgeStore
    from support_agent_policy import SupportAgentPolicyStore
    from support_agent_provider import ProviderUsage, SynthesisTurn
    from support_agent_service import SupportAgentService
    from support_agent_sessions import OwnerRateLimiter, SessionInFlightGuard, SupportSessionStore

    class _RepeatAdapter:
        def __init__(self) -> None:
            self.requests = []

        async def complete_synthesis(self, **request):
            self.requests.append(request)
            content = json.dumps(
                {
                    "schema_version": "1",
                    "status": "answer",
                    "reply": "Переподключитесь и повторите проверку доступа.",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            return SynthesisTurn(
                content=content,
                finish_reason="stop",
                usage=ProviderUsage(prompt_tokens=100, completion_tokens=20, cached_tokens=80),
                latency_ms=5,
            )

    class _RecordingHarness:
        def __init__(self, wrapped) -> None:
            self.wrapped = wrapped
            self.requests = []

        async def run(self, request):
            self.requests.append(request)
            return await self.wrapped.run(request)

    policy = SupportAgentPolicyStore().load(Path(api.__file__).resolve().parents[1] / "shared" / "support-agent-policy.json")
    knowledge_store = SupportKnowledgeStore()
    knowledge = knowledge_store.load(Path(api.__file__).resolve().parents[1] / "shared" / "support-ai-knowledge.json")
    adapter = _RepeatAdapter()
    recording_harness = _RecordingHarness(
        SupportAgentHarness(
            policy=policy,
            knowledge=knowledge,
            grounding_engine=SupportGroundingEngine(knowledge_store, knowledge),
            session_store=SupportSessionStore(),
            rate_limiter=OwnerRateLimiter(),
            in_flight_guard=SessionInFlightGuard(),
            adapter=adapter,
        )
    )
    api.SUPPORT_AGENT_SERVICE = SupportAgentService(
        config=SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://enterprise.xcody.dev/v1",
            model="minimax-m3",
            reasoning_effort="medium",
        ),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=lambda _config, _settings: recording_harness,
        time_source=lambda: 100.0,
    )

    start_body = _start_trial(client, install_id="support-p1-device")
    headers = _auth_headers(start_body)

    invalid_scope = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={"message": "Подключено, но интернета нет", "scope": "billing"},
    )
    assert invalid_scope.status_code == 422

    too_many_diagnostics = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {f"unknown_{index}": "value" for index in range(21)},
        },
    )
    assert too_many_diagnostics.status_code == 422
    assert recording_harness.requests == []

    oversized_diagnostics = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {"platform": "x" * 513},
        },
    )
    assert oversized_diagnostics.status_code == 422
    assert recording_harness.requests == []

    attacker_value = "vless://private-profile sk-private-token"

    assistant = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "safeDiagnostics": {
                "app_version": "1.0.0",
                "platform": "windows",
                "route_mode": "all_except_ru",
                "connection_status": "connected",
                "attacker_key": attacker_value,
            },
        },
    )
    assert assistant.status_code == 200, assistant.text
    assistant_body = assistant.json()
    assert assistant_body["reply"]
    assert assistant_body["suggestedActions"]
    assert assistant_body["shouldEscalate"] is False
    assert assistant_body["source"] == "support_agent"
    generated_session_id = assistant_body["assistantSessionId"]
    assert 16 <= len(generated_session_id) <= 64

    supplied = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistant_session_id": generated_session_id,
        },
    )
    assert supplied.status_code == 200, supplied.text
    assert supplied.json()["assistantSessionId"] == generated_session_id

    invalid_session = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": "../../invalid",
        },
    )
    assert invalid_session.status_code == 200, invalid_session.text
    assert invalid_session.json()["assistantSessionId"] != "../../invalid"

    for _index in range(3):
        response = client.post(
            "/api/client/support/assistant",
            headers=headers,
            json={
                "message": "Подключено, но интернета нет",
                "scope": "support",
                "assistantSessionId": generated_session_id,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["source"] == "support_agent"

    seventh = client.post(
        "/api/client/support/assistant",
        headers=headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert seventh.status_code == 200, seventh.text
    assert seventh.json()["source"] == "local_fallback"
    assert seventh.json()["shouldEscalate"] is True
    assert len(adapter.requests) == 6

    second_start = _start_trial(client, install_id="support-p2-device")
    second_headers = _auth_headers(second_start)
    cross_owner = client.post(
        "/api/client/support/assistant",
        headers=second_headers,
        json={
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert cross_owner.status_code == 200, cross_owner.text
    assert cross_owner.json()["source"] == "support_agent"
    assert recording_harness.requests[0].session_scope.client_session_id == generated_session_id
    assert recording_harness.requests[-1].session_scope.client_session_id == generated_session_id
    assert (
        recording_harness.requests[0].session_scope.internal_session_key
        != recording_harness.requests[-1].session_scope.internal_session_key
    )

    from models import Event

    event_session = api.SessionLocal()
    try:
        events = event_session.query(Event).filter(Event.event_name == "client_support_assistant").all()
        serialized_events = "\n".join(str(event.meta_json or "") for event in events)
    finally:
        event_session.close()
    assert '"diagnostics_keys":["app_version","connection_status","platform","route_mode"]' in serialized_events
    assert "attacker_key" not in serialized_events
    assert attacker_value not in serialized_events
    assert attacker_value not in caplog.text

    ticket = client.post(
        "/api/tickets",
        headers=headers,
        json={"subject": "Connection issue", "body": "ERR_CONNECTION_CLOSED"},
    )
    assert ticket.status_code == 200, ticket.text
    ticket_body = ticket.json()["ticket"]
    assert ticket_body["operatorPresence"] in {"online", "away", "offline"}
    assert ticket_body["operatorTyping"] is False
    assert isinstance(ticket_body["unreadForUser"], int)
    assert "slaHint" in ticket_body

    calls_before_denial = len(recording_harness.requests)
    denied_ticket = client.post(
        "/api/client/support/assistant",
        headers=second_headers,
        json={
            "ticketId": ticket_body["id"],
            "message": "Подключено, но интернета нет",
            "scope": "support",
            "assistantSessionId": generated_session_id,
        },
    )
    assert denied_ticket.status_code == 403
    assert len(recording_harness.requests) == calls_before_denial
