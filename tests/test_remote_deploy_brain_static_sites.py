import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


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
            remote_marketing="/var/www/portal/releases/202605070001/marketing",
        )

        joined = "\n".join(checks)

        self.assertIn("test -f /var/www/portal/releases/202605070001/webapp/index.html", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/marketing/index.html", joined)
        self.assertIn("test -f /var/www/portal/releases/202605070001/marketing/checkout/index.html", joined)
        self.assertIn("test ! -e /var/www/portal/releases/202605070001/marketing/fk-verify.html", joined)
        self.assertIn("test ! -e /var/www/portal/releases/202605070001/marketing/fk-payment-theme.css", joined)
        self.assertNotIn("test -f /var/www/portal/releases/202605070001/marketing/fk-verify.html", joined)

    def test_post_deploy_smoke_requires_legacy_payment_static_absent(self) -> None:
        commands = self.module._post_deploy_smoke_commands(
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
        )

        joined = "\n".join(commands)

        self.assertIn("https://api.pokrov.space/api/health", joined)
        self.assertIn("https://pokrov.space/", joined)
        self.assertIn("https://app.pokrov.space/", joined)
        self.assertIn("https://pokrov.space/fk-verify.html", joined)
        self.assertIn("https://pokrov.space/fk-payment-theme.css", joined)
        self.assertIn("404|410", joined)
        self.assertIn("legacy_static_present", joined)
        self.assertIn("absent_or_fallback", joined)
        self.assertIn("payment-page-global", joined)
        self.assertIn("^[0-9a-fA-F]{32,128}$", joined)

    def test_local_static_output_validation_requires_release_ready_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            local_webapp = root / "webapp" / "out"
            local_marketing = root / "marketing" / "out"

            failures = self.module._local_static_output_validation_failures(
                local_webapp=local_webapp,
                local_marketing=local_marketing,
            )

            self.assertIn(f"missing local static file: {local_webapp / 'index.html'}", failures)
            self.assertIn(f"missing local static file: {local_marketing / 'index.html'}", failures)
            self.assertIn(f"missing local static file: {local_marketing / 'checkout' / 'index.html'}", failures)

            (local_webapp).mkdir(parents=True)
            (local_marketing / "checkout").mkdir(parents=True)
            (local_webapp / "index.html").write_text("app", encoding="utf-8")
            (local_marketing / "index.html").write_text("marketing", encoding="utf-8")
            (local_marketing / "checkout" / "index.html").write_text("checkout", encoding="utf-8")
            (local_marketing / "fk-verify.html").write_text("legacy", encoding="utf-8")
            (local_marketing / "fk-payment-theme.css").write_text("legacy", encoding="utf-8")

            failures = self.module._local_static_output_validation_failures(
                local_webapp=local_webapp,
                local_marketing=local_marketing,
            )

            self.assertIn(f"forbidden legacy payment static file is present: {local_marketing / 'fk-verify.html'}", failures)
            self.assertIn(f"forbidden legacy payment static file is present: {local_marketing / 'fk-payment-theme.css'}", failures)

            (local_marketing / "fk-verify.html").unlink()
            (local_marketing / "fk-payment-theme.css").unlink()
            self.assertEqual(
                [],
                self.module._local_static_output_validation_failures(
                    local_webapp=local_webapp,
                    local_marketing=local_marketing,
                ),
            )

    def test_plan_only_builds_local_bundles_without_ssh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            local_webapp = root / "webapp" / "out"
            local_marketing = root / "marketing" / "out"
            (local_webapp).mkdir(parents=True)
            (local_marketing / "checkout").mkdir(parents=True)
            (local_webapp / "index.html").write_text("app", encoding="utf-8")
            (local_marketing / "index.html").write_text("marketing", encoding="utf-8")
            (local_marketing / "checkout" / "index.html").write_text("checkout", encoding="utf-8")

            def fail_connect(*_args, **_kwargs):
                raise AssertionError("plan-only must not open SSH")

            old_repo_root = self.module.REPO_ROOT
            old_connect = self.module.connect_node
            old_argv = sys.argv
            try:
                self.module.REPO_ROOT = root
                self.module.connect_node = fail_connect
                sys.argv = [
                    "remote_deploy_brain_static_sites.py",
                    "--brain-ip",
                    "82.21.114.104",
                    "--plan-only",
                ]

                self.assertEqual(0, self.module.main())
            finally:
                self.module.REPO_ROOT = old_repo_root
                self.module.connect_node = old_connect
                sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
