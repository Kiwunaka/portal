import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "remote_brain_apply_release_handoff.py"
    spec = importlib.util.spec_from_file_location("remote_brain_apply_release_handoff", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteBrainApplyReleaseHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_read_release_env_preserves_empty_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / "release-links.env"
            env_file.write_text(
                "\n".join(
                    [
                        "APP_ANDROID_PLAY_URL=",
                        "APP_ANDROID_APK_URL=https://github.com/example/release.apk",
                        "APP_ANDROID_MIRROR_URL=",
                        "APP_WINDOWS_EXE_URL=https://github.com/example/release.exe",
                        "APP_WINDOWS_MIRROR_URL=",
                        "APP_DOCS_URL=https://pokrov.space/install/",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            values = self.module._read_release_env(env_file)

        self.assertEqual(values["APP_ANDROID_PLAY_URL"], "")
        self.assertEqual(values["APP_ANDROID_APK_URL"], "https://github.com/example/release.apk")
        self.assertEqual(values["APP_WINDOWS_EXE_URL"], "https://github.com/example/release.exe")
        self.assertEqual(values["APP_DOCS_URL"], "https://pokrov.space/install/")

    def test_validate_release_env_requires_android_windows_and_docs(self) -> None:
        failures = self.module._validate_release_env(
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "",
            }
        )

        self.assertEqual(
            failures,
            [
                "android release URL is missing",
                "windows release URL is missing",
                "docs_url is missing",
            ],
        )

    def test_read_release_metadata_accepts_download_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            metadata_file = Path(td) / "release-handoff.json"
            metadata_file.write_text(
                """
                {
                  "schema_version": 1,
                  "client_lane": "bridge",
                  "release_version": "0.9.0-beta+20508",
                  "downloads": {
                    "android": {
                      "apk_url": "https://downloads.example.com/pokrov-android-arm64.apk",
                      "apk_variants": [
                        {
                          "abi": "x86_64",
                          "url": "https://downloads.example.com/pokrov-android-x86_64.apk",
                          "sha256": "cccc",
                          "size_bytes": 300
                        },
                        {
                          "abi": "universal",
                          "url": "https://downloads.example.com/pokrov-android-universal.apk",
                          "sha256": "dddd",
                          "size_bytes": 400
                        }
                      ]
                    },
                    "windows": {
                      "exe_url": "https://downloads.example.com/pokrov-windows.exe"
                    },
                    "docs_url": "https://pokrov.space/install/"
                  }
                }
                """.strip(),
                encoding="utf-8",
            )

            values = self.module._read_release_metadata(metadata_file)

        self.assertEqual(values["APP_ANDROID_APK_URL"], "https://downloads.example.com/pokrov-android-arm64.apk")
        self.assertEqual(values["APP_ANDROID_APK_X86_64_URL"], "https://downloads.example.com/pokrov-android-x86_64.apk")
        self.assertEqual(values["APP_ANDROID_X86_64_SHA256"], "cccc")
        self.assertEqual(values["APP_ANDROID_X86_64_SIZE_BYTES"], "300")
        self.assertEqual(values["APP_ANDROID_APK_UNIVERSAL_URL"], "https://downloads.example.com/pokrov-android-universal.apk")
        self.assertEqual(values["APP_ANDROID_UNIVERSAL_SHA256"], "dddd")
        self.assertEqual(values["APP_ANDROID_UNIVERSAL_SIZE_BYTES"], "400")
        self.assertEqual(values["APP_WINDOWS_EXE_URL"], "https://downloads.example.com/pokrov-windows.exe")
        self.assertEqual(values["APP_DOCS_URL"], "https://pokrov.space/install/")

    def test_read_release_metadata_projects_strict_v2_to_runtime_values(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "tests"
            / "fixtures"
            / "release-handoff"
            / "valid-v2.json"
        )

        values = self.module._read_release_metadata(fixture)

        self.assertEqual(values["APP_RELEASE_SCHEMA_VERSION"], "2")
        self.assertEqual(values["APP_RELEASE_CHANNEL"], "rc")
        self.assertEqual(values["APP_RELEASE_CANDIDATE_LABEL"], "pokrov-1.2.0-rc.1")
        self.assertEqual(
            values["APP_RELEASE_HANDOFF_SHA256"],
            hashlib.sha256(fixture.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            values["APP_RELEASE_ARTIFACT_SET_SHA256"],
            "5254bd2f7d65c16a18b6f3deb81d0470c426495866b807b21873caae541987de",
        )
        self.assertEqual(values["APP_RELEASE_CORE_VERSION"], "1.1.0")
        self.assertEqual(values["APP_RELEASE_CORE_DESKTOP_ABI"], "2")
        self.assertEqual(values["APP_RELEASE_CORE_ANDROID_PACKAGE"], "space.pokrov.core")
        self.assertEqual(values["APP_ANDROID_VERSION"], "1.2.0-rc.1")
        self.assertEqual(
            values["APP_ANDROID_APK_URL"],
            "https://github.com/Kiwunaka/pokrov/releases/download/v1.2.0-rc.1/pokrov-android-arm64-v8a.apk",
        )
        self.assertEqual(values["APP_ANDROID_SHA256"], "2" * 64)
        self.assertEqual(values["APP_ANDROID_SIZE_BYTES"], "100000000")
        self.assertEqual(
            values["APP_ANDROID_RELEASE_NOTES"],
            "POKROV 1.2.0 RC: единый проверяемый кандидат для Android и Windows.",
        )
        self.assertEqual(
            values["APP_ANDROID_RELEASE_NOTES_URL"],
            "https://github.com/Kiwunaka/pokrov/releases/tag/v1.2.0-rc.1",
        )
        self.assertEqual(values["APP_ANDROID_PUBLISHED_AT"], "2026-08-21T12:00:00Z")
        self.assertEqual(
            values["APP_WINDOWS_EXE_URL"],
            "https://github.com/Kiwunaka/pokrov/releases/download/v1.2.0-rc.1/pokrov-windows-setup-x64.exe",
        )
        self.assertEqual(values["APP_WINDOWS_SHA256"], "7" * 64)
        self.assertEqual(
            values["APP_WINDOWS_RELEASE_NOTES"],
            values["APP_ANDROID_RELEASE_NOTES"],
        )
        self.assertEqual(
            values["APP_WINDOWS_RELEASE_NOTES_URL"],
            values["APP_ANDROID_RELEASE_NOTES_URL"],
        )
        self.assertEqual(values["APP_WINDOWS_PUBLISHED_AT"], "2026-08-21T12:00:00Z")
        self.assertEqual(values["APP_DOCS_URL"], "https://pokrov.space/install/")

    def test_read_release_metadata_rejects_invalid_strict_v2_before_projection(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "tests"
            / "fixtures"
            / "release-handoff"
            / "valid-v2.json"
        )
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        payload["sources"]["core"]["revision"] = "not-a-revision"
        with tempfile.TemporaryDirectory() as td:
            metadata_file = Path(td) / "release-handoff.json"
            metadata_file.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "Invalid strict release-handoff v2 metadata"):
                self.module._read_release_metadata(metadata_file)

    def test_resolve_release_values_prefers_metadata_before_legacy_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            metadata_file = Path(td) / "release-handoff.json"
            env_file = Path(td) / "release-links.env"
            metadata_file.write_text(
                """
                {
                  "runtime_env": {
                    "APP_ANDROID_APK_URL": "https://metadata.example.com/pokrov-android.apk",
                    "APP_ANDROID_MIN_SUPPORTED_VERSION": "1.1.0",
                    "APP_ANDROID_RELEASE_NOTES": "Android release notes",
                    "APP_ANDROID_RELEASE_NOTES_URL": "https://metadata.example.com/android-notes",
                    "APP_ANDROID_PUBLISHED_AT": "2026-08-14T05:56:25Z",
                    "APP_WINDOWS_EXE_URL": "https://metadata.example.com/pokrov-windows.exe",
                    "APP_WINDOWS_MIN_SUPPORTED_VERSION": "1.1.0",
                    "APP_WINDOWS_RELEASE_NOTES": "Windows release notes",
                    "APP_WINDOWS_RELEASE_NOTES_URL": "https://metadata.example.com/windows-notes",
                    "APP_WINDOWS_PUBLISHED_AT": "2026-08-14T05:56:25Z",
                    "APP_DOCS_URL": "https://pokrov.space/install/"
                  }
                }
                """.strip(),
                encoding="utf-8",
            )
            env_file.write_text(
                "\n".join(
                    [
                        "APP_ANDROID_APK_URL=https://env.example.com/pokrov-android.apk",
                        "APP_WINDOWS_EXE_URL=https://env.example.com/pokrov-windows.exe",
                        "APP_DOCS_URL=https://pokrov.space/install/",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            values, source = self.module._resolve_release_values(str(metadata_file), str(env_file))

        self.assertEqual(values["APP_ANDROID_APK_URL"], "https://metadata.example.com/pokrov-android.apk")
        self.assertEqual(values["APP_ANDROID_MIN_SUPPORTED_VERSION"], "1.1.0")
        self.assertEqual(values["APP_ANDROID_RELEASE_NOTES"], "Android release notes")
        self.assertEqual(values["APP_ANDROID_PUBLISHED_AT"], "2026-08-14T05:56:25Z")
        self.assertEqual(values["APP_WINDOWS_RELEASE_NOTES"], "Windows release notes")
        self.assertEqual(values["APP_WINDOWS_MIN_SUPPORTED_VERSION"], "1.1.0")
        self.assertEqual(values["APP_WINDOWS_PUBLISHED_AT"], "2026-08-14T05:56:25Z")
        self.assertEqual(source, metadata_file)

    def test_rewrite_env_updates_existing_release_keys_and_adds_missing_ones(self) -> None:
        original = "\n".join(
            [
                "EXISTING=1",
                "APP_ANDROID_APK_URL=https://old.example/apk",
                "APP_WINDOWS_EXE_URL=https://old.example/exe",
                "",
            ]
        )
        updated = self.module._rewrite_env(
            original,
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "https://new.example/apk",
                "APP_ANDROID_MIN_SUPPORTED_VERSION": "1.1.0",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://new.example/exe",
                "APP_WINDOWS_MIN_SUPPORTED_VERSION": "1.1.0",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            },
        )

        self.assertIn("EXISTING=1", updated)
        self.assertIn("APP_ANDROID_APK_URL=https://new.example/apk", updated)
        self.assertIn("APP_ANDROID_MIN_SUPPORTED_VERSION=1.1.0", updated)
        self.assertIn("APP_WINDOWS_EXE_URL=https://new.example/exe", updated)
        self.assertIn("APP_WINDOWS_MIN_SUPPORTED_VERSION=1.1.0", updated)
        self.assertIn("APP_DOCS_URL=https://pokrov.space/install/", updated)
        self.assertEqual(updated.count("APP_ANDROID_APK_URL="), 1)

    def test_release_values_preview_includes_runtime_download_keys(self) -> None:
        preview = self.module._release_values_preview(
            {
                "APP_ANDROID_APK_URL": "https://github.com/example/release.apk",
                "APP_ANDROID_APK_ARM64_URL": "https://github.com/example/release-arm64.apk",
                "APP_WINDOWS_EXE_URL": "https://github.com/example/release.exe",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            }
        )

        self.assertIn("APP_ANDROID_APK_URL=https://github.com/example/release.apk", preview)
        self.assertIn("APP_ANDROID_APK_ARM64_URL=https://github.com/example/release-arm64.apk", preview)
        self.assertIn("APP_WINDOWS_EXE_URL=https://github.com/example/release.exe", preview)
        self.assertIn("APP_DOCS_URL=https://pokrov.space/install/", preview)
        self.assertIn("APP_ANDROID_PLAY_URL=", preview)


if __name__ == "__main__":
    unittest.main()
