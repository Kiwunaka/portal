import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from subprocess import CompletedProcess


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

    def test_parse_ss_listeners_ignores_wide_header_spacing(self) -> None:
        raw = """
Netid  State      Recv-Q Send-Q Local Address:Port               Peer Address:Port
udp    UNCONN     0      0      127.0.0.1:9001                  0.0.0.0:*
"""

        listeners = self.module._parse_ss_listeners(raw)

        self.assertEqual(
            listeners,
            [
                self.module.Listener(protocol="udp", state="UNCONN", host="127.0.0.1", port=9001, process_name="", pid=None),
            ],
        )

    def test_parse_ss_listeners_ignores_unexpected_banner_lines(self) -> None:
        raw = """
adb server version (32) doesn't match this client (41); killing...
* daemon started successfully
error: device still authorizing
udp    UNCONN     0      0      127.0.0.1:9001               0.0.0.0:*
"""

        listeners = self.module._parse_ss_listeners(raw)

        self.assertEqual(
            listeners,
            [
                self.module.Listener(protocol="udp", state="UNCONN", host="127.0.0.1", port=9001, process_name="", pid=None),
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

    def test_adb_executable_prefers_sdk_platform_tools_on_windows(self) -> None:
        with TemporaryDirectory() as tmp:
            sdk_root = Path(tmp)
            adb_path = sdk_root / "platform-tools" / "adb.exe"
            adb_path.parent.mkdir(parents=True)
            adb_path.write_text("", encoding="utf-8")

            self.module._adb_executable.cache_clear()
            with mock.patch.dict(
                self.module.os.environ,
                {
                    "ANDROID_SDK_ROOT": str(sdk_root),
                    "LOCALAPPDATA": str(sdk_root / "ignored"),
                },
                clear=False,
            ):
                with mock.patch.object(self.module.os, "name", "nt"):
                    with mock.patch.object(self.module.shutil, "which", return_value="C:\\Windows\\adb.exe"):
                        self.assertEqual(self.module._adb_executable(), str(adb_path))
            self.module._adb_executable.cache_clear()

    def test_adb_executable_respects_explicit_override(self) -> None:
        self.module._adb_executable.cache_clear()
        with mock.patch.dict(
            self.module.os.environ,
            {
                "ANDROID_AUDIT_ADB": "D:\\tools\\adb.exe",
                "ANDROID_SDK_ROOT": "",
                "ANDROID_HOME": "",
                "LOCALAPPDATA": "",
            },
            clear=False,
        ):
            with mock.patch.object(self.module.shutil, "which", return_value=None):
                self.assertEqual(self.module._adb_executable(), "D:\\tools\\adb.exe")
        self.module._adb_executable.cache_clear()

    def test_recoverable_adb_error_detects_missing_or_offline_devices(self) -> None:
        self.assertTrue(self.module._is_recoverable_adb_error("adb.exe: device 'emulator-5554' not found"))
        self.assertTrue(self.module._is_recoverable_adb_error("error: device offline"))
        self.assertTrue(self.module._is_recoverable_adb_error("error: device still authorizing"))
        self.assertFalse(self.module._is_recoverable_adb_error("permission denied"))

    def test_parse_package_evidence_detects_debuggable_and_version(self) -> None:
        raw = """
Package [space.pokrov.pokrov_android_shell] (abc):
  versionCode=42 minSdk=23 targetSdk=35
  versionName=0.4.0-beta.4
  installerPackageName=com.android.packageinstaller
  codePath=/data/app/~~abc/base.apk
  flags=[ HAS_CODE DEBUGGABLE ALLOW_CLEAR_USER_DATA ]
"""

        evidence = self.module._parse_package_evidence(
            raw,
            package_name="space.pokrov.pokrov_android_shell",
            release_evidence="apk sha256 abc123",
        )

        self.assertEqual(evidence.package_name, "space.pokrov.pokrov_android_shell")
        self.assertEqual(evidence.version_name, "0.4.0-beta.4")
        self.assertEqual(evidence.version_code, "42")
        self.assertEqual(evidence.installer_package_name, "com.android.packageinstaller")
        self.assertTrue(evidence.debuggable)
        self.assertEqual(evidence.release_evidence, "apk sha256 abc123")

    def test_package_evidence_failures_require_release_build_and_version(self) -> None:
        evidence = self.module.PackageEvidence(
            package_name="space.pokrov.pokrov_android_shell",
            version_name="0.4.0-beta.4",
            version_code="42",
            installer_package_name="",
            code_path="/data/app/base.apk",
            debuggable=True,
            release_evidence="apk sha256 abc123",
        )

        failures = self.module._package_evidence_failures(
            evidence,
            require_release_build=True,
            expected_version_name="0.4.0-beta.5",
            expected_version_code="43",
        )

        self.assertIn("installed package is debuggable while release build was required", failures)
        self.assertIn("installed versionName 0.4.0-beta.4 does not match expected 0.4.0-beta.5", failures)
        self.assertIn("installed versionCode 42 does not match expected 43", failures)

    def test_collect_listeners_recovers_after_transient_adb_failure(self) -> None:
        failure = CompletedProcess(
            args=["adb", "shell", "ss -ltnup"],
            returncode=1,
            stdout="",
            stderr="adb.exe: device 'emulator-5554' not found",
        )
        success = CompletedProcess(
            args=["adb", "shell", "ss -ltnup"],
            returncode=0,
            stdout="udp UNCONN 0 0 127.0.0.1:9001 0.0.0.0:*\n",
            stderr="",
        )

        with mock.patch.object(self.module, "_run_adb_shell", side_effect=[failure, success]):
            with mock.patch.object(self.module, "_ensure_device_ready") as ensure_device_ready:
                listeners = self.module._collect_listeners("emulator-5554")

        ensure_device_ready.assert_called_once_with("emulator-5554")
        self.assertEqual(
            listeners,
            [
                self.module.Listener(protocol="udp", state="UNCONN", host="127.0.0.1", port=9001, process_name="", pid=None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
