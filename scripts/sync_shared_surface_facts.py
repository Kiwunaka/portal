from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "shared"
TARGET = REPO_ROOT / "external" / "client-fork" / "app" / "lib" / "features" / "portal" / "config" / "shared_surface_facts.dart"


def _read_json(name: str) -> dict:
    return json.loads((SHARED_DIR / name).read_text(encoding="utf-8"))


def _quoted(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _dart_list(items: list[str]) -> str:
    return "<String>[" + ", ".join(_quoted(item) for item in items) + "]"


def build_dart() -> str:
    product = _read_json("product-facts.json")
    public_urls = _read_json("public-urls.json")

    return "\n".join(
        [
            "// Generated from shared/*.json via scripts/sync_shared_surface_facts.py.",
            "",
            "class PortalSharedProductFacts {",
            f"  static const platformBrand = {_quoted(product['brands']['platform'])};",
            f"  static const clientBrand = {_quoted(product['brands']['client'])};",
            f"  static const canonicalTrialDays = {int(product['trial']['days'])};",
            f"  static const telegramRewardDays = {int(product['telegram_reward']['days'])};",
            f"  static const publicPlatformScope = {_dart_list(product['platform_scope']['public'])};",
            f"  static const readinessOnlyPlatforms = {_dart_list(product['platform_scope']['readiness_only'])};",
            "}",
            "",
            "class PortalSharedPublicUrls {",
            f"  static const marketing = {_quoted(public_urls['surfaces']['marketing'])};",
            f"  static const webapp = {_quoted(public_urls['surfaces']['webapp'])};",
            f"  static const api = {_quoted(public_urls['surfaces']['api'])};",
            f"  static const connect = {_quoted(public_urls['surfaces']['connect'])};",
            f"  static const checkout = {_quoted(public_urls['surfaces']['checkout'])};",
            f"  static const bot = {_quoted(public_urls['telegram']['bot'])};",
            f"  static const supportBot = {_quoted(public_urls['telegram']['support_bot'])};",
            f"  static const feedbackBot = {_quoted(public_urls['telegram']['feedback_bot'])};",
            f"  static const newsChannel = {_quoted(public_urls['telegram']['channel'])};",
            f"  static const supportEmail = {_quoted(public_urls['contact']['support_email'])};",
            f"  static const enterpriseEmail = {_quoted(public_urls['contact']['enterprise_email'])};",
            "}",
            "",
        ]
    )


def main() -> None:
    TARGET.write_text(build_dart(), encoding="utf-8")


if __name__ == "__main__":
    main()
