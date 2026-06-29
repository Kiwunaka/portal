import asyncio
import importlib
import inspect
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

    async def get_chat_member(self, chat_id: str, user_id: int):
        self.calls.append((chat_id, user_id))
        if self._fail:
            raise RuntimeError("api unavailable")
        return _FakeMember(self._status or "left")


class _FakeMessage:
    def __init__(self):
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
        for k in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID", "NEWS_CHANNEL_ID", "CHECKOUT_TICKET_SECRET", "CHECKOUT_TICKET_TTL_SECONDS"):
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

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])
        if "db" in sys.modules:
            importlib.reload(sys.modules["db"])
        if "bot" in sys.modules:
            importlib.reload(sys.modules["bot"])
        self.bot_module = importlib.import_module("bot")
        importlib.reload(self.bot_module)

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

    def test_show_key_exposes_single_public_connection_link(self) -> None:
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
        self.assertNotIn("?format=plain", final_text)
        self.assertNotIn("Обычная ссылка", final_text)

        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        labels = [button.text for row in reply_markup.inline_keyboard for button in row]
        self.assertIn("📋 Скопировать ссылку", labels)
        self.assertIn("📱 QR для подключения", labels)
        self.assertIn("📲 Как подключить вручную", labels)
        self.assertNotIn("👨‍👩‍👧‍👦 Поделиться доступом", labels)
        self.assertNotIn("🚨 Panic Mode", labels)

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

    def test_redeem_gift_card_accepts_plan_access_key(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)
        code = "POKROV-PLAN-KEY1"

        session = self.bot_module.Session()
        try:
            session.add(self.bot_module.GiftCard(code=code, card_type="start_99", created_by=2002))
            session.commit()
        finally:
            session.close()

        ok, result = asyncio.run(self.bot_module.redeem_gift_card(code, 1001, _FakeBot(status="member")))
        self.assertTrue(ok, result)
        self.assertIn("дней", result)

        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            card = session.query(self.bot_module.GiftCard).filter_by(code=code).first()
            self.assertIsNotNone(user)
            self.assertIsNotNone(card)
            self.assertEqual(str(user.current_plan_code or ""), "start_99")
            self.assertEqual(int(card.redeemed_by or 0), 1001)
        finally:
            session.close()

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

    def test_tariff_payment_choice_text_stays_rub_only_and_closed_without_launch_gate(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        text = self.bot_module._build_tariff_payment_choice_text(tariff_key="1_month", tg_id=1001)
        self.assertIn("Цена в ₽: *249 ₽*", text)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐", text)
        self.assertIn("Оплата пока закрыта", text)
        self.assertNotIn("выберите удобную кассу", text.lower())

    def test_tariff_payment_choice_keyboard_keeps_plan_in_checkout_url(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
        self.bot_module.checkout_context_by_user[1001] = {
            "promo_code": "WELCOME14",
            "campaign_key": "launch_week_1",
        }
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
            ]
            keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="3_months")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog
        self.assertEqual(keyboard.inline_keyboard[0][0].text, "💳 Cardlink · 699 ₽")
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:cardlink:3_months")
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

    def test_direct_rub_payment_keyboard_keeps_site_fallback(self) -> None:
        self.bot_module.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
        self.bot_module.checkout_context_by_user[1001] = {
            "promo_code": "WELCOME14",
            "campaign_key": "launch_week_1",
        }
        keyboard = self.bot_module._build_direct_rub_payment_keyboard(
            tg_id=1001,
            tariff_key="3_months",
            payment_url="https://pay.freekassa.ru/?order=abc",
        )
        self.assertEqual(keyboard.inline_keyboard[0][0].url, "https://pay.freekassa.ru/?order=abc")
        self.assertIn("plan=3_months", keyboard.inline_keyboard[1][0].url)
        self.assertIn("promo=WELCOME14", keyboard.inline_keyboard[1][0].url)
        self.assertIn("campaign=launch_week_1", keyboard.inline_keyboard[1][0].url)
        flat_text = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertFalse(any("Stars" in text or "⭐" in text for text in flat_text))

    def test_process_buy_rub_opens_direct_payment_link(self) -> None:
        callback = _FakeCallback(1001, data="pay_rub:cardlink:1_month")

        old_catalog = self.bot_module.enabled_provider_catalog

        async def _fake_create_payment_link(*, provider, tg_id, tariff_key):
            self.assertEqual(str(provider), "cardlink")
            self.assertEqual(int(tg_id), 1001)
            self.assertEqual(str(tariff_key), "1_month")
            return {
                "order_id": "cardlink_bot_1001_test",
                "payment_url": "https://checkout.cardlink.link/pay/test",
            }

        old_create = self.bot_module._create_rub_payment_link_for_bot
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
            ]
            self.bot_module._create_rub_payment_link_for_bot = _fake_create_payment_link
            asyncio.run(self.bot_module.process_buy_rub(callback, _FakeBot(status="member")))
        finally:
            self.bot_module._create_rub_payment_link_for_bot = old_create
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertTrue(callback.message.edits)
        self.assertIn("Следующий шаг: откройте оплату", callback.message.edits[-1])
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        self.assertEqual(reply_markup.inline_keyboard[0][0].url, "https://checkout.cardlink.link/pay/test")
        self.assertEqual(callback.answers[-1], ("Ссылка на оплату готова", False))

    def test_tariff_payment_choice_keyboard_lists_enabled_rub_providers(self) -> None:
        old_catalog = self.bot_module.enabled_provider_catalog
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_provider_catalog = lambda: [
                {"code": "cardlink", "label": "Cardlink", "supports_bot": True},
                {"code": "pally", "label": "Paypalich", "supports_bot": True},
            ]
            keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="1_month")
        finally:
            self.bot_module.enabled_provider_catalog = old_catalog

        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:cardlink:1_month")
        self.assertEqual(keyboard.inline_keyboard[1][0].callback_data, "pay_rub:pally:1_month")
        flat_rows = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertIn("📚 Посмотреть долгие тарифы", flat_rows)
        self.assertIn("◀️ К тарифам", flat_rows)

    def test_tariff_keyboard_is_rub_first_without_visible_stars(self) -> None:
        keyboard = self.bot_module.tariff_keyboard(tg_id=1001, show_trial=True, include_long_plans=False)
        labels = [row[0].text for row in keyboard.inline_keyboard]
        self.assertTrue(any("99 ₽" in text for text in labels))
        self.assertTrue(any("249 ₽" in text for text in labels))
        self.assertTrue(any("699 ₽" in text for text in labels))
        self.assertFalse(any("⭐" in text for text in labels))
        self.assertFalse(any("Stars" in text for text in labels))
        self.assertFalse(any("points" in text.lower() for text in labels))

    def test_main_bot_regular_keyboards_use_modern_button_fields_when_supported(self) -> None:
        if not self.bot_module.SUPPORTS_BTN_STYLE:
            self.skipTest("aiogram InlineKeyboardButton has no style field")

        keyboard = self.bot_module.tariff_keyboard(tg_id=1001, show_trial=True, include_long_plans=False)
        buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in keyboard.inline_keyboard
            for button in row
        }

        self.assertEqual(getattr(buttons["charge_long"], "style", None), self.bot_module.BTN_STYLE_PRIMARY)
        self.assertEqual(getattr(buttons["back"], "style", None), self.bot_module.BTN_STYLE_DANGER)

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

    def test_main_keyboard_uses_kabinet_label_instead_of_portal(self) -> None:
        rows = self.bot_module.main_keyboard_specs(1001)
        labels = [str(button.get("text") or "") for row in rows for button in row]
        upper_labels = [label.upper() for label in labels]
        self.assertTrue(any("КАБИНЕТ" in label for label in upper_labels))
        self.assertTrue(any("ПОДКЛЮЧИТЬ УСТРОЙСТВО" in label for label in upper_labels))
        self.assertTrue(any("ПОМОЩЬ" in label for label in upper_labels))
        self.assertFalse(any("ПОРТАЛ" in label for label in upper_labels))
        self.assertFalse(any("РУЧНАЯ ССЫЛКА" in label for label in upper_labels))
        self.assertFalse(any("БОНУСЫ" in label for label in upper_labels))

    def test_confused_help_routes_to_user_intents_without_raw_link(self) -> None:
        callback = _FakeCallback(1001, data="confused_help")

        asyncio.run(self.bot_module.confused_help(callback))

        final_text = callback.message.edits[-1]
        self.assertIn("Давайте без терминов", final_text)
        self.assertNotIn("connect.pokrov.space", final_text)
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        labels = [button.text for row in reply_markup.inline_keyboard for button in row]
        self.assertIn("📲 Подключить это устройство", labels)
        self.assertIn("🎫 Есть код оплаты или подарок", labels)
        self.assertIn("🔗 Есть личная ссылка", labels)
        self.assertIn("⚠️ Подключение не работает", labels)

    def test_bulk_subscription_update_broadcasts_do_not_send_raw_links(self) -> None:
        bulk_handlers = (
            self.bot_module.admin_broadcast_links,
            self.bot_module.admin_broadcast,
        )
        for handler in bulk_handlers:
            with self.subTest(handler=handler.__name__):
                source = inspect.getsource(handler)
                self.assertNotIn("build_subscription_link", source)
                self.assertNotIn("connect.pokrov.space", source)
                self.assertNotIn("ссылка подписки", source.lower())

    def test_configure_public_bot_menu_matches_live_checker_payload(self) -> None:
        class _MenuBot:
            def __init__(self) -> None:
                self.commands = []
                self.menu_button = None

            async def set_my_commands(self, commands):
                self.commands = list(commands)

            async def set_chat_menu_button(self, *, menu_button):
                self.menu_button = menu_button

        fake = _MenuBot()
        asyncio.run(self.bot_module._configure_public_bot_menu(fake))

        command_payload = [(item.command, item.description) for item in fake.commands]
        self.assertEqual(
            command_payload,
            [
                ("start", "Открыть главное меню"),
                ("cabinet", "Открыть кабинет"),
                ("support", "Написать в поддержку"),
                ("promo", "Активировать промокод"),
                ("redeem", "Активировать ключ доступа"),
            ],
        )
        self.assertEqual(getattr(fake.menu_button, "text", ""), "POKROV")
        self.assertEqual(getattr(getattr(fake.menu_button, "web_app", None), "url", ""), "https://app.pokrov.space/")

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

    def test_more_menu_back_clears_pending_code_prompts(self) -> None:
        callback = _FakeCallback(1001)

        asyncio.run(self.bot_module.gift_redeem_prompt(callback))
        self.assertIn(1001, self.bot_module.pending_redeem_codes)
        asyncio.run(self.bot_module.menu_more(callback))
        self.assertNotIn(1001, self.bot_module.pending_redeem_codes)

        asyncio.run(self.bot_module.promo_activate_prompt(callback))
        self.assertIn(1001, self.bot_module.pending_promo_codes)
        asyncio.run(self.bot_module.menu_more(callback))
        self.assertNotIn(1001, self.bot_module.pending_promo_codes)

    def test_wheel_back_returns_to_bonuses_menu(self) -> None:
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
        asyncio.run(self.bot_module.show_wheel(callback))

        markup = callback.message.edit_kwargs[-1]["reply_markup"]
        callbacks = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
            if getattr(button, "callback_data", None)
        ]
        self.assertIn("menu_bonuses", callbacks)
        self.assertNotIn("back", callbacks)


if __name__ == "__main__":
    unittest.main()
