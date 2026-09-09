import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))


def test_case_owner_linked_payment_redaction_and_operator_handoff():
    from models import (Base, User, SupportTicket, SupportTicketMessage, SupportAttachment,
                        AccountIdentity, ExternalOrder, ExternalPaymentEvent, AdminAudit, SupportBundleUpload, Event)
    from support_case_context import read_case, pending_case_message
    engine = create_engine("sqlite://")
    tables = [User, SupportTicket, SupportTicketMessage, SupportAttachment, AccountIdentity,
              ExternalOrder, ExternalPaymentEvent, AdminAudit, SupportBundleUpload, Event]
    Base.metadata.create_all(engine, tables=[m.__table__ for m in tables])
    with Session(engine) as session:
        session.add_all([User(tg_id=1, account_id="owned"), User(tg_id=2, account_id="owned"),
                         User(tg_id=3, account_id="other")])
        session.add_all([SupportTicket(id=10, user_tg_id=1, account_id="owned"),
                         ExternalOrder(tg_id=2, order_id="private-order", provider="test", status="paid", amount=99),
                         ExternalOrder(tg_id=3, order_id="foreign-order", provider="test", status="paid", amount=777),
                         SupportTicketMessage(ticket_id=10, sender_tg_id=1, sender_role="user",
                           body="Оплатил, но доступ не появился. Email person@example.org. Пароль: secret-value")])
        session.commit()
        case, _, _ = read_case(session, 1, 10)
        assert [p["amount"] for p in case["payments"]] == [99]
        serialized = json.dumps(case)
        assert all(secret not in serialized for secret in ("private-order", "foreign-order", "person@example.org", "secret-value"))
        assert pending_case_message(session, 2, 10) is not None
        with pytest.raises(ValueError, match="owner_mismatch"):
            read_case(session, 3, 10)
        assert pending_case_message(session, 3, 10) is None
        session.get(SupportTicket, 10).assigned_admin_tg_id = 99
        session.flush()
        assert read_case(session, 1, 10) == ({"operator_handling": True}, [], [])
        assert pending_case_message(session, 1, 10) is None


def test_file_extract_redacts_before_context_and_bounds_size():
    from support_case_context import extract_file, MAX_FILE_BYTES
    text = extract_file("Оплата прошла. Email person@example.org.\nПароль: secret-value".encode(), "text/plain")
    assert "person@example.org" not in text and "secret-value" not in text
    assert "лимит" in extract_file(b"x" * (MAX_FILE_BYTES + 1), "text/plain")
