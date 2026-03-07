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


def main() -> int:
    parser = argparse.ArgumentParser(description="Content-aware UI smoke for exported marketing/webapp artifacts.")
    parser.add_argument(
        "--report",
        default=str(REPO_ROOT / "docs" / "audit-artifacts" / "ui-visual-smoke-report.md"),
        help="Path to markdown report.",
    )
    args = parser.parse_args()

    checks = [
        Check(
            name="marketing-home-cta",
            path=REPO_ROOT / "marketing" / "src" / "app" / "page.tsx",
            must_contain=("Подключиться в Telegram", "Сравнить планы", "Уже подключены?"),
            must_not_contain=("Открыть Telegram",),
        ),
        Check(
            name="marketing-offer-flow",
            path=REPO_ROOT / "marketing" / "src" / "app" / "offer" / "page.tsx",
            must_contain=("Продолжить в Telegram",),
            must_not_contain=("/checkout/", "Открыть оплату"),
        ),
        Check(
            name="marketing-checkout-gateway",
            path=REPO_ROOT / "marketing" / "src" / "app" / "checkout" / "page.tsx",
            must_contain=("Продолжение через Telegram", "Получить персональную ссылку в Telegram"),
            must_not_contain=("PORTALcheckout",),
        ),
        Check(
            name="webapp-entry",
            path=REPO_ROOT / "webapp" / "src" / "app" / "page.tsx",
            must_contain=("portal entry", "Продолжить вход в PORTAL", "Очистить веб-вход"),
        ),
        Check(
            name="webapp-local-qr",
            path=REPO_ROOT / "webapp" / "src" / "components" / "subscription-qr-card.tsx",
            must_contain=('import("qrcode")',),
        ),
        Check(
            name="webapp-dashboard-qr-usage",
            path=REPO_ROOT / "webapp" / "src" / "app" / "(dashboard)" / "dashboard" / "page.tsx",
            must_contain=("SubscriptionQrCard",),
            must_not_contain=("api.qrserver.com",),
        ),
    ]

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
