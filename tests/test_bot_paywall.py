import asyncio
from contextlib import contextmanager
import importlib
import os
import sys
import tempfile
import types
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError


class _FakeMember:
    def __init__(self, status: str):
        self.status = status


class _FakeBot:
    def __init__(self, status: str | None = None, fail: bool = False):
        self._status = status
        self._fail = fail
        self.calls: list[tuple[str, int]] = []
        self.invoices: list[dict] = []
        self.pre_checkout_answers: list[dict] = []
        self.command_sets: list[list[object]] = []
        self.menu_buttons: list[object] = []
        self.messages: list[dict] = []

    async def get_chat_member(self, chat_id: str, user_id: int):
        self.calls.append((chat_id, user_id))
        if self._fail:
            raise RuntimeError("api unavailable")
        return _FakeMember(self._status or "left")

    async def send_invoice(self, **kwargs):
        self.invoices.append(dict(kwargs))
        return None

    async def answer_pre_checkout_query(self, pre_checkout_query_id, **kwargs):
        self.pre_checkout_answers.append({"id": pre_checkout_query_id, **dict(kwargs)})
        return None

    async def set_my_commands(self, commands):
        self.command_sets.append(list(commands))
        return None

    async def set_chat_menu_button(self, **kwargs):
        self.menu_buttons.append(kwargs.get("menu_button"))
        return None

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": chat_id, "text": str(text), **dict(kwargs)})
        return None


class _FakeMessage:
    def __init__(self, tg_id: int = 1001, text: str = ""):
        self.from_user = _FakeUser(tg_id)
        self.text = text
        self.edits: list[str] = []
        self.edit_kwargs: list[dict] = []
        self.answers: list[tuple[str, dict]] = []

    async def edit_text(self, text, **_kwargs):
        self.edits.append(str(text))
        self.edit_kwargs.append(dict(_kwargs))
        return None

    async def answer(self, text, **kwargs):
        self.answers.append((str(text), dict(kwargs)))
        return None


class _FakeUser:
    def __init__(self, tg_id: int):
        self.id = int(tg_id)


class _FakeCallback:
    def __init__(self, tg_id: int, data: str = ""):
        self.from_user = _FakeUser(tg_id)
        self.message = _FakeMessage()
        self.answers: list[tuple[str, bool]] = []
        self.data = data

    async def answer(self, text="", show_alert=False):
        self.answers.append((str(text), bool(show_alert)))
        return None


class BotPaywallTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved_env: dict[str, str | None] = {}
        for k in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "ADMIN_ID",
            "NEWS_CHANNEL_ID",
            "CHECKOUT_TICKET_SECRET",
            "CHECKOUT_TICKET_TTL_SECONDS",
            "BOT_STARS_PAYMENTS_ENABLED",
            "SUPPORT_USERNAME",
            "SUPPORT_BOT_USERNAME",
            "FEEDBACK_USERNAME",
        ):
            self._saved_env[k] = os.environ.get(k)
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
                        def save(self, *a, **k):
                            return None

                    return _Img()

            sys.modules["qrcode"] = types.SimpleNamespace(QRCode=_DummyQR)

        self._tmp = tempfile.TemporaryDirectory()
        db_path = (repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").as_posix()
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["NEWS_CHANNEL_ID"] = "@portal_news_channel"
        os.environ["CHECKOUT_TICKET_SECRET"] = "checkout_secret_test_123"
        os.environ["CHECKOUT_TICKET_TTL_SECONDS"] = "900"
        os.environ["BOT_STARS_PAYMENTS_ENABLED"] = "false"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["SUPPORT_BOT_USERNAME"] = "pokrov_supportbot"
        os.environ["FEEDBACK_USERNAME"] = "pokrov_feedbackbot"

        for module_name in (
            "bot",
            "payment_providers",
            "email_delivery_service",
            "gift_cards_service",
            "events_service",
            "free_cycle_service",
            "pay_attempts_service",
            "points_service",
            "tickets_repo",
            "web_auth_service",
            "nodes_repo",
            "models",
            "db",
            "config",
        ):
            sys.modules.pop(module_name, None)
        self.bot_module = importlib.import_module("bot")

    @contextmanager
    def _checkout_gate_green(self):
        old_gate = self.bot_module._bot_checkout_runtime_issues
        self.bot_module._bot_checkout_runtime_issues = lambda: []
        try:
            yield
        finally:
            self.bot_module._bot_checkout_runtime_issues = old_gate

    def _make_paid_user(self, tg_id: int = 1001) -> None:
        self.bot_module.ensure_pending_user(tg_id, username="alice")
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=tg_id).first()
            self.assertIsNotNone(user)
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.is_active = True
            user.first_purchase_done = True
            user.expiry_at = self.bot_module._utcnow() + timedelta(days=30)
            session.commit()
        finally:
            session.close()

    def tearDown(self) -> None:
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if self._saved_qrcode is None:
            sys.modules.pop("qrcode", None)
        else:
            sys.modules["qrcode"] = self._saved_qrcode
        self._tmp.cleanup()

    def test_build_subscription_link_uses_canonical_connect_host(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.sub_token = "token_1001_secure"
            session.commit()
        finally:
            session.close()

        link = self.bot_module.build_subscription_link(1001)
        self.assertTrue(link.startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/token_1001_secure"))

    def test_show_key_frames_connection_link_as_manual_recovery_path(self) -> None:
        class _EditableMessage(_FakeMessage):
            async def edit_text(self, text, **kwargs):
                self.edits.append(str(text))
                self.edit_kwargs.append(dict(kwargs))
                return self

            async def answer_photo(self, photo=None, caption=None, **kwargs):
                self.answers.append((str(caption), dict(kwargs)))
                return None

        class _EditableCallback(_FakeCallback):
            def __init__(self, tg_id: int):
                super().__init__(tg_id=tg_id, data="show_key")
                self.message = _EditableMessage()

        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.sub_token = "token_1001_secure"
            user.is_active = True
            user.sub_type = "PAID"
            user.expiry_at = self.bot_module._utcnow() + timedelta(days=30)
            session.commit()
        finally:
            session.close()

        callback = _EditableCallback(1001)

        async def _fast_sleep(_seconds: float):
            return None

        with patch("asyncio.sleep", new=_fast_sleep):
            asyncio.run(self.bot_module.show_key(callback))

        final_text = callback.message.edits[-1]
        self.assertIn("https://connect.pokrov.space/s8Kx2mP7qR4wT/token_1001_secure", final_text)
        self.assertIn("ручной вариант", final_text.lower())
        self.assertIn("запасной", final_text.lower())
        self.assertNotIn("?format=plain", final_text)
        self.assertNotIn("Обычная ссылка", final_text)

        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        labels = [button.text for row in reply_markup.inline_keyboard for button in row]
        self.assertIn("📲 Открыть кабинет", labels)
        self.assertIn("🧭 Ручная ссылка", labels)
        self.assertIn("📱 QR для ручного подключения", labels)
        self.assertNotIn("📋 Скопировать ссылку", labels)

    def test_check_subscription_allows_when_channel_not_configured(self) -> None:
        self.bot_module.NEWS_CHANNEL_ID = ""
        fake = _FakeBot(status="left")
        ok = asyncio.run(self.bot_module.check_subscription(1001, fake))
        self.assertTrue(ok)
        self.assertEqual(fake.calls, [])

    def test_check_subscription_true_for_member(self) -> None:
        self.bot_module.NEWS_CHANNEL_ID = "@portal_news_channel"
        fake = _FakeBot(status="member")
        ok = asyncio.run(self.bot_module.check_subscription(1001, fake))
        self.assertTrue(ok)
        self.assertEqual(fake.calls, [("@portal_news_channel", 1001)])

    def test_check_subscription_false_for_non_member(self) -> None:
        self.bot_module.NEWS_CHANNEL_ID = "@portal_news_channel"
        fake = _FakeBot(status="left")
        ok = asyncio.run(self.bot_module.check_subscription(1001, fake))
        self.assertFalse(ok)

    def test_check_subscription_false_when_api_fails(self) -> None:
        self.bot_module.NEWS_CHANNEL_ID = "@portal_news_channel"
        fake = _FakeBot(fail=True)
        ok = asyncio.run(self.bot_module.check_subscription(1001, fake))
        self.assertFalse(ok)

    def test_public_bot_menu_exposes_cabinet_and_support_commands(self) -> None:
        fake = _FakeBot()

        asyncio.run(self.bot_module._configure_public_bot_menu(fake))

        commands = [getattr(command, "command", "") for command in fake.command_sets[-1]]
        self.assertEqual(commands, ["start", "cabinet", "support", "promo", "redeem"])
        self.assertTrue(fake.menu_buttons)
        menu_button = fake.menu_buttons[-1]
        self.assertEqual(getattr(menu_button, "text", ""), "Кабинет")
        self.assertEqual(getattr(getattr(menu_button, "web_app", None), "url", ""), self.bot_module.WEBAPP_URL)

    def test_support_command_opens_support_menu(self) -> None:
        handler = getattr(self.bot_module, "support_command", None)
        self.assertTrue(callable(handler), "missing /support command handler")
        message = _FakeMessage(1001, text="/support")

        asyncio.run(handler(message))

        self.assertEqual(self.bot_module._user_context_mode.get(1001), "support")
        self.assertTrue(message.answers)
        text, kwargs = message.answers[-1]
        self.assertIn("POKROV", text)
        buttons = [
            button
            for row in kwargs["reply_markup"].inline_keyboard
            for button in row
        ]
        callback_data = {getattr(button, "callback_data", "") for button in buttons}
        urls = {getattr(button, "url", "") or "" for button in buttons}
        self.assertIn("faq_connect", callback_data)
        self.assertIn("support_diagnose", callback_data)
        self.assertTrue(any("pokrov_supportbot?start=ticket_new" in url for url in urls))

    def test_cabinet_command_opens_webapp_cabinet(self) -> None:
        handler = getattr(self.bot_module, "cabinet_command", None)
        self.assertTrue(callable(handler), "missing /cabinet command handler")
        message = _FakeMessage(1001, text="/cabinet")

        asyncio.run(handler(message))

        self.assertTrue(message.answers)
        text, kwargs = message.answers[-1]
        self.assertIn("POKROV", text)
        buttons = [
            button
            for row in kwargs["reply_markup"].inline_keyboard
            for button in row
        ]
        web_app_urls = [
            getattr(getattr(button, "web_app", None), "url", "")
            for button in buttons
        ]
        callback_data = {getattr(button, "callback_data", "") for button in buttons}
        self.assertIn(self.bot_module.WEBAPP_URL, web_app_urls)
        self.assertIn(self.bot_module._webapp_route_url("redeem"), web_app_urls)
        self.assertIn(self.bot_module._webapp_route_url("subscription"), web_app_urls)
        self.assertIn(self.bot_module._webapp_route_url("settings"), web_app_urls)
        self.assertIn(self.bot_module._webapp_route_url("downloads"), web_app_urls)
        self.assertIn("support", callback_data)
        cabinet_button = next(button for button in buttons if getattr(button, "web_app", None) is not None)
        support_button = next(button for button in buttons if getattr(button, "callback_data", "") == "support")
        back_button = next(button for button in buttons if getattr(button, "callback_data", "") == "back")
        self.assertEqual(getattr(cabinet_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(support_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_instruction_device_menu_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        callback = _FakeCallback(1001, data="instruction")

        asyncio.run(self.bot_module.show_instruction(callback))

        kwargs = callback.message.edit_kwargs[-1]
        buttons = [
            button
            for row in kwargs["reply_markup"].inline_keyboard
            for button in row
        ]
        android_button = next(button for button in buttons if getattr(button, "callback_data", "") == "instr_android")
        apple_button = next(button for button in buttons if getattr(button, "callback_data", "") == "instr_ios")
        cabinet_button = next(button for button in buttons if getattr(button, "web_app", None) is not None)
        back_button = next(button for button in buttons if getattr(button, "callback_data", "") == "back")
        callback_data = {getattr(button, "callback_data", "") for button in buttons}
        self.assertEqual(getattr(android_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(android_button, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertIn("статус", str(getattr(apple_button, "text", "")).lower())
        self.assertNotIn("instr_mac", callback_data)
        self.assertEqual(getattr(cabinet_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(back_button, "icon_custom_emoji_id", None), "5368324170671202299")

    def test_instruction_platform_menu_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        self.bot_module.WEBAPP_URL = "https://app.pokrov.space/"
        callback = _FakeCallback(1001, data="instr_android")

        asyncio.run(self.bot_module.instruction_platform(callback))

        buttons = [
            button
            for row in callback.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        ]
        download_button = next(button for button in buttons if getattr(button, "url", None))
        show_key_button = next(button for button in buttons if getattr(button, "callback_data", "") == "show_key")
        devices_button = next(button for button in buttons if getattr(button, "callback_data", "") == "instruction")

        self.assertEqual(getattr(download_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(download_button, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(download_button, "url", ""), "https://app.pokrov.space/downloads/?platform=android")
        self.assertEqual(getattr(show_key_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(devices_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_apple_instruction_is_status_only_not_install_flow(self) -> None:
        callback = _FakeCallback(1001, data="instr_ios")

        asyncio.run(self.bot_module.instruction_platform(callback))

        text = callback.message.edits[-1]
        buttons = [
            button
            for row in callback.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        ]
        callback_data = {getattr(button, "callback_data", "") for button in buttons}
        url_button = next(button for button in buttons if getattr(button, "url", None))

        self.assertIn("статус подготовки", text)
        self.assertIn("не входят", text)
        self.assertNotIn("Установите подходящее приложение", text)
        self.assertNotIn("show_key", callback_data)
        self.assertIn("статус", str(getattr(url_button, "text", "")).lower())

    def test_support_connect_faq_routes_public_downloads_through_cabinet(self) -> None:
        self.bot_module.WEBAPP_URL = "https://app.pokrov.space/"
        connect = self.bot_module._support_faq_answer("connect")

        self.assertIn("https://app.pokrov.space/downloads/?platform=android", connect)
        self.assertIn("https://app.pokrov.space/downloads/?platform=windows", connect)
        self.assertIn("Apple пока в подготовке", connect)
        self.assertNotIn("iPhone / iPad:", connect)
        self.assertNotIn("APP_ANDROID_APK_URL", connect)
        self.assertNotIn("github.com", connect)

    def test_support_renew_faq_is_honest_while_lavatop_checkout_is_closed(self) -> None:
        renew = self.bot_module._support_faq_answer("renew")

        self.assertIn("Оплата временно недоступна", renew)
        self.assertIn("Lava.top", renew)
        self.assertIn("Проверить статус продления", renew)
        self.assertNotIn("Откройте оплату в ₽", renew)
        self.assertNotIn("После успешной оплаты доступ обновится автоматически", renew)

    def test_webapp_route_url_keeps_legacy_base_path_and_drops_query(self) -> None:
        self.bot_module.WEBAPP_URL = "https://kiwunaka.space:8444/webapp/?v=20260320"

        self.assertEqual(
            self.bot_module._webapp_route_url("redeem"),
            "https://kiwunaka.space:8444/webapp/redeem/",
        )
        self.assertEqual(
            self.bot_module._webapp_downloads_url("windows"),
            "https://kiwunaka.space:8444/webapp/downloads/?platform=windows",
        )

    def test_start_and_terms_keyboards_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        terms_keyboard = self.bot_module._tos_offer_keyboard(back_callback="menu_more")
        terms_buttons = [button for row in terms_keyboard.inline_keyboard for button in row]
        read_terms = next(button for button in terms_buttons if getattr(button, "url", None))
        accept_terms = next(button for button in terms_buttons if getattr(button, "callback_data", "") == "accept_tos")
        terms_back = next(button for button in terms_buttons if getattr(button, "callback_data", "") == "menu_more")

        self.assertEqual(getattr(read_terms, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(accept_terms, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(accept_terms, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(terms_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        start_keyboard = self.bot_module._start_mode_keyboard()
        start_buttons = [button for row in start_keyboard.inline_keyboard for button in row]
        simple = next(button for button in start_buttons if getattr(button, "callback_data", "") == "mode_simple")
        pro = next(button for button in start_buttons if getattr(button, "callback_data", "") == "mode_pro")

        self.assertEqual(getattr(simple, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(simple, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(pro, "style", None), self.bot_module.BTN_STYLE_PRIMARY)

    def test_sync_telegram_identity_updates_primary_and_linked_usernames(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="old_name")
        session = self.bot_module.Session()
        try:
            linked = self.bot_module.User(
                tg_id=9000000000100,
                username="app_000100",
                uuid=str(uuid.uuid4()),
                email="APP_9000000000100",
                sub_type="FREE",
                current_plan_code="trial",
                is_active=True,
                linked_telegram_id=1001,
                linked_telegram_username="old_linked",
                sub_token="linked_token",
            )
            session.add(linked)
            session.commit()
        finally:
            session.close()

        changed = self.bot_module.sync_telegram_identity(1001, "fresh_name")
        self.assertTrue(changed)

        session = self.bot_module.Session()
        try:
            primary = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            linked = session.query(self.bot_module.User).filter_by(tg_id=9000000000100).first()
            self.assertEqual(primary.username, "fresh_name")
            self.assertEqual(linked.linked_telegram_username, "fresh_name")
        finally:
            session.close()

    def test_sync_telegram_identity_clears_stale_usernames(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="old_name")
        session = self.bot_module.Session()
        try:
            linked = self.bot_module.User(
                tg_id=9000000000101,
                username="app_000101",
                uuid=str(uuid.uuid4()),
                email="APP_9000000000101",
                sub_type="FREE",
                current_plan_code="trial",
                is_active=True,
                linked_telegram_id=1001,
                linked_telegram_username="old_linked",
                sub_token="linked_token_2",
            )
            session.add(linked)
            session.commit()
        finally:
            session.close()

        changed = self.bot_module.sync_telegram_identity(1001, None)
        self.assertTrue(changed)

        session = self.bot_module.Session()
        try:
            primary = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            linked = session.query(self.bot_module.User).filter_by(tg_id=9000000000101).first()
            self.assertIsNone(primary.username)
            self.assertIsNone(linked.linked_telegram_username)
        finally:
            session.close()

    def test_opening_bonus_activation_is_one_time(self) -> None:
        self.bot_module.OPENING_PREMIUM_ENABLED = True
        self.bot_module.OPENING_PREMIUM_DAYS = 14
        self.bot_module.OPENING_PREMIUM_CAMPAIGN_KEY = "opening_premium_14d"
        self.bot_module.set_tos_accepted(1001)

        class _Msg:
            def __init__(self, bot):
                self.bot = bot

        calls: list[int] = []

        async def _fake_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            calls.append(int(tg_id))
            return None

        old_create_subscription = self.bot_module.create_subscription
        self.bot_module.create_subscription = _fake_create_subscription
        try:
            msg = _Msg(bot=_FakeBot(status="member"))
            ok1, reason1 = asyncio.run(
                self.bot_module._try_activate_opening_premium_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                )
            )
            ok2, reason2 = asyncio.run(
                self.bot_module._try_activate_opening_premium_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                )
            )
        finally:
            self.bot_module.create_subscription = old_create_subscription

        self.assertTrue(ok1)
        self.assertEqual(reason1, "activated")
        self.assertFalse(ok2)
        self.assertEqual(reason2, "already_claimed")
        self.assertEqual(calls, [1001])

        s = self.bot_module.Session()
        try:
            user = s.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            self.assertIsNone(getattr(user, "channel_bonus_claimed_at", None))
            self.assertFalse(bool(getattr(user, "channel_bonus_active", False)))
            self.assertIsNone(getattr(user, "channel_bonus_revoked_at", None))
        finally:
            s.close()

    def test_opening_bonus_does_not_burn_campaign_claim_on_subscription_failure(self) -> None:
        self.bot_module.OPENING_PREMIUM_ENABLED = True
        self.bot_module.OPENING_PREMIUM_DAYS = 14
        self.bot_module.OPENING_PREMIUM_CAMPAIGN_KEY = "opening_premium_14d"
        self.bot_module.set_tos_accepted(1001)

        class _Msg:
            def __init__(self, bot):
                self.bot = bot

        async def _failing_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            raise RuntimeError("subscription failed")

        async def _ok_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            return None

        old_create_subscription = self.bot_module.create_subscription
        try:
            msg = _Msg(bot=_FakeBot(status="member"))
            self.bot_module.create_subscription = _failing_create_subscription
            with self.assertRaises(RuntimeError):
                asyncio.run(
                    self.bot_module._try_activate_opening_premium_bonus(
                        message=msg,
                        bot=msg.bot,
                        tg_id=1001,
                        username="alice",
                    )
                )

            self.assertFalse(
                self.bot_module._campaign_claimed(
                    tg_id=1001,
                    campaign_key=self.bot_module.OPENING_PREMIUM_CAMPAIGN_KEY,
                )
            )

            self.bot_module.create_subscription = _ok_create_subscription
            ok, reason = asyncio.run(
                self.bot_module._try_activate_opening_premium_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                )
            )
        finally:
            self.bot_module.create_subscription = old_create_subscription

        self.assertTrue(ok)
        self.assertEqual(reason, "activated")

    def test_parse_start_deeplink_context_supports_promo_and_campaign(self) -> None:
        promo, campaign = self.bot_module._parse_start_deeplink_context("promo_newyear")
        self.assertEqual(promo, "NEWYEAR")
        self.assertEqual(campaign, "")

        promo2, campaign2 = self.bot_module._parse_start_deeplink_context("campaign_launch__promo_welcome14")
        self.assertEqual(promo2, "WELCOME14")
        self.assertEqual(campaign2, "launch")

    def test_parse_start_deeplink_context_sanitizes_payload(self) -> None:
        promo, campaign = self.bot_module._parse_start_deeplink_context("promo_new-year!!!")
        self.assertEqual(promo, "NEW-YEAR")
        self.assertEqual(campaign, "")

        promo2, campaign2 = self.bot_module._parse_start_deeplink_context("campaign_bad key!!__promo_20%OFF")
        self.assertEqual(promo2, "20OFF")
        self.assertEqual(campaign2, "badkey")

    def test_parse_friend_gift_ref_code(self) -> None:
        code = self.bot_module._parse_friend_gift_ref_code("gift3_SWAZ7K3F")
        self.assertEqual(code, "SWAZ7K3F")

        bad = self.bot_module._parse_friend_gift_ref_code("gift3_!!!")
        self.assertEqual(bad, "")

    def test_main_connect_cta_variant_is_stable_per_user(self) -> None:
        label1 = self.bot_module._main_connect_cta_text(1001)
        label2 = self.bot_module._main_connect_cta_text(1001)
        self.assertEqual(label1, label2)
        self.assertIn(label1, set(self.bot_module.MAIN_CONNECT_CTA_LABELS.values()))

    def test_friend_gift_activation_is_one_time(self) -> None:
        self.bot_module.FRIEND_GIFT_ENABLED = True
        self.bot_module.FRIEND_GIFT_DAYS = 3
        self.bot_module.FRIEND_GIFT_CAMPAIGN_KEY = "friend_gift_3d"
        self.bot_module.set_tos_accepted(1001)

        self.bot_module.ensure_pending_user(2002, username="referrer")
        ref_code = self.bot_module.get_or_create_referral_code(2002)
        self.assertTrue(ref_code)

        class _Msg:
            def __init__(self, bot):
                self.bot = bot

        calls: list[int] = []

        async def _fake_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            calls.append(int(tg_id))
            return None

        old_create_subscription = self.bot_module.create_subscription
        self.bot_module.create_subscription = _fake_create_subscription
        try:
            msg = _Msg(bot=_FakeBot(status="member"))
            ok1, reason1 = asyncio.run(
                self.bot_module._try_activate_friend_gift_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                    referral_code=ref_code,
                )
            )
            ok2, reason2 = asyncio.run(
                self.bot_module._try_activate_friend_gift_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                    referral_code=ref_code,
                )
            )
        finally:
            self.bot_module.create_subscription = old_create_subscription

        self.assertTrue(ok1)
        self.assertEqual(reason1, "activated")
        self.assertFalse(ok2)
        self.assertEqual(reason2, "already_claimed")
        self.assertEqual(calls, [1001])

    def test_friend_gift_does_not_burn_campaign_claim_on_subscription_failure(self) -> None:
        self.bot_module.FRIEND_GIFT_ENABLED = True
        self.bot_module.FRIEND_GIFT_DAYS = 3
        self.bot_module.FRIEND_GIFT_CAMPAIGN_KEY = "friend_gift_3d"
        self.bot_module.set_tos_accepted(1001)

        self.bot_module.ensure_pending_user(2002, username="referrer")
        ref_code = self.bot_module.get_or_create_referral_code(2002)
        self.assertTrue(ref_code)

        class _Msg:
            def __init__(self, bot):
                self.bot = bot

        async def _failing_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            raise RuntimeError("subscription failed")

        async def _ok_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            return None

        old_create_subscription = self.bot_module.create_subscription
        try:
            msg = _Msg(bot=_FakeBot(status="member"))
            self.bot_module.create_subscription = _failing_create_subscription
            with self.assertRaises(RuntimeError):
                asyncio.run(
                    self.bot_module._try_activate_friend_gift_bonus(
                        message=msg,
                        bot=msg.bot,
                        tg_id=1001,
                        username="alice",
                        referral_code=ref_code,
                    )
                )

            self.assertFalse(
                self.bot_module._campaign_claimed(
                    tg_id=1001,
                    campaign_key=self.bot_module.FRIEND_GIFT_CAMPAIGN_KEY,
                )
            )

            self.bot_module.create_subscription = _ok_create_subscription
            ok, reason = asyncio.run(
                self.bot_module._try_activate_friend_gift_bonus(
                    message=msg,
                    bot=msg.bot,
                    tg_id=1001,
                    username="alice",
                    referral_code=ref_code,
                )
            )
        finally:
            self.bot_module.create_subscription = old_create_subscription

        self.assertTrue(ok)
        self.assertEqual(reason, "activated")

    def test_activate_promo_code_tracks_success_and_denial(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        session = self.bot_module.Session()
        try:
            session.add(self.bot_module.PromoCode(code="WELCOME14", promo_type="days", value=14, uses_left=2))
            session.commit()
        finally:
            session.close()

        tracked: list[dict] = []

        def _fake_track_event(**kwargs):
            tracked.append(kwargs)
            return 1

        old_track_event = self.bot_module.track_event
        try:
            self.bot_module.track_event = _fake_track_event
            ok, _msg = self.bot_module.activate_promo_code_for_user(1001, "WELCOME14")
            self.assertTrue(ok)
            denied, _msg2 = self.bot_module.activate_promo_code_for_user(1001, "WELCOME14")
            self.assertFalse(denied)
        finally:
            self.bot_module.track_event = old_track_event

        self.assertEqual([item["event_name"] for item in tracked], ["promo_redeemed", "promo_redeem_denied"])
        self.assertEqual(str(tracked[0]["meta"].get("code") or ""), "WELCOME14")
        self.assertEqual(str(tracked[1]["meta"].get("reason") or ""), "already_redeemed")

    def test_redeem_gift_card_tracks_success_and_denial(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        gift_code = self.bot_module.create_gift_card(2002, "standard")
        self.assertTrue(gift_code)

        tracked: list[dict] = []

        def _fake_track_event(**kwargs):
            tracked.append(kwargs)
            return 1

        old_track_event = self.bot_module.track_event
        try:
            self.bot_module.track_event = _fake_track_event
            ok, _msg = asyncio.run(self.bot_module.redeem_gift_card(gift_code, 1001, _FakeBot(status="member")))
            self.assertTrue(ok)
            denied, _msg2 = asyncio.run(self.bot_module.redeem_gift_card(gift_code, 1001, _FakeBot(status="member")))
            self.assertFalse(denied)
        finally:
            self.bot_module.track_event = old_track_event

        self.assertEqual([item["event_name"] for item in tracked], ["gift_redeemed", "gift_redeem_denied"])
        self.assertEqual(str(tracked[0]["meta"].get("card_type") or "").lower(), "standard")
        self.assertEqual(str(tracked[1]["meta"].get("reason") or ""), "already_redeemed")

    def test_redeem_gift_card_normalizes_human_key_input(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        gift_code = self.bot_module.create_gift_card(2002, "standard")
        self.assertTrue(gift_code)
        human_code = str(gift_code).replace("-", "\u2011", 1).replace("-", "\u2212", 1)

        ok, _msg = asyncio.run(self.bot_module.redeem_gift_card(human_code.lower(), 1001, _FakeBot(status="member")))

        self.assertTrue(ok)

    def test_redeem_gift_card_accepts_paid_access_key_plan_codes(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        from models import GiftCard, PlanCatalog

        session = self.bot_module.Session()
        try:
            session.add(
                PlanCatalog(
                    code="bot_plan_key",
                    label="Bot plan key",
                    amount_rub=249,
                    amount_stars=249,
                    days=30,
                    device_limit=5,
                    node_policy="managed_premium",
                    is_active=True,
                )
            )
            session.add(GiftCard(code="POKROV-PLAN-2026", card_type="bot_plan_key", created_by=0))
            session.commit()
        finally:
            session.close()

        ok, _msg = asyncio.run(self.bot_module.redeem_gift_card("pokrov plan 2026", 1001, _FakeBot(status="member")))

        self.assertTrue(ok)
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            self.assertEqual(str(user.sub_type or "").upper(), "PAID")
            self.assertEqual(str(user.current_plan_code or ""), "bot_plan_key")
            self.assertTrue(bool(user.first_purchase_done))
            card = session.query(GiftCard).filter_by(code="POKROV-PLAN-2026").first()
            self.assertIsNotNone(card)
            self.assertEqual(int(card.redeemed_by or 0), 1001)
        finally:
            session.close()

    def test_admin_direct_trial_gift_uses_canonical_five_days(self) -> None:
        import inspect

        source = inspect.getsource(self.bot_module.admin_gift)

        self.assertIn("`/gift [tg_id] trial` — Пробный (5 дней)", source)
        self.assertIn('"trial": {"days": 5', source)
        self.assertNotIn("Пробный (7 дней)", source)
        self.assertNotIn('"trial": {"days": 7', source)

    def test_gift_card_menu_hides_stars_purchase_when_disabled(self) -> None:
        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = False
        callback = _FakeCallback(1001, data="gift_cards")

        asyncio.run(self.bot_module.show_gift_cards(callback))

        self.assertTrue(callback.message.edits)
        self.assertIn("Lava.top", callback.message.edits[-1])
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        buttons = [button for row in reply_markup.inline_keyboard for button in row]
        labels = [str(button.text or "") for button in buttons]
        callback_data = [str(getattr(button, "callback_data", "") or "") for button in buttons]
        self.assertFalse(any("⭐" in text or "Stars" in text for text in labels))
        self.assertFalse(any(value.startswith("buy_giftcard_") for value in callback_data))
        self.assertIn("gift_redeem_prompt", callback_data)

    def test_gift_card_purchase_callback_does_not_invoice_when_stars_disabled(self) -> None:
        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = False
        callback = _FakeCallback(1001, data="buy_giftcard_standard")
        bot = _FakeBot(status="member")

        asyncio.run(self.bot_module.buy_gift_card(callback, bot))

        self.assertEqual(bot.invoices, [])
        self.assertTrue(callback.message.edits)
        self.assertEqual(callback.answers[-1], ("Оплата подарков пока закрыта", True))

    def test_stars_tariff_callback_and_precheckout_are_blocked_by_default(self) -> None:
        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = False
        callback = _FakeCallback(1001, data="pay_stars_1_month")
        bot = _FakeBot(status="member")

        asyncio.run(self.bot_module.process_buy_stars(callback, bot))

        self.assertEqual(bot.invoices, [])
        self.assertTrue(callback.message.edits)
        self.assertEqual(callback.answers[-1], ("Оплата через Stars закрыта", True))

        pre_checkout = types.SimpleNamespace(id="precheckout-1")
        asyncio.run(self.bot_module.pre_checkout_handler(pre_checkout, bot))
        self.assertEqual(bot.pre_checkout_answers[-1]["id"], "precheckout-1")
        self.assertFalse(bot.pre_checkout_answers[-1]["ok"])

    def test_status_copy_uses_lavatop_when_stars_disabled(self) -> None:
        text = self.bot_module.TEXTS["status"].format(
            tg_id=1001,
            expiry="01.06.2026",
            stars=249,
            payment_line="💳 Оплата: `Lava.top-only beta`",
            status_icon="🟢",
            status_text="АКТИВЕН",
            plan_label="30 дней",
        )

        self.assertIn("Lava.top-only beta", text)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐ Оплачено", text)

    def test_public_achievement_copy_hides_stars_when_disabled(self) -> None:
        desc = str(self.bot_module.ACHIEVEMENTS["big_spender"]["desc"])

        self.assertNotIn("Stars", desc)
        self.assertNotIn("⭐", desc)

    def test_more_menus_hide_stars_purchase_buttons_when_disabled(self) -> None:
        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = False

        for handler_name, callback_data in (("show_settings", "settings"), ("menu_more", "menu_more")):
            callback = _FakeCallback(1001, data=callback_data)
            asyncio.run(getattr(self.bot_module, handler_name)(callback))
            reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
            buttons = [button for row in reply_markup.inline_keyboard for button in row]
            labels = [str(button.text or "") for button in buttons]
            callbacks = [str(getattr(button, "callback_data", "") or "") for button in buttons]

            self.assertNotIn("buy_family_slot", callbacks)
            self.assertFalse(any("Family +1" in label for label in labels))

    def test_more_menus_use_modern_button_fields(self) -> None:
        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = False
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        settings = _FakeCallback(1001, data="settings")
        asyncio.run(self.bot_module.show_settings(settings))
        settings_buttons = [
            button for row in settings.message.edit_kwargs[-1]["reply_markup"].inline_keyboard for button in row
        ]
        show_key = next(button for button in settings_buttons if getattr(button, "callback_data", "") == "show_key")
        mode_simple = next(button for button in settings_buttons if getattr(button, "callback_data", "") == "mode_simple")
        settings_back = next(button for button in settings_buttons if getattr(button, "callback_data", "") == "back")

        self.assertEqual(getattr(show_key, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(show_key, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(mode_simple, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(settings_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        more = _FakeCallback(1001, data="menu_more")
        asyncio.run(self.bot_module.menu_more(more))
        more_buttons = [button for row in more.message.edit_kwargs[-1]["reply_markup"].inline_keyboard for button in row]
        gift_cards = next(button for button in more_buttons if getattr(button, "callback_data", "") == "gift_cards")
        redeem = next(button for button in more_buttons if getattr(button, "callback_data", "") == "gift_redeem_prompt")
        promo = next(button for button in more_buttons if getattr(button, "callback_data", "") == "promo_activate_prompt")
        more_back = next(button for button in more_buttons if getattr(button, "callback_data", "") == "back")

        self.assertEqual(getattr(gift_cards, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(redeem, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(redeem, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(promo, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(more_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_unpaid_bonuses_menu_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        callback = _FakeCallback(1001, data="menu_bonuses")

        asyncio.run(self.bot_module.menu_bonuses(callback))

        buttons = [button for row in callback.message.edit_kwargs[-1]["reply_markup"].inline_keyboard for button in row]
        channel_bonus = next(button for button in buttons if getattr(button, "callback_data", "") == "bonus_offer_main")
        charge = next(button for button in buttons if getattr(button, "callback_data", "") == "charge")
        back = next(button for button in buttons if getattr(button, "callback_data", "") == "back")

        self.assertEqual(getattr(channel_bonus, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(channel_bonus, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(charge, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_paid_bonus_and_reward_menus_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        self._make_paid_user(1001)

        bonuses = _FakeCallback(1001, data="menu_bonuses")
        asyncio.run(self.bot_module.menu_bonuses(bonuses))
        bonus_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in bonuses.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        }

        self.assertEqual(getattr(bonus_buttons["referral"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(bonus_buttons["achievements"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(bonus_buttons["wheel"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(bonus_buttons["streak"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(bonus_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(bonus_buttons["wheel"], "icon_custom_emoji_id", None), "5373141891321699086")

        with patch.object(self.bot_module, "can_spin_wheel", return_value=(True, 0)):
            with patch.object(self.bot_module, "wheel_prizes_for_user", return_value=[(3, 10), (30, 1)]):
                wheel = _FakeCallback(1001, data="wheel")
                asyncio.run(self.bot_module.show_wheel(wheel))
        wheel_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in wheel.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(wheel_buttons["wheel_spin"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(wheel_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        achievements = _FakeCallback(1001, data="achievements")
        achievements.bot = _FakeBot(status="member")
        with patch.object(self.bot_module, "check_achievements", new=lambda *_args, **_kwargs: asyncio.sleep(0)):
            asyncio.run(self.bot_module.show_achievements(achievements))
        achievements_back = achievements.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(achievements_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_review_prompt_keyboards_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        self._make_paid_user(1001)

        message = _FakeMessage(1001, text="/review")
        asyncio.run(self.bot_module.review_command(message))
        review_buttons = [
            button
            for row in message.answers[-1][1]["reply_markup"].inline_keyboard
            for button in row
        ]
        rating_button = next(button for button in review_buttons if getattr(button, "callback_data", "") == "rate_5")
        cancel_button = next(button for button in review_buttons if getattr(button, "callback_data", "") == "back")
        self.assertEqual(getattr(rating_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(cancel_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

        rate = _FakeCallback(1001, data="rate_5")
        asyncio.run(self.bot_module.rate_review(rate))
        rate_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in rate.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(rate_buttons["review_skip_text"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(rate_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_gift_promo_and_network_keyboards_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        promo = _FakeCallback(1001, data="promo_help")
        asyncio.run(self.bot_module.promo_help(promo))
        promo_back = promo.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(promo_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        gift = _FakeCallback(1001, data="gift_redeem_prompt")
        asyncio.run(self.bot_module.gift_redeem_prompt(gift))
        gift_back = gift.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(gift_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        prompt = _FakeCallback(1001, data="promo_activate_prompt")
        asyncio.run(self.bot_module.promo_activate_prompt(prompt))
        prompt_back = prompt.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(prompt_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        self.bot_module.BOT_STARS_PAYMENTS_ENABLED = True
        cards = _FakeCallback(1001, data="gift_cards")
        asyncio.run(self.bot_module.show_gift_cards(cards))
        gift_card_buttons = [
            button
            for row in cards.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        ]
        buy_button = next(button for button in gift_card_buttons if str(getattr(button, "callback_data", "") or "").startswith("buy_giftcard_"))
        cards_back = next(button for button in gift_card_buttons if getattr(button, "callback_data", "") == "back")
        self.assertEqual(getattr(buy_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(cards_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        network = _FakeCallback(1001, data="network_status")
        with patch.object(self.bot_module, "_bot_enabled_nodes", return_value=[]):
            asyncio.run(self.bot_module.network_status(network))
        network_back = network.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(network_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_bot_checkout_url_includes_tracking_context(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
        url = self.bot_module._bot_checkout_url(
            1001,
            plan_code="start_99",
            promo_code="WELCOME14",
            campaign_key="launch_week_1",
        )
        self.assertIn("source=bot", url)
        self.assertIn("tg_id=1001", url)
        self.assertIn("plan=start_99", url)
        self.assertIn("promo=WELCOME14", url)
        self.assertIn("campaign=launch_week_1", url)
        self.assertIn("checkout_ticket=", url)

    def test_tariff_payment_choice_text_separates_tariff_and_payment_method(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            with self._checkout_gate_green():
                text = self.bot_module._build_tariff_payment_choice_text(tariff_key="1_month", tg_id=1001)
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog
        self.assertIn("Цена в ₽: *249 ₽*", text)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐", text)
        self.assertIn("Откроем оплату в рублях", text)

    def test_tariff_payment_choice_text_is_status_first_when_rub_checkout_closed(self) -> None:
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: []
            text = self.bot_module._build_tariff_payment_choice_text(tariff_key="1_month", tg_id=1001)
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertIn("Оплата временно недоступна", text)
        self.assertIn("Lava.top", text)
        self.assertIn("статус", text.lower())
        self.assertNotIn("Откроем оплату", text)
        self.assertNotIn("выберите удобную кассу", text.lower())

    def test_tariff_payment_choice_keyboard_links_checkout_status_when_rub_checkout_closed(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://pay.pokrov.space/checkout/?from=bot"
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: []
            keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="1_month")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog

        flat_buttons = [button for row in keyboard.inline_keyboard for button in row]
        callback_data = [str(getattr(button, "callback_data", "") or "") for button in flat_buttons]
        urls = [str(getattr(button, "url", "") or "") for button in flat_buttons]
        self.assertFalse(any(value.startswith("pay_rub") for value in callback_data))
        self.assertTrue(any("pay.pokrov.space/checkout/" in value for value in urls))
        self.assertTrue(any("plan=1_month" in value for value in urls))
        self.assertIn("support", callback_data)

    def test_tariff_payment_choice_keyboard_hides_lavatop_until_checkout_gate_is_green(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://pay.pokrov.space/checkout/?from=bot"
        missing_evidence = Path(self._tmp.name) / "missing-paid-checkout-evidence.json"
        with patch.dict(
            os.environ,
            {
                "RUB_CHECKOUT_ENABLED": "true",
                "PUBLIC_API_BASE_URL": "https://api.pokrov.space",
                "PAY_CHECKOUT_URL": "https://pay.pokrov.space/checkout/",
                "PAY_SUCCESS_URL": "https://api.pokrov.space/pay/success",
                "PAY_FAIL_URL": "https://api.pokrov.space/pay/fail",
                "RUB_PAYMENT_PROVIDER_ORDER": "lavatop",
                "RUB_PAYMENT_PROVIDER_ENABLED": "lavatop",
                "LAVATOP_API_KEY": "lava_api_test",
                "LAVATOP_OFFER_ID": "offer_test",
                "LAVATOP_WEBHOOK_API_KEY": "lava_webhook_test",
                "EMAIL_AUTH_PUBLIC_ENABLED": "false",
                "EMAIL_DELIVERY_WEBHOOK_URL": "",
                "EMAIL_AUTH_WEBHOOK_URL": "",
                "EMAIL_DELIVERY_WEBHOOK_SECRET": "",
                "EMAIL_AUTH_DEBUG_ECHO": "false",
                "PAID_CHECKOUT_LAUNCH_EVIDENCE_REQUIRED": "true",
                "PAID_CHECKOUT_LAUNCH_EVIDENCE_PATH": missing_evidence.as_posix(),
            },
            clear=False,
        ):
            email_delivery_service = importlib.import_module("email_delivery_service")
            importlib.reload(email_delivery_service)
            rows = self.bot_module._tariff_payment_choice_keyboard_specs(tg_id=1001, tariff_key="1_month")

        flat_buttons = [button for row in rows for button in row]
        callback_data = [str(button.get("callback_data") or "") for button in flat_buttons]
        urls = [str(button.get("url") or "") for button in flat_buttons]
        self.assertFalse(any(value.startswith("pay_rub:") for value in callback_data))
        self.assertTrue(any("pay.pokrov.space/checkout/" in value for value in urls))
        self.assertTrue(any("plan=1_month" in value for value in urls))
        self.assertIn("support", callback_data)

    def test_tariff_payment_choice_keyboard_keeps_plan_in_checkout_url(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
        self.bot_module.checkout_context_by_user[1001] = {
            "promo_code": "WELCOME14",
            "campaign_key": "launch_week_1",
        }
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
                {"code": "pally", "label": "Paypalich", "supports_bot": True},
            ]
            with self._checkout_gate_green():
                keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="3_months")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:lavatop:3_months")
        callback_data = [str(button.callback_data or "") for row in keyboard.inline_keyboard for button in row]
        self.assertFalse(any("cardlink" in value or "pally" in value for value in callback_data))
        flat_rows = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertIn("📚 Посмотреть долгие тарифы", flat_rows)
        self.assertIn("◀️ К тарифам", flat_rows)

    def test_bot_rub_order_payload_uses_ticket_without_email(self) -> None:
        self.bot_module.checkout_context_by_user[1001] = {
            "promo_code": "WELCOME14",
            "campaign_key": "launch_week_1",
        }

        payload, ticket = self.bot_module._bot_rub_order_payload(
            provider="lavatop",
            tg_id=1001,
            tariff_key="start_99",
        )

        self.assertTrue(ticket)
        self.assertEqual(payload["provider"], "lavatop")
        self.assertEqual(payload["plan_code"], "start_99")
        self.assertEqual(payload["checkout_ticket"], ticket)
        self.assertEqual(payload["currency"], "RUB")
        self.assertNotIn("buyer_email", payload)

    def test_bot_rub_order_payload_defaults_to_lavatop(self) -> None:
        payload, _ticket = self.bot_module._bot_rub_order_payload(
            provider="",
            tg_id=1001,
            tariff_key="start_99",
        )

        self.assertEqual(payload["provider"], "lavatop")

    def test_direct_rub_payment_keyboard_keeps_site_fallback(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
        self.bot_module.checkout_context_by_user[1001] = {
            "promo_code": "WELCOME14",
            "campaign_key": "launch_week_1",
        }
        keyboard = self.bot_module._build_direct_rub_payment_keyboard(
            tg_id=1001,
            tariff_key="3_months",
            payment_url="https://app.lava.top/invoice/test",
            provider_label="Lava.top",
        )
        self.assertEqual(keyboard.inline_keyboard[0][0].url, "https://app.lava.top/invoice/test")
        self.assertIn("plan=3_months", keyboard.inline_keyboard[1][0].url)
        self.assertIn("promo=WELCOME14", keyboard.inline_keyboard[1][0].url)
        self.assertIn("campaign=launch_week_1", keyboard.inline_keyboard[1][0].url)
        flat_text = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertFalse(any("Stars" in text or "⭐" in text for text in flat_text))

    def test_process_buy_rub_opens_direct_payment_link(self) -> None:
        callback = _FakeCallback(1001, data="pay_rub:lavatop:1_month")

        old_catalog = self.bot_module.enabled_provider_catalog

        async def _fake_create_payment_link(*, provider, tg_id, tariff_key):
            self.assertEqual(str(provider), "lavatop")
            self.assertEqual(int(tg_id), 1001)
            self.assertEqual(str(tariff_key), "1_month")
            return {
                "order_id": "lavatop_bot_1001_test",
                "payment_url": "https://app.lava.top/invoice/test",
            }

        old_create = self.bot_module._create_rub_payment_link_for_bot
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            self.bot_module._create_rub_payment_link_for_bot = _fake_create_payment_link
            with self._checkout_gate_green():
                asyncio.run(self.bot_module.process_buy_rub(callback, _FakeBot(status="member")))
        finally:
            self.bot_module._create_rub_payment_link_for_bot = old_create
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertTrue(callback.message.edits)
        self.assertIn("Следующий шаг: откройте оплату", callback.message.edits[-1])
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        self.assertEqual(reply_markup.inline_keyboard[0][0].url, "https://app.lava.top/invoice/test")
        self.assertEqual(callback.answers[-1], ("Ссылка на оплату готова", False))

    def test_process_buy_rub_rejects_non_lava_provider_even_if_stale_env_enables_it(self) -> None:
        callback = _FakeCallback(1001, data="pay_rub:cardlink:1_month")

        async def _fake_create_payment_link(**_kwargs):
            raise AssertionError("non-Lava provider must not create a bot order")

        old_catalog = self.bot_module.enabled_provider_catalog
        old_create = self.bot_module._create_rub_payment_link_for_bot
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            self.bot_module._create_rub_payment_link_for_bot = _fake_create_payment_link
            with self._checkout_gate_green():
                asyncio.run(self.bot_module.process_buy_rub(callback, _FakeBot(status="member")))
        finally:
            self.bot_module._create_rub_payment_link_for_bot = old_create
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertEqual(callback.message.edits, [])
        self.assertTrue(callback.answers[-1][1])

    def test_tariff_payment_choice_keyboard_lists_only_lavatop_for_public_bot(self) -> None:
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
                {"code": "pally", "label": "Paypalich", "supports_bot": True},
            ]
            with self._checkout_gate_green():
                keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="1_month")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:lavatop:1_month")
        callback_data = [str(button.callback_data or "") for row in keyboard.inline_keyboard for button in row]
        self.assertFalse(any("cardlink" in value or "pally" in value for value in callback_data))
        flat_rows = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertIn("📚 Посмотреть долгие тарифы", flat_rows)
        self.assertIn("◀️ К тарифам", flat_rows)

    def test_tariff_payment_choice_specs_style_public_lavatop_cta(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            with self._checkout_gate_green():
                rows = self.bot_module._tariff_payment_choice_keyboard_specs(tg_id=1001, tariff_key="1_month")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertEqual(rows[0][0]["callback_data"], "pay_rub:lavatop:1_month")
        self.assertEqual(rows[0][0]["style"], self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(rows[0][0]["icon_custom_emoji_id"], "5368324170671202286")

    def test_direct_rub_payment_specs_style_payment_cta(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        rows = self.bot_module._direct_rub_payment_keyboard_specs(
            tg_id=1001,
            tariff_key="1_month",
            payment_url="https://app.lava.top/invoice/test",
            provider_label="Lava.top",
        )

        self.assertEqual(rows[0][0]["url"], "https://app.lava.top/invoice/test")
        self.assertEqual(rows[0][0]["style"], self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(rows[0][0]["icon_custom_emoji_id"], "5368324170671202286")

    def test_tariff_keyboard_is_rub_first_without_visible_stars(self) -> None:
        keyboard = self.bot_module.tariff_keyboard(tg_id=1001, show_trial=True, include_long_plans=False)
        labels = [row[0].text for row in keyboard.inline_keyboard]
        self.assertTrue(any("99 ₽" in text for text in labels))
        self.assertTrue(any("249 ₽" in text for text in labels))
        self.assertTrue(any("699 ₽" in text for text in labels))
        self.assertFalse(any("⭐" in text for text in labels))
        self.assertFalse(any("Stars" in text for text in labels))
        self.assertFalse(any("points" in text.lower() for text in labels))

    def test_tariff_keyboard_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        keyboard = self.bot_module.tariff_keyboard(tg_id=1001, show_trial=True, include_long_plans=False)

        trial_button = keyboard.inline_keyboard[0][0]
        first_plan_button = next(
            button
            for row in keyboard.inline_keyboard
            for button in row
            if str(getattr(button, "callback_data", "") or "") == "buy_start_99"
        )
        long_plans_button = next(
            button
            for row in keyboard.inline_keyboard
            for button in row
            if str(getattr(button, "callback_data", "") or "") == "charge_long"
        )
        back_button = keyboard.inline_keyboard[-1][0]

        self.assertEqual(getattr(trial_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(trial_button, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(first_plan_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(first_plan_button, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(long_plans_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_channel_bonus_keyboard_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        keyboard = self.bot_module._channel_bonus_keyboard("main")
        buttons = [button for row in keyboard.inline_keyboard for button in row]
        subscribe_button = next(button for button in buttons if getattr(button, "url", None))
        claim_button = next(
            button
            for button in buttons
            if str(getattr(button, "callback_data", "") or "") == "bonus_claim_main"
        )
        skip_button = next(
            button
            for button in buttons
            if str(getattr(button, "callback_data", "") or "") == "bonus_skip_main"
        )
        back_button = next(
            button
            for button in buttons
            if str(getattr(button, "callback_data", "") or "") == "back"
        )

        self.assertEqual(getattr(subscribe_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(claim_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(claim_button, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(skip_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_twelve_month_tariff_savings_is_45_percent(self) -> None:
        self.assertEqual(self.bot_module._tariff_savings_pct("12_months"), 45)

    def test_tariff_payment_choice_text_calls_points_bonuses(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        with patch.object(self.bot_module, "preview_redeemable_points") as preview:
            preview.return_value = types.SimpleNamespace(redeemable_points=100)
            text = self.bot_module._build_tariff_payment_choice_text(tariff_key="1_month", tg_id=1001)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐", text)
        self.assertNotIn("points", text.lower())

    def test_choose_tariff_text_is_trial_first_and_no_stars(self) -> None:
        text = self.bot_module.build_choose_tariff_text()
        self.assertIn("5 дней", text)
        self.assertIn("бесплатно", text.lower())
        self.assertIn("5 ГБ", text)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐", text)

    def test_dual_pay_text_uses_five_day_trial_copy(self) -> None:
        text = self.bot_module._dual_pay_text(show_trial=True)
        self.assertIn("5 дней", text)
        self.assertNotIn("3 дня", text)
        self.assertIn("Оплата временно недоступна", text)
        self.assertNotIn("карта и СБП", text)
        self.assertNotIn("оплату в рублях", text)
        self.assertNotIn("После оплаты всё включится автоматически", text)

    def test_dual_pay_keyboard_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        keyboard = self.bot_module._dual_pay_keyboard(tg_id=1001, show_trial=True)

        trial_button = keyboard.inline_keyboard[0][0]
        charge_button = keyboard.inline_keyboard[1][0]
        back_button = keyboard.inline_keyboard[-1][0]
        self.assertIn("Посмотреть тарифы", str(getattr(charge_button, "text", "")))
        self.assertNotIn("оплату", str(getattr(charge_button, "text", "")).lower())
        self.assertEqual(getattr(trial_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(trial_button, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(charge_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(charge_button, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_support_menu_uses_modern_button_fields_for_operator_ctas(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        keyboard = self.bot_module._support_menu_markup()
        buttons = [button for row in keyboard.inline_keyboard for button in row]
        ticket_button = next(button for button in buttons if "ticket_new" in str(getattr(button, "url", "") or ""))
        diagnose_button = next(button for button in buttons if str(getattr(button, "callback_data", "") or "") == "support_diagnose")
        not_work_button = next(button for button in buttons if str(getattr(button, "callback_data", "") or "") == "faq_notwork")

        self.assertEqual(getattr(ticket_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(ticket_button, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(diagnose_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(not_work_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_support_menu_styles_all_public_faq_entries(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        keyboard = self.bot_module._support_menu_markup()
        buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in keyboard.inline_keyboard
            for button in row
            if getattr(button, "callback_data", None)
        }

        for callback_data in ("faq_connect", "faq_renew", "faq_referral", "faq_device"):
            self.assertEqual(getattr(buttons[callback_data], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
            self.assertEqual(getattr(buttons[callback_data], "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(buttons["faq_notwork"], "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(buttons["support_diagnose"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_support_detail_screens_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        faq = _FakeCallback(1001, data="faq_connect")
        asyncio.run(self.bot_module.show_faq_answer(faq))
        faq_buttons = [button for row in faq.message.edit_kwargs[-1]["reply_markup"].inline_keyboard for button in row]
        faq_back = next(button for button in faq_buttons if getattr(button, "callback_data", "") == "support")
        faq_ticket = next(button for button in faq_buttons if "ticket_new" in str(getattr(button, "url", "") or ""))

        self.assertEqual(getattr(faq_back, "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(faq_ticket, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(faq_ticket, "icon_custom_emoji_id", None), "5368324170671202286")

        diagnose = _FakeCallback(1001, data="support_diagnose")
        asyncio.run(self.bot_module.support_diagnose(diagnose))
        diagnose_buttons = [
            button for row in diagnose.message.edit_kwargs[-1]["reply_markup"].inline_keyboard for button in row
        ]
        show_key = next(button for button in diagnose_buttons if getattr(button, "callback_data", "") == "show_key")
        support_back = next(button for button in diagnose_buttons if getattr(button, "callback_data", "") == "support")
        diagnose_ticket = next(
            button for button in diagnose_buttons if "ticket_new" in str(getattr(button, "url", "") or "")
        )

        self.assertEqual(getattr(show_key, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(support_back, "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(diagnose_ticket, "style", None), self.bot_module.BTN_STYLE_PRIMARY)

    def test_ticket_view_keyboard_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        user_keyboard = self.bot_module._ticket_view_keyboard(
            42,
            self.bot_module.STATUS_OPEN,
            is_admin=False,
        )
        user_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in user_keyboard.inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(user_buttons["ticket_reply_42"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(user_buttons["ticket_close_42"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(user_buttons["ticket_my"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(user_buttons["support"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        closed_keyboard = self.bot_module._ticket_view_keyboard(
            42,
            self.bot_module.STATUS_CLOSED,
            is_admin=False,
        )
        closed_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in closed_keyboard.inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(closed_buttons["ticket_reopen_42"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)

        open_ticket = self.bot_module._ticket_open_keyboard(42).inline_keyboard[0][0]
        self.assertEqual(getattr(open_ticket, "callback_data", None), "ticket_view_42")
        self.assertEqual(getattr(open_ticket, "style", None), self.bot_module.BTN_STYLE_PRIMARY)

    def test_ticket_list_and_create_keyboards_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        empty = _FakeCallback(1001, data="ticket_my")
        asyncio.run(self.bot_module.ticket_my(empty))
        empty_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in empty.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(empty_buttons["ticket_new"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(empty_buttons["support"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        create = _FakeCallback(1001, data="ticket_new")
        create.bot = _FakeBot(status="member")
        asyncio.run(self.bot_module.ticket_new(create))
        create_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in create.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(create_buttons["support"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        listing = _FakeCallback(1001, data="ticket_my")
        asyncio.run(self.bot_module.ticket_my(listing))
        list_buttons = [
            button
            for row in listing.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        ]
        ticket_button = next(button for button in list_buttons if str(getattr(button, "callback_data", "") or "").startswith("ticket_view_"))
        new_button = next(button for button in list_buttons if getattr(button, "callback_data", "") == "ticket_new")
        back_button = next(button for button in list_buttons if getattr(button, "callback_data", "") == "support")
        self.assertEqual(getattr(ticket_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(new_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

        reply = _FakeCallback(1001, data=f"ticket_reply_{str(getattr(ticket_button, 'callback_data')).split('_')[-1]}")
        asyncio.run(self.bot_module.ticket_reply(reply))
        reply_back = reply.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[-1][0]
        self.assertEqual(getattr(reply_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_stars_unavailable_keyboard_uses_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        keyboard = self.bot_module._stars_payments_unavailable_keyboard()
        buttons = [button for row in keyboard.inline_keyboard for button in row]
        gift_button = next(button for button in buttons if str(getattr(button, "callback_data", "") or "") == "gift_redeem_prompt")
        cabinet_button = next(button for button in buttons if getattr(button, "web_app", None) is not None)
        back_button = next(button for button in buttons if str(getattr(button, "callback_data", "") or "") == "menu_more")

        self.assertEqual(getattr(gift_button, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(cabinet_button, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(back_button, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_access_key_keyboard_uses_modern_button_fields_for_account_actions(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"
        keyboard = self.bot_module._access_key_keyboard()
        buttons = {str(button.callback_data or ""): button for row in keyboard.inline_keyboard for button in row}

        self.assertEqual(getattr(buttons["copy_key"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(buttons["show_qr"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(buttons["share_access"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(buttons["panic_menu"], "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(buttons["copy_key"], "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(buttons["share_access"], "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(buttons["panic_menu"], "icon_custom_emoji_id", None), "5368324170671202299")

    def test_access_key_keyboard_uses_copy_text_button_when_link_is_known(self) -> None:
        keyboard = self.bot_module._access_key_keyboard(copy_text="https://connect.pokrov.space/sub/test")
        copy_button = keyboard.inline_keyboard[0][0]

        self.assertIsNone(getattr(copy_button, "callback_data", None))
        self.assertEqual(getattr(getattr(copy_button, "copy_text", None), "text", None), "https://connect.pokrov.space/sub/test")

    def test_simple_onboarding_keyboards_use_modern_button_fields(self) -> None:
        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        device_keyboard = self.bot_module._mode_simple_device_keyboard()
        install_keyboard = self.bot_module._mode_simple_install_keyboard(
            app_name="POKROV",
            app_link="https://pokrov.space/install/",
        )
        plan_keyboard = self.bot_module._mode_simple_plan_keyboard(starter_price=99, recommended_price=699)

        simple_android = next(
            button
            for row in device_keyboard.inline_keyboard
            for button in row
            if str(getattr(button, "callback_data", "") or "") == "simple_android"
        )
        installed = next(
            button
            for row in install_keyboard.inline_keyboard
            for button in row
            if str(getattr(button, "callback_data", "") or "") == "simple_step3"
        )
        download = install_keyboard.inline_keyboard[0][0]
        trial = plan_keyboard.inline_keyboard[0][0]
        back = plan_keyboard.inline_keyboard[-1][0]

        self.assertEqual(getattr(simple_android, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(simple_android, "icon_custom_emoji_id", None), "5368324170671202286")
        self.assertEqual(getattr(download, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(installed, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(trial, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(back, "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_simple_onboarding_routes_platform_downloads_through_cabinet(self) -> None:
        self.bot_module.WEBAPP_URL = "https://app.pokrov.space/"

        android = _FakeCallback(1001, data="simple_android")
        windows = _FakeCallback(1001, data="simple_pc")

        asyncio.run(self.bot_module.mode_simple_step2(android))
        asyncio.run(self.bot_module.mode_simple_step2(windows))

        android_url = android.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[0][0].url
        windows_url = windows.message.edit_kwargs[-1]["reply_markup"].inline_keyboard[0][0].url
        self.assertEqual(android_url, "https://app.pokrov.space/downloads/?platform=android")
        self.assertEqual(windows_url, "https://app.pokrov.space/downloads/?platform=windows")
        self.assertNotIn("github.com", android_url)
        self.assertNotIn("github.com", windows_url)

    def test_simple_onboarding_apple_is_status_only(self) -> None:
        callback = _FakeCallback(1001, data="simple_ios")

        asyncio.run(self.bot_module.mode_simple_step2(callback))

        text = callback.message.edits[-1]
        buttons = [
            button
            for row in callback.message.edit_kwargs[-1]["reply_markup"].inline_keyboard
            for button in row
        ]
        callback_data = {getattr(button, "callback_data", "") for button in buttons}

        self.assertIn("Apple пока в подготовке", text)
        self.assertIn("Android и Windows", text)
        self.assertNotIn("👇 Нажмите, чтобы скачать", text)
        self.assertNotIn("simple_step3", callback_data)

    def test_main_keyboard_uses_kabinet_label_instead_of_portal(self) -> None:
        rows = self.bot_module.main_keyboard_specs(1001)
        labels = [str(button.get("text") or "") for row in rows for button in row]
        upper_labels = [label.upper() for label in labels]
        self.assertTrue(any("КАБИНЕТ" in label for label in upper_labels))
        self.assertFalse(any("ПОРТАЛ" in label for label in upper_labels))

    def test_telegram_button_payload_keeps_current_style_and_icon_fields(self) -> None:
        rows = [[
            self.bot_module._btn_spec(
                text="Open",
                callback_data="open",
                style=self.bot_module.BTN_STYLE_PRIMARY,
                icon_custom_emoji_id="5368324170671202286",
            )
        ]]

        payload = self.bot_module._keyboard_payload(rows)
        button = payload["inline_keyboard"][0][0]
        self.assertEqual(button["style"], "primary")
        self.assertEqual(button["icon_custom_emoji_id"], "5368324170671202286")
        self.assertEqual(button["callback_data"], "open")

    def test_telegram_button_requires_raw_markup_when_ptb_lacks_new_fields(self) -> None:
        rows = [[
            self.bot_module._btn_spec(
                text="Open",
                callback_data="open",
                style=self.bot_module.BTN_STYLE_SUCCESS,
                icon_custom_emoji_id="5368324170671202286",
            )
        ]]

        with patch.object(self.bot_module, "SUPPORTS_BTN_STYLE", False), patch.object(
            self.bot_module, "SUPPORTS_BTN_ICON", False
        ):
            self.assertTrue(self.bot_module._needs_raw_markup(rows))

        with patch.object(self.bot_module, "SUPPORTS_BTN_STYLE", True), patch.object(
            self.bot_module, "SUPPORTS_BTN_ICON", True
        ):
            self.assertFalse(self.bot_module._needs_raw_markup(rows))

    def test_telegram_button_constructor_omits_unsupported_new_fields(self) -> None:
        captured: list[dict] = []

        class _FakeInlineKeyboardButton:
            def __init__(self, **kwargs):
                captured.append(dict(kwargs))

        spec = self.bot_module._btn_spec(
            text="Open",
            callback_data="open",
            style=self.bot_module.BTN_STYLE_DANGER,
            icon_custom_emoji_id="5368324170671202286",
        )

        with patch.object(self.bot_module, "InlineKeyboardButton", _FakeInlineKeyboardButton), patch.object(
            self.bot_module, "SUPPORTS_BTN_STYLE", False
        ), patch.object(self.bot_module, "SUPPORTS_BTN_ICON", False):
            self.bot_module._button_from_spec(spec)

        self.assertEqual(captured[-1], {"text": "Open", "callback_data": "open"})

        with patch.object(self.bot_module, "InlineKeyboardButton", _FakeInlineKeyboardButton), patch.object(
            self.bot_module, "SUPPORTS_BTN_STYLE", True
        ), patch.object(self.bot_module, "SUPPORTS_BTN_ICON", True):
            self.bot_module._button_from_spec(spec)

        self.assertEqual(captured[-1]["style"], "danger")
        self.assertEqual(captured[-1]["icon_custom_emoji_id"], "5368324170671202286")

    def test_direct_inline_keyboard_button_infers_modern_fields(self) -> None:
        if not (self.bot_module.SUPPORTS_BTN_STYLE and self.bot_module.SUPPORTS_BTN_ICON):
            self.skipTest("Installed aiogram does not expose modern button fields")

        self.bot_module.BTN_EMOJI_PRIMARY_ID = "5368324170671202286"
        self.bot_module.BTN_EMOJI_SUCCESS_ID = "5373141891321699086"
        self.bot_module.BTN_EMOJI_DANGER_ID = "5368324170671202299"

        back = self.bot_module.InlineKeyboardButton(text="Back", callback_data="back")
        create = self.bot_module.InlineKeyboardButton(text="Create", callback_data="ticket_new")
        open_link = self.bot_module.InlineKeyboardButton(text="Open", url="https://pokrov.space/")

        self.assertEqual(getattr(back, "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(back, "icon_custom_emoji_id", None), "5368324170671202299")
        self.assertEqual(getattr(create, "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(create, "icon_custom_emoji_id", None), "5373141891321699086")
        self.assertEqual(getattr(open_link, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(open_link, "icon_custom_emoji_id", None), "5368324170671202286")

    def test_env_example_documents_telegram_button_custom_emoji_ids(self) -> None:
        env_example = (Path(__file__).resolve().parents[1] / "portal_bot" / ".env.example").read_text(encoding="utf-8")

        for name in ("TG_BTN_EMOJI_PRIMARY_ID", "TG_BTN_EMOJI_SUCCESS_ID", "TG_BTN_EMOJI_DANGER_ID"):
            self.assertIn(f"{name}=", env_example)

    def test_web_login_receipt_and_payment_keyboards_use_modern_fields(self) -> None:
        login_keyboard = self.bot_module._web_login_issued_keyboard("https://app.pokrov.space/?web_session_token=test")
        login_buttons = {
            str(getattr(button, "callback_data", "") or getattr(button, "url", "") or ""): button
            for row in login_keyboard.inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(login_buttons["https://app.pokrov.space/?web_session_token=test"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(login_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        invoice_keyboard = self.bot_module._stars_invoice_check_keyboard()
        invoice_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in invoice_keyboard.inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(invoice_buttons["status"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(invoice_buttons["charge"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(invoice_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        support_keyboard = self.bot_module._fulfillment_support_keyboard()
        support_buttons = [button for row in support_keyboard.inline_keyboard for button in row]
        support_url = next(button for button in support_buttons if getattr(button, "url", ""))
        support_back = next(button for button in support_buttons if getattr(button, "callback_data", "") == "back")
        self.assertEqual(getattr(support_url, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(support_back, "style", None), self.bot_module.BTN_STYLE_DANGER)

        ready_keyboard = self.bot_module._paid_access_ready_keyboard()
        ready_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in ready_keyboard.inline_keyboard
            for button in row
            if getattr(button, "callback_data", "")
        }
        ready_web_app = next(
            button
            for row in ready_keyboard.inline_keyboard
            for button in row
            if getattr(button, "web_app", None) is not None
        )
        self.assertEqual(getattr(ready_buttons["instruction"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(ready_web_app, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(ready_buttons["show_key"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(ready_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

    def test_public_fallback_keyboards_use_modern_fields(self) -> None:
        channel_keyboard = self.bot_module._channel_link_keyboard()
        channel = channel_keyboard.inline_keyboard[0][0]
        self.assertEqual(getattr(channel, "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertIn("t.me/", getattr(channel, "url", ""))

        no_access = self.bot_module._no_access_fallback_keyboard(1001)
        no_access_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in no_access.inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(no_access_buttons["charge"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(no_access_buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        panic_confirm = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.bot_module._panic_confirm_keyboard().inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(panic_confirm["panic_execute"], "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(panic_confirm["show_key"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        panic_done = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.bot_module._panic_done_keyboard().inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(panic_done["show_key"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(panic_done["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        single_back = self.bot_module._single_back_keyboard().inline_keyboard[0][0]
        self.assertEqual(getattr(single_back, "style", None), self.bot_module.BTN_STYLE_DANGER)
        self.assertEqual(getattr(single_back, "callback_data", None), "back")

        channel_success = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.bot_module._channel_bonus_activated_keyboard().inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(channel_success["show_key"], "style", None), self.bot_module.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(channel_success["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

        payment_fallback = self.bot_module._payment_success_fallback_keyboard().inline_keyboard[0][0]
        self.assertEqual(getattr(payment_fallback, "callback_data", None), "show_key")
        self.assertEqual(getattr(payment_fallback, "style", None), self.bot_module.BTN_STYLE_SUCCESS)

        expired_recovery = self.bot_module._expired_access_recovery_keyboard().inline_keyboard[0][0]
        self.assertEqual(getattr(expired_recovery, "callback_data", None), "charge")
        self.assertEqual(getattr(expired_recovery, "style", None), self.bot_module.BTN_STYLE_PRIMARY)

    def test_activate_promo_code_rejects_expired_promo(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        session = self.bot_module.Session()
        try:
            session.add(
                self.bot_module.PromoCode(
                    code="EXPIRED14",
                    promo_type="days",
                    value=14,
                    uses_left=10,
                    expires_at=self.bot_module._utcnow() - timedelta(days=1),
                )
            )
            session.commit()
        finally:
            session.close()

        ok, result = self.bot_module.activate_promo_code_for_user(1001, "EXPIRED14")
        self.assertFalse(ok)
        self.assertIn("ист", result.lower())

    def test_activate_promo_code_respects_campaign_segment_restrictions(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.sub_type = "FREE"
            user.is_active = True
            session.add(
                self.bot_module.PromoCode(
                    code="PAIDONLY20",
                    promo_type="discount",
                    value=20,
                    uses_left=10,
                )
            )
            session.add(
                self.bot_module.IncentiveCampaign(
                    name="Paid only promo",
                    campaign_type="promo",
                    target_value="PAIDONLY20",
                    segment="paid",
                    max_activations=-1,
                    activations_count=0,
                    auto_disable=True,
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        ok, result = self.bot_module.activate_promo_code_for_user(1001, "PAIDONLY20")
        self.assertFalse(ok)
        self.assertIn("недоступ", result.lower())

    def test_activate_promo_code_rejects_zero_value_without_burning_usage(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)

        session = self.bot_module.Session()
        try:
            session.add(
                self.bot_module.PromoCode(
                    code="ZERODAYS",
                    promo_type="days",
                    value=0,
                    uses_left=2,
                )
            )
            session.commit()
        finally:
            session.close()

        ok, _result = self.bot_module.activate_promo_code_for_user(1001, "ZERODAYS")
        self.assertFalse(ok)

        session = self.bot_module.Session()
        try:
            promo = session.query(self.bot_module.PromoCode).filter_by(code="ZERODAYS").first()
            self.assertIsNotNone(promo)
            self.assertEqual(int(promo.uses_left or 0), 2)

            usage = session.query(self.bot_module.PromoUsage).filter_by(tg_id=1001, promo_code="ZERODAYS").all()
            self.assertEqual(usage, [])
        finally:
            session.close()

    def test_redeem_gift_card_respects_campaign_segment_restrictions(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)
        code = self.bot_module.create_gift_card(2002, "standard")
        self.assertTrue(code)

        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.sub_type = "FREE"
            user.is_active = True
            session.add(
                self.bot_module.IncentiveCampaign(
                    name="Paid only gift",
                    campaign_type="gift",
                    target_value="STANDARD",
                    segment="paid",
                    max_activations=-1,
                    activations_count=0,
                    auto_disable=True,
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        ok, result = asyncio.run(self.bot_module.redeem_gift_card(code, 1001, _FakeBot(status="member")))
        self.assertFalse(ok)
        self.assertIn("недоступ", result.lower())


    def test_mark_campaign_claim_once_returns_false_on_duplicate_insert_race(self) -> None:
        class _FakeSession:
            def __init__(self) -> None:
                self.rollback_called = False
                self.closed = False

            def add(self, _row) -> None:
                return None

            def commit(self) -> None:
                raise IntegrityError("insert", {}, Exception("duplicate"))

            def rollback(self) -> None:
                self.rollback_called = True

            def close(self) -> None:
                self.closed = True

        fake = _FakeSession()
        old_session_factory = self.bot_module.Session
        self.bot_module.Session = lambda: fake
        try:
            out = self.bot_module._mark_campaign_claim_once(tg_id=1001, campaign_key="opening_premium_14d")
        finally:
            self.bot_module.Session = old_session_factory

        self.assertFalse(out)
        self.assertTrue(fake.rollback_called)
        self.assertTrue(fake.closed)

    def test_wheel_spin_uses_configured_cooldown_and_tracks_result(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")

        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            user.sub_type = "PAID"
            user.is_active = True
            user.first_purchase_done = True
            user.expiry_at = self.bot_module._utcnow() + timedelta(days=30)
            session.commit()
        finally:
            session.close()

        callback = _FakeCallback(1001)
        tracked: list[dict] = []
        panel_calls: list[tuple[int, int]] = []

        async def _fake_sleep(_seconds):
            return None

        async def _fake_update_client_traffic(tg_id, add_gb):
            panel_calls.append((int(tg_id), int(add_gb)))
            return True

        def _fake_track_event(**kwargs):
            tracked.append(kwargs)
            return 1

        old_spin = self.bot_module.spin_wheel
        old_award = self.bot_module.award_achievement
        old_panel_update = self.bot_module.panel.update_client_traffic
        old_track_event = self.bot_module.track_event
        try:
            self.bot_module.spin_wheel = lambda _tg_id: 30
            self.bot_module.award_achievement = lambda tg_id, achievement_id: 0
            self.bot_module.panel.update_client_traffic = _fake_update_client_traffic
            self.bot_module.track_event = _fake_track_event
            with patch("asyncio.sleep", new=_fake_sleep):
                with patch.object(self.bot_module, "_wheel_cooldown_days", return_value=5):
                    asyncio.run(self.bot_module.do_wheel_spin(callback))
        finally:
            self.bot_module.spin_wheel = old_spin
            self.bot_module.award_achievement = old_award
            self.bot_module.panel.update_client_traffic = old_panel_update
            self.bot_module.track_event = old_track_event

        self.assertEqual(panel_calls, [(1001, 0)])
        self.assertGreaterEqual(len(callback.message.edits), 2)
        self.assertIn("Приходи через 5 дней", callback.message.edits[-1])
        self.assertEqual(callback.answers[-1], ("🎉 +30 Дней!", True))
        self.assertEqual(len(tracked), 1)
        self.assertEqual(tracked[0]["event_name"], "wheel_spin")
        self.assertEqual(int(tracked[0]["meta"]["prize_days"]), 30)
        self.assertEqual(int(tracked[0]["meta"]["cooldown_days"]), 5)
        self.assertTrue(bool(tracked[0]["meta"]["sync_ok"]))


if __name__ == "__main__":
    unittest.main()
