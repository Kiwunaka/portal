import asyncio
import importlib
import json
import os
import sys
import tempfile
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
        self.command_sets: list[list[object]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": int(chat_id), "text": str(text), **dict(kwargs)})
        return None

    async def set_my_commands(self, commands):
        self.command_sets.append(list(commands))


class _FakeMessage:
    def __init__(
        self,
        tg_id: int,
        text: str = "",
        bot: _FakeBot | None = None,
        *,
        caption: str = "",
        photo: list | None = None,
        document=None,
        video=None,
    ):
        self.from_user = _FakeUser(tg_id)
        self.text = text
        self.caption = caption
        self.photo = photo or []
        self.document = document
        self.video = video
        self.bot = bot or _FakeBot()
        self.answers: list[tuple[str, dict]] = []
        self.edits: list[str] = []
        self.edit_kwargs: list[dict] = []

    async def answer(self, text, **kwargs):
        self.answers.append((str(text), dict(kwargs)))
        return None

    async def edit_text(self, text, **kwargs):
        self.edits.append(str(text))
        self.edit_kwargs.append(dict(kwargs))
        return None

    async def copy_to(self, chat_id, **kwargs):
        self.bot.copies.append({"chat_id": int(chat_id), **dict(kwargs)})
        return None


class _FakeCallback:
    def __init__(self, tg_id: int, data: str, bot: _FakeBot | None = None):
        self.from_user = _FakeUser(tg_id)
        self.data = data
        self.bot = bot or _FakeBot()
        self.message = _FakeMessage(tg_id, bot=self.bot)
        self.answers: list[tuple[str, bool]] = []

    async def answer(self, text="", show_alert=False):
        self.answers.append((str(text), bool(show_alert)))
        return None


class _FakeTelegramFile:
    def __init__(self, file_id: str, **kwargs):
        self.file_id = file_id
        self.file_unique_id = kwargs.pop("file_unique_id", f"unique-{file_id}")
        for key, value in kwargs.items():
            setattr(self, key, value)


class HelpbotLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for key in (
            "DATABASE_URL",
            "HELP_BOT_TOKEN",
            "ADMIN_ID",
            "BOT_USERNAME",
            "TG_BTN_EMOJI_PRIMARY_ID",
            "TG_BTN_EMOJI_SUCCESS_ID",
            "TG_BTN_EMOJI_DANGER_ID",
            "SUPPORT_AI_ENABLED",
            "SUPPORT_AI_API_KEY",
            "SUPPORT_AI_MODEL",
            "SUPPORT_AI_MIN_INTERVAL_SECONDS",
        ):
            self._saved_env[key] = os.environ.get(key)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_helpbot_test_{uuid.uuid4().hex}.db").resolve())
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.db_path).as_posix()}"
        os.environ["HELP_BOT_TOKEN"] = "123456:test_helpbot_token"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["BOT_USERNAME"] = "pokrov_vpnbot"
        os.environ["TG_BTN_EMOJI_PRIMARY_ID"] = "5368324170671202286"
        os.environ["TG_BTN_EMOJI_SUCCESS_ID"] = "5373141891321699086"
        os.environ["TG_BTN_EMOJI_DANGER_ID"] = "5368324170671202299"
        os.environ["SUPPORT_AI_ENABLED"] = "false"
        os.environ["SUPPORT_AI_API_KEY"] = ""
        os.environ["SUPPORT_AI_MODEL"] = "deepseek/deepseek-v4-flash"
        os.environ["SUPPORT_AI_MIN_INTERVAL_SECONDS"] = "0"

        for module_name in (
            "config",
            "db",
            "models",
            "migrations",
            "tickets_repo",
            "copy_catalog",
            "telegram_buttons",
            "support_ai_service",
            "helpbot",
        ):
            sys.modules.pop(module_name, None)

        self.helpbot = importlib.import_module("helpbot")
        self.telegram_buttons = importlib.import_module("telegram_buttons")

    def tearDown(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for module_name in ("helpbot", "support_ai_service", "tickets_repo", "db", "models", "migrations"):
            sys.modules.pop(module_name, None)
        try:
            close_all_sessions()
            bind = self.helpbot.SessionLocal.kw.get("bind")
            if bind is not None:
                bind.dispose()
            Path(self.db_path).unlink(missing_ok=True)
        finally:
            self._tmp.cleanup()

    def _ticket_messages(self, ticket_id: int):
        session = self.helpbot.SessionLocal()
        try:
            ticket = self.helpbot.get_ticket_by_id(session, ticket_id)
            messages = self.helpbot.list_ticket_messages(session, ticket_id=ticket_id, limit=20)
            return ticket, messages
        finally:
            session.close()

    def test_user_and_admin_continue_same_helpbot_ticket_thread(self) -> None:
        bot = _FakeBot()

        start = _FakeMessage(1001, "/start ticket_new", bot=bot)
        asyncio.run(self.helpbot.start(start))
        self.assertTrue(start.answers)
        self.assertIn("1001", str(bot.messages[-1]["text"]))
        self.assertIn(1001, self.helpbot.pending_ticket_replies)

        ticket_id = self.helpbot.pending_ticket_replies[1001]
        user_reply = _FakeMessage(1001, "First launch does not connect", bot=bot)
        asyncio.run(self.helpbot.capture_ticket_reply(user_reply))
        self.assertNotIn(1001, self.helpbot.pending_ticket_replies)

        admin_open = _FakeCallback(9999, f"hb_ticket_reply_{ticket_id}", bot=bot)
        asyncio.run(self.helpbot.ticket_reply(admin_open))
        self.assertEqual(self.helpbot.pending_ticket_replies[9999], ticket_id)

        admin_reply = _FakeMessage(9999, "Please refresh the profile and try again.", bot=bot)
        asyncio.run(self.helpbot.capture_ticket_reply(admin_reply))

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.helpbot.STATUS_IN_PROGRESS)
        self.assertEqual([message.sender_role for message in messages], ["user", "admin"])
        self.assertEqual([message.body for message in messages], ["First launch does not connect", "Please refresh the profile and try again."])
        self.assertTrue(any(message["chat_id"] == 1001 for message in bot.messages))

    def test_user_text_receives_ai_support_hint_when_enabled(self) -> None:
        bot = _FakeBot()

        async def fake_generate(user_text, *, ticket_id, user_tg_id, config):
            self.assertEqual(user_text, "How do I get the trial?")
            self.assertGreater(ticket_id, 0)
            self.assertEqual(user_tg_id, 1001)
            return "**Коротко:** Откройте приложение POKROV и нажмите `Try free`."

        self.helpbot.SUPPORT_AI_CONFIG.enabled = True
        self.helpbot.SUPPORT_AI_CONFIG.api_key = "sk-test"
        self.helpbot.SUPPORT_AI_CONFIG.min_interval_seconds = 0
        self.helpbot.generate_support_reply = fake_generate

        start = _FakeMessage(1001, "/start ticket_new", bot=bot)
        asyncio.run(self.helpbot.start(start))
        ticket_id = self.helpbot.pending_ticket_replies[1001]

        user_reply = _FakeMessage(1001, "How do I get the trial?", bot=bot)
        asyncio.run(self.helpbot.capture_ticket_reply(user_reply))

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.helpbot.STATUS_OPEN)
        self.assertEqual([message.sender_role for message in messages], ["user", "assistant"])
        self.assertEqual(messages[-1].body, "**Коротко:** Откройте приложение POKROV и нажмите `Try free`.")
        self.assertTrue(user_reply.answers)
        self.assertIn("<b>Коротко:</b>", user_reply.answers[-1][0])
        self.assertIn("<code>Try free</code>", user_reply.answers[-1][0])
        self.assertEqual(user_reply.answers[-1][1].get("parse_mode"), "HTML")
        buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in user_reply.answers[-1][1]["reply_markup"].inline_keyboard
            for button in row
        }
        self.assertIn(f"hb_aiq_no_{ticket_id}", buttons)
        self.assertIn(f"hb_aiq_steps_{ticket_id}", buttons)
        self.assertIn(f"hb_aiq_operator_{ticket_id}", buttons)

    def test_helpbot_ai_quick_replies_prompt_details_or_call_operator(self) -> None:
        bot = _FakeBot()

        start = _FakeMessage(1001, "/start ticket_new", bot=bot)
        asyncio.run(self.helpbot.start(start))
        ticket_id = self.helpbot.pending_ticket_replies[1001]

        user_reply = _FakeMessage(1001, "Hiddify пустой профиль", bot=bot)
        asyncio.run(self.helpbot.capture_ticket_reply(user_reply))

        details = _FakeCallback(1001, f"hb_aiq_no_{ticket_id}", bot=bot)
        asyncio.run(self.helpbot.support_ai_quick_reply(details))
        self.assertEqual(self.helpbot.pending_ticket_replies[1001], ticket_id)
        self.assertTrue(details.message.answers)
        self.assertIn("Устройство:", details.message.answers[-1][0])

        operator = _FakeCallback(1001, f"hb_aiq_operator_{ticket_id}", bot=bot)
        asyncio.run(self.helpbot.support_ai_quick_reply(operator))

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.helpbot.STATUS_OPEN)
        self.assertEqual([message.sender_role for message in messages], ["user", "user"])
        self.assertEqual(messages[-1].body, "Нужна ручная проверка оператором.")
        self.assertTrue(any(row["chat_id"] == 9999 and "попросил оператора" in row["text"] for row in bot.messages))

    def test_helpbot_captures_telegram_photo_and_document_attachments(self) -> None:
        bot = _FakeBot()

        start = _FakeMessage(1001, "/start ticket_new", bot=bot)
        asyncio.run(self.helpbot.start(start))
        ticket_id = self.helpbot.pending_ticket_replies[1001]

        user_photo = _FakeMessage(
            1001,
            bot=bot,
            caption="Экран ошибки после входа",
            photo=[_FakeTelegramFile("photo-file-id", width=1280, height=720, file_size=4096)],
        )
        asyncio.run(self.helpbot.capture_ticket_attachment(user_photo))
        self.assertNotIn(1001, self.helpbot.pending_ticket_replies)

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.helpbot.STATUS_OPEN)
        self.assertEqual(messages[0].sender_role, "user")
        self.assertEqual(messages[0].body, "Экран ошибки после входа")
        self.assertEqual(messages[0].media_type, "photo")
        self.assertEqual(messages[0].media_file_id, "photo-file-id")
        user_payload = json.loads(messages[0].media_payload)
        self.assertEqual(user_payload["source"], "telegram")
        self.assertEqual(user_payload["kind"], "photo")
        self.assertEqual(user_payload["name"], "Скриншот из Telegram")
        self.assertTrue(any(row["chat_id"] == 9999 for row in bot.copies))

        admin_open = _FakeCallback(9999, f"hb_ticket_reply_{ticket_id}", bot=bot)
        asyncio.run(self.helpbot.ticket_reply(admin_open))

        admin_document = _FakeMessage(
            9999,
            bot=bot,
            caption="Посмотрите лог, пожалуйста",
            document=_FakeTelegramFile("document-file-id", file_name="pokrov.log", mime_type="text/plain", file_size=2048),
        )
        asyncio.run(self.helpbot.capture_ticket_attachment(admin_document))

        ticket, messages = self._ticket_messages(ticket_id)
        self.assertEqual(ticket.status, self.helpbot.STATUS_IN_PROGRESS)
        self.assertEqual([message.sender_role for message in messages], ["user", "admin"])
        self.assertEqual(messages[1].media_type, "file")
        self.assertEqual(messages[1].media_file_id, "document-file-id")
        admin_payload = json.loads(messages[1].media_payload)
        self.assertEqual(admin_payload["name"], "pokrov.log")
        self.assertEqual(admin_payload["content_type"], "text/plain")
        self.assertTrue(any(row["chat_id"] == 1001 and "Новый ответ команды POKROV" in row.get("caption", "") for row in bot.copies))

    def test_helpbot_denies_other_user_ticket_view(self) -> None:
        bot = _FakeBot()
        start = _FakeMessage(1001, "/start ticket_new", bot=bot)
        asyncio.run(self.helpbot.start(start))
        ticket_id = self.helpbot.pending_ticket_replies[1001]

        denied = _FakeCallback(1002, f"hb_ticket_view_{ticket_id}", bot=bot)
        asyncio.run(self.helpbot.ticket_view(denied))

        self.assertTrue(denied.answers)
        self.assertTrue(denied.answers[-1][1])

    def test_helpbot_keyboards_use_modern_button_fields_when_supported(self) -> None:
        if not self.telegram_buttons.SUPPORTS_BTN_STYLE:
            self.skipTest("aiogram InlineKeyboardButton has no style field")

        menu_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.helpbot._main_menu(is_admin=True).inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(menu_buttons["hb_ticket_new"], "style", None), self.telegram_buttons.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(menu_buttons["hb_ticket_my"], "style", None), self.telegram_buttons.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(menu_buttons["hb_admin_queue"], "style", None), self.telegram_buttons.BTN_STYLE_PRIMARY)

        open_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.helpbot._ticket_view_keyboard(42, self.helpbot.STATUS_OPEN, is_admin=False).inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(open_buttons["hb_ticket_reply_42"], "style", None), self.telegram_buttons.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(open_buttons["hb_ticket_close_42"], "style", None), self.telegram_buttons.BTN_STYLE_DANGER)
        self.assertEqual(getattr(open_buttons["hb_ticket_my"], "style", None), self.telegram_buttons.BTN_STYLE_PRIMARY)

        closed_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.helpbot._ticket_view_keyboard(42, self.helpbot.STATUS_CLOSED, is_admin=False).inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(closed_buttons["hb_ticket_reopen_42"], "style", None), self.telegram_buttons.BTN_STYLE_SUCCESS)

        if self.telegram_buttons.SUPPORTS_BTN_ICON:
            self.assertEqual(getattr(menu_buttons["hb_ticket_new"], "icon_custom_emoji_id", None), "5373141891321699086")
            self.assertEqual(getattr(open_buttons["hb_ticket_close_42"], "icon_custom_emoji_id", None), "5368324170671202299")

    def test_helpbot_configures_public_start_command(self) -> None:
        bot = _FakeBot()

        asyncio.run(self.helpbot._configure_support_bot_commands(bot))

        self.assertTrue(bot.command_sets)
        commands = {getattr(command, "command", ""): getattr(command, "description", "") for command in bot.command_sets[-1]}
        self.assertEqual(commands, {"start": "Открыть поддержку"})
