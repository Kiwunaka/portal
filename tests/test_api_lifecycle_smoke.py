import hashlib
import hmac
import importlib
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode, urlparse

from fastapi.testclient import TestClient


def _sign_telegram_init_data(*, bot_token: str, tg_id: int, username: str) -> str:
    params = {
        "auth_date": str(int(time.time())),
        "query_id": "AAEAAAE",
        "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
    }
    items = sorted((k, v) for k, v in params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in items])
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = check_hash
    return urlencode(params)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ApiLifecycleSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self.bot_token = "test_bot_token_123"

        self._saved_env: dict[str, str | None] = {}
        for key in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "ADMIN_ID",
            "WEBAPP_SESSION_SECRET",
            "PUBLIC_CHANNEL",
            "SUPPORT_UPLOAD_DIR",
            "RUB_CHECKOUT_ENABLED",
            "PAID_CHECKOUT_LAUNCH_APPROVED",
            "CHECKOUT_TICKET_SECRET",
            "CHECKOUT_TICKET_TTL_SECONDS",
            "LAVATOP_API_KEY",
            "LAVATOP_OFFER_ID",
            "LAVATOP_DYNAMIC_AMOUNT_ENABLED",
            "LAVATOP_WEBHOOK_API_KEY",
            "LAVATOP_WEBHOOK_IP_ALLOWLIST",
            "RUB_PAYMENT_PROVIDER_ENABLED",
            "RUB_PAYMENT_PROVIDER_ORDER",
            "EMAIL_AUTH_PUBLIC_ENABLED",
            "EMAIL_AUTH_DEBUG_ECHO",
            "EMAIL_DELIVERY_WEBHOOK_URL",
            "EMAIL_DELIVERY_WEBHOOK_SECRET",
        ):
            self._saved_env[key] = os.environ.get(key)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = self.bot_token
        os.environ["ADMIN_ID"] = "9999"
        os.environ["WEBAPP_SESSION_SECRET"] = "test_webapp_secret_123"
        os.environ["PUBLIC_CHANNEL"] = "pokrov_vpn"
        os.environ["SUPPORT_UPLOAD_DIR"] = str((Path(self._tmp.name) / "support_uploads").resolve())
        os.environ["RUB_CHECKOUT_ENABLED"] = "true"
        os.environ["PAID_CHECKOUT_LAUNCH_APPROVED"] = "true"
        os.environ["CHECKOUT_TICKET_SECRET"] = "checkout_secret_test_123"
        os.environ["CHECKOUT_TICKET_TTL_SECONDS"] = "900"
        os.environ["LAVATOP_API_KEY"] = "lavatop_api_key_test"
        os.environ["LAVATOP_OFFER_ID"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = "true"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lavatop_webhook_key_test"
        os.environ.pop("LAVATOP_WEBHOOK_IP_ALLOWLIST", None)
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "lavatop"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "lavatop"
        os.environ["EMAIL_AUTH_PUBLIC_ENABLED"] = "true"
        os.environ["EMAIL_AUTH_DEBUG_ECHO"] = "false"
        os.environ["EMAIL_DELIVERY_WEBHOOK_URL"] = "https://relay.pokrov.test/email/deliver"
        os.environ["EMAIL_DELIVERY_WEBHOOK_SECRET"] = "relay-secret"

        for module_name in (
            "api",
            "db",
            "models",
            "migrations",
            "config",
            "email_delivery_service",
            "offers_service",
            "points_service",
            "gift_cards_service",
        ):
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.client = TestClient(self.api.app)

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    def _auth_headers(self, tg_id: int, username: str) -> dict[str, str]:
        return {
            "X-Telegram-Init-Data": _sign_telegram_init_data(
                bot_token=self.bot_token,
                tg_id=tg_id,
                username=username,
            )
        }

    def _execute_admin_intent(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str,
        path: str,
        payload: dict,
    ):
        admin_headers = self._auth_headers(9999, "admin")
        prepared = self.client.post(
            "/api/admin/action-intents",
            headers=admin_headers,
            json={
                "action": action,
                "target": {"type": target_type, "id": target_id},
                "payload": payload,
            },
        )
        self.assertEqual(prepared.status_code, 200, prepared.text)
        challenge = str(prepared.json()["confirmation_challenge"])
        return self.client.post(
            path,
            headers={
                **admin_headers,
                "X-Admin-Intent-Id": str(prepared.json()["intent_id"]),
                "X-Admin-Idempotency-Key": str(uuid.uuid4()),
                "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
            },
            json=payload,
        )

    def test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase(self) -> None:
        class _FakePanel:
            async def login(self):
                return True

            async def add_client(self, **_kwargs):
                return True

            async def enable_client(self, *_args, **_kwargs):
                return True

            async def refresh(self):
                return []

            async def get_user_key_snapshots(self, **_kwargs):
                return []

            async def update_client_traffic(self, *_args, **_kwargs):
                return True

            async def close(self):
                return None

        control_panel = importlib.import_module("control_panel")
        gift_cards_service = importlib.import_module("gift_cards_service")
        free_cycle_service = importlib.import_module("free_cycle_service")
        missing = object()
        original_api_panel = self.api.ControlPanel
        original_control_panel = control_panel.ControlPanel
        original_gift_panel = getattr(gift_cards_service, "ControlPanel", missing)
        original_free_cycle_panel = getattr(free_cycle_service, "ControlPanel", missing)

        def _restore_panel_classes() -> None:
            self.api.ControlPanel = original_api_panel
            control_panel.ControlPanel = original_control_panel
            if original_gift_panel is missing:
                try:
                    delattr(gift_cards_service, "ControlPanel")
                except AttributeError:
                    pass
            else:
                gift_cards_service.ControlPanel = original_gift_panel
            if original_free_cycle_panel is missing:
                try:
                    delattr(free_cycle_service, "ControlPanel")
                except AttributeError:
                    pass
            else:
                free_cycle_service.ControlPanel = original_free_cycle_panel

        self.addCleanup(_restore_panel_classes)
        self.api.ControlPanel = _FakePanel
        control_panel.ControlPanel = _FakePanel
        gift_cards_service.ControlPanel = _FakePanel
        free_cycle_service.ControlPanel = _FakePanel
        trial = self.client.post(
            "/api/client/session/start-trial",
            json={
                "install_id": f"install-{uuid.uuid4().hex}",
                "device_name": "Smoke Pixel",
                "platform": "android",
                "os_version": "14",
                "app_version": "1.0.0",
                "locale": "ru-RU",
                "time_zone": "Europe/Moscow",
            },
        )

        self.assertEqual(trial.status_code, 200, trial.text)
        trial_body = trial.json()
        self.assertTrue(trial_body.get("ok"))
        self.assertTrue(trial_body.get("created"))
        session_token = str(trial_body.get("session_token") or "")
        self.assertTrue(session_token)
        account_id = int(trial_body.get("account_id") or 0)
        self.assertGreater(account_id, 0)
        subscription_url = str(trial_body.get("subscription_url") or "")
        self.assertTrue(subscription_url.startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))

        auth_headers = {"Authorization": f"Bearer {session_token}"}
        auth_session = self.client.get("/api/auth/session", headers=auth_headers)
        self.assertEqual(auth_session.status_code, 200, auth_session.text)
        self.assertEqual(int(auth_session.json()["user"]["id"]), account_id)
        self.assertEqual(str(auth_session.json()["user"]["auth_type"]), "app")

        dashboard_before = self.client.get("/api/dashboard", headers=auth_headers)
        self.assertEqual(dashboard_before.status_code, 200, dashboard_before.text)
        dashboard_before_body = dashboard_before.json()
        self.assertTrue(str(dashboard_before_body.get("subscription_url") or "").startswith("https://connect.pokrov.space/s8Kx2mP7qR4wT/"))
        expiry_before = str(dashboard_before_body.get("expiry_at") or "")

        profile = self.client.get(f"/api/user/{account_id}", headers=auth_headers)
        self.assertEqual(profile.status_code, 200, profile.text)
        self.assertEqual(int(profile.json()["tg_id"]), account_id)

        config_path = urlparse(subscription_url).path
        with patch.object(self.api, "_nodes_for_user", side_effect=lambda user, nodes, session=None: list(nodes or [])[:1]):
            smart_profile = self.client.get(config_path, headers={"Host": "connect.pokrov.space"})
        self.assertEqual(smart_profile.status_code, 200, smart_profile.text)
        self.assertEqual(smart_profile.headers.get("content-type"), "application/json")
        self.assertIn("outbounds", smart_profile.json())

        ticket = self.client.post(
            "/api/tickets",
            headers=auth_headers,
            json={"subject": "Smoke support", "body": "Проверка полного API-цикла"},
        )
        self.assertEqual(ticket.status_code, 200, ticket.text)
        self.assertEqual(str(ticket.json()["ticket"]["status"]), "open")

        promo_payload = {
            "code": "SMOKE14",
            "promo_type": "days",
            "value": 14,
            "uses_left": 10,
            "expires_at": None,
        }
        promo = self._execute_admin_intent(
            action="promo.create",
            target_type="promo",
            target_id="SMOKE14",
            path="/api/admin/promos",
            payload=promo_payload,
        )
        self.assertEqual(promo.status_code, 200, promo.text)

        gift = self._execute_admin_intent(
            action="gift_code.create",
            target_type="gift_code",
            target_id="standard",
            path="/api/admin/gift-codes",
            payload={"card_type": "standard"},
        )
        self.assertEqual(gift.status_code, 200, gift.text)
        gift_code = str(gift.json().get("gift_code", {}).get("code") or "")
        self.assertTrue(gift_code)

        from db import SessionLocal
        from models import Event, ExternalOrder, ExternalPaymentEvent, ReferralBonusQueue, ReferralRelationship, User

        s = SessionLocal()
        try:
            linked_user = s.query(User).filter(User.tg_id == account_id).first()
            self.assertIsNotNone(linked_user)
            linked_user.linked_telegram_id = account_id
            linked_user.linked_telegram_username = f"app_{account_id}"
            s.commit()
        finally:
            s.close()

        async def _always_member(*_args, **_kwargs):
            return True, "member"

        with patch.object(self.api, "_is_channel_member", new=_always_member):
            channel_bonus = self.client.post("/api/bonuses/channel/claim", headers=auth_headers)
        self.assertEqual(channel_bonus.status_code, 200, channel_bonus.text)
        self.assertTrue(channel_bonus.json().get("ok"))

        promo_redeem = self.client.post("/api/promo/redeem", headers=auth_headers, json={"code": "SMOKE14"})
        self.assertEqual(promo_redeem.status_code, 200, promo_redeem.text)
        self.assertTrue(promo_redeem.json().get("ok"))

        gift_redeem = self.client.post("/api/gift/redeem", headers=auth_headers, json={"code": gift_code})
        self.assertEqual(gift_redeem.status_code, 200, gift_redeem.text)
        self.assertTrue(gift_redeem.json().get("ok"))

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2002,
                    username="referrer",
                    uuid=str(uuid.uuid4()),
                    email="user_2002",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                    expiry_at=_utcnow() + timedelta(days=20),
                    referral_count=0,
                )
            )
            user = s.query(User).filter(User.tg_id == account_id).first()
            self.assertIsNotNone(user)
            user.referrer_id = 2002
            user.first_purchase_done = False
            s.commit()
        finally:
            s.close()

        checkout_ticket = self.api._create_checkout_ticket(
            tg_id=account_id,
            plan_code="1_month",
            promo_code="SMOKE14",
            campaign_key="api_smoke",
            source="site",
        )
        async def _fake_create_rub_payment(**_kwargs):
            payment_url = "https://app.lava.top/pay/api-lifecycle-smoke"
            return {"payment_url": payment_url, "remote": {"payment_url": payment_url}}

        with patch.object(self.api, "create_rub_payment", new=_fake_create_rub_payment):
            create_order = self.client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "1_month",
                    "checkout_ticket": checkout_ticket,
                    "currency": "RUB",
                },
            )
        self.assertEqual(create_order.status_code, 200, create_order.text)
        order_body = create_order.json()
        self.assertTrue(order_body.get("ok"))
        self.assertEqual(str(order_body.get("status") or ""), "pending")
        self.assertEqual(str(order_body.get("provider") or ""), "lavatop")
        self.assertEqual(str(order_body.get("payment_url") or ""), "https://app.lava.top/pay/api-lifecycle-smoke")
        self.assertTrue(bool(order_body.get("discount_applied")))

        order_id = str(order_body.get("order_id") or "")
        self.assertTrue(order_id)
        callback_payload = {
            "eventType": "payment.success",
            "contractId": str(uuid.uuid4()),
            "amount": float(order_body.get("amount_rub") or 0),
            "currency": "RUB",
            "status": "completed",
            "timestamp": "2026-07-21T00:00:00Z",
            "clientUtm": {
                "utm_content": order_id,
                "utm_medium": "site",
                "utm_campaign": "api_smoke",
                "utm_term": "1_month",
            },
            "tg_id": str(account_id),
            "plan_code": "1_month",
            "source": "site",
        }
        callback = self.client.post(
            "/api/payments/result/lavatop",
            json=callback_payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(callback.status_code, 200, callback.text)
        self.assertTrue(callback.json().get("ok"))
        self.assertTrue(callback.json().get("activated"))

        dashboard_after = self.client.get("/api/dashboard", headers=auth_headers)
        self.assertEqual(dashboard_after.status_code, 200, dashboard_after.text)
        dashboard_after_body = dashboard_after.json()
        self.assertEqual(str(dashboard_after_body.get("sub_type") or ""), "PAID")
        self.assertEqual(str(dashboard_after_body.get("current_plan_code") or ""), "1_month")
        self.assertNotEqual(str(dashboard_after_body.get("expiry_at") or ""), expiry_before)

        final_ticket_list = self.client.get("/api/tickets", headers=auth_headers)
        self.assertEqual(final_ticket_list.status_code, 200, final_ticket_list.text)
        self.assertTrue(final_ticket_list.json().get("tickets"))

        s = SessionLocal()
        try:
            order_row = s.query(ExternalOrder).filter(ExternalOrder.order_id == order_id).first()
            payment_events = s.query(ExternalPaymentEvent).filter(ExternalPaymentEvent.order_id == order_id).all()
            bonus_queue = s.query(ReferralBonusQueue).filter(ReferralBonusQueue.order_id == order_id).first()
            bonus_events = (
                s.query(Event)
                .filter(
                    Event.tg_id == account_id,
                    Event.event_name.in_(
                        [
                            "promo_channel_activated",
                            "promo_redeemed",
                            "gift_redeemed",
                            "ticket_created",
                        ]
                    ),
                )
                .all()
            )
            referred_user = s.query(User).filter(User.tg_id == account_id).first()
            referrer = s.query(User).filter(User.tg_id == 2002).first()
            self.assertIsNotNone(order_row)
            self.assertEqual(str(order_row.provider or ""), "lavatop")
            self.assertEqual(str(order_row.status or ""), "paid")
            self.assertEqual(len(payment_events), 1)
            self.assertIsNone(bonus_queue)
            self.assertEqual(len(bonus_events), 4)
            self.assertIsNotNone(referred_user)
            self.assertTrue(bool(referred_user.first_purchase_done))
            self.assertIsNotNone(referrer)
            self.assertEqual(int(referrer.referral_count or 0), 1)
            relationship = s.query(ReferralRelationship).filter_by(referred_account_id=referred_user.account_id).one()
            self.assertEqual(relationship.referrer_account_id, referrer.account_id)
            self.assertEqual(relationship.status, "holding")
            self.assertEqual(relationship.hold_until - relationship.first_payment_at, timedelta(hours=72))
        finally:
            s.close()
