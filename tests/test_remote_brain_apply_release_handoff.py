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

    def test_validate_release_env_accepts_github_artifacts_and_install_docs(self) -> None:
        failures = self.module._validate_release_env(
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            }
        )

        self.assertEqual(failures, [])

    def test_validate_release_env_rejects_malformed_or_wrong_role_urls(self) -> None:
        failures = self.module._validate_release_env(
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "javascript:alert(1)",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://connect.pokrov.space/pokrov.exe",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pay.pokrov.space/checkout/",
            }
        )

        joined = "\n".join(failures)
        self.assertIn("APP_ANDROID_APK_URL must be an https URL", joined)
        self.assertIn("APP_WINDOWS_EXE_URL must point to a GitHub Releases .exe artifact", joined)
        self.assertIn("APP_DOCS_URL must point to https://pokrov.space/install/", joined)

    def test_validate_release_env_rejects_wrong_artifact_extensions(self) -> None:
        failures = self.module._validate_release_env(
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.zip",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.msix",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            }
        )

        joined = "\n".join(failures)
        self.assertIn("APP_ANDROID_APK_URL must point to a GitHub Releases .apk artifact", joined)
        self.assertIn("APP_WINDOWS_EXE_URL must point to a GitHub Releases .exe artifact", joined)

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

    def test_read_release_metadata_accepts_staged_client_apps_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            metadata_file = Path(td) / "staged-client-apps.json"
            metadata_file.write_text(
                """
                {
                  "android": {
                    "play_url": "",
                    "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
                    "mirror_url": ""
                  },
                  "windows": {
                    "exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
                    "mirror_url": ""
                  },
                  "docs_url": "https://pokrov.space/install/"
                }
                """.strip(),
                encoding="utf-8",
            )

            values = self.module._read_release_metadata(metadata_file)

        self.assertEqual(
            values["APP_ANDROID_APK_URL"],
            "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
        )
        self.assertEqual(
            values["APP_WINDOWS_EXE_URL"],
            "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
        )
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

    def test_dry_run_report_contains_release_values_without_mutation_claim(self) -> None:
        report = self.module._dry_run_report(
            {
                "APP_ANDROID_PLAY_URL": "",
                "APP_ANDROID_APK_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
                "APP_ANDROID_MIRROR_URL": "",
                "APP_WINDOWS_EXE_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
                "APP_WINDOWS_MIRROR_URL": "",
                "APP_DOCS_URL": "https://pokrov.space/install/",
            },
            Path("release-handoff.json"),
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["mode"], "remote_brain_apply_release_handoff_dry_run")
        self.assertIn("no SSH connection", str(report["note"]))
        self.assertEqual(
            report["values"]["APP_ANDROID_APK_URL"],
            "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
        )

    def test_runtime_sync_evidence_rejects_missing_or_plain_no_go(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            no_go = Path(td) / "handoff.md"
            no_go.write_text("NO-GO for public beta publication.\n", encoding="utf-8")

            self.assertIn(
                "required",
                self.module._release_handoff_evidence_failure(None),
            )
            self.assertIn(
                "NO-GO",
                self.module._release_handoff_evidence_failure(no_go),
            )

    def test_runtime_sync_evidence_accepts_public_go_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            go = Path(td) / "handoff.md"
            go.write_text("GO for public beta publication.\n", encoding="utf-8")

            self.assertEqual(self.module._release_handoff_evidence_failure(go), "")

    def test_runtime_sync_evidence_rejects_public_go_with_mixed_case_no_go(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            go = Path(td) / "handoff.md"
            go.write_text(
                "\n".join(
                    [
                        "GO for public beta publication",
                        "No-Go for payment launch.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn("NO-GO", self.module._release_handoff_evidence_failure(go))

    def test_runtime_sync_evidence_accepts_narrow_sync_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-sync.md"
            evidence.write_text(
                "\n".join(
                    [
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(self.module._release_handoff_evidence_failure(evidence), "")

    def test_runtime_sync_evidence_rejects_narrow_sync_with_no_go_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-sync.md"
            evidence.write_text(
                "\n".join(
                    [
                        "NO-GO for public beta publication.",
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn("NO-GO", self.module._release_handoff_evidence_failure(evidence))

    def test_runtime_sync_evidence_rejects_marker_examples_inside_fenced_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runbook.md"
            evidence.write_text(
                "\n".join(
                    [
                        "Operator runbook example:",
                        "",
                        "```text",
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                        "```",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn(
                "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                self.module._release_handoff_evidence_failure(evidence),
            )

    def test_runtime_sync_evidence_rejects_artifact_staging_no_runtime_sync_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-sync.md"
            evidence.write_text(
                "\n".join(
                    [
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                        "NO RUNTIME SYNC OR ANNOUNCEMENT",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn("NO RUNTIME SYNC", self.module._release_handoff_evidence_failure(evidence))

    def test_runtime_sync_evidence_requires_explicit_operator_approval_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-sync.md"
            evidence.write_text(
                "\n".join(
                    [
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn(
                "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                self.module._release_handoff_evidence_failure(evidence),
            )

    def test_runtime_sync_guard_evidence_is_not_accepted_as_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-link-sync-guard.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Runtime Link Sync Guard Evidence",
                        "",
                        "- Decision: `NO RUNTIME SYNC`",
                        "- Classification: `BLOCKED_BY_ACCESS`",
                        "",
                        "Runtime sync may only proceed after a dated evidence file explicitly contains:",
                        "",
                        "- `RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE`",
                        "- `OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true`",
                        "- `STAGED GITHUB ASSET REACHABILITY GREEN`",
                        "- `NO PUBLIC ANNOUNCEMENT`",
                        "- `PAID CHECKOUT REMAINS CLOSED`",
                        "",
                        "The evidence file must not contain:",
                        "",
                        "- `NO RUNTIME SYNC OR ANNOUNCEMENT`",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn("NO RUNTIME SYNC", self.module._release_handoff_evidence_failure(evidence))

    def test_no_runtime_sync_decision_rejects_marker_list_without_blocking_footer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "runtime-link-sync-guard.md"
            evidence.write_text(
                "\n".join(
                    [
                        "- Decision: `NO RUNTIME SYNC`",
                        "- Classification: `BLOCKED_BY_ACCESS`",
                        "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE",
                        "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true",
                        "STAGED GITHUB ASSET REACHABILITY GREEN",
                        "NO PUBLIC ANNOUNCEMENT",
                        "PAID CHECKOUT REMAINS CLOSED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertIn("NO RUNTIME SYNC", self.module._release_handoff_evidence_failure(evidence))


if __name__ == "__main__":
    unittest.main()
