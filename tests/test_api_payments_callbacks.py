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
            "RUB_CHECKOUT_ENABLED",
            "ADMIN_ID",
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
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "cardlink,pally,platima,freekassa"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "cardlink,pally,platima,freekassa"
        os.environ["CARDLINK_API_TOKEN"] = "cardlink_token_test"
        os.environ["CARDLINK_SHOP_ID"] = "cardlink_shop_test"
        os.environ["PALLY_API_TOKEN"] = "pally_token_test"
        os.environ["PALLY_SHOP_ID"] = "pally_shop_test"
        os.environ["PLATIMA_PROJECT_ID"] = "platima_project_test"
        os.environ["PLATIMA_API_KEY_PROJECT"] = "platima_key_project_test"
        os.environ["RUB_CHECKOUT_ENABLED"] = "true"
        os.environ["ADMIN_ID"] = "9999"

        for module_name in ("api", "db", "models", "migrations", "config", "offers_service", "points_service", "gift_cards_service"):
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)

    def tearDown(self) -> None:
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
        from models import PointsLedger, ReferralBonusQueue, User

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
        rows = response.json().get("providers", [])
        self.assertTrue(any((row.get("code") == "cardlink") for row in rows))
        self.assertTrue(any((row.get("code") == "pally") for row in rows))
        self.assertTrue(any((row.get("code") == "platima") for row in rows))
        self.assertTrue(any((row.get("code") == "freekassa") for row in rows))

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
            self.assertEqual(kwargs["description"], "PORTAL Start 30 дней")
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
                "channel_username": "portal_privacy",
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
        self.assertEqual(str(found.get("channel_username") or ""), "portal_privacy")
        self.assertEqual(int(found.get("post_id") or 0), 1001)
        self.assertEqual(str(found.get("tg_link") or ""), "https://t.me/portal_privacy/1001")

        remove = client.delete(f"/api/admin/live-updates/{update_id}", headers=admin_hdrs)
        self.assertEqual(remove.status_code, 200, remove.text)


if __name__ == "__main__":
    unittest.main()
