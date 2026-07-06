from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    path: Path
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8", errors="replace")


def _run_checks(checks: list[Check]) -> tuple[int, list[str]]:
    failures: list[str] = []
    for check in checks:
        text = _read(check.path)
        for item in check.must_contain:
            if item not in text:
                failures.append(f"{check.name}: missing `{item}` in {check.path.relative_to(REPO_ROOT)}")
        for item in check.must_not_contain:
            if item in text:
                failures.append(f"{check.name}: unexpected `{item}` in {check.path.relative_to(REPO_ROOT)}")
    return len(failures), failures


def _default_checks() -> list[Check]:
    return [
        Check(
            name="marketing-home-page",
            path=REPO_ROOT / "marketing" / "src" / "app" / "page.tsx",
            must_contain=(
                "buildMarketingMetadata",
                "buildSoftwareApplicationJsonLd",
                "buildFaqJsonLd",
                "<Hero />",
                "<Pricing />",
                "<FinalCta />",
            ),
            must_not_contain=(
                "config.connectUrl",
                "POKROV Network",
                "All except RU",
                "premium trial",
                "raw subscription link",
                "managed premium",
                "app-first",
                "key-first",
                "consumer path",
            ),
        ),
        Check(
            name="marketing-home-shell",
            path=REPO_ROOT / "marketing" / "src" / "components" / "layout" / "page-shell.tsx",
            must_contain=(
                "CANONICAL_WEBAPP_URL",
                "MARKETING_CANONICAL_PATHS.install",
                "<Topbar labels={labels} />",
                'id="main-content"',
            ),
            must_not_contain=("config.connectUrl", "CANONICAL_CONNECT_URL"),
        ),
        Check(
            name="marketing-home-topbar",
            path=REPO_ROOT / "marketing" / "src" / "components" / "layout" / "topbar.tsx",
            must_contain=(
                "MarketingBrandLogo",
                'Link href="/"',
                "aria-expanded={menuOpen}",
                "AnimatePresence",
                "setMenuOpen(false)",
                "labels.cabinetHref",
                "labels.downloadHref",
            ),
            must_not_contain=("data-theme-toggle", "document.documentElement.dataset.theme"),
        ),
        Check(
            name="marketing-home-hero",
            path=REPO_ROOT / "marketing" / "src" / "components" / "home" / "hero.tsx",
            must_contain=(
                "HeroVisual",
                "getSharedProductFacts",
                "getTariffPlans().find",
                "MARKETING_CANONICAL_PATHS.install",
                'href="/#how-it-works"',
            ),
            must_not_contain=("config.connectUrl", "raw subscription link", "managed premium"),
        ),
        Check(
            name="marketing-home-pricing",
            path=REPO_ROOT / "marketing" / "src" / "components" / "home" / "pricing.tsx",
            must_contain=(
                "getTariffPlans()",
                ".filter((plan) => plan.is_active)",
                "MARKETING_CANONICAL_PATHS.checkout",
                "encodeURIComponent(plan.code)",
                "PriceCard",
            ),
            must_not_contain=("CHECKOUT_READY_PLAN_CODES", "start_99 only"),
        ),
        Check(
            name="marketing-home-footer",
            path=REPO_ROOT / "marketing" / "src" / "components" / "layout" / "footer.tsx",
            must_contain=(
                "CANONICAL_WEBAPP_URL",
                "CANONICAL_SUPPORT_BOT_URL",
                "CANONICAL_NEWS_CHANNEL_URL",
                "CANONICAL_GITHUB_RELEASES_URL",
                "MARKETING_CANONICAL_PATHS.offer",
                "MARKETING_CANONICAL_PATHS.privacy",
            ),
            must_not_contain=("config.connectUrl", "CANONICAL_CONNECT_URL"),
        ),
        Check(
            name="marketing-layout-seo",
            path=REPO_ROOT / "marketing" / "src" / "app" / "layout.tsx",
            must_contain=("metadataBase", "manifest", "/favicon.ico", "/apple-icon.png", "JsonLd"),
        ),
        Check(
            name="marketing-checkout-gateway",
            path=REPO_ROOT / "marketing" / "src" / "app" / "checkout" / "checkout-client.tsx",
            must_contain=(
                "config.webappUrl",
                "fetchAccessKeyStatus",
                "fetchPaymentProviderState",
                "buildRedeemHref",
                "/api/payments/providers",
                "/api/payments/orders/create-public",
                "getPricingPreviewDiscountPercent",
                "tariffPlanAllowsDiscount",
                "payment_method: paymentMethod",
                "MARKETING_CANONICAL_PATHS.install",
            ),
            must_not_contain=(
                "config.connectUrl",
                "PORTALcheckout",
                "activation key",
                "All except RU",
                "premium trial",
                "raw subscription link",
                "managed premium",
                "app-first",
                "key-first",
                "First-party promo slots",
                "Support and manual recovery",
                "all_except_ru",
            ),
        ),
        Check(
            name="marketing-offer-flow",
            path=REPO_ROOT / "marketing" / "src" / "app" / "offer" / "page.tsx",
            must_contain=("buildMarketingMetadata", "buildBreadcrumbJsonLd", "MARKETING_CANONICAL_PATHS.mobile", "config.contactEmail"),
            must_not_contain=(
                "/checkout/",
                "PORTAL",
                "activation key",
                "managed-access",
                "app-first",
                "best-effort",
                "production SLA",
                "localhost/control-surface",
            ),
        ),
        Check(
            name="marketing-privacy-flow",
            path=REPO_ROOT / "marketing" / "src" / "app" / "privacy" / "page.tsx",
            must_contain=("buildMarketingMetadata", "buildBreadcrumbJsonLd", "config.contactEmail"),
            must_not_contain=("/checkout/", "PORTAL"),
        ),
        Check(
            name="webapp-entry",
            path=REPO_ROOT / "webapp" / "src" / "app" / "page.tsx",
            must_contain=(
                "PokrovLogo",
                "POKROV cabinet",
                "pokrovBranding.cabinetName",
                "CabinetEntryAuth",
                "href={pokrovBranding.marketingUrl}",
            ),
            must_not_contain=("POKROV Network",),
        ),
        Check(
            name="webapp-local-qr",
            path=REPO_ROOT / "webapp" / "src" / "components" / "subscription-qr-card.tsx",
            must_contain=('import("qrcode")',),
        ),
        Check(
            name="webapp-dashboard-app-first",
            path=REPO_ROOT / "webapp" / "src" / "app" / "(dashboard)" / "dashboard" / "page.tsx",
            must_contain=(
                "resolveTrafficStatusText",
                "StatusHero",
                "GroupedSection",
                'primaryHref = isActive ? "/downloads/" : "/subscription/checkout/"',
                "Button href={primaryHref}",
                'href="/support/"',
            ),
            must_not_contain=("SubscriptionQrCard", "api.qrserver.com", "?format=plain"),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Content-aware UI smoke for marketing and webapp release surfaces.")
    parser.add_argument(
        "--report",
        default=str(REPO_ROOT / "docs" / "audit-artifacts" / "ui-visual-smoke-report.md"),
        help="Path to markdown report.",
    )
    args = parser.parse_args()

    checks = _default_checks()

    fail_count, failures = _run_checks(checks)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# UI Visual Smoke Report",
        "",
        f"- Checks: {len(checks)}",
        f"- FAIL: {fail_count}",
        "",
    ]
    if failures:
        lines.append("## Failures")
        lines.append("")
        for item in failures:
            lines.append(f"- {item}")
    else:
        lines.append("## Result")
        lines.append("")
        lines.append("- PASS")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if failures:
        for item in failures:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1
    print("UI visual smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
