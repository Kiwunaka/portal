from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "singbox_authenticated_egress_adapter.py"
    spec = importlib.util.spec_from_file_location("singbox_authenticated_egress_adapter", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _MemorySocket:
    def __init__(self, received: bytes) -> None:
        self.received = bytearray(received)
        self.sent: list[bytes] = []
        self.timeouts: list[float] = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def close(self) -> None:
        self.closed = True

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def sendall(self, value: bytes) -> None:
        self.sent.append(value)

    def recv(self, size: int) -> bytes:
        if not self.received:
            return b""
        chunk = bytes(self.received[:size])
        del self.received[:size]
        return chunk


class _FakeTlsContext:
    def __init__(self, tls_socket: _MemorySocket) -> None:
        self.tls_socket = tls_socket
        self.server_hostname = ""

    def wrap_socket(self, _raw_socket: object, *, server_hostname: str):
        self.server_hostname = server_hostname
        return self.tls_socket


class _FakeProcess:
    def __init__(self) -> None:
        self.pid = 0
        self.terminated = False
        self.killed = False

    def poll(self):
        return None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        return 0


class _FakeEndpoint:
    def close(self) -> None:
        return None


class SingboxAuthenticatedEgressAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.script_path = Path(__file__).resolve().parents[1] / "scripts" / "singbox_authenticated_egress_adapter.py"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.config_path = self.root / "adapter.json"
        self.store_path = self.root / "canaries.json"
        self.core_path = Path(sys.executable).resolve()
        self.profile_id = "synthetic_canary"
        self.node_code = "synthetic_node"
        self.node_host = "node.example.invalid"
        self.probe_target = self.module.ProbeTarget(
            hostname="probe.example.invalid",
            port=443,
            path="/api/public/authenticated-egress-probe",
            expected_status=204,
            marker_header_name="X-Pokrov-Egress-Probe",
            marker_header_value="pokrov-authenticated-egress-v1",
        )
        self._write_documents()

    def _write_documents(self) -> None:
        self.store_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "profiles": {
                        self.profile_id: {
                            "node_code": self.node_code,
                            "endpoint": {"host": self.node_host, "port": 443},
                            "uuid": "11111111-1111-4111-8111-111111111111",
                            "flow": "xtls-rprx-vision",
                            "reality": {
                                "server_name": "front.example.invalid",
                                "public_key": "A" * 43,
                                "short_id": "0000000000000000",
                                "fingerprint": "chrome",
                            },
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "core_path": str(self.core_path),
                    "credential_store_path": str(self.store_path),
                    "probe": {
                        "hostname": self.probe_target.hostname,
                        "port": self.probe_target.port,
                        "path": self.probe_target.path,
                        "expected_status": self.probe_target.expected_status,
                        "marker_header_name": self.probe_target.marker_header_name,
                        "marker_header_value": self.probe_target.marker_header_value,
                    },
                    "timeouts": {
                        "total_seconds": 10.0,
                        "core_start_seconds": 2.0,
                        "connect_seconds": 2.0,
                        "io_seconds": 2.0,
                        "shutdown_seconds": 1.0,
                    },
                }
            ),
            encoding="utf-8",
        )

    def _request(self, **changes: object) -> bytes:
        payload: dict[str, object] = {
            "schema_version": 1,
            "node_code": self.node_code,
            "host": self.node_host,
            "port": 443,
            "profile_id": self.profile_id,
        }
        payload.update(changes)
        return json.dumps(payload).encode("utf-8")

    def _credential(self):
        return self.module._load_credential(self.store_path, profile_id=self.profile_id)

    def test_cli_strict_input_produces_exact_one_response_without_stderr(self) -> None:
        payload = json.loads(self._request())
        payload["unexpected"] = True
        completed = subprocess.run(
            [sys.executable, str(self.script_path)],
            input=json.dumps(payload).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout.count(b"\n"), 1)
        response = json.loads(completed.stdout)
        self.assertEqual(set(response), self.module._RESPONSE_FIELDS)
        self.assertEqual(response["profile_id"], self.profile_id)
        self.assertEqual(response["status"], "not_run")
        self.assertEqual(response["classification"], "request_invalid")

    def test_runtime_config_rejects_extra_fields(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        payload["extra"] = "rejected"
        self.config_path.write_text(json.dumps(payload), encoding="utf-8")

        response = self.module.handle_request(
            self._request(),
            config_path=self.config_path,
            runtime_parent=self.root,
        )

        self.assertEqual(response["status"], "not_run")
        self.assertEqual(response["classification"], "adapter_config_invalid")

    def test_request_rejects_duplicate_keys(self) -> None:
        raw = self._request()[:-1] + b',"port":443}'

        request, profile_id = self.module._parse_request(raw)

        self.assertIsNone(request)
        self.assertEqual(profile_id, "invalid_request")

    def test_binding_mismatch_prevents_core_spawn(self) -> None:
        with mock.patch.object(self.module, "_start_core") as start_core:
            response = self.module.handle_request(
                self._request(host="other.example.invalid"),
                config_path=self.config_path,
                runtime_parent=self.root,
            )

        start_core.assert_not_called()
        self.assertEqual(response["status"], "not_run")
        self.assertEqual(response["classification"], "probe_material_invalid")

    def test_generated_config_has_one_vless_outbound_no_fallback_and_disabled_log(self) -> None:
        config = self.module._build_singbox_config(self._credential(), socks_port=31080)

        self.assertEqual(config["log"], {"disabled": True})
        self.assertEqual(config["route"], {"final": "authenticated-egress"})
        self.assertEqual(len(config["inbounds"]), 1)
        self.assertEqual(config["inbounds"][0]["listen"], "127.0.0.1")
        self.assertEqual(len(config["outbounds"]), 1)
        self.assertEqual(config["outbounds"][0]["type"], "vless")
        self.assertTrue(config["outbounds"][0]["tls"]["reality"]["enabled"])
        self.assertNotIn(config["outbounds"][0]["type"], {"direct", "block", "urltest", "selector"})
        self.assertTrue(self.module._validate_generated_config(config, socks_port=31080))

    def test_synthetic_socks_tls_and_marker_success(self) -> None:
        socks_reply = b"\x05\x00" + b"\x05\x00\x00\x01" + b"\x00\x00\x00\x00\x00\x00"
        raw_socket = _MemorySocket(socks_reply)
        tls_socket = _MemorySocket(
            b"HTTP/1.1 204 No Content\r\n"
            b"X-Pokrov-Egress-Probe: pokrov-authenticated-egress-v1\r\n"
            b"Content-Length: 0\r\n\r\n"
        )
        context = _FakeTlsContext(tls_socket)
        connected_to: list[tuple[Path, float]] = []
        endpoint = self.root / "private.sock"

        def connect(address, *, timeout):
            connected_to.append((address, timeout))
            return raw_socket

        result = self.module._probe_through_socks(
            socks_endpoint=endpoint,
            target=self.probe_target,
            deadline=20.0,
            connect_timeout=2.0,
            io_timeout=2.0,
            clock=lambda: 10.0,
            connection_factory=connect,
            ssl_context_factory=lambda: context,
        )

        self.assertEqual(result, "")
        self.assertEqual(connected_to[0][0], endpoint)
        self.assertEqual(context.server_hostname, self.probe_target.hostname)
        self.assertIn(self.probe_target.hostname.encode("ascii"), raw_socket.sent[1])
        self.assertIn(b"Host: probe.example.invalid", tls_socket.sent[0])

    def test_marker_or_status_mismatch_fails(self) -> None:
        for response in (
            b"HTTP/1.1 204 No Content\r\nX-Pokrov-Egress-Probe: wrong\r\n\r\n",
            b"HTTP/1.1 200 OK\r\nX-Pokrov-Egress-Probe: pokrov-authenticated-egress-v1\r\nContent-Length: 0\r\n\r\n",
        ):
            with self.subTest(response=response[:16]):
                self.assertFalse(
                    self.module._read_http_response(_MemorySocket(response), target=self.probe_target)
                )

    def test_timeout_terminates_process_and_removes_ephemeral_config(self) -> None:
        process = _FakeProcess()
        config_paths: list[Path] = []

        def start_core(_core_path: Path, config_path: Path):
            config_paths.append(config_path)
            self.assertTrue(config_path.exists())
            return process

        def create_endpoint(runtime_dir: Path):
            return _FakeEndpoint(), runtime_dir / "authenticated-proxy.sock"

        with (
            mock.patch.object(self.module, "_choose_loopback_port", return_value=31080),
            mock.patch.object(self.module, "_start_core", side_effect=start_core),
            mock.patch.object(self.module, "_create_unix_socks_listener", side_effect=create_endpoint),
            mock.patch.object(self.module, "_wait_for_child_listener", return_value=""),
            mock.patch.object(self.module, "_start_unix_socks_bridge", return_value=_FakeEndpoint()),
            mock.patch.object(self.module, "_probe_through_socks", return_value="timeout"),
            mock.patch.object(self.module, "_terminate_process") as terminate,
        ):
            response = self.module.handle_request(
                self._request(),
                config_path=self.config_path,
                runtime_parent=self.root,
            )

        self.assertEqual(response["status"], "fail")
        self.assertEqual(response["classification"], "timeout")
        terminate.assert_called_once_with(process, timeout_seconds=1.0)
        self.assertTrue(config_paths)
        self.assertTrue(all(not path.exists() for path in config_paths))
        self.assertEqual(list(self.root.glob("pokrov-authenticated-egress-*")), [])

    def test_core_spawn_argv_and_env_contain_no_credentials(self) -> None:
        config_path = self.root / "ephemeral.json"
        with mock.patch.object(self.module.subprocess, "Popen", side_effect=OSError) as popen:
            with self.assertRaises(OSError):
                self.module._start_core(self.core_path, config_path)

        argv = popen.call_args.args[0]
        child_env = popen.call_args.kwargs["env"]
        serialized = json.dumps({"argv": argv, "env": child_env}, sort_keys=True)
        self.assertEqual(argv, [str(self.core_path), "run", "-c", str(config_path)])
        self.assertLessEqual(set(child_env), {"PATH", "LANG", "LC_ALL", "SystemRoot"})
        self.assertNotIn("11111111-1111-4111-8111-111111111111", serialized)
        self.assertNotIn("A" * 43, serialized)
        self.assertNotIn("0000000000000000", serialized)

    def test_pass_response_contains_no_credential_or_endpoint_material(self) -> None:
        process = _FakeProcess()

        def create_endpoint(runtime_dir: Path):
            return _FakeEndpoint(), runtime_dir / "authenticated-proxy.sock"

        with (
            mock.patch.object(self.module, "_choose_loopback_port", return_value=31080),
            mock.patch.object(self.module, "_start_core", return_value=process),
            mock.patch.object(self.module, "_create_unix_socks_listener", side_effect=create_endpoint),
            mock.patch.object(self.module, "_wait_for_child_listener", return_value=""),
            mock.patch.object(self.module, "_start_unix_socks_bridge", return_value=_FakeEndpoint()),
            mock.patch.object(self.module, "_probe_through_socks", return_value=""),
            mock.patch.object(self.module, "_process_owns_loopback_listener", return_value=True),
            mock.patch.object(self.module, "_terminate_process"),
        ):
            response = self.module.handle_request(
                self._request(),
                config_path=self.config_path,
                runtime_parent=self.root,
            )

        serialized = json.dumps(response, sort_keys=True)
        self.assertEqual(response["status"], "pass")
        self.assertEqual(response["classification"], "authenticated_egress")
        self.assertEqual(set(response), self.module._RESPONSE_FIELDS)
        self.assertNotIn(self.node_host, serialized)
        self.assertNotIn("11111111-1111-4111-8111-111111111111", serialized)
        self.assertNotIn("A" * 43, serialized)

    @unittest.skipIf(os.name == "nt", "Linux UDS ownership policy")
    def test_precreated_unix_endpoint_is_rejected(self) -> None:
        runtime_dir = self.root / "private-runtime"
        runtime_dir.mkdir(mode=0o700)
        endpoint = runtime_dir / self.module._UNIX_SOCKS_NAME
        endpoint.write_text("occupied", encoding="utf-8")

        with self.assertRaises(self.module.AdapterValidationError):
            self.module._create_unix_socks_listener(runtime_dir)

    def test_hijacked_loopback_port_cannot_produce_pass(self) -> None:
        process = _FakeProcess()

        def create_endpoint(runtime_dir: Path):
            return _FakeEndpoint(), runtime_dir / "authenticated-proxy.sock"

        with (
            mock.patch.object(self.module, "_choose_loopback_port", return_value=31080),
            mock.patch.object(self.module, "_start_core", return_value=process),
            mock.patch.object(self.module, "_create_unix_socks_listener", side_effect=create_endpoint),
            mock.patch.object(self.module, "_wait_for_child_listener", return_value="proxy_unavailable"),
            mock.patch.object(self.module, "_probe_through_socks") as probe,
            mock.patch.object(self.module, "_terminate_process"),
        ):
            response = self.module.handle_request(
                self._request(), config_path=self.config_path, runtime_parent=self.root
            )

        probe.assert_not_called()
        self.assertEqual(response["status"], "fail")
        self.assertEqual(response["classification"], "proxy_unavailable")

    def test_wait_for_child_listener_rejects_unowned_port(self) -> None:
        process = _FakeProcess()
        ticks = iter((0.0, 1.0))
        with mock.patch.object(self.module, "_process_owns_loopback_listener", return_value=False) as owns_listener:
            result = self.module._wait_for_child_listener(
                process,
                port=31080,
                deadline=1.0,
                clock=lambda: next(ticks),
                sleep=lambda _seconds: None,
            )

        self.assertEqual(result, "proxy_unavailable")
        owns_listener.assert_called_once_with(process, port=31080)

    def test_child_must_own_listener_after_marker_before_pass(self) -> None:
        process = _FakeProcess()

        def create_endpoint(runtime_dir: Path):
            return _FakeEndpoint(), runtime_dir / "authenticated-proxy.sock"

        with (
            mock.patch.object(self.module, "_choose_loopback_port", return_value=31080),
            mock.patch.object(self.module, "_start_core", return_value=process),
            mock.patch.object(self.module, "_create_unix_socks_listener", side_effect=create_endpoint),
            mock.patch.object(self.module, "_wait_for_child_listener", return_value=""),
            mock.patch.object(self.module, "_start_unix_socks_bridge", return_value=_FakeEndpoint()),
            mock.patch.object(self.module, "_probe_through_socks", return_value=""),
            mock.patch.object(self.module, "_process_owns_loopback_listener", return_value=False) as owns_listener,
            mock.patch.object(self.module, "_terminate_process"),
        ):
            response = self.module.handle_request(
                self._request(), config_path=self.config_path, runtime_parent=self.root
            )

        owns_listener.assert_called_once_with(process, port=31080)
        self.assertEqual(response["status"], "fail")
        self.assertEqual(response["classification"], "proxy_ownership_lost")

    @unittest.skipIf(os.name == "nt", "POSIX path policy")
    def test_posix_path_policy_rejects_symlink_and_group_writable_file(self) -> None:
        target = self.root / "owned-file"
        target.write_text("synthetic", encoding="utf-8")
        target.chmod(0o700)
        link = self.root / "owned-link"
        link.symlink_to(target)

        self.assertTrue(self.module._secure_runtime_path(target, executable=True))
        self.assertFalse(self.module._secure_runtime_path(link, executable=True))
        target.chmod(0o720)
        self.assertFalse(self.module._secure_runtime_path(target, executable=True))

    @unittest.skipIf(os.name == "nt", "POSIX ownership policy")
    def test_posix_path_policy_rejects_untrusted_owner(self) -> None:
        real_stat = self.store_path.stat()
        untrusted_stat = mock.Mock(st_mode=real_stat.st_mode, st_uid=real_stat.st_uid + 1)
        with mock.patch.object(Path, "stat", return_value=untrusted_stat):
            self.assertFalse(self.module._secure_runtime_path(self.store_path, executable=False))

    @unittest.skipIf(os.name == "nt", "POSIX descriptor race policy")
    def test_posix_descriptor_read_rejects_parent_replaced_with_symlink(self) -> None:
        live_parent = self.root / "live"
        replacement_parent = self.root / "replacement"
        moved_parent = self.root / "moved-live"
        live_parent.mkdir(mode=0o700)
        replacement_parent.mkdir(mode=0o700)
        requested = live_parent / "document.json"
        replacement = replacement_parent / "document.json"
        requested.write_text('{"source":"requested"}', encoding="utf-8")
        replacement.write_text('{"source":"replacement"}', encoding="utf-8")
        requested.chmod(0o600)
        replacement.chmod(0o600)
        real_read = os.read
        replaced = False

        def racing_read(fd: int, size: int) -> bytes:
            nonlocal replaced
            if not replaced:
                live_parent.rename(moved_parent)
                live_parent.symlink_to(replacement_parent, target_is_directory=True)
                replaced = True
            return real_read(fd, size)

        with (
            mock.patch.object(self.module.os, "read", side_effect=racing_read),
            self.assertRaises(self.module.AdapterValidationError),
        ):
            self.module._read_secure_json(requested, max_bytes=1024)

        self.assertTrue(replaced)

    @unittest.skipIf(os.name == "nt", "POSIX descriptor bounded read policy")
    def test_posix_descriptor_read_handles_partials_and_rejects_oversize_before_read(self) -> None:
        document = self.root / "partial.json"
        document.write_text('{"ok":true}', encoding="utf-8")
        document.chmod(0o600)
        real_read = os.read
        partial_calls = 0

        def partial_read(fd: int, size: int) -> bytes:
            nonlocal partial_calls
            partial_calls += 1
            return real_read(fd, min(size, 2))

        with mock.patch.object(self.module.os, "read", side_effect=partial_read):
            result = self.module._read_secure_json(document, max_bytes=1024)

        self.assertEqual(result, {"ok": True})
        self.assertGreater(partial_calls, 1)

        document.write_bytes(b"x" * 17)
        document.chmod(0o600)
        with (
            mock.patch.object(self.module.os, "read") as bounded_read,
            self.assertRaises(self.module.AdapterValidationError),
        ):
            self.module._read_secure_json(document, max_bytes=16)
        bounded_read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
