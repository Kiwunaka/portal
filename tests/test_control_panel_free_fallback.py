import os
import sys
import unittest
from pathlib import Path


async def _async_result(value):
    return value


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
            last_health_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            last_ok_at=None,
            cpu_percent=None,
            last_probe_at=None,
        )

    async def test_add_client_free_stays_disabled_even_when_legacy_pool_exists(self) -> None:
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
        self.assertFalse(ok)
        self.assertEqual(calls, [])

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

    async def test_enable_client_free_stays_disabled_even_when_legacy_pool_exists(self) -> None:
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

        self.assertFalse(ok)
        self.assertEqual(calls, [])

    async def test_disable_client_toggles_existing_copies_without_provisioning(self) -> None:
        from control_panel import ControlPanel
        from models import User

        cp = ControlPanel()
        nodes = [self._node("pl_free"), self._node("free"), self._node("pl")]
        calls = []
        fake_user = User(tg_id=123, uuid="uuid", email="email", sub_type="FREE", is_active=False, sub_token="token")

        async def fake_refresh():
            return nodes

        async def fake_set_existing_user_enabled_on_nodes(**kwargs):
            calls.append(kwargs)
            return {node.code: True for node in nodes}

        async def forbidden_ensure_user_on_all_nodes(**_kwargs):
            self.fail("disable must not provision or ensure missing clients")

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
        cp.set_existing_user_enabled_on_nodes = fake_set_existing_user_enabled_on_nodes
        cp.ensure_user_on_all_nodes = forbidden_ensure_user_on_all_nodes

        import control_panel as cp_mod

        old_session_local = cp_mod.SessionLocal
        cp_mod.SessionLocal = lambda: _FakeSession()
        try:
            ok = await cp.enable_client("uuid", False)
        finally:
            cp_mod.SessionLocal = old_session_local

        self.assertTrue(ok)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["tg_id"], 123)
        self.assertEqual(calls[0]["node_codes"], ["pl_free", "free", "pl"])
        self.assertFalse(calls[0]["enable"])
        self.assertEqual(calls[0]["sub_id"], "token")

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

    async def test_rotate_pooled_key_updates_existing_copies_only(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000111"
        new_uuid = "00000000-0000-4000-8000-000000000222"
        nodes = [self._node("pl"), self._node("nl"), self._node("absent")]
        calls = []
        apply_calls = []

        class _FakeClient:
            def __init__(self, code: str, current_uuid: str | None):
                self.code = code
                self.current_uuid = current_uuid

            async def find_client_by_tgid(self, _tg_id):
                if self.current_uuid is None:
                    return None
                return {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True}

            async def find_clients_by_tgid(self, _tg_id, **_kwargs):
                client = await self.find_client_by_tgid(_tg_id)
                return [] if client is None else [(4, client)]

            async def update_client_enable(self, client, _enable, **kwargs):
                calls.append((self.code, kwargs["lookup_client_uuid"], client["id"]))
                if kwargs["lookup_client_uuid"] != self.current_uuid:
                    return False
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                apply_calls.append(self.code)
                return True

            async def wait_for_xray_running(self):
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result(nodes)
        cp._clients = {
            "pl": _FakeClient("pl", old_uuid),
            "nl": _FakeClient("nl", old_uuid),
            "absent": _FakeClient("absent", None),
        }

        ok = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123,
            old_key_uuid=old_uuid,
            new_key_uuid=new_uuid,
            sub_id="sub",
        )

        self.assertTrue(ok)
        self.assertEqual(calls, [("pl", old_uuid, new_uuid), ("nl", old_uuid, new_uuid)])
        self.assertEqual(apply_calls, ["pl", "nl"])
        self.assertEqual(cp._clients["pl"].current_uuid, new_uuid)
        self.assertEqual(cp._clients["nl"].current_uuid, new_uuid)
        self.assertIsNone(cp._clients["absent"].current_uuid)

    async def test_rotate_pooled_key_applies_runtime_only_after_panel_readback(self) -> None:
        from control_panel import ControlPanel

        events: list[str] = []

        class _Client:
            current_uuid = "old-key"

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                events.append("read")
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                events.append("write")
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                events.append("confirm")
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                events.append("apply")
                return True

            async def wait_for_xray_running(self):
                events.append("ready")
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}

        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(events, ["read", "write", "read", "confirm", "apply", "ready", "read", "confirm"])

    async def test_rotate_pooled_key_compensates_after_midflight_confirmation_failure(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000311"
        new_uuid = "00000000-0000-4000-8000-000000000322"
        nodes = [self._node("pl"), self._node("nl")]
        calls = []

        class _FakeClient:
            def __init__(self, code: str, fail_confirmation: bool = False):
                self.code = code
                self.current_uuid = old_uuid
                self.fail_confirmation = fail_confirmation

            async def find_client_by_tgid(self, _tg_id):
                return {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True}

            async def find_clients_by_tgid(self, _tg_id, **_kwargs):
                return [(4, await self.find_client_by_tgid(_tg_id))]

            async def update_client_enable(self, client, _enable, **kwargs):
                calls.append((self.code, kwargs["lookup_client_uuid"], client["id"]))
                if kwargs["lookup_client_uuid"] != self.current_uuid:
                    return False
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return not self.fail_confirmation and self.current_uuid == client_uuid

            async def restart_xray_service(self):
                return True

            async def wait_for_xray_running(self):
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result(nodes)
        cp._clients = {"pl": _FakeClient("pl"), "nl": _FakeClient("nl", fail_confirmation=True)}

        ok = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123,
            old_key_uuid=old_uuid,
            new_key_uuid=new_uuid,
            sub_id="sub",
        )

        self.assertFalse(ok)
        self.assertEqual(
            calls,
            [
                ("pl", old_uuid, new_uuid),
                ("nl", old_uuid, new_uuid),
                ("nl", new_uuid, old_uuid),
                ("pl", new_uuid, old_uuid),
            ],
        )
        self.assertEqual(cp._clients["pl"].current_uuid, old_uuid)
        self.assertEqual(cp._clients["nl"].current_uuid, old_uuid)

    async def test_rotate_pooled_key_blocks_exact_old_mismatch_and_compensates(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000411"
        new_uuid = "00000000-0000-4000-8000-000000000422"
        unexpected_uuid = "00000000-0000-4000-8000-000000000433"
        nodes = [self._node("pl"), self._node("nl")]
        calls = []

        class _FakeClient:
            def __init__(self, code: str, current_uuid: str):
                self.code = code
                self.current_uuid = current_uuid

            async def find_client_by_tgid(self, _tg_id):
                return {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True}

            async def find_clients_by_tgid(self, _tg_id, **_kwargs):
                return [(4, await self.find_client_by_tgid(_tg_id))]

            async def update_client_enable(self, client, _enable, **kwargs):
                calls.append((self.code, kwargs["lookup_client_uuid"], client["id"]))
                if kwargs["lookup_client_uuid"] != self.current_uuid:
                    return False
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                return True

            async def wait_for_xray_running(self):
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result(nodes)
        cp._clients = {"pl": _FakeClient("pl", old_uuid), "nl": _FakeClient("nl", unexpected_uuid)}

        ok = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123,
            old_key_uuid=old_uuid,
            new_key_uuid=new_uuid,
            sub_id="sub",
        )

        self.assertFalse(ok)
        self.assertEqual(calls, [])
        self.assertEqual(cp._clients["pl"].current_uuid, old_uuid)
        self.assertEqual(cp._clients["nl"].current_uuid, unexpected_uuid)

    async def test_rotate_pooled_key_requires_an_existing_copy(self) -> None:
        from control_panel import ControlPanel

        nodes = [self._node("pl"), self._node("nl")]

        class _AbsentClient:
            async def find_client_by_tgid(self, _tg_id):
                return None

            async def find_clients_by_tgid(self, _tg_id, **_kwargs):
                return []

            async def update_client_enable(self, *_args, **_kwargs):
                raise AssertionError("rotation must not provision an absent copy")

        cp = ControlPanel()
        cp.refresh = lambda: _async_result(nodes)
        cp._clients = {"pl": _AbsentClient(), "nl": _AbsentClient()}

        ok = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123,
            old_key_uuid="00000000-0000-4000-8000-000000000511",
            new_key_uuid="00000000-0000-4000-8000-000000000522",
            sub_id="sub",
        )

        self.assertFalse(ok)

    async def test_rotate_pooled_key_compensates_ambiguous_false_after_remote_write(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000611"
        new_uuid = "00000000-0000-4000-8000-000000000622"
        calls = []

        class _Client:
            current_uuid = old_uuid

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": False})]

            async def update_client_enable(self, client, _enable, **kwargs):
                calls.append((kwargs["lookup_client_uuid"], client["id"], _enable))
                self.current_uuid = client["id"]
                return False

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                return True

            async def wait_for_xray_running(self):
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}
        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid=old_uuid, new_key_uuid=new_uuid, sub_id="sub"
        )

        self.assertEqual(result.status, "retry")
        self.assertEqual(result.code, "rotation_panel_failed")
        self.assertEqual(calls, [(old_uuid, new_uuid, False), (new_uuid, old_uuid, False)])
        self.assertEqual(cp._clients["pl"].current_uuid, old_uuid)

    async def test_rotate_pooled_key_compensates_exception_after_remote_write(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000711"
        new_uuid = "00000000-0000-4000-8000-000000000722"

        class _Client:
            current_uuid = old_uuid
            writes = 0

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.writes += 1
                self.current_uuid = client["id"]
                if self.writes == 1:
                    raise RuntimeError("transport interrupted")
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                return True

            async def wait_for_xray_running(self):
                return True

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}
        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid=old_uuid, new_key_uuid=new_uuid, sub_id="sub"
        )

        self.assertEqual(result.status, "retry")
        self.assertEqual(cp._clients["pl"].current_uuid, old_uuid)

    async def test_rotate_pooled_key_marks_manual_review_when_compensation_cannot_confirm_old(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000811"
        new_uuid = "00000000-0000-4000-8000-000000000822"

        class _Client:
            current_uuid = old_uuid
            writes = 0

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.writes += 1
                if self.writes == 1:
                    self.current_uuid = client["id"]
                    return False
                return False

            async def confirm_client_profile(self, **_kwargs):
                return False

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}
        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid=old_uuid, new_key_uuid=new_uuid, sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")

    async def test_rotate_pooled_key_accepts_preexisting_replacement_for_safe_retry(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000000911"
        new_uuid = "00000000-0000-4000-8000-000000000922"

        class _Client:
            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": new_uuid, "tgId": "123", "email": "user@example.test", "enable": False})]

            async def update_client_enable(self, *_args, **_kwargs):
                raise AssertionError("idempotent retry must not rewrite an already confirmed replacement")

            async def restart_xray_service(self):
                return True

            async def wait_for_xray_running(self):
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return client_uuid == new_uuid

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}
        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid=old_uuid, new_key_uuid=new_uuid, sub_id="sub"
        )

        self.assertTrue(result.succeeded)

    async def test_rotate_pooled_key_marks_repair_required_when_runtime_apply_fails(self) -> None:
        from control_panel import ControlPanel

        class _Client:
            def __init__(self):
                self.current_uuid = "old-key"
                self.restart_calls = 0

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                self.restart_calls += 1
                return True

            async def wait_for_xray_running(self):
                return self.restart_calls > 1

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        client = _Client()
        cp._clients = {"pl": client}

        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_runtime_apply_failed")
        self.assertEqual(client.current_uuid, "old-key")
        self.assertEqual(client.restart_calls, 2)

    async def test_forward_compensation_applies_old_runtime_after_later_restore_failure(self) -> None:
        from control_panel import ControlPanel

        events: list[tuple[str, str]] = []

        class _Client:
            def __init__(self, code: str, *, fail_restore: bool = False):
                self.code = code
                self.fail_restore = fail_restore
                self.durable_uuid = "old-key"
                self.runtime_uuid = "old-key"
                self.runtime_confirmation_required = False

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.durable_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.runtime_confirmation_required = False
                if client["id"] == "old-key" and self.fail_restore:
                    return False
                self.durable_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.durable_uuid == client_uuid and (
                    not self.runtime_confirmation_required or self.runtime_uuid == client_uuid
                )

            async def restart_xray_service(self):
                events.append(("apply", self.code))
                self.runtime_confirmation_required = True
                self.runtime_uuid = self.durable_uuid
                return True

            async def wait_for_xray_running(self):
                return not (self.code == "pl" and self.durable_uuid == "new-key") and self.runtime_uuid == self.durable_uuid

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl"), self._node("nl")])
        cp._clients = {"pl": _Client("pl"), "nl": _Client("nl", fail_restore=True)}

        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")
        self.assertEqual([event for event in events if event[0] == "apply"], [("apply", "pl"), ("apply", "pl")])
        self.assertEqual(cp._clients["pl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["pl"].runtime_uuid, "old-key")
        self.assertEqual(cp._clients["nl"].durable_uuid, "new-key")
        self.assertEqual(cp._clients["nl"].runtime_uuid, "old-key")

    async def test_forward_compensation_continues_after_earlier_old_runtime_apply_failure(self) -> None:
        from control_panel import ControlPanel

        events: list[tuple[str, str]] = []

        class _Client:
            def __init__(self, code: str, *, fail_old_runtime_apply: bool = False):
                self.code = code
                self.fail_old_runtime_apply = fail_old_runtime_apply
                self.durable_uuid = "old-key"
                self.runtime_uuid = "old-key"
                self.runtime_confirmation_required = False

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.durable_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.runtime_confirmation_required = False
                self.durable_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.durable_uuid == client_uuid and (
                    not self.runtime_confirmation_required or self.runtime_uuid == client_uuid
                )

            async def restart_xray_service(self):
                events.append(("apply", self.code))
                self.runtime_confirmation_required = True
                if not (self.fail_old_runtime_apply and self.durable_uuid == "old-key"):
                    self.runtime_uuid = self.durable_uuid
                return True

            async def wait_for_xray_running(self):
                if self.code == "nl" and self.durable_uuid == "new-key":
                    return False
                return self.runtime_uuid == self.durable_uuid

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl"), self._node("nl")])
        cp._clients = {"pl": _Client("pl"), "nl": _Client("nl", fail_old_runtime_apply=True)}

        result = await cp.rotate_user_key_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")
        self.assertEqual(
            [event for event in events if event[0] == "apply"],
            [("apply", "pl"), ("apply", "nl"), ("apply", "nl"), ("apply", "pl")],
        )
        self.assertEqual(cp._clients["pl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["pl"].runtime_uuid, "old-key")
        self.assertEqual(cp._clients["nl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["nl"].runtime_uuid, "new-key")

    async def test_rollback_pooled_key_applies_old_runtime_after_later_restore_failure(self) -> None:
        from control_panel import ControlPanel

        events: list[tuple[str, str]] = []

        class _Client:
            def __init__(self, code: str, *, fail_restore: bool = False):
                self.code = code
                self.fail_restore = fail_restore
                self.durable_uuid = "new-key"
                self.runtime_uuid = "new-key"
                self.runtime_apply_started = False

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                events.append(("read", self.code))
                return [(4, {"id": self.durable_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                events.append(("restore", self.code))
                if self.fail_restore:
                    return False
                self.durable_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                events.append(("confirm", self.code))
                return self.durable_uuid == client_uuid and (
                    not self.runtime_apply_started or self.runtime_uuid == client_uuid
                )

            async def restart_xray_service(self):
                events.append(("apply", self.code))
                self.runtime_apply_started = True
                self.runtime_uuid = self.durable_uuid
                return True

            async def wait_for_xray_running(self):
                events.append(("ready", self.code))
                return self.runtime_uuid == "old-key"

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl"), self._node("nl")])
        cp._clients = {"pl": _Client("pl"), "nl": _Client("nl", fail_restore=True)}

        result = await cp.rollback_user_key_rotation_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")
        self.assertEqual([event for event in events if event[0] == "apply"], [("apply", "pl")])
        self.assertEqual(cp._clients["pl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["pl"].runtime_uuid, "old-key")
        self.assertEqual(cp._clients["nl"].durable_uuid, "new-key")
        self.assertEqual(cp._clients["nl"].runtime_uuid, "new-key")

    async def test_rollback_pooled_key_continues_after_earlier_runtime_apply_failure(self) -> None:
        from control_panel import ControlPanel

        events: list[tuple[str, str]] = []

        class _Client:
            def __init__(self, code: str, *, fail_apply: bool = False):
                self.code = code
                self.fail_apply = fail_apply
                self.durable_uuid = "new-key"
                self.runtime_uuid = "new-key"
                self.runtime_apply_started = False

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.durable_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.durable_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.durable_uuid == client_uuid and (
                    not self.runtime_apply_started or self.runtime_uuid == client_uuid
                )

            async def restart_xray_service(self):
                events.append(("apply", self.code))
                self.runtime_apply_started = True
                if not self.fail_apply:
                    self.runtime_uuid = self.durable_uuid
                return True

            async def wait_for_xray_running(self):
                events.append(("ready", self.code))
                return self.runtime_uuid == "old-key"

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl"), self._node("nl")])
        cp._clients = {"pl": _Client("pl", fail_apply=True), "nl": _Client("nl")}

        result = await cp.rollback_user_key_rotation_on_existing_nodes(
            tg_id=123, old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")
        self.assertEqual([event for event in events if event[0] == "apply"], [("apply", "pl"), ("apply", "nl")])
        self.assertEqual(cp._clients["pl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["pl"].runtime_uuid, "new-key")
        self.assertEqual(cp._clients["nl"].durable_uuid, "old-key")
        self.assertEqual(cp._clients["nl"].runtime_uuid, "old-key")

    async def test_rollback_reapplies_preexisting_old_durable_key_to_new_runtime(self) -> None:
        from control_panel import ControlPanel

        class _Client:
            durable_uuid = "old-key"
            runtime_uuid = "new-key"
            restart_calls = 0

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.durable_uuid, "tgId": "123", "enable": True})]

            async def update_client_enable(self, *_args, **_kwargs):
                raise AssertionError("durable state is already restored")

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.durable_uuid == client_uuid and self.runtime_uuid == client_uuid

            async def restart_xray_service(self):
                self.restart_calls += 1
                self.runtime_uuid = self.durable_uuid
                return True

            async def wait_for_xray_running(self):
                return self.runtime_uuid == "old-key"

        client = _Client()
        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": client}

        result = await cp.rollback_user_key_rotation_on_existing_nodes(
            tg_id=123,
            old_key_uuid="old-key",
            new_key_uuid="new-key",
            sub_id="sub",
        )

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(client.restart_calls, 1)
        self.assertEqual(client.runtime_uuid, "old-key")

    async def test_rollback_node_key_marks_manual_review_when_old_runtime_apply_fails(self) -> None:
        from control_panel import ControlPanel

        class _Client:
            current_uuid = "new-key"

            async def find_clients_by_tgid(self, *_args, **_kwargs):
                return [(4, {"id": self.current_uuid, "tgId": "123", "email": "user@example.test", "enable": True})]

            async def update_client_enable(self, client, _enable, **_kwargs):
                self.current_uuid = client["id"]
                return True

            async def confirm_client_profile(self, *, client_uuid, **_kwargs):
                return self.current_uuid == client_uuid

            async def restart_xray_service(self):
                return False

        cp = ControlPanel()
        cp._clients = {"pl": _Client()}
        cp._resolve_target_node = lambda _code: _async_result(self._node("pl"))

        result = await cp.rollback_user_key_rotation_on_node(
            tg_id=123, node_code="pl", old_key_uuid="old-key", new_key_uuid="new-key", sub_id="sub"
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.code, "rotation_compensation_failed")

    async def test_rotate_pooled_key_blocks_duplicate_or_other_managed_inbound_before_write(self) -> None:
        from control_panel import ControlPanel

        old_uuid = "00000000-0000-4000-8000-000000001011"
        new_uuid = "00000000-0000-4000-8000-000000001022"

        for rows in (
            [(4, {"id": old_uuid, "tgId": "123"}), (4, {"id": old_uuid, "tgId": "123"})],
            [(4, {"id": old_uuid, "tgId": "123"}), (9, {"id": old_uuid, "tgId": "123"})],
        ):
            class _Client:
                async def find_clients_by_tgid(self, *_args, **_kwargs):
                    return rows

                async def update_client_enable(self, *_args, **_kwargs):
                    raise AssertionError("ambiguous panel rows must block before writes")

            cp = ControlPanel()
            cp.refresh = lambda: _async_result([self._node("pl")])
            cp._clients = {"pl": _Client()}
            result = await cp.rotate_user_key_on_existing_nodes(
                tg_id=123, old_key_uuid=old_uuid, new_key_uuid=new_uuid, sub_id="sub"
            )
            self.assertEqual(result.status, "manual_review")
            self.assertEqual(result.code, "rotation_panel_manual_review")

    async def test_existing_user_revoke_updates_every_matching_inbound(self) -> None:
        from control_panel import ControlPanel

        calls: list[int] = []

        class _Client:
            async def find_clients_by_tgid(self, tg_id, *, include_disabled=False):
                self_test.assertEqual(tg_id, 123)
                self_test.assertTrue(include_disabled)
                return [
                    (4, {"id": "key", "tgId": "123"}),
                    (9, {"id": "key", "tgId": "123"}),
                ]

            async def update_client_enable(self, _client, enable, *, inbound_id, **_kwargs):
                self_test.assertFalse(enable)
                calls.append(inbound_id)
                return True

        self_test = self
        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}

        result = await cp.set_existing_user_enabled_on_nodes(
            tg_id=123,
            node_codes=["pl"],
            enable=False,
            sub_id="sub",
        )

        self.assertEqual(result, {"pl": True})
        self.assertEqual(calls, [4, 9])

    async def test_existing_user_revoke_distinguishes_read_error_from_absence(self) -> None:
        from control_panel import ControlPanel

        class _Client:
            async def find_clients_by_tgid(self, *_args, **_kwargs):
                raise TimeoutError("panel read failed")

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([self._node("pl")])
        cp._clients = {"pl": _Client()}

        result = await cp.set_existing_user_enabled_on_nodes(
            tg_id=123,
            node_codes=["pl"],
            enable=False,
        )

        self.assertEqual(result, {"pl": False})

    async def test_low_level_panel_read_failure_blocks_revoke_and_profile_preimage(self) -> None:
        from dataclasses import replace

        from control_panel import ControlPanel
        from panel_client import PanelClient, PanelReadError

        secret = "https://user:password@panel.example/raw-client-uuid"
        node = replace(self._node("pl"), access_role="paid")

        class _Session:
            def get(self, *_args, **_kwargs):
                raise RuntimeError(secret)

        client = PanelClient(node)
        client.cookies = {"session": "present"}
        client.session = _Session()
        mutation_calls: list[tuple] = []

        async def failed_reauth():
            return False

        async def forbidden_update(*args, **kwargs):
            mutation_calls.append((args, kwargs))
            return True

        client.login = failed_reauth
        client.update_client_enable = forbidden_update
        cp = ControlPanel()
        cp.refresh = lambda: _async_result([node])
        cp._clients = {"pl": client}

        revoked = await cp.set_existing_user_enabled_on_nodes(
            tg_id=123,
            node_codes=["pl"],
            enable=False,
        )
        self.assertEqual(revoked, {"pl": False})

        client.cookies = {"session": "present"}
        with self.assertRaises(PanelReadError):
            await cp.get_user_profile_state_on_node(
                tg_id=123,
                client_uuid="raw-client-uuid",
                email="user@example.test",
                node_code="pl",
                expected_access_role="paid",
            )

        self.assertEqual(mutation_calls, [])

    async def test_user_entrypoints_close_db_before_panel_await_and_pass_scalar_snapshot(self) -> None:
        import control_panel as cp_mod
        from control_panel import ControlPanel, PanelUserSnapshot

        closed_sessions: list[bool] = []
        row = type(
            "DetachedUser",
            (),
            {
                "tg_id": 123,
                "uuid": "key",
                "email": "user@example.test",
                "sub_token": "sub",
                "sub_type": "PAID",
                "current_plan_code": "paid_30d",
                "is_active": True,
                "expiry_at": None,
                "free_profile_state": "",
                "free_profile_active_role": "",
            },
        )()

        class _Query:
            def filter_by(self, **_kwargs):
                return self

            def first(self):
                return row

        class _Session:
            def __init__(self):
                self.closed = False
                closed_sessions.append(False)

            def query(self, *_args):
                return _Query()

            def close(self):
                self.closed = True
                closed_sessions[-1] = True

        cp = ControlPanel()
        received: list[PanelUserSnapshot] = []

        async def set_snapshot(user, *, enable):
            self.assertTrue(all(closed_sessions))
            self.assertIsInstance(user, PanelUserSnapshot)
            self.assertTrue(enable)
            received.append(user)
            return True

        cp._set_user_snapshot_enabled = set_snapshot
        old_session_local = cp_mod.SessionLocal
        cp_mod.SessionLocal = _Session
        try:
            self.assertTrue(await cp.enable_client("key", True))
            self.assertTrue(await cp.update_client_traffic(123, 1))
        finally:
            cp_mod.SessionLocal = old_session_local

        self.assertEqual(len(received), 2)
        self.assertEqual(received[0].tg_id, 123)

    async def test_refresh_closes_db_before_async_client_cleanup(self) -> None:
        import control_panel as cp_mod
        from control_panel import ControlPanel

        session_closed = False

        class _Session:
            def close(self):
                nonlocal session_closed
                session_closed = True

        class _StaleClient:
            async def close(self):
                self_test.assertTrue(session_closed)

        self_test = self
        cp = ControlPanel()
        cp._clients = {"stale": _StaleClient()}
        old_session_local = cp_mod.SessionLocal
        old_enabled_nodes = cp_mod.enabled_nodes
        cp_mod.SessionLocal = _Session
        cp_mod.enabled_nodes = lambda _session: []
        try:
            self.assertEqual(await cp.refresh(), [])
        finally:
            cp_mod.SessionLocal = old_session_local
            cp_mod.enabled_nodes = old_enabled_nodes

        self.assertEqual(cp._clients, {})

    async def test_refresh_rejects_transport_overlap_before_client_construction(self) -> None:
        import json
        from types import SimpleNamespace

        import control_panel as cp_mod
        from control_panel import ControlPanel
        from node_policy import NodeAccessRoleError

        class _Session:
            def close(self):
                return None

        shared = {
            "panel_base_url": "https://panel.example.test:8444",
            "panel_path": "panel",
            "enabled": True,
            "flow": "xtls-rprx-vision",
        }
        nodes = [
            SimpleNamespace(
                id=1,
                code="nl-paid",
                name="NL Paid",
                inbound_id=43,
                access_role="paid",
                transport_profiles_json=json.dumps(
                    {"operator_shadow": {"inbound_id": 42, "enabled": True}}
                ),
                **shared,
            ),
            SimpleNamespace(
                id=2,
                code="nl-free-soft",
                name="NL Free Soft",
                inbound_id=42,
                access_role="free_soft",
                transport_profiles_json=None,
                **shared,
            ),
        ]

        def forbidden_client(_node):
            raise AssertionError("validation must happen before panel client construction")

        old_session_local = cp_mod.SessionLocal
        old_enabled_nodes = cp_mod.enabled_nodes
        old_panel_client = cp_mod.PanelClient
        cp_mod.SessionLocal = _Session
        cp_mod.enabled_nodes = lambda _session: nodes
        cp_mod.PanelClient = forbidden_client
        try:
            with self.assertRaisesRegex(NodeAccessRoleError, r"inbound_id=42"):
                await ControlPanel().refresh()
        finally:
            cp_mod.SessionLocal = old_session_local
            cp_mod.enabled_nodes = old_enabled_nodes
            cp_mod.PanelClient = old_panel_client

    async def test_operator_panel_responses_redact_adversarial_exception_detail(self) -> None:
        import json

        from control_panel import ControlPanel

        secret = "https://user:password@panel.example/provider/raw-client-uuid"
        node = self._node("pl")

        class _Client:
            async def get_inbound_snapshot(self, *_args, **_kwargs):
                raise RuntimeError(secret)

            async def get_client_snapshot_by_tgid(self, *_args, **_kwargs):
                raise RuntimeError(secret)

            async def get_node_online_summary(self):
                raise RuntimeError(secret)

            async def get_node_runtime_snapshot(self):
                raise RuntimeError(secret)

        cp = ControlPanel()
        cp.refresh = lambda: _async_result([node])
        cp._clients = {"pl": _Client()}

        payload = {
            "drift": await cp.get_node_drift_report(),
            "keys": await cp.get_user_key_snapshots(tg_id=123),
            "online": await cp.get_node_online_summaries(),
            "runtime": await cp.get_node_runtime_snapshots(),
        }
        serialized = json.dumps(payload)

        self.assertNotIn(secret, serialized)
        self.assertNotIn("password", serialized)
        self.assertIn("panel_request_failed", serialized)


if __name__ == "__main__":
    unittest.main()
