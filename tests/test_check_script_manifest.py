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


if __name__ == "__main__":
    unittest.main()
