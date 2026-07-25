import importlib
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace


class PlanPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for k in (
            "FREE_LIMIT_IP",
            "PAID_LIMIT_IP",
            "FREE_TOTAL_GB",
            "NODE_PL_FREE_LIMIT_IP",
            "NODE_PL_FREE_TOTAL_GB",
            "NODE_PL_LIMIT_IP",
            "NODE_PL_TOTAL_GB",
            "DATABASE_URL",
            "BOT_TOKEN",
        ):
            self._saved[k] = os.environ.get(k)
            os.environ.pop(k, None)

        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

        config = importlib.import_module("config")
        importlib.reload(config)
        db = importlib.import_module("db")
        try:
            db.engine.dispose()
        except Exception:
            pass
        importlib.reload(db)

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    @staticmethod
    def _node(code: str):
        from nodes_repo import NodeRuntime

        return NodeRuntime(
            id=1,
            code=code,
            name=code,
            host="example.test",
            accepting_new_clients=True,
            is_draining=False,
            vless_port=443,
            reality_sni="example.com",
            reality_pbk="pbk",
            reality_sid="sid",
            fingerprint="firefox",
            flow="xtls-rprx-vision",
            panel_base_url="http://127.0.0.1:15739",
            panel_path="xui",
            panel_user="admin",
            panel_pass="pass",
            inbound_id=4,
            weight=100,
            health_score=0.0,
            last_health_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            cpu_percent=0.0,
            last_ok_at=None,
            last_probe_at=None,
        )

    def test_panel_policy_defaults(self) -> None:
        from panel_client import PanelClient

        free_client = PanelClient(self._node("pl_free"))
        paid_client = PanelClient(self._node("pl"))

        self.assertEqual(free_client._limit_ip_policy(), 1)
        self.assertEqual(free_client._total_gb_policy(), 5)
        self.assertEqual(free_client._total_bytes_policy(), 5 * 1024 * 1024 * 1024)

        self.assertEqual(paid_client._limit_ip_policy(), 5)
        self.assertEqual(paid_client._total_gb_policy(), 0)
        self.assertEqual(paid_client._total_bytes_policy(), 0)

    def test_paid_node_override_does_not_change_exact_free_policy(self) -> None:
        from panel_client import PanelClient

        os.environ["FREE_LIMIT_IP"] = "1"
        os.environ["NODE_PL_FREE_LIMIT_IP"] = "3"
        os.environ["FREE_TOTAL_GB"] = "5"
        os.environ["NODE_PL_FREE_TOTAL_GB"] = "8"
        os.environ["PAID_LIMIT_IP"] = "5"
        os.environ["NODE_PL_LIMIT_IP"] = "7"

        free_client = PanelClient(self._node("pl_free"))
        paid_client = PanelClient(self._node("pl"))

        self.assertEqual(free_client._limit_ip_policy(), 1)
        self.assertEqual(free_client._total_gb_policy(), 5)
        self.assertEqual(paid_client._limit_ip_policy(), 7)

    def test_api_plan_total_gb_policy(self) -> None:
        os.environ["FREE_TOTAL_GB"] = "5"
        os.environ["FREE_LIMIT_IP"] = "1"
        os.environ["PAID_LIMIT_IP"] = "5"

        api = importlib.import_module("api")
        importlib.reload(api)

        free_user = SimpleNamespace(sub_type="FREE")
        paid_user = SimpleNamespace(sub_type="PAID")

        self.assertEqual(api._plan_total_gb(free_user), 5)
        self.assertEqual(api._plan_total_gb(paid_user), 0)
        self.assertEqual(api._plan_device_limit(free_user), 1)
        self.assertEqual(api._plan_device_limit(paid_user), 5)

    def test_api_access_policy_for_paid_trial_bonus_and_free_soft_mode(self) -> None:
        os.environ["FREE_TOTAL_GB"] = "5"
        os.environ["FREE_LIMIT_IP"] = "1"
        os.environ["PAID_LIMIT_IP"] = "5"

        api = importlib.import_module("api")
        importlib.reload(api)

        now = datetime(2030, 1, 10, 12, 0, 0)
        paid_user = SimpleNamespace(
            sub_type="PAID",
            current_plan_code="1_month",
            is_active=True,
            expiry_at=now + timedelta(days=30),
            channel_bonus_claimed_at=None,
        )
        paid = api._build_access_policy(user=paid_user, used_bytes=3 * 1024**3, now=now)
        self.assertEqual(paid["access_state"], "paid_unlimited")
        self.assertEqual(paid["traffic_policy"]["kind"], "unlimited")
        self.assertIsNone(paid["traffic_limit_gb"])
        self.assertIsNone(paid["traffic_remaining_gb"])

        trial_user = SimpleNamespace(
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=now + timedelta(days=5),
            channel_bonus_claimed_at=None,
            free_cycle_next_reset_at=None,
        )
        trial = api._build_access_policy(user=trial_user, used_bytes=0, now=now)
        self.assertEqual(trial["access_state"], "trial_premium")
        self.assertEqual(trial["traffic_policy"]["kind"], "unlimited")

        bonus_user = SimpleNamespace(
            sub_type="BONUS",
            current_plan_code="channel_bonus",
            is_active=True,
            expiry_at=now + timedelta(days=10),
            channel_bonus_claimed_at=now,
            free_cycle_next_reset_at=None,
        )
        bonus = api._build_access_policy(user=bonus_user, used_bytes=0, now=now)
        self.assertEqual(bonus["access_state"], "bonus_premium")
        self.assertEqual(bonus["traffic_policy"]["kind"], "unlimited")

        free_user = SimpleNamespace(
            sub_type="FREE",
            current_plan_code="free_monthly",
            is_active=True,
            expiry_at=now + timedelta(days=365),
            channel_bonus_claimed_at=None,
            free_cycle_next_reset_at=now + timedelta(days=12),
            free_profile_state="soft_active",
            free_profile_active_role="free_soft",
        )
        soft = api._build_access_policy(user=free_user, used_bytes=6 * 1024**3, now=now)
        self.assertEqual(soft["access_state"], "free_soft_mode")
        self.assertEqual(soft["traffic_policy"]["kind"], "soft_limited")
        self.assertTrue(soft["soft_mode_active"])
        self.assertEqual(soft["traffic_limit_gb"], 5.0)
        self.assertEqual(soft["traffic_remaining_gb"], 0.0)

    def test_free_pool_routing_fails_closed_for_stale_free_plan_labels(self) -> None:
        from node_policy import user_uses_free_pool

        now = datetime(2030, 1, 10, 12, 0, 0)
        valid_trial = SimpleNamespace(
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=now + timedelta(days=5),
        )
        stale_trial = SimpleNamespace(
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=now + timedelta(days=3650),
        )

        self.assertFalse(user_uses_free_pool(valid_trial, now=now))
        self.assertTrue(user_uses_free_pool(stale_trial, now=now))
        for plan_code in ("channel_bonus", "start_99", "1_month"):
            with self.subTest(plan_code=plan_code):
                user = SimpleNamespace(
                    sub_type="FREE",
                    current_plan_code=plan_code,
                    is_active=True,
                    expiry_at=now + timedelta(days=3650),
                )
                self.assertTrue(user_uses_free_pool(user, now=now))

    def test_access_policy_does_not_promote_unbounded_free_trial_projection(self) -> None:
        api = importlib.import_module("api")
        importlib.reload(api)

        now = datetime(2030, 1, 10, 12, 0, 0)
        user = SimpleNamespace(
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=now + timedelta(days=3650),
            channel_bonus_claimed_at=None,
            free_cycle_next_reset_at=now + timedelta(days=30),
            free_profile_state="standard",
            free_profile_active_role="free_standard",
        )

        access = api._build_access_policy(user=user, used_bytes=0, now=now)

        self.assertEqual(access["access_state"], "free_monthly")
        self.assertEqual(access["traffic_policy"]["kind"], "metered")

    def test_api_plan_catalog_fallback_defaults(self) -> None:
        api = importlib.import_module("api")
        importlib.reload(api)

        s = api.SessionLocal()
        try:
            rows = api._plan_catalog_payload(s=s, only_active=True)
            codes = [str(r.get("code") or "") for r in rows]
            self.assertIn("start_99", codes)
            self.assertIn("1_month", codes)
            self.assertGreaterEqual(len(rows), 6)
        finally:
            s.close()

    def test_api_price_with_pending_discount(self) -> None:
        api = importlib.import_module("api")
        importlib.reload(api)

        final_price, pct = api._price_with_pending_discount(amount_rub=249, pending_pct=20)
        self.assertEqual(final_price, 199)
        self.assertEqual(pct, 20)


if __name__ == "__main__":
    unittest.main()
