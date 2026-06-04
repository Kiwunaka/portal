import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path


class ControlPanelFreeFallbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for k in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved[k] = os.environ.get(k)
            os.environ.pop(k, None)
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

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
            cpu_percent=0.0,
            last_health_at=None,
            last_probe_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            last_ok_at=None,
        )

    async def test_add_client_free_targets_free_pool(self) -> None:
        from control_panel import ControlPanel

        cp = ControlPanel()
        calls = []

        async def fake_refresh():
            return [self._node("pl_free"), self._node("free"), self._node("pl")]

        async def fake_ensure_user_on_all_nodes(**kwargs):
            calls.append(kwargs["only_node_codes"])
            return {"free": True}

        cp.refresh = fake_refresh
        cp.ensure_user_on_all_nodes = fake_ensure_user_on_all_nodes

        ok = await cp.add_client("uuid", "email", "FREE", 0, 123, "token")
        self.assertTrue(ok)
        self.assertEqual(calls, [["free"]])

    async def test_add_client_stale_trial_free_user_targets_free_pool(self) -> None:
        from control_panel import ControlPanel
        from models import User

        cp = ControlPanel()
        calls = []
        fake_user = User(
            tg_id=123,
            uuid="uuid",
            email="email",
            sub_type="FREE",
            current_plan_code="trial",
            is_active=True,
            expiry_at=datetime.now() + timedelta(days=3650),
            sub_token="token",
        )

        async def fake_refresh():
            return [self._node("nl-free"), self._node("de-paid"), self._node("us-paid")]

        async def fake_ensure_user_on_all_nodes(**kwargs):
            calls.append(kwargs["only_node_codes"])
            return {"nl-free": True}

        class _FakeQuery:
            def filter_by(self, **kwargs):
                return self

            def first(self):
                return fake_user

        class _FakeSession:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

            def close(self):
                return None

        cp.refresh = fake_refresh
        cp.ensure_user_on_all_nodes = fake_ensure_user_on_all_nodes

        import control_panel as cp_mod

        old_session_local = cp_mod.SessionLocal
        cp_mod.SessionLocal = lambda: _FakeSession()
        try:
            ok = await cp.add_client("uuid", "email", "FREE", 0, 123, "token")
        finally:
            cp_mod.SessionLocal = old_session_local

        self.assertTrue(ok)
        self.assertEqual(calls, [["nl-free"]])

    async def test_add_client_free_returns_false_without_free_pool(self) -> None:
        from control_panel import ControlPanel

        cp = ControlPanel()
        calls = []

        async def fake_refresh():
            return [self._node("pl")]

        async def fake_ensure_user_on_all_nodes(**kwargs):
            calls.append(kwargs["only_node_codes"])
            return {"pl": False}

        cp.refresh = fake_refresh
        cp.ensure_user_on_all_nodes = fake_ensure_user_on_all_nodes

        ok = await cp.add_client("uuid", "email", "FREE", 0, 123, "token")
        self.assertFalse(ok)
        self.assertEqual(calls, [])

    async def test_enable_client_free_uses_free_pool(self) -> None:
        from control_panel import ControlPanel
        from models import User

        cp = ControlPanel()
        calls = []
        fake_user = User(tg_id=123, uuid="uuid", email="email", sub_type="FREE", is_active=True, sub_token="token")

        async def fake_refresh():
            return [self._node("pl_free"), self._node("free"), self._node("pl")]

        async def fake_ensure_user_on_all_nodes(**kwargs):
            calls.append(kwargs["only_node_codes"])
            return {"free": True}

        class _FakeQuery:
            def filter_by(self, **kwargs):
                return self

            def first(self):
                return fake_user

        class _FakeSession:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

            def close(self):
                return None

        async def fake_close():
            return None

        cp.ensure_user_on_all_nodes = fake_ensure_user_on_all_nodes
        cp.refresh = fake_refresh
        cp.close = fake_close

        import control_panel as cp_mod

        old_session_local = cp_mod.SessionLocal
        cp_mod.SessionLocal = lambda: _FakeSession()
        try:
            ok = await cp.enable_client("uuid", True)
        finally:
            cp_mod.SessionLocal = old_session_local

        self.assertTrue(ok)
        self.assertEqual(calls, [["free"]])

    async def test_ensure_user_on_all_nodes_paid_targets_each_exact_non_free_node(self) -> None:
        from control_panel import ControlPanel

        cp = ControlPanel()
        calls = []

        nodes = [
            self._node("brain"),
            self._node("nl"),
            self._node("nl-alt"),
            self._node("free"),
        ]

        class _FakeClient:
            def __init__(self, code: str):
                self.code = code

            async def ensure_client(self, **kwargs):
                calls.append(self.code)
                return True

        async def fake_refresh():
            return nodes

        class _FakeQuery:
            def filter_by(self, **kwargs):
                return self

            def first(self):
                return None

        class _FakeSession:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

            def add(self, *_args, **_kwargs):
                return None

            def commit(self):
                return None

            def close(self):
                return None

        cp.refresh = fake_refresh
        cp._clients = {node.code: _FakeClient(node.code) for node in nodes}

        import control_panel as cp_mod

        old_session_local = cp_mod.SessionLocal
        cp_mod.SessionLocal = lambda: _FakeSession()
        try:
            result = await cp.ensure_user_on_all_nodes(
                tg_id=123,
                client_uuid="uuid",
                email="email",
                sub_id="token",
                enable=True,
            )
        finally:
            cp_mod.SessionLocal = old_session_local

        self.assertEqual(calls, ["brain", "nl", "nl-alt"])
        self.assertEqual(result, {"brain": True, "nl": True, "nl-alt": True})


if __name__ == "__main__":
    unittest.main()
