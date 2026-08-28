import importlib.util
import json
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
            apk = root / "pokrov-android-arm64-v8a.apk"
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
        self.assertIn("pokrov-android-arm64-v8a.apk", command[4])
        self.assertIn("pokrov-windows-setup-x64.exe", command[5])
        self.assertIn(str(apk), "\n".join(plan["staging"]["commands"]))
        self.assertIn(str(exe), "\n".join(plan["staging"]["commands"]))
        self.assertEqual(plan["expected_urls"]["APP_ANDROID_PLAY_URL"], "")
        self.assertEqual(
            plan["expected_urls"]["APP_ANDROID_APK_URL"],
            "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-arm64-v8a.apk",
        )
        self.assertEqual(
            plan["expected_urls"]["APP_WINDOWS_EXE_URL"],
            "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
        )
        self.assertEqual(plan["expected_urls"]["APP_DOCS_URL"], "https://pokrov.space/install/")
        self.assertEqual(plan["artifacts"][0]["sha256"], apk_sha256)
        self.assertEqual(plan["artifacts"][0]["filename"], "pokrov-android-arm64-v8a.apk")
        self.assertEqual(plan["artifacts"][0]["source_filename"], "pokrov-android-arm64-v8a.apk")

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
        self.assertEqual(plan["artifacts"][0]["filename"], "pokrov-android-arm64-v8a.apk")
        self.assertEqual(plan["artifacts"][0]["path"], str(stage_dir / "pokrov-android-arm64-v8a.apk"))
        self.assertEqual(plan["artifacts"][1]["source_filename"], "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe")
        self.assertEqual(plan["artifacts"][1]["filename"], "pokrov-windows-setup-x64.exe")
        self.assertIn("pokrov-android-arm64-v8a.apk", plan["expected_urls"]["APP_ANDROID_APK_URL"])
        self.assertNotIn("app-release.apk", plan["expected_urls"]["APP_ANDROID_APK_URL"])

    def test_build_plan_includes_all_android_splits_and_accepts_current_v1_prerelease_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            arm64 = root / "app-arm64-v8a-release.apk"
            armv7 = root / "app-armeabi-v7a-release.apk"
            x86_64 = root / "app-x86_64-release.apk"
            universal = root / "app-release.apk"
            exe = root / "pokrov-windows-setup-x64.exe"
            notes = root / "notes.md"
            for path, payload in (
                (arm64, b"arm64"),
                (armv7, b"armv7"),
                (x86_64, b"x86_64"),
                (universal, b"universal"),
                (exe, b"exe"),
            ):
                path.write_bytes(payload)
            notes.write_text("release notes", encoding="utf-8")

            plan = self.module._build_plan(
                repo="Kiwunaka/pokrov",
                tag="v1.0.3-beta.1",
                title="POKROV 1.0.3-beta.1",
                android_apk=arm64,
                android_armeabi_v7a_apk=armv7,
                android_x86_64_apk=x86_64,
                android_universal_apk=universal,
                windows_exe=exe,
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
            )

        self.assertEqual(
            [item["filename"] for item in plan["artifacts"]],
            [
                "pokrov-android-arm64-v8a.apk",
                "pokrov-android-armeabi-v7a.apk",
                "pokrov-android-x86_64.apk",
                "pokrov-android-universal.apk",
                "pokrov-windows-setup-x64.exe",
            ],
        )
        self.assertTrue(plan["expected_urls"]["APP_ANDROID_APK_URL"].endswith("pokrov-android-arm64-v8a.apk"))
        self.assertTrue(plan["expected_urls"]["APP_ANDROID_APK_UNIVERSAL_URL"].endswith("pokrov-android-universal.apk"))
        self.assertEqual(len(plan["gh_command"][4:9]), 5)

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

        self.assertIn("tag must be a beta/rc prerelease tag, for example v1.0.3-beta.1", failures)
        self.assertIn(f"Android APK must have .apk extension: {apk}", failures)
        self.assertIn(f"Windows EXE must have .exe extension: {exe}", failures)

    def test_build_plan_rejects_non_install_docs_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-arm64-v8a.apk"
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

    def test_build_plan_accepts_exact_strict_v2_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            sources = {
                ("android", "apk", "arm64-v8a"): root / "arm64.apk",
                ("android", "apk", "armeabi-v7a"): root / "armv7.apk",
                ("android", "apk", "x86_64"): root / "x86.apk",
                ("android", "apk", "universal"): root / "universal.apk",
                ("windows", "exe", "x64"): root / "setup.exe",
            }
            canonical_names = {
                ("android", "apk", "arm64-v8a"): "pokrov-android-arm64-v8a.apk",
                ("android", "apk", "armeabi-v7a"): "pokrov-android-armeabi-v7a.apk",
                ("android", "apk", "x86_64"): "pokrov-android-x86_64.apk",
                ("android", "apk", "universal"): "pokrov-android-universal.apk",
                ("windows", "exe", "x64"): "pokrov-windows-setup-x64.exe",
            }
            for index, source in enumerate(sources.values()):
                source.write_bytes(f"artifact-{index}".encode())
            notes = root / "notes.md"
            notes.write_text("release notes", encoding="utf-8")
            tag = "v1.2.0-beta.4046"
            handoff = root / "release-handoff-v2.json"
            handoff.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "release": {"version": "1.2.0"},
                        "artifacts": [
                            {
                                "platform": key[0],
                                "kind": key[1],
                                "architecture": key[2],
                                "file_name": canonical_names[key],
                                "public_url": (
                                    f"https://github.com/Kiwunaka/pokrov/releases/download/"
                                    f"{tag}/{canonical_names[key]}"
                                ),
                                "sha256": self.module._sha256(source),
                                "size_bytes": source.stat().st_size,
                            }
                            for key, source in sources.items()
                        ],
                    }
                ),
                encoding="utf-8",
            )

            plan = self.module._build_plan(
                repo="Kiwunaka/pokrov",
                tag=tag,
                title="POKROV 1.2.0-beta.4046",
                android_apk=sources[("android", "apk", "arm64-v8a")],
                android_armeabi_v7a_apk=sources[("android", "apk", "armeabi-v7a")],
                android_x86_64_apk=sources[("android", "apk", "x86_64")],
                android_universal_apk=sources[("android", "apk", "universal")],
                windows_exe=sources[("windows", "exe", "x64")],
                notes_file=notes,
                docs_url="https://pokrov.space/install/",
                release_handoff=handoff,
            )

        self.assertEqual(5, len(plan["artifacts"]))

    def test_build_plan_rejects_strict_v2_hash_and_public_url_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "arm64.apk"
            exe = root / "setup.exe"
            notes = root / "notes.md"
            handoff = root / "release-handoff-v2.json"
            apk.write_bytes(b"apk")
            exe.write_bytes(b"exe")
            notes.write_text("release notes", encoding="utf-8")
            handoff.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "release": {"version": "1.2.0"},
                        "artifacts": [
                            {
                                "platform": "android",
                                "kind": "apk",
                                "architecture": "arm64-v8a",
                                "file_name": "pokrov-android-arm64-v8a.apk",
                                "public_url": (
                                    "https://github.com/Kiwunaka/pokrov/releases/download/"
                                    "v1.2.0/pokrov-android-arm64-v8a.apk"
                                ),
                                "sha256": "0" * 64,
                                "size_bytes": apk.stat().st_size,
                            },
                            {
                                "platform": "windows",
                                "kind": "exe",
                                "architecture": "x64",
                                "file_name": "pokrov-windows-setup-x64.exe",
                                "public_url": (
                                    "https://github.com/Kiwunaka/pokrov/releases/download/"
                                    "v1.2.0-beta.4046/pokrov-windows-setup-x64.exe"
                                ),
                                "sha256": self.module._sha256(exe),
                                "size_bytes": exe.stat().st_size,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit) as raised:
                self.module._build_plan(
                    repo="Kiwunaka/pokrov",
                    tag="v1.2.0-beta.4046",
                    title="POKROV 1.2.0-beta.4046",
                    android_apk=apk,
                    windows_exe=exe,
                    notes_file=notes,
                    docs_url="https://pokrov.space/install/",
                    release_handoff=handoff,
                )

        message = str(raised.exception)
        self.assertIn("Android arm64-v8a APK SHA256 does not match strict-v2", message)
        self.assertIn("Android arm64-v8a APK public URL does not match planned tag", message)

    def test_build_plan_reports_missing_github_cli_without_failing_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            apk = root / "pokrov-android-arm64-v8a.apk"
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
