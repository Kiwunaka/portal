import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "freekassa_api_probe.py"
    spec = importlib.util.spec_from_file_location("freekassa_api_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeChannel:
    def recv_exit_status(self) -> int:
        return 0


class _FakeStream:
    def __init__(self, text: str = "") -> None:
        self.channel = _FakeChannel()
        self._text = text

    def read(self) -> bytes:
        return self._text.encode("utf-8")


class _FakeSsh:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.closed = False

    def exec_command(self, cmd: str, timeout: int):
        self.commands.append(cmd)
        return None, _FakeStream('{"paymentUrl":"https://pay.example"}'), _FakeStream()

    def close(self) -> None:
        self.closed = True


class FreekassaApiProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_main_passes_passwords_path_to_brain_connection(self) -> None:
        ssh = _FakeSsh()
        passwords = Path("C:/secrets/PASSWORDS.txt")
        argv = [
            "freekassa_api_probe.py",
            "--brain-ip",
            "82.21.114.104",
            "--passwords",
            str(passwords),
        ]

        with mock.patch.object(sys, "argv", argv), mock.patch.object(
            self.module, "connect_node", return_value=(ssh, "password")
        ) as connect:
            code = self.module.main()

        self.assertEqual(code, 0)
        self.assertTrue(ssh.closed)
        connect.assert_called_once()
        self.assertEqual(connect.call_args.kwargs["code"], "brain")
        self.assertEqual(connect.call_args.kwargs["passwords_path"], passwords)

    def test_remote_python_builds_bounded_ascii_json_api_probe(self) -> None:
        cmd = self.module._remote_python(
            "site",
            "orders/create",
            {
                "paymentId": "order_1",
                "amount": 99.0,
                "description": "\u0442\u0435\u0441\u0442",
            },
        )

        self.assertIn("cd /root/portal_bot", cmd)
        self.assertIn("api._freekassa_api_request", cmd)
        self.assertIn("source='site'", cmd)
        self.assertIn("method='orders/create'", cmd)
        self.assertIn("\\\\u0442\\\\u0435\\\\u0441\\\\u0442", cmd)
        self.assertNotIn("\u0442\u0435\u0441\u0442", cmd)


if __name__ == "__main__":
    unittest.main()
