from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETING_ROOT = REPO_ROOT / "marketing" / "src"
WEBAPP_ROOT = REPO_ROOT / "webapp" / "src"
COPY_CATALOG = REPO_ROOT / "copy" / "catalog.ru.json"


def _read(*parts: str) -> str:
    return MARKETING_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _read_webapp(*parts: str) -> str:
    return WEBAPP_ROOT.joinpath(*parts).read_text(encoding="utf-8")


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
    home_files = [
        _read("app", "page.tsx"),
        _read("components", "layout", "page-shell.tsx"),
        _read("components", "layout", "topbar.tsx"),
        _read("components", "layout", "footer.tsx"),
        _read("components", "home", "hero.tsx"),
        _read("components", "home", "pricing.tsx"),
        _read("components", "home", "final-cta.tsx"),
    ]
    combined = "\n".join(home_files)

    assert "config.connectUrl" not in combined
    assert "CANONICAL_CONNECT_URL" not in combined
    assert "CANONICAL_WEBAPP_URL" in combined
    assert "MARKETING_CANONICAL_PATHS.install" in combined
    assert "MARKETING_CANONICAL_PATHS.checkout" in combined


def test_marketing_metadata_declares_canonical_and_share_metadata() -> None:
    layout = _read("app", "layout.tsx")
    marketing_site = _read("lib", "marketing-site.ts")
    home_page = _read("app", "page.tsx")

    assert "metadataBase" in layout
    assert "buildOrganizationJsonLd" in layout
    assert "buildWebSiteJsonLd" in layout
    assert "alternates" in marketing_site
    assert "canonical" in marketing_site
    assert "twitter" in marketing_site
    assert "images" in marketing_site
    assert '"/opengraph-image.png?v=20260817"' in marketing_site
    assert '"/twitter-image.png?v=20260817"' in marketing_site
    assert "buildMarketingMetadata" in home_page
    assert "buildSoftwareApplicationJsonLd" in home_page
    assert "buildFaqJsonLd" in home_page


def test_marketing_home_uses_current_redesign_structure() -> None:
    page = _read("app", "page.tsx")
    shell = _read("components", "layout", "page-shell.tsx")
    topbar = _read("components", "layout", "topbar.tsx")
    hero = _read("components", "home", "hero.tsx")
    pricing = _read("components", "home", "pricing.tsx")
    footer = _read("components", "layout", "footer.tsx")

    for component in (
        "<Hero />",
        "<Steps />",
        "<Showcase />",
        "<Pricing />",
        "<Faq />",
        "<FinalCta />",
    ):
        assert component in page
    assert "ServicesGrid" not in page
    assert '<main id="main-content"' in shell
    assert "MarketingBrandLogo" in topbar
    assert "AnimatePresence" in topbar
    assert "HeroVisual" in hero
    assert "PriceCard" in pricing
    assert "CANONICAL_NEWS_CHANNEL_URL" in footer
    assert "lp-hero-stage" not in page + shell + topbar + hero + pricing + footer


def test_marketing_sitemap_includes_checkout_route() -> None:
    marketing_site = _read("lib", "marketing-site.ts")
    sitemap_block = marketing_site.split(
        "export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [",
        1,
    )[1].split("];", 1)[0]

    assert "MARKETING_CANONICAL_PATHS.checkout" in sitemap_block


def test_homepage_primary_trial_cta_starts_with_install_and_trial_fact_can_open_checkout() -> None:
    hero = _read("components", "home", "hero.tsx")
    pricing = _read("components", "home", "pricing.tsx")
    final_cta = _read("components", "home", "final-cta.tsx")

    assert "PlatformDownloadAction" in hero
    assert "initialAndroidUrl={config.androidApkUrl}" in hero
    assert "initialWindowsUrl={config.windowsExeUrl}" in hero
    assert "MARKETING_CANONICAL_PATHS.checkout" in hero
    assert "?plan=start_99" in hero
    assert 'href="/#how-it-works"' in hero
    assert "MARKETING_CANONICAL_PATHS.install" in pricing
    assert "MARKETING_CANONICAL_PATHS.checkout" in pricing
    assert pricing.index("MARKETING_CANONICAL_PATHS.install") < pricing.index("MARKETING_CANONICAL_PATHS.checkout")
    assert "MARKETING_CANONICAL_PATHS.install" in final_cta
    assert "CANONICAL_SUPPORT_BOT_URL" in final_cta
    assert "MARKETING_CANONICAL_PATHS.checkout" not in final_cta


def test_homepage_pricing_exposes_all_active_plans_after_payment_gate() -> None:
    pricing = _read("components", "home", "pricing.tsx")

    assert "getTariffPlans()" in pricing
    assert ".filter((plan) => plan.is_active)" in pricing
    assert "plans.map((plan)" in pricing
    assert "CHECKOUT_READY_PLAN_CODES" not in pricing
    assert "encodeURIComponent(plan.code)" in pricing


def test_cabinet_dashboard_download_ctas_point_to_install_route() -> None:
    dashboard = _read_webapp("app", "(dashboard)", "dashboard", "page.tsx")

    assert "https://pokrov.space/#download" not in dashboard
    assert 'const primaryHref = !isActive' in dashboard
    assert '? "/subscription/checkout/"' in dashboard
    assert 'nextStep === "install"' in dashboard
    assert '? "/downloads/"' in dashboard
    assert "href={primaryHref}" in dashboard


def test_outside_store_beta_copy_avoids_store_distribution_claims() -> None:
    surfaces = [
        _read("app", "page.tsx"),
        _read("components", "layout", "footer.tsx"),
        _read("components", "home", "hero.tsx"),
        _read("components", "home", "pricing.tsx"),
        _read("components", "intent", "intent-landing.tsx"),
        _read("app", "install", "page.tsx"),
        _read_copy_catalog(),
        _read_webapp("app", "(dashboard)", "dashboard", "page.tsx"),
        _read_webapp("components", "cabinet", "downloads-surface.tsx"),
    ]

    combined = "\n".join(surfaces)
    assert "Google Play" not in combined
    assert "production signing" not in combined
    assert "physical audit proof" not in combined
    assert "trusted Windows" not in combined

    known_limits = (REPO_ROOT / "shared" / "beta-known-limitations.json").read_text(encoding="utf-8")
    assert "outside_store_beta" in known_limits
    assert "GitHub Releases" in known_limits


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
    assert "Зарегистрироваться" in entry
    assert "Восстановление" in entry
