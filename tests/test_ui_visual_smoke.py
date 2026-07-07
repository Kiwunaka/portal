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

        page_check = checks["marketing-home-page"]
        self.assertTrue(str(page_check.path).endswith("marketing\\src\\app\\page.tsx"))
        self.assertIn("buildMarketingMetadata", page_check.must_contain)
        self.assertIn("buildSoftwareApplicationJsonLd", page_check.must_contain)
        self.assertIn("<Hero />", page_check.must_contain)
        self.assertIn("<Pricing />", page_check.must_contain)
        self.assertIn("config.connectUrl", page_check.must_not_contain)

        shell_check = checks["marketing-home-shell"]
        self.assertIn("CANONICAL_WEBAPP_URL", shell_check.must_contain)
        self.assertIn("MARKETING_CANONICAL_PATHS.install", shell_check.must_contain)
        self.assertIn("CANONICAL_CONNECT_URL", shell_check.must_not_contain)

        topbar_check = checks["marketing-home-topbar"]
        self.assertIn("MarketingBrandLogo", topbar_check.must_contain)
        self.assertIn("aria-expanded={menuOpen}", topbar_check.must_contain)
        self.assertIn("setMenuOpen(false)", topbar_check.must_contain)

        hero_check = checks["marketing-home-hero"]
        self.assertIn("HeroVisual", hero_check.must_contain)
        self.assertIn("MARKETING_CANONICAL_PATHS.install", hero_check.must_contain)
        self.assertIn('href="/#how-it-works"', hero_check.must_contain)

        pricing_check = checks["marketing-home-pricing"]
        self.assertIn("getTariffPlans()", pricing_check.must_contain)
        self.assertIn(".filter((plan) => plan.is_active)", pricing_check.must_contain)
        self.assertIn("MARKETING_CANONICAL_PATHS.checkout", pricing_check.must_contain)
        self.assertIn("CHECKOUT_READY_PLAN_CODES", pricing_check.must_not_contain)

        footer_check = checks["marketing-home-footer"]
        self.assertIn("CANONICAL_NEWS_CHANNEL_URL", footer_check.must_contain)
        self.assertIn("CANONICAL_GITHUB_RELEASES_URL", footer_check.must_contain)

        layout_check = checks["marketing-layout-seo"]
        self.assertIn("metadataBase", layout_check.must_contain)
        self.assertIn("/apple-icon.png", layout_check.must_contain)

        checkout_check = checks["marketing-checkout-gateway"]
        self.assertIn("config.webappUrl", checkout_check.must_contain)
        self.assertIn("fetchPaymentProviderState", checkout_check.must_contain)
        self.assertIn("/api/payments/providers", checkout_check.must_contain)
        self.assertIn("tariffPlanAllowsDiscount", checkout_check.must_contain)
        self.assertIn("payment_method: paymentMethod", checkout_check.must_contain)
        self.assertIn("config.connectUrl", checkout_check.must_not_contain)
        self.assertIn("activation key", checkout_check.must_not_contain)

        offer_check = checks["marketing-offer-flow"]
        self.assertIn("buildMarketingMetadata", offer_check.must_contain)

        privacy_check = checks["marketing-privacy-flow"]
        self.assertIn("config.contactEmail", privacy_check.must_contain)

        webapp_entry = checks["webapp-entry"]
        self.assertIn("POKROV cabinet", webapp_entry.must_contain)
        self.assertIn("pokrovBranding.cabinetName", webapp_entry.must_contain)


if __name__ == "__main__":
    unittest.main()
