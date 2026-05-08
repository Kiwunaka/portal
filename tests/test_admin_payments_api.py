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
from unittest.mock import patch
from pathlib import Path

from fastapi.testclient import TestClient


class AdminPaymentsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self.db_path = str((repo_root / f"portal_api_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env: dict[str, str | None] = {}
        for key in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID"):
            self._saved_env[key] = os.environ.get(key)
        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["ADMIN_ID"] = "9999"

        for module_name in ("api", "db", "models", "migrations", "config"):
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

    @staticmethod
    def _sign_telegram_init_data(*, bot_token: str, tg_id: int, username: str) -> str:
        params = {
            "auth_date": str(int(time.time())),
            "query_id": "AAEAAAE",
            "user": f'{{"id":{tg_id},"first_name":"Test","username":"{username}"}}',
        }
        data_check_string = "\n".join(f"{key}={params[key]}" for key in sorted(params))
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        params["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        from urllib.parse import urlencode

        return urlencode(params)

    def _auth_headers(self, tg_id: int = 9999, username: str = "admin") -> dict[str, str]:
        return {
            "X-Telegram-Init-Data": self._sign_telegram_init_data(
                bot_token="test_bot_token_123",
                tg_id=tg_id,
                username=username,
            )
        }

    def test_admin_payment_ledger_lists_orders_with_callback_state(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder, ExternalPaymentEvent, User

        session = SessionLocal()
        try:
            session.add(
                User(
                    tg_id=2403,
                    username="paid_user",
                    sub_type="FREE",
                    is_active=False,
                    stars_paid=0,
                )
            )
            session.add(
                ExternalOrder(
                    order_id="order-review-2403",
                    provider="freekassa",
                    tg_id=2403,
                    plan_code="start_99",
                    amount=99,
                    currency="RUB",
                    status="manual_review",
                    source="checkout",
                    campaign="beta",
                    promo_code="WELCOME20",
                    meta_json=json.dumps(
                        {
                            "description": "POKROV start",
                            "secret": "must-not-render",
                            "fulfillment": {
                                "mode": "access_key_email",
                                "status": "email_delivery_error",
                                "buyer_email": "buyer@pokrov.test",
                                "access_key": "POKROV-SECRET-KEY",
                                "email_delivery": {
                                    "status": "delivery_error",
                                    "mode": "webhook",
                                    "http_status": 502,
                                    "detail": "provider token leaked nowhere",
                                },
                            },
                        }
                    ),
                )
            )
            session.add(
                ExternalPaymentEvent(
                    provider="freekassa",
                    event_type="result",
                    external_id="tx-review-2403",
                    order_id="order-review-2403",
                    payload_json=json.dumps({"status": "unknown", "token": "raw-provider-token"}),
                    signature_ok=True,
                    processed_ok=False,
                )
            )
            session.commit()
        finally:
            session.close()

        response = self.client.get("/api/admin/payments/orders", headers=self._auth_headers())
        self.assertEqual(response.status_code, 200, response.text)
        rows = response.json().get("orders") or []
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["order_id"], "order-review-2403")
        self.assertEqual(row["provider"], "freekassa")
        self.assertEqual(row["status"], "manual_review")
        self.assertEqual(row["tg_id"], 2403)
        self.assertEqual(row["event_count"], 1)
        self.assertEqual(row["last_event"]["event_type"], "result")
        self.assertFalse(bool(row["last_event"]["processed_ok"]))
        self.assertEqual(row["fulfillment"]["mode"], "access_key_email")
        self.assertEqual(row["fulfillment"]["status"], "email_delivery_error")
        self.assertEqual(row["fulfillment"]["buyer_email"], "buyer@pokrov.test")
        self.assertTrue(row["fulfillment"]["access_key_present"])
        self.assertEqual(row["fulfillment"]["access_key_preview"], "...-KEY")
        self.assertEqual(row["fulfillment"]["email_delivery"]["status"], "delivery_error")
        self.assertEqual(row["fulfillment"]["email_delivery"]["http_status"], 502)
        self.assertNotIn("payload_json", row)
        self.assertNotIn("raw-provider-token", json.dumps(row))
        self.assertNotIn("must-not-render", json.dumps(row))
        self.assertNotIn("POKROV-SECRET-KEY", json.dumps(row))
        self.assertNotIn("provider token", json.dumps(row))

    def test_admin_payment_reconcile_requires_note_and_audits_status_change(self) -> None:
        from db import SessionLocal
        from models import AdminAudit, ExternalOrder

        session = SessionLocal()
        try:
            session.add(
                ExternalOrder(
                    order_id="order-failed-2404",
                    provider="freekassa",
                    tg_id=2404,
                    plan_code="start_99",
                    amount=99,
                    currency="RUB",
                    status="failed",
                )
            )
            session.commit()
        finally:
            session.close()

        no_note = self.client.post(
            "/api/admin/payments/orders/freekassa/order-failed-2404/reconcile",
            headers=self._auth_headers(),
            json={"status": "manual_review"},
        )
        self.assertEqual(no_note.status_code, 422, no_note.text)

        response = self.client.post(
            "/api/admin/payments/orders/freekassa/order-failed-2404/reconcile",
            headers=self._auth_headers(),
            json={"status": "manual_review", "note": "Provider dashboard shows paid; waiting for fulfillment decision."},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["order"]["status"], "manual_review")

        session = SessionLocal()
        try:
            order = session.query(ExternalOrder).filter(ExternalOrder.order_id == "order-failed-2404").first()
            self.assertIsNotNone(order)
            self.assertEqual(order.status, "manual_review")
            audit = session.query(AdminAudit).filter(AdminAudit.action == "admin_payment_reconcile").first()
            self.assertIsNotNone(audit)
            self.assertEqual(audit.target_tg_id, 2404)
            meta = json.loads(audit.meta or "{}")
            self.assertEqual(meta["provider"], "freekassa")
            self.assertEqual(meta["order_id"], "order-failed-2404")
            self.assertEqual(meta["from_status"], "failed")
            self.assertEqual(meta["to_status"], "manual_review")
            self.assertIn("Provider dashboard", meta["note"])
        finally:
            session.close()

    def test_admin_can_resend_paid_public_access_key_email_with_audit_note(self) -> None:
        from db import SessionLocal
        from models import AdminAudit, ExternalOrder

        session = SessionLocal()
        try:
            session.add(
                ExternalOrder(
                    order_id="lavatop-public-email-retry",
                    provider="lavatop",
                    tg_id=None,
                    plan_code="start_99",
                    amount=99,
                    currency="RUB",
                    status="paid",
                    paid_at=self.api._utcnow(),
                    source="site",
                    meta_json=json.dumps(
                        {
                            "fulfillment": {
                                "mode": "access_key_email",
                                "status": "email_delivery_error",
                                "buyer_email": "buyer@pokrov.test",
                                "access_key": "POKROV-TEST-1234",
                            }
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )
            session.commit()
        finally:
            session.close()

        deliveries: list[dict[str, object]] = []

        async def _fake_deliver_payment_access_key(**kwargs):
            deliveries.append(dict(kwargs))
            return {"status": "sent", "kind": "payment_access_key", "email": kwargs["email"], "mode": "webhook"}

        with patch.object(self.api, "deliver_payment_access_key", _fake_deliver_payment_access_key):
            response = self.client.post(
                "/api/admin/payments/orders/lavatop/lavatop-public-email-retry/resend-access-key-email",
                headers=self._auth_headers(),
                json={"note": "Customer reports missing email; resend from operator cockpit."},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["delivery"]["status"], "sent")
        order = response.json()["order"]
        self.assertEqual(order["fulfillment"]["status"], "email_sent")
        self.assertEqual(order["fulfillment"]["email_delivery"]["status"], "sent")
        self.assertEqual(order["fulfillment"]["access_key_preview"], "...1234")
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["email"], "buyer@pokrov.test")
        self.assertEqual(deliveries[0]["access_key"], "POKROV-TEST-1234")

        session = SessionLocal()
        try:
            row = session.query(ExternalOrder).filter(ExternalOrder.order_id == "lavatop-public-email-retry").first()
            self.assertIsNotNone(row)
            meta = json.loads(str(row.meta_json or "{}"))
            self.assertEqual(meta["fulfillment"]["email_delivery"]["status"], "sent")
            audit = session.query(AdminAudit).filter(AdminAudit.action == "admin_payment_resend_access_key_email").first()
            self.assertIsNotNone(audit)
            audit_meta = json.loads(audit.meta or "{}")
            self.assertEqual(audit_meta["provider"], "lavatop")
            self.assertEqual(audit_meta["order_id"], "lavatop-public-email-retry")
            self.assertEqual(audit_meta["delivery_status"], "sent")
            self.assertIn("missing email", audit_meta["note"])
        finally:
            session.close()

    def test_admin_resend_access_key_email_rejects_unpaid_order(self) -> None:
        from db import SessionLocal
        from models import ExternalOrder

        session = SessionLocal()
        try:
            session.add(
                ExternalOrder(
                    order_id="lavatop-pending-email-retry",
                    provider="lavatop",
                    tg_id=None,
                    plan_code="start_99",
                    amount=99,
                    currency="RUB",
                    status="pending",
                    source="site",
                    meta_json=json.dumps(
                        {"fulfillment": {"mode": "access_key_email", "buyer_email": "buyer@pokrov.test"}},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )
            session.commit()
        finally:
            session.close()

        response = self.client.post(
            "/api/admin/payments/orders/lavatop/lavatop-pending-email-retry/resend-access-key-email",
            headers=self._auth_headers(),
            json={"note": "Do not send until provider marks the order paid."},
        )

        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("Only paid orders", response.text)


if __name__ == "__main__":
    unittest.main()
