import sys
import unittest
from pathlib import Path


class AdminWebappSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = str(repo_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

    def test_admin_smoke_has_no_false_mojibake_hits(self) -> None:
        import importlib

        smoke = importlib.import_module("admin_webapp_smoke")
        importlib.reload(smoke)

        self.assertEqual(smoke._check_mojibake(), [])


if __name__ == "__main__":
    unittest.main()
