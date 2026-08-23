from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
GENERATOR_PATH = REPO_ROOT / "scripts" / "generate_commercial_contract.py"

if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_commercial_contract_for_tests", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(relative: str) -> dict:
    value = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_generated_commercial_contract_is_current_and_schema_bounded() -> None:
    generator = _load_generator()
    product = _read_json("shared/product-facts.json")
    tariff = _read_json("shared/tariff-catalog.json")
    contract = _read_json("shared/commercial-contract.json")
    schema = _read_json("shared/commercial-contract.schema.json")

    assert contract == generator.build_contract(product, tariff)
    unsigned = {key: value for key, value in contract.items() if key != "contract_sha256"}
    assert contract["contract_sha256"] == generator._digest(unsigned)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(contract)
    assert schema["properties"]["price_authority"]["const"] == "server_commercial_contract"
    assert schema["properties"]["promo_authority"]["const"] == "server_offer_preview_only"
    assert schema["properties"]["capacity_policy"]["properties"]["limit_units"]["const"] == 300
    assert schema["properties"]["plans"]["items"]["properties"]["temporary_campaign_saving_percent"]["const"] == 0
    assert (REPO_ROOT / "docs/generated/commercial-contract.md").read_text(encoding="utf-8") == generator.render_document(contract)


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    (
        (lambda catalog: catalog.__setitem__("pricing_preview", {"discount_codes": {"POKROV10": 10}}), "static_pricing_preview_forbidden"),
        (lambda catalog: catalog.__setitem__("commercial_revision", "latest"), "invalid_commercial_revision"),
        (lambda catalog: catalog["capacity_policy"].__setitem__("limit_units", 301), "capacity_limit_must_be_300"),
        (lambda catalog: catalog["plans"][1].__setitem__("temporary_campaign_saving_percent", 10), "static_campaign_saving_forbidden"),
    ),
)
def test_generator_rejects_stale_or_client_owned_commercial_truth(mutation, error_code: str) -> None:
    generator = _load_generator()
    product = _read_json("shared/product-facts.json")
    tariff = copy.deepcopy(_read_json("shared/tariff-catalog.json"))
    mutation(tariff)

    with pytest.raises(generator.CommercialContractError, match=error_code):
        generator.build_contract(product, tariff)


def test_python_adapter_validates_sources_projection_and_scalar_health() -> None:
    commercial = importlib.import_module("commercial_contract")
    commercial.clear_commercial_contract_cache()
    contract = commercial.get_commercial_contract()
    projection = [
        {
            "code": plan["code"],
            "amount_rub": plan["amount_rub"],
            "days": plan["duration_days"],
            "device_limit": plan["device_limit"],
        }
        for plan in contract["plans"]
        if plan["is_active"] and plan["public_visibility"] != "hidden"
    ]

    commercial.assert_plan_projection_matches_contract(projection)
    changed = copy.deepcopy(projection)
    changed[0]["amount_rub"] += 1
    with pytest.raises(commercial.CommercialContractError, match="commercial_plan_projection_mismatch"):
        commercial.assert_plan_projection_matches_contract(changed)

    health = commercial.commercial_health_snapshot()
    assert health["commercial_revision"] == contract["commercial_revision"]
    assert health["legal_launch_state"] == "blocked"
    assert health["source_consistency"] == "consistent"
    assert all(type(value) in {str, int} for value in health.values())


def test_legal_capacity_and_price_authorities_are_explicitly_fail_closed() -> None:
    contract = _read_json("shared/commercial-contract.json")

    assert contract["price_authority"] == "server_commercial_contract"
    assert contract["promo_authority"] == "server_offer_preview_only"
    assert contract["campaign_saving_authority"] == "server_offer_preview_only"
    assert contract["legal"]["launch_ready"] is False
    assert contract["legal"]["allowed_launch_channels"] == []
    assert contract["capacity_policy"]["limit_units"] == 300
    assert contract["capacity_policy"]["acquisition_allowed_bands"] == ["green", "yellow"]
    assert contract["capacity_policy"]["resume_below_ratio"] < contract["capacity_policy"]["pause_at_ratio"]
    assert all(plan["temporary_campaign_saving_percent"] == 0 for plan in contract["plans"])


def test_marketing_webapp_bot_and_json_ld_share_the_manifest_price_authority() -> None:
    marketing_checkout = (REPO_ROOT / "marketing/src/app/checkout/checkout-client.tsx").read_text(encoding="utf-8")
    marketing_acquisition = (REPO_ROOT / "marketing/src/lib/acquisition.ts").read_text(encoding="utf-8")
    marketing_site = (REPO_ROOT / "marketing/src/lib/marketing-site.ts").read_text(encoding="utf-8")
    webapp_api = (REPO_ROOT / "webapp/src/lib/api.ts").read_text(encoding="utf-8")
    webapp_checkout = (REPO_ROOT / "webapp/src/app/(dashboard)/subscription/checkout/page.tsx").read_text(encoding="utf-8")
    bot = (REPO_ROOT / "portal_bot/bot.py").read_text(encoding="utf-8")
    payment_routes = (REPO_ROOT / "portal_bot/api_payment_routes.py").read_text(encoding="utf-8")
    payment_return_service = (REPO_ROOT / "portal_bot/payment_return_service.py").read_text(encoding="utf-8")
    tariff_helper = (REPO_ROOT / "shared/tariff-catalog.ts").read_text(encoding="utf-8")

    assert "assertCommercialPlanProjection(ALL_TARIFF_PLANS)" in marketing_site
    assert "price: String(plan.amount_rub || 0)" in marketing_site
    assert "COMMERCIAL_REVISION" in marketing_checkout
    assert 'response.headers.get("X-Pokrov-Commercial-Revision")' in marketing_checkout
    assert "assertCommercialPlanProjection(payload.plans)" in marketing_checkout
    assert "Boolean(catalog && providerState?.ok" in marketing_checkout
    assert 'fetch(`${base}/api/public/offers/preview`' in marketing_checkout
    assert "promo_code: promoCode" in marketing_checkout
    assert "offer_token: payload.offer_token" in marketing_checkout
    assert "payment_return_token" in marketing_checkout
    assert "paymentMethods.map" in marketing_checkout
    assert 'mintAcquisitionHandoff("checkout", undefined, config.apiBaseUrl)' in marketing_checkout
    assert "apiBaseUrl = CANONICAL_API_BASE_URL" in marketing_acquisition
    assert "`${apiBase}/api/acquisition/handoffs`" in marketing_acquisition
    assert "COMMERCIAL_REVISION" in webapp_api
    assert 'response.headers.get("X-Pokrov-Commercial-Revision")' in webapp_api
    assert "assertCommercialPlanProjection(payload.plans)" in webapp_api
    assert "catalogVerified && providerState?.ok" in webapp_checkout
    assert "promo_code: promoCode || undefined" in webapp_checkout
    assert 'apiFetch("/api/public/offers/preview"' in webapp_api
    assert 'unauthenticatedJsonPost("/api/payments/orders/status"' in webapp_api
    assert "offer_token: offerPreview?.valid" in webapp_checkout
    assert "paymentMethods.map" in webapp_checkout
    assert '@app.post("/api/payments/orders/status"' in payment_routes
    assert "PAYMENT_RETURN_STATES" in payment_return_service
    assert '"processing", "paid", "failed", "cancelled", "manual_review", "expired"' in payment_return_service
    assert "commercial_plan_map" in bot and "BOT_COMMERCIAL_REVISION = commercial_revision()" in bot
    bot_tariff_block = bot[bot.index("# Tariff definitions"):bot.index("# Backward compatibility")]
    assert '"stars": 239' not in bot_tariff_block
    assert "getPricingPreviewDiscountPercent" not in tariff_helper
    assert "discount_codes" not in tariff_helper
