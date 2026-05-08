import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "check_script_manifest.py"
    spec = importlib.util.spec_from_file_location("check_script_manifest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckScriptManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_iter_refs_ignores_client_fork_script_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(
                "python scripts/release_gate_check.py\n"
                "python external/client-fork/scripts/check_release_urls.py\n",
                encoding="utf-8",
            )

            refs = self.module._iter_refs(path)

        self.assertIn("scripts/release_gate_check.py", refs)
        self.assertNotIn("scripts/check_release_urls.py", refs)

    def test_collect_doc_files_skips_retained_work_order_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "developer" / "work-orders").mkdir(parents=True)
            (root / "docs" / "product").mkdir(parents=True)
            (root / "docs" / "README.md").write_text("# docs\n", encoding="utf-8")
            (root / "docs" / "developer" / "work-orders" / "old.md").write_text(
                "python scripts/removed_legacy_probe.py\n",
                encoding="utf-8",
            )
            (root / "docs" / "product" / "current.md").write_text(
                "python scripts/release_gate_check.py\n",
                encoding="utf-8",
            )

            docs = {path.relative_to(root).as_posix() for path in self.module._collect_doc_files(root)}

        self.assertIn("docs/README.md", docs)
        self.assertIn("docs/product/current.md", docs)
        self.assertNotIn("docs/developer/work-orders/old.md", docs)


if __name__ == "__main__":
    unittest.main()
