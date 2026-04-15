from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Finding:
    level: str
    file: str
    message: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _add_pass(findings: list[Finding], path: Path, message: str) -> None:
    findings.append(Finding("PASS", str(path.relative_to(REPO_ROOT)), message))


def _add_fail(findings: list[Finding], path: Path, message: str) -> None:
    findings.append(Finding("FAIL", str(path.relative_to(REPO_ROOT)), message))


def _collect_findings() -> list[Finding]:
    findings: list[Finding] = []

    marketing_root = REPO_ROOT / "marketing" / "src"
    marketing_landing = marketing_root / "components" / "marketing-landing.tsx"
    marketing_layout = marketing_root / "app" / "layout.tsx"
    marketing_checkout = marketing_root / "app" / "checkout" / "checkout-client.tsx"
    marketing_offer = marketing_root / "app" / "offer" / "page.tsx"
    marketing_privacy = marketing_root / "app" / "privacy" / "page.tsx"
    marketing_robots = marketing_root / "app" / "robots.ts"
    marketing_sitemap = marketing_root / "app" / "sitemap.ts"
    marketing_manifest = marketing_root / "app" / "manifest.ts"
    marketing_og = REPO_ROOT / "marketing" / "public" / "opengraph-image.png"
    marketing_twitter = REPO_ROOT / "marketing" / "public" / "twitter-image.png"
    marketing_favicon = REPO_ROOT / "marketing" / "public" / "favicon.ico"
    marketing_apple_icon = REPO_ROOT / "marketing" / "public" / "apple-icon.png"
    webapp_legal = REPO_ROOT / "webapp" / "src" / "app" / "(dashboard)" / "support" / "legal" / "page.tsx"
    api_file = REPO_ROOT / "portal_bot" / "api.py"

    for path in (
        marketing_robots,
        marketing_sitemap,
        marketing_manifest,
        marketing_og,
        marketing_twitter,
        marketing_favicon,
        marketing_apple_icon,
    ):
        if path.exists():
            _add_pass(findings, path, "Marketing SEO route is present")
        else:
            _add_fail(findings, path, "Missing marketing SEO route")

    landing_text = _read(marketing_landing)
    if "href={config.connectUrl}" in landing_text:
        _add_fail(findings, marketing_landing, "Public marketing CTA still routes to connect host")
    else:
        _add_pass(findings, marketing_landing, "Public marketing CTA no longer routes to connect host")

    if "config.webappUrl" in landing_text:
        _add_pass(findings, marketing_landing, "Public cabinet CTA points to webapp host")
    else:
        _add_fail(findings, marketing_landing, "Public cabinet CTA is not wired to webapp host")

    if '"/checkout/?plan=${encodeURIComponent(planCode)}"' in landing_text or 'return `/checkout/?plan=${encodeURIComponent(planCode)}`;' in landing_text:
        _add_pass(findings, marketing_landing, "Pricing CTA routes through public checkout gateway")
    else:
        _add_fail(findings, marketing_landing, "Pricing CTA does not route through public checkout gateway")

    if "config.newsChannelUrl" in landing_text:
        _add_pass(findings, marketing_landing, "Marketing footer exposes canonical news channel")
    else:
        _add_fail(findings, marketing_landing, "Marketing footer misses canonical news channel")

    layout_text = _read(marketing_layout)
    for required in ("metadataBase", "manifest", "icons", "apple", "/favicon.ico", "/apple-icon.png"):
        if required in layout_text:
            _add_pass(findings, marketing_layout, f"Layout includes `{required}` metadata wiring")
        else:
            _add_fail(findings, marketing_layout, f"Layout misses `{required}` metadata wiring")

    for required in ("alternates", "canonical", "twitter", "images"):
        if required in landing_text:
            _add_pass(findings, marketing_landing, f"Marketing metadata declares `{required}`")
        else:
            _add_fail(findings, marketing_landing, f"Marketing metadata misses `{required}`")

    checkout_text = _read(marketing_checkout)
    if "config.connectUrl" in checkout_text:
        _add_fail(findings, marketing_checkout, "Checkout gateway still falls back to connect host")
    else:
        _add_pass(findings, marketing_checkout, "Checkout gateway uses cabinet-safe fallback instead of connect host")

    for legal_file in (marketing_offer, marketing_privacy):
        legal_text = _read(legal_file)
        if 'href="/checkout/' in legal_text:
            _add_fail(findings, legal_file, "Legal page still links directly into checkout")
        else:
            _add_pass(findings, legal_file, "Legal page avoids direct checkout CTA")

    webapp_legal_text = _read(webapp_legal)
    for bad_href in ('href="/offer"', 'href="/privacy"', 'href="/offer/"', 'href="/privacy/"'):
        if bad_href in webapp_legal_text:
            _add_fail(findings, webapp_legal, f"Webapp legal page still uses internal marketing link: {bad_href}")
    if not any(item.level == "FAIL" and item.file.endswith("support\\legal\\page.tsx") for item in findings):
        _add_pass(findings, webapp_legal, "Webapp legal links use absolute marketing URLs")

    api_text = _read(api_file)
    if 'checkout_mode": "bot_fallback"' not in api_text:
        _add_fail(findings, api_file, "Admin campaign link builder is not marked as safe bot fallback")
    else:
        _add_pass(findings, api_file, "Admin campaign link builder marks public checkout as safe fallback")

    if "SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED" not in api_text:
        _add_fail(findings, api_file, "Missing compat env-flag for numeric subscription fallback")
    else:
        _add_pass(findings, api_file, "Compat env-flag for numeric subscription fallback is present")

    return findings


def _write_report(findings: list[Finding], report_path: Path) -> None:
    lines = [
        "# Link Check Report",
        "",
        f"- FAIL: {sum(1 for item in findings if item.level == 'FAIL')}",
        f"- PASS: {sum(1 for item in findings if item.level == 'PASS')}",
        "",
        "| Status | File | Message |",
        "| --- | --- | --- |",
    ]
    for item in findings:
        lines.append(f"| {item.level} | `{item.file}` | {item.message} |")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public CTA, legal, and SEO routing for release.")
    parser.add_argument(
        "--report",
        default=str(REPO_ROOT / "docs" / "audit-artifacts" / "link-check-report.md"),
        help="Path to the markdown report.",
    )
    args = parser.parse_args()

    findings = _collect_findings()
    _write_report(findings, Path(args.report))

    fail_count = sum(1 for item in findings if item.level == "FAIL")
    for item in findings:
        print(f"[{item.level}] {item.file}: {item.message}")
    if fail_count:
        print(f"\nLink check failed: {fail_count} issue(s) found.", file=sys.stderr)
        return 1
    print("\nLink check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
