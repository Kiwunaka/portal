import asyncio
import importlib
import os
import sys
import tempfile
import types
import unittest
import uuid
from pathlib import Path

from sqlalchemy.orm import close_all_sessions


class _FakeUser:
    def __init__(self, tg_id: int):
        self.id = int(tg_id)


class _FakeBot:
    def __init__(self):
        self.messages: list[dict] = []
        self.copies: list[dict] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": int(chat_id), "text": str(text), **dict(kwargs)})
        return None


class _FakeMessage:
    def __init__(
        self,
        tg_id: int,
        *,
        bot: _FakeBot | None = None,
        text: str = "",
        caption: str = "",
        document=None,
        media_group_id: str = "",
    ):
        self.from_user = _FakeUser(tg_id)
        self.text = text
        self.caption = caption
        self.document = document
        self.photo = []
        self.video = None
        self.media_group_id = media_group_id
        self.bot = bot or _FakeBot()
        self.answers: list[tuple[str, dict]] = []

    async def answer(self, text, **kwargs):
        self.answers.append((str(text), dict(kwargs)))
        return None

    async def copy_to(self, chat_id, **kwargs):
        self.bot.copies.append({"chat_id": int(chat_id), **dict(kwargs)})
        return None


class _FakeTelegramFile:
    def __init__(self, file_id: str, **kwargs):
        self.file_id = file_id
        self.file_unique_id = kwargs.pop("file_unique_id", f"unique-{file_id}")
        for key, value in kwargs.items():
            setattr(self, key, value)


class MainBotTicketAttachmentTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for key in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID", "NEWS_CHANNEL_ID", "CHECKOUT_TICKET_SECRET"):
            self._saved_env[key] = os.environ.get(key)

        self._saved_qrcode = sys.modules.get("qrcode")
        if self._saved_qrcode is None:
            class _DummyQR:
                def __init__(self, *args, **kwargs):
                    pass

                def add_data(self, *args, **kwargs):
                    return None

                def make(self, *args, **kwargs):
                    return None

                def make_image(self, *args, **kwargs):
                    class _Img:
                        def save(self, *args, **kwargs):
                            return None

                    return _Img()

            sys.modules["qrcode"] = types.SimpleNamespace(QRCode=_DummyQR)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_main_bot_ticket_test_{uuid.uuid4().hex}.db").resolve())
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"
        os.environ["BOT_TOKEN"] = "123456:test_main_bot_token"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["NEWS_CHANNEL_ID"] = "@portal_news_channel"
        os.environ["CHECKOUT_TICKET_SECRET"] = "checkout_secret_test_123"

        for module_name in (
            "config",
            "db",
            "models",
            "migrations",
            "tickets_repo",
            "copy_catalog",
            "telegram_buttons",
            "telegram_profile",
            "bot",
        ):
            sys.modules.pop(module_name, None)

        self.bot_module = importlib.import_module("bot")
        importlib.reload(self.bot_module)

    def tearDown(self) -> None:
        close_all_sessions()
        db_module = sys.modules.get("db")
        if db_module is not None:
            try:
                db_module.engine.dispose()
            except Exception:
                pass
        for module_name in ("bot", "telegram_profile", "telegram_buttons", "tickets_repo", "migrations", "models", "db", "config"):
            sys.modules.pop(module_name, None)
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if self._saved_qrcode is None:
            sys.modules.pop("qrcode", None)
        else:
            sys.modules["qrcode"] = self._saved_qrcode
        try:
            Path(self.db_path).unlink(missing_ok=True)
        finally:
            self._tmp.cleanup()

    def _create_ticket(self, user_tg_id: int = 1001) -> int:
        session = self.bot_module.Session()
        try:
            ticket = self.bot_module.create_ticket(session, user_tg_id=user_tg_id)
            session.commit()
            return int(ticket.id)
        finally:
            session.close()

    def _ticket_messages(self, ticket_id: int):
        session = self.bot_module.Session()
        try:
            ticket = self.bot_module.get_ticket_by_id(session, ticket_id)
            messages = self.bot_module.list_ticket_messages(session, ticket_id=ticket_id, limit=20)
            return ticket, messages
        finally:
            session.close()

    def test_admin_ticket_reply_accepts_document_with_caption(self) -> None:
        ticket_id = self._create_ticket(user_tg_id=1001)
        self.bot_module.pending_ticket_replies[9999] = ticket_id
        fake_bot = _FakeBot()
        document = _FakeTelegramFile(
            "document-file-id",
            file_name="Hiddify-Windows-Setup-x64.exe",
            mime_type="application/octet-stream",
            file_size=36_400_000,
        )
        message = _FakeMessage(
            9999,
            bot=fake_bot,
            caption="Здравствуйте, могу отправить ссылку на запасное приложение.",
            document=document,
        )

        asyncio.run(self.bot_module.capture_ticket_attachment(message))

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.bot_module.STATUS_IN_PROGRESS)
        self.assertEqual(ticket.assigned_admin_tg_id, 9999)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].sender_role, "admin")
        self.assertEqual(messages[0].media_type, "file")
        self.assertEqual(messages[0].media_file_id, "document-file-id")
        self.assertIn("запасное приложение", messages[0].body)
        self.assertNotIn(9999, self.bot_module.pending_ticket_replies)
        self.assertTrue(message.answers)
        self.assertIn("Ответ добавлен", message.answers[-1][0])
        self.assertEqual(fake_bot.copies[0]["chat_id"], 1001)
        self.assertIn("Новый ответ команды POKROV", fake_bot.copies[0]["caption"])
        self.assertIn("запасное приложение", fake_bot.copies[0]["caption"])

    def test_admin_ticket_reply_accepts_multiple_documents_from_same_media_group(self) -> None:
        ticket_id = self._create_ticket(user_tg_id=1001)
        self.bot_module.pending_ticket_replies[9999] = ticket_id
        fake_bot = _FakeBot()

        first = _FakeMessage(
            9999,
            bot=fake_bot,
            document=_FakeTelegramFile("first-file-id", file_name="Hiddify-Windows-Setup-x64.exe"),
            media_group_id="album-1",
        )
        second = _FakeMessage(
            9999,
            bot=fake_bot,
            caption="Приложение для Android.",
            document=_FakeTelegramFile("second-file-id", file_name="Hiddify-Android-arm64.apk"),
            media_group_id="album-1",
        )

        asyncio.run(self.bot_module.capture_ticket_attachment(first))
        asyncio.run(self.bot_module.capture_ticket_attachment(second))

        _ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual([message.media_file_id for message in messages], ["first-file-id", "second-file-id"])
        self.assertEqual(len(fake_bot.copies), 2)
