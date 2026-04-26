from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETING_ROOT = REPO_ROOT / "marketing" / "src"


def _read(*parts: str) -> str:
    return (MARKETING_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def test_marketing_has_real_seo_entrypoints() -> None:
    for relative_path in (
        ("app", "robots.ts"),
        ("app", "sitemap.ts"),
        ("app", "manifest.ts"),
    ):
        assert MARKETING_ROOT.joinpath(*relative_path).exists(), f"Missing SEO route: {'/'.join(relative_path)}"


def test_marketing_public_ctas_do_not_use_connect_host() -> None:
    marketing_landing = _read("components", "marketing-landing.tsx")

    assert 'href={config.connectUrl}' not in marketing_landing
    assert "config.webappUrl" in marketing_landing
    assert "/checkout/?plan=" in marketing_landing


def test_marketing_metadata_declares_canonical_and_share_metadata() -> None:
    layout = _read("app", "layout.tsx")
    landing = _read("components", "marketing-landing.tsx")

    assert "metadataBase" in layout
    assert "alternates" in landing
    assert "canonical" in landing
    assert "twitter" in landing
    assert "images" in landing


def test_marketing_landing_has_quiet_luxury_structure() -> None:
    landing = _read("components", "marketing-landing.tsx")

    assert "lp-hero-stage" in landing
    assert "lp-trust-grid" in landing
    assert "lp-pricing-shell" in landing
    assert "lp-footer-cta" in landing
    assert '<details className="lp-faq-item">' in landing


def test_marketing_sitemap_includes_checkout_route() -> None:
    marketing_site = _read("lib", "marketing-site.ts")
    sitemap_block = marketing_site.split(
        "export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [",
        1,
    )[1].split("];", 1)[0]

    assert "MARKETING_CANONICAL_PATHS.checkout" in sitemap_block
