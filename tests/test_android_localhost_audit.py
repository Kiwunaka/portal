import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "android_localhost_audit.py"
    spec = importlib.util.spec_from_file_location("android_localhost_audit", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AndroidLocalhostAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_parse_ss_listeners_reads_tcp_udp_and_ipv6_loopback(self) -> None:
        raw = """
Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
tcp   LISTEN 0      4096   127.0.0.1:10808   *:*              users:(("libbox",pid=1234,fd=10))
udp   UNCONN 0      0      127.0.0.1:16450   *:*              users:(("libbox",pid=1234,fd=11))
tcp   LISTEN 0      50     [::1]:7078        *:*              users:(("app_process",pid=1234,fd=12))
"""

        listeners = self.module._parse_ss_listeners(raw)

        self.assertEqual(
            listeners,
            [
                self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=10808, process_name="libbox", pid=1234),
                self.module.Listener(protocol="udp", state="UNCONN", host="127.0.0.1", port=16450, process_name="libbox", pid=1234),
                self.module.Listener(protocol="tcp", state="LISTEN", host="::1", port=7078, process_name="app_process", pid=1234),
            ],
        )

    def test_new_localhost_listeners_ignores_baseline_ports(self) -> None:
        baseline = [
            self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=5357, process_name="system", pid=100),
        ]
        after = [
            self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=5357, process_name="system", pid=100),
            self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=10808, process_name="libbox", pid=1234),
        ]

        new_listeners = self.module._new_localhost_listeners(baseline, after)

        self.assertEqual(
            new_listeners,
            [
                self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=10808, process_name="libbox", pid=1234),
            ],
        )

    def test_audit_failures_report_new_listener_and_successful_probe(self) -> None:
        after_connect = [
            self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=10808, process_name="libbox", pid=1234),
        ]
        probes = [
            self.module.PortProbeResult(
                phase="after_connect",
                protocol="tcp",
                host="127.0.0.1",
                port=10808,
                reachable=True,
                stdout="probe ok",
                stderr="",
            ),
        ]

        failures = self.module._audit_failures(
            baseline=[],
            after_launch=[],
            after_connect=after_connect,
            after_disconnect=[],
            probes=probes,
        )

        self.assertIn("after_connect exposes new localhost listener tcp/127.0.0.1:10808", failures)
        self.assertIn("unauthenticated localhost probe succeeded for tcp/127.0.0.1:10808 during after_connect", failures)

    def test_audit_failures_pass_when_only_baseline_listener_remains(self) -> None:
        baseline = [
            self.module.Listener(protocol="tcp", state="LISTEN", host="127.0.0.1", port=5357, process_name="system", pid=100),
        ]

        failures = self.module._audit_failures(
            baseline=baseline,
            after_launch=baseline,
            after_connect=baseline,
            after_disconnect=baseline,
            probes=[],
        )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
