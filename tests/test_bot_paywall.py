import asyncio
import importlib
import os
import sys
import tempfile
import types
import unittest
import uuid
from pathlib import Path


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

    def test_parse_start_deeplink_context_supports_promo_and_campaign(self) -> None:
        promo, campaign = self.bot_module._parse_start_deeplink_context("promo_newyear")
        self.assertEqual(promo, "NEWYEAR")
        self.assertEqual(campaign, "")

        promo2, campaign2 = self.bot_module._parse_start_deeplink_context("campaign_launch__promo_welcome14")
        self.assertEqual(promo2, "WELCOME14")
        self.assertEqual(campaign2, "launch")

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


if __name__ == "__main__":
    unittest.main()
