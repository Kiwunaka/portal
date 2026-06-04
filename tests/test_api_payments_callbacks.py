import hashlib
import hmac
import importlib
import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from fastapi.testclient import TestClient


class ApiPaymentCallbacksTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env: dict[str, str | None] = {}
        for k in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "FREEKASSA_SIGNING_SECRET",
            "PAYMENT_CALLBACK_TOLERANT_MODE",
            "CHECKOUT_TICKET_SECRET",
            "CHECKOUT_TICKET_TTL_SECONDS",
            "FK_SITE_SHOP_ID",
            "FK_SITE_API_KEY",
            "FK_SITE_SECRET_WORD_1",
            "FK_SITE_SECRET_WORD_2",
            "FK_BOT_SHOP_ID",
            "FK_BOT_API_KEY",
            "FK_BOT_SECRET_WORD_1",
            "FK_BOT_SECRET_WORD_2",
            "RUB_PAYMENT_PROVIDER_ENABLED",
            "RUB_PAYMENT_PROVIDER_ORDER",
            "CARDLINK_API_TOKEN",
            "CARDLINK_SHOP_ID",
            "PALLY_API_TOKEN",
            "PALLY_SHOP_ID",
            "PLATIMA_PROJECT_ID",
            "PLATIMA_API_KEY_PROJECT",
            "LAVATOP_API_KEY",
            "LAVATOP_OFFER_ID",
            "LAVATOP_WEBHOOK_API_KEY",
            "LAVATOP_WEBHOOK_IP_ALLOWLIST",
            "RUB_CHECKOUT_ENABLED",
            "PAID_CHECKOUT_LAUNCH_APPROVED",
            "ADMIN_ID",
            "EMAIL_AUTH_PUBLIC_ENABLED",
            "EMAIL_AUTH_DEBUG_ECHO",
            "EMAIL_DELIVERY_WEBHOOK_URL",
            "EMAIL_DELIVERY_WEBHOOK_SECRET",
        ):
            self._saved_env[k] = os.environ.get(k)
        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["FREEKASSA_SIGNING_SECRET"] = "test_fk_secret"
        os.environ["PAYMENT_CALLBACK_TOLERANT_MODE"] = "false"
        os.environ["CHECKOUT_TICKET_SECRET"] = "checkout_secret_test_123"
        os.environ["CHECKOUT_TICKET_TTL_SECONDS"] = "900"
        os.environ["FK_SITE_SHOP_ID"] = "69962"
        os.environ["FK_SITE_API_KEY"] = "fk_api_key_test"
        os.environ["FK_SITE_SECRET_WORD_1"] = "fk_sw1_test"
        os.environ["FK_SITE_SECRET_WORD_2"] = "fk_sw2_test"
        os.environ["FK_BOT_SHOP_ID"] = "69963"
        os.environ["FK_BOT_API_KEY"] = "fk_api_key_bot_test"
        os.environ["FK_BOT_SECRET_WORD_1"] = "fk_sw1_bot_test"
        os.environ["FK_BOT_SECRET_WORD_2"] = "fk_sw2_bot_test"
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "lavatop,cardlink,pally,platima,freekassa"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "lavatop,cardlink,pally,platima,freekassa"
        os.environ["CARDLINK_API_TOKEN"] = "cardlink_token_test"
        os.environ["CARDLINK_SHOP_ID"] = "cardlink_shop_test"
        os.environ["PALLY_API_TOKEN"] = "pally_token_test"
        os.environ["PALLY_SHOP_ID"] = "pally_shop_test"
        os.environ["PLATIMA_PROJECT_ID"] = "platima_project_test"
        os.environ["PLATIMA_API_KEY_PROJECT"] = "platima_key_project_test"
        os.environ["LAVATOP_API_KEY"] = "lavatop_api_key_test"
        os.environ["LAVATOP_OFFER_ID"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lavatop_webhook_key_test"
        os.environ.pop("LAVATOP_WEBHOOK_IP_ALLOWLIST", None)
        os.environ["RUB_CHECKOUT_ENABLED"] = "true"
        os.environ["PAID_CHECKOUT_LAUNCH_APPROVED"] = "true"
        os.environ["ADMIN_ID"] = "9999"
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
            "payment_providers",
        ):
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)
        self.telegram_messages: list[dict[str, object]] = []

        async def _fake_sync_user_after_paid_purchase(tg_id: int) -> bool:
            return True

        async def _fake_telegram_send_message(chat_id: int, text: str, **kwargs) -> bool:
            self.telegram_messages.append({"chat_id": int(chat_id), "text": str(text), "kwargs": dict(kwargs)})
            return True

        self._old_sync_user_after_paid_purchase = self.api._sync_user_after_paid_purchase
        self._old_telegram_send_message = self.api._telegram_send_message
        self.api._sync_user_after_paid_purchase = _fake_sync_user_after_paid_purchase
        self.api._telegram_send_message = _fake_telegram_send_message

    def tearDown(self) -> None:
        try:
            self.api._sync_user_after_paid_purchase = self._old_sync_user_after_paid_purchase
            self.api._telegram_send_message = self._old_telegram_send_message
        except Exception:
            pass
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._tmp.cleanup()

    @staticmethod
    def _hmac_sha256(secret: str, payload: bytes) -> str:
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _fk_sci_signature(*, merchant_id: str, amount: str, order_id: str, secret_word_2: str) -> str:
        base = f"{merchant_id}:{amount}:{secret_word_2}:{order_id}"
        return hashlib.md5(base.encode("utf-8")).hexdigest()

    @staticmethod
    def _sign_telegram_init_data(*, bot_token: str, tg_id: int, username: str) -> str:
        params = {
            "auth_date": "1700000000",
            "query_id": "AAEAAAE",
            "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
        }
        items = sorted((k, v) for k, v in params.items())
        data_check_string = "\n".join([f"{k}={v}" for k, v in items])
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        params["hash"] = check_hash
        return urlencode(params)

    def _auth_headers(self, tg_id: int, username: str) -> dict[str, str]:
        init_data = self._sign_telegram_init_data(
            bot_token="test_bot_token_123",
            tg_id=tg_id,
            username=username,
        )
        return {"X-Telegram-Init-Data": init_data}

    def test_success_and_fail_landing_routes(self) -> None:
        client = TestClient(self.api.app)
        ok = client.get("/pay/success")
        bad = client.get("/pay/fail")
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(bad.status_code, 200, bad.text)
        self.assertIn("text/html", ok.headers.get("content-type", ""))
        self.assertIn("text/html", bad.headers.get("content-type", ""))

    def test_result_callback_is_idempotent_and_persists_single_event(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "order_id": "order-1001",
            "external_tx_id": "tx-abc-1",
            "amount": "249.00",
            "currency": "RUB",
            "status": "paid",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        sig = self._hmac_sha256("test_fk_secret", raw)

        r1 = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        r2 = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r1.json().get("ok"))
        self.assertTrue(r2.json().get("duplicate"))

        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent

        s = SessionLocal()
        try:
            events = s.query(ExternalPaymentEvent).all()
            orders = s.query(ExternalOrder).all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].provider, "freekassa")
            self.assertEqual(events[0].event_type, "result")
            self.assertEqual(events[0].external_id, "tx-abc-1")
            self.assertEqual(len(orders), 1)
            self.assertEqual(orders[0].order_id, "order-1001")
        finally:
            s.close()

    def test_invalid_signature_is_rejected(self) -> None:
        client = TestClient(self.api.app)
        payload = {"order_id": "order-2001", "external_tx_id": "tx-abc-2", "status": "paid"}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        r = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": "invalid"},
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_invalid_signature_does_not_poison_later_valid_callback(self) -> None:
        client = TestClient(self.api.app)
        payload = {"order_id": "order-2002", "external_tx_id": "tx-abc-2b", "status": "paid"}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        valid_sig = self._hmac_sha256("test_fk_secret", raw)

        bad = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": "invalid"},
        )
        self.assertEqual(bad.status_code, 400, bad.text)

        good = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": valid_sig},
        )
        self.assertEqual(good.status_code, 200, good.text)
        self.assertTrue(good.json().get("ok"))
        self.assertFalse(good.json().get("duplicate"))

        from db import SessionLocal
        from models import ExternalPaymentEvent

        s = SessionLocal()
        try:
            events = (
                s.query(ExternalPaymentEvent)
                .filter(ExternalPaymentEvent.external_id == "tx-abc-2b")
                .order_by(ExternalPaymentEvent.id.asc())
                .all()
            )
            self.assertEqual(len(events), 1)
            self.assertTrue(bool(events[0].signature_ok))
            self.assertTrue(bool(events[0].processed_ok))
        finally:
            s.close()

    def test_signed_failed_result_records_order_without_activation(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2401,
                    username="failedpay",
                    uuid=str(uuid.uuid4()),
                    email="user_2401",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-failed-2401",
                    provider="freekassa",
                    tg_id=2401,
                    plan_code="1_month",
                    source="site",
                    amount=249.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "order_id": "order-failed-2401",
            "external_tx_id": "tx-failed-2401",
            "status": "failed",
            "tg_id": "2401",
            "plan_code": "1_month",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        sig = self._hmac_sha256("test_fk_secret", raw)

        response = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("status"), "failed")
        self.assertFalse(body.get("activated"))

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 2401).first()
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "order-failed-2401").first()
            self.assertIsNotNone(user)
            self.assertIsNotNone(row)
            self.assertEqual(str(user.sub_type or ""), "FREE")
            self.assertEqual(str(row.status or ""), "failed")
            self.assertIsNone(row.paid_at)
        finally:
            s.close()

    def test_signed_cancelled_result_records_cancelled_without_activation(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2402,
                    username="cancelpay",
                    uuid=str(uuid.uuid4()),
                    email="user_2402",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-cancelled-2402",
                    provider="freekassa",
                    tg_id=2402,
                    plan_code="1_month",
                    source="site",
                    amount=249.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "order_id": "order-cancelled-2402",
            "external_tx_id": "tx-cancelled-2402",
            "status": "cancelled",
            "tg_id": "2402",
            "plan_code": "1_month",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        sig = self._hmac_sha256("test_fk_secret", raw)

        response = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json().get("status"), "cancelled")
        self.assertFalse(response.json().get("activated"))

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 2402).first()
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "order-cancelled-2402").first()
            self.assertIsNotNone(user)
            self.assertIsNotNone(row)
            self.assertEqual(str(user.sub_type or ""), "FREE")
            self.assertEqual(str(row.status or ""), "cancelled")
            self.assertIsNone(row.paid_at)
        finally:
            s.close()

    def test_unknown_signed_result_goes_to_manual_review(self) -> None:
        client = TestClient(self.api.app)

        payload = {
            "order_id": "order-review-2403",
            "external_tx_id": "tx-review-2403",
            "status": "needs_operator",
            "tg_id": "2403",
            "plan_code": "1_month",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        sig = self._hmac_sha256("test_fk_secret", raw)

        response = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("status"), "manual_review")
        self.assertFalse(body.get("activated"))

        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent

        s = SessionLocal()
        try:
            event = s.query(ExternalPaymentEvent).filter(ExternalPaymentEvent.external_id == "tx-review-2403").first()
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "order-review-2403").first()
            self.assertIsNotNone(event)
            self.assertIsNotNone(row)
            self.assertTrue(bool(event.signature_ok))
            self.assertFalse(bool(event.processed_ok))
            self.assertEqual(str(row.status or ""), "manual_review")
            self.assertIsNone(row.paid_at)
        finally:
            s.close()

    def test_freekassa_sci_amount_currency_mismatch_goes_to_manual_review(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2450,
                    username="fk_mismatch",
                    uuid=str(uuid.uuid4()),
                    email="user_2450",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-fk-mismatch-2450",
                    provider="freekassa",
                    tg_id=2450,
                    plan_code="12_months",
                    source="site",
                    amount=1499.0,
                    currency="RUB",
                    status="created",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        amount = "1.00"
        order_id = "order-fk-mismatch-2450"
        sig = self._fk_sci_signature(
            merchant_id="69962",
            amount=amount,
            order_id=order_id,
            secret_word_2="fk_sw2_test",
        )
        payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": amount,
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": sig,
            "us_tg_id": "2450",
            "us_plan_code": "12_months",
            "currency": "USD",
            "intid": "tx-fk-mismatch-2450",
        }

        response = client.post("/api/payments/result/freekassa", params=payload)

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("status"), "manual_review")
        self.assertFalse(body.get("activated"))
        self.assertEqual(body.get("activation_reason"), "amount_mismatch")

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == order_id).first()
            user = s.query(User).filter(User.tg_id == 2450).first()
            event = s.query(ExternalPaymentEvent).filter(ExternalPaymentEvent.external_id == "tx-fk-mismatch-2450").first()
            self.assertIsNotNone(row)
            self.assertIsNotNone(user)
            self.assertIsNotNone(event)
            self.assertEqual(str(row.status or ""), "manual_review")
            self.assertEqual(float(row.amount or 0), 1499.0)
            self.assertEqual(str(row.currency or ""), "RUB")
            self.assertIsNone(row.paid_at)
            self.assertEqual(str(user.sub_type or ""), "FREE")
            self.assertFalse(bool(event.processed_ok))
        finally:
            s.close()

    def test_freekassa_notify_alias_returns_yes_for_valid_sci(self) -> None:
        client = TestClient(self.api.app)
        merchant_id = "69962"
        amount = "249.00"
        order_id = "order-3001"
        sig = self._fk_sci_signature(
            merchant_id=merchant_id,
            amount=amount,
            order_id=order_id,
            secret_word_2="fk_sw2_test",
        )
        payload = {
            "MERCHANT_ID": merchant_id,
            "AMOUNT": amount,
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": sig,
            "us_tg_id": "1001",
            "us_plan_code": "1_month",
            "intid": "tx-fk-1",
        }
        r = client.post(
            "/api/payments/freekassa/notify",
            params=payload,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.text.strip(), "YES")

    def test_freekassa_notify_rejects_bad_sci_signature(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": "249.00",
            "MERCHANT_ORDER_ID": "order-3002",
            "SIGN": "bad_signature",
            "intid": "tx-fk-2",
        }
        r = client.post("/api/payments/freekassa/notify", params=payload)
        self.assertEqual(r.status_code, 400, r.text)

    def test_freekassa_notify_awards_referrer_bonus_on_first_paid_purchase(self) -> None:
        client = TestClient(self.api.app)

        from datetime import datetime, timedelta
        from db import SessionLocal
        from models import ExternalOrder, PointsLedger, ReferralBonusQueue, User

        s = SessionLocal()
        try:
            ref_expiry = datetime.utcnow() + timedelta(days=20)
            s.add(
                User(
                    tg_id=2002,
                    username="ref",
                    uuid=str(uuid.uuid4()),
                    email="user_2002",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                    expiry_at=ref_expiry,
                    referral_count=0,
                )
            )
            s.add(
                User(
                    tg_id=2003,
                    username="invited",
                    uuid=str(uuid.uuid4()),
                    email="user_2003",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                    referrer_id=2002,
                    first_purchase_done=False,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-ref-first-1",
                    provider="freekassa",
                    tg_id=2003,
                    plan_code="1_month",
                    source="site",
                    amount=249.0,
                    currency="RUB",
                    status="created",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        merchant_id = "69962"
        amount = "249.00"
        order_id = "order-ref-first-1"
        sig = self._fk_sci_signature(
            merchant_id=merchant_id,
            amount=amount,
            order_id=order_id,
            secret_word_2="fk_sw2_test",
        )
        payload = {
            "MERCHANT_ID": merchant_id,
            "AMOUNT": amount,
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": sig,
            "us_tg_id": "2003",
            "us_plan_code": "1_month",
            "intid": "tx-fk-ref-1",
        }
        r = client.post("/api/payments/freekassa/notify", params=payload)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.text.strip(), "YES")

        s = SessionLocal()
        try:
            invited = s.query(User).filter(User.tg_id == 2003).first()
            referrer = s.query(User).filter(User.tg_id == 2002).first()
            queued = (
                s.query(ReferralBonusQueue)
                .filter(
                    ReferralBonusQueue.order_id == order_id,
                    ReferralBonusQueue.referrer_tg_id == 2002,
                    ReferralBonusQueue.referred_tg_id == 2003,
                )
                .first()
            )
            points_rows = (
                s.query(PointsLedger)
                .filter(PointsLedger.tg_id == 2002, PointsLedger.reason.like("referral_earned%"), PointsLedger.ref_tg_id == 2003)
                .all()
            )
            self.assertIsNotNone(invited)
            self.assertIsNotNone(referrer)
            self.assertIsNotNone(queued)
            self.assertEqual(len(points_rows), 1)
            self.assertGreater(int(points_rows[0].delta_points or 0), 0)
            self.assertTrue(bool(invited.first_purchase_done))
            self.assertEqual(int(referrer.referral_count or 0), 1)
            self.assertTrue(bool(referrer.expiry_at and referrer.expiry_at < datetime.utcnow() + timedelta(days=30)))
        finally:
            s.close()

    def test_freekassa_order_endpoints_use_remote_api_wrapper(self) -> None:
        client = TestClient(self.api.app)
        hdrs = self._auth_headers(1001, "alice")

        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=1001,
                    username="alice",
                    uuid=str(uuid.uuid4()),
                    email="user_1001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        calls: list[tuple[str, str, dict]] = []

        async def fake_fk_request(*, source: str, method: str, data: dict):
            calls.append((source, method, dict(data)))
            if method == "orders/create":
                return {"location": "https://pay.example/fk/order-1"}
            if method == "orders":
                return {"orderId": data.get("orderId"), "status": "new"}
            if method == "orders/refund":
                return {"orderId": data.get("orderId"), "status": "refunded"}
            if method == "currencies":
                return {"currencies": [{"code": "RUB"}]}
            if method == "currencies/status":
                return {"currency": data.get("currency"), "enabled": True}
            return {"ok": True}

        old_fk_request = self.api._freekassa_api_request
        self.api._freekassa_api_request = fake_fk_request
        try:
            create = client.post(
                "/api/payments/freekassa/orders/create",
                headers=hdrs,
                json={"plan_code": "1_month", "source": "site", "tg_id": 1001},
            )
            self.assertEqual(create.status_code, 200, create.text)
            body = create.json()
            self.assertTrue(body.get("ok"))
            order_id = str(body.get("order_id") or "")
            self.assertTrue(order_id)

            get_order = client.get(f"/api/payments/freekassa/orders/{order_id}", headers=hdrs)
            self.assertEqual(get_order.status_code, 200, get_order.text)
            self.assertEqual(str(get_order.json().get("status_local") or ""), "pending")

            admin_hdrs = self._auth_headers(9999, "admin")
            refund = client.post(f"/api/payments/freekassa/orders/{order_id}/refund", headers=admin_hdrs)
            self.assertEqual(refund.status_code, 200, refund.text)

            currencies = client.get("/api/payments/freekassa/currencies", headers=hdrs)
            self.assertEqual(currencies.status_code, 200, currencies.text)

            currency_status = client.get("/api/payments/freekassa/currencies/RUB/status", headers=hdrs)
            self.assertEqual(currency_status.status_code, 200, currency_status.text)

            called_methods = [m for _, m, _ in calls]
            self.assertIn("orders", called_methods)
            self.assertIn("orders/refund", called_methods)
            self.assertIn("currencies", called_methods)
            self.assertIn("currencies/status", called_methods)
        finally:
            self.api._freekassa_api_request = old_fk_request

    def test_create_public_order_uses_checkout_ticket_and_applies_discount(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=1001,
                    username="alice",
                    uuid=str(uuid.uuid4()),
                    email="user_1001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                    pending_discount_pct=20,
                    pending_discount_code="WELCOME20",
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=1001,
            plan_code="1_month",
            promo_code="WELCOME20",
            campaign_key="launch_w1",
            source="site",
        )
        r = client.post(
            "/api/payments/freekassa/orders/create-public",
            json={"plan_code": "1_month", "checkout_ticket": ticket, "currency": "RUB"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 20)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 249)
        self.assertEqual(int(body.get("amount_rub") or 0), 199)
        payment_url = str(body.get("payment_url") or "")
        self.assertTrue(payment_url.startswith("https://pay.fk.money/?"))
        parsed = urlparse(payment_url)
        query = parse_qs(parsed.query)
        self.assertEqual(query.get("currency"), ["RUB"])
        self.assertEqual(query.get("us_tg_id"), ["1001"])
        self.assertEqual(query.get("us_plan_code"), ["1_month"])
        self.assertEqual(query.get("us_campaign"), ["launch_w1"])
        self.assertEqual(query.get("us_promo_code"), ["WELCOME20"])

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 1001).first()
            self.assertIsNotNone(user)
            self.assertEqual(int(user.pending_discount_pct or 0), 20)
            self.assertEqual(str(user.pending_discount_code or ""), "WELCOME20")
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 1001, ExternalOrder.provider == "freekassa").first()
            self.assertIsNotNone(row)
            self.assertIn("\"discount_pct\":20", str(row.meta_json or ""))
            self.assertIn("\"payment_url\":\"https://pay.fk.money/", str(row.meta_json or ""))
        finally:
            s.close()

    def test_create_public_order_applies_referral_first_purchase_discount(self) -> None:
        client = TestClient(self.api.app)

        from datetime import datetime, timedelta
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2002,
                    username="ref",
                    uuid=str(uuid.uuid4()),
                    email="user_2002",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                    expiry_at=datetime.utcnow() + timedelta(days=30),
                )
            )
            s.add(
                User(
                    tg_id=2003,
                    username="invited",
                    uuid=str(uuid.uuid4()),
                    email="user_2003",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                    referrer_id=2002,
                    first_purchase_done=False,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=2003,
            plan_code="1_month",
            promo_code="",
            campaign_key="ref_test",
            source="site",
        )
        r = client.post(
            "/api/payments/freekassa/orders/create-public",
            json={"plan_code": "1_month", "checkout_ticket": ticket, "currency": "RUB"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 20)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 249)
        self.assertEqual(int(body.get("amount_rub") or 0), 199)
        self.assertTrue(str(body.get("payment_url") or "").startswith("https://pay.fk.money/?"))

    def test_create_public_order_rejects_plan_mismatch_with_ticket(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=3001,
                    username="mismatch",
                    uuid=str(uuid.uuid4()),
                    email="user_3001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=3001,
            plan_code="1_month",
            promo_code="",
            campaign_key="mismatch_test",
            source="site",
        )
        response = client.post(
            "/api/payments/freekassa/orders/create-public",
            json={"plan_code": "12_months", "checkout_ticket": ticket, "currency": "RUB"},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Plan code does not match checkout ticket", response.text)

    def test_rub_provider_catalog_lists_enabled_providers(self) -> None:
        client = TestClient(self.api.app)
        response = client.get("/api/payments/providers")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertFalse(body.get("blocked"))
        self.assertEqual(body.get("checkout_mode"), "account_session_first")
        rows = body.get("providers", [])
        self.assertTrue(any((row.get("code") == "lavatop") for row in rows))
        self.assertTrue(any((row.get("code") == "cardlink") for row in rows))
        self.assertTrue(any((row.get("code") == "pally") for row in rows))
        self.assertTrue(any((row.get("code") == "platima") for row in rows))
        self.assertTrue(any((row.get("code") == "freekassa") for row in rows))

    def test_rub_provider_catalog_reports_blocked_state_when_checkout_disabled(self) -> None:
        client = TestClient(self.api.app)
        old_enabled = self.api.RUB_CHECKOUT_ENABLED
        try:
            self.api.RUB_CHECKOUT_ENABLED = False
            response = client.get("/api/payments/providers")
        finally:
            self.api.RUB_CHECKOUT_ENABLED = old_enabled

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body.get("ok"))
        self.assertTrue(body.get("blocked"))
        self.assertEqual(body.get("providers"), [])
        self.assertIn("checkout_disabled", body.get("blocked_reasons", []))
        self.assertTrue(any("disabled" in text.lower() for text in body.get("blocked_reason_texts", [])))

    def test_rub_provider_catalog_requires_paid_checkout_launch_approval(self) -> None:
        client = TestClient(self.api.app)
        old_approved = getattr(self.api, "PAID_CHECKOUT_LAUNCH_APPROVED", None)
        try:
            self.api.PAID_CHECKOUT_LAUNCH_APPROVED = False
            response = client.get("/api/payments/providers")
        finally:
            if old_approved is None:
                try:
                    delattr(self.api, "PAID_CHECKOUT_LAUNCH_APPROVED")
                except AttributeError:
                    pass
            else:
                self.api.PAID_CHECKOUT_LAUNCH_APPROVED = old_approved

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body.get("ok"))
        self.assertTrue(body.get("blocked"))
        self.assertEqual(body.get("providers"), [])
        self.assertIn("paid_checkout_launch_evidence_missing", body.get("blocked_reasons", []))

    def test_rub_checkout_blocks_when_email_delivery_is_not_ready(self) -> None:
        client = TestClient(self.api.app)
        old_status = self.api.email_delivery_runtime_status
        try:
            self.api.email_delivery_runtime_status = lambda: {
                "ok": True,
                "enabled": False,
                "blocked_reasons": ["delivery_webhook_missing"],
            }
            providers = client.get("/api/payments/providers")
            create = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "lavatop", "plan_code": "1_month", "currency": "RUB", "buyer_email": "buyer@pokrov.test"},
            )
        finally:
            self.api.email_delivery_runtime_status = old_status

        self.assertEqual(providers.status_code, 200, providers.text)
        provider_body = providers.json()
        self.assertFalse(provider_body.get("ok"))
        self.assertTrue(provider_body.get("blocked"))
        self.assertIn("email_delivery_not_ready", provider_body.get("blocked_reasons", []))
        self.assertEqual(create.status_code, 503, create.text)
        self.assertIn("Email delivery is not ready", create.text)

    def test_provider_specific_create_is_blocked_when_provider_not_enabled(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=9001,
                    username="provider_gate",
                    uuid=str(uuid.uuid4()),
                    email="user_9001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=9001,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )
        old_enabled = os.environ.get("RUB_PAYMENT_PROVIDER_ENABLED")
        old_order = os.environ.get("RUB_PAYMENT_PROVIDER_ORDER")
        try:
            os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "lavatop"
            os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "lavatop"
            response = client.post(
                "/api/payments/freekassa/orders/create-public",
                json={
                    "plan_code": "start_99",
                    "currency": "RUB",
                    "checkout_ticket": ticket,
                },
            )
        finally:
            if old_enabled is None:
                os.environ.pop("RUB_PAYMENT_PROVIDER_ENABLED", None)
            else:
                os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = old_enabled
            if old_order is None:
                os.environ.pop("RUB_PAYMENT_PROVIDER_ORDER", None)
            else:
                os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = old_order

        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("freekassa is not enabled for RUB checkout", response.text)

    def test_public_checkout_url_rewrites_legacy_portal_privacy_host(self) -> None:
        old_url = getattr(self.api.Settings, "PAY_CHECKOUT_URL", "")
        try:
            self.api.Settings.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
            self.assertEqual(self.api._public_checkout_url(), "https://pay.pokrov.space/checkout/")
        finally:
            self.api.Settings.PAY_CHECKOUT_URL = old_url

    def test_generic_create_public_order_uses_selected_provider(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4444,
                    username="multi",
                    uuid=str(uuid.uuid4()),
                    email="user_4444",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4444,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )

        async def _fake_create_rub_payment(**kwargs):
            self.assertEqual(kwargs["provider"], "cardlink")
            self.assertEqual(kwargs["description"], "POKROV Старт на 30 дней")
            return {
                "payment_url": "https://checkout.cardlink.link/pay/test-order",
                "remote": {"payment_url": "https://checkout.cardlink.link/pay/test-order"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "cardlink", "plan_code": "start_99", "checkout_ticket": ticket, "currency": "RUB"},
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body.get("provider"), "cardlink")
        self.assertEqual(body.get("provider_label"), "Cardlink")
        self.assertEqual(body.get("payment_url"), "https://checkout.cardlink.link/pay/test-order")

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4444, ExternalOrder.provider == "cardlink").first()
            self.assertIsNotNone(row)
            self.assertEqual(str(row.plan_code or ""), "start_99")
        finally:
            s.close()

    def test_start99_public_order_blocks_after_first_purchase_flag(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4455,
                    username="start99_used",
                    uuid=str(uuid.uuid4()),
                    email="user_4455",
                    sub_type="PAID",
                    is_active=True,
                    first_purchase_done=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4455,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )

        async def _unexpected_create_rub_payment(**kwargs):
            raise AssertionError("start_99 repeat purchase must be blocked before provider invoice creation")

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _unexpected_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "lavatop", "plan_code": "start_99", "checkout_ticket": ticket, "currency": "RUB"},
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("start_99 is available only once", response.text)

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4455).first()
            self.assertIsNone(row)
        finally:
            s.close()

    def test_start99_public_order_blocks_when_user_has_paid_lavatop_start99_order(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4456,
                    username="start99_lava_paid",
                    uuid=str(uuid.uuid4()),
                    email="user_4456",
                    sub_type="FREE",
                    is_active=True,
                    first_purchase_done=False,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_start99_paid_4456",
                    provider="lavatop",
                    tg_id=4456,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="paid",
                    paid_at=self.api._utcnow(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4456,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )

        async def _unexpected_create_rub_payment(**kwargs):
            raise AssertionError("paid Lava.top start_99 history must block repeat provider invoice creation")

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _unexpected_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "lavatop", "plan_code": "start_99", "checkout_ticket": ticket, "currency": "RUB"},
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("start_99 is available only once", response.text)

        s = SessionLocal()
        try:
            rows = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4456).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].order_id, "lavatop_start99_paid_4456")
        finally:
            s.close()

    def test_start99_public_order_blocks_when_user_has_any_paid_lavatop_order(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4457,
                    username="start99_lava_paid_other_plan",
                    uuid=str(uuid.uuid4()),
                    email="user_4457",
                    sub_type="FREE",
                    is_active=True,
                    first_purchase_done=False,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_1_month_paid_4457",
                    provider="lavatop",
                    tg_id=4457,
                    plan_code="1_month",
                    source="site",
                    amount=299.0,
                    currency="RUB",
                    status="paid",
                    paid_at=self.api._utcnow(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4457,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )

        async def _unexpected_create_rub_payment(**kwargs):
            raise AssertionError("paid Lava.top history must block repeat provider invoice creation")

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _unexpected_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "lavatop", "plan_code": "start_99", "checkout_ticket": ticket, "currency": "RUB"},
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("start_99 is available only once", response.text)

        s = SessionLocal()
        try:
            rows = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4457).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].order_id, "lavatop_1_month_paid_4457")
        finally:
            s.close()

    def test_anonymous_public_lavatop_order_requires_email_and_uses_it_for_invoice(self) -> None:
        client = TestClient(self.api.app)
        capture: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            capture.update(kwargs)
            return {
                "payment_url": "https://checkout.lava.top/pay/public-order",
                "remote": {"paymentUrl": "https://checkout.lava.top/pay/public-order"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "start_99",
                    "buyer_email": "buyer@pokrov.test",
                    "currency": "RUB",
                },
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json().get("payment_url"), "https://checkout.lava.top/pay/public-order")
        custom = capture.get("custom")
        self.assertIsInstance(custom, dict)
        self.assertEqual(custom["email"], "buyer@pokrov.test")
        self.assertNotIn("tg_id", custom)

        from db import SessionLocal
        from models import ExternalOrder

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            self.assertIsNone(row.tg_id)
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["mode"], "access_key_email")
            self.assertEqual(meta["fulfillment"]["buyer_email"], "buyer@pokrov.test")
        finally:
            s.close()

    def test_lavatop_callback_marks_order_paid_with_api_key_header(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=6666,
                    username="lavatop_user",
                    uuid=str(uuid.uuid4()),
                    email="user_6666",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_bot_6666_test",
                    provider="lavatop",
                    tg_id=6666,
                    plan_code="start_99",
                    source="bot",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "7ea82675-4ded-4133-95a7-a6efbaf165cc",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "timestamp": "2026-04-26T10:00:00Z",
            "clientUtm": {
                "utm_content": "lavatop_bot_6666_test",
                "utm_medium": "bot",
                "utm_campaign": "open_beta",
                "utm_term": "start_99",
            },
            "tg_id": "6666",
            "plan_code": "start_99",
            "source": "bot",
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json().get("ok"))
        self.assertTrue(response.json().get("activated"))

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.provider == "lavatop", ExternalOrder.order_id == "lavatop_bot_6666_test").first()
            event = s.query(ExternalPaymentEvent).filter(ExternalPaymentEvent.provider == "lavatop").first()
            user = s.query(User).filter(User.tg_id == 6666).first()
            self.assertIsNotNone(row)
            self.assertIsNotNone(event)
            self.assertIsNotNone(user)
            self.assertEqual(str(row.status or ""), "paid")
            self.assertEqual(str(event.external_id or ""), "7ea82675-4ded-4133-95a7-a6efbaf165cc")
            self.assertTrue(bool(event.signature_ok))
            self.assertEqual(str(user.sub_type or ""), "PAID")
        finally:
            s.close()

        self.assertEqual(len(self.telegram_messages), 1)
        sent = self.telegram_messages[0]
        self.assertEqual(sent["chat_id"], 6666)
        sent_text = str(sent["text"])
        self.assertIn("Оплата прошла", sent_text)
        self.assertIn("Лучший путь: откройте POKROV", sent_text)
        self.assertIn("Ручная ссылка / QR", sent_text)
        self.assertNotIn("connect.pokrov.space", sent_text)
        self.assertNotIn("Happ", sent_text)
        self.assertNotIn("Hiddify", sent_text)
        kwargs = sent["kwargs"]
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")
        keyboard = kwargs.get("reply_markup")
        self.assertIsInstance(keyboard, dict)
        flat_buttons = [button for row in keyboard["inline_keyboard"] for button in row]
        self.assertTrue(any(button.get("callback_data") == "show_key" for button in flat_buttons))
        self.assertTrue(any(button.get("web_app") for button in flat_buttons))

    def test_lavatop_callback_behind_local_proxy_uses_webhook_auth_after_allowlist_miss(self) -> None:
        os.environ["LAVATOP_WEBHOOK_IP_ALLOWLIST"] = "158.160.60.174"
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=6688,
                    username="lavatop_proxy_user",
                    uuid=str(uuid.uuid4()),
                    email="user_6688",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_site_6688_proxy",
                    provider="lavatop",
                    tg_id=6688,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "local-proxy-contract",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {
                "utm_content": "lavatop_site_6688_proxy",
                "utm_medium": "site",
                "utm_term": "start_99",
            },
            "tg_id": "6688",
            "plan_code": "start_99",
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Forwarded-For": "127.0.0.1", "X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json().get("activated"))

        missing_key = client.post(
            "/api/payments/result/lavatop",
            json={**payload, "contractId": "local-proxy-contract-no-key"},
            headers={"X-Forwarded-For": "127.0.0.1"},
        )
        self.assertEqual(missing_key.status_code, 400, missing_key.text)
        self.assertIn("Invalid signature", missing_key.text)

    def test_lavatop_callback_does_not_extend_account_twice_for_same_order(self) -> None:
        from datetime import timedelta

        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        base_expiry = self.api._utcnow() + timedelta(days=10)
        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=6699,
                    username="lavatop_idempotent_user",
                    uuid=str(uuid.uuid4()),
                    email="user_6699",
                    sub_type="PAID",
                    is_active=True,
                    expiry_at=base_expiry,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_site_6699_idempotent",
                    provider="lavatop",
                    tg_id=6699,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    meta_json=json.dumps(
                        {"fulfillment": {"mode": "account_extend", "status": "pending_payment"}},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {
                "utm_content": "lavatop_site_6699_idempotent",
                "utm_medium": "site",
                "utm_term": "start_99",
            },
            "tg_id": "6699",
            "plan_code": "start_99",
        }
        first = client.post(
            "/api/payments/result/lavatop",
            json={**payload, "contractId": "idempotent-contract-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        second = client.post(
            "/api/payments/result/lavatop",
            json={**payload, "contractId": "idempotent-contract-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertTrue(first.json().get("activated"))
        self.assertEqual(second.json().get("activation_reason"), "already_applied")

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 6699).first()
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "lavatop_site_6699_idempotent").first()
            self.assertIsNotNone(user)
            self.assertIsNotNone(row)
            self.assertEqual(user.expiry_at, base_expiry + timedelta(days=30))
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["status"], "account_extended")
        finally:
            s.close()

    def test_lavatop_callback_issues_public_access_key_once_and_emails_it(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, GiftCard

        s = SessionLocal()
        try:
            s.add(
                ExternalOrder(
                    order_id="lavatop_site_public_key",
                    provider="lavatop",
                    tg_id=None,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    meta_json=json.dumps(
                        {
                            "buyer_email": "buyer@pokrov.test",
                            "fulfillment": {
                                "mode": "access_key_email",
                                "status": "pending_payment",
                                "buyer_email": "buyer@pokrov.test",
                            },
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        deliveries: list[dict[str, object]] = []

        async def _fake_deliver_payment_access_key(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "kind": "payment_access_key", "email": kwargs["email"], "mode": "webhook"}

        old_deliver = self.api.deliver_payment_access_key
        try:
            self.api.deliver_payment_access_key = _fake_deliver_payment_access_key
            payload = {
                "eventType": "payment.success",
                "contractId": "public-key-contract-1",
                "amount": 99,
                "currency": "RUB",
                "status": "completed",
                "clientUtm": {
                    "utm_content": "lavatop_site_public_key",
                    "utm_medium": "site",
                    "utm_term": "start_99",
                },
            }
            first = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            second = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = old_deliver

        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json().get("activated"))
        self.assertEqual(second.status_code, 200, second.text)
        self.assertTrue(second.json().get("duplicate"))
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["email"], "buyer@pokrov.test")
        self.assertTrue(str(deliveries[0]["access_key"]).startswith("POKROV-"))

        s = SessionLocal()
        try:
            cards = s.query(GiftCard).all()
            row = s.query(ExternalOrder).filter(ExternalOrder.provider == "lavatop", ExternalOrder.order_id == "lavatop_site_public_key").first()
            self.assertEqual(len(cards), 1)
            self.assertEqual(str(cards[0].card_type or ""), "start_99")
            self.assertIsNotNone(row)
            self.assertEqual(str(row.status or ""), "paid")
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["status"], "email_sent")
        finally:
            s.close()

    def test_lavatop_paid_callback_amount_mismatch_goes_to_manual_review(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, GiftCard, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=7777,
                    username="mismatch_lava",
                    uuid=str(uuid.uuid4()),
                    email="user_7777",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_bot_7777_mismatch",
                    provider="lavatop",
                    tg_id=7777,
                    plan_code="start_99",
                    source="bot",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "amount-mismatch-contract",
            "amount": 1,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "lavatop_bot_7777_mismatch", "utm_term": "start_99"},
            "tg_id": "7777",
            "plan_code": "start_99",
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body.get("status"), "manual_review")
        self.assertFalse(body.get("activated"))
        self.assertEqual(body.get("activation_reason"), "amount_mismatch")

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "lavatop_bot_7777_mismatch").first()
            user = s.query(User).filter(User.tg_id == 7777).first()
            cards = s.query(GiftCard).all()
            self.assertEqual(str(row.status or ""), "manual_review")
            self.assertEqual(str(user.sub_type or ""), "FREE")
            self.assertEqual(cards, [])
        finally:
            s.close()

    def test_lavatop_callback_rejects_invalid_webhook_api_key(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "eventType": "payment.success",
            "contractId": "0ea82675-4ded-4133-95a7-a6efbaf165cc",
            "status": "completed",
            "clientUtm": {"utm_content": "lavatop_bot_bad_key"},
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "wrong_key"},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Invalid signature", response.text)

    def test_pally_callback_marks_order_paid(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder

        s = SessionLocal()
        try:
            s.add(
                ExternalOrder(
                    order_id="pally_bot_5555_test",
                    provider="pally",
                    tg_id=5555,
                    plan_code="start_99",
                    source="bot",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        amount = "99.00"
        order_id = "pally_bot_5555_test"
        sign = hashlib.md5(f"{amount}:{order_id}:pally_token_test".encode("utf-8")).hexdigest().upper()
        payload = {
            "InvId": order_id,
            "OutSum": amount,
            "Status": "paid",
            "SignatureValue": sign,
            "TrsId": "pally_tx_5555",
            "us_tg_id": "5555",
            "us_plan_code": "start_99",
            "us_source": "bot",
        }
        response = client.post("/api/payments/result/pally", data=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json().get("ok"))

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.provider == "pally", ExternalOrder.order_id == order_id).first()
            self.assertIsNotNone(row)
            self.assertEqual(str(row.status or ""), "paid")
        finally:
            s.close()

    def test_parse_freekassa_payment_url_uses_source_shop_fallback(self) -> None:
        url = self.api._parse_freekassa_payment_url({}, "fk_site_order_1", source="bot")
        self.assertIn("69963", url)
        self.assertIn("fk_site_order_1", url)

    def test_public_plans_and_admin_plans_crud(self) -> None:
        client = TestClient(self.api.app)
        admin_hdrs = self._auth_headers(9999, "admin")

        pub_before = client.get("/api/public/plans")
        self.assertEqual(pub_before.status_code, 200, pub_before.text)
        self.assertTrue(any((p.get("code") == "start_99") for p in pub_before.json().get("plans", [])))

        create = client.post(
            "/api/admin/plans",
            headers=admin_hdrs,
            json={
                "code": "special_45",
                "label": "Special 45",
                "amount_rub": 459,
                "amount_stars": 459,
                "days": 45,
                "device_limit": 2,
                "node_policy": "paid_pool",
                "badge": "Test",
                "is_active": True,
                "sort_order": 5,
            },
        )
        self.assertEqual(create.status_code, 200, create.text)

        rows = client.get("/api/admin/plans", headers=admin_hdrs)
        self.assertEqual(rows.status_code, 200, rows.text)
        self.assertTrue(any((p.get("code") == "special_45") for p in rows.json().get("plans", [])))

        patch = client.patch(
            "/api/admin/plans/special_45",
            headers=admin_hdrs,
            json={"amount_rub": 499, "is_active": False, "sort_order": 55},
        )
        self.assertEqual(patch.status_code, 200, patch.text)

        remove = client.delete("/api/admin/plans/special_45", headers=admin_hdrs)
        self.assertEqual(remove.status_code, 200, remove.text)

    def test_public_live_updates_and_admin_live_updates_crud(self) -> None:
        client = TestClient(self.api.app)
        admin_hdrs = self._auth_headers(9999, "admin")

        public_rows = client.get("/api/public/live-updates")
        self.assertEqual(public_rows.status_code, 200, public_rows.text)
        self.assertGreaterEqual(len(public_rows.json().get("updates", [])), 1)

        create = client.post(
            "/api/admin/live-updates",
            headers=admin_hdrs,
            json={
                "title": "Node maintenance completed",
                "summary": "New route profile is online.",
                "channel_username": "pokrov_vpn",
                "post_id": 999,
                "published_at": "2026-02-15T10:00:00",
                "is_active": True,
                "sort_order": 1,
            },
        )
        self.assertEqual(create.status_code, 200, create.text)
        update_id = int(create.json().get("id") or 0)
        self.assertGreater(update_id, 0)

        patch = client.patch(
            f"/api/admin/live-updates/{update_id}",
            headers=admin_hdrs,
            json={"title": "Node maintenance done", "summary": "Fresh route profile online.", "post_id": 1001, "sort_order": 2},
        )
        self.assertEqual(patch.status_code, 200, patch.text)

        rows = client.get("/api/admin/live-updates", headers=admin_hdrs)
        self.assertEqual(rows.status_code, 200, rows.text)
        found = next((r for r in rows.json().get("updates", []) if int(r.get("id") or 0) == update_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(str(found.get("channel_username") or ""), "pokrov_vpn")
        self.assertEqual(int(found.get("post_id") or 0), 1001)
        self.assertEqual(str(found.get("tg_link") or ""), "https://t.me/pokrov_vpn/1001")

        remove = client.delete(f"/api/admin/live-updates/{update_id}", headers=admin_hdrs)
        self.assertEqual(remove.status_code, 200, remove.text)


if __name__ == "__main__":
    unittest.main()
