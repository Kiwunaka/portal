from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _assert_contains(text: str, snippets: tuple[str, ...], *, context: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"{context} missing snippets: {missing}"


def test_homepage_navigation_mobile_menu_and_core_sections_have_story_contracts() -> None:
    topbar = _read("marketing/src/components/layout/topbar.tsx")
    shell = _read("marketing/src/components/layout/page-shell.tsx")
    footer = _read("marketing/src/components/layout/footer.tsx")
    page = _read("marketing/src/app/page.tsx")
    hero = _read("marketing/src/components/home/hero.tsx")
    pricing = _read("marketing/src/components/home/pricing.tsx")
    faq = _read("marketing/src/components/home/faq.tsx")

    _assert_contains(
        topbar,
        (
            "useState(false)",
            'href="/"',
            "labels.nav.map",
            "labels.cabinetHref",
            "labels.downloadHref",
            "aria-expanded={menuOpen}",
            "AnimatePresence",
            "useReducedMotion",
            "onClick={() => setMenuOpen(false)}",
        ),
        context="homepage topbar",
    )
    _assert_contains(
        shell,
        (
            "Topbar labels={labels}",
            "Footer",
            "#features",
            "#how-it-works",
            "#pricing",
            "#faq",
            "MARKETING_CANONICAL_PATHS.install",
        ),
        context="homepage shell",
    )
    _assert_contains(
        page,
        (
            "JsonLd data={buildSoftwareApplicationJsonLd",
            "JsonLd data={buildFaqJsonLd(MARKETING_FAQ)}",
            "Hero",
            "HonestyStrip",
            "ServicesGrid",
            "Steps",
            "Showcase",
            "Pricing",
            "TelegramBonus",
            "Faq",
            "FinalCta",
        ),
        context="homepage page",
    )
    _assert_contains(
        hero,
        (
            "HeroVisual",
            "getTariffPlans().find",
            "MARKETING_CANONICAL_PATHS.install",
            'href="/#how-it-works"',
        ),
        context="homepage hero",
    )
    _assert_contains(
        pricing,
        (
            "function Pricing",
            "getTariffPlans()",
            ".filter((plan) => plan.is_active)",
            "plans.map",
            "PriceCard",
            "MARKETING_CANONICAL_PATHS.checkout",
            "plan.code",
        ),
        context="homepage pricing",
    )
    assert "CHECKOUT_READY_PLAN_CODES" not in pricing
    _assert_contains(
        faq,
        (
            "MARKETING_FAQ",
            "Accordion",
            'id="faq"',
        ),
        context="homepage faq",
    )
    _assert_contains(
        footer,
        (
            "FooterColumn",
            "CANONICAL_SUPPORT_BOT_URL",
            "CANONICAL_GITHUB_RELEASES_URL",
            "MARKETING_CANONICAL_PATHS.offer",
            "MARKETING_CANONICAL_PATHS.privacy",
        ),
        context="homepage footer",
    )


def test_marketing_route_seo_and_responsive_checks_cover_public_entrypoints() -> None:
    marketing_site = _read("marketing/src/lib/marketing-site.ts")
    responsive = _read("marketing/scripts/check-marketing-responsive.mjs")
    seo = _read("marketing/scripts/check-marketing-seo.mjs")

    canonical_routes = ("/mobile/", "/devices/", "/telegram/", "/youtube/", "/tiktok/", "/vpn/")
    for route in canonical_routes:
        assert f'"{route}"' in marketing_site
        assert f'"{route}"' in responsive
        assert (ROOT / f"marketing/src/app{route}page.tsx").exists()

    _assert_contains(
        responsive,
        (
            "const ROUTES =",
            "const VIEWPORTS =",
            'name: "mobile"',
            'name: "tablet"',
            'name: "desktop"',
            "page.screenshot",
            "hasBrand: bodyText.includes(\"POKROV\")",
            "hasPrimaryCta",
            "root.scrollWidth",
            "root.clientWidth",
            "consoleIssues",
            "framework overlay visible",
            "horizontal overflow",
        ),
        context="marketing responsive script",
    )
    _assert_contains(
        seo,
        (
            "legacyRedirectMap",
            "checkCanonicalRoutes",
            "checkRedirectsFile",
            "checkSourceCopy",
            "checkSitemapSource",
            "checkBuiltOutput",
            "public/_redirects",
        ),
        context="marketing seo script",
    )


def test_marketing_checkout_contract_keeps_provider_fallback_redeem_and_email_flow() -> None:
    checkout = _read("marketing/src/app/checkout/checkout-client.tsx")
    checkout_page = _read("marketing/src/app/checkout/page.tsx")
    cabinet_checkout = _read("webapp/src/app/(dashboard)/subscription/checkout/page.tsx")
    tariff_helpers = _read("shared/tariff-catalog.ts")

    _assert_contains(
        checkout,
        (
            "function candidateApiBases",
            "config.apiBaseUrl",
            "window.location.origin",
            "https://api.pokrov.space",
            "async function fetchCatalog",
            "/api/public/catalog",
            "async function fetchAccessKeyStatus",
            "/api/access-keys/status/",
            "async function fetchPaymentProviderState",
            "/api/payments/providers",
            "async function createPublicRubOrder",
            "/api/payments/orders/create-public",
            "buyer_email",
            "payment_method",
            "promo_code",
            "getCheckoutTariffPlans",
            "tariffPlanAllowsDiscount",
            "PAYMENT_METHOD_OPTIONS",
            "window.location.assign(paymentUrl)",
            "function buildRedeemHref",
            'url.pathname = "/redeem/"',
            'type="email"',
            'placeholder="email@example.com"',
            "checkoutReady",
            "checkoutBlockedReasons",
            "config.botUrl",
            "MARKETING_CANONICAL_PATHS.install",
        ),
        context="marketing checkout client",
    )
    assert "CHECKOUT_READY_PLAN_CODES" not in checkout
    assert "CHECKOUT_READY_PLAN_CODES" not in cabinet_checkout
    _assert_contains(
        cabinet_checkout,
        (
            "getCheckoutTariffPlans",
            "tariffPlanAllowsDiscount",
            "PAYMENT_METHOD_OPTIONS",
            "payment_method: paymentMethod",
            "promo_code: discountPercent > 0 ? promoCode : undefined",
        ),
        context="cabinet checkout client",
    )
    _assert_contains(
        tariff_helpers,
        (
            "export function isCheckoutTariffPlan",
            "export function getCheckoutTariffPlans",
            "Number(plan?.amount_rub || 0) > 0",
            '!== "start_99"',
        ),
        context="tariff helper checkout gates",
    )
    _assert_contains(
        checkout_page,
            (
                "buildBreadcrumbJsonLd",
                "CheckoutClient",
                'path: "/checkout/"',
                "noIndex: false",
            ),
        context="marketing checkout page",
    )


def test_install_legal_machine_files_and_intent_pages_remain_available() -> None:
    source_paths = (
        "marketing/src/app/install/page.tsx",
        "marketing/src/app/offer/page.tsx",
        "marketing/src/app/privacy/page.tsx",
        "marketing/src/app/robots.ts",
        "marketing/src/app/sitemap.ts",
        "marketing/src/app/manifest.ts",
        "marketing/src/components/funnel-tracker.tsx",
    )
    for relative_path in source_paths:
        assert (ROOT / relative_path).exists(), f"missing {relative_path}"

    install_page = _read("marketing/src/app/install/page.tsx")
    vpn_page = _read("marketing/src/app/vpn/page.tsx")

    _assert_contains(
        install_page,
        (
            "function buildCabinetDownloadsHref",
            'url.pathname = "/downloads/"',
            'url.searchParams.set("platform", platform)',
            "config.webappUrl",
            "config.supportTelegramUrl",
            "PlatformTabs",
            'id: "android"',
            'id: "windows"',
            "buildFaqJsonLd",
            "buildBreadcrumbJsonLd",
            "target=\"_blank\"",
        ),
        context="marketing install page",
    )
    _assert_contains(
        vpn_page,
        (
            "VPN_FAQ",
            "buildArticleJsonLd",
            "buildFaqJsonLd(VPN_FAQ)",
            "MARKETING_CANONICAL_PATHS.vpn",
            "vpn",
            "android",
            "windows",
        ),
        context="marketing vpn page",
    )
