import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path


class P0ServicesTests(unittest.TestCase):
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
        for k in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID"):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["ADMIN_ID"] = "9999"

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])
        if "db" in sys.modules:
            importlib.reload(sys.modules["db"])
        if "pay_attempts_service" in sys.modules:
            importlib.reload(sys.modules["pay_attempts_service"])
        if "points_service" in sys.modules:
            importlib.reload(sys.modules["points_service"])

        self.pay_attempts_service = importlib.import_module("pay_attempts_service")
        importlib.reload(self.pay_attempts_service)
        self.points_service = importlib.import_module("points_service")
        importlib.reload(self.points_service)

        from db import init_db

        init_db()

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

    def test_pay_attempt_lifecycle(self) -> None:
        svc = self.pay_attempts_service
        row = svc.start_attempt(
            tg_id=1001,
            source="webapp",
            plan_code="9_months",
            amount_stars=1399,
            currency="XTR",
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.status, svc.STATUS_STARTED)

        payload = f"portal_9_months_1001_full_a{row.id}_p0"
        ok_invoice = svc.mark_invoice_sent(attempt_id=row.id, set_invoice_payload=payload)
        self.assertTrue(ok_invoice)

        fetched = svc.get_attempt_by_payload(invoice_payload=payload)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, svc.STATUS_INVOICE_SENT)

        ok_paid = svc.mark_paid(attempt_id=row.id, invoice_payload=payload)
        self.assertTrue(ok_paid)

        fetched2 = svc.get_attempt_by_payload(invoice_payload=payload)
        self.assertIsNotNone(fetched2)
        self.assertEqual(fetched2.status, svc.STATUS_PAID)
        self.assertIsNotNone(fetched2.paid_at)

    def test_abandoned_candidates_detection(self) -> None:
        svc = self.pay_attempts_service
        from db import SessionLocal
        from models import PayAttempt

        row = svc.start_attempt(
            tg_id=1002,
            source="bot",
            plan_code="1_month",
            amount_stars=249,
            currency="XTR",
        )
        self.assertIsNotNone(row)

        s = SessionLocal()
        try:
            db_row = s.query(PayAttempt).filter(PayAttempt.id == row.id).first()
            self.assertIsNotNone(db_row)
            db_row.started_at = datetime.utcnow() - timedelta(minutes=70)
            s.commit()
        finally:
            s.close()

        items = svc.find_abandoned_candidates(older_than_minutes=60, limit=10)
        ids = [int(x.id) for x in items]
        self.assertIn(int(row.id), ids)

        ok = svc.mark_abandoned(attempt_id=row.id)
        self.assertTrue(ok)

    def test_resolve_pending_attempt_for_payment(self) -> None:
        svc = self.pay_attempts_service
        first = svc.start_attempt(
            tg_id=3001,
            source="bot",
            plan_code="1_month",
            amount_stars=249,
            currency="XTR",
        )
        second = svc.start_attempt(
            tg_id=3001,
            source="bot",
            plan_code="3_months",
            amount_stars=699,
            currency="XTR",
        )
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        resolved = svc.resolve_pending_attempt_for_payment(
            tg_id=3001,
            amount_stars=699,
            currency="XTR",
            within_hours=24,
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(int(resolved.id), int(second.id))
        self.assertEqual(str(resolved.plan_code), "3_months")

    def test_points_monthly_cap_and_redeem_caps(self) -> None:
        pts = self.points_service

        # 10% from 5000 stars = 500, but monthly cap = 300.
        grant = pts.award_referral_points(
            tg_id=2001,
            paid_stars=5000,
            ref_tg_id=1001,
            pay_attempt_id=77,
        )
        self.assertEqual(grant, 300)

        total, expiring = pts.available_points(tg_id=2001)
        self.assertEqual(total, 300)
        self.assertGreaterEqual(expiring, 0)

        # For 1_month=249 with first purchase 20%:
        # plan cap after first-discount ~= 99, so redeemable should be <= 99.
        preview = pts.preview_redeemable_points(
            tg_id=2001,
            plan_price_stars=249,
            first_purchase_discount_pct=0.20,
        )
        self.assertEqual(preview.available_points, 300)
        self.assertLessEqual(preview.redeemable_points, preview.max_points_by_plan_cap)
        self.assertLessEqual(preview.redeemable_points, preview.max_points_by_total_cap)
        self.assertLessEqual(preview.redeemable_points, 99)

        used = pts.spend_points(tg_id=2001, amount=preview.redeemable_points, pay_attempt_id=78)
        self.assertEqual(used, preview.redeemable_points)

        total_after, _ = pts.available_points(tg_id=2001)
        self.assertEqual(total_after, 300 - used)

    def test_points_referral_tier_progression(self) -> None:
        pts = self.points_service

        snap0 = pts.referral_tier_snapshot(tg_id=4001)
        self.assertEqual(str(snap0["tier_key"]), "bronze")
        self.assertEqual(int(float(snap0["percent"])), 10)

        # Simulate paid referrals from 5 distinct users -> should move to silver (15% by default).
        for ref_id in range(5001, 5006):
            granted = pts.award_referral_points(
                tg_id=4001,
                paid_stars=200,
                ref_tg_id=ref_id,
                pay_attempt_id=ref_id,
            )
            self.assertGreater(granted, 0)

        snap1 = pts.referral_tier_snapshot(tg_id=4001)
        self.assertEqual(str(snap1["tier_key"]), "silver")
        self.assertEqual(int(float(snap1["percent"])), 15)


if __name__ == "__main__":
    unittest.main()
