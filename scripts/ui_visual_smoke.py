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
            name="marketing-home-cta",
            path=REPO_ROOT / "marketing" / "src" / "components" / "marketing-landing.tsx",
            must_contain=(
                "POKROV",
                "config.webappUrl",
                "config.newsChannelUrl",
                "/checkout/?plan=",
                "lp-hero-stage",
                "lp-trust-grid",
                "lp-pricing-shell",
                "lp-footer-cta",
                '<details className="lp-faq-item">',
            ),
            must_not_contain=("href={config.connectUrl}", "POKROV Network"),
        ),
        Check(
            name="marketing-layout-seo",
            path=REPO_ROOT / "marketing" / "src" / "app" / "layout.tsx",
            must_contain=("metadataBase", "manifest", "/favicon.ico", "/apple-icon.png", "JsonLd"),
        ),
        Check(
            name="marketing-checkout-gateway",
            path=REPO_ROOT / "marketing" / "src" / "app" / "checkout" / "checkout-client.tsx",
            must_contain=("config.webappUrl", "Продолжить в Telegram", "Открыть кабинет"),
            must_not_contain=("config.connectUrl", "PORTALcheckout"),
        ),
        Check(
            name="marketing-offer-flow",
            path=REPO_ROOT / "marketing" / "src" / "app" / "offer" / "page.tsx",
            must_contain=("Открыть Telegram-бота", "Публичная оферта"),
            must_not_contain=("/checkout/", "PORTAL"),
        ),
        Check(
            name="marketing-privacy-flow",
            path=REPO_ROOT / "marketing" / "src" / "app" / "privacy" / "page.tsx",
            must_contain=("Политика конфиденциальности", "config.contactEmail"),
            must_not_contain=("/checkout/", "PORTAL"),
        ),
        Check(
            name="webapp-entry",
            path=REPO_ROOT / "webapp" / "src" / "app" / "page.tsx",
            must_contain=(
                "PokrovLogo",
                "POKROV cabinet",
                "pokrovBranding.entryEyebrow",
                "CabinetEntryAuth",
                "href={pokrovBranding.marketingUrl}",
            ),
            must_not_contain=("Продолжить вход в PORTAL", "POKROV Network"),
        ),
        Check(
            name="webapp-local-qr",
            path=REPO_ROOT / "webapp" / "src" / "components" / "subscription-qr-card.tsx",
            must_contain=('import("qrcode")', "QR-код ссылки подключения"),
        ),
        Check(
            name="webapp-dashboard-app-first",
            path=REPO_ROOT / "webapp" / "src" / "app" / "(dashboard)" / "dashboard" / "page.tsx",
            must_contain=(
                "fetchNodeStatus",
                "resolveTrafficStatusText",
                "CabinetHero",
                'href="/downloads/"',
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
