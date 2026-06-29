from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _assert_contains(text: str, snippets: tuple[str, ...], *, context: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"{context} missing snippets: {missing}"


def test_homepage_navigation_mobile_menu_and_core_sections_have_story_contracts() -> None:
    topbar = _read("marketing/src/components/home/homepage-topbar.tsx")
    homepage = _read("marketing/src/components/home/homepage.tsx")

    _assert_contains(
        topbar,
        (
            "useState(false)",
            'href="/"',
            "#features",
            "#how-it-works",
            "#pricing",
            "#faq",
            "cabinetHref",
            "installHref",
            "aria-expanded={open}",
            "setOpen(true)",
            "setOpen(false)",
            'role="dialog"',
            'aria-hidden={!open}',
            'e.key === "Escape"',
            'document.body.style.overflow = "hidden"',
            "onClick={() => setOpen(false)}",
        ),
        context="homepage topbar",
    )
    _assert_contains(
        homepage,
        (
            "function Hero",
            "HeroAppPreview",
            "TRUST.map",
            "FEATURES.map",
            "HOW_IT_WORKS.map",
            "function Pricing",
            "buildPlanCards",
            "CHECKOUT_READY_PLAN_CODES",
            "MARKETING_FAQ.map",
            "function FinalCta",
            "function Footer",
            "JsonLd data={buildSoftwareApplicationJsonLd",
            "JsonLd data={buildFaqJsonLd(MARKETING_FAQ)}",
            "href={links.installHref}",
            'href="#how-it-works"',
            "href={links.checkoutHref}",
        ),
        context="homepage sections",
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
            "promo_code",
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
            "noIndex: true",
            "function buildCabinetDownloadsHref",
            'url.pathname = "/downloads/"',
            'url.searchParams.set("platform", platform)',
            "config.webappUrl",
            "config.supportTelegramUrl",
            "androidHasArtifact",
            "windowsHasArtifact",
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
