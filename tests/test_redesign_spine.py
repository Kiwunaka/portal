import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_redesign_spine_locks_visual_and_copy_decisions() -> None:
    tokens = _load_json("shared/design-tokens.json")
    catalog = _load_json("copy/catalog.ru.json")
    spine = _load_json("shared/redesign-spine.json")

    palette = tokens["theme"]["palette"]
    assert palette["canvas"] == "#f8faf7"
    assert palette["emerald"] == "#176d4d"
    assert palette["mint"] == "#eaf6ef"
    assert tokens["theme"]["radius"]["card"] == "1.25rem"
    assert tokens["theme"]["shadow"]["medium"].startswith("0 18px 52px")
    assert tokens["theme"]["shadows"]["medium"].startswith("0 18px 52px")
    assert tokens["platform_exports"]["app"]["radius_dp"]["card"] == 20
    assert tokens["platform_exports"]["web"]["css_variables"]["--pokrov-color-canvas"] == "theme.palette.canvas"

    items = catalog["items"]
    assert items["marketing.hero.primary_cta"]["ru"] == "Попробовать 5 дней"
    assert items["app.nav.protection"]["ru"] == "Подключение"
    assert items["app.nav.locations"]["ru"] == "Локации"
    assert items["app.nav.rules"]["ru"] == "Правила"
    assert items["app.nav.profile"]["ru"] == "Профиль"
    assert items["cabinet.nav.home"]["ru"] == "Главная"
    assert items["cabinet.nav.billing"]["ru"] == "Тарифы и оплата"
    assert items["cabinet.nav.devices"]["ru"] == "Устройства"
    assert items["cabinet.nav.downloads"]["ru"] == "Загрузки"
    assert items["cabinet.nav.support"]["ru"] == "Поддержка"
    assert items["cabinet.nav.profile"]["ru"] == "Профиль"
    assert items["cabinet.nav.settings"]["ru"] == "Настройки"
    assert items["brand.subtitle"]["ru"] == ""
    assert items["platform.apple.badge"]["ru"] == "Готовится"

    assert spine["brand"]["subtitle"] == ""
    assert spine["public_cta"]["primary"] == "Попробовать 5 дней"
    assert spine["app_navigation"] == ["Подключение", "Локации", "Правила", "Профиль"]
    assert spine["cabinet_navigation"] == [
        "Главная",
        "Тарифы и оплата",
        "Устройства",
        "Загрузки",
        "Поддержка",
        "Профиль",
        "Настройки",
    ]
    assert spine["platform_policy"]["apple_badge"] == "Готовится"
    assert spine["platform_policy"]["apple_rule"] == "Show Apple as preparing only; do not add dates or primary CTAs."
    assert spine["visual_direction"]["name"] == "white-mint premium utility"


def test_redesign_asset_manifest_locks_reusable_hero_asset() -> None:
    spine = _load_json("shared/redesign-spine.json")
    manifest = _load_json("shared/redesign-assets.json")

    hero = manifest["assets"]["hero_product"]
    assert spine["asset_policy"]["manifest"] == "shared/redesign-assets.json"
    assert spine["asset_policy"]["hero_product"] == "marketing/public/redesign/pokrov-hero-product.png"
    assert hero["workspace_path"] == "marketing/public/redesign/pokrov-hero-product.png"
    assert hero["public_path"] == "/redesign/pokrov-hero-product.png"
    assert hero["source_path"] == "marketing/public/redesign/pokrov-hero-product-source.png"
    assert hero["text_embedded"] is False
    assert (ROOT / hero["workspace_path"]).is_file()


def test_brand_assets_use_canonical_mark_without_legacy_or_stock_exports() -> None:
    tokens = _load_json("shared/design-tokens.json")
    spine = _load_json("shared/redesign-spine.json")
    manifest = _load_json("shared/redesign-assets.json")

    expected_mark = "marketing/public/redesign/brand/pokrov-mark.svg"
    expected_icon = "marketing/public/redesign/brand/pokrov-app-icon-1024.png"
    expected_pwa_icons = {
        "any_192": "marketing/public/redesign/brand/pokrov-app-icon-192.png",
        "any_512": "marketing/public/redesign/brand/pokrov-app-icon-512.png",
        "maskable_512": "marketing/public/redesign/brand/pokrov-maskable-512.png",
        "apple_180": "marketing/public/apple-touch-icon.png",
    }

    brand_assets = tokens["theme"]["brand_assets"]
    assert brand_assets["preferred_mark_asset"] == expected_mark
    assert brand_assets["preferred_app_icon"] == expected_icon
    assert brand_assets["pwa_icons"] == expected_pwa_icons
    assert spine["asset_policy"]["brand_mark_svg"] == expected_mark
    assert spine["asset_policy"]["app_icon_master"] == expected_icon

    vector_masters = manifest["brand"]["canonical_mark"]["provenance"]["vector_masters"]
    spine_vector_masters = spine["asset_policy"]["canonical_mark_provenance"]["vector_masters"]
    assert vector_masters == ["logo/logoclear.svg"]
    assert spine_vector_masters == ["logo/logoclear.svg"]

    forbidden_asset_text = json.dumps([tokens, spine, manifest], ensure_ascii=False).lower()
    assert "logowithtext" not in forbidden_asset_text
    assert "premium vpn" not in forbidden_asset_text

    for stock_asset in ("file.svg", "globe.svg", "next.svg", "vercel.svg", "window.svg"):
        assert not (ROOT / "webapp" / "public" / stock_asset).exists()
