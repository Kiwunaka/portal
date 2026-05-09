import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "prepare_github_release_plan.py"
    spec = importlib.util.spec_from_file_location("prepare_github_release_plan", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrepareGithubReleasePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_build_plan_outputs_prerelease_command_and_handoff_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-universal.apk"
            exe = root / "pokrov-windows-setup-x64.exe"
            notes = root / "notes.md"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")
            apk_sha256 = self.module._sha256(apk)

            plan = self.module._build_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=apk,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
            )

        command = plan["gh_command"]

        self.assertEqual(command[:3], ["gh", "release", "create"])
        self.assertNotIn("--draft", command)
        self.assertIn("--prerelease", command)
        self.assertIn("pokrov-android-universal.apk", command[4])
        self.assertIn("pokrov-windows-setup-x64.exe", command[5])
        self.assertIn(str(apk), "\n".join(plan["staging"]["commands"]))
        self.assertIn(str(exe), "\n".join(plan["staging"]["commands"]))
        self.assertEqual(plan["expected_urls"]["APP_ANDROID_PLAY_URL"], "")
        self.assertEqual(
            plan["expected_urls"]["APP_ANDROID_APK_URL"],
            "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
        )
        self.assertEqual(
            plan["expected_urls"]["APP_WINDOWS_EXE_URL"],
            "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
        )
        self.assertEqual(plan["expected_urls"]["APP_DOCS_URL"], "https://pokrov.space/install/")
        self.assertEqual(plan["artifacts"][0]["sha256"], apk_sha256)
        self.assertEqual(plan["artifacts"][0]["filename"], "pokrov-android-universal.apk")
        self.assertEqual(plan["artifacts"][0]["source_filename"], "pokrov-android-universal.apk")

    def test_build_plan_stages_raw_build_names_to_canonical_asset_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "app-release.apk"
            exe = root / "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe"
            notes = root / "notes.md"
            stage_dir = root / "stage"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")

            plan = self.module._build_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=apk,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
                stage_dir=stage_dir,
            )

        self.assertEqual(plan["artifacts"][0]["source_filename"], "app-release.apk")
        self.assertEqual(plan["artifacts"][0]["filename"], "pokrov-android-universal.apk")
        self.assertEqual(plan["artifacts"][0]["path"], str(stage_dir / "pokrov-android-universal.apk"))
        self.assertEqual(plan["artifacts"][1]["source_filename"], "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe")
        self.assertEqual(plan["artifacts"][1]["filename"], "pokrov-windows-setup-x64.exe")
        self.assertIn("pokrov-android-universal.apk", plan["expected_urls"]["APP_ANDROID_APK_URL"])
        self.assertNotIn("app-release.apk", plan["expected_urls"]["APP_ANDROID_APK_URL"])

    def test_build_plan_rejects_non_beta_tag_and_wrong_artifact_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-universal.zip"
            exe = root / "pokrov-windows-setup-x64.txt"
            notes = root / "notes.md"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")

            failures = self.module._plan_failures(
                repo="Kiwunaka/POKROV-app",
                tag="v1.0.0",
                android_apk=apk,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
            )

        self.assertIn("tag must be a 0.x.x beta tag, for example v0.2.0-beta.1", failures)
        self.assertIn(f"Android APK must have .apk extension: {apk}", failures)
        self.assertIn(f"Windows EXE must have .exe extension: {exe}", failures)

    def test_build_plan_rejects_non_install_docs_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-universal.apk"
            exe = root / "pokrov-windows-setup-x64.exe"
            notes = root / "notes.md"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")

            failures = self.module._plan_failures(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                android_apk=apk,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://github.com/Kiwunaka/POKROV-app",
            )

        self.assertEqual(["APP_DOCS_URL must stay under https://pokrov.space/install/"], failures)

    def test_build_plan_rejects_handoff_sha_mismatch_for_same_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "app-release.apk"
            exe = root / "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe"
            notes = root / "notes.md"
            handoff = root / "release-handoff.json"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"new-exe")
            notes.write_text("release notes", encoding="utf-8")
            handoff.write_text(
                """{
  "github_release": {"tag": "v0.2.0-beta.1"},
  "downloads": {
    "android": {"sha256": "%s"},
    "windows": {"sha256": "0000000000000000000000000000000000000000000000000000000000000000"}
  }
}
"""
                % self.module._sha256(apk),
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit) as raised:
                self.module._build_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=apk,
                    windows_exe=exe,
                    notes_file=notes,
                    docs_url="https://pokrov.space/install/",
                    release_handoff=handoff,
                )

        message = str(raised.exception)
        self.assertIn("Windows EXE SHA256 does not match release handoff", message)
        self.assertIn("0000000000000000000000000000000000000000000000000000000000000000", message)

    def test_build_plan_reports_missing_github_cli_without_failing_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-universal.apk"
            exe = root / "pokrov-windows-setup-x64.exe"
            notes = root / "notes.md"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")

            plan = self.module._build_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=apk,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
                gh_path="",
            )

        self.assertEqual(False, plan["tooling"]["gh"]["available"])
        self.assertEqual("BLOCKED_TOOL_MISSING", plan["tooling"]["gh"]["classification"])
        self.assertIn("Install GitHub CLI", plan["tooling"]["gh"]["next_action"])
        self.assertEqual(plan["gh_command"][0], "gh")


if __name__ == "__main__":
    unittest.main()
