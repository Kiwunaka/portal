import asyncio
import hashlib
import importlib
import inspect
import json
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


class _FakeSuccessfulPayment:
    def __init__(self, *, payload: str, charge_id: str, amount: int = 299):
        self.invoice_payload = payload
        self.telegram_payment_charge_id = charge_id
        self.provider_payment_charge_id = f"provider-{charge_id}"
        self.total_amount = int(amount)
        self.currency = "XTR"


class _FakePaymentMessage(_FakeMessage):
    def __init__(self, *, tg_id: int, payload: str, charge_id: str, amount: int = 299):
        super().__init__()
        self.from_user = _FakeUser(tg_id)
        self.successful_payment = _FakeSuccessfulPayment(
            payload=payload,
            charge_id=charge_id,
            amount=amount,
        )


def _owned_panel_client(
    *,
    token: str,
    client_uuid: str | None = None,
    node_code: str = "NL-test",
    node_id: int = 0,
) -> dict:
    return {
        "id": client_uuid or "12345678-1234-4234-9234-123456789abc",
        "email": "User_1001",
        "subId": token,
        "tgId": "1001",
        "_node_code": node_code,
        "_node_id": node_id,
    }

class _FakeUser:
    def __init__(self, tg_id: int):
        self.id = int(tg_id)


class _FakeCallback:
    def __init__(self, tg_id: int, data: str = ""):
        self.from_user = _FakeUser(tg_id)
        self.message = _FakeMessage()
        self.message.chat = types.SimpleNamespace(id=int(tg_id))
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

    def test_admin_resync_respects_persisted_free_role_and_blocks_transitions(self) -> None:
        nodes = [
            types.SimpleNamespace(
                code="nl-free-standard",
                access_role="free_standard",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
            ),
            types.SimpleNamespace(
                code="nl-free-soft",
                access_role="free_soft",
                enabled=True,
                accepting_new_clients=True,
                is_draining=False,
            ),
        ]
        old_enabled_nodes = self.bot_module._bot_enabled_nodes
        self.bot_module._bot_enabled_nodes = lambda: nodes
        try:
            soft_user = types.SimpleNamespace(
                sub_type="FREE",
                current_plan_code="free_monthly",
                free_profile_state="soft_active",
                free_profile_active_role="free_soft",
            )
            pending_user = types.SimpleNamespace(
                sub_type="FREE",
                current_plan_code="free_monthly",
                free_profile_state="soft_transition_pending",
                free_profile_active_role="free_standard",
            )
            paid_pending_user = types.SimpleNamespace(
                sub_type="PAID",
                current_plan_code="paid_30d",
                free_profile_state="soft_transition_pending",
                free_profile_active_role="free_standard",
            )

            self.assertEqual(self.bot_module._bot_resync_node_codes(soft_user), ["nl-free-soft"])
            with self.assertRaisesRegex(ValueError, "transition"):
                self.bot_module._bot_resync_node_codes(pending_user)
            with self.assertRaisesRegex(ValueError, "transition"):
                self.bot_module._bot_resync_node_codes(paid_pending_user)
        finally:
            self.bot_module._bot_enabled_nodes = old_enabled_nodes

        bulk_source = inspect.getsource(self.bot_module.admin_sync_free_pl)
        self.assertIn("_bot_resync_node_codes", bulk_source)
        self.assertNotIn("only_node_codes=free_codes", bulk_source)

    def test_expiry_monitor_uses_durable_reentry_instead_of_direct_panel_mutation(self) -> None:
        source = inspect.getsource(self.bot_module.monitor_expiry)

        self.assertIn("_queue_expired_user_reentry", source)
        self.assertNotIn("ensure_user_on_all_nodes", source)
        self.assertNotIn("set_existing_user_enabled_on_nodes", source)

    def test_soft_profile_copy_uses_shared_two_mbps_fact(self) -> None:
        user = types.SimpleNamespace(
            sub_type="FREE",
            current_plan_code="free_monthly",
            free_profile_state="soft_active",
            free_profile_active_role="free_soft",
        )

        self.assertEqual(self.bot_module.FREE_SOFT_SPEED_MBIT, 2)
        self.assertIn("2 Мбит/с", self.bot_module._plan_mode_label("FREE", user=user))
        self.assertIn("2 Мбит/с", self.bot_module._free_access_note(user))
        self.assertNotIn("50 Мбит/с", self.bot_module._free_access_note(user))
        self.assertEqual(asyncio.run(self.bot_module._free_remaining_gb(1001, user=user)), (0.0, 5.0))

        trial_user = types.SimpleNamespace(
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=self.bot_module._utcnow() + timedelta(days=5),
            free_profile_state="standard",
            free_profile_active_role="free_standard",
        )
        trial_label = self.bot_module._plan_mode_label("FREE", user=trial_user)
        self.assertIn("премиум", trial_label)
        self.assertNotIn("5 ГБ", trial_label)

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

    def test_app_link_rejects_admin_telegram_for_non_admin_account(self) -> None:
        account_tg_id = 424242
        admin_tg_id = 9999
        code = "appadminbind"
        session = self.bot_module.Session()
        try:
            session.add(
                self.bot_module.User(
                    tg_id=account_tg_id,
                    username="attacker_app",
                    uuid=str(uuid.uuid4()),
                    sub_token="attacker-token",
                )
            )
            session.add(
                self.bot_module.User(
                    tg_id=admin_tg_id,
                    username="admin_owner",
                    uuid=str(uuid.uuid4()),
                    sub_token="admin-token",
                )
            )
            session.add(
                self.bot_module.StartLink(
                    code=code,
                    target_action=f"app_link:{account_tg_id}",
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        status = self.bot_module._bind_app_account_to_telegram(
            account_tg_id=account_tg_id,
            telegram_id=admin_tg_id,
            telegram_username="admin_owner",
            start_code=code,
        )

        self.assertEqual(status, "telegram_already_linked")
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=account_tg_id).first()
            self.assertIsNotNone(user)
            self.assertIsNone(user.linked_telegram_id)
        finally:
            session.close()

    def test_build_subscription_link_uses_canonical_connect_host(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        session = self.bot_module.Session()
        try:
            user = session.query(self.bot_module.User).filter_by(tg_id=1001).first()
            self.assertIsNotNone(user)
            self.assertTrue(user.account_id)
            from models import AccountIdentity

            identity = (
                session.query(AccountIdentity)
                .filter_by(
                    account_id=str(user.account_id),
                    kind="telegram",
                    provider="telegram",
                    subject_norm="1001",
                )
                .one()
            )
            self.assertIsNotNone(identity)
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
                self.message.chat = types.SimpleNamespace(id=tg_id, type="private")

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
        self.assertIn("📋 Скопировать для Happ", labels)
        self.assertIn("📱 QR для Hiddify", labels)
        self.assertIn("📱 QR для Happ", labels)
        self.assertIn("📲 Как подключить вручную", labels)
        self.assertNotIn("Karing", " ".join(labels))
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

    def test_channel_acquisition_gate_cannot_block_customer_critical_actions(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="new-lead")
        new_lead = self.bot_module.get_user(1001)
        self.assertTrue(
            self.bot_module._channel_acquisition_gate_blocks(
                user=new_lead,
                action="trial",
                is_member=False,
            )
        )
        for action in ("payment", "renewal", "recovery", "support"):
            self.assertFalse(
                self.bot_module._channel_acquisition_gate_blocks(
                    user=new_lead,
                    action=action,
                    is_member=False,
                )
            )

        session = self.bot_module.Session()
        try:
            customer = session.query(self.bot_module.User).filter_by(tg_id=1001).one()
            customer.first_purchase_done = True
            customer.is_active = False
            customer.expiry_at = self.bot_module._utcnow() - timedelta(days=1)
            session.commit()
        finally:
            session.close()
        former_customer = self.bot_module.get_user(1001)
        for action in ("acquisition", "trial", "payment", "renewal", "recovery", "support"):
            self.assertFalse(
                self.bot_module._channel_acquisition_gate_blocks(
                    user=former_customer,
                    action=action,
                    is_member=False,
                )
            )

    def test_legacy_trial_callbacks_route_to_app_without_granting_entitlement(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="new-lead")
        calls: list[int] = []

        async def _fake_create_subscription(message, tg_id, tariff, bot, **_kwargs):
            calls.append(int(tg_id))
            return True

        old_create_subscription = self.bot_module.create_subscription
        self.bot_module.create_subscription = _fake_create_subscription
        try:
            blocked = _FakeCallback(1001, data="trial_direct")
            asyncio.run(
                self.bot_module._activate_trial_tariff(
                    blocked,
                    _FakeBot(status="left"),
                    retry_callback_data="trial_direct",
                )
            )
            self.assertEqual(calls, [])
            self.assertTrue(blocked.message.edits)
            self.assertIn("прилож", blocked.message.edits[-1].lower())
            blocked_markup = blocked.message.edit_kwargs[-1].get("reply_markup")
            blocked_buttons = [button for row in blocked_markup.inline_keyboard for button in row]
            self.assertTrue(any(getattr(button, "callback_data", None) == "instruction" for button in blocked_buttons))
            self.assertFalse(any(getattr(button, "callback_data", None) in {"trial_direct", "buy_trial"} for button in blocked_buttons))

            allowed = _FakeCallback(1001, data="trial_direct")
            asyncio.run(
                self.bot_module._activate_trial_tariff(
                    allowed,
                    _FakeBot(status="member"),
                    retry_callback_data="trial_direct",
                )
            )
            self.assertEqual(calls, [])
        finally:
            self.bot_module.create_subscription = old_create_subscription

    def test_manual_subscription_variants_preserve_query_and_fragment(self) -> None:
        base = "https://connect.pokrov.space/token?existing=1#manual"
        self.assertEqual(
            self.bot_module._subscription_link_for_format(base, "happ"),
            "https://connect.pokrov.space/token?existing=1&format=happ#manual",
        )
        self.assertEqual(
            self.bot_module._subscription_link_for_format(
                "https://connect.pokrov.space/token?format=plain&existing=1",
                "happ",
            ),
            "https://connect.pokrov.space/token?existing=1&format=happ",
        )

    def test_bearer_link_handlers_refuse_group_chats(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)
        callback = _FakeCallback(1001, data="show_key")
        callback.message.chat.id = -100123

        asyncio.run(self.bot_module.show_key(callback))

        self.assertFalse(callback.message.edits)
        self.assertTrue(callback.answers)
        self.assertTrue(callback.answers[-1][1])
        self.assertIn("личном чате", callback.answers[-1][0].lower())

        for handler, data in (
            (self.bot_module.copy_key_callback, "copy_key"),
            (self.bot_module.show_qr_code, "show_qr"),
        ):
            nested = _FakeCallback(1001, data=data)
            nested.message.chat.id = -100123
            asyncio.run(handler(nested))
            self.assertTrue(nested.answers[-1][1])
            self.assertNotIn("connect.pokrov.space", nested.answers[-1][0])

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

        account_foundation_module = importlib.import_module("account_foundation_service")
        lock_calls: list[tuple[str, bool]] = []

        def _record_lock(_session, lock_key: str, *, shared: bool = False) -> None:
            lock_calls.append((str(lock_key), bool(shared)))

        with patch.object(
            account_foundation_module,
            "_acquire_postgres_advisory_lock",
            side_effect=_record_lock,
        ):
            changed = self.bot_module.sync_telegram_identity(1001, "fresh_name")
        self.assertTrue(changed)
        self.assertEqual(
            lock_calls,
            [
                ("pokrov_account_foundation_user:1001", False),
                ("pokrov_account_foundation_user:9000000000100", False),
                ("pokrov_account_foundation_backfill", False),
            ],
        )

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

    def test_friend_gift_link_waits_for_server_connection_evidence(self) -> None:
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
        self.assertEqual(reason1, "linked_waiting_evidence")
        self.assertFalse(ok2)
        self.assertEqual(reason2, "already_linked")
        self.assertEqual(calls, [])
        from models import EntitlementGrant, ReferralRelationship, User

        session = self.bot_module.Session()
        try:
            referred = session.query(User).filter_by(tg_id=1001).one()
            referrer = session.query(User).filter_by(tg_id=2002).one()
            relationship = session.query(ReferralRelationship).filter_by(referred_account_id=referred.account_id).one()
            self.assertEqual(relationship.referrer_account_id, referrer.account_id)
            self.assertEqual(session.query(EntitlementGrant).filter_by(source="referral_friend").count(), 0)
            self.assertEqual(referred.referrer_id, 2002)
        finally:
            session.close()

    def test_first_stars_payment_preserves_expiry_and_queues_72h_referral_hold(self) -> None:
        from models import EntitlementGrant, ReferralRelationship, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.ensure_pending_user(2002, username="referrer")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            referrer = session.query(User).filter_by(tg_id=2002).one()
            user.expiry_at = now + timedelta(days=5)
            user.sub_type = "FREE"
            user.current_plan_code = "trial"
            user.first_purchase_done = False
            session.add(
                EntitlementGrant(
                    id=str(uuid.uuid4()), account_id=str(user.account_id), legacy_tg_id=1001,
                    idempotency_key="stars-referral-typed-trial", source="premium_trial",
                    status="active", grant_kind="premium_trial", plan_code="trial",
                    starts_at=now, expires_at=now + timedelta(days=5), activated_at=now,
                    duration_days=5, provider="internal_economy", created_at=now, updated_at=now,
                )
            )
            referrer.expiry_at = now + timedelta(days=20)
            referrer.sub_type = "PAID"
            referrer.current_plan_code = "1_month"
            referrer.is_active = True
            session.commit()
            user_expiry_before = user.expiry_at
            referrer_expiry_before = referrer.expiry_at
        finally:
            session.close()
        self.assertTrue(self.bot_module.set_referrer(1001, 2002))

        class _Panel:
            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="first_stars_panel_token_123")

            async def update_client_traffic(self, _tg_id, _gb):
                return True

        old_panel = self.bot_module.panel
        self.bot_module.panel = _Panel()
        try:
            asyncio.run(
                self.bot_module.create_subscription(
                    _FakeMessage(),
                    1001,
                    {"stars": 299, "days": 30, "gb": 0, "subId": "1_MONTH", "sub_type": "PAID"},
                    _FakeBot(status="member"),
                    paid_amount_stars=299,
                    pay_attempt_id=501,
                )
            )
        finally:
            self.bot_module.panel = old_panel

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            referrer = session.query(User).filter_by(tg_id=2002).one()
            relationship = session.query(ReferralRelationship).filter_by(referred_account_id=user.account_id).one()
            self.assertGreaterEqual(user.expiry_at, user_expiry_before + timedelta(days=30))
            self.assertEqual(referrer.expiry_at, referrer_expiry_before)
            self.assertEqual(relationship.status, "holding")
            self.assertEqual(relationship.hold_until - relationship.first_payment_at, timedelta(hours=72))
            self.assertEqual(session.query(EntitlementGrant).filter_by(source="referral_referrer").count(), 0)
        finally:
            session.close()

    def test_paid_attempt_without_grant_replay_applies_renewal_once(self) -> None:
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "PAID"
            user.current_plan_code = "1_month"
            user.expiry_at = now + timedelta(days=10)
            user.first_purchase_done = True
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="paid", invoice_payload="portal_1_month_1001_buy_a1",
                started_at=now, updated_at=now, paid_at=now,
            )
            session.add(attempt)
            session.commit()
            attempt_id = int(attempt.id)
            original_expiry = user.expiry_at
        finally:
            session.close()

        payload = f"portal_1_month_1001_buy_a{attempt_id}"
        session = self.bot_module.Session()
        try:
            session.query(PayAttempt).filter_by(id=attempt_id).update({PayAttempt.invoice_payload: payload})
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="crash_confirmed_panel_token_123")

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs

        async def _sent(**_kwargs):
            return True

        self.bot_module.panel = panel
        self.bot_module._send_text_with_specs = _sent
        try:
            message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-crash-confirmed")
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grants = session.query(EntitlementGrant).filter_by(source="provider_payment").all()
            attempt = session.query(PayAttempt).filter_by(id=attempt_id).one()
            self.assertEqual(len(grants), 1)
            self.assertEqual(attempt.paid_at, now)
            self.assertEqual(user.expiry_at, original_expiry + timedelta(days=30))
            self.assertIn('"projection_already_applied":true', str(grants[0].metadata_json))
            self.assertEqual(panel.updates, 1)
        finally:
            session.close()

    def test_existing_stars_payment_fact_with_pending_projection_is_finished_on_replay(self) -> None:
        from economy_service import _provider_payment_key
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        charge_id = "stars-pending-projection"
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            original_expiry = user.expiry_at
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="paid", invoice_payload="portal_1_month_1001_buy_a2",
                started_at=now, updated_at=now, paid_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.add(
                EntitlementGrant(
                    id=str(uuid.uuid4()), account_id=str(user.account_id), legacy_tg_id=1001,
                    idempotency_key=_provider_payment_key("stars", charge_id), source="provider_payment",
                    status="recorded", grant_kind="payment_fact", plan_code="1_month",
                    activated_at=now, duration_days=0, provider="stars", external_order_id=charge_id,
                    metadata_json='{"is_first_payment":true,"projection_already_applied":false}',
                    created_at=now, updated_at=now,
                )
            )
            session.commit()
        finally:
            session.close()

        class _Panel:
            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="pending_projection_panel_token_123")

            async def update_client_traffic(self, _tg_id, _gb):
                return True

        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        self.bot_module.panel = _Panel()

        async def _sent(**_kwargs):
            return True

        self.bot_module._send_text_with_specs = _sent
        try:
            asyncio.run(
                self.bot_module.payment_success(
                    _FakePaymentMessage(tg_id=1001, payload=payload, charge_id=charge_id),
                    _FakeBot(status="member"),
                )
            )
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id=charge_id).one()
            self.assertEqual(grant.grant_kind, "paid_access")
            self.assertEqual(grant.duration_days, 30)
            self.assertEqual(user.expiry_at, grant.expires_at)
        finally:
            session.close()

    def test_stars_projection_survives_panel_failure_and_replay_retries_side_effect(self) -> None:
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a3",
                started_at=now, updated_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.fail = True
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="panel_retry_token_123456789")

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                if self.fail:
                    raise RuntimeError("panel unavailable")
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        self.bot_module.panel = panel

        async def _sent(**_kwargs):
            return True

        self.bot_module._send_text_with_specs = _sent
        message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-panel-retry")
        try:
            fulfillment_started_at = self.bot_module._utcnow()
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            fulfillment_finished_at = self.bot_module._utcnow()
            session = self.bot_module.Session()
            try:
                user = session.query(User).filter_by(tg_id=1001).one()
                grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-panel-retry").one()
                expiry_after_failure = user.expiry_at
                self.assertEqual(expiry_after_failure, grant.expires_at)
                self.assertGreaterEqual(
                    expiry_after_failure,
                    fulfillment_started_at + timedelta(days=30) - timedelta(seconds=1),
                )
                self.assertLessEqual(
                    expiry_after_failure,
                    fulfillment_finished_at + timedelta(days=30) + timedelta(seconds=1),
                )
                self.assertIn('"projection_already_applied":true', str(grant.metadata_json))
            finally:
                session.close()

            retry_actions = [
                button.callback_data
                for _text, kwargs in message.answers
                for row in getattr(kwargs.get("reply_markup"), "inline_keyboard", [])
                for button in row
                if str(getattr(button, "callback_data", "")).startswith("retry_stars:")
            ]
            self.assertEqual(len(retry_actions), 1)
            panel.fail = False
            asyncio.run(
                self.bot_module.retry_stars_fulfillment(
                    _FakeCallback(1001, data=str(retry_actions[0])),
                    _FakeBot(status="member"),
                )
            )
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            self.assertEqual(user.expiry_at, expiry_after_failure)
            self.assertEqual(session.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
            self.assertEqual(panel.updates, 2)
        finally:
            session.close()

    def test_existing_panel_false_update_remains_unprocessed_and_replays_without_duplicate_duration(self) -> None:
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a31",
                started_at=now, updated_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.succeed = False
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="false_then_true_panel_token_123")

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return self.succeed

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs

        async def _sent(**_kwargs):
            return True

        self.bot_module.panel = panel
        self.bot_module._send_text_with_specs = _sent
        charge_id = "stars-false-update-retry"
        first_message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id=charge_id)
        try:
            asyncio.run(self.bot_module.payment_success(first_message, _FakeBot(status="member")))
            self.assertFalse(self.bot_module._stars_payment_already_processed(charge_id))
            self.assertFalse(any("Доступ готов" in text for text, _kwargs in first_message.answers))
            retry_actions = [
                button.callback_data
                for _text, kwargs in first_message.answers
                for row in getattr(kwargs.get("reply_markup"), "inline_keyboard", [])
                for button in row
                if str(getattr(button, "callback_data", "")).startswith("retry_stars:")
            ]
            self.assertEqual(len(retry_actions), 1)
            session = self.bot_module.Session()
            try:
                expiry_after_failure = session.query(User).filter_by(tg_id=1001).one().expiry_at
            finally:
                session.close()

            panel.succeed = True
            retry_callback = _FakeCallback(1001, data=str(retry_actions[0]))
            asyncio.run(self.bot_module.retry_stars_fulfillment(retry_callback, _FakeBot(status="member")))
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id=charge_id).one()
            self.assertEqual(user.expiry_at, expiry_after_failure)
            self.assertEqual(grant.expires_at, expiry_after_failure)
            self.assertEqual(grant.duration_days, 30)
            self.assertEqual(panel.updates, 2)
            self.assertTrue(self.bot_module._stars_payment_already_processed(charge_id))
        finally:
            session.close()

    def test_completed_stars_payment_duplicate_replay_returns_without_panel_or_duration_change(self) -> None:
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow()
        session = self.bot_module.Session()
        try:
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a4",
                started_at=now, updated_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token="complete_duplicate_panel_token_123")

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        self.bot_module.panel = panel

        async def _sent(**_kwargs):
            return True

        self.bot_module._send_text_with_specs = _sent
        message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-complete-duplicate")
        try:
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            session = self.bot_module.Session()
            try:
                expiry = session.query(User).filter_by(tg_id=1001).one().expiry_at
            finally:
                session.close()
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            self.assertEqual(session.query(User).filter_by(tg_id=1001).one().expiry_at, expiry)
            self.assertEqual(session.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
            self.assertEqual(panel.updates, 1)
        finally:
            session.close()

    def test_new_panel_client_provisioning_cannot_erase_applied_stars_projection(self) -> None:
        from models import EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a5",
                started_at=now, updated_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.client = None

            async def get_existing_client(self, _tg_id):
                return dict(self.client) if self.client else None

            async def add_client(self, user_uuid, email, _sub_type, _gb, tg_id, sub_token):
                self.client = _owned_panel_client(token=sub_token, client_uuid=user_uuid)
                self.client["email"] = email
                self.client["tgId"] = str(tg_id)
                return True

        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        self.bot_module.panel = _Panel()

        async def _sent(**_kwargs):
            return True

        self.bot_module._send_text_with_specs = _sent
        try:
            asyncio.run(
                self.bot_module.payment_success(
                    _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-new-panel-client"),
                    _FakeBot(status="member"),
                )
            )
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-new-panel-client").one()
            self.assertEqual(user.expiry_at, grant.expires_at)
            self.assertEqual(user.sub_type, "PAID")
            self.assertEqual(grant.expires_at - grant.starts_at, timedelta(days=30))
        finally:
            session.close()

    def test_add_client_success_then_local_reconcile_failure_replays_exact_panel_credentials(self) -> None:
        from models import AccessKey, EntitlementGrant, Node, PayAttempt, User, UserNode

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a6",
                started_at=now, updated_at=now,
            )
            session.add_all(
                [
                    attempt,
                    Node(
                        id=77,
                        code="NL-test",
                        name="NL test",
                        enabled=True,
                        accepting_new_clients=True,
                    ),
                ]
            )
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.client = None
                self.adds = 0
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return dict(self.client) if self.client else None

            async def add_client(self, user_uuid, email, _sub_type, _gb, tg_id, sub_token):
                self.adds += 1
                self.client = _owned_panel_client(
                    token=sub_token,
                    client_uuid=user_uuid,
                    node_id=77,
                )
                self.client["email"] = email
                self.client["tgId"] = str(tg_id)
                return True

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        original_reconcile = getattr(self.bot_module, "_reconcile_owned_panel_client", None)
        reconcile_calls = 0

        def _fail_first_reconcile(*args, **kwargs):
            nonlocal reconcile_calls
            reconcile_calls += 1
            if reconcile_calls == 1:
                raise RuntimeError("forced local credential commit failure")
            if original_reconcile is None:
                raise AssertionError("missing credential reconciliation")
            return original_reconcile(*args, **kwargs)

        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        old_reconcile = getattr(self.bot_module, "_reconcile_owned_panel_client", None)
        self.bot_module.panel = panel
        self.bot_module._reconcile_owned_panel_client = _fail_first_reconcile

        async def _sent(**_kwargs):
            return True

        self.bot_module._send_text_with_specs = _sent
        message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-local-reconcile-retry")
        try:
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            session = self.bot_module.Session()
            try:
                grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-local-reconcile-retry").one()
                expiry_after_failure = grant.expires_at
                self.assertEqual(session.query(User).filter_by(tg_id=1001).one().expiry_at, expiry_after_failure)
            finally:
                session.close()

            retry_actions = [
                button.callback_data
                for _text, kwargs in message.answers
                for row in getattr(kwargs.get("reply_markup"), "inline_keyboard", [])
                for button in row
                if str(getattr(button, "callback_data", "")).startswith("retry_stars:")
            ]
            self.assertEqual(len(retry_actions), 1)
            asyncio.run(
                self.bot_module.retry_stars_fulfillment(
                    _FakeCallback(1001, data=str(retry_actions[0])),
                    _FakeBot(status="member"),
                )
            )
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send
            if old_reconcile is None:
                delattr(self.bot_module, "_reconcile_owned_panel_client")
            else:
                self.bot_module._reconcile_owned_panel_client = old_reconcile

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-local-reconcile-retry").one()
            key = session.query(AccessKey).filter_by(tg_id=1001, node_code="NL-test").one()
            node = session.query(UserNode).filter_by(tg_id=1001, node_id=77).one()
            self.assertEqual(user.uuid, panel.client["id"])
            self.assertEqual(user.email, panel.client["email"])
            self.assertEqual(user.sub_token, panel.client["subId"])
            self.assertTrue(self.bot_module.build_subscription_link(1001).endswith(f"/{panel.client['subId']}"))
            self.assertEqual(key.key_uuid, panel.client["id"])
            self.assertEqual(key.panel_email, panel.client["email"])
            self.assertEqual(node.client_uuid, panel.client["id"])
            self.assertEqual(node.panel_email, panel.client["email"])
            self.assertEqual(user.expiry_at, expiry_after_failure)
            self.assertEqual(grant.expires_at, expiry_after_failure)
            self.assertEqual(panel.adds, 1)
            self.assertEqual(reconcile_calls, 2)
        finally:
            session.close()

    def test_marker_failure_replay_reconciles_existing_panel_client_without_duplicate_duration(self) -> None:
        from models import AccessKey, EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_token = "different_local_token_123"
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a7",
                started_at=now, updated_at=now,
            )
            session.add_all(
                [
                    attempt,
                    AccessKey(
                        tg_id=1001,
                        key_uuid="87654321-4321-4321-8321-cba987654321",
                        panel_email="User_1001",
                        node_code="NL-test",
                        pool_code="free_pool",
                        state="active",
                        source="legacy_user",
                        is_primary=True,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        panel_token = "exact_panel_token_123456789"

        class _Panel:
            def __init__(self):
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(token=panel_token)

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs
        original_marker = self.bot_module._mark_stars_payment_processed
        marker_calls = 0

        def _drop_first_marker(**kwargs):
            nonlocal marker_calls
            marker_calls += 1
            if marker_calls > 1:
                original_marker(**kwargs)

        async def _sent(**_kwargs):
            return True

        self.bot_module.panel = panel
        self.bot_module._send_text_with_specs = _sent
        self.bot_module._mark_stars_payment_processed = _drop_first_marker
        message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-marker-retry")
        try:
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            session = self.bot_module.Session()
            try:
                first_expiry = session.query(User).filter_by(tg_id=1001).one().expiry_at
            finally:
                session.close()
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send
            self.bot_module._mark_stars_payment_processed = original_marker

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-marker-retry").one()
            key = session.query(AccessKey).filter_by(tg_id=1001, node_code="NL-test").one()
            self.assertEqual(user.sub_token, panel_token)
            self.assertEqual(key.key_uuid, "12345678-1234-4234-9234-123456789abc")
            self.assertEqual(user.expiry_at, first_expiry)
            self.assertEqual(grant.expires_at, first_expiry)
            self.assertEqual(grant.duration_days, 30)
            self.assertEqual(panel.updates, 2)
            self.assertEqual(marker_calls, 2)
        finally:
            session.close()

    def test_legacy_panel_lane_without_db_node_id_reconciles_and_replays_idempotently(self) -> None:
        from models import AccessKey, EntitlementGrant, PayAttempt, User, UserNode

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a8",
                started_at=now, updated_at=now,
            )
            session.add(attempt)
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        panel_token = "legacy_lane_exact_token_123456"

        class _Panel:
            def __init__(self):
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(
                    token=panel_token,
                    node_code="legacy-nl",
                    node_id=0,
                )

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        old_send = self.bot_module._send_text_with_specs

        async def _sent(**_kwargs):
            return True

        self.bot_module.panel = panel
        self.bot_module._send_text_with_specs = _sent
        message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id="stars-legacy-panel-lane")
        try:
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
            session = self.bot_module.Session()
            try:
                first_expiry = session.query(User).filter_by(tg_id=1001).one().expiry_at
            finally:
                session.close()
            asyncio.run(self.bot_module.payment_success(message, _FakeBot(status="member")))
        finally:
            self.bot_module.panel = old_panel
            self.bot_module._send_text_with_specs = old_send

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id="stars-legacy-panel-lane").one()
            key = session.query(AccessKey).filter_by(tg_id=1001, node_code="legacy-nl").one()
            self.assertEqual(user.sub_token, panel_token)
            self.assertEqual(key.key_uuid, user.uuid)
            self.assertEqual(session.query(UserNode).filter_by(tg_id=1001).count(), 0)
            self.assertEqual(user.expiry_at, first_expiry)
            self.assertEqual(grant.expires_at, first_expiry)
            self.assertEqual(grant.duration_days, 30)
            self.assertEqual(panel.updates, 1)
        finally:
            session.close()

    def test_panel_client_without_node_id_or_node_code_remains_retryable_failure(self) -> None:
        with self.assertRaisesRegex(ValueError, "node"):
            self.bot_module._validated_owned_panel_client(
                tg_id=1001,
                panel_client=_owned_panel_client(
                    token="missing_lane_identity_token_123",
                    node_code="",
                    node_id=0,
                ),
            )

    def test_access_key_node_provenance_mismatch_is_retryable_without_duplicate_duration(self) -> None:
        from models import AccessKey, EntitlementGrant, PayAttempt, User

        self.bot_module.ensure_pending_user(1001, username="alice")
        now = self.bot_module._utcnow().replace(microsecond=0)
        client_uuid = "12345678-1234-4234-9234-123456789abc"
        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            user.sub_type = "FREE"
            user.current_plan_code = "free_monthly"
            user.expiry_at = now
            attempt = PayAttempt(
                tg_id=1001, source="bot", plan_code="1_month", amount_stars=299,
                currency="XTR", status="invoice_sent", invoice_payload="portal_1_month_1001_buy_a32",
                started_at=now, updated_at=now,
            )
            session.add_all(
                [
                    attempt,
                    AccessKey(
                        tg_id=1001,
                        key_uuid=client_uuid,
                        panel_email="User_1001",
                        node_code="conflicting-node",
                        pool_code="free_pool",
                        state="active",
                        source="legacy_user",
                        is_primary=True,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            session.flush()
            payload = f"portal_1_month_1001_buy_a{attempt.id}"
            attempt.invoice_payload = payload
            session.commit()
        finally:
            session.close()

        class _Panel:
            def __init__(self):
                self.updates = 0

            async def get_existing_client(self, _tg_id):
                return _owned_panel_client(
                    token="provenance_mismatch_token_123",
                    client_uuid=client_uuid,
                    node_code="NL-test",
                    node_id=0,
                )

            async def update_client_traffic(self, _tg_id, _gb):
                self.updates += 1
                return True

        panel = _Panel()
        old_panel = self.bot_module.panel
        self.bot_module.panel = panel
        charge_id = "stars-provenance-mismatch"
        first_message = _FakePaymentMessage(tg_id=1001, payload=payload, charge_id=charge_id)
        try:
            asyncio.run(self.bot_module.payment_success(first_message, _FakeBot(status="member")))
            retry_actions = [
                button.callback_data
                for _text, kwargs in first_message.answers
                for row in getattr(kwargs.get("reply_markup"), "inline_keyboard", [])
                for button in row
                if str(getattr(button, "callback_data", "")).startswith("retry_stars:")
            ]
            self.assertEqual(len(retry_actions), 1)
            session = self.bot_module.Session()
            try:
                key = session.query(AccessKey).filter_by(tg_id=1001, key_uuid=client_uuid).one()
                key.node_code = "NL-test"
                session.commit()
            finally:
                session.close()
            asyncio.run(
                self.bot_module.retry_stars_fulfillment(
                    _FakeCallback(1001, data=str(retry_actions[0])),
                    _FakeBot(status="member"),
                )
            )
        finally:
            self.bot_module.panel = old_panel

        session = self.bot_module.Session()
        try:
            user = session.query(User).filter_by(tg_id=1001).one()
            grant = session.query(EntitlementGrant).filter_by(external_order_id=charge_id).one()
            self.assertEqual(session.query(EntitlementGrant).filter_by(external_order_id=charge_id).count(), 1)
            self.assertEqual(user.expiry_at, grant.expires_at)
            self.assertEqual(grant.duration_days, 30)
            self.assertEqual(panel.updates, 1)
            self.assertTrue(self.bot_module._stars_payment_already_processed(charge_id))
        finally:
            session.close()

    def test_friend_link_does_not_call_subscription_or_burn_campaign_claim(self) -> None:
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

        old_create_subscription = self.bot_module.create_subscription
        try:
            msg = _Msg(bot=_FakeBot(status="member"))
            self.bot_module.create_subscription = _failing_create_subscription
            ok, reason = asyncio.run(
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
            replay_ok, replay_reason = asyncio.run(
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
        self.assertEqual(reason, "linked_waiting_evidence")
        self.assertFalse(replay_ok)
        self.assertEqual(replay_reason, "already_linked")

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
        for item in tracked:
            meta = item["meta"]
            self.assertNotIn("code", meta)
            self.assertEqual(meta["code_preview"], f"...{gift_code[-4:]}")
            self.assertEqual(meta["code_fp"], hashlib.sha256(gift_code.encode("utf-8")).hexdigest()[:16])
            self.assertEqual(meta["code_len"], len(gift_code))

    def test_gift_event_persistence_never_contains_raw_activation_code(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        self.bot_module.set_tos_accepted(1001)
        code = self.bot_module.create_gift_card(2002, "standard")
        self.assertTrue(code)

        ok, _message = asyncio.run(self.bot_module.redeem_gift_card(code, 1001, _FakeBot(status="member")))
        denied, _denied_message = asyncio.run(self.bot_module.redeem_gift_card(code, 1001, _FakeBot(status="member")))
        self.assertTrue(ok)
        self.assertFalse(denied)

        session = self.bot_module.Session()
        try:
            rows = (
                session.query(self.bot_module.Event)
                .filter(self.bot_module.Event.event_name.in_(["gift_redeemed", "gift_redeem_denied"]))
                .order_by(self.bot_module.Event.id.asc())
                .all()
            )
            self.assertEqual([row.event_name for row in rows], ["gift_redeemed", "gift_redeem_denied"])
            for row in rows:
                raw_meta = str(row.meta_json or "")
                meta = json.loads(raw_meta)
                self.assertFalse(code in raw_meta)
                self.assertNotIn("code", meta)
                self.assertEqual(meta["code_preview"], f"...{code[-4:]}")
                self.assertEqual(meta["code_fp"], hashlib.sha256(code.encode("utf-8")).hexdigest()[:16])
                self.assertEqual(meta["code_len"], len(code))
        finally:
            session.close()

    def test_wrong_account_payment_fallback_denial_event_is_redacted(self) -> None:
        from account_foundation_service import ensure_user_account_foundation
        from payment_entitlement_service import ensure_fallback_gift_card, ensure_pending_claim, mark_paid

        for tg_id, username in ((1001, "owner"), (1002, "wrong")):
            self.bot_module.ensure_pending_user(tg_id, username=username)
            self.bot_module.set_tos_accepted(tg_id)
        code = "POKROV-" + "PAYMENT" + "-DENY"
        session = self.bot_module.Session()
        try:
            owner = session.query(self.bot_module.User).filter_by(tg_id=1001).one()
            wrong = session.query(self.bot_module.User).filter_by(tg_id=1002).one()
            ensure_user_account_foundation(session, owner, now=self.bot_module._utcnow())
            ensure_user_account_foundation(session, wrong, now=self.bot_module._utcnow())
            claim = ensure_pending_claim(
                session,
                provider="lavatop",
                order_id="bot-wrong-account",
                buyer_email="owner@example.test",
                plan_code="1_month",
                duration_days=30,
                now=self.bot_module._utcnow(),
            ).claim
            mark_paid(session, provider="lavatop", order_id="bot-wrong-account", paid_at=self.bot_module._utcnow())
            ensure_fallback_gift_card(
                session,
                provider="lavatop",
                order_id="bot-wrong-account",
                gift_code=code,
                now=self.bot_module._utcnow(),
            )
            claim.account_id = str(owner.account_id)
            claim.status = "paid_attached"
            session.commit()
        finally:
            session.close()

        ok, _message = asyncio.run(self.bot_module.redeem_gift_card(code, 1002, _FakeBot(status="member")))
        self.assertFalse(ok)
        session = self.bot_module.Session()
        try:
            event = (
                session.query(self.bot_module.Event)
                .filter_by(tg_id=1002, event_name="gift_redeem_denied")
                .order_by(self.bot_module.Event.id.desc())
                .first()
            )
            self.assertIsNotNone(event)
            raw_meta = str(event.meta_json or "")
            meta = json.loads(raw_meta)
            self.assertFalse(code in raw_meta)
            self.assertNotIn("code", meta)
            self.assertEqual(meta["reason"], "payment_account_conflict")
            self.assertEqual(meta["code_preview"], f"...{code[-4:]}")
            self.assertEqual(meta["code_fp"], hashlib.sha256(code.encode("utf-8")).hexdigest()[:16])
            self.assertEqual(meta["code_len"], len(code))
        finally:
            session.close()

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

    def test_direct_gift_recipient_receives_canonical_account(self) -> None:
        code = "POKROV-DIRECT-GIFT-ACCOUNT"
        recipient_tg_id = 31001
        session = self.bot_module.Session()
        try:
            session.add(self.bot_module.GiftCard(code=code, card_type="standard", created_by=2002))
            session.commit()
        finally:
            session.close()

        class _Panel:
            async def login(self):
                return True

            async def get_existing_client(self, _tg_id):
                return None

            async def add_client(self, *_args, **_kwargs):
                return True

            async def close(self):
                return None

        with patch("control_panel.ControlPanel", _Panel):
            result = asyncio.run(
                self.bot_module.redeem_gift_card_service(
                    code=code,
                    recipient_tg_id=recipient_tg_id,
                    require_tos=False,
                )
            )

        self.assertTrue(result["ok"], result)
        session = self.bot_module.Session()
        try:
            recipient = session.query(self.bot_module.User).filter_by(tg_id=recipient_tg_id).one()
            self.assertTrue(recipient.account_id)
        finally:
            session.close()

    def test_app_link_bind_merges_canonical_accounts_before_returning(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="telegram_owner")
        app_tg_id = 9_000_000_000_102
        start_code = "app_link_account_merge_102"
        session = self.bot_module.Session()
        try:
            app_user = self.bot_module.User(
                tg_id=app_tg_id,
                username="app_000102",
                uuid=str(uuid.uuid4()),
                email=f"APP_{app_tg_id}",
                sub_type="FREE",
                current_plan_code="trial",
                is_active=True,
                is_app_user=True,
                app_install_id="install-bind-merge-102",
                sub_token="linked_token_102",
            )
            session.add(app_user)
            self.bot_module.ensure_user_account_foundation(session, app_user)
            session.add(
                self.bot_module.StartLink(
                    code=start_code,
                    target_action=f"link_account:{app_tg_id}",
                    is_active=True,
                )
            )
            session.commit()
            telegram_user = session.query(self.bot_module.User).filter_by(tg_id=1001).one()
            session.refresh(app_user)
            self.assertNotEqual(str(telegram_user.account_id), str(app_user.account_id))
        finally:
            session.close()

        account_foundation_module = importlib.import_module("account_foundation_service")
        lock_calls: list[tuple[str, bool]] = []

        def _record_lock(_session, lock_key: str, *, shared: bool = False) -> None:
            lock_calls.append((str(lock_key), bool(shared)))

        with patch.object(
            account_foundation_module,
            "_acquire_postgres_advisory_lock",
            side_effect=_record_lock,
        ):
            result = self.bot_module._bind_app_account_to_telegram(
                account_tg_id=app_tg_id,
                telegram_id=1001,
                telegram_username="telegram_owner",
                start_code=start_code,
            )

        self.assertEqual(result, "linked")
        self.assertEqual(
            lock_calls,
            [
                ("pokrov_account_foundation_user:1001", False),
                (f"pokrov_account_foundation_user:{app_tg_id}", False),
                ("pokrov_account_foundation_backfill", False),
            ],
        )
        session = self.bot_module.Session()
        try:
            telegram_user = session.query(self.bot_module.User).filter_by(tg_id=1001).one()
            app_user = session.query(self.bot_module.User).filter_by(tg_id=app_tg_id).one()
            link = session.query(self.bot_module.StartLink).filter_by(code=start_code).one()
            self.assertEqual(str(app_user.account_id), str(telegram_user.account_id))
            self.assertEqual(app_user.linked_telegram_id, 1001)
            self.assertFalse(link.is_active)
        finally:
            session.close()

        self.bot_module.ensure_pending_user(2002, username="replay_attempt")
        replay = self.bot_module._bind_app_account_to_telegram(
            account_tg_id=app_tg_id,
            telegram_id=2002,
            telegram_username="replay_attempt",
            start_code=start_code,
        )
        self.assertEqual(replay, "expired")
        session = self.bot_module.Session()
        try:
            app_user = session.query(self.bot_module.User).filter_by(tg_id=app_tg_id).one()
            self.assertEqual(app_user.linked_telegram_id, 1001)
        finally:
            session.close()

    def test_app_link_bind_requires_both_user_endpoints_and_keeps_link_unused(self) -> None:
        app_tg_id = 9_000_000_000_103
        missing_telegram_id = 1003
        start_code = "app_link_missing_telegram_103"
        session = self.bot_module.Session()
        try:
            app_user = self.bot_module.User(
                tg_id=app_tg_id,
                username="app_000103",
                uuid=str(uuid.uuid4()),
                email=f"APP_{app_tg_id}",
                sub_type="FREE",
                current_plan_code="trial",
                is_active=True,
                is_app_user=True,
                app_install_id="install-bind-missing-telegram-103",
                sub_token="linked_token_103",
            )
            session.add(app_user)
            self.bot_module.ensure_user_account_foundation(session, app_user)
            session.add(
                self.bot_module.StartLink(
                    code=start_code,
                    target_action=f"link_account:{app_tg_id}",
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        result = self.bot_module._bind_app_account_to_telegram(
            account_tg_id=app_tg_id,
            telegram_id=missing_telegram_id,
            telegram_username="missing_owner",
            start_code=start_code,
        )

        self.assertEqual(result, "not_found")
        session = self.bot_module.Session()
        try:
            app_user = session.query(self.bot_module.User).filter_by(tg_id=app_tg_id).one()
            link = session.query(self.bot_module.StartLink).filter_by(code=start_code).one()
            self.assertIsNone(app_user.linked_telegram_id)
            self.assertTrue(link.is_active)
        finally:
            session.close()

    def test_manual_bot_user_receives_canonical_account_immediately(self) -> None:
        user = self.bot_module.create_manual_user_record(
            display_name="Offline owner",
            days=30,
            created_by_admin=9999,
        )

        self.assertTrue(user.account_id)
        session = self.bot_module.Session()
        try:
            stored = session.query(self.bot_module.User).filter_by(tg_id=int(user.tg_id)).one()
            self.assertEqual(str(stored.account_id), str(user.account_id))
        finally:
            session.close()

    def test_app_link_bind_rejects_transitive_account_chain(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="first_telegram")
        self.bot_module.ensure_pending_user(2002, username="second_telegram")
        app_tg_id = 9_000_000_000_701
        start_code = "app_link_transitive_rejected_701"
        session = self.bot_module.Session()
        try:
            first_app = self.bot_module.User(
                tg_id=app_tg_id,
                username="app_000701",
                uuid=str(uuid.uuid4()),
                email=f"APP_{app_tg_id}",
                sub_type="FREE",
                current_plan_code="trial",
                is_active=True,
                is_app_user=True,
                app_install_id="install-transitive-701",
                linked_telegram_id=1001,
                linked_telegram_linked_at=self.bot_module._utcnow(),
                sub_token="linked_token_701",
            )
            session.add(first_app)
            self.bot_module.ensure_user_account_foundation(session, first_app)
            session.add(
                self.bot_module.StartLink(
                    code=start_code,
                    target_action="link_account:1001",
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        result = self.bot_module._bind_app_account_to_telegram(
            account_tg_id=1001,
            telegram_id=2002,
            telegram_username="second_telegram",
            start_code=start_code,
        )

        self.assertEqual(result, "transitive_link_not_supported")
        session = self.bot_module.Session()
        try:
            first_telegram = session.query(self.bot_module.User).filter_by(tg_id=1001).one()
            second_telegram = session.query(self.bot_module.User).filter_by(tg_id=2002).one()
            link = session.query(self.bot_module.StartLink).filter_by(code=start_code).one()
            self.assertIsNone(first_telegram.linked_telegram_id)
            self.assertNotEqual(str(first_telegram.account_id), str(second_telegram.account_id))
            self.assertTrue(link.is_active)
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
        old_catalog = self.bot_module.enabled_public_provider_catalog
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_public_provider_catalog = lambda plan_code=None: [
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="3_months")
        finally:
            self.bot_module.enabled_public_provider_catalog = old_catalog
        self.assertEqual(keyboard.inline_keyboard[0][0].text, "💳 Lava.top · 699 ₽")
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:lavatop:3_months")
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
        callback = _FakeCallback(1001, data="pay_rub:lavatop:1_month")

        old_catalog = self.bot_module.enabled_public_provider_catalog

        async def _fake_create_payment_link(*, provider, tg_id, tariff_key):
            self.assertEqual(str(provider), "lavatop")
            self.assertEqual(int(tg_id), 1001)
            self.assertEqual(str(tariff_key), "1_month")
            return {
                "order_id": "lavatop_bot_1001_test",
                "payment_url": "https://checkout.lava.top/pay/test",
            }

        old_create = self.bot_module._create_rub_payment_link_for_bot
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_public_provider_catalog = lambda plan_code=None: [
                {"code": "lavatop", "label": "Lava.top", "supports_bot": True},
            ]
            self.bot_module._create_rub_payment_link_for_bot = _fake_create_payment_link
            asyncio.run(self.bot_module.process_buy_rub(callback, _FakeBot(status="member")))
        finally:
            self.bot_module._create_rub_payment_link_for_bot = old_create
            self.bot_module.enabled_public_provider_catalog = old_catalog

        self.assertTrue(callback.message.edits)
        self.assertIn("Следующий шаг: откройте оплату", callback.message.edits[-1])
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        self.assertEqual(reply_markup.inline_keyboard[0][0].url, "https://checkout.lava.top/pay/test")
        self.assertEqual(callback.answers[-1], ("Ссылка на оплату готова", False))

    def test_tariff_payment_choice_keyboard_is_lava_only_and_plan_ready(self) -> None:
        old_catalog = self.bot_module.enabled_public_provider_catalog
        try:
            self.bot_module.RUB_CHECKOUT_ENABLED = True
            self.bot_module.PAID_CHECKOUT_LAUNCH_APPROVED = True
            self.bot_module.enabled_public_provider_catalog = lambda plan_code=None: (
                [{"code": "lavatop", "label": "Lava.top", "supports_bot": True}]
                if plan_code == "1_month"
                else []
            )
            keyboard = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="1_month")
            unsupported = self.bot_module._build_tariff_payment_choice_keyboard(tg_id=1001, tariff_key="3_months")
        finally:
            self.bot_module.enabled_public_provider_catalog = old_catalog

        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "pay_rub:lavatop:1_month")
        self.assertFalse(
            any(
                str(getattr(button, "callback_data", "") or "").startswith("pay_rub")
                for row in unsupported.inline_keyboard
                for button in row
            )
        )
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
        self.assertIsNone(getattr(buttons["back"], "style", None))

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
        text = self.bot_module.build_choose_tariff_text(show_trial=True)
        self.assertIn("5 дней", text)
        self.assertIn("бесплатно", text.lower())
        self.assertIn("5 ГБ", text)
        self.assertNotIn("Stars", text)
        self.assertNotIn("⭐", text)

        returning_text = self.bot_module.build_choose_tariff_text(show_trial=False)
        self.assertNotIn("5 дней бесплатно", returning_text.lower())
        self.assertNotIn("бесплатный старт", returning_text.lower())

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

    def test_main_menu_cta_does_not_offer_unavailable_checkout_or_repeat_trial(self) -> None:
        with patch.object(self.bot_module, "_bot_checkout_blocked_reasons", return_value=["blocked"]):
            with patch.object(self.bot_module, "TELEGRAM_STARS_CHECKOUT_ENABLED", True):
                with patch.object(self.bot_module, "get_user", return_value=None):
                    self.assertEqual(self.bot_module._main_menu_cta_spec(1001)["callback_data"], "instruction")

            used_trial = types.SimpleNamespace(
                is_active=False,
                expiry_at=None,
                sub_type="FREE",
                trial_used=True,
            )
            with patch.object(self.bot_module, "get_user", return_value=used_trial):
                self.assertEqual(self.bot_module._main_menu_cta_spec(1001)["callback_data"], "gift_redeem_prompt")

            active_paid = types.SimpleNamespace(
                is_active=True,
                expiry_at=self.bot_module._utcnow() + timedelta(days=30),
                sub_type="PAID",
                trial_used=False,
            )
            with patch.object(self.bot_module, "get_user", return_value=active_paid):
                self.assertEqual(self.bot_module._main_menu_cta_spec(1001)["callback_data"], "gift_redeem_prompt")

        with patch.object(self.bot_module, "_bot_checkout_blocked_reasons", return_value=[]):
            self.assertEqual(self.bot_module._main_menu_cta_spec(1001)["callback_data"], "charge")

    def test_help_command_opens_faq_menu(self) -> None:
        message = _FakeMessage()
        message.from_user = _FakeUser(1001)
        with patch.object(self.bot_module, "_track_bot_entry") as track:
            asyncio.run(self.bot_module.help_command(message))

        self.assertIn("Частые вопросы", message.answers[-1][0])
        self.assertIsNotNone(message.answers[-1][1].get("reply_markup"))
        track.assert_called_once()

    def test_manual_link_flow_uses_native_copy_button_without_fake_delay_or_karing(self) -> None:
        source = inspect.getsource(self.bot_module.show_key)
        self.assertIn("_subscription_copy_button(", source)
        self.assertIn("value=sub_link", source)
        self.assertNotIn("asyncio.sleep", source)
        self.assertNotIn("Karing", source)

        button = self.bot_module._subscription_copy_button(
            label="📋 Скопировать ссылку",
            value="https://connect.pokrov.space/example",
            fallback_callback="copy_key",
        )
        if self.bot_module.SUPPORTS_BTN_COPY_TEXT:
            self.assertEqual(getattr(getattr(button, "copy_text", None), "text", None), "https://connect.pokrov.space/example")
        else:
            self.assertEqual(button.callback_data, "copy_key")

    def test_reset_link_copy_is_honest_about_imported_profiles_and_has_no_fake_delay(self) -> None:
        menu_source = inspect.getsource(self.bot_module.panic_menu)
        execute_source = inspect.getsource(self.bot_module.panic_execute)

        self.assertNotIn("asyncio.sleep", execute_source)
        self.assertNotIn("потеряли устройство", menu_source)
        self.assertNotIn("старая ссылка перестанет работать", menu_source.lower())
        self.assertIn("импорт", menu_source.lower())
        self.assertIn("поддерж", menu_source.lower())
        self.assertIn("импорт", execute_source.lower())

    def test_admin_trial_gift_matches_five_day_canonical_trial(self) -> None:
        source = inspect.getsource(self.bot_module.admin_gift)
        self.assertIn('"trial": {"days": 5', source)
        self.assertNotIn("Пробный (7 дней)", source)

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
        self.assertIn("❓ Частые вопросы", labels)

    def test_faq_menu_lists_every_answer_topic(self) -> None:
        callback = _FakeCallback(1001, data="faqmenu")

        asyncio.run(self.bot_module.show_faq_menu(callback))

        final_text = callback.message.edits[-1]
        self.assertIn("Частые вопросы", final_text)
        reply_markup = callback.message.edit_kwargs[-1]["reply_markup"]
        callbacks = [
            str(getattr(button, "callback_data", "") or "")
            for row in reply_markup.inline_keyboard
            for button in row
        ]
        menu_keys = {key for key, _label in self.bot_module.FAQ_MENU_ITEMS}
        for key in menu_keys:
            self.assertIn(f"faq_{key}", callbacks)
            self.assertIn(key, self.bot_module.FAQ_ANSWERS)
        self.assertEqual(menu_keys, set(self.bot_module.FAQ_ANSWERS))

    def test_faq_answers_do_not_leak_raw_links_or_stars(self) -> None:
        for key, answer in self.bot_module.FAQ_ANSWERS.items():
            with self.subTest(faq=key):
                self.assertNotIn("connect.pokrov.space", answer)
                self.assertNotIn("Stars", answer)
                self.assertNotIn("⭐", answer)

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
            [(item["command"], item["description"]) for item in self.bot_module.expected_public_command_payload()],
        )
        self.assertEqual(getattr(fake.menu_button, "text", ""), "POKROV")
        self.assertEqual(getattr(getattr(fake.menu_button, "web_app", None), "url", ""), "https://app.pokrov.space/")

    def test_bot_entry_tracking_uses_safe_metadata(self) -> None:
        tracked = []

        def _fake_track_event(**kwargs):
            tracked.append(kwargs)

        old_track_event = self.bot_module.track_event
        try:
            self.bot_module.track_event = _fake_track_event
            self.bot_module._track_bot_entry(
                tg_id=1001,
                entrypoint="start",
                meta={
                    "created_new": True,
                    "start_arg_present": True,
                    "start_arg_kind": "campaign",
                    "raw_start_arg": "campaign_SECRET",
                },
            )
        finally:
            self.bot_module.track_event = old_track_event

        self.assertEqual(len(tracked), 1)
        self.assertEqual(tracked[0]["event_name"], "bot_entry_opened")
        self.assertEqual(tracked[0]["source"], "bot")
        self.assertEqual(tracked[0]["meta"]["entrypoint"], "start")
        self.assertEqual(tracked[0]["meta"]["start_arg_kind"], "campaign")
        self.assertNotIn("raw_start_arg", tracked[0]["meta"])

    def test_start_arg_analytics_classification(self) -> None:
        classify = self.bot_module._classify_start_arg_for_analytics

        self.assertEqual(classify(start_arg=""), "plain")
        self.assertEqual(classify(start_arg="SWAZ1234", referral_code="SWAZ1234"), "referral")
        self.assertEqual(classify(start_arg="promo_HELLO", deeplink_promo_code="HELLO"), "promo")
        self.assertEqual(classify(start_arg="campaign_ru", deeplink_campaign_key="ru"), "campaign")
        self.assertEqual(
            classify(start_arg="campaign_ru__promo_HELLO", deeplink_promo_code="HELLO", deeplink_campaign_key="ru"),
            "campaign_promo",
        )
        self.assertEqual(classify(start_arg="gift3_ABC123", friend_gift_referral_code="ABC123"), "friend_gift")
        self.assertEqual(classify(start_arg="launch14", opening_bonus_requested=True), "opening_bonus")
        self.assertEqual(classify(start_arg="app", app_link_account_id=1001), "app_link")
        self.assertEqual(classify(start_arg="pay"), "payment")
        self.assertEqual(classify(start_arg="renew"), "payment")

    def test_reserved_payment_start_cannot_be_intercepted_by_dynamic_start_link(self) -> None:
        session = self.bot_module.Session()
        try:
            session.add(
                self.bot_module.StartLink(
                    code="pay",
                    target_action="app_link:9000000000101",
                    is_active=True,
                )
            )
            session.commit()
        finally:
            session.close()

        class _StartBot:
            async def delete_message(self, *_args, **_kwargs):
                return None

        class _StartMessage(_FakeMessage):
            def __init__(self):
                super().__init__()
                self.from_user = types.SimpleNamespace(id=1001, username="alice")
                self.text = "/start pay"
                self.bot = _StartBot()

            async def delete(self):
                return None

        async def _no_panel_user(_tg_id):
            return None

        bind_calls: list[int] = []

        def _bind(**kwargs):
            bind_calls.append(int(kwargs["account_tg_id"]))
            return "linked"

        with patch.object(self.bot_module.panel, "get_existing_client", new=_no_panel_user):
            with patch.object(self.bot_module, "_bind_app_account_to_telegram", side_effect=_bind):
                tos_message = _StartMessage()
                asyncio.run(self.bot_module.cmd_start(tos_message))
                self.assertIn("услов", tos_message.answers[-1][0].lower())
                self.assertEqual(bind_calls, [])

                self.bot_module.set_tos_accepted(1001)
                tariff_message = _StartMessage()
                asyncio.run(self.bot_module.cmd_start(tariff_message))

        self.assertEqual(bind_calls, [])
        self.assertIn("с чего начнём", tariff_message.answers[-1][0].lower())
        markup = tariff_message.answers[-1][1]["reply_markup"]
        callbacks = {
            str(getattr(button, "callback_data", "") or "")
            for row in markup.inline_keyboard
            for button in row
        }
        self.assertIn("charge_long", callbacks)

    def test_stars_creation_and_precheckout_stay_closed_even_if_legacy_flag_is_true(self) -> None:
        callback = _FakeCallback(1001, data="pay_stars_1_month")

        class _InvoiceBot:
            def __init__(self):
                self.invoices = []
                self.precheckout = []

            async def send_invoice(self, **kwargs):
                self.invoices.append(kwargs)

            async def answer_pre_checkout_query(self, query_id, **kwargs):
                self.precheckout.append((query_id, kwargs))

        bot = _InvoiceBot()
        with patch.object(self.bot_module, "TELEGRAM_STARS_CHECKOUT_ENABLED", True):
            asyncio.run(self.bot_module.process_buy_stars(callback, bot))
            query = types.SimpleNamespace(id="legacy-precheckout")
            asyncio.run(self.bot_module.pre_checkout_handler(query, bot))

        self.assertEqual(bot.invoices, [])
        self.assertEqual(bot.precheckout[0][0], "legacy-precheckout")
        self.assertFalse(bot.precheckout[0][1]["ok"])

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

    def _seed_paid_reward_authority(self, *tg_ids: int) -> str:
        from models import EntitlementGrant

        for tg_id in tg_ids:
            self.bot_module.ensure_pending_user(tg_id, username=f"user_{tg_id}")
        session = self.bot_module.Session()
        try:
            users = [session.query(self.bot_module.User).filter_by(tg_id=tg_id).one() for tg_id in tg_ids]
            account_id = str(users[0].account_id)
            now = self.bot_module._utcnow()
            for user in users:
                user.account_id = account_id
                user.sub_type = "PAID"
                user.current_plan_code = "month"
                user.is_active = True
                user.first_purchase_done = True
                user.expiry_at = now + timedelta(days=30)
            session.add(
                EntitlementGrant(
                    id=str(uuid.uuid4()),
                    account_id=account_id,
                    legacy_tg_id=tg_ids[0],
                    idempotency_key=f"test-provider-payment:{account_id}",
                    source="provider_payment",
                    status="active",
                    grant_kind="paid_access",
                    plan_code="month",
                    starts_at=now - timedelta(days=1),
                    expires_at=now + timedelta(days=30),
                    activated_at=now - timedelta(days=1),
                    duration_days=31,
                    provider="test",
                    created_at=now - timedelta(days=1),
                    updated_at=now,
                )
            )
            session.commit()
            return account_id
        finally:
            session.close()

    def test_wheel_spin_uses_shared_reward_result_and_tracks_result(self) -> None:
        account_id = self._seed_paid_reward_authority(1001)

        callback = _FakeCallback(1001)
        tracked: list[dict] = []
        calls: list[dict] = []

        async def _fake_sleep(_seconds):
            return None

        def _fake_track_event(**kwargs):
            tracked.append(kwargs)
            return 1

        def _fake_spin(_session, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(
                feature="wheel",
                account_id=account_id,
                grant_id="00000000-0000-4000-8000-000000000777",
                reward_days=30,
                sync_state="sync_pending",
                wheel_next_spin_at=kwargs["now"] + timedelta(days=7),
            )

        old_spin = self.bot_module.spin_wheel
        old_track_event = self.bot_module.track_event
        old_flag = self.bot_module.BONUS_WHEEL_ENABLED
        try:
            self.bot_module.BONUS_WHEEL_ENABLED = True
            self.bot_module.spin_wheel = _fake_spin
            self.bot_module.track_event = _fake_track_event
            with patch("asyncio.sleep", new=_fake_sleep):
                asyncio.run(self.bot_module.do_wheel_spin(callback))
        finally:
            self.bot_module.spin_wheel = old_spin
            self.bot_module.track_event = old_track_event
            self.bot_module.BONUS_WHEEL_ENABLED = old_flag

        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0]["enabled"])
        self.assertEqual(calls[0]["account_id"], account_id)
        self.assertGreaterEqual(len(callback.message.edits), 2)
        self.assertIn("Приходи через 7 дней", callback.message.edits[-1])
        self.assertEqual(callback.answers[-1], ("🎉 +30 Дней!", True))
        self.assertEqual(len(tracked), 1)
        self.assertEqual(tracked[0]["event_name"], "wheel_spin")
        self.assertEqual(int(tracked[0]["meta"]["prize_days"]), 30)
        self.assertEqual(int(tracked[0]["meta"]["cooldown_days"]), 7)
        self.assertEqual(tracked[0]["meta"]["sync_state"], "sync_pending")

    def test_disabled_wheel_callback_never_calls_reward_mutator(self) -> None:
        callback = _FakeCallback(1001)
        calls: list[object] = []
        old_spin = self.bot_module.spin_wheel
        old_flag = self.bot_module.BONUS_WHEEL_ENABLED
        try:
            self.bot_module.BONUS_WHEEL_ENABLED = False
            self.bot_module.spin_wheel = lambda *_args, **_kwargs: calls.append(True)
            asyncio.run(self.bot_module.do_wheel_spin(callback))
        finally:
            self.bot_module.spin_wheel = old_spin
            self.bot_module.BONUS_WHEEL_ENABLED = old_flag

        self.assertEqual(calls, [])
        self.assertIn("временно недоступ", callback.answers[-1][0].lower())

    def test_trial_user_is_rejected_by_shared_wheel_authority(self) -> None:
        self.bot_module.ensure_pending_user(1001, username="alice")
        callback = _FakeCallback(1001)

        async def _fake_sleep(_seconds):
            return None

        old_flag = self.bot_module.BONUS_WHEEL_ENABLED
        try:
            self.bot_module.BONUS_WHEEL_ENABLED = True
            with patch("asyncio.sleep", new=_fake_sleep):
                asyncio.run(self.bot_module.do_wheel_spin(callback))
        finally:
            self.bot_module.BONUS_WHEEL_ENABLED = old_flag

        self.assertIn("платн", callback.answers[-1][0].lower())

    def test_telegram_aliases_share_one_wheel_cooldown(self) -> None:
        from models import EntitlementGrant, NodeProvisioningJob

        self._seed_paid_reward_authority(1001, 1002)
        first = _FakeCallback(1001)
        alias = _FakeCallback(1002)

        async def _fake_sleep(_seconds):
            return None

        old_flag = self.bot_module.BONUS_WHEEL_ENABLED
        try:
            self.bot_module.BONUS_WHEEL_ENABLED = True
            with patch("asyncio.sleep", new=_fake_sleep):
                asyncio.run(self.bot_module.do_wheel_spin(first))
                asyncio.run(self.bot_module.do_wheel_spin(alias))
        finally:
            self.bot_module.BONUS_WHEEL_ENABLED = old_flag

        self.assertIn("следующ", alias.message.edits[-1].lower())
        session = self.bot_module.Session()
        try:
            self.assertEqual(session.query(EntitlementGrant).filter_by(source="bonus_wheel").count(), 1)
            self.assertEqual(
                session.query(NodeProvisioningJob).filter_by(job_type="reward_entitlement_sync").count(),
                1,
            )
        finally:
            session.close()

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
        self._seed_paid_reward_authority(1001)
        old_flag = self.bot_module.BONUS_WHEEL_ENABLED
        try:
            self.bot_module.BONUS_WHEEL_ENABLED = True
            callback = _FakeCallback(1001)
            asyncio.run(self.bot_module.show_wheel(callback))
        finally:
            self.bot_module.BONUS_WHEEL_ENABLED = old_flag

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
