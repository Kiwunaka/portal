import asyncio
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))


@pytest.fixture
def case_db(tmp_path, monkeypatch):
    import db
    from models import (Base, User, SupportTicket, SupportTicketMessage, SupportAttachment,
                        AccountIdentity, ExternalOrder, ExternalPaymentEvent, AdminAudit,
                        SupportBundleUpload, Event, AccessKey, NodeRuntimeMetric)
    engine = create_engine("sqlite:///" + str(tmp_path / "case.db"))
    tables = [User, SupportTicket, SupportTicketMessage, SupportAttachment, AccountIdentity,
              ExternalOrder, ExternalPaymentEvent, AdminAudit, SupportBundleUpload, Event,
              AccessKey, NodeRuntimeMetric]
    Base.metadata.create_all(engine, tables=[m.__table__ for m in tables])
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(db, "SessionLocal", factory)
    with factory() as session:
        session.add_all([User(tg_id=1, account_id="own"), User(tg_id=2, account_id="own"),
                         User(tg_id=3, account_id="foreign"),
                         SupportTicket(id=10, user_tg_id=1, account_id="own"),
                         SupportTicketMessage(ticket_id=10, sender_tg_id=1, sender_role="user", body="Оплатил, доступа нет"),
                         ExternalOrder(tg_id=2, order_id="own-private", provider="test", status="paid", amount=99),
                         ExternalOrder(tg_id=3, order_id="other-private", provider="test", status="paid", amount=777),
                         AccessKey(tg_id=2, key_uuid="own-key", panel_email="own-private", node_code="own-node"),
                         AccessKey(tg_id=3, key_uuid="foreign-key", panel_email="foreign-private", node_code="foreign-node"),
                         NodeRuntimeMetric(node_code="own-node", dataplane_ok=True),
                         NodeRuntimeMetric(node_code="foreign-node", dataplane_ok=False)])
        session.commit()
    yield factory
    engine.dispose()


def test_tools_are_owner_bound_and_writes_commit_with_reply(case_db):
    from support_case_tools import CaseTools, persist_case_actions
    from support_case_context import pending_case_message
    from models import SupportTicket, SupportTicketMessage
    from tickets_repo import add_ticket_message

    async def run():
        tools = CaseTools(1, 10)
        assert await tools.start()
        assert not await CaseTools(3, 10).start()
        async def call(name, args):
            return await tools.execute(name, args, analyze_attachment=None, search=lambda _: [])
        assert await call("read_payments", {"owner_id": 3}) == {"error": "invalid_arguments"}
        payments = await call("read_payments", {})
        assert [p["amount"] for p in payments["payments"]] == [99]
        assert "private" not in json.dumps(payments)
        nodes = await call("read_node_status", {})
        assert [node["dataplane_ok"] for node in nodes["nodes"]] == [True]
        assert "own-node" not in json.dumps(nodes) and "private" not in json.dumps(nodes)
        await call("write_case_note", {"text": "Оплата есть, доступа нет. Email user@example.org"})
        await call("propose_action", {"action": "review_access", "reason": "Проверить выдачу доступа"})
        await call("request_operator", {"queue": "billing", "reason": "Нужно проверить выдачу"})
        with case_db() as session:
            assert session.query(SupportTicketMessage).count() == 1
            assert pending_case_message(session, 1, 10, lock=True) == tools.revision
            persist_case_actions(session, 10, tuple(tools.actions))
            session.rollback()
        with case_db() as session:
            assert session.get(SupportTicket, 10).escalated_at is None
            assert session.query(SupportTicketMessage).count() == 1
            assert persist_case_actions(session, 10, tuple(tools.actions))
            reply = "Длинный ответ. " * 800 + "\nОбращение передано в очередь оператора."
            add_ticket_message(session, ticket_id=10, sender_role="assistant", sender_tg_id=0, body=reply)
            session.commit()
            messages = session.query(SupportTicketMessage).order_by(SupportTicketMessage.id).all()
            assert len(messages) == 5 and messages[-1].body == reply
            assert all(m.visibility == "internal" for m in messages[1:4])
            assert "user@example.org" not in messages[1].body
            ticket = session.get(SupportTicket, 10)
            assert ticket.waiting_on == "operator" and ticket.queue == "billing" and ticket.escalated_at
            assert pending_case_message(session, 1, 10) is None
    asyncio.run(run())


def test_tools_reject_stale_turn(case_db):
    from support_case_tools import CaseTools
    from tickets_repo import add_ticket_message
    async def run():
        tools = CaseTools(1, 10)
        assert await tools.start()
        with case_db() as session:
            add_ticket_message(session, ticket_id=10, sender_tg_id=1, sender_role="user", body="Новое сообщение")
            session.commit()
        assert await tools.execute("request_operator", {"reason": "Проверка", "queue": "billing"},
                                   analyze_attachment=None, search=None) == {"error": "case_changed"}
        assert tools.actions == []
    asyncio.run(run())


def test_tool_attachment_and_provider_reads_are_on_demand(case_db, monkeypatch):
    import support_case_context as context
    calls = []
    original = context.read_case
    def read(*args):
        data, _, _ = original(*args)
        return data, [{"telegram_id": "file", "media_type": "document"}], [(0, "invoice")]
    monkeypatch.setattr(context, "read_case", read)
    async def provider(_):
        calls.append("provider")
        return {"source": "test_live", "status": "COMPLETED"}
    monkeypatch.setattr(context, "check_lava_invoice", provider)
    async def run():
        snapshot = await context.load_case(1, 10, analyze_attachment=None, section="account")
        assert snapshot["attachments"] == [] and calls == []
        snapshot = await context.load_case(1, 10, analyze_attachment=None, section="payments")
        assert snapshot["payments"][0]["live_provider"]["status"] == "COMPLETED"
        assert snapshot["attachments"] == [] and calls == ["provider"]
    asyncio.run(run())
