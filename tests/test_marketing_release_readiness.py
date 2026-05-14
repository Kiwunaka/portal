from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETING_ROOT = REPO_ROOT / "marketing" / "src"
WEBAPP_ROOT = REPO_ROOT / "webapp" / "src"
COPY_CATALOG = REPO_ROOT / "copy" / "catalog.ru.json"


def _read(*parts: str) -> str:
    return (MARKETING_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_webapp(*parts: str) -> str:
    return (WEBAPP_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def _read_copy_catalog() -> str:
    return COPY_CATALOG.read_text(encoding="utf-8")


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


def test_homepage_free_trial_ctas_start_with_install_not_checkout() -> None:
    homepage = _read("components", "home", "homepage.tsx")
    hero = homepage.split("function Hero", 1)[1].split("function ProofStrip", 1)[0]
    free_plan = homepage.split("<div className={styles.pricingIntro}>", 1)[1].split("<div className={styles.planGrid}>", 1)[0]
    final_cta = homepage.split("function FinalCta", 1)[1].split("export default", 1)[0]

    assert "href={links.installHref}" in hero
    assert "href={links.checkoutHref}" not in hero
    assert "href={links.installHref}" in free_plan
    assert "href={links.checkoutHref}" not in free_plan
    assert 'href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}' in final_cta


def test_cabinet_dashboard_download_ctas_point_to_install_route() -> None:
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")

    assert "https://pokrov.space/#download" not in dashboard
    assert "https://pokrov.space/install/" in dashboard


def test_outside_store_beta_copy_avoids_store_distribution_claims() -> None:
    surfaces = [
        _read("components", "marketing-landing.tsx"),
        _read("app", "install", "page.tsx"),
        _read_copy_catalog(),
        _read_webapp("app", "(dashboard)", "dashboard", "page.tsx"),
        _read_webapp("components", "cabinet", "downloads-surface.tsx"),
    ]

    combined = "\n".join(surfaces)
    assert "Google Play" not in combined
    assert "production signing" not in combined
    assert "до signing" not in combined
    assert "физического аудита" not in combined
    assert "GitHub Releases" in combined


def test_email_auth_enabled_ui_stays_ru_only() -> None:
    entry = _read_webapp("components", "cabinet-entry-auth.tsx")

    forbidden = [
        "Verification email sent.",
        "Account created.",
        "Email session token is missing.",
        "Email action failed.",
        'placeholder="Password"',
        ">Sign in<",
        ">Create account<",
        'placeholder="Verification token"',
        'placeholder="Reset token"',
        'placeholder="New password"',
        '"Reset and sign in"',
        '"Send reset email"',
    ]
    for text in forbidden:
        assert text not in entry
    assert "Войти" in entry
    assert "Создать аккаунт" in entry
    assert "Восстановить доступ" in entry
