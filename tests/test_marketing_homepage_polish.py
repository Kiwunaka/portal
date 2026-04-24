import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME_TSX = ROOT / "marketing/src/components/home/homepage.tsx"
HOME_CSS = ROOT / "marketing/src/components/home/homepage.module.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _css_block(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\n\}}", css, re.DOTALL)
    assert match, f"Missing CSS selector: {selector}"
    return match.group("body")


def test_homepage_story_starts_with_key_and_app_activation() -> None:
    text = _read(HOME_TSX)
    before_pricing = text.split('<section id="pricing"', 1)[0]

    assert "Получить ключ на 5 дней" in before_pricing
    assert "Скачать приложение" in before_pricing
    assert "Три шага: получить ключ, скачать приложение, активировать." in text
    assert "оплат" not in before_pricing.lower()
    assert "VPN" not in text


def test_homepage_copy_avoids_stale_repeated_terms() -> None:
    text = _read(HOME_TSX).lower()

    for stale in ("спокой", "маршрут", "инфраструкт", "одном спокойном пути"):
        assert stale not in text


def test_homepage_cta_colors_override_link_inheritance() -> None:
    css = _read(HOME_CSS)

    assert ".page a {" not in css
    assert ".page :where(a)" in css
    assert "color: #ffffff;" in _css_block(css, ".primaryButton")
    assert "color: var(--emerald-strong);" in _css_block(css, ".lightButton")
    assert "color: #ffffff;" in _css_block(css, ".outlineButton")


def test_homepage_uses_large_product_mockup_and_compact_status_rail() -> None:
    tsx = _read(HOME_TSX)
    css = _read(HOME_CSS)

    assert "productStatusRail" in tsx
    assert "productStatusRail" in css
    assert "width: min(112%, 760px);" in css
    assert "mapPanel" not in tsx
    assert "mapPanel" not in css
    assert "heroHintRail" not in tsx
    assert "heroHintRail" not in css
