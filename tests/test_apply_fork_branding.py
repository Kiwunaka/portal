import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = (
        repo_root
        / "external"
        / "client-fork"
        / "app"
        / ".github"
        / "scripts"
        / "apply_fork_branding.py"
    )
    spec = importlib.util.spec_from_file_location("apply_fork_branding", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ApplyForkBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_rewrite_constants_preserves_env_driven_release_metadata(self) -> None:
        source = """
abstract class Constants {
  static const appName = "Legacy";
  static const githubUrl = String.fromEnvironment(
    "PORTAL_RELEASE_REPOSITORY_URL",
    defaultValue: "",
  );
}
"""

        rewritten = self.module._rewrite_constants(
            source,
            brand_name="POKROV VPN",
        )

        self.assertIn('static const appName = "POKROV VPN";', rewritten)
        self.assertIn('String.fromEnvironment(\n    "PORTAL_RELEASE_REPOSITORY_URL",', rewritten)
        self.assertNotIn('static const githubUrl = "https://github.com/', rewritten)

    def test_rewrite_windows_exe_config_uses_canonical_public_publisher_url(self) -> None:
        source = """
publisher: Legacy VPN
publisher_url: https://github.com/example/repo
display_name: Legacy VPN
executable_name: Legacy.exe
output_base_file_name: legacy-setup
install_dir_name: "{autopf64}\\Legacy VPN"
"""

        rewritten = self.module._rewrite_windows_exe_config(
            source,
            publisher_name="POKROV VPN",
            publisher_url="https://pokrov.space/",
            display_name="POKROV VPN",
            exe_name="POKROVVPN.exe",
            output_base_file_name="pokrov-vpn-setup",
            install_dir_name='"{autopf64}\\\\POKROV VPN"',
        )

        self.assertIn("publisher: POKROV VPN", rewritten)
        self.assertIn("publisher_url: https://pokrov.space/", rewritten)
        self.assertIn("display_name: POKROV VPN", rewritten)
        self.assertNotIn("github.com/example/repo", rewritten)


if __name__ == "__main__":
    unittest.main()
