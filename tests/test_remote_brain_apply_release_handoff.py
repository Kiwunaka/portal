import importlib.util
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
                      "apk_url": "https://downloads.example.com/pokrov-android.apk"
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

        self.assertEqual(values["APP_ANDROID_APK_URL"], "https://downloads.example.com/pokrov-android.apk")
        self.assertEqual(values["APP_WINDOWS_EXE_URL"], "https://downloads.example.com/pokrov-windows.exe")
        self.assertEqual(values["APP_DOCS_URL"], "https://pokrov.space/install/")

    def test_resolve_release_values_prefers_metadata_before_legacy_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            metadata_file = Path(td) / "release-handoff.json"
            env_file = Path(td) / "release-links.env"
            metadata_file.write_text(
                """
                {
                  "runtime_env": {
                    "APP_ANDROID_APK_URL": "https://metadata.example.com/pokrov-android.apk",
                    "APP_WINDOWS_EXE_URL": "https://metadata.example.com/pokrov-windows.exe",
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
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://new.example/exe",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            },
        )

        self.assertIn("EXISTING=1", updated)
        self.assertIn("APP_ANDROID_APK_URL=https://new.example/apk", updated)
        self.assertIn("APP_WINDOWS_EXE_URL=https://new.example/exe", updated)
        self.assertIn("APP_DOCS_URL=https://pokrov.space/install/", updated)
        self.assertEqual(updated.count("APP_ANDROID_APK_URL="), 1)

    def test_release_values_preview_includes_runtime_download_keys(self) -> None:
        preview = self.module._release_values_preview(
            {
                "APP_ANDROID_APK_URL": "https://github.com/example/release.apk",
                "APP_WINDOWS_EXE_URL": "https://github.com/example/release.exe",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            }
        )

        self.assertIn("APP_ANDROID_APK_URL=https://github.com/example/release.apk", preview)
        self.assertIn("APP_WINDOWS_EXE_URL=https://github.com/example/release.exe", preview)
        self.assertIn("APP_DOCS_URL=https://pokrov.space/install/", preview)
        self.assertIn("APP_ANDROID_PLAY_URL=", preview)


if __name__ == "__main__":
    unittest.main()
