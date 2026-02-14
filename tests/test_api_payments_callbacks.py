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
from urllib.parse import urlencode

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
            "FK_SITE_SHOP_ID",
            "FK_SITE_API_KEY",
            "FK_SITE_SECRET_WORD_1",
            "FK_SITE_SECRET_WORD_2",
            "FK_BOT_SHOP_ID",
            "FK_BOT_API_KEY",
            "FK_BOT_SECRET_WORD_1",
            "FK_BOT_SECRET_WORD_2",
            "RUB_CHECKOUT_ENABLED",
            "ADMIN_ID",
        ):
            self._saved_env[k] = os.environ.get(k)
        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["FREEKASSA_SIGNING_SECRET"] = "test_fk_secret"
        os.environ["PAYMENT_CALLBACK_TOLERANT_MODE"] = "false"
        os.environ["FK_SITE_SHOP_ID"] = "69962"
        os.environ["FK_SITE_API_KEY"] = "fk_api_key_test"
        os.environ["FK_SITE_SECRET_WORD_1"] = "fk_sw1_test"
        os.environ["FK_SITE_SECRET_WORD_2"] = "fk_sw2_test"
        os.environ["FK_BOT_SHOP_ID"] = "69963"
        os.environ["FK_BOT_API_KEY"] = "fk_api_key_bot_test"
        os.environ["FK_BOT_SECRET_WORD_1"] = "fk_sw1_bot_test"
        os.environ["FK_BOT_SECRET_WORD_2"] = "fk_sw2_bot_test"
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
            self.assertIn("orders/create", called_methods)
            self.assertIn("orders", called_methods)
            self.assertIn("orders/refund", called_methods)
            self.assertIn("currencies", called_methods)
            self.assertIn("currencies/status", called_methods)
        finally:
            self.api._freekassa_api_request = old_fk_request


if __name__ == "__main__":
    unittest.main()
