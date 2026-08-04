import base64
import json
import os
import sys
import unittest
from pathlib import Path


class PanelClientMultiInboundTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self._saved = {}
        for key in ("DATABASE_URL", "BOT_TOKEN"):
            self._saved[key] = os.environ.get(key)
            os.environ.pop(key, None)
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    @staticmethod
    def _node():
        from nodes_repo import NodeRuntime

        return NodeRuntime(
            id=1,
            code="pl",
            name="pl",
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
            inbound_id=1,
            weight=100,
            health_score=0.0,
            last_health_at=None,
            is_healthy=True,
            panel_latency_ms=100,
            panel_error_rate=0.0,
            active_clients=0,
            last_ok_at=None,
            transport_profiles_json=json.dumps(
                [
                    {
                        "name": "legacy_reality_fallback",
                        "enabled": True,
                        "kind": "reality",
                        "inbound_id": 1,
                        "host": "example.test",
                        "port": 443,
                        "tls_server_name": "example.com",
                        "reality_public_key": "pbk",
                        "reality_short_id": "sid",
                    },
                    {
                        "name": "grpc_443_primary",
                        "enabled": True,
                        "kind": "xhttp",
                        "inbound_id": 2,
                        "host": "example.test",
                        "port": 443,
                        "tls_server_name": "xhttp.example.com",
                        "xhttp_path": "/mux-grpc",
                    },
                    {
                        "name": "operator_lab",
                        "enabled": False,
                        "kind": "grpc",
                        "inbound_id": 3,
                        "host": "example.test",
                        "port": 443,
                        "tls_server_name": "lab.example.com",
                        "grpc_service_name": "lab-grpc",
                    },
                ]
            ),
        )

    async def test_find_client_by_tgid_scans_enabled_catalog_inbounds(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node())

        async def fake_get_inbounds():
            return [
                {"id": 1, "settings": json.dumps({"clients": []})},
                {"id": 2, "settings": json.dumps({"clients": [{"id": "u-2", "email": "User_42", "tgId": "42"}]})},
                {"id": 3, "settings": json.dumps({"clients": [{"id": "u-3", "email": "User_42", "tgId": "42"}]})},
            ]

        client._get_inbounds = fake_get_inbounds

        found = await client.find_client_by_tgid(42)
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "u-2")

    async def test_empty_successful_inbound_list_remains_legitimate_absence(self) -> None:
        from panel_client import PanelClient

        class _Response:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def json(self, **_kwargs):
                return {"success": True, "obj": []}

        class _Session:
            def get(self, *_args, **_kwargs):
                return _Response()

        client = PanelClient(self._node())
        client.cookies = {"session": "present"}
        client.session = _Session()

        self.assertEqual(await client._get_inbounds(), [])
        self.assertEqual(await client.find_clients_by_tgid(42, include_disabled=True), [])

    async def test_inbound_network_failure_raises_typed_error_instead_of_absence(self) -> None:
        from panel_client import PanelClient, PanelReadError

        secret = "https://user:password@panel.example/clients/raw-uuid"

        class _Session:
            def get(self, *_args, **_kwargs):
                raise RuntimeError(secret)

        client = PanelClient(self._node())
        client.cookies = {"session": "present"}
        client.session = _Session()

        async def successful_reauth():
            return True

        client.login = successful_reauth

        with self.assertRaises(PanelReadError) as raised:
            await client.find_clients_by_tgid(42, include_disabled=True)

        self.assertEqual(raised.exception.error_kind, "panel_inbounds_network_error")
        self.assertNotIn(secret, str(raised.exception))

    async def test_inbound_login_failure_is_not_an_empty_list(self) -> None:
        from panel_client import PanelClient, PanelReadError

        client = PanelClient(self._node())

        async def failed_login():
            return False

        client.login = failed_login

        with self.assertRaises(PanelReadError) as raised:
            await client._get_inbounds()

        self.assertEqual(raised.exception.error_kind, "panel_login_failed")

    async def test_inbound_http_failure_remains_typed_after_bounded_reauth(self) -> None:
        from panel_client import PanelClient, PanelReadError

        class _Response:
            status = 503

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

        class _Session:
            def get(self, *_args, **_kwargs):
                return _Response()

        client = PanelClient(self._node())
        client.cookies = {"session": "present"}
        client.session = _Session()

        async def successful_reauth():
            return True

        client.login = successful_reauth

        with self.assertRaises(PanelReadError) as raised:
            await client._get_inbounds()

        self.assertEqual(raised.exception.error_kind, "panel_inbounds_http_error")

    async def test_inbound_snapshot_derives_public_key_without_exposing_private_key(self) -> None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import x25519

        from panel_client import PanelClient

        private_bytes = bytes(range(1, 33))
        private_key = base64.urlsafe_b64encode(private_bytes).decode("ascii").rstrip("=")
        expected_public = base64.urlsafe_b64encode(
            x25519.X25519PrivateKey.from_private_bytes(private_bytes)
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("ascii").rstrip("=")
        client = PanelClient(self._node())

        async def fake_get_inbounds():
            return [
                {
                    "id": 1,
                    "remark": "primary",
                    "enable": True,
                    "port": 443,
                    "protocol": "vless",
                    "streamSettings": json.dumps(
                        {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "privateKey": private_key,
                                "dest": "example.com:443",
                                "serverNames": ["example.com"],
                                "shortIds": ["sid"],
                            },
                        }
                    ),
                }
            ]

        client._get_inbounds = fake_get_inbounds

        snapshot = await client.get_inbound_snapshot()

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["public_key"], expected_public)
        self.assertNotIn(private_key, json.dumps(snapshot))

    async def test_ensure_client_syncs_all_enabled_catalog_inbounds(self) -> None:
        from panel_client import PanelClient

        client = PanelClient(self._node())

        async def fake_get_inbounds():
            return [
                {"id": 1, "settings": json.dumps({"clients": [{"id": "uuid-42", "email": "User_42", "tgId": "42", "subId": "legacy", "enable": True}]})},
                {"id": 2, "settings": json.dumps({"clients": []})},
                {"id": 4, "settings": json.dumps({"clients": [{"id": "stale-42", "email": "User_42", "tgId": "42"}]})},
            ]

        updated: list[tuple[int | None, str | None, str | None]] = []
        added: list[tuple[int | None, str | None]] = []
        deleted: list[tuple[int, str]] = []

        async def fake_update_client_enable(client_payload: dict, enable: bool, sub_id: str | None = None, hard_cap_gb_override: int | None = None, inbound_id: int | None = None, flow: str | None = None) -> bool:
            updated.append((inbound_id, sub_id, flow))
            return True

        async def fake_add_client(**kwargs) -> bool:
            added.append((kwargs.get("inbound_id"), kwargs.get("flow")))
            return True

        async def fake_delete_client_from_inbound(*, inbound_id: int, client_uuid: str) -> bool:
            deleted.append((inbound_id, client_uuid))
            return True

        client._get_inbounds = fake_get_inbounds
        client.update_client_enable = fake_update_client_enable
        client.add_client = fake_add_client
        client._delete_client_from_inbound = fake_delete_client_from_inbound

        ok = await client.ensure_client(
            tg_id=42,
            client_uuid="uuid-42",
            email="User_42",
            sub_id="secure-42",
            enable=True,
        )

        self.assertTrue(ok)
        self.assertEqual(updated, [(1, "secure-42", "xtls-rprx-vision")])
        self.assertEqual(added, [(2, "")])
        self.assertEqual(deleted, [(4, "stale-42")])
