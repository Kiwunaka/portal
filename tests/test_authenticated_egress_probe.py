import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "authenticated_egress_probe.py"
    spec = importlib.util.spec_from_file_location("authenticated_egress_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AuthenticatedEgressProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.registry = Path(self._tmp.name) / "profiles.json"
        self.now = datetime(2026, 8, 1, 12, 0, 0)

    def _write_registry(self, *, expires_at: str = "2026-08-02T12:00:00Z") -> None:
        self.registry.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "profiles": {
                        "de": {
                            "profile_id": "de_canary_v1",
                            "expires_at": expires_at,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_missing_runtime_configuration_is_unavailable(self) -> None:
        result = self.module.probe_authenticated_egress(node_code="de", host="node.test", port=443)

        self.assertIsNone(result["ok"])
        self.assertEqual(result["state"], "unavailable")
        self.assertEqual(result["error_kind"], "probe_material_unavailable")

    def test_invalid_port_is_fail_closed_without_exception(self) -> None:
        result = self.module.probe_authenticated_egress(
            node_code="de",
            host="node.test",
            port="not-a-port",
        )

        self.assertIsNone(result["ok"])
        self.assertEqual(result["state"], "unavailable")
        self.assertEqual(result["error_kind"], "probe_request_invalid")

    def test_adapter_subprocess_does_not_inherit_parent_secrets(self) -> None:
        with (
            mock.patch.dict(
                self.module.os.environ,
                {
                    "BOT_TOKEN": "parent-only-value",
                    "DATABASE_URL": "parent-only-value",
                    "NODE_AUTHENTICATED_EGRESS_PROFILES": "parent-only-value",
                },
            ),
            mock.patch.object(self.module.subprocess, "Popen", side_effect=OSError) as popen,
        ):
            error, raw = self.module._run_adapter(
                adapter_path=Path(sys.executable).resolve(),
                request={"schema_version": 1},
                timeout_sec=1.0,
            )

        self.assertEqual(error, "probe_material_unavailable")
        self.assertEqual(raw, b"")
        child_env = popen.call_args.kwargs["env"]
        self.assertNotIn("BOT_TOKEN", child_env)
        self.assertNotIn("DATABASE_URL", child_env)
        self.assertNotIn("NODE_AUTHENTICATED_EGRESS_PROFILES", child_env)
        self.assertLessEqual(set(child_env), {"PATH", "LANG", "LC_ALL", "SystemRoot"})

    def test_expired_profile_is_unavailable_without_running_adapter(self) -> None:
        self._write_registry(expires_at="2026-08-01T11:59:59Z")
        with mock.patch.object(self.module, "_run_adapter") as adapter:
            result = self.module.probe_authenticated_egress(
                node_code="de",
                host="node.test",
                port=443,
                adapter_path=sys.executable,
                profiles_path=self.registry,
                now=self.now,
            )

        adapter.assert_not_called()
        self.assertIsNone(result["ok"])
        self.assertEqual(result["error_kind"], "probe_material_expired")

    def test_strict_adapter_pass_proves_authenticated_egress_without_returning_profile_id(self) -> None:
        self._write_registry()
        response = json.dumps(
            {
                "schema_version": 1,
                "profile_id": "de_canary_v1",
                "status": "pass",
                "classification": "authenticated_egress",
                "detail_code": None,
            }
        ).encode("utf-8")
        with mock.patch.object(self.module, "_run_adapter", return_value=("", response)) as adapter:
            result = self.module.probe_authenticated_egress(
                node_code="de",
                host="node.test",
                port=443,
                adapter_path=sys.executable,
                profiles_path=self.registry,
                now=self.now,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "healthy")
        self.assertEqual(result["probe_classification"], "authenticated_egress")
        self.assertNotIn("profile_id", result)
        request = adapter.call_args.kwargs["request"]
        self.assertEqual(set(request), {"schema_version", "node_code", "host", "port", "profile_id"})
        self.assertFalse(any(key in request for key in ("uuid", "private_key", "short_id", "token", "secret")))

    def test_pass_with_near_miss_classification_is_fail_closed(self) -> None:
        response = json.dumps(
            {
                "schema_version": 1,
                "profile_id": "de_canary_v1",
                "status": "pass",
                "classification": "authenticated_egress_ok",
                "detail_code": None,
            }
        ).encode("utf-8")

        ok, error_kind, classification = self.module._parse_adapter_response(
            response,
            expected_profile_id="de_canary_v1",
        )

        self.assertFalse(ok)
        self.assertEqual(error_kind, "adapter_invalid_pass")
        self.assertEqual(classification, "adapter_failure")

    def test_pass_with_non_null_detail_is_fail_closed(self) -> None:
        response = json.dumps(
            {
                "schema_version": 1,
                "profile_id": "de_canary_v1",
                "status": "pass",
                "classification": "authenticated_egress",
                "detail_code": "unexpected_detail",
            }
        ).encode("utf-8")

        ok, error_kind, classification = self.module._parse_adapter_response(
            response,
            expected_profile_id="de_canary_v1",
        )

        self.assertFalse(ok)
        self.assertEqual(error_kind, "adapter_invalid_pass")
        self.assertEqual(classification, "adapter_failure")

    def test_mixed_case_pass_is_fail_closed(self) -> None:
        response = json.dumps(
            {
                "schema_version": 1,
                "profile_id": "de_canary_v1",
                "status": "PASS",
                "classification": "authenticated_egress",
                "detail_code": None,
            }
        ).encode("utf-8")

        ok, error_kind, classification = self.module._parse_adapter_response(
            response,
            expected_profile_id="de_canary_v1",
        )

        self.assertFalse(ok)
        self.assertEqual(error_kind, "adapter_malformed_response")
        self.assertEqual(classification, "adapter_failure")

    def test_adapter_handshake_failure_is_failed_not_unavailable(self) -> None:
        self._write_registry()
        response = json.dumps(
            {
                "schema_version": 1,
                "profile_id": "de_canary_v1",
                "status": "fail",
                "classification": "reality_handshake_failed",
                "detail_code": "reality_handshake_failed",
            }
        ).encode("utf-8")
        with mock.patch.object(self.module, "_run_adapter", return_value=("", response)):
            result = self.module.probe_authenticated_egress(
                node_code="de",
                host="node.test",
                port=443,
                adapter_path=sys.executable,
                profiles_path=self.registry,
                now=self.now,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["error_kind"], "reality_handshake_failed")

    @unittest.skipIf(os.name == "nt", "POSIX path policy")
    def test_posix_runtime_path_rejects_symlink_and_group_writable_file(self) -> None:
        target = Path(self._tmp.name) / "adapter"
        target.write_text("adapter", encoding="utf-8")
        target.chmod(0o700)
        link = Path(self._tmp.name) / "adapter-link"
        link.symlink_to(target)

        self.assertTrue(self.module._secure_runtime_path(target, executable=True))
        self.assertFalse(self.module._secure_runtime_path(link, executable=True))

        target.chmod(0o720)
        self.assertFalse(self.module._secure_runtime_path(target, executable=True))

    @unittest.skipIf(os.name == "nt", "POSIX ownership policy")
    def test_posix_runtime_path_rejects_untrusted_owner(self) -> None:
        target = Path(self._tmp.name) / "profiles.json"
        target.write_text("{}", encoding="utf-8")
        target.chmod(0o600)
        real_stat = target.stat()
        untrusted_stat = mock.Mock(st_mode=real_stat.st_mode, st_uid=real_stat.st_uid + 1)

        with mock.patch.object(Path, "stat", return_value=untrusted_stat):
            self.assertFalse(self.module._secure_runtime_path(target, executable=False))


if __name__ == "__main__":
    unittest.main()
