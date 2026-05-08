import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "publish_github_release_assets.py"
    spec = importlib.util.spec_from_file_location("publish_github_release_assets", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sample_inputs(root: Path) -> dict[str, Path]:
    apk = root / "app-release.apk"
    exe = root / "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe"
    notes = root / "notes.md"
    go = root / "handoff.md"
    apk.write_bytes(b"apk")
    exe.write_bytes(b"exe")
    notes.write_text("release notes", encoding="utf-8")
    return {"apk": apk, "exe": exe, "notes": notes, "go": go}


class _FakeGithubApi:
    def __init__(self) -> None:
        self.created_release_payloads: list[dict[str, object]] = []
        self.uploads: list[dict[str, object]] = []

    def create_release(self, *, repo: str, token: str, payload: dict[str, object]) -> dict[str, object]:
        self.created_release_payloads.append({"repo": repo, "token": token, "payload": payload})
        return {
            "id": 123,
            "html_url": f"https://github.com/{repo}/releases/tag/{payload['tag_name']}",
            "upload_url": f"https://uploads.github.com/repos/{repo}/releases/123/assets{{?name,label}}",
        }

    def upload_asset(
        self,
        *,
        upload_url: str,
        token: str,
        name: str,
        path: Path,
        content_type: str,
    ) -> dict[str, object]:
        self.uploads.append(
            {
                "upload_url": upload_url,
                "token": token,
                "name": name,
                "path": str(path),
                "content_type": content_type,
            }
        )
        return {
            "name": name,
            "browser_download_url": f"https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/{name}",
        }


class _FakeGithubCli:
    def __init__(self) -> None:
        self.created_release_payloads: list[dict[str, object]] = []

    def create_release(
        self,
        *,
        repo: str,
        tag: str,
        title: str,
        notes_file: Path,
        asset_paths: list[Path],
    ) -> dict[str, object]:
        self.created_release_payloads.append(
            {
                "repo": repo,
                "tag": tag,
                "title": title,
                "notes_file": str(notes_file),
                "asset_names": [path.name for path in asset_paths],
            }
        )
        return {
            "release_id": 456,
            "release_url": f"https://github.com/{repo}/releases/tag/{tag}",
            "uploaded_assets": [
                {
                    "name": path.name,
                    "browser_download_url": f"https://github.com/{repo}/releases/download/{tag}/{path.name}",
                    "size_bytes": path.stat().st_size,
                }
                for path in asset_paths
            ],
        }


class PublishGithubReleaseAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_dry_run_plan_uses_canonical_asset_names_without_token_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))

            plan = self.module.build_publish_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=paths["apk"],
                windows_exe=paths["exe"],
                notes_file=paths["notes"],
                docs_url="https://pokrov.space/install/",
                execute=False,
                go_evidence_file=None,
                env={},
            )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["classification"], "DRY_RUN")
        self.assertEqual(plan["token"]["present"], False)
        self.assertEqual(plan["release_auth"]["ready"], False)
        self.assertEqual([asset["upload_name"] for asset in plan["assets"]], ["pokrov-android-universal.apk", "pokrov-windows-setup-x64.exe"])
        self.assertIn("GitHub CLI", "\n".join(plan["execute_requirements"]))
        self.assertIn("GITHUB_TOKEN", "\n".join(plan["execute_requirements"]))
        self.assertEqual(plan["expected_urls"]["APP_ANDROID_PLAY_URL"], "")

    def test_execute_rejects_current_no_go_handoff_before_uploading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text("NO-GO for public beta publication.", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                self.module.build_publish_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=paths["apk"],
                    windows_exe=paths["exe"],
                    notes_file=paths["notes"],
                    docs_url="https://pokrov.space/install/",
                    execute=True,
                    go_evidence_file=paths["go"],
                    env={"GITHUB_TOKEN": "secret-token"},
                )

        message = str(raised.exception)
        self.assertIn("GO evidence file is not a public-beta GO handoff", message)
        self.assertNotIn("secret-token", message)

    def test_execute_requires_release_auth_without_printing_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text("GO for public beta publication.", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                self.module.build_publish_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=paths["apk"],
                    windows_exe=paths["exe"],
                    notes_file=paths["notes"],
                    docs_url="https://pokrov.space/install/",
                    execute=True,
                    go_evidence_file=paths["go"],
                    env={},
                    gh_authenticated=False,
                )

        self.assertIn("GitHub release auth", str(raised.exception))

    def test_execute_accepts_explicit_artifact_staging_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text(
                "NO-GO for public beta publication.\n"
                "ARTIFACT STAGING GO FOR RUNTIME SMOKE\n"
                "NON-URL P0 GATES GREEN FOR ARTIFACT STAGING\n"
                "ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE\n"
                "NO RUNTIME SYNC OR ANNOUNCEMENT\n",
                encoding="utf-8",
            )

            plan = self.module.build_publish_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=paths["apk"],
                windows_exe=paths["exe"],
                notes_file=paths["notes"],
                docs_url="https://pokrov.space/install/",
                execute=True,
                go_evidence_file=paths["go"],
                env={"GITHUB_TOKEN": "secret-token"},
            )

        self.assertEqual(plan["mode"], "execute")
        self.assertFalse(plan["draft"])
        self.assertIn("ARTIFACT STAGING GO FOR RUNTIME SMOKE", "\n".join(plan["execute_requirements"]))
        self.assertIn("NON-URL P0 GATES GREEN FOR ARTIFACT STAGING", "\n".join(plan["execute_requirements"]))
        self.assertIn("ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE", "\n".join(plan["execute_requirements"]))

    def test_artifact_staging_authorization_requires_non_url_p0_green_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text(
                "NO-GO for public beta publication.\n"
                "ARTIFACT STAGING GO FOR RUNTIME SMOKE\n"
                "NO RUNTIME SYNC OR ANNOUNCEMENT\n",
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit) as raised:
                self.module.build_publish_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=paths["apk"],
                    windows_exe=paths["exe"],
                    notes_file=paths["notes"],
                    docs_url="https://pokrov.space/install/",
                    execute=True,
                    go_evidence_file=paths["go"],
                    env={"GITHUB_TOKEN": "secret-token"},
                )

        self.assertIn("NON-URL P0 GATES GREEN FOR ARTIFACT STAGING", str(raised.exception))

    def test_artifact_staging_authorization_rejects_unresolved_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text(
                "NO-GO for public beta publication.\n"
                "ARTIFACT STAGING GO FOR RUNTIME SMOKE\n"
                "NON-URL P0 GATES GREEN FOR ARTIFACT STAGING\n"
                "ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE\n"
                "NO RUNTIME SYNC OR ANNOUNCEMENT\n"
                "Lava.top checkout evidence: POST_DEPLOY_ONLY_BLOCKED_BY_ACCESS\n",
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit) as raised:
                self.module.build_publish_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=paths["apk"],
                    windows_exe=paths["exe"],
                    notes_file=paths["notes"],
                    docs_url="https://pokrov.space/install/",
                    execute=True,
                    go_evidence_file=paths["go"],
                    env={"GITHUB_TOKEN": "secret-token"},
                )

        self.assertIn("BLOCKED_BY_ACCESS", str(raised.exception))

    def test_artifact_staging_authorization_requires_no_runtime_sync_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text("ARTIFACT STAGING GO FOR RUNTIME SMOKE\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                self.module.build_publish_plan(
                    repo="Kiwunaka/POKROV-app",
                    tag="v0.2.0-beta.1",
                    title="POKROV 0.2.0-beta.1",
                    android_apk=paths["apk"],
                    windows_exe=paths["exe"],
                    notes_file=paths["notes"],
                    docs_url="https://pokrov.space/install/",
                    execute=True,
                    go_evidence_file=paths["go"],
                    env={"GITHUB_TOKEN": "secret-token"},
                )

        self.assertIn("NO RUNTIME SYNC OR ANNOUNCEMENT", str(raised.exception))

    def test_execute_create_release_and_uploads_canonical_assets(self) -> None:
        fake_api = _FakeGithubApi()
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text("GO for public beta publication.", encoding="utf-8")
            plan = self.module.build_publish_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=paths["apk"],
                windows_exe=paths["exe"],
                notes_file=paths["notes"],
                docs_url="https://pokrov.space/install/",
                execute=True,
                go_evidence_file=paths["go"],
                env={"GITHUB_TOKEN": "secret-token"},
            )

            result = self.module.publish_from_plan(plan, token="secret-token", github_api=fake_api)

        self.assertEqual(fake_api.created_release_payloads[0]["payload"]["draft"], False)
        self.assertEqual(fake_api.created_release_payloads[0]["payload"]["prerelease"], True)
        self.assertEqual(fake_api.created_release_payloads[0]["payload"]["body"], "release notes")
        self.assertEqual([upload["name"] for upload in fake_api.uploads], ["pokrov-android-universal.apk", "pokrov-windows-setup-x64.exe"])
        self.assertEqual([asset["name"] for asset in result["uploaded_assets"]], ["pokrov-android-universal.apk", "pokrov-windows-setup-x64.exe"])
        self.assertNotIn("app-release.apk", "\n".join(asset["browser_download_url"] for asset in result["uploaded_assets"]))
        self.assertEqual(result["publish_method"], "github_rest")

    def test_execute_can_publish_with_authenticated_gh_cli_without_token(self) -> None:
        fake_cli = _FakeGithubCli()
        with tempfile.TemporaryDirectory() as temp_root:
            paths = _sample_inputs(Path(temp_root))
            paths["go"].write_text("GO for public beta publication.", encoding="utf-8")
            plan = self.module.build_publish_plan(
                repo="Kiwunaka/POKROV-app",
                tag="v0.2.0-beta.1",
                title="POKROV 0.2.0-beta.1",
                android_apk=paths["apk"],
                windows_exe=paths["exe"],
                notes_file=paths["notes"],
                docs_url="https://pokrov.space/install/",
                execute=True,
                go_evidence_file=paths["go"],
                env={},
                gh_authenticated=True,
            )

            result = self.module.publish_from_plan(plan, token="", github_cli=fake_cli)

        self.assertEqual(plan["token"]["present"], False)
        self.assertEqual(plan["github_cli"]["authenticated"], True)
        self.assertEqual(plan["release_auth"]["methods"], ["gh_cli_keyring"])
        self.assertEqual(fake_cli.created_release_payloads[0]["asset_names"], ["pokrov-android-universal.apk", "pokrov-windows-setup-x64.exe"])
        self.assertEqual([asset["name"] for asset in result["uploaded_assets"]], ["pokrov-android-universal.apk", "pokrov-windows-setup-x64.exe"])
        self.assertEqual(result["publish_method"], "gh_cli")


if __name__ == "__main__":
    unittest.main()
