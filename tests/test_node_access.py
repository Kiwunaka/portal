import sys
import unittest
from pathlib import Path
from unittest.mock import patch


class NodeAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = str(repo_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

    def test_connect_node_falls_back_to_port_22(self) -> None:
        import node_access

        attempts: list[tuple[int, bool]] = []

        class FakeTransport:
            def set_keepalive(self, _seconds: int) -> None:
                return None

        class FakeClient:
            def set_missing_host_key_policy(self, _policy) -> None:
                return None

            def connect(self, host, port, username, timeout, banner_timeout, auth_timeout, allow_agent, look_for_keys, **auth):
                attempts.append((int(port), bool(auth.get("password"))))
                if int(port) == 29374:
                    raise RuntimeError("primary port failed")
                if int(port) == 22 and auth.get("password") == "pw":
                    return None
                raise RuntimeError("unexpected auth")

            def get_transport(self):
                return FakeTransport()

            def close(self) -> None:
                return None

        with patch.object(node_access, "load_private_key", return_value=None), patch.object(
            node_access, "parse_passwords", return_value={"nl": "pw"}
        ), patch.object(node_access.paramiko, "SSHClient", side_effect=lambda: FakeClient()):
            _ssh, method = node_access.connect_node(
                code="nl",
                host="82.24.195.93",
                passwords_path=Path("ignored.txt"),
            )

        self.assertEqual(method, "password")
        self.assertEqual(attempts, [(29374, True), (22, True)])


if __name__ == "__main__":
    unittest.main()
