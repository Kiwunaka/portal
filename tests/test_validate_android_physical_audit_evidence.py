from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "validate_android_physical_audit_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_android_physical_audit_evidence", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_payload() -> dict:
    return {
        "serial": "R58N12345AB",
        "package_name": "space.pokrov.pokrov_android_shell",
        "baseline": [],
        "after_launch": [],
        "after_connect": [],
        "after_disconnect": [],
        "probes": [],
        "failures": [],
        "package_evidence": {
            "package_name": "space.pokrov.pokrov_android_shell",
            "version_name": "0.2.0-beta.1",
            "version_code": "42",
            "installer_package_name": "com.android.packageinstaller",
            "code_path": "/data/app/base.apk",
            "debuggable": False,
            "release_evidence": "app-release.apk sha256 1A369891641964A9A30A296E7D47111A07B6DDAAD5ABC293F7EF938A654DADB0",
        },
        "audit_metadata": {
            "created_at_utc": "2026-05-08T00:00:00Z",
            "require_release_build": True,
            "release_evidence_present": True,
            "connect_wait_sec": 30,
            "disconnect_wait_sec": 15,
            "after_connect_observed": True,
            "after_disconnect_observed": True,
        },
    }


class AndroidPhysicalAuditEvidenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_accepts_current_physical_release_audit_evidence(self) -> None:
        report = self.module.validate_payload(_valid_payload())

        self.assertTrue(report["ok"])
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["summary"]["debuggable"], False)

    def test_rejects_emulator_rehearsal_even_if_failures_empty(self) -> None:
        payload = _valid_payload()
        payload["serial"] = "emulator-5554"

        report = self.module.validate_payload(payload)

        self.assertFalse(report["ok"])
        self.assertIn("physical adb serial", "\n".join(report["missing"]))

    def test_rejects_debuggable_or_wrong_package_evidence(self) -> None:
        payload = _valid_payload()
        payload["package_name"] = "space.pokrov.vpn"
        payload["package_evidence"]["package_name"] = "space.pokrov.vpn"
        payload["package_evidence"]["debuggable"] = True

        report = self.module.validate_payload(payload)

        missing = "\n".join(report["missing"])
        self.assertIn("package_name=space.pokrov.pokrov_android_shell", missing)
        self.assertIn("package_evidence.package_name=space.pokrov.pokrov_android_shell", missing)
        self.assertIn("package_evidence.debuggable=false", missing)

    def test_rejects_old_audit_json_without_metadata_and_release_evidence(self) -> None:
        payload = {
            "serial": "R58N12345AB",
            "package_name": "space.pokrov.pokrov_android_shell",
            "baseline": [],
            "after_launch": [],
            "after_connect": [],
            "after_disconnect": [],
            "probes": [],
            "failures": [],
        }

        report = self.module.validate_payload(payload)

        self.assertFalse(report["ok"])
        missing = "\n".join(report["missing"])
        self.assertIn("package_evidence from --require-release-build", missing)
        self.assertIn("audit_metadata from current android_localhost_audit.py", missing)


if __name__ == "__main__":
    unittest.main()
