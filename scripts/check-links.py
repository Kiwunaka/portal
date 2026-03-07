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
    return path.read_text(encoding="utf-8")


def _collect_findings() -> list[Finding]:
    findings: list[Finding] = []

    marketing_home = REPO_ROOT / "marketing" / "src" / "app" / "page.tsx"
    marketing_checkout = REPO_ROOT / "marketing" / "src" / "app" / "checkout" / "page.tsx"
    marketing_offer = REPO_ROOT / "marketing" / "src" / "app" / "offer" / "page.tsx"
    marketing_privacy = REPO_ROOT / "marketing" / "src" / "app" / "privacy" / "page.tsx"
    webapp_legal = REPO_ROOT / "webapp" / "src" / "app" / "(dashboard)" / "support" / "legal" / "page.tsx"
    api_file = REPO_ROOT / "portal_bot" / "api.py"

    hardcoded_forbidden = ("portal_privacy_bot", "net4ebur_bot")
    public_files = [marketing_home, marketing_checkout, webapp_legal]
    for path in public_files:
        text = _read(path)
        for bot_name in hardcoded_forbidden:
            if bot_name in text:
                findings.append(Finding("FAIL", str(path.relative_to(REPO_ROOT)), f"Найден жёстко зашитый username бота: {bot_name}"))

    marketing_text = _read(marketing_home)
    if re.search(r'href="/checkout/?', marketing_text):
        findings.append(Finding("FAIL", str(marketing_home.relative_to(REPO_ROOT)), "Cold CTA всё ещё ведёт на /checkout вместо bot-first сценария"))
    else:
        findings.append(Finding("PASS", str(marketing_home.relative_to(REPO_ROOT)), "Cold CTA переведены на bot-first сценарий"))

    for legal_file in (marketing_offer, marketing_privacy):
        legal_text = _read(legal_file)
        if 'href="/checkout/' in legal_text or 'children":"Открыть оплату"' in legal_text:
            findings.append(Finding("FAIL", str(legal_file.relative_to(REPO_ROOT)), "Legal CTA всё ещё ведёт в ticket-only checkout"))
        else:
            findings.append(Finding("PASS", str(legal_file.relative_to(REPO_ROOT)), "Legal CTA переведён в безопасный Telegram flow"))

    webapp_legal_text = _read(webapp_legal)
    for bad_href in ('href="/offer"', 'href="/privacy"', 'href="/offer/"', 'href="/privacy/"'):
        if bad_href in webapp_legal_text:
            findings.append(Finding("FAIL", str(webapp_legal.relative_to(REPO_ROOT)), f"Юридическая ссылка остаётся внутренней для webapp: {bad_href}"))
    if not any(item.level == "FAIL" and item.file.endswith("support\\legal\\page.tsx") for item in findings):
        findings.append(Finding("PASS", str(webapp_legal.relative_to(REPO_ROOT)), "Юридические ссылки webapp указывают на marketing absolute URL"))

    api_text = _read(api_file)
    if 'checkout_mode": "bot_fallback"' not in api_text:
        findings.append(Finding("FAIL", str(api_file.relative_to(REPO_ROOT)), "Admin campaign link builder не помечен как safe bot fallback"))
    else:
        findings.append(Finding("PASS", str(api_file.relative_to(REPO_ROOT)), "Admin campaign link builder переводит public checkout в safe fallback"))

    if "SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED" not in api_text:
        findings.append(Finding("FAIL", str(api_file.relative_to(REPO_ROOT)), "Не найден compat env-flag для numeric subscription fallback"))
    else:
        findings.append(Finding("PASS", str(api_file.relative_to(REPO_ROOT)), "Compat env-flag для numeric subscription fallback подключён"))

    checkout_text = _read(marketing_checkout)
    if "PORTALcheckout" in checkout_text:
        findings.append(Finding("FAIL", str(marketing_checkout.relative_to(REPO_ROOT)), "Checkout heading всё ещё склеивается без визуального разделения"))
    else:
        findings.append(Finding("PASS", str(marketing_checkout.relative_to(REPO_ROOT)), "Checkout heading визуально разделён корректно"))

    return findings


def _write_report(findings: list[Finding], report_path: Path) -> None:
    lines = [
        "# Link Check Report",
        "",
        f"- Проверено файлов: 6",
        f"- FAIL: {sum(1 for item in findings if item.level == 'FAIL')}",
        f"- PASS: {sum(1 for item in findings if item.level == 'PASS')}",
        "",
        "| Статус | Файл | Сообщение |",
        "| --- | --- | --- |",
    ]
    for item in findings:
        lines.append(f"| {item.level} | `{item.file}` | {item.message} |")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate key public CTA and legal links.")
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
