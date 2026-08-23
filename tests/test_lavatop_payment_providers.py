import asyncio
import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


class LavaTopPaymentProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)
        self.providers = importlib.import_module("payment_providers")
        importlib.reload(self.providers)
        self._saved_env: dict[str, str | None] = {}
        for key in (
            "LAVATOP_API_BASE_URL",
            "LAVATOP_API_KEY",
            "LAVATOP_BUYER_EMAIL_DOMAIN",
            "LAVATOP_DYNAMIC_AMOUNT_ENABLED",
            "LAVATOP_OFFER_ID",
            "LAVATOP_OFFER_ID_START_99",
            "LAVATOP_PAYMENT_METHOD",
            "LAVATOP_PAYMENT_PROVIDER",
            "LAVATOP_WEBHOOK_API_KEY",
            "CARDLINK_API_TOKEN",
            "CARDLINK_SHOP_ID",
            "PALLY_API_TOKEN",
            "PALLY_SHOP_ID",
            "RUB_PAYMENT_PROVIDER_ENABLED",
            "RUB_PAYMENT_PROVIDER_ORDER",
        ):
            self._saved_env[key] = os.environ.get(key)
            os.environ.pop(key, None)
    def tearDown(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_lavatop_configuration_requires_invoice_and_webhook_secrets(self) -> None:
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        self.assertFalse(self.providers.provider_is_configured("lavatop"))

        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        self.assertTrue(self.providers.provider_is_configured("lavatop"))

    def test_enabled_catalog_can_prefer_lavatop_when_fully_configured(self) -> None:
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "lavatop,cardlink"
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "lavatop"

        self.assertEqual(self.providers.enabled_rub_provider_codes(), ["lavatop"])
        catalog = self.providers.enabled_provider_catalog()
        self.assertEqual(catalog[0]["code"], "lavatop")
        self.assertEqual(catalog[0]["label"], "Lava.top")

    def test_public_catalog_is_lava_only_even_when_stale_env_enables_other_providers(self) -> None:
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = "true"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        os.environ["CARDLINK_API_TOKEN"] = "cardlink_token"
        os.environ["CARDLINK_SHOP_ID"] = "cardlink_shop"
        os.environ["PALLY_API_TOKEN"] = "pally_token"
        os.environ["PALLY_SHOP_ID"] = "pally_shop"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "cardlink,pally,lavatop"
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "cardlink,pally,lavatop"

        self.assertEqual(
            [row["code"] for row in self.providers.enabled_public_provider_catalog(plan_code="1_month")],
            ["lavatop"],
        )

    def test_public_lavatop_readiness_is_exact_per_plan_without_dynamic_offer(self) -> None:
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID_START_99"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        os.environ["RUB_PAYMENT_PROVIDER_ORDER"] = "lavatop"
        os.environ["RUB_PAYMENT_PROVIDER_ENABLED"] = "lavatop"

        self.assertTrue(self.providers.public_provider_is_configured_for_plan("lavatop", "start_99"))
        self.assertFalse(self.providers.public_provider_is_configured_for_plan("lavatop", "1_month"))
        self.assertEqual(
            [row["code"] for row in self.providers.enabled_public_provider_catalog(plan_code="start_99")],
            ["lavatop"],
        )
        self.assertEqual(self.providers.enabled_public_provider_catalog(plan_code="1_month"), [])

    def test_create_lavatop_invoice_uses_v3_contract_payload(self) -> None:
        os.environ["LAVATOP_API_BASE_URL"] = "https://lava.example.test"
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID_START_99"] = "836b9fc5-7ae9-4a27-9642-592bc44072b7"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        os.environ["LAVATOP_PAYMENT_PROVIDER"] = "PAY2ME"
        os.environ["LAVATOP_PAYMENT_METHOD"] = "SBP"
        os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = "true"
        os.environ["LAVATOP_BUYER_EMAIL_DOMAIN"] = "customers.example"
        capture: dict[str, object] = {}

        class FakeRegistry:
            async def post_object(self, **kwargs):
                capture["url"] = kwargs["url"]
                capture["headers"] = dict(kwargs.get("headers") or {})
                capture["json"] = dict(kwargs.get("json_body") or {})
                return SimpleNamespace(
                    status=201,
                    body={
                        "id": "7ea82675-4ded-4133-95a7-a6efbaf165cc",
                        "paymentUrl": "https://checkout.lava.top/pay/contract-1",
                    },
                )

        result = asyncio.run(
            self.providers.create_rub_payment(
                http_registry=FakeRegistry(),
                provider="lavatop",
                order_id="lavatop_site_101_abcd",
                amount_rub=99,
                currency="RUB",
                description="POKROV Start",
                success_url="https://pay.pokrov.space/success",
                fail_url="https://pay.pokrov.space/fail",
                result_url="https://api.pokrov.space/api/payments/result/lavatop",
                refund_url="https://api.pokrov.space/api/payments/refund/lavatop",
                chargeback_url="https://api.pokrov.space/api/payments/chargeback/lavatop",
                logo_url="",
                custom={
                    "tg_id": 101,
                    "plan_code": "start_99",
                    "source": "site",
                    "campaign": "beta",
                    "promo_code": "WELCOME20",
                },
            )
        )

        self.assertEqual(result["payment_url"], "https://checkout.lava.top/pay/contract-1")
        self.assertEqual(capture["url"], "https://lava.example.test/api/v3/invoice")
        self.assertEqual(capture["headers"]["X-Api-Key"], "lava_api_test")
        payload = capture["json"]
        self.assertEqual(payload["email"], "pokrov+lavatop_site_101_abcd@customers.example")
        self.assertEqual(payload["offerId"], "836b9fc5-7ae9-4a27-9642-592bc44072b7")
        self.assertEqual(payload["currency"], "RUB")
        self.assertEqual(payload["paymentProvider"], "PAY2ME")
        self.assertEqual(payload["paymentMethod"], "SBP")
        self.assertEqual(payload["buyerLanguage"], "RU")
        self.assertEqual(payload["amount"], 99.0)
        self.assertEqual(payload["clientUtm"]["utm_content"], "lavatop_site_101_abcd")
        self.assertEqual(payload["clientUtm"]["utm_medium"], "site")
        self.assertEqual(payload["clientUtm"]["utm_campaign"], "beta")
        self.assertEqual(payload["clientUtm"]["utm_term"], "start_99")

    def test_create_lavatop_invoice_allows_per_order_payment_method_override(self) -> None:
        os.environ["LAVATOP_API_BASE_URL"] = "https://lava.example.test"
        os.environ["LAVATOP_API_KEY"] = "lava_api_test"
        os.environ["LAVATOP_OFFER_ID"] = "5264bc13-4cb0-4b88-8753-7af13f3e657b"
        os.environ["LAVATOP_WEBHOOK_API_KEY"] = "lava_webhook_test"
        os.environ["LAVATOP_PAYMENT_PROVIDER"] = "SMART_GLOCAL"
        os.environ["LAVATOP_PAYMENT_METHOD"] = "CARD"
        os.environ["LAVATOP_DYNAMIC_AMOUNT_ENABLED"] = "true"
        capture: dict[str, object] = {}

        class FakeRegistry:
            async def post_object(self, **kwargs):
                capture["json"] = dict(kwargs.get("json_body") or {})
                return SimpleNamespace(
                    status=201,
                    body={
                        "id": "invoice-1",
                        "paymentUrl": "https://checkout.lava.top/pay/contract-1",
                    },
                )

        asyncio.run(
            self.providers.create_rub_payment(
                http_registry=FakeRegistry(),
                provider="lavatop",
                order_id="lavatop_site_method_abcd",
                amount_rub=99,
                currency="RUB",
                description="POKROV Start",
                success_url="https://pay.pokrov.space/success",
                fail_url="https://pay.pokrov.space/fail",
                result_url="https://api.pokrov.space/api/payments/result/lavatop",
                refund_url="https://api.pokrov.space/api/payments/refund/lavatop",
                chargeback_url="https://api.pokrov.space/api/payments/chargeback/lavatop",
                logo_url="",
                custom={
                    "plan_code": "start_99",
                    "source": "site",
                    "lavatop_payment_provider": "PAY2ME",
                    "lavatop_payment_method": "SBP",
                },
            )
        )

        payload = capture["json"]
        self.assertEqual(payload["paymentProvider"], "PAY2ME")
        self.assertEqual(payload["paymentMethod"], "SBP")
        self.assertEqual(payload["amount"], 99.0)

    def test_lavatop_callback_helpers_extract_contract_and_status(self) -> None:
        payload = {
            "eventType": "payment.success",
            "contractId": "7ea82675-4ded-4133-95a7-a6efbaf165cc",
            "amount": 99,
            "currency": "RUB",
            "status": "completed",
            "clientUtm": {"utm_content": "lavatop_bot_5555_abcd"},
        }
        self.assertEqual(
            self.providers.callback_ids("lavatop", payload),
            ("lavatop_bot_5555_abcd", "7ea82675-4ded-4133-95a7-a6efbaf165cc"),
        )
        self.assertEqual(self.providers.callback_status("lavatop", payload), "completed")

        failed = dict(payload)
        failed["eventType"] = "payment.failed"
        failed["status"] = "failed"
        self.assertEqual(self.providers.callback_status("lavatop", failed), "failed")


if __name__ == "__main__":
    unittest.main()
