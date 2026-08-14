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
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient


class ApiPaymentCallbacksTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str((Path(self._tmp.name) / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env: dict[str, str | None] = {}
        for k in (
            "DATABASE_URL",
            "BOT_TOKEN",
            "FREEKASSA_SIGNING_SECRET",
            "FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED",
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
            "LAVATOP_OFFER_ID_START_99",
            "LAVATOP_DYNAMIC_AMOUNT_ENABLED",
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
        # Legacy generic callback coverage is explicit. Production defaults to SCI-only.
        os.environ["FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED"] = "true"
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
        os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = "true"
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
            "acquisition_service",
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
    def _freekassa_order_meta(
        *,
        plan_code: str = "1_month",
        duration_days: int = 30,
        amount_rub: str = "239.00",
        currency: str = "RUB",
        source: str = "site",
    ) -> str:
        return json.dumps(
            {
                "entitlement_snapshot": {
                    "plan_code": plan_code,
                    "duration_days": duration_days,
                    "amount_rub": amount_rub,
                    "currency": currency,
                    "source": source,
                },
                "fulfillment": {"mode": "account_extend", "status": "pending_payment"},
            },
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
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

    def _auth_headers(self, tg_id: int, username: str) -> dict[str, str]:
        init_data = self._sign_telegram_init_data(
            bot_token="test_bot_token_123",
            tg_id=tg_id,
            username=username,
        )
        return {"X-Telegram-Init-Data": init_data}

    def _execute_admin_intent(
        self,
        client: TestClient,
        *,
        action: str,
        target_type: str,
        target_id: str | int,
        method: str,
        path: str,
        payload: dict,
    ):
        admin_headers = self._auth_headers(9999, "admin")
        prepared = client.post(
            "/api/admin/action-intents",
            headers=admin_headers,
            json={
                "action": action,
                "target": {"type": target_type, "id": str(target_id)},
                "payload": payload,
            },
        )
        self.assertEqual(prepared.status_code, 200, prepared.text)
        challenge = str(prepared.json()["confirmation_challenge"])
        return client.request(
            method,
            path,
            headers={
                **admin_headers,
                "X-Admin-Intent-Id": str(prepared.json()["intent_id"]),
                "X-Admin-Idempotency-Key": str(uuid.uuid4()),
                "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
            },
            json=payload,
        )

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
        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=1001,
                    username="callback_idempotent",
                    uuid=str(uuid.uuid4()),
                    email="user_1001",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-1001",
                    provider="freekassa",
                    tg_id=1001,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()
        payload = {
            "order_id": "order-1001",
            "external_tx_id": "tx-abc-1",
            "amount": "239.00",
            "currency": "RUB",
            "status": "paid",
            "tg_id": "1001",
            "plan_code": "1_month",
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

    def test_callback_body_cap_rejects_oversized_payload_before_parse(self) -> None:
        client = TestClient(self.api.app)
        old_limit = self.api.PAYMENT_CALLBACK_MAX_BYTES
        self.api.PAYMENT_CALLBACK_MAX_BYTES = 16
        try:
            r = client.post(
                "/api/payments/result/freekassa",
                data=b'{"order_id":"too-large-for-test"}',
                headers={"Content-Type": "application/json", "X-Signature": "invalid"},
            )
        finally:
            self.api.PAYMENT_CALLBACK_MAX_BYTES = old_limit
        self.assertEqual(r.status_code, 413, r.text)

    def test_invalid_callback_payload_is_redacted_before_persist(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "order_id": "order-redact-1",
            "external_tx_id": "tx-redact-1",
            "status": "paid",
            "signature": "do-not-store",
            "buyer_email": "buyer@example.test",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        r = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": "invalid"},
        )
        self.assertEqual(r.status_code, 400, r.text)

        from db import SessionLocal
        from models import ExternalPaymentEvent

        s = SessionLocal()
        try:
            event = (
                s.query(ExternalPaymentEvent)
                .filter(ExternalPaymentEvent.external_id == "tx-redact-1")
                .first()
            )
            self.assertIsNotNone(event)
            stored = event.payload_json
            self.assertNotIn("do-not-store", stored)
            self.assertNotIn("buyer@example.test", stored)
            self.assertIn("[redacted]", stored)
        finally:
            s.close()

    def test_invalid_signature_does_not_poison_later_valid_callback(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2002,
                    username="callback_signature_retry",
                    uuid=str(uuid.uuid4()),
                    email="user_2002",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="order-2002",
                    provider="freekassa",
                    tg_id=2002,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()
        payload = {
            "order_id": "order-2002",
            "external_tx_id": "tx-abc-2b",
            "status": "paid",
            "amount": "239.00",
            "currency": "RUB",
            "tg_id": "2002",
            "plan_code": "1_month",
        }
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
                    amount=239.0,
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
                    amount=239.0,
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

        repeated = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertTrue(repeated.json().get("duplicate"))

        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent

        s = SessionLocal()
        try:
            event = s.query(ExternalPaymentEvent).filter(ExternalPaymentEvent.external_id == "tx-review-2403").first()
            row = s.query(ExternalOrder).filter(ExternalOrder.order_id == "order-review-2403").first()
            self.assertIsNotNone(event)
            self.assertIsNone(row)
            self.assertTrue(bool(event.signature_ok))
            self.assertTrue(bool(event.processed_ok))
        finally:
            s.close()

    def test_freekassa_notify_alias_returns_yes_for_valid_sci(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent

        merchant_id = "69962"
        amount = "239.00"
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
        s = SessionLocal()
        try:
            self.assertIsNone(s.query(ExternalOrder).filter_by(order_id=order_id).one_or_none())
            event = s.query(ExternalPaymentEvent).filter_by(external_id="tx-fk-1").one()
            self.assertTrue(bool(event.processed_ok))
        finally:
            s.close()

    def test_freekassa_notify_rejects_bad_sci_signature(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": "239.00",
            "MERCHANT_ORDER_ID": "order-3002",
            "SIGN": "bad_signature",
            "intid": "tx-fk-2",
        }
        r = client.post("/api/payments/freekassa/notify", params=payload)
        self.assertEqual(r.status_code, 400, r.text)

    def test_freekassa_incomplete_sci_never_downgrades_to_generic_hmac(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": "239.00",
            "MERCHANT_ORDER_ID": "order-incomplete-sci",
            "status": "paid",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        signature = self._hmac_sha256("test_fk_secret", raw)

        response = client.post(
            "/api/payments/result/freekassa",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": signature},
        )

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("incomplete_sci_payload", response.text)

    def test_freekassa_generic_hmac_requires_explicit_compatibility_flag(self) -> None:
        client = TestClient(self.api.app)
        payload = {
            "order_id": "order-generic-disabled",
            "amount": "239.00",
            "currency": "RUB",
            "status": "paid",
        }
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        signature = self._hmac_sha256("test_fk_secret", raw)
        old_compat = self.api.FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED
        self.api.FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED = False
        try:
            response = client.post(
                "/api/payments/result/freekassa",
                data=raw,
                headers={"Content-Type": "application/json", "X-Signature": signature},
            )
        finally:
            self.api.FREEKASSA_GENERIC_HMAC_COMPAT_ENABLED = old_compat

        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("generic_hmac_disabled", response.text)

    def test_freekassa_generic_callback_without_state_is_not_paid(self) -> None:
        self.assertEqual(
            self.api._status_from_event(
                "result",
                {"order_id": "order-no-state"},
                signature_ok=True,
                provider="freekassa",
            ),
            "manual_review",
        )

    def test_freekassa_decimal_amount_and_currency_are_strict(self) -> None:
        self.assertEqual(self.api._payload_amount_decimal({"AMOUNT": "239.00"}), Decimal("239.00"))
        self.assertEqual(self.api._payload_currency({"CURRENCY": "rub"}), "RUB")
        for invalid in ("", "0", "-1", "1.001", "NaN", "Infinity"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(self.api._payload_amount_decimal({"AMOUNT": invalid}))

    def test_freekassa_shop_lookup_does_not_fallback_across_sources(self) -> None:
        self.assertEqual(self.api._fk_shop_by_source(""), {})
        self.assertEqual(self.api._fk_shop_by_source("desktop"), {})
        self.assertEqual(self.api._fk_shop_by_source("site").get("shop_id"), "69962")
        self.assertEqual(self.api._fk_shop_by_source("bot").get("shop_id"), "69963")

    def test_freekassa_paid_callback_must_match_local_order_authority(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        order_id = "fk-authority-order"
        s = SessionLocal()
        try:
            s.add(
                ExternalOrder(
                    order_id=order_id,
                    provider="freekassa",
                    tg_id=7401,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        base_payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": "239.00",
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": "signature-shape-only",
            "CURRENCY": "RUB",
            "us_tg_id": "7401",
            "us_plan_code": "1_month",
            "us_source": "site",
        }
        self.assertEqual(
            self.api._validate_paid_callback_against_order(
                provider="freekassa",
                order_id=order_id,
                payload=base_payload,
            ),
            (True, "ok"),
        )
        mismatches = (
            ({"AMOUNT": "239.01"}, "amount_mismatch"),
            ({"AMOUNT": "NaN"}, "invalid_amount"),
            ({"CURRENCY": "USD"}, "currency_mismatch"),
            ({"us_plan_code": "12_months"}, "plan_mismatch"),
            ({"us_source": "bot"}, "source_mismatch"),
            ({"MERCHANT_ID": "69963"}, "merchant_source_mismatch"),
        )
        for changed, expected_reason in mismatches:
            with self.subTest(changed=changed):
                payload = dict(base_payload)
                payload.update(changed)
                self.assertEqual(
                    self.api._validate_paid_callback_against_order(
                        provider="freekassa",
                        order_id=order_id,
                        payload=payload,
                    ),
                    (False, expected_reason),
                )

    def test_freekassa_callback_cannot_mutate_existing_order_authority(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        order_id = "fk-immutable-order"
        s = SessionLocal()
        try:
            s.add(
                ExternalOrder(
                    order_id=order_id,
                    provider="freekassa",
                    tg_id=7402,
                    plan_code="1_month",
                    source="site",
                    campaign="canonical-campaign",
                    promo_code="CANONICAL",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
            row = self.api._upsert_external_order(
                s,
                provider="freekassa",
                order_id=order_id,
                payload={
                    "tg_id": "999999",
                    "plan_code": "12_months",
                    "source": "bot",
                    "campaign": "callback-campaign",
                    "promo_code": "CALLBACK",
                    "AMOUNT": "999.00",
                    "CURRENCY": "USD",
                },
                status="manual_review",
                mark_paid=False,
            )
            s.commit()
            self.assertIsNotNone(row)
            self.assertEqual(row.tg_id, 7402)
            self.assertEqual(row.plan_code, "1_month")
            self.assertEqual(row.source, "site")
            self.assertEqual(row.campaign, "canonical-campaign")
            self.assertEqual(row.promo_code, "CANONICAL")
            self.assertEqual(float(row.amount or 0), 239.0)
            self.assertEqual(row.currency, "RUB")
            self.assertEqual(row.status, "manual_review")
        finally:
            s.close()

    def test_freekassa_unknown_order_is_never_created_from_callback(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        s = SessionLocal()
        try:
            row = self.api._upsert_external_order(
                s,
                provider="freekassa",
                order_id="fk-unknown-callback-order",
                payload={"AMOUNT": "239.00", "CURRENCY": "RUB", "status": "failed"},
                status="failed",
                mark_paid=False,
            )
            s.commit()
            self.assertIsNone(row)
            self.assertIsNone(
                s.query(ExternalOrder).filter_by(order_id="fk-unknown-callback-order").one_or_none()
            )
        finally:
            s.close()

    def test_signed_provider_callback_cannot_overwrite_created_order_attribution(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        order_id = "lavatop-immutable-attribution"
        s = SessionLocal()
        try:
            s.add(
                ExternalOrder(
                    order_id=order_id,
                    provider="lavatop",
                    source="telegram_ads",
                    campaign="aug_launch",
                    acquisition_session_id="acquisition-session-a",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json="{}",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
            row = self.api._upsert_external_order(
                s,
                provider="lavatop",
                order_id=order_id,
                payload={
                    "source": "callback_override",
                    "campaign": "callback_override",
                    "status": "completed",
                },
                status="paid",
                mark_paid=True,
            )
            s.commit()

            self.assertIsNotNone(row)
            self.assertEqual(row.source, "telegram_ads")
            self.assertEqual(row.campaign, "aug_launch")
            self.assertEqual(row.acquisition_session_id, "acquisition-session-a")
            self.assertEqual(row.status, "paid")
        finally:
            s.close()

    def test_freekassa_fulfillment_rejects_missing_entitlement_snapshot(self) -> None:
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=7403,
                    username="missing_snapshot",
                    uuid=str(uuid.uuid4()),
                    email="user_7403",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="fk-missing-snapshot",
                    provider="freekassa",
                    tg_id=7403,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        self.assertEqual(
            self.api._apply_external_paid_order(
                provider="freekassa",
                order_id="fk-missing-snapshot",
                payload={"us_plan_code": "1_month"},
            ),
            (False, "missing_entitlement_snapshot"),
        )
        s = SessionLocal()
        try:
            self.assertEqual(
                s.query(EntitlementGrant)
                .filter_by(provider="freekassa", external_order_id="fk-missing-snapshot")
                .count(),
                0,
            )
            self.assertEqual(s.query(User).filter_by(tg_id=7403).one().sub_type, "FREE")
        finally:
            s.close()

    def test_freekassa_fulfillment_uses_immutable_duration_snapshot(self) -> None:
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=7404,
                    username="snapshot_duration",
                    uuid=str(uuid.uuid4()),
                    email="user_7404",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="fk-snapshot-duration",
                    provider="freekassa",
                    tg_id=7404,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(duration_days=17),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        activated, reason = self.api._apply_external_paid_order(
            provider="freekassa",
            order_id="fk-snapshot-duration",
            payload={"us_plan_code": "1_month"},
        )
        self.assertTrue(activated, reason)
        s = SessionLocal()
        try:
            grant = (
                s.query(EntitlementGrant)
                .filter_by(provider="freekassa", external_order_id="fk-snapshot-duration")
                .one()
            )
            self.assertEqual(grant.plan_code, "1_month")
            self.assertEqual(grant.duration_days, 17)
        finally:
            s.close()

    def test_admin_plan_key_then_real_payment_still_starts_first_referral_hold(self) -> None:
        client = TestClient(self.api.app)

        from datetime import datetime, timedelta
        from db import SessionLocal
        from models import ExternalOrder, PointsLedger, ReferralBonusQueue, ReferralRelationship, ReferralTransition, User

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
            invited_expiry = datetime.utcnow() + timedelta(days=5)
            invited = User(
                    tg_id=2003,
                    username="invited",
                    uuid=str(uuid.uuid4()),
                    email="user_2003",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                    referrer_id=2002,
                    first_purchase_done=False,
                    expiry_at=invited_expiry,
                )
            self.api._apply_access_key_to_user(
                user=invited,
                meta={"kind": "plan", "days": 30, "plan_code": "1_month"},
                now=datetime.utcnow(),
            )
            self.assertFalse(bool(invited.first_purchase_done))
            s.add(invited)
            s.add(
                ExternalOrder(
                    order_id="order-ref-first-1",
                    provider="freekassa",
                    tg_id=2003,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        merchant_id = "69962"
        amount = "239.00"
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
        replay_response = client.post("/api/payments/freekassa/notify", params=payload)
        self.assertEqual(replay_response.status_code, 200, replay_response.text)

        s = SessionLocal()
        try:
            invited = s.query(User).filter(User.tg_id == 2003).first()
            referrer = s.query(User).filter(User.tg_id == 2002).first()
            relationship = s.query(ReferralRelationship).filter_by(referred_account_id=invited.account_id).one_or_none()
            points_rows = (
                s.query(PointsLedger)
                .filter(PointsLedger.tg_id == 2002, PointsLedger.reason.like("referral_earned%"), PointsLedger.ref_tg_id == 2003)
                .all()
            )
            self.assertIsNotNone(invited)
            self.assertIsNotNone(referrer)
            self.assertIsNotNone(relationship)
            self.assertEqual(relationship.referrer_account_id, referrer.account_id)
            self.assertEqual(relationship.status, "holding")
            self.assertEqual(relationship.hold_until - relationship.first_payment_at, timedelta(hours=72))
            self.assertEqual(s.query(ReferralBonusQueue).filter_by(order_id=order_id).count(), 0)
            self.assertEqual(
                s.query(ReferralTransition).filter_by(transition_kind="first_payment_held").count(),
                1,
            )
            self.assertEqual(len(points_rows), 1)
            self.assertGreater(int(points_rows[0].delta_points or 0), 0)
            self.assertTrue(bool(invited.first_purchase_done))
            self.assertGreaterEqual(invited.expiry_at, invited_expiry + timedelta(days=30))
            self.assertEqual(int(referrer.referral_count or 0), 1)
            self.assertTrue(bool(referrer.expiry_at and referrer.expiry_at < datetime.utcnow() + timedelta(days=30)))
        finally:
            s.close()

    def test_freekassa_new_order_is_closed_but_historical_operations_use_remote_api_wrapper(self) -> None:
        client = TestClient(self.api.app)
        hdrs = self._auth_headers(1001, "alice")

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
                )
            )
            s.add(
                ExternalOrder(
                    order_id="historical-freekassa-order-1001",
                    provider="freekassa",
                    tg_id=1001,
                    plan_code="1_month",
                    source="site",
                    amount=239.0,
                    currency="RUB",
                    status="pending",
                    meta_json=self._freekassa_order_meta(),
                    created_at=self.api._utcnow(),
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
            self.assertEqual(create.status_code, 503, create.text)
            self.assertIn("freekassa is not enabled for public RUB checkout", create.text)
            self.assertEqual(calls, [])

            order_id = "historical-freekassa-order-1001"
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
        captured: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            captured.update(kwargs)
            return {
                "payment_url": "https://app.lava.top/pay/pending-discount-test",
                "remote": {"payment_url": "https://app.lava.top/pay/pending-discount-test"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            r = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "1_month",
                    "checkout_ticket": ticket,
                    "currency": "RUB",
                },
            )
        finally:
            self.api.create_rub_payment = old_create
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 20)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 239)
        self.assertEqual(int(body.get("amount_rub") or 0), 191)
        self.assertEqual(body.get("provider"), "lavatop")
        self.assertEqual(body.get("payment_url"), "https://app.lava.top/pay/pending-discount-test")
        self.assertEqual(captured.get("provider"), "lavatop")
        self.assertEqual(int(captured.get("amount_rub") or 0), 191)
        self.assertEqual(captured.get("custom", {}).get("campaign"), "launch_w1")
        self.assertEqual(captured.get("custom", {}).get("promo_code"), "WELCOME20")

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 1001).first()
            self.assertIsNotNone(user)
            self.assertEqual(int(user.pending_discount_pct or 0), 20)
            self.assertEqual(str(user.pending_discount_code or ""), "WELCOME20")
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 1001, ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            self.assertIn("\"discount_pct\":20", str(row.meta_json or ""))
            self.assertIn("\"payment_url\":\"https://app.lava.top/pay/pending-discount-test", str(row.meta_json or ""))
            meta = json.loads(row.meta_json or "{}")
            self.assertEqual(meta.get("entitlement_snapshot", {}).get("plan_code"), "1_month")
            self.assertEqual(meta.get("entitlement_snapshot", {}).get("duration_days"), 30)
            self.assertEqual(meta.get("entitlement_snapshot", {}).get("amount_rub"), "191.00")
            self.assertEqual(meta.get("entitlement_snapshot", {}).get("currency"), "RUB")
            self.assertEqual(meta.get("entitlement_snapshot", {}).get("source"), "site")
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
        captured: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            captured.update(kwargs)
            return {
                "payment_url": "https://app.lava.top/pay/referral-discount-test",
                "remote": {"payment_url": "https://app.lava.top/pay/referral-discount-test"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            r = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "1_month",
                    "checkout_ticket": ticket,
                    "currency": "RUB",
                },
            )
        finally:
            self.api.create_rub_payment = old_create
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 20)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 239)
        self.assertEqual(int(body.get("amount_rub") or 0), 191)
        self.assertEqual(body.get("provider"), "lavatop")
        self.assertEqual(body.get("payment_url"), "https://app.lava.top/pay/referral-discount-test")
        self.assertEqual(captured.get("provider"), "lavatop")
        self.assertEqual(int(captured.get("amount_rub") or 0), 191)

    def test_lavatop_public_order_applies_direct_promo_to_non_start99_plan_with_card(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, PromoCode, PromoUsage, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4449,
                    username="promo_card",
                    uuid=str(uuid.uuid4()),
                    email="user_4449",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(PromoCode(code="WELCOME20", promo_type="discount", value=20, uses_left=-1))
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4449,
            plan_code="1_month",
            promo_code="WELCOME20",
            campaign_key="launch_w1",
            source="bot",
        )
        captured: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            captured.update(kwargs)
            return {
                "payment_url": "https://app.lava.top/pay/card-promo-test",
                "remote": {"payment_url": "https://app.lava.top/pay/card-promo-test"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "1_month",
                    "checkout_ticket": ticket,
                    "currency": "RUB",
                    "payment_method": "card",
                },
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 20)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 239)
        self.assertEqual(int(body.get("amount_rub") or 0), 191)
        self.assertEqual(captured["provider"], "lavatop")
        self.assertEqual(int(captured["amount_rub"]), 191)
        self.assertEqual(captured["custom"]["promo_code"], "WELCOME20")
        self.assertEqual(captured["custom"]["payment_method"], "card")
        self.assertEqual(captured["custom"]["lavatop_payment_provider"], "SMART_GLOCAL")
        self.assertEqual(captured["custom"]["lavatop_payment_method"], "CARD")

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4449, ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            meta = json.loads(row.meta_json or "{}")
            self.assertEqual(meta.get("request", {}).get("promo_code"), "WELCOME20")
            self.assertEqual(meta.get("request", {}).get("payment_method"), "card")
            self.assertEqual(meta.get("pricing", {}).get("direct_discount_pct"), 20)
            self.assertEqual(meta.get("pricing", {}).get("direct_discount_source"), "promo_code")
            self.assertIsNone(s.query(PromoUsage).filter(PromoUsage.promo_code == "WELCOME20").first())
        finally:
            s.close()

    def test_admin_gift_does_not_consume_first_successful_payment_authority(self) -> None:
        from datetime import datetime
        from models import User

        user = User(
            tg_id=2010,
            sub_type="FREE",
            current_plan_code="free_monthly",
            expiry_at=datetime(2026, 7, 20),
            is_active=True,
            first_purchase_done=False,
        )
        self.api._apply_access_key_to_user(
            user=user,
            meta={"kind": "legacy_gift", "days": 30, "plan_code": "1_month"},
            now=datetime(2026, 7, 12),
        )
        self.assertFalse(bool(user.first_purchase_done))

        self.api._apply_access_key_to_user(
            user=user,
            meta={"kind": "plan", "days": 30, "plan_code": "1_month"},
            now=datetime(2026, 7, 12),
        )
        self.assertFalse(bool(user.first_purchase_done))

    def test_start99_public_order_ignores_referral_and_pending_discounts(self) -> None:
        client = TestClient(self.api.app)

        from datetime import datetime, timedelta
        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=2004,
                    username="ref_start99",
                    uuid=str(uuid.uuid4()),
                    email="user_2004",
                    sub_type="PAID",
                    is_active=True,
                    tos_accepted=True,
                    expiry_at=datetime.utcnow() + timedelta(days=30),
                )
            )
            s.add(
                User(
                    tg_id=2005,
                    username="start99_invited",
                    uuid=str(uuid.uuid4()),
                    email="user_2005",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                    referrer_id=2004,
                    first_purchase_done=False,
                    pending_discount_pct=20,
                    pending_discount_code="WELCOME20",
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=2005,
            plan_code="start_99",
            promo_code="WELCOME20",
            campaign_key="start99_no_discount",
            source="site",
        )
        captured: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            captured.update(kwargs)
            return {
                "payment_url": "https://app.lava.top/pay/start99-no-discount-test",
                "remote": {"payment_url": "https://app.lava.top/pay/start99-no-discount-test"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "start_99",
                    "checkout_ticket": ticket,
                    "currency": "RUB",
                },
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertFalse(body.get("discount_applied"))
        self.assertEqual(int(body.get("discount_pct") or 0), 0)
        self.assertEqual(int(body.get("base_amount_rub") or 0), 99)
        self.assertEqual(int(body.get("amount_rub") or 0), 99)
        self.assertEqual(captured.get("provider"), "lavatop")
        self.assertEqual(int(captured.get("amount_rub") or 0), 99)

        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == 2005).first()
            self.assertIsNotNone(user)
            self.assertEqual(int(user.pending_discount_pct or 0), 20)
            self.assertEqual(str(user.pending_discount_code or ""), "WELCOME20")
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 2005, ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            meta = json.loads(row.meta_json or "{}")
            self.assertEqual(meta.get("request", {}).get("requested_promo_code"), "WELCOME20")
            self.assertEqual(meta.get("request", {}).get("promo_code"), "")
            self.assertEqual(meta.get("pricing", {}).get("discount_pct"), 0)
            self.assertEqual(meta.get("pricing", {}).get("final_amount_rub"), 99)
        finally:
            s.close()

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
        self.assertEqual([row.get("code") for row in rows], ["lavatop"])
        self.assertEqual(
            rows[0].get("supported_plan_codes"),
            ["start_99", "1_month", "3_months", "6_months", "9_months", "12_months"],
        )

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
        self.assertIn("freekassa is not enabled for public RUB checkout", response.text)

    def test_public_checkout_url_rewrites_legacy_portal_privacy_host(self) -> None:
        old_url = getattr(self.api.Settings, "PAY_CHECKOUT_URL", "")
        try:
            self.api.Settings.PAY_CHECKOUT_URL = "https://portal-privacy.online/checkout?from=bot"
            self.assertEqual(self.api._public_checkout_url(), "https://pay.pokrov.space/checkout/")
        finally:
            self.api.Settings.PAY_CHECKOUT_URL = old_url

    def test_public_order_rejects_stale_non_lava_provider_configuration(self) -> None:
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

        response = client.post(
            "/api/payments/orders/create-public",
            json={"provider": "cardlink", "plan_code": "start_99", "checkout_ticket": ticket, "currency": "RUB"},
        )

        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("public RUB checkout", response.text)

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4444, ExternalOrder.provider == "cardlink").first()
            self.assertIsNone(row)
        finally:
            s.close()

    def test_public_order_rejects_lava_plan_without_exact_offer_readiness(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4450,
                    username="plan_gate",
                    uuid=str(uuid.uuid4()),
                    email="user_4450",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4450,
            plan_code="1_month",
            promo_code="",
            campaign_key="",
            source="bot",
        )
        old_global = os.environ.pop("LAVATOP_OFFER_ID", None)
        old_dynamic = os.environ.pop("LAVATOP_DYNAMIC_AMOUNT_ENABLED", None)
        os.environ["LAVATOP_OFFER_ID_START_99"] = "start-only-offer"
        try:
            response = client.post(
                "/api/payments/orders/create-public",
                json={"provider": "lavatop", "plan_code": "1_month", "checkout_ticket": ticket, "currency": "RUB"},
            )
        finally:
            if old_global is not None:
                os.environ["LAVATOP_OFFER_ID"] = old_global
            if old_dynamic is not None:
                os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = old_dynamic

        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("plan is not configured", response.text.lower())
        s = SessionLocal()
        try:
            self.assertIsNone(
                s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4450, ExternalOrder.provider == "lavatop").first()
            )
        finally:
            s.close()

    def test_lavatop_public_order_forwards_selected_payment_method(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4448,
                    username="method_choice",
                    uuid=str(uuid.uuid4()),
                    email="user_4448",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4448,
            plan_code="start_99",
            promo_code="",
            campaign_key="",
            source="bot",
        )
        captured: dict[str, object] = {}

        async def _fake_create_rub_payment(**kwargs):
            captured.update(kwargs)
            return {
                "payment_url": "https://app.lava.top/pay/sbp-test",
                "remote": {"payment_url": "https://app.lava.top/pay/sbp-test"},
            }

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _fake_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "start_99",
                    "checkout_ticket": ticket,
                    "currency": "RUB",
                    "payment_method": "sbp",
                },
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(captured["provider"], "lavatop")
        self.assertEqual(captured["custom"]["payment_method"], "sbp")
        self.assertEqual(captured["custom"]["lavatop_payment_provider"], "PAY2ME")
        self.assertEqual(captured["custom"]["lavatop_payment_method"], "SBP")

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4448, ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            meta = json.loads(row.meta_json or "{}")
            self.assertEqual(meta.get("payment_method", {}).get("choice"), "sbp")
            self.assertEqual(meta.get("payment_method", {}).get("lavatop_payment_provider"), "PAY2ME")
            self.assertEqual(meta.get("payment_method", {}).get("lavatop_payment_method"), "SBP")
        finally:
            s.close()

    def test_start99_public_order_blocks_after_actual_paid_order(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            user = User(
                    tg_id=4455,
                    username="start99_used",
                    uuid=str(uuid.uuid4()),
                    email="user_4455",
                    sub_type="PAID",
                    is_active=True,
                    first_purchase_done=True,
                    tos_accepted=True,
                )
            s.add_all(
                [
                    user,
                    ExternalOrder(
                        order_id="start99-prior-paid-order",
                        tg_id=4455,
                        provider="lavatop",
                        plan_code="1_month",
                        status="paid",
                        amount=239,
                        currency="RUB",
                    ),
                ]
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
        self.assertEqual(response.json()["detail"]["code"], "start_99_already_used")

        s = SessionLocal()
        try:
            rows = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4455).all()
            self.assertEqual([row.order_id for row in rows], ["start99-prior-paid-order"])
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
        self.assertEqual(response.json()["detail"]["code"], "start_99_already_used")

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
        self.assertEqual(response.json()["detail"]["code"], "start_99_already_used")

        s = SessionLocal()
        try:
            rows = s.query(ExternalOrder).filter(ExternalOrder.tg_id == 4457).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].order_id, "lavatop_1_month_paid_4457")
        finally:
            s.close()

    def test_start99_eligibility_returns_disabled_state_and_regular_month_ticket(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=4458,
                    username="eligibility_paid",
                    uuid=str(uuid.uuid4()),
                    email="user_4458",
                    sub_type="PAID",
                    is_active=True,
                    first_purchase_done=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="eligibility-prior-paid-order",
                    tg_id=4458,
                    provider="lavatop",
                    plan_code="1_month",
                    status="paid",
                    amount=239,
                    currency="RUB",
                )
            )
            s.commit()
        finally:
            s.close()

        ticket = self.api._create_checkout_ticket(
            tg_id=4458,
            plan_code="start_99",
            promo_code="",
            campaign_key="campaign-a",
            source="bot",
        )
        response = client.post(
            "/api/payments/start-99-eligibility",
            json={"checkout_ticket": ticket},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["known"])
        self.assertFalse(payload["eligible"])
        self.assertEqual(payload["reason"], "start_99_already_used")
        self.assertEqual(payload["replacement_plan"], "1_month")
        replacement = self.api._parse_checkout_ticket(payload["replacement_checkout_ticket"])
        self.assertIsNotNone(replacement)
        self.assertEqual(replacement["tg_id"], 4458)
        self.assertEqual(replacement["plan_code"], "1_month")
        self.assertEqual(replacement["campaign_key"], "campaign-a")

    def test_anonymous_start99_rejects_email_with_prior_provider_confirmed_payment(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, PaymentEntitlementClaim

        s = SessionLocal()
        try:
            s.add(
                PaymentEntitlementClaim(
                    provider="lavatop",
                    order_id="anonymous-prior-paid",
                    buyer_email_norm="repeat@pokrov.test",
                    status="paid_unclaimed",
                    plan_code="1_month",
                    duration_days=30,
                    paid_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        async def _unexpected_create_rub_payment(**kwargs):
            raise AssertionError("repeat anonymous start_99 must be blocked before invoice creation")

        old_create = self.api.create_rub_payment
        try:
            self.api.create_rub_payment = _unexpected_create_rub_payment
            response = client.post(
                "/api/payments/orders/create-public",
                json={
                    "provider": "lavatop",
                    "plan_code": "start_99",
                    "buyer_email": "REPEAT@pokrov.test",
                    "currency": "RUB",
                },
            )
        finally:
            self.api.create_rub_payment = old_create

        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["detail"]["code"], "start_99_already_used")
        s = SessionLocal()
        try:
            self.assertEqual(s.query(ExternalOrder).count(), 0)
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
        from models import ExternalOrder, PaymentEntitlementClaim

        s = SessionLocal()
        try:
            row = s.query(ExternalOrder).filter(ExternalOrder.provider == "lavatop").first()
            self.assertIsNotNone(row)
            self.assertIsNone(row.tg_id)
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["mode"], "access_key_email")
            self.assertEqual(meta["fulfillment"]["buyer_email"], "buyer@pokrov.test")
            claim = s.query(PaymentEntitlementClaim).filter_by(
                provider="lavatop",
                order_id=str(row.order_id),
            ).one()
            self.assertEqual(claim.status, "pending_payment")
            self.assertEqual(claim.buyer_email_norm, "buyer@pokrov.test")
            self.assertEqual(claim.plan_code, "start_99")
            self.assertEqual(claim.duration_days, 30)
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
        self.assertTrue(first.json().get("activated"), first.text)
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
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

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
            third = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "public-key-contract-2"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = old_deliver

        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json().get("activated"))
        self.assertEqual(second.status_code, 200, second.text)
        self.assertTrue(second.json().get("duplicate"))
        self.assertEqual(third.status_code, 200, third.text)
        self.assertFalse(third.json().get("duplicate"))
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
            stored = str(row.meta_json or "")
            self.assertNotIn(str(deliveries[0]["access_key"]), stored)
            self.assertNotIn("access_key", json.loads(stored)["fulfillment"])
            events = s.query(ExternalPaymentEvent).filter_by(order_id="lavatop_site_public_key").all()
            self.assertTrue(all(str(deliveries[0]["access_key"]) not in str(event.payload_json or "") for event in events))
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["status"], "email_sent")
            claim = s.query(PaymentEntitlementClaim).filter_by(
                provider="lavatop",
                order_id="lavatop_site_public_key",
            ).one()
            self.assertEqual(claim.status, "paid_unclaimed")
            self.assertEqual(claim.fallback_gift_card_id, cards[0].id)
            self.assertEqual(
                s.query(ExternalPaymentEvent).filter_by(
                    provider="lavatop",
                    order_id="lavatop_site_public_key",
                ).count(),
                2,
            )
        finally:
            s.close()

    def test_signed_paid_event_retries_after_durable_fulfillment_failure(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, ExternalPaymentEvent, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=7801,
                    username="retry_payment",
                    uuid=str(uuid.uuid4()),
                    email="user_7801",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_retry_7801",
                    provider="lavatop",
                    tg_id=7801,
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
            "contractId": "retry-contract-7801",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "lavatop_retry_7801", "utm_term": "start_99"},
            "tg_id": "7801",
            "plan_code": "start_99",
        }
        original_fulfill = self.api._fulfill_external_paid_order
        self.api._fulfill_external_paid_order = lambda **_kwargs: (False, "forced_failure", {})
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api._fulfill_external_paid_order = original_fulfill

        self.assertEqual(first.status_code, 503, first.text)
        s = SessionLocal()
        try:
            event = s.query(ExternalPaymentEvent).filter_by(external_id="retry-contract-7801").one()
            self.assertFalse(bool(event.processed_ok))
        finally:
            s.close()

        retry = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertFalse(retry.json().get("duplicate"))
        self.assertTrue(retry.json().get("activated"))

        s = SessionLocal()
        try:
            event = s.query(ExternalPaymentEvent).filter_by(external_id="retry-contract-7801").one()
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
        finally:
            s.close()

    def test_legacy_paid_fallback_card_is_linked_without_duplicate_or_email(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        legacy_code = "POKROV-LEGACY-CALLBACK"
        s = SessionLocal()
        try:
            s.add(
                GiftCard(
                    code=legacy_code,
                    card_type="start_99",
                    created_by=0,
                    created_at=self.api._utcnow(),
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_legacy_paid_fallback",
                    provider="lavatop",
                    tg_id=None,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="paid",
                    paid_at=self.api._utcnow(),
                    meta_json=json.dumps(
                        {
                            "buyer_email": "legacy-buyer@example.test",
                            "fulfillment": {
                                "mode": "access_key_email",
                                "status": "email_sent",
                                "buyer_email": "legacy-buyer@example.test",
                                "access_key": legacy_code,
                                "email_delivery": {
                                    "status": "sent",
                                    "mode": "webhook",
                                    "http_status": 200,
                                    "error_code": None,
                                },
                            },
                        },
                        separators=(",", ":"),
                    ),
                    created_at=self.api._utcnow(),
                )
            )
            s.commit()
        finally:
            s.close()

        deliveries: list[dict[str, object]] = []

        async def _unexpected_delivery(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        base_payload = {
            "eventType": "payment.success",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {
                "utm_content": "lavatop_legacy_paid_fallback",
                "utm_term": "start_99",
            },
        }
        old_delivery = self.api.deliver_payment_access_key
        self.api.deliver_payment_access_key = _unexpected_delivery
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json={**base_payload, "contractId": "legacy-fallback-event-1"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            replay = client.post(
                "/api/payments/result/lavatop",
                json={**base_payload, "contractId": "legacy-fallback-event-1"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            second_event = client.post(
                "/api/payments/result/lavatop",
                json={**base_payload, "contractId": "legacy-fallback-event-2"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = old_delivery

        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json().get("activated"))
        self.assertEqual(first.json().get("activation_reason"), "access_key_relinked")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(second_event.status_code, 200, second_event.text)
        self.assertTrue(second_event.json().get("activated"))
        self.assertEqual(deliveries, [])

        s = SessionLocal()
        try:
            cards = s.query(GiftCard).all()
            claim = s.query(PaymentEntitlementClaim).filter_by(
                provider="lavatop",
                order_id="lavatop_legacy_paid_fallback",
            ).one()
            events = s.query(ExternalPaymentEvent).filter_by(
                provider="lavatop",
                order_id="lavatop_legacy_paid_fallback",
            ).all()
            order = s.query(ExternalOrder).filter_by(order_id="lavatop_legacy_paid_fallback").one()
            self.assertEqual(len(cards), 1)
            self.assertEqual(claim.fallback_gift_card_id, cards[0].id)
            self.assertEqual(claim.status, "paid_unclaimed")
            self.assertEqual(len(events), 2)
            self.assertTrue(all(bool(event.processed_ok) for event in events))
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 0)
            stored_meta = json.loads(order.meta_json)
            self.assertEqual(stored_meta["fulfillment"]["status"], "email_sent")
            self.assertNotIn("access_key", stored_meta["fulfillment"])
            self.assertNotIn(legacy_code, order.meta_json)
            self.assertTrue(all(legacy_code not in str(event.payload_json or "") for event in events))
        finally:
            s.close()

    def test_paid_order_is_not_downgraded_by_late_failed_or_pending_events(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import ExternalOrder, User

        s = SessionLocal()
        try:
            s.add(
                User(
                    tg_id=7802,
                    username="monotonic_payment",
                    uuid=str(uuid.uuid4()),
                    email="user_7802",
                    sub_type="FREE",
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_monotonic_7802",
                    provider="lavatop",
                    tg_id=7802,
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

        base = {
            "eventType": "payment.success",
            "amount": 99,
            "currency": "RUB",
            "clientUtm": {"utm_content": "lavatop_monotonic_7802", "utm_term": "start_99"},
            "tg_id": "7802",
            "plan_code": "start_99",
        }
        for contract_id, status in (
            ("monotonic-paid", "completed"),
            ("monotonic-failed", "failed"),
            ("monotonic-pending", "pending"),
        ):
            response = client.post(
                "/api/payments/result/lavatop",
                json={**base, "contractId": contract_id, "status": status},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            self.assertEqual(response.status_code, 200, response.text)

        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id="lavatop_monotonic_7802").one()
            self.assertEqual(order.status, "paid")
            self.assertIsNotNone(order.paid_at)
        finally:
            s.close()

    def test_refund_reverses_attached_claim_and_grant_once(self) -> None:
        client = TestClient(self.api.app)

        from db import SessionLocal
        from models import Account, AccountIdentity, EntitlementGrant, ExternalOrder, PaymentEntitlementClaim, User
        from payment_entitlement_service import attach_by_verified_email, ensure_pending_claim

        s = SessionLocal()
        try:
            s.add(Account(id="refund-account", status="active", created_source="test"))
            s.add(
                User(
                    tg_id=7803,
                    username="refund_claim_user",
                    uuid=str(uuid.uuid4()),
                    email="user_7803",
                    account_id="refund-account",
                    sub_type="FREE",
                    current_plan_code="free_monthly",
                    expiry_at=self.api._utcnow(),
                    is_active=True,
                    tos_accepted=True,
                )
            )
            s.add(
                AccountIdentity(
                    account_id="refund-account",
                    kind="email",
                    provider="email",
                    subject_norm="refund@example.test",
                    verified_at=self.api._utcnow(),
                )
            )
            s.add(
                ExternalOrder(
                    order_id="lavatop_refund_claim",
                    provider="lavatop",
                    tg_id=None,
                    plan_code="start_99",
                    source="site",
                    amount=99.0,
                    currency="RUB",
                    status="pending",
                    meta_json=json.dumps({"buyer_email": "refund@example.test"}),
                    created_at=self.api._utcnow(),
                )
            )
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="lavatop_refund_claim",
                buyer_email="refund@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            attach_by_verified_email(
                s,
                provider="lavatop",
                order_id="lavatop_refund_claim",
                buyer_email="refund@example.test",
                account_id="refund-account",
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        base = {
            "amount": 99,
            "currency": "RUB",
            "clientUtm": {"utm_content": "lavatop_refund_claim", "utm_term": "start_99"},
        }
        paid = client.post(
            "/api/payments/result/lavatop",
            json={**base, "contractId": "refund-paid-event", "status": "completed"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        refunded = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "refund-event", "status": "refunded"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        repeated = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "refund-event", "status": "refunded"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(paid.status_code, 200, paid.text)
        self.assertEqual(refunded.status_code, 200, refunded.text)
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertTrue(repeated.json().get("duplicate"))

        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="lavatop_refund_claim").one()
            grant = s.get(EntitlementGrant, claim.grant_id)
            order = s.query(ExternalOrder).filter_by(order_id="lavatop_refund_claim").one()
            self.assertEqual(claim.status, "reversed")
            self.assertEqual(claim.reversal_reason, "refunded")
            self.assertEqual(grant.status, "reversed")
            self.assertEqual(grant.reversed_at, claim.reversed_at)
            self.assertEqual(order.status, "refunded")
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
        url = self.api._parse_freekassa_payment_url(
            {},
            "fk_site_order_1",
            source="bot",
        )
        self.assertIn("69963", url)
        self.assertIn("fk_site_order_1", url)

    def test_public_plans_and_admin_plans_crud(self) -> None:
        client = TestClient(self.api.app)
        admin_hdrs = self._auth_headers(9999, "admin")

        pub_before = client.get("/api/public/plans")
        self.assertEqual(pub_before.status_code, 200, pub_before.text)
        self.assertTrue(any((p.get("code") == "start_99") for p in pub_before.json().get("plans", [])))

        create_payload = {
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
            }
        create = self._execute_admin_intent(
            client,
            action="plan.create",
            target_type="plan",
            target_id="special_45",
            method="POST",
            path="/api/admin/plans",
            payload=create_payload,
        )
        self.assertEqual(create.status_code, 200, create.text)

        rows = client.get("/api/admin/plans", headers=admin_hdrs)
        self.assertEqual(rows.status_code, 200, rows.text)
        self.assertTrue(any((p.get("code") == "special_45") for p in rows.json().get("plans", [])))

        patch_payload = {"amount_rub": 499, "is_active": False, "sort_order": 55}
        patch = self._execute_admin_intent(
            client,
            action="plan.update",
            target_type="plan",
            target_id="special_45",
            method="PATCH",
            path="/api/admin/plans/special_45",
            payload=patch_payload,
        )
        self.assertEqual(patch.status_code, 200, patch.text)

        remove = self._execute_admin_intent(
            client,
            action="plan.delete",
            target_type="plan",
            target_id="special_45",
            method="DELETE",
            path="/api/admin/plans/special_45",
            payload={},
        )
        self.assertEqual(remove.status_code, 200, remove.text)

    def test_public_live_updates_and_admin_live_updates_crud(self) -> None:
        client = TestClient(self.api.app)
        admin_hdrs = self._auth_headers(9999, "admin")

        public_rows = client.get("/api/public/live-updates")
        self.assertEqual(public_rows.status_code, 200, public_rows.text)
        self.assertGreaterEqual(len(public_rows.json().get("updates", [])), 1)

        create_payload = {
                "title": "Node maintenance completed",
                "summary": "New route profile is online.",
                "link": None,
                "channel_username": "pokrov_vpn",
                "post_id": 999,
                "published_at": "2026-02-15T10:00:00",
                "is_active": True,
                "sort_order": 1,
            }
        create = self._execute_admin_intent(
            client,
            action="live_update.create",
            target_type="live_update",
            target_id="new",
            method="POST",
            path="/api/admin/live-updates",
            payload=create_payload,
        )
        self.assertEqual(create.status_code, 200, create.text)
        update_id = int(create.json().get("id") or 0)
        self.assertGreater(update_id, 0)

        patch_payload = {
            "title": "Node maintenance done",
            "summary": "Fresh route profile online.",
            "post_id": 1001,
            "sort_order": 2,
        }
        patch = self._execute_admin_intent(
            client,
            action="live_update.update",
            target_type="live_update",
            target_id=update_id,
            method="PATCH",
            path=f"/api/admin/live-updates/{update_id}",
            payload=patch_payload,
        )
        self.assertEqual(patch.status_code, 200, patch.text)

        rows = client.get("/api/admin/live-updates", headers=admin_hdrs)
        self.assertEqual(rows.status_code, 200, rows.text)
        found = next((r for r in rows.json().get("updates", []) if int(r.get("id") or 0) == update_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(str(found.get("channel_username") or ""), "pokrov_vpn")
        self.assertEqual(int(found.get("post_id") or 0), 1001)
        self.assertEqual(str(found.get("tg_link") or ""), "https://t.me/pokrov_vpn/1001")

        remove = self._execute_admin_intent(
            client,
            action="live_update.delete",
            target_type="live_update",
            target_id=update_id,
            method="DELETE",
            path=f"/api/admin/live-updates/{update_id}",
            payload={},
        )
        self.assertEqual(remove.status_code, 200, remove.text)

    def test_paid_after_verified_email_mismatch_never_issues_fallback(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import Account, AccountIdentity, ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import attach_by_verified_email, ensure_pending_claim

        s = SessionLocal()
        try:
            s.add(Account(id="mismatch-account", status="active", created_source="test"))
            s.add(AccountIdentity(
                account_id="mismatch-account",
                kind="email",
                provider="email",
                subject_norm="owner@example.test",
                verified_at=self.api._utcnow(),
            ))
            s.add(ExternalOrder(
                order_id="manual-email-claim",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "buyer@example.test"}),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="manual-email-claim",
                buyer_email="buyer@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            mismatch = attach_by_verified_email(
                s,
                provider="lavatop",
                order_id="manual-email-claim",
                buyer_email="owner@example.test",
                account_id="mismatch-account",
                now=self.api._utcnow(),
            )
            self.assertEqual(mismatch.code, "verified_email_mismatch")
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "manual-email-event",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "manual-email-claim", "utm_term": "start_99"},
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "manual_review")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))

        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id="manual-email-claim").one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="manual-email-claim").one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="manual-email-event").one()
            self.assertEqual(claim.status, "manual_review")
            self.assertEqual(order.status, "manual_review")
            self.assertIsNone(claim.fallback_gift_card_id)
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(s.query(GiftCard).count(), 0)
        finally:
            s.close()

    def test_late_paid_after_reversal_never_issues_fallback(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_pending_claim, reverse_claim

        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="reversed-before-paid",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="refunded",
                meta_json=json.dumps({"buyer_email": "buyer@example.test"}),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="reversed-before-paid",
                buyer_email="buyer@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            reverse_claim(
                s,
                provider="lavatop",
                order_id="reversed-before-paid",
                reason="refunded",
                reversed_at=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "late-paid-after-reversal",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "reversed-before-paid", "utm_term": "start_99"},
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        another = client.post(
            "/api/payments/result/lavatop",
            json={**payload, "contractId": "late-paid-after-reversal-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "claim_reversed")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(another.status_code, 200, another.text)
        self.assertFalse(another.json().get("activated"))
        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="reversed-before-paid").one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="late-paid-after-reversal").one()
            self.assertEqual(claim.status, "reversed")
            self.assertIsNone(claim.fallback_gift_card_id)
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(s.query(GiftCard).count(), 0)
        finally:
            s.close()

    def test_public_fallback_email_evidence_failure_retries_delivery_before_completion(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="email-evidence-retry-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "retry@example.test"}),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        deliveries: list[str] = []

        async def _delivery(**kwargs):
            deliveries.append(str(kwargs["access_key"]))
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        payload = {
            "eventType": "payment.success",
            "contractId": "email-evidence-retry-event",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "email-evidence-retry-order", "utm_term": "start_99"},
        }
        original_delivery = self.api.deliver_payment_access_key
        original_record = self.api._record_access_key_delivery_result
        self.api.deliver_payment_access_key = _delivery
        self.api._record_access_key_delivery_result = lambda **_kwargs: False
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            self.api._record_access_key_delivery_result = original_record
            retry = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery
            self.api._record_access_key_delivery_result = original_record

        self.assertEqual(first.status_code, 503, first.text)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertFalse(retry.json().get("duplicate"))
        self.assertEqual(len(deliveries), 2)
        self.assertEqual(deliveries[0], deliveries[1])
        s = SessionLocal()
        try:
            self.assertEqual(s.query(GiftCard).count(), 1)
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="email-evidence-retry-order").one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="email-evidence-retry-event").one()
            self.assertIsNotNone(claim.fallback_gift_card_id)
            self.assertTrue(bool(event.processed_ok))
        finally:
            s.close()

    def test_existing_email_pending_fallback_is_delivered_and_completed(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_fallback_gift_card, ensure_pending_claim, mark_paid

        code = "POKROV-PENDING-DELIVERY"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="pending-delivery-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({
                    "buyer_email": "pending@example.test",
                    "fulfillment": {
                        "mode": "access_key_email",
                        "status": "email_pending",
                        "buyer_email": "pending@example.test",
                        "access_key": code,
                    },
                }),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="pending-delivery-order",
                buyer_email="pending@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id="pending-delivery-order", paid_at=self.api._utcnow())
            ensure_fallback_gift_card(
                s,
                provider="lavatop",
                order_id="pending-delivery-order",
                gift_code=code,
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        deliveries: list[dict[str, object]] = []

        async def _delivery(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        original_delivery = self.api.deliver_payment_access_key
        self.api.deliver_payment_access_key = _delivery
        try:
            response = client.post(
                "/api/payments/result/lavatop",
                json={
                    "eventType": "payment.success",
                    "contractId": "pending-delivery-event",
                    "amount": 99,
                    "currency": "RUB",
                    "status": "completed",
                    "clientUtm": {"utm_content": "pending-delivery-order", "utm_term": "start_99"},
                },
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["email"], "pending@example.test")
        self.assertEqual(deliveries[0]["access_key"], code)
        s = SessionLocal()
        try:
            event = s.query(ExternalPaymentEvent).filter_by(external_id="pending-delivery-event").one()
            self.assertTrue(bool(event.processed_ok))
        finally:
            s.close()

    def test_existing_fulfilled_claim_survives_removed_catalog_on_new_paid_events(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import Account, AccountIdentity, EntitlementGrant, ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim, User
        from payment_entitlement_service import (
            attach_by_verified_email,
            ensure_pending_claim,
            fulfill_attached_paid_claim,
            mark_paid,
        )

        s = SessionLocal()
        try:
            s.add(Account(id="retired-plan-account", status="active", created_source="test"))
            s.add(AccountIdentity(
                account_id="retired-plan-account",
                kind="email",
                provider="email",
                subject_norm="snapshot-owner@example.test",
                verified_at=self.api._utcnow(),
            ))
            s.add(User(
                tg_id=8901,
                username="retired_plan_owner",
                uuid=str(uuid.uuid4()),
                email="user_8901",
                account_id="retired-plan-account",
                sub_type="FREE",
                current_plan_code="free_monthly",
                expiry_at=self.api._utcnow(),
                is_active=True,
                tos_accepted=True,
            ))
            s.add(ExternalOrder(
                order_id="fulfilled-retired-plan-order",
                provider="lavatop",
                tg_id=None,
                plan_code="retired_snapshot",
                amount=321,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({"fulfillment": {"mode": "account_claim", "status": "account_extended"}}),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="fulfilled-retired-plan-order",
                buyer_email="snapshot-owner@example.test",
                plan_code="retired_snapshot",
                duration_days=47,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id="fulfilled-retired-plan-order", paid_at=self.api._utcnow())
            attach_by_verified_email(
                s,
                provider="lavatop",
                order_id="fulfilled-retired-plan-order",
                buyer_email="snapshot-owner@example.test",
                account_id="retired-plan-account",
                now=self.api._utcnow(),
            )
            fulfilled = fulfill_attached_paid_claim(
                s,
                provider="lavatop",
                order_id="fulfilled-retired-plan-order",
                now=self.api._utcnow(),
            )
            original_grant_id = fulfilled.claim.grant_id
            s.commit()
        finally:
            s.close()

        deliveries: list[dict[str, object]] = []

        async def _unexpected_delivery(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        payload = {
            "eventType": "payment.success",
            "amount": 321,
            "currency": "RUB",
            "status": "completed",
            "buyer_email": "callback-change@example.test",
            "clientUtm": {"utm_content": "fulfilled-retired-plan-order", "utm_term": "retired_snapshot"},
        }
        original_resolve = self.api._resolve_plan_config
        original_delivery = self.api.deliver_payment_access_key
        self.api._resolve_plan_config = lambda **_kwargs: None
        self.api.deliver_payment_access_key = _unexpected_delivery
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "retired-plan-event-1"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            second = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "retired-plan-event-2"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api._resolve_plan_config = original_resolve
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json().get("activated"), first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertTrue(second.json().get("activated"), second.text)
        self.assertEqual(deliveries, [])
        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="fulfilled-retired-plan-order").one()
            order = s.query(ExternalOrder).filter_by(order_id="fulfilled-retired-plan-order").one()
            self.assertEqual(claim.status, "fulfilled")
            self.assertEqual(claim.plan_code, "retired_snapshot")
            self.assertEqual(claim.duration_days, 47)
            self.assertEqual(claim.grant_id, original_grant_id)
            self.assertEqual(order.status, "paid")
            self.assertEqual(json.loads(order.meta_json)["fulfillment"]["status"], "account_extended")
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
            self.assertEqual(s.query(GiftCard).count(), 0)
            self.assertEqual(s.query(ExternalPaymentEvent).filter_by(order_id="fulfilled-retired-plan-order").count(), 2)
        finally:
            s.close()

    def test_existing_sent_fallback_keeps_snapshot_duration_on_new_paid_events(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_fallback_gift_card, ensure_pending_claim, mark_paid

        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="sent-fallback-duration-snapshot",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({
                    "buyer_email": "duration-owner@example.test",
                    "fulfillment": {
                        "mode": "access_key_email",
                        "status": "email_sent",
                        "buyer_email": "duration-owner@example.test",
                        "email_delivery": {"status": "sent", "mode": "webhook", "http_status": 200},
                    },
                }),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="sent-fallback-duration-snapshot",
                buyer_email="duration-owner@example.test",
                plan_code="start_99",
                duration_days=61,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id="sent-fallback-duration-snapshot", paid_at=self.api._utcnow())
            ensure_fallback_gift_card(
                s,
                provider="lavatop",
                order_id="sent-fallback-duration-snapshot",
                gift_code="POKROV-DURATION-SNAPSHOT",
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        deliveries: list[dict[str, object]] = []

        async def _unexpected_delivery(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        payload = {
            "eventType": "payment.success",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "sent-fallback-duration-snapshot", "utm_term": "start_99"},
        }
        original_delivery = self.api.deliver_payment_access_key
        self.api.deliver_payment_access_key = _unexpected_delivery
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "duration-snapshot-event-1"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            second = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "duration-snapshot-event-2"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(first.status_code, 200, first.text)
        self.assertTrue(first.json().get("activated"))
        self.assertEqual(second.status_code, 200, second.text)
        self.assertTrue(second.json().get("activated"))
        self.assertEqual(deliveries, [])
        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="sent-fallback-duration-snapshot").one()
            order = s.query(ExternalOrder).filter_by(order_id="sent-fallback-duration-snapshot").one()
            self.assertEqual(claim.status, "paid_unclaimed")
            self.assertEqual(claim.plan_code, "start_99")
            self.assertEqual(claim.duration_days, 61)
            self.assertEqual(order.status, "paid")
            self.assertEqual(json.loads(order.meta_json)["fulfillment"]["status"], "email_sent")
            self.assertEqual(s.query(GiftCard).count(), 1)
            self.assertEqual(s.query(EntitlementGrant).count(), 0)
            self.assertEqual(s.query(ExternalPaymentEvent).filter_by(order_id="sent-fallback-duration-snapshot").count(), 2)
        finally:
            s.close()

    def test_email_transport_failure_keeps_durable_fallback_and_retries(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="email-transport-retry-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "transport@example.test"}),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        deliveries: list[str] = []

        async def _delivery(**kwargs):
            deliveries.append(str(kwargs["access_key"]))
            if len(deliveries) == 1:
                return {"status": "delivery_error", "mode": "webhook", "http_status": 502}
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        payload = {
            "eventType": "payment.success",
            "contractId": "email-transport-retry-event",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "email-transport-retry-order", "utm_term": "start_99"},
        }
        original_delivery = self.api.deliver_payment_access_key
        self.api.deliver_payment_access_key = _delivery
        try:
            first = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            retry = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            later_event = client.post(
                "/api/payments/result/lavatop",
                json={**payload, "contractId": "email-transport-later-event"},
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(first.status_code, 503, first.text)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(later_event.status_code, 200, later_event.text)
        self.assertEqual(len(deliveries), 2)
        self.assertEqual(deliveries[0], deliveries[1])
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id="email-transport-retry-order").one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="email-transport-retry-order").one()
            events = s.query(ExternalPaymentEvent).filter_by(order_id="email-transport-retry-order").all()
            self.assertEqual(s.query(GiftCard).count(), 1)
            self.assertIsNotNone(claim.fallback_gift_card_id)
            self.assertEqual(json.loads(order.meta_json)["fulfillment"]["status"], "email_sent")
            self.assertTrue(all(bool(event.processed_ok) for event in events))
        finally:
            s.close()

    def test_redeemed_legacy_fallback_conflict_is_terminal_for_all_receipts(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        code = "POKROV-REDEEMED-LEGACY"
        s = SessionLocal()
        try:
            s.add(GiftCard(
                code=code,
                card_type="start_99",
                created_by=0,
                redeemed_by=777,
                redeemed_at=self.api._utcnow(),
                created_at=self.api._utcnow(),
            ))
            s.add(ExternalOrder(
                order_id="redeemed-legacy-conflict-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({
                    "buyer_email": "legacy@example.test",
                    "fulfillment": {
                        "mode": "access_key_email",
                        "status": "email_sent",
                        "buyer_email": "legacy@example.test",
                        "access_key": code,
                    },
                }),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "redeemed-conflict-event-1",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "redeemed-legacy-conflict-order", "utm_term": "start_99"},
        }
        first = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        another = client.post(
            "/api/payments/result/lavatop",
            json={**payload, "contractId": "redeemed-conflict-event-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json().get("activated"))
        self.assertEqual(first.json().get("activation_reason"), "fallback_redeemed_conflict")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(another.status_code, 200, another.text)
        self.assertFalse(another.json().get("activated"))
        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="redeemed-legacy-conflict-order").one()
            events = s.query(ExternalPaymentEvent).filter_by(order_id="redeemed-legacy-conflict-order").all()
            self.assertEqual(claim.status, "manual_review")
            self.assertEqual(claim.last_error, "fallback_redeemed_conflict")
            self.assertTrue(all(bool(event.processed_ok) for event in events))
            self.assertEqual(s.query(EntitlementGrant).count(), 0)
        finally:
            s.close()

    def test_unified_redeem_uses_payment_claim_after_plan_removal(self) -> None:
        client = TestClient(self.api.app)
        from account_foundation_service import ensure_user_account_foundation
        from db import SessionLocal
        from models import EntitlementGrant, GiftCard, User
        from payment_entitlement_service import ensure_fallback_gift_card, ensure_pending_claim, mark_paid

        s = SessionLocal()
        try:
            user = User(
                tg_id=8899,
                username="removed_plan_user",
                uuid=str(uuid.uuid4()),
                email="user_8899",
                sub_type="FREE",
                current_plan_code="free_monthly",
                expiry_at=self.api._utcnow(),
                is_active=True,
                tos_accepted=True,
            )
            s.add(user)
            s.flush()
            ensure_user_account_foundation(s, user, now=self.api._utcnow())
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="removed-plan-unified",
                buyer_email="buyer@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id="removed-plan-unified", paid_at=self.api._utcnow())
            ensure_fallback_gift_card(
                s,
                provider="lavatop",
                order_id="removed-plan-unified",
                gift_code="POKROV-UNIFIED-REMOVED",
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        original_meta = self.api._access_key_meta_from_card_type
        original_sync = self.api._sync_control_panel_access

        async def _sync(**_kwargs):
            return True

        self.api._access_key_meta_from_card_type = lambda **_kwargs: None
        self.api._sync_control_panel_access = _sync
        try:
            first = client.post(
                "/api/redeem",
                json={"code": "POKROV-UNIFIED-REMOVED"},
                headers=self._auth_headers(8899, "removed_plan_user"),
            )
            second = client.post(
                "/api/redeem",
                json={"code": "POKROV-UNIFIED-REMOVED"},
                headers=self._auth_headers(8899, "removed_plan_user"),
            )
        finally:
            self.api._access_key_meta_from_card_type = original_meta
            self.api._sync_control_panel_access = original_sync

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json().get("kind"), "access_key")
        status = first.json()["result"]["status"]
        self.assertEqual(status["kind"], "plan")
        self.assertEqual(status["plan"]["code"], "start_99")
        self.assertEqual(status["days"], 30)
        self.assertEqual(second.status_code, 200, second.text)
        s = SessionLocal()
        try:
            self.assertEqual(s.query(GiftCard).count(), 1)
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
        finally:
            s.close()

    def test_callback_after_fulfilled_cross_account_conflict_stays_single_owner(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import Account, AccountIdentity, EntitlementGrant, ExternalOrder, GiftCard, PaymentEntitlementClaim, User
        from payment_entitlement_service import (
            attach_by_verified_email,
            ensure_pending_claim,
            fulfill_attached_paid_claim,
            mark_paid,
        )

        s = SessionLocal()
        try:
            for account_id, email in (
                ("fulfilled-owner", "owner@example.test"),
                ("fulfilled-other", "other@example.test"),
            ):
                s.add(Account(id=account_id, status="active", created_source="test"))
                s.add(AccountIdentity(
                    account_id=account_id,
                    kind="email",
                    provider="email",
                    subject_norm=email,
                    verified_at=self.api._utcnow(),
                ))
            s.add(User(
                tg_id=8810,
                username="fulfilled_owner",
                uuid=str(uuid.uuid4()),
                email="user_8810",
                account_id="fulfilled-owner",
                sub_type="FREE",
                current_plan_code="free_monthly",
                expiry_at=self.api._utcnow(),
                is_active=True,
                tos_accepted=True,
            ))
            s.add(ExternalOrder(
                order_id="fulfilled-cross-account",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "owner@example.test"}),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id="fulfilled-cross-account",
                buyer_email="owner@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id="fulfilled-cross-account", paid_at=self.api._utcnow())
            attach_by_verified_email(
                s,
                provider="lavatop",
                order_id="fulfilled-cross-account",
                buyer_email="owner@example.test",
                account_id="fulfilled-owner",
                now=self.api._utcnow(),
            )
            fulfilled = fulfill_attached_paid_claim(
                s,
                provider="lavatop",
                order_id="fulfilled-cross-account",
                now=self.api._utcnow(),
            )
            conflict = attach_by_verified_email(
                s,
                provider="lavatop",
                order_id="fulfilled-cross-account",
                buyer_email="other@example.test",
                account_id="fulfilled-other",
                now=self.api._utcnow(),
            )
            self.assertEqual(conflict.code, "account_conflict")
            self.assertEqual(conflict.claim.status, "fulfilled")
            original_grant_id = fulfilled.claim.grant_id
            s.commit()
        finally:
            s.close()

        response = client.post(
            "/api/payments/result/lavatop",
            json={
                "eventType": "payment.success",
                "contractId": "fulfilled-cross-account-event",
                "amount": 99,
                "currency": "RUB",
                "status": "completed",
                "clientUtm": {"utm_content": "fulfilled-cross-account", "utm_term": "start_99"},
            },
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json().get("activated"))

        s = SessionLocal()
        try:
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id="fulfilled-cross-account").one()
            self.assertEqual(claim.status, "fulfilled")
            self.assertEqual(claim.account_id, "fulfilled-owner")
            self.assertEqual(claim.grant_id, original_grant_id)
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 1)
            self.assertEqual(s.query(GiftCard).count(), 0)
        finally:
            s.close()

    def test_public_order_ignores_callback_tg_id_injection(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, GiftCard, User

        s = SessionLocal()
        try:
            s.add(User(
                tg_id=8802,
                username="callback_injector",
                uuid=str(uuid.uuid4()),
                email="user_8802",
                sub_type="FREE",
                is_active=True,
                tos_accepted=True,
            ))
            s.add(ExternalOrder(
                order_id="public-ownerless-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "public@example.test"}),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        async def _delivery(**_kwargs):
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        old_delivery = self.api.deliver_payment_access_key
        self.api.deliver_payment_access_key = _delivery
        try:
            response = client.post(
                "/api/payments/result/lavatop",
                json={
                    "eventType": "payment.success",
                    "contractId": "public-ownerless-event",
                    "amount": 99,
                    "currency": "RUB",
                    "status": "completed",
                    "clientUtm": {"utm_content": "public-ownerless-order", "utm_term": "start_99"},
                    "tg_id": "8802",
                },
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = old_delivery

        self.assertEqual(response.status_code, 200, response.text)
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id="public-ownerless-order").one()
            self.assertIsNone(order.tg_id)
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 0)
            self.assertEqual(s.query(GiftCard).count(), 1)
        finally:
            s.close()

    def test_freekassa_signed_owner_mismatch_is_terminal_manual_review(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, ExternalPaymentEvent

        order_id = "fk-owner-bound-order"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id=order_id,
                provider="freekassa",
                tg_id=8803,
                plan_code="1_month",
                source="site",
                amount=239,
                currency="RUB",
                status="pending",
                meta_json=self._freekassa_order_meta(),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()
        signature = self._fk_sci_signature(
            merchant_id="69962",
            amount="239.00",
            order_id=order_id,
            secret_word_2="fk_sw2_test",
        )
        payload = {
            "MERCHANT_ID": "69962",
            "AMOUNT": "239.00",
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": signature,
            "us_tg_id": "999999",
            "us_plan_code": "1_month",
            "intid": "fk-owner-mismatch-event",
        }
        first = client.post("/api/payments/freekassa/notify", params=payload)
        second = client.post("/api/payments/freekassa/notify", params=payload)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)

        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="fk-owner-mismatch-event").one()
            self.assertEqual(order.tg_id, 8803)
            self.assertEqual(order.status, "manual_review")
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(s.query(EntitlementGrant).filter_by(source="provider_payment").count(), 0)
        finally:
            s.close()

    def test_delivery_evidence_and_sensitive_db_logs_are_redacted(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id="sensitive-delivery-order",
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "private@example.test"}),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        self.api._record_access_key_delivery_result(
            provider="lavatop",
            order_id="sensitive-delivery-order",
            delivery={
                "status": "failed",
                "mode": "webhook",
                "http_status": 502,
                "detail": "relay body private@example.test POKROV-SECRET-CODE",
                "body": "raw relay body",
                "email": "leak@example.test",
                "code": "POKROV-LEAK-CODE",
            },
        )
        s = SessionLocal()
        try:
            stored = s.query(ExternalOrder).filter_by(order_id="sensitive-delivery-order").one().meta_json
            self.assertNotIn("relay body", stored)
            self.assertNotIn("leak@example.test", stored)
            self.assertNotIn("POKROV-LEAK-CODE", stored)
            delivery = json.loads(stored)["fulfillment"]["email_delivery"]
            self.assertEqual(set(delivery), {"status", "mode", "http_status", "error_code"})
        finally:
            s.close()

        original_ensure = self.api.ensure_pending_claim
        secret_error = "private@example.test POKROV-SECRET-CODE params=('raw-sql',)"

        def _raise_sensitive(**_kwargs):
            raise RuntimeError(secret_error)

        self.api.ensure_pending_claim = _raise_sensitive
        try:
            with self.assertLogs(self.api.logger, level="ERROR") as captured:
                result = self.api._issue_payment_access_key_for_order(
                    provider="lavatop",
                    order_id="sensitive-delivery-order",
                    payload={},
                )
        finally:
            self.api.ensure_pending_claim = original_ensure
        self.assertFalse(result[0])
        logs = "\n".join(captured.output)
        self.assertNotIn("private@example.test", logs)
        self.assertNotIn("POKROV-SECRET-CODE", logs)
        self.assertNotIn("raw-sql", logs)

    def test_refund_intent_is_visible_across_inter_commit_exception(self) -> None:
        client = TestClient(self.api.app, raise_server_exceptions=False)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent
        from payment_entitlement_service import ensure_fallback_gift_card, ensure_pending_claim, mark_paid

        order_id = "refund-crash-window"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id=order_id,
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({"buyer_email": "refund-crash@example.test"}),
                created_at=self.api._utcnow(),
                paid_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id=order_id,
                buyer_email="refund-crash@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            mark_paid(s, provider="lavatop", order_id=order_id, paid_at=self.api._utcnow())
            ensure_fallback_gift_card(
                s,
                provider="lavatop",
                order_id=order_id,
                gift_code="POKROV-REFUND-CRASH",
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.refunded",
            "contractId": "refund-crash-event",
            "amount": 99,
            "currency": "RUB",
            "status": "refunded",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        original = self.api._record_payment_reversal_operator_action

        def _crash(**_kwargs):
            raise RuntimeError("simulated inter-commit crash")

        self.api._record_payment_reversal_operator_action = _crash
        try:
            failed = client.post(
                "/api/payments/refund/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api._record_payment_reversal_operator_action = original

        self.assertEqual(failed.status_code, 503, failed.text)
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="refund-crash-event").one()
            meta = json.loads(order.meta_json)
            self.assertEqual(order.status, "refunded")
            self.assertEqual(meta["fulfillment"]["status"], "reversal_pending_operator_action")
            self.assertTrue(meta["reversal"]["operator_action_required"])
            self.assertEqual(meta["reversal"]["reconciliation_status"], "pending")
            self.assertFalse(bool(event.processed_ok))
            self.assertTrue(self.api._payment_reversal_needs_operator(order))
        finally:
            s.close()

        retried = client.post(
            "/api/payments/refund/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        self.assertEqual(retried.status_code, 200, retried.text)
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            meta = json.loads(order.meta_json)
            self.assertFalse(meta["reversal"]["operator_action_required"])
            self.assertFalse(self.api._payment_reversal_needs_operator(order))
        finally:
            s.close()

    def test_dangling_fallback_is_terminal_and_deduped_for_all_receipts(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_pending_claim, mark_paid

        order_id = "dangling-fallback-order"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                order_id=order_id,
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "dangling@example.test"}),
                created_at=self.api._utcnow(),
            ))
            claim = ensure_pending_claim(
                s,
                provider="lavatop",
                order_id=order_id,
                buyer_email="dangling@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            ).claim
            mark_paid(s, provider="lavatop", order_id=order_id, paid_at=self.api._utcnow())
            claim.fallback_gift_card_id = 999999
            s.commit()
        finally:
            s.close()

        base = {
            "eventType": "payment.success",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        first = client.post(
            "/api/payments/result/lavatop",
            json={**base, "contractId": "dangling-fallback-event-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/result/lavatop",
            json={**base, "contractId": "dangling-fallback-event-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        another = client.post(
            "/api/payments/result/lavatop",
            json={**base, "contractId": "dangling-fallback-event-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json().get("activated"))
        self.assertEqual(first.json().get("activation_reason"), "fallback_missing")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(another.status_code, 200, another.text)
        self.assertEqual(another.json().get("activation_reason"), "manual_review")
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            events = s.query(ExternalPaymentEvent).filter_by(order_id=order_id).all()
            self.assertEqual(order.status, "manual_review")
            self.assertEqual(claim.status, "manual_review")
            self.assertEqual(claim.last_error, "fallback_missing")
            self.assertTrue(all(bool(event.processed_ok) for event in events))
            self.assertEqual(s.query(GiftCard).count(), 0)
        finally:
            s.close()

    def test_dangling_grant_reversal_is_terminal_but_unreconciled(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import Account, ExternalOrder, ExternalPaymentEvent, PaymentEntitlementClaim

        order_id = "dangling-grant-reversal"
        now = self.api._utcnow()
        s = SessionLocal()
        try:
            s.add(Account(id="dangling-grant-account", status="active", created_source="test"))
            s.add(ExternalOrder(
                order_id=order_id,
                provider="lavatop",
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                created_at=now,
                paid_at=now,
            ))
            s.add(PaymentEntitlementClaim(
                provider="lavatop",
                order_id=order_id,
                buyer_email_norm="dangling-grant@example.test",
                account_id="dangling-grant-account",
                status="fulfilled",
                plan_code="start_99",
                duration_days=30,
                grant_id="missing-grant-id",
                paid_at=now,
                attached_at=now,
                fulfilled_at=now,
                created_at=now,
                updated_at=now,
            ))
            s.commit()
        finally:
            s.close()

        base = {
            "eventType": "payment.refunded",
            "amount": 99,
            "currency": "RUB",
            "status": "refunded",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        first = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-grant-event-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-grant-event-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        another = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-grant-event-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json().get("activated"))
        self.assertEqual(first.json().get("activation_reason"), "grant_not_found")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(another.status_code, 200, another.text)
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            events = s.query(ExternalPaymentEvent).filter_by(order_id=order_id).all()
            reversal = json.loads(order.meta_json)["reversal"]
            self.assertEqual(claim.status, "manual_review")
            self.assertIsNone(claim.reversed_at)
            self.assertEqual(claim.last_error, "grant_not_found")
            self.assertTrue(reversal["operator_action_required"])
            self.assertEqual(reversal["reconciliation_status"], "grant_not_found")
            self.assertTrue(self.api._payment_reversal_needs_operator(order))
            self.assertTrue(all(bool(event.processed_ok) for event in events))
        finally:
            s.close()

    def test_user_owned_fallback_collision_is_terminal_without_transfer(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        code = "POKROV-OWNED-COLLISION"
        order_id = "owned-fallback-collision"
        s = SessionLocal()
        try:
            s.add(GiftCard(
                code=code,
                card_type="start_99",
                created_by=777,
                created_at=self.api._utcnow(),
            ))
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                plan_code="start_99",
                status="pending",
                amount=99,
                currency="RUB",
                meta_json=json.dumps({"buyer_email": "owned-collision@example.test"}),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        original_generate = self.api._generate_gift_code_for_admin
        self.api._generate_gift_code_for_admin = lambda _session: code
        try:
            response = client.post(
                "/api/payments/result/lavatop",
                json={
                    "eventType": "payment.success",
                    "contractId": "owned-fallback-event",
                    "amount": 99,
                    "currency": "RUB",
                    "status": "completed",
                    "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
                },
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api._generate_gift_code_for_admin = original_generate

        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "fallback_creator_conflict")
        s = SessionLocal()
        try:
            card = s.query(GiftCard).filter_by(code=code).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="owned-fallback-event").one()
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            self.assertEqual(card.created_by, 777)
            self.assertIsNone(card.redeemed_by)
            self.assertIsNone(claim.fallback_gift_card_id)
            self.assertEqual(claim.status, "manual_review")
            self.assertEqual(claim.last_error, "fallback_creator_conflict")
            self.assertTrue(bool(event.processed_ok))
            self.assertNotIn(code, str(order.meta_json or ""))
            self.assertNotIn(code, str(event.payload_json or ""))
        finally:
            s.close()

    def test_external_order_upsert_locks_shared_order_before_read(self) -> None:
        from models import ExternalOrder

        operations: list[str] = []
        row = ExternalOrder(
            provider="lavatop",
            order_id="shared-lock-order",
            status="paid",
            amount=99,
            currency="RUB",
            created_at=self.api._utcnow(),
        )

        class _Query:
            def filter(self, *_args):
                operations.append("filter")
                return self

            def with_for_update(self):
                operations.append("lock")
                return self

            def populate_existing(self):
                operations.append("refresh")
                return self

            def first(self):
                operations.append("read")
                return row

        class _Session:
            def query(self, model):
                self.assert_model = model
                operations.append("query")
                return _Query()

        session = _Session()
        result = self.api._upsert_external_order(
            session,
            provider="lavatop",
            order_id="shared-lock-order",
            payload={"status": "completed"},
            status="paid",
            mark_paid=True,
        )

        self.assertIs(result, row)
        self.assertEqual(operations, ["query", "filter", "lock", "refresh", "read"])

    def test_stale_paid_update_cannot_overwrite_reversal_state(self) -> None:
        from models import ExternalOrder

        row = ExternalOrder(
            provider="lavatop",
            order_id="stale-paid-after-refund",
            status="paid",
            amount=99,
            currency="RUB",
            created_at=self.api._utcnow(),
            paid_at=self.api._utcnow(),
        )

        class _Query:
            def filter(self, *_args):
                return self

            def with_for_update(self):
                return self

            def populate_existing(self):
                return self

            def first(self):
                return row

        class _Session:
            def query(self, _model):
                return _Query()

        session = _Session()
        self.api._upsert_external_order(
            session,
            provider="lavatop",
            order_id=row.order_id,
            payload={"status": "refunded"},
            status="refunded",
            mark_paid=False,
        )
        self.api._mark_payment_reversal_pending(row=row, provider="lavatop", event_type="refund")
        self.api._upsert_external_order(
            session,
            provider="lavatop",
            order_id=row.order_id,
            payload={"status": "completed"},
            status="paid",
            mark_paid=True,
        )

        meta = json.loads(row.meta_json)
        self.assertEqual(row.status, "refunded")
        self.assertEqual(meta["fulfillment"]["status"], "reversal_pending_operator_action")
        self.assertTrue(meta["reversal"]["operator_action_required"])

        self.api._upsert_external_order(
            session,
            provider="lavatop",
            order_id=row.order_id,
            payload={"status": "chargeback"},
            status="chargeback",
            mark_paid=False,
        )
        self.api._mark_payment_reversal_pending(row=row, provider="lavatop", event_type="chargeback")
        self.api._upsert_external_order(
            session,
            provider="lavatop",
            order_id=row.order_id,
            payload={"status": "refunded"},
            status="refunded",
            mark_paid=False,
        )
        self.assertEqual(row.status, "chargeback")

    def test_paid_fulfillment_stops_after_refund_receipt_commits(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_pending_claim

        order_id = "paid-after-refund-receipt"
        s = SessionLocal()
        try:
            order = ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="refunded",
                meta_json=json.dumps({"buyer_email": "reversal-window@example.test"}),
                created_at=self.api._utcnow(),
            )
            self.api._mark_payment_reversal_pending(
                row=order,
                provider="lavatop",
                event_type="refund",
            )
            s.add(order)
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id=order_id,
                buyer_email="reversal-window@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        payload = {
            "eventType": "payment.success",
            "contractId": "paid-after-refund-event",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        response = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/result/lavatop",
            json=payload,
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "order_reversed")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id="paid-after-refund-event").one()
            self.assertEqual(order.status, "refunded")
            self.assertEqual(claim.status, "pending_payment")
            self.assertIsNone(claim.fallback_gift_card_id)
            self.assertEqual(s.query(GiftCard).count(), 0)
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(json.loads(event.payload_json)["_pokrov_processing_error"], "order_reversed")
        finally:
            s.close()

    def test_user_bootstrap_relocks_order_before_account_grant(self) -> None:
        from db import SessionLocal
        from models import EntitlementGrant, ExternalOrder, User

        order_id = "bootstrap-reversal-gap"
        tg_id = 909001
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                tg_id=tg_id,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({"fulfillment": {"status": "pending_payment"}}),
                created_at=self.api._utcnow(),
                paid_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        original_bootstrap = self.api._ensure_user_row_for_login

        def _bootstrap_then_refund(*, tg_id: int, username=None, include_legacy_payment_authority=True):
            original_bootstrap(
                tg_id=tg_id,
                username=username,
                include_legacy_payment_authority=include_legacy_payment_authority,
            )
            other = SessionLocal()
            try:
                order = other.query(ExternalOrder).filter_by(provider="lavatop", order_id=order_id).one()
                order.status = "refunded"
                self.api._mark_payment_reversal_pending(
                    row=order,
                    provider="lavatop",
                    event_type="refund",
                )
                other.commit()
            finally:
                other.close()

        self.api._ensure_user_row_for_login = _bootstrap_then_refund
        try:
            activated, reason = self.api._apply_external_paid_order(
                provider="lavatop",
                order_id=order_id,
                payload={"status": "completed", "plan_code": "start_99"},
            )
        finally:
            self.api._ensure_user_row_for_login = original_bootstrap

        self.assertFalse(activated)
        self.assertEqual(reason, "order_reversed")
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            user = s.query(User).filter_by(tg_id=tg_id).one()
            self.assertEqual(order.status, "refunded")
            meta = json.loads(order.meta_json)
            self.assertEqual(meta["fulfillment"]["status"], "reversal_pending_operator_action")
            self.assertTrue(meta["reversal"]["operator_action_required"])
            self.assertIsNotNone(user.account_id)
            self.assertEqual(
                s.query(EntitlementGrant).filter_by(
                    provider="lavatop",
                    external_order_id=order_id,
                    source="provider_payment",
                ).count(),
                0,
            )
        finally:
            s.close()

    def test_dangling_fallback_reversal_is_terminal_and_replay_safe(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, PaymentEntitlementClaim

        order_id = "dangling-fallback-reversal"
        now = self.api._utcnow()
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="paid",
                meta_json=json.dumps({"buyer_email": "dangling-reversal@example.test"}),
                created_at=now,
                paid_at=now,
            ))
            s.add(PaymentEntitlementClaim(
                provider="lavatop",
                order_id=order_id,
                buyer_email_norm="dangling-reversal@example.test",
                status="paid_unclaimed",
                plan_code="start_99",
                duration_days=30,
                fallback_gift_card_id=999999,
                paid_at=now,
                created_at=now,
                updated_at=now,
            ))
            s.commit()
        finally:
            s.close()

        base = {
            "eventType": "payment.refunded",
            "amount": 99,
            "currency": "RUB",
            "status": "refunded",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        first = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-fallback-refund-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        replay = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-fallback-refund-1"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )
        another = client.post(
            "/api/payments/refund/lavatop",
            json={**base, "contractId": "dangling-fallback-refund-2"},
            headers={"X-Api-Key": "lavatop_webhook_key_test"},
        )

        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json().get("activated"))
        self.assertEqual(first.json().get("activation_reason"), "fallback_missing")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(another.status_code, 200, another.text)
        self.assertEqual(another.json().get("activation_reason"), "fallback_missing")
        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            events = s.query(ExternalPaymentEvent).filter_by(order_id=order_id).all()
            meta = json.loads(order.meta_json)
            self.assertEqual(order.status, "refunded")
            self.assertEqual(claim.status, "manual_review")
            self.assertIsNone(claim.reversed_at)
            self.assertEqual(claim.last_error, "fallback_missing")
            self.assertTrue(meta["reversal"]["operator_action_required"])
            self.assertEqual(meta["reversal"]["reconciliation_status"], "fallback_missing")
            self.assertEqual(meta["fulfillment"]["status"], "reversal_pending_operator_action")
            self.assertTrue(all(bool(event.processed_ok) for event in events))
        finally:
            s.close()

    def test_delivery_evidence_locks_order_and_sent_is_monotonic(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        order_id = "delivery-evidence-monotonic"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                status="paid",
                amount=99,
                currency="RUB",
                meta_json=json.dumps({
                    "fulfillment": {
                        "status": "email_sent",
                        "email_delivery": {
                            "status": "sent",
                            "mode": "webhook",
                            "http_status": 200,
                            "error_code": None,
                        },
                    },
                }),
                created_at=self.api._utcnow(),
            ))
            s.commit()
        finally:
            s.close()

        self.assertTrue(self.api._record_access_key_delivery_result(
            provider="lavatop",
            order_id=order_id,
            delivery={"status": "failed", "mode": "webhook", "http_status": 503},
        ))
        s = SessionLocal()
        try:
            fulfillment = json.loads(s.query(ExternalOrder).filter_by(order_id=order_id).one().meta_json)["fulfillment"]
            self.assertEqual(fulfillment["status"], "email_sent")
            self.assertEqual(fulfillment["email_delivery"]["status"], "sent")
            self.assertEqual(fulfillment["email_delivery"]["http_status"], 200)
        finally:
            s.close()

        operations: list[str] = []
        original_session_local = self.api.SessionLocal

        class _Query:
            def filter(self, *_args):
                operations.append("filter")
                return self

            def with_for_update(self):
                operations.append("lock")
                return self

            def first(self):
                operations.append("read")
                return None

        class _FakeSession:
            def query(self, _model):
                operations.append("query")
                return _Query()

            def close(self):
                return None

        self.api.SessionLocal = _FakeSession
        try:
            self.assertFalse(self.api._record_access_key_delivery_result(
                provider="lavatop",
                order_id="missing-delivery-order",
                delivery={"status": "failed"},
            ))
        finally:
            self.api.SessionLocal = original_session_local
        self.assertEqual(operations, ["query", "filter", "lock", "read"])

    def test_reversal_during_email_delivery_finishes_paid_receipt_terminally(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim
        from payment_entitlement_service import ensure_pending_claim

        order_id = "reversal-during-email"
        paid_event_id = "paid-email-race-event"
        reversal_event_id = "refund-email-race-event"
        s = SessionLocal()
        try:
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="pending",
                meta_json=json.dumps({"buyer_email": "delivery-race@example.test"}),
                created_at=self.api._utcnow(),
            ))
            ensure_pending_claim(
                s,
                provider="lavatop",
                order_id=order_id,
                buyer_email="delivery-race@example.test",
                plan_code="start_99",
                duration_days=30,
                now=self.api._utcnow(),
            )
            s.commit()
        finally:
            s.close()

        delivery_calls: list[str] = []
        original_delivery = self.api.deliver_payment_access_key

        async def _deliver_after_reversal(**_kwargs):
            delivery_calls.append("sent")
            refund_payload = {
                "eventType": "payment.refunded",
                "contractId": reversal_event_id,
                "amount": 99,
                "currency": "RUB",
                "status": "refunded",
                "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
            }
            self.api._record_external_payment_event(
                provider="lavatop",
                event_type="refund",
                external_id=reversal_event_id,
                order_id=order_id,
                payload=refund_payload,
                signature_ok=True,
                processed_ok=False,
                status="refunded",
            )
            self.api._record_payment_reversal_operator_action(
                provider="lavatop",
                order_id=order_id,
                event_type="refund",
                payload=refund_payload,
                reason="refunded",
            )
            self.api._complete_external_payment_event(
                provider="lavatop",
                event_type="refund",
                external_id=reversal_event_id,
                processed_ok=True,
            )
            return {"status": "sent", "mode": "webhook", "http_status": 200}

        payload = {
            "eventType": "payment.success",
            "contractId": paid_event_id,
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
        }
        self.api.deliver_payment_access_key = _deliver_after_reversal
        try:
            response = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            replay = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "claim_reversed")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(delivery_calls, ["sent"])

        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            claim = s.query(PaymentEntitlementClaim).filter_by(order_id=order_id).one()
            paid_event = s.query(ExternalPaymentEvent).filter_by(external_id=paid_event_id).one()
            card = s.query(GiftCard).filter_by(id=claim.fallback_gift_card_id).one()
            meta = json.loads(order.meta_json)
            self.assertEqual(order.status, "refunded")
            self.assertEqual(claim.status, "reversed")
            self.assertEqual(meta["fulfillment"]["status"], "reversed")
            self.assertEqual(meta["fulfillment"]["email_delivery"]["status"], "sent")
            self.assertFalse(meta["reversal"]["operator_action_required"])
            self.assertEqual(meta["reversal"]["reconciliation_status"], "reversed")
            self.assertTrue(bool(paid_event.processed_ok))
            self.assertEqual(json.loads(paid_event.payload_json)["_pokrov_processing_error"], "claim_reversed")
            self.assertIsNone(card.redeemed_at)
        finally:
            s.close()

    def test_large_new_callback_preserves_valid_reversal_and_delivery_metadata(self) -> None:
        client = TestClient(self.api.app)
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, GiftCard, PaymentEntitlementClaim

        order_id = "large-callback-reversed-order"
        event_id = "large-callback-new-event"
        secret_value = "relay-secret-material-" + ("S" * 492)
        s = SessionLocal()
        try:
            card = GiftCard(
                code="POKROV-LARGE-CALLBACK",
                card_type="start_99",
                created_by=0,
                created_at=self.api._utcnow(),
            )
            s.add(card)
            s.flush()
            now = self.api._utcnow()
            s.add(ExternalOrder(
                provider="lavatop",
                order_id=order_id,
                tg_id=None,
                plan_code="start_99",
                amount=99,
                currency="RUB",
                status="refunded",
                meta_json=json.dumps({
                    "buyer_email": "large-callback@example.test",
                    "pricing": {"base_amount_rub": 99, "final_amount_rub": 99},
                    "fulfillment": {
                        "mode": "access_key_email",
                        "status": "reversed",
                        "email_delivery": {
                            "status": "sent",
                            "mode": "webhook",
                            "http_status": 200,
                            "error_code": None,
                        },
                    },
                    "reversal": {
                        "operator_action_required": False,
                        "reconciliation_status": "reversed",
                        "recorded_at": now.isoformat(),
                    },
                }, separators=(",", ":")),
                created_at=now,
                paid_at=now,
            ))
            s.add(PaymentEntitlementClaim(
                provider="lavatop",
                order_id=order_id,
                buyer_email_norm="large-callback@example.test",
                status="reversed",
                plan_code="start_99",
                duration_days=30,
                fallback_gift_card_id=int(card.id),
                paid_at=now,
                reversed_at=now,
                reversal_reason="refunded",
                created_at=now,
                updated_at=now,
            ))
            s.commit()
        finally:
            s.close()

        oversized = {f"extra_{index:02d}": chr(65 + index) * 512 for index in range(10)}
        oversized["api_secret"] = secret_value
        oversized["customer_email"] = "private-buyer@example.test" + ("E" * 486)
        payload = {
            "eventType": "payment.success",
            "contractId": event_id,
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": order_id, "utm_term": "start_99"},
            **oversized,
        }
        delivery_calls: list[str] = []
        original_delivery = self.api.deliver_payment_access_key

        async def _unexpected_delivery(**_kwargs):
            delivery_calls.append("called")
            return {"status": "sent"}

        self.api.deliver_payment_access_key = _unexpected_delivery
        try:
            response = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
            replay = client.post(
                "/api/payments/result/lavatop",
                json=payload,
                headers={"X-Api-Key": "lavatop_webhook_key_test"},
            )
        finally:
            self.api.deliver_payment_access_key = original_delivery

        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json().get("activated"))
        self.assertEqual(response.json().get("activation_reason"), "claim_reversed")
        self.assertTrue(replay.json().get("duplicate"))
        self.assertEqual(delivery_calls, [])

        s = SessionLocal()
        try:
            order = s.query(ExternalOrder).filter_by(order_id=order_id).one()
            event = s.query(ExternalPaymentEvent).filter_by(external_id=event_id).one()
            self.assertLessEqual(len(order.meta_json), 4000)
            order_meta = json.loads(order.meta_json)
            self.assertLessEqual(len(event.payload_json), 16000)
            event_meta = json.loads(event.payload_json)
            self.assertEqual(order_meta["fulfillment"]["status"], "reversed")
            self.assertEqual(order_meta["fulfillment"]["email_delivery"]["status"], "sent")
            self.assertFalse(order_meta["reversal"]["operator_action_required"])
            self.assertEqual(order_meta["reversal"]["reconciliation_status"], "reversed")
            self.assertEqual(order_meta["pricing"]["final_amount_rub"], 99)
            self.assertNotIn(secret_value, order.meta_json)
            self.assertNotIn(secret_value, event.payload_json)
            self.assertIn("[redacted]", event.payload_json)
            self.assertTrue(bool(event.processed_ok))
            self.assertEqual(event_meta["_pokrov_processing_error"], "claim_reversed")
        finally:
            s.close()

if __name__ == "__main__":
    unittest.main()
