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

    def test_ui_smoke_tracks_current_trial_first_copy(self) -> None:
        import importlib

        smoke = importlib.import_module("ui_visual_smoke")
        importlib.reload(smoke)

        checks = {check.name: check for check in smoke._default_checks()}

        hero_check = checks["marketing-home-cta"]
        self.assertTrue(str(hero_check.path).endswith("marketing\\src\\components\\marketing-landing.tsx"))
        self.assertIn("🚀 Начать бесплатно", hero_check.must_contain)
        self.assertIn("Посмотреть тарифы", hero_check.must_contain)
        self.assertIn("Открыть в Telegram", hero_check.must_contain)

        offer_check = checks["marketing-offer-flow"]
        self.assertIn("Открыть Telegram-бота", offer_check.must_contain)

        checkout_check = checks["marketing-checkout-gateway"]
        self.assertIn("Продолжить в Telegram", checkout_check.must_contain)
        self.assertIn("Запустить тест в Telegram", checkout_check.must_contain)


if __name__ == "__main__":
    unittest.main()
