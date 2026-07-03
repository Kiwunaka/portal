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

    def test_ui_smoke_tracks_marketing_release_contract(self) -> None:
        import importlib

        smoke = importlib.import_module("ui_visual_smoke")
        importlib.reload(smoke)

        checks = {check.name: check for check in smoke._default_checks()}

        hero_check = checks["marketing-home-cta"]
        self.assertTrue(str(hero_check.path).endswith("marketing\\src\\components\\marketing-landing.tsx"))
        self.assertIn("config.webappUrl", hero_check.must_contain)
        self.assertIn("config.newsChannelUrl", hero_check.must_contain)
        self.assertIn("/checkout/?plan=", hero_check.must_contain)
        self.assertIn("POKROV открывает YouTube, TikTok и другие сервисы", hero_check.must_contain)
        self.assertIn("Один сценарий под эту задачу.", hero_check.must_contain)
        self.assertIn("lp-hero-stage", hero_check.must_contain)
        self.assertIn("lp-trust-grid", hero_check.must_contain)
        self.assertIn("lp-pricing-shell", hero_check.must_contain)
        self.assertIn("lp-footer-cta", hero_check.must_contain)
        self.assertIn('className="lp-faq-item"', hero_check.must_contain)
        self.assertIn("href={config.connectUrl}", hero_check.must_not_contain)
        self.assertIn("managed premium", hero_check.must_not_contain)

        layout_check = checks["marketing-layout-seo"]
        self.assertIn("metadataBase", layout_check.must_contain)
        self.assertIn("/apple-icon.png", layout_check.must_contain)

        offer_check = checks["marketing-offer-flow"]
        self.assertIn("Открыть Telegram-бота", offer_check.must_contain)

        privacy_check = checks["marketing-privacy-flow"]
        self.assertIn("config.contactEmail", privacy_check.must_contain)

        checkout_check = checks["marketing-checkout-gateway"]
        self.assertIn("config.webappUrl", checkout_check.must_contain)
        self.assertIn("fetchPaymentProviderState", checkout_check.must_contain)
        self.assertIn("/api/payments/providers", checkout_check.must_contain)
        self.assertIn("Оплата временно недоступна", checkout_check.must_contain)
        self.assertIn("код активации", checkout_check.must_contain)
        self.assertIn("Продолжить в Telegram", checkout_check.must_contain)
        self.assertIn("config.connectUrl", checkout_check.must_not_contain)
        self.assertIn("activation key", checkout_check.must_not_contain)

        webapp_entry = checks["webapp-entry"]
        self.assertIn("POKROV cabinet", webapp_entry.must_contain)
        self.assertIn("pokrovBranding.cabinetName", webapp_entry.must_contain)


if __name__ == "__main__":
    unittest.main()
