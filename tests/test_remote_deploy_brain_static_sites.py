import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "remote_deploy_brain_static_sites.py"
    spec = importlib.util.spec_from_file_location("remote_deploy_brain_static_sites", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteDeployBrainStaticSitesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_release_payload_validation_requires_legacy_payment_static_absent(self) -> None:
        checks = self.module._release_payload_validation_checks(
            remote_webapp="/var/www/portal/releases/202605070001/webapp",
            remote_adminapp="/var/www/portal/releases/202605070001/adminapp",
            remote_marketing="/var/www/portal/releases/202605070001/marketing",
        )

        joined = "\n".join(checks)

        self.assertIn("test -f /var/www/portal/releases/202605070001/webapp/index.html", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/adminapp/index.html", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/adminapp/__build.json", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/adminapp/__routes.json", joined)
        self.assertIn("pokrov-operator-center", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/marketing/index.html", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/marketing/checkout/index.html", joined)
        self.assertIn("test ! -e /var/www/portal/releases/202605070001/marketing/fk-verify.html", joined)
        self.assertIn("test ! -e /var/www/portal/releases/202605070001/marketing/fk-payment-theme.css", joined)
        self.assertNotIn("test -f /var/www/portal/releases/202605070001/marketing/fk-verify.html", joined)

    def test_post_deploy_smoke_requires_legacy_payment_static_absent(self) -> None:
        commands = self.module._post_deploy_smoke_commands(
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            admin_domain="admin.pokrov.space",
        )

        joined = "\n".join(commands)

        self.assertIn("https://api.pokrov.space/api/health", joined)
        self.assertIn("https://pokrov.space/", joined)
        self.assertIn("https://app.pokrov.space/", joined)
        self.assertIn("https://admin.pokrov.space/", joined)
        self.assertIn("https://admin.pokrov.space/__build.json", joined)
        self.assertIn("https://admin.pokrov.space/__routes.json", joined)
        self.assertIn("operator_build_ok", joined)
        self.assertIn("operator_routes_ok", joined)
        self.assertIn("https://pokrov.space/fk-verify.html", joined)
        self.assertIn("https://pokrov.space/fk-payment-theme.css", joined)
        self.assertIn('[ "$status" = "404" ] || [ "$status" = "410" ]', joined)
        self.assertIn("legacy_static_present", joined)
        self.assertIn("absent_or_fallback", joined)
        self.assertIn("payment-page-global", joined)
        self.assertIn("^[0-9a-fA-F]{32,128}$", joined)
        self.assertNotIn(";*)", joined)
        self.assertNotIn("case \"$status\"", joined)

    def test_local_static_output_validation_requires_release_ready_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            local_webapp = root / "webapp" / "out"
            local_adminapp = root / "adminapp" / "out"
            local_marketing = root / "marketing" / "out"

            failures = self.module._local_static_output_validation_failures(
                local_webapp=local_webapp,
                local_adminapp=local_adminapp,
                local_marketing=local_marketing,
            )

            self.assertIn(f"missing local static file: {local_webapp / 'index.html'}", failures)
            self.assertIn(f"missing local static file: {local_adminapp / 'index.html'}", failures)
            self.assertIn(f"missing local static file: {local_adminapp / '__build.json'}", failures)
            self.assertIn(f"missing local static file: {local_adminapp / '__routes.json'}", failures)
            self.assertIn(f"missing local static file: {local_marketing / 'index.html'}", failures)
            self.assertIn(f"missing local static file: {local_marketing / 'checkout' / 'index.html'}", failures)

            (local_webapp).mkdir(parents=True)
            (local_adminapp).mkdir(parents=True)
            (local_marketing / "checkout").mkdir(parents=True)
            (local_webapp / "index.html").write_text("app", encoding="utf-8")
            (local_adminapp / "index.html").write_text("admin", encoding="utf-8")
            self._write_admin_identity(local_adminapp)
            (local_marketing / "index.html").write_text("marketing", encoding="utf-8")
            (local_marketing / "checkout" / "index.html").write_text("checkout", encoding="utf-8")
            (local_marketing / "fk-verify.html").write_text("legacy", encoding="utf-8")
            (local_marketing / "fk-payment-theme.css").write_text("legacy", encoding="utf-8")

            failures = self.module._local_static_output_validation_failures(
                local_webapp=local_webapp,
                local_adminapp=local_adminapp,
                local_marketing=local_marketing,
            )

            self.assertIn(f"forbidden legacy payment static file is present: {local_marketing / 'fk-verify.html'}", failures)
            self.assertIn(f"forbidden legacy payment static file is present: {local_marketing / 'fk-payment-theme.css'}", failures)

            (local_marketing / "fk-verify.html").unlink()
            (local_marketing / "fk-payment-theme.css").unlink()
            (local_adminapp / "bad.js").write_text('fetch("http://127.0.0.1:3107/api/admin/auth/session")', encoding="utf-8")
            failures = self.module._local_static_output_validation_failures(
                local_webapp=local_webapp,
                local_adminapp=local_adminapp,
                local_marketing=local_marketing,
            )
            self.assertIn(
                f"forbidden dev API origin 'http://127.0.0.1:3107' in adminapp static file: {local_adminapp / 'bad.js'}",
                failures,
            )

            (local_adminapp / "bad.js").unlink()
            self.assertEqual(
                [],
                self.module._local_static_output_validation_failures(
                    local_webapp=local_webapp,
                    local_adminapp=local_adminapp,
                    local_marketing=local_marketing,
                ),
            )

    @staticmethod
    def _write_admin_identity(local_adminapp: Path) -> None:
        (local_adminapp / "__build.json").write_text(
            json.dumps(
                {
                    "schema": "pokrov-operator-build-v1",
                    "app": "pokrov-operator-center",
                    "canonical_domain": "admin.pokrov.space",
                    "frontend_commit": "abcdef1",
                    "expected_api_schema": "admin-v2.1",
                    "route_manifest_hash": "route-hash",
                    "cutover_matrix_hash": "cutover-hash",
                }
            ),
            encoding="utf-8",
        )
        (local_adminapp / "__routes.json").write_text(
            json.dumps(
                {
                    "schema": "pokrov-operator-route-manifest-v1",
                    "app": "pokrov-operator-center",
                    "manifest_hash": "route-hash",
                    "cutover_matrix_hash": "cutover-hash",
                    "workspaces": [{"id": f"workspace-{index}"} for index in range(7)],
                }
            ),
            encoding="utf-8",
        )

    def test_plan_only_builds_local_bundles_without_ssh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            local_webapp = root / "webapp" / "out"
            local_adminapp = root / "adminapp" / "out"
            local_marketing = root / "marketing" / "out"
            (local_webapp).mkdir(parents=True)
            (local_adminapp).mkdir(parents=True)
            (local_marketing / "checkout").mkdir(parents=True)
            (local_webapp / "index.html").write_text("app", encoding="utf-8")
            (local_adminapp / "index.html").write_text("admin", encoding="utf-8")
            self._write_admin_identity(local_adminapp)
            (local_marketing / "index.html").write_text("marketing", encoding="utf-8")
            (local_marketing / "checkout" / "index.html").write_text("checkout", encoding="utf-8")

            def fail_connect(*_args, **_kwargs):
                raise AssertionError("plan-only must not open SSH")

            fake_node_access = ModuleType("node_access")
            fake_node_access.connect_node = fail_connect
            old_repo_root = self.module.REPO_ROOT
            old_node_access = sys.modules.get("node_access")
            old_argv = sys.argv
            try:
                self.module.REPO_ROOT = root
                sys.modules["node_access"] = fake_node_access
                sys.argv = [
                    "remote_deploy_brain_static_sites.py",
                    "--brain-ip",
                    "82.21.114.104",
                    "--plan-only",
                ]

                self.assertEqual(0, self.module.main())
            finally:
                self.module.REPO_ROOT = old_repo_root
                if old_node_access is None:
                    sys.modules.pop("node_access", None)
                else:
                    sys.modules["node_access"] = old_node_access
                sys.argv = old_argv

    def test_adminapp_rollback_command_is_exact_fingerprint_bound_and_atomic(self) -> None:
        command = self.module._adminapp_rollback_command(
            remote_root="/var/www/portal",
            expected_current_route_hash="a" * 64,
            expected_current_cutover_hash="b" * 64,
            expected_rollback_route_hash="c" * 64,
            expected_rollback_cutover_hash="d" * 64,
        )
        self.assertIn("current=$(readlink -f /var/www/portal/adminapp)", command)
        self.assertIn("rollback=$(readlink -f /var/www/portal/adminapp.rollback)", command)
        self.assertIn('test "$current" != "$rollback"', command)
        self.assertIn("/var/www/portal/adminapp.next", command)
        self.assertIn("/var/www/portal/adminapp.rollback.next", command)
        self.assertIn("a" * 64, command)
        self.assertIn("d" * 64, command)
        self.assertGreaterEqual(command.count("python3 -c"), 3)

    def test_adminapp_rollback_command_rejects_non_exact_hashes(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact lowercase SHA-256"):
            self.module._adminapp_rollback_command(
                remote_root="/var/www/portal",
                expected_current_route_hash="not-a-hash",
                expected_current_cutover_hash="b" * 64,
                expected_rollback_route_hash="c" * 64,
                expected_rollback_cutover_hash="d" * 64,
            )


if __name__ == "__main__":
    unittest.main()
