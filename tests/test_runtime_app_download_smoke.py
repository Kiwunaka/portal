import importlib.util
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "runtime_app_download_smoke.py"
    spec = importlib.util.spec_from_file_location("runtime_app_download_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeAppDownloadSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_parse_wrapper_args_strips_redact_flag(self) -> None:
        redact, passthrough = self.module._parse_wrapper_args(
            ["--redact", "--base-url", "https://api.pokrov.space", "--check-providers"]
        )

        self.assertTrue(redact)
        self.assertEqual(passthrough, ["--base-url", "https://api.pokrov.space", "--check-providers"])

    def test_redact_runtime_text_covers_telegram_init_data(self) -> None:
        raw = (
            "TELEGRAM_INIT_DATA=query_id=AAA&user=%7B%22id%22%3A1%7D&hash=secret "
            "--init-data query_id=BBB&auth_date=1710000000&hash=other "
            "--init-data=query_id=CCC&signature=sig&chat_instance=chat&hash=equal"
        )

        redacted = self.module._redact_runtime_text(raw)

        self.assertNotIn("query_id=AAA", redacted)
        self.assertNotIn("query_id=BBB", redacted)
        self.assertNotIn("query_id=CCC", redacted)
        self.assertNotIn("signature=sig", redacted)
        self.assertNotIn("chat_instance=chat", redacted)
        self.assertNotIn("secret", redacted)
        self.assertNotIn("other", redacted)
        self.assertNotIn("equal", redacted)
        self.assertIn("TELEGRAM_INIT_DATA=<redacted>", redacted)
        self.assertIn("--init-data <redacted>", redacted)

    def test_redact_runtime_text_strips_github_release_asset_signed_query(self) -> None:
        raw = (
            "[OK] android.apk_url: HEAD 200 -> "
            "https://release-assets.githubusercontent.com/github-production-release-asset/1218036659/asset-id?"
            "sp=r&sv=2018-11-09&sig=temporary-signature&jwt=temporary-jwt"
        )

        redacted = self.module._redact_runtime_text(raw)

        self.assertIn("https://release-assets.githubusercontent.com/github-production-release-asset/1218036659/asset-id?<redacted-query>", redacted)
        self.assertNotIn("temporary-signature", redacted)
        self.assertNotIn("temporary-jwt", redacted)
        self.assertNotIn("sig=", redacted)
        self.assertNotIn("jwt=", redacted)

    def test_main_redacts_stdout_and_stderr(self) -> None:
        def fake_run(_argv):
            print("TELEGRAM_INIT_DATA=query_id=AAA&hash=secret")
            print("--init-data=query_id=BBB&signature=sig&hash=hidden", file=sys.stderr)
            return 2

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.module, "_run_smoke", side_effect=fake_run):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = self.module.main(["--redact", "--check-providers"])

        self.assertEqual(code, 2)
        self.assertNotIn("query_id=AAA", stdout.getvalue())
        self.assertNotIn("secret", stdout.getvalue())
        self.assertNotIn("query_id=BBB", stderr.getvalue())
        self.assertNotIn("signature=sig", stderr.getvalue())
        self.assertNotIn("hidden", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
