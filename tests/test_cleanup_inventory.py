import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "cleanup_inventory.py"
    spec = importlib.util.spec_from_file_location("cleanup_inventory", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CleanupInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_inventory_matches_safe_generated_junk_and_preserves_protected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".tmp-run").mkdir()
            (root / ".tmp-local.log").write_text("log", encoding="utf-8")
            (root / "portal_api_test_fixture.db").write_text("", encoding="utf-8")
            (root / "portal_api_test_fixture.db-journal").write_text("", encoding="utf-8")
            (root / "docs" / "audit-artifacts" / "__pycache__").mkdir(parents=True)
            (root / "external" / "client-fork" / "app" / "out" / "__pycache__").mkdir(parents=True)
            (root / "external" / "client-fork" / "app" / ".dart_tool").mkdir(parents=True)
            (root / "external" / "client-fork" / "app" / "build").mkdir(parents=True)
            (root / "external" / "client-fork" / "app" / "windows" / "flutter" / "ephemeral").mkdir(parents=True)
            (root / "external" / "client-fork" / "app" / "windows" / "runner" / "__pycache__").mkdir(parents=True)

            matches = self.module._walk_inventory(
                root,
                (self.module.CLASS_SAFE, self.module.CLASS_INTENTIONAL_RESET),
            )
            paths = {match.path for match in matches}

        self.assertIn(".tmp-run/", paths)
        self.assertIn(".tmp-local.log", paths)
        self.assertIn("portal_api_test_fixture.db", paths)
        self.assertIn("portal_api_test_fixture.db-journal", paths)
        self.assertIn("external/client-fork/app/.dart_tool/", paths)
        self.assertIn("external/client-fork/app/build/", paths)
        self.assertIn("external/client-fork/app/windows/flutter/ephemeral/", paths)
        self.assertNotIn("docs/audit-artifacts/__pycache__/", paths)
        self.assertNotIn("external/client-fork/app/out/__pycache__/", paths)
        self.assertNotIn("external/client-fork/app/windows/runner/__pycache__/", paths)

    def test_adminapp_static_export_is_safe_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "adminapp" / "out").mkdir(parents=True)
            matches = self.module._walk_inventory(
                root,
                (self.module.CLASS_SAFE,),
            )

        match = next(item for item in matches if item.path == "adminapp/out/")
        self.assertEqual(match.cleanup_class, self.module.CLASS_SAFE)

    def test_content_video_workspace_is_never_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".content-video-ad" / "__pycache__").mkdir(parents=True)
            matches = self.module._walk_inventory(
                root,
                (self.module.CLASS_SAFE,),
            )

        self.assertFalse(
            any(item.path.startswith(".content-video-ad/") for item in matches)
        )

    def test_apply_deletes_valid_matches_and_rejects_unsafe_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".tmp-run").mkdir()
            (root / "portal_api_test_fixture.db").write_text("", encoding="utf-8")

            matches = self.module._walk_inventory(root, (self.module.CLASS_SAFE,))
            deleted = self.module._apply_matches(root, matches)

            self.assertEqual(sorted(deleted), [".tmp-run/", "portal_api_test_fixture.db"])
            self.assertFalse((root / ".tmp-run").exists())
            self.assertFalse((root / "portal_api_test_fixture.db").exists())

            with self.assertRaises(RuntimeError):
                self.module._ensure_safe_apply_target(
                    root,
                    self.module.CleanupMatch(
                        cleanup_class=self.module.CLASS_SAFE,
                        kind="dir",
                        path="../outside/",
                        reason="test",
                    ),
                )

            with self.assertRaises(RuntimeError):
                self.module._ensure_safe_apply_target(
                    root,
                    self.module.CleanupMatch(
                        cleanup_class=self.module.CLASS_SAFE,
                        kind="dir",
                        path="ops-local/__pycache__/",
                        reason="test",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
