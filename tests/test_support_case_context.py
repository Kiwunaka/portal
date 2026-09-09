import json
import asyncio
import io
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


def test_vision_projection_redacts_and_rejects_extra_fields():
    from support_case_context import parse_attachment_analysis
    value = {"visible_text": "Оплата 99. Email person@example.org.\nПароль: secret-value",
             "visual_details": "Красная кнопка", "uncertainty": ""}
    result = parse_attachment_analysis(json.dumps(value))
    assert "99" in result["visible_text"] and result["visual_details"] == "Красная кнопка"
    assert "person@example.org" not in json.dumps(result) and "secret-value" not in json.dumps(result)
    with pytest.raises(ValueError, match="schema"):
        parse_attachment_analysis(json.dumps({**value, "reply": "внутренний ответ"}))
    with pytest.raises(ValueError, match="schema"):
        parse_attachment_analysis(json.dumps({**value, "visible_text": "x" * 1201}))


def test_images_and_pdf_pages_are_prepared_without_ocr(monkeypatch):
    from PIL import Image
    import support_case_context as module
    buffer = io.BytesIO(); Image.new("RGB", (20, 20), "red").save(buffer, format="PNG")
    assert module.prepare_vision_images(buffer.getvalue()) == [("image/png", buffer.getvalue())]
    with pytest.raises(ValueError, match="size"):
        module.prepare_vision_images(b"x" * (module.MAX_FILE_BYTES + 1))
    def rasterize(command, **kwargs):
        assert command[:7] == ["pdftoppm", "-f", "1", "-l", "3", "-scale-to", "1800"]
        assert kwargs["timeout"] == 8
        Path(command[-1] + "-1.jpg").write_bytes(b"rendered-page")
    monkeypatch.setattr(module.subprocess, "run", rasterize)
    assert module.prepare_vision_images(b"%PDF-fixture") == [("image/jpeg", b"rendered-page")]


@pytest.mark.parametrize("vision_failure", [False, True])
def test_case_load_parallel_vision_and_payment_keep_private_result(monkeypatch, tmp_path, vision_failure):
    from contextlib import nullcontext
    from PIL import Image
    import db
    import support_case_context as module
    image_path = tmp_path / "screen.png"
    Image.new("RGB", (20, 20), "red").save(image_path)
    (tmp_path / "note.txt").write_text("Ошибка. Email person@example.org", encoding="utf-8")
    monkeypatch.setenv("SUPPORT_UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(db, "SessionLocal", lambda: nullcontext(None))
    monkeypatch.setattr(module, "read_case", lambda *args: (
        {"operator_handling": False, "payments": [{"status": "paid"}]},
        [{"stored_name": "screen.png", "mime": "image/png"},
         {"stored_name": "note.txt", "mime": "text/plain"}], [(0, "owned-invoice")]))
    async def run():
        payment_started, vision_started = asyncio.Event(), asyncio.Event()
        async def payment(invoice):
            assert invoice == "owned-invoice"
            payment_started.set()
            await vision_started.wait()
            return {"status": "COMPLETED"}
        async def analyze(images):
            assert images[0][0] == "image/png"
            vision_started.set()
            await payment_started.wait()
            if vision_failure:
                raise asyncio.TimeoutError()
            return json.dumps({"visible_text": "99 рублей, person@example.org", "visual_details": "Красный значок", "uncertainty": ""})
        monkeypatch.setattr(module, "check_lava_invoice", payment)
        return await asyncio.wait_for(module.load_case(1, 10, analyze_attachment=analyze), timeout=2)
    result = asyncio.run(run())
    assert result["payments"][0]["live_provider"]["status"] == "COMPLETED"
    assert "person@example.org" not in json.dumps(result)
    if vision_failure:
        assert result["attachments"][0]["status"] == "unreadable_or_over_limit"
    else:
        assert result["attachments"][0]["visual_details"] == "Красный значок"
    assert result["attachments"][1]["source"] == "unverified_user_file_text"
