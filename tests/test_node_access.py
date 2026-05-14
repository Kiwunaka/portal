import sys
import unittest
import base64
import struct
from pathlib import Path
from unittest.mock import patch
import tempfile

from cryptography.hazmat.primitives.asymmetric import rsa


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

    def test_private_key_candidates_support_mini_russia_key_names(self) -> None:
        import node_access

        with tempfile.TemporaryDirectory() as tmp:
            key_dir = Path(tmp)
            candidates = node_access._private_key_candidates("mini", key_dir)

        names = [path.name for path in candidates]
        self.assertIn("RUSSIA_private.ppk", names)
        self.assertIn("RUSSIA.ppk", names)

    def test_load_unencrypted_putty_rsa_v2_key(self) -> None:
        import node_access

        def ssh_string(value: bytes) -> bytes:
            return struct.pack(">I", len(value)) + value

        def mpint(value: int) -> bytes:
            raw = value.to_bytes((value.bit_length() + 7) // 8, "big") or b"\x00"
            if raw[0] & 0x80:
                raw = b"\x00" + raw
            return raw

        key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        numbers = key.private_numbers()
        public_blob = b"".join(
            [
                ssh_string(b"ssh-rsa"),
                ssh_string(mpint(numbers.public_numbers.e)),
                ssh_string(mpint(numbers.public_numbers.n)),
            ]
        )
        private_blob = b"".join(
            [
                ssh_string(mpint(numbers.d)),
                ssh_string(mpint(numbers.p)),
                ssh_string(mpint(numbers.q)),
                ssh_string(mpint(pow(numbers.q, -1, numbers.p))),
            ]
        )
        ppk = "\n".join(
            [
                "PuTTY-User-Key-File-2: ssh-rsa",
                "Encryption: none",
                'Comment: "test"',
                "Public-Lines: 1",
                base64.b64encode(public_blob).decode("ascii"),
                "Private-Lines: 1",
                base64.b64encode(private_blob).decode("ascii"),
                "Private-MAC: unused",
            ]
        )

        loaded = node_access._load_putty_rsa_v2(ppk)

        self.assertIsNotNone(loaded)

    def test_connect_node_uses_password_file_parent_as_default_key_dir(self) -> None:
        import node_access

        seen_key_dirs: list[Path] = []

        class FakeTransport:
            def set_keepalive(self, _seconds: int) -> None:
                return None

        class FakeClient:
            def set_missing_host_key_policy(self, _policy) -> None:
                return None

            def connect(self, host, port, username, timeout, banner_timeout, auth_timeout, allow_agent, look_for_keys, **auth):
                if not auth.get("pkey"):
                    raise RuntimeError("expected key auth")
                return None

            def get_transport(self):
                return FakeTransport()

            def close(self) -> None:
                return None

        def fake_load_private_key(code: str, *, key_dir: Path | None = None):
            seen_key_dirs.append(Path(key_dir or ""))
            return object()

        with tempfile.TemporaryDirectory() as tmp:
            passwords_path = Path(tmp) / "PASSWORDS.txt"
            passwords_path.write_text("", encoding="utf-8")
            with patch.object(node_access, "load_private_key", side_effect=fake_load_private_key), patch.object(
                node_access, "parse_passwords", return_value={}
            ), patch.object(node_access.paramiko, "SSHClient", side_effect=lambda: FakeClient()):
                _ssh, method = node_access.connect_node(
                    code="free",
                    host="151.245.217.23",
                    passwords_path=passwords_path,
                )

        self.assertEqual(method, "key")
        self.assertEqual(seen_key_dirs, [passwords_path.parent])


if __name__ == "__main__":
    unittest.main()
