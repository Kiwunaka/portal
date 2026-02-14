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
        ):
            self._saved_env[k] = os.environ.get(k)
        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["FREEKASSA_SIGNING_SECRET"] = "test_fk_secret"
        os.environ["PAYMENT_CALLBACK_TOLERANT_MODE"] = "false"

        for module_name in ("api", "db", "models", "migrations", "config"):
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

    def test_freekassa_notify_alias(self) -> None:
        client = TestClient(self.api.app)
        payload = {"order_id": "order-3001", "external_tx_id": "tx-abc-3", "status": "paid"}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        sig = self._hmac_sha256("test_fk_secret", raw)
        r = client.post(
            "/api/payments/freekassa/notify",
            data=raw,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json().get("ok"))


if __name__ == "__main__":
    unittest.main()
