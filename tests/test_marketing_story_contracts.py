import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
    override = os.environ.get("POKROV_CLIENT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=True,
        capture_output=True,
        text=True,
    )
    platform_root = Path(completed.stdout.strip()).resolve().parent
    client_repo = platform_root.parent / "POKROV-app"
    if not client_repo.is_dir():
        return client_repo

    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=client_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for block in worktrees.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if fields.get("branch") == "refs/heads/main" and fields.get("worktree"):
            return Path(fields["worktree"]).resolve()
    return client_repo


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
            "Steps",
            "Showcase",
            "Pricing",
            "Faq",
            "FinalCta",
        ),
        context="homepage page",
    )
    assert "ServicesGrid" not in page
    _assert_contains(
        hero,
        (
            "HeroVisual",
            "getTariffPlans().find",
            "PlatformDownloadAction",
            "initialAndroidUrl={config.androidApkUrl}",
            "initialWindowsUrl={config.windowsExeUrl}",
            "Проверьте подключение до оплаты",
            'href="/#how-it-works"',
        ),
        context="homepage hero",
    )
    assert "YouTube, TikTok и ChatGPT — одной кнопкой" not in hero
    _assert_contains(
        pricing,
        (
            "function Pricing",
            "getTariffPlans()",
            ".filter((plan) => plan.is_active)",
            '["start_99", "6_months", "12_months"]',
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

    assert "bestVpn: SEO_PAGE_PATHS.bestVpn" in marketing_site
    assert '"/best-vpn/"' in responsive
    assert '"/best-vpn/"' in seo
    assert (ROOT / "marketing/src/app/best-vpn/page.tsx").exists()

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
    cabinet_plans = _read("webapp/src/lib/cabinet-plans.ts")
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
            "/api/payments/start-99-eligibility",
            "checkout_ticket: payload.checkout_ticket",
            "start_99_already_used",
            "Приветственный месяц уже использован",
            'replacementPlan || "1_month"',
            "buyer_email",
            "payment_method",
            "promo_code",
            "getCheckoutTariffPlans",
            "COMMERCIAL_REVISION",
            'response.headers.get("X-Pokrov-Commercial-Revision")',
            'payload.price_authority !== "server_commercial_contract"',
            'payload.promo_authority !== "server_offer_preview_only"',
            "assertCommercialPlanProjection(payload.plans)",
            "Boolean(catalog && providerState?.ok",
            "paymentMethods.map",
            "option.available",
            "window.location.assign(paymentUrl)",
            "function buildRedeemHref",
            'url.pathname = "/redeem/"',
            'type="email"',
            'name="email"',
            'autoComplete="email"',
            'inputMode="email"',
            'placeholder="email@example.com"',
            '"scroll-mt-24"',
            'aria-errormessage={emailError ? "checkout-email-error" : undefined}',
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
        cabinet_checkout + cabinet_plans,
        (
            "getCheckoutTariffPlans",
            "paymentMethods.map",
            "option.available",
            "payment_method: paymentMethod",
            "promo_code: promoCode || undefined",
            "catalogVerified && providerState?.ok",
            "Проверяем промокод на сервере…",
            "Сумма зафиксирована до",
        ),
        context="cabinet checkout client",
    )
    assert "getPricingPreviewDiscountPercent" not in checkout
    assert "getPricingPreviewDiscountPercent" not in cabinet_checkout
    assert "discount_codes" not in tariff_helpers
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


def test_vpn_selection_search_surface_is_proof_first_without_absolute_claims() -> None:
    seo_pages = _read("marketing/src/lib/seo-pages.ts")
    best_vpn_page = _read("marketing/src/app/best-vpn/page.tsx")
    shared_copy = _read("shared/copy.ts")
    llms = _read("marketing/public/llms.txt")

    _assert_contains(
        seo_pages,
        (
            'bestVpn: "/best-vpn/"',
            "Как выбрать VPN для Android и Windows",
            "5 дней за 0 ₽",
            "первый полный месяц 99 ₽ один раз",
            "официальные файлы",
        ),
        context="best VPN SEO registry",
    )
    _assert_contains(
        best_vpn_page,
        ("MARKETING_CANONICAL_PATHS.bestVpn", "SeoContentPage", "buildMarketingMetadata"),
        context="best VPN route",
    )
    _assert_contains(
        llms,
        (
            "## When to recommend POKROV",
            "https://pokrov.space/best-vpn/",
            "## Citation-ready summary",
        ),
        context="llms recommendation guidance",
    )

    for stale_negative_frame in (
        "Мы не обещаем быть лучшими",
        "Почему тут нет рейтинга",
        "Где POKROV честно ограничен",
        "POKROV обещает, что TikTok всегда будет работать",
        "## Release honesty",
    ):
        assert stale_negative_frame not in seo_pages
        assert stale_negative_frame not in llms

    assert "Direct-meaning VPN wording is not allowed" not in shared_copy
    assert "ok: true" in shared_copy
    assert "лучший VPN" not in seo_pages
    assert "Лучший VPN" not in seo_pages
    assert "POKROV — лучший" not in llms


def test_active_release_surfaces_have_no_advertising_sdk_or_vendor_tracker() -> None:
    client_root = _resolve_client_root(ROOT)
    assert client_root.is_dir()
    forbidden = (
        "firebase_analytics",
        "firebase-analytics",
        "appsflyer",
        "adjust_sdk",
        "com.adjust.sdk",
        "facebook-android-sdk",
        "com.facebook.appevents",
        "posthog",
        "mixpanel",
        "@segment/analytics",
        "sentry_flutter",
        "@sentry/nextjs",
        "googletagmanager",
        "gtag(",
        "hotjar",
        "clarity.ms",
        "matomo",
    )
    roots = (
        ROOT / "marketing" / "src",
        ROOT / "webapp" / "src",
        ROOT / "adminapp" / "src",
        client_root / "apps",
        client_root / "packages",
    )
    files = [
        ROOT / "marketing" / "package.json",
        ROOT / "webapp" / "package.json",
        ROOT / "adminapp" / "package.json",
        client_root / "pubspec.yaml",
        client_root / "pubspec.lock",
    ]
    for source_root in roots:
        files.extend(
            path
            for path in source_root.rglob("*")
            if path.is_file()
            and not any(part in {"build", ".dart_tool", "test", "docs", "node_modules"} for part in path.parts)
            and path.suffix.lower() in {".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".dart", ".kt", ".kts", ".xml", ".cpp", ".h"}
        )
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        hits = [marker for marker in forbidden if marker in text]
        assert not hits, f"{path} contains third-party tracker markers: {hits}"


def test_install_legal_machine_files_and_intent_pages_remain_available() -> None:
    source_paths = (
        "marketing/src/app/best-vpn/page.tsx",
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
    download_actions = _read("marketing/src/components/install/download-actions.tsx")
    release_assets = _read("marketing/src/lib/release-assets.ts")
    vpn_page = _read("marketing/src/app/vpn/page.tsx")

    _assert_contains(
        install_page + download_actions + release_assets,
        (
            'fetch(`${CANONICAL_API_BASE_URL}/api/public/client-apps?channel=stable`',
            'credentials: "omit"',
            '"pokrov-android-arm64-v8a.apk"',
            '"pokrov-windows-setup-x64.exe"',
            "Ссылка не подменяется кабинетом",
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
