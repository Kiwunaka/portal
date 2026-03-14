import sys
import unittest
from pathlib import Path


class UiVisualSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = str(repo_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

    def test_checkout_gateway_uses_checkout_client_file(self) -> None:
        import importlib

        smoke = importlib.import_module("ui_visual_smoke")
        importlib.reload(smoke)

        checks = smoke._default_checks()
        checkout_check = next(check for check in checks if check.name == "marketing-checkout-gateway")

        self.assertTrue(str(checkout_check.path).endswith("marketing\\src\\app\\checkout\\checkout-client.tsx"))


if __name__ == "__main__":
    unittest.main()
