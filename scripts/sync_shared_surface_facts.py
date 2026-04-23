from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "shared"
POKROV_APP_ROOT = REPO_ROOT.parent / "POKROV-app"
DEFAULT_BRIDGE_TARGET = REPO_ROOT / "external" / "client-fork" / "app" / "lib" / "features" / "portal" / "config" / "shared_surface_facts.dart"
DEFAULT_POKROV_APP_TARGETS = {
    "product_contract": POKROV_APP_ROOT / "config" / "product-contract.seed.json",
    "runtime_profile": POKROV_APP_ROOT / "config" / "runtime-profile.seed.json",
    "platform_matrix": POKROV_APP_ROOT / "config" / "platform-matrix.seed.json",
}


def _read_json(name: str) -> dict[str, Any]:
    return json.loads((SHARED_DIR / name).read_text(encoding="utf-8"))


def _quoted(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _dart_list(items: list[str]) -> str:
    return "<String>[" + ", ".join(_quoted(item) for item in items) + "]"


def build_bridge_dart(product: dict[str, Any], public_urls: dict[str, Any]) -> str:
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


def _expand_readiness_targets(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for item in values:
        if item == "apple":
            for platform in ("ios", "macos"):
                if platform not in expanded:
                    expanded.append(platform)
            continue
        if item not in expanded:
            expanded.append(item)
    return expanded


def _merge_dict(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def build_pokrov_app_updates(product: dict[str, Any], public_urls: dict[str, Any]) -> dict[str, dict[str, Any]]:
    readiness_only = _expand_readiness_targets(list(product["platform_scope"]["readiness_only"]))
    return {
        "product_contract": {
            "brand": product["brands"]["platform"],
            "public_product_line": product["brands"]["client"],
            "client_strategy": product["strategy"]["client"],
            "identity_model": product["strategy"]["identity_model"],
            "public_scope": list(product["platform_scope"]["public"]),
            "readiness_only_scope": readiness_only,
            "default_runtime_core": product["engines"]["default"],
            "advanced_fallback_core": product["engines"]["advanced_fallback"],
            "trial_days": int(product["trial"]["days"]),
            "telegram_bonus_days": int(product["telegram_reward"]["days"]),
            "recovery_order": list(product["versions"]["support_recovery_order"]),
            "support_surfaces": [
                public_urls["telegram"]["support_bot_username"],
                public_urls["contact"]["support_email"],
            ],
        },
        "runtime_profile": {
            "brand": product["brands"]["platform"],
            "client_strategy": product["strategy"]["client"],
            "identity_model": product["strategy"]["identity_model"],
            "default_runtime_core": product["engines"]["default"],
            "advanced_fallback_core": product["engines"]["advanced_fallback"],
            "trial_days": int(product["trial"]["days"]),
            "telegram_bonus_days": int(product["telegram_reward"]["days"]),
            "official_surfaces": {
                "app": public_urls["surfaces"]["webapp"],
                "api": public_urls["surfaces"]["api"],
                "connect": public_urls["surfaces"]["connect"],
                "checkout": public_urls["surfaces"]["checkout"],
            },
            "support_surfaces": [
                public_urls["telegram"]["support_bot_username"],
                public_urls["telegram"]["feedback_bot_username"],
            ],
        },
        "platform_matrix": {
            "public_release_targets": list(product["platform_scope"]["public"]),
            "readiness_only_targets": readiness_only,
        },
    }


def _write_json_target(path: Path, updates: dict[str, Any]) -> None:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    merged = _merge_dict(existing, updates)
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync shared root facts into the canonical POKROV-app seed config lane and optional legacy bridge compatibility target."
    )
    parser.add_argument(
        "--target-lane",
        choices=("pokrov-app", "bridge", "both"),
        default="pokrov-app",
        help="Where to write generated shared facts.",
    )
    parser.add_argument(
        "--pokrov-app-root",
        default=str(POKROV_APP_ROOT),
        help="Root path for the canonical POKROV-app checkout.",
    )
    parser.add_argument(
        "--bridge-target",
        default=str(DEFAULT_BRIDGE_TARGET),
        help="Legacy bridge Dart target used only for compatibility syncs.",
    )
    args = parser.parse_args()

    product = _read_json("product-facts.json")
    public_urls = _read_json("public-urls.json")

    if args.target_lane in {"pokrov-app", "both"}:
        pokrov_app_root = Path(args.pokrov_app_root)
        targets = {
            "product_contract": pokrov_app_root / "config" / "product-contract.seed.json",
            "runtime_profile": pokrov_app_root / "config" / "runtime-profile.seed.json",
            "platform_matrix": pokrov_app_root / "config" / "platform-matrix.seed.json",
        }
        for key, updates in build_pokrov_app_updates(product, public_urls).items():
            _write_json_target(targets[key], updates)

    if args.target_lane in {"bridge", "both"}:
        Path(args.bridge_target).write_text(build_bridge_dart(product, public_urls), encoding="utf-8")


if __name__ == "__main__":
    main()
