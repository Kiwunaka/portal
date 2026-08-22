from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from admin_action_intent_service import (  # noqa: E402
    ActionIntentError,
    execute_action_intent,
    prepare_action_intent,
)
from migrations import run_migrations  # noqa: E402
from models import (  # noqa: E402
    Account,
    Base,
    Event,
    ServiceIncident,
    SupportBundleUpload,
    SupportTicket,
    User,
)
from operator_work_service import add_admin_audit  # noqa: E402
from support_work_service import (  # noqa: E402
    attempt_explorer,
    list_support_tickets,
    search_support_cases,
    support_bundle_upload_id_for_ref,
    support_ticket_detail,
    user_360,
)
from tickets_repo import add_ticket_message, create_ticket, list_ticket_messages  # noqa: E402


@pytest.fixture()
def database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'support-work.db').as_posix()}")
    Base.metadata.create_all(engine)
    run_migrations(engine)
    factory = sessionmaker(bind=engine)
    try:
        yield factory
    finally:
        engine.dispose()


def _seed(factory):
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    session = factory()
    try:
        user = User(
            tg_id=1001,
            uuid=str(uuid.uuid4()),
            email="support@example.test",
            sub_type="paid",
            is_active=True,
            sub_token="synthetic-test-token",
            app_install_id="install-secret-value",
            app_platform="windows",
            app_version="1.2.0",
            app_last_seen_at=now,
        )
        session.add(user)
        ticket = create_ticket(session, user_tg_id=1001, subject="Не подключается")
        ticket.environment = "test"
        ticket.priority = "critical"
        ticket.queue = "connection"
        ticket.sla_due_at = now - timedelta(minutes=5)
        add_ticket_message(
            session,
            ticket_id=ticket.id,
            sender_tg_id=1001,
            sender_role="user",
            body="Публичное сообщение",
        )
        add_ticket_message(
            session,
            ticket_id=ticket.id,
            sender_tg_id=9999,
            sender_role="admin",
            body="Секретная внутренняя заметка",
            visibility="internal",
        )
        session.add(
            Event(
                tg_id=1001,
                event_name="runtime_start_failed",
                source="client",
                session_id="raw-session-secret",
                device_id="raw-device-secret",
                platform="windows",
                app_version="1.2.0",
                build_number="42",
                surface="client",
                subsystem="runtime",
                stage="core_start",
                result="failure",
                error_category="runtime",
                error_code="CORE-001",
                attempt_number=1,
                trace_id="raw-trace-secret",
                occurred_at=now,
                received_at=now,
                meta_json=json.dumps(
                    {
                        "token": "raw-token-must-never-leak",
                        "url": "https://private.example/path",
                        "ip": "203.0.113.10",
                    }
                ),
            )
        )
        session.commit()
        return int(ticket.id), int(ticket.version)
    finally:
        session.close()


def test_support_projection_is_server_ordered_versioned_and_hides_internal_notes(database) -> None:
    ticket_id, _version = _seed(database)
    session = database()
    try:
        rows = list_support_tickets(session, environment="test", status="active", limit=20)
        assert rows[0]["id"] == ticket_id
        assert rows[0]["priority"] == "critical"
        assert rows[0]["queue"] == "connection"
        assert rows[0]["sla_status"] == "breached"
        assert rows[0]["version"] >= 3

        public_messages = list_ticket_messages(session, ticket_id, limit=20)
        operator_messages = list_ticket_messages(
            session, ticket_id, limit=20, include_internal=True
        )
        assert [row.body for row in public_messages] == ["Публичное сообщение"]
        assert [row.visibility for row in operator_messages] == ["public", "internal"]

        detail = support_ticket_detail(
            session, environment="test", ticket_id=ticket_id
        )
        assert detail is not None
        assert detail["messages"][-1]["visibility"] == "internal"
        assert detail["evidence_policy"]["support_bundles"] == "ttl_and_access_audit_enforced"
    finally:
        session.close()


def test_support_search_resolves_case_bundle_and_safe_correlation_without_raw_identity(database) -> None:
    ticket_id, _version = _seed(database)
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    upload_id = str(uuid.uuid4())
    session = database()
    try:
        event = session.query(Event).filter(Event.tg_id == 1001).one()
        event.trace_id = "corr-support-501"
        session.add(
            SupportBundleUpload(
                upload_id=upload_id,
                ticket_id=ticket_id,
                owner_tg_id=1001,
                owner_binding_hash="a" * 64,
                idempotency_key="support-search-test",
                bundle_id="client-bundle-private-501",
                expected_size_bytes=32,
                expected_sha256="b" * 64,
                content_type="application/octet-stream",
                received_size_bytes=32,
                status="validated",
                object_name="private-object-name.bin",
                diagnostic_profile="standard",
                app_version="1.2.0",
                build_number="42",
                platform="windows",
                expires_at=now + timedelta(days=7),
                completed_at=now,
                validated_at=now,
            )
        )
        session.commit()

        detail = support_ticket_detail(session, environment="test", ticket_id=ticket_id)
        assert detail is not None
        bundle_ref = detail["support_bundles"][0]["bundle_ref"]
        assert support_bundle_upload_id_for_ref(
            session,
            environment="test",
            ticket_id=ticket_id,
            bundle_ref=bundle_ref,
        ) == upload_id

        case_results = search_support_cases(
            session, environment="test", query=f"#{ticket_id}"
        )
        bundle_results = search_support_cases(
            session, environment="test", query=bundle_ref
        )
        correlation_results = search_support_cases(
            session, environment="test", query="corr-support-501"
        )

        assert case_results[0]["kind"] == "case"
        assert bundle_results[0] == {
            "kind": "support_bundle",
            "id": bundle_ref,
            "title": f"Пакет поддержки · тикет #{ticket_id}",
            "subtitle": "Статус validated, профиль standard",
            "href": f"/tickets?selected={ticket_id}",
        }
        assert correlation_results[0]["kind"] == "correlation"
        projected = json.dumps(
            case_results + bundle_results + correlation_results,
            ensure_ascii=False,
        )
        for raw_value in (
            upload_id,
            "client-bundle-private-501",
            "private-object-name.bin",
            "raw-session-secret",
            "raw-device-secret",
            "support@example.test",
        ):
            assert raw_value not in projected
    finally:
        session.close()


def test_user_360_uses_opaque_attempt_refs_and_never_projects_raw_meta(database) -> None:
    ticket_id, _version = _seed(database)
    session = database()
    try:
        projection = user_360(
            session,
            environment="test",
            tg_id=1001,
            include_sensitive_diagnostics=True,
        )
        assert projection is not None
        assert projection["installations"][0]["installation_ref"].startswith("install_")
        assert projection["attempts"][0]["attempt_ref"].startswith("attempt_")
        assert projection["fingerprints"][0]["fingerprint"].startswith("fp_")
        serialized = json.dumps(projection, ensure_ascii=False)
        for forbidden in (
            "raw-token-must-never-leak",
            "private.example",
            "203.0.113.10",
            "raw-session-secret",
            "raw-device-secret",
            "raw-trace-secret",
            "install-secret-value",
        ):
            assert forbidden not in serialized

        explored = attempt_explorer(
            session, environment="test", ticket_id=ticket_id
        )
        assert explored is not None
        assert explored["attempts"][0]["event_count"] == 1
    finally:
        session.close()


def test_user_360_keeps_unlinked_events_separate_and_includes_account_tickets(database) -> None:
    direct_ticket_id, _version = _seed(database)
    session = database()
    try:
        user = session.query(User).filter(User.tg_id == 1001).one()
        account_id = str(uuid.uuid4())
        session.add(Account(id=account_id, status="active", created_source="test"))
        user.account_id = account_id
        session.flush()
        linked_ticket = create_ticket(
            session,
            user_tg_id=2002,
            account_id=account_id,
            subject="Тикет связанной идентичности",
        )
        linked_ticket.environment = "test"
        now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        for offset in (1, 2):
            session.add(
                Event(
                    tg_id=1001,
                    event_name=f"unlinked_event_{offset}",
                    source="client",
                    platform="windows",
                    surface="client",
                    result="failure",
                    occurred_at=now + timedelta(seconds=offset),
                    received_at=now + timedelta(seconds=offset),
                )
            )
        session.commit()

        projection = user_360(
            session,
            environment="test",
            tg_id=1001,
            include_sensitive_diagnostics=True,
        )
        assert projection is not None
        assert {row["id"] for row in projection["tickets"]} == {
            direct_ticket_id,
            int(linked_ticket.id),
        }
        assert len(projection["attempts"]) == 3
        assert len({row["attempt_ref"] for row in projection["attempts"]}) == 3
    finally:
        session.close()


def test_ticket_detail_never_resolves_incident_from_another_environment(database) -> None:
    ticket_id, _version = _seed(database)
    session = database()
    try:
        incident_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        session.add(
            ServiceIncident(
                id=incident_id,
                incident_key=f"cross-environment-{incident_id[:8]}",
                title="Чужой incident",
                summary="Не должен попасть в test projection.",
                started_at=now,
                confirmed_by=9999,
                confirmed_at=now,
                environment="production",
            )
        )
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).one()
        ticket.incident_id = incident_id
        session.commit()

        detail = support_ticket_detail(session, environment="test", ticket_id=ticket_id)
        assert detail is not None
        assert detail["incident"] is None
    finally:
        session.close()


def test_support_claim_is_guarded_by_explicit_and_intent_versions(database) -> None:
    ticket_id, _version = _seed(database)
    session = database()
    try:
        current = support_ticket_detail(session, environment="test", ticket_id=ticket_id)
        assert current is not None
        payload = {
            "_environment": "test",
            "_operator_id": "11111111-1111-4111-8111-111111111111",
            "_actor_tg_id": 9999,
            "expected_version": current["version"],
        }
        prepared = prepare_action_intent(
            session=session,
            actor_tg_id=9999,
            action="ticket.claim",
            target={"type": "ticket", "id": str(ticket_id)},
            payload=payload,
        )
        session.commit()
    finally:
        session.close()

    result = asyncio.run(
        execute_action_intent(
            session_factory=database,
            actor_tg_id=9999,
            intent_id=prepared["intent_id"],
            idempotency_key=str(uuid.uuid4()),
            confirmation_sha256_header=hashlib.sha256(
                "ПОДТВЕРДИТЬ".encode("utf-8")
            ).hexdigest(),
            action="ticket.claim",
            target={"type": "ticket", "id": str(ticket_id)},
            payload=payload,
            audit_writer=add_admin_audit,
        )
    )
    assert result["status"] == "completed"
    assert result["ticket"]["assigned_admin_tg_id"] == 9999
    assert result["ticket"]["version"] == payload["expected_version"] + 1

    stale_session = database()
    try:
        with pytest.raises(ActionIntentError) as raised:
            prepare_action_intent(
                session=stale_session,
                actor_tg_id=9999,
                action="ticket.claim",
                target={"type": "ticket", "id": str(ticket_id)},
                payload=payload,
            )
        assert raised.value.code == "stale_version"
    finally:
        stale_session.close()
