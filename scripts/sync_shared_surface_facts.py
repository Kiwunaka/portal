from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "shared"
COPY_CATALOG_PATH = REPO_ROOT / "copy" / "catalog.ru.json"
MARKETING_GOVERNANCE_PATH = (
    SHARED_DIR / "contracts" / "marketing" / "marketing-governance.v1.json"
)
POKROV_APP_ROOT = REPO_ROOT.parent / "POKROV-app"
DEFAULT_BRIDGE_TARGET = (
    REPO_ROOT
    / "external"
    / "client-fork"
    / "app"
    / "lib"
    / "features"
    / "portal"
    / "config"
    / "shared_surface_facts.dart"
)
DEFAULT_POKROV_APP_TARGETS = {
    "product_contract": POKROV_APP_ROOT / "config" / "product-contract.seed.json",
    "runtime_profile": POKROV_APP_ROOT / "config" / "runtime-profile.seed.json",
    "platform_matrix": POKROV_APP_ROOT / "config" / "platform-matrix.seed.json",
}


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"object required: {path}")
    return value


def _read_json(name: str) -> dict[str, Any]:
    return _read_object(SHARED_DIR / name)


def _canonical_text_sha256(path: Path) -> str:
    canonical = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _shared_sha256(name: str) -> str:
    return _canonical_text_sha256(SHARED_DIR / name)


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


def build_pokrov_app_updates(
    product: dict[str, Any],
    public_urls: dict[str, Any],
    commercial: dict[str, Any],
    copy_catalog: dict[str, Any],
    marketing_governance: dict[str, Any],
    public_urls_sha256: str,
    copy_catalog_sha256: str,
) -> dict[str, dict[str, Any]]:
    readiness_only = _expand_readiness_targets(
        list(product["platform_scope"]["readiness_only"])
    )
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
            "platform_authority": {
                "product_facts_contract": "shared/product-facts.json",
                "product_facts_sha256": commercial["source_sha256"]["product_facts"],
                "public_urls_contract": "shared/public-urls.json",
                "public_urls_sha256": public_urls_sha256,
                "commercial_contract": "shared/commercial-contract.json",
                "commercial_revision": commercial["commercial_revision"],
                "commercial_contract_sha256": commercial["contract_sha256"],
                "tariff_catalog_contract": "shared/tariff-catalog.json",
                "tariff_catalog_sha256": commercial["source_sha256"]["tariff_catalog"],
                "copy_catalog_contract": "copy/catalog.ru.json",
                "copy_catalog_version": copy_catalog["catalog_version"],
                "copy_catalog_sha256": copy_catalog_sha256,
                "marketing_governance_contract": "shared/contracts/marketing/marketing-governance.v1.json",
                "marketing_governance_revision": marketing_governance["revision"],
                "marketing_governance_contract_sha256": marketing_governance[
                    "contract_sha256"
                ],
            },
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


def build_pokrov_app_product_facts_dart(
    product: dict[str, Any],
    public_urls: dict[str, Any],
    commercial: dict[str, Any],
    public_urls_sha256: str,
) -> str:
    readiness_only = _expand_readiness_targets(
        list(product["platform_scope"]["readiness_only"])
    )
    runtime_cores = {"sing-box": "RuntimeCore.singBox", "xray": "RuntimeCore.xray"}
    route_modes = {"all_except_ru": "RouteMode.allExceptRu"}
    client_platforms = {
        "android": "ClientPlatform.android",
        "windows": "ClientPlatform.windows",
        "ios": "ClientPlatform.ios",
        "macos": "ClientPlatform.macos",
    }
    public_target_lines = [
        f"    {client_platforms[item]}," for item in product["platform_scope"]["public"]
    ]
    readiness_target_lines = [
        f"    {client_platforms[item]}," for item in readiness_only
    ]
    return "\n".join(
        [
            "// Generated from platform shared facts via scripts/sync_shared_surface_facts.py.",
            "// Do not edit this projection by hand.",
            "",
            "import 'package:pokrov_core_domain/core_domain.dart';",
            "",
            "abstract final class PlatformProductFacts {",
            "  static const productFactsSha256 =",
            f"      {_quoted(commercial['source_sha256']['product_facts'])};",
            "  static const publicUrlsSha256 =",
            f"      {_quoted(public_urls_sha256)};",
            f"  static const commercialRevision = {_quoted(commercial['commercial_revision'])};",
            "  static const commercialContractSha256 =",
            f"      {_quoted(commercial['contract_sha256'])};",
            "  static const tariffCatalogSha256 =",
            f"      {_quoted(commercial['source_sha256']['tariff_catalog'])};",
            f"  static const trialDays = {int(product['trial']['days'])};",
            f"  static const telegramRewardDays = {int(product['telegram_reward']['days'])};",
            f"  static const referralFriendDays = {int(product['referral_reward']['friend_days'])};",
            f"  static const referralReferrerDays = {int(product['referral_reward']['referrer_days'])};",
            f"  static const referralHoldHours = {int(product['referral_reward']['referrer_hold_hours'])};",
            f"  static const defaultRuntimeCore = {runtime_cores[product['engines']['default']]};",
            f"  static const advancedFallbackCore = {runtime_cores[product['engines']['advanced_fallback']]};",
            f"  static const defaultRouteMode = {route_modes[product['network_defaults']['routing_mode_default']]};",
            "  static const publicReleaseTargets = <ClientPlatform>[",
            *public_target_lines,
            "  ];",
            "  static const readinessOnlyTargets = <ClientPlatform>[",
            *readiness_target_lines,
            "  ];",
            f"  static const offerPath = {_quoted(product['legal']['offer_path'])};",
            f"  static const privacyPath = {_quoted(product['legal']['privacy_path'])};",
            f"  static const offerUrl = {_quoted(public_urls['legal']['offer'])};",
            f"  static const privacyUrl = {_quoted(public_urls['legal']['privacy'])};",
            f"  static const githubReleasesUrl = {_quoted(public_urls['releases']['github_releases'])};",
            f"  static const supportBot = {_quoted(public_urls['telegram']['support_bot_username'])};",
            f"  static const feedbackBot = {_quoted(public_urls['telegram']['feedback_bot_username'])};",
            f"  static const publicChannel = {_quoted(public_urls['telegram']['channel_username'])};",
            f"  static const supportEmail = {_quoted(public_urls['contact']['support_email'])};",
            "}",
            "",
        ]
    )


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def build_pokrov_app_copy_contract_document(
    commercial: dict[str, Any],
    copy_catalog: dict[str, Any],
    marketing_governance: dict[str, Any],
    public_urls_sha256: str,
    copy_catalog_sha256: str,
) -> str:
    items = copy_catalog.get("items")
    if not isinstance(items, dict):
        raise SystemExit("copy catalog items must be an object")

    family_counts: dict[str, dict[str, int]] = {}
    app_items: list[tuple[str, dict[str, Any]]] = []
    for key, raw in sorted(items.items()):
        if not isinstance(key, str) or not isinstance(raw, dict):
            raise SystemExit("copy catalog entries must be keyed objects")
        family = key.split(".", 1)[0]
        counts = family_counts.setdefault(family, {"entries": 0, "public": 0})
        counts["entries"] += 1
        if raw.get("allowed_public") is True:
            counts["public"] += 1
        if family == "app":
            app_items.append((key, raw))

    lines = [
        "# Generated Platform Copy Contract",
        "",
        "Generated by the platform `scripts/sync_shared_surface_facts.py`. Do not edit by hand.",
        "",
        "This file maps copy ownership for the active client. It is a digest-pinned reference, not a second source of product, price, claim, or launch truth.",
        "",
        f"- product facts SHA-256: `{commercial['source_sha256']['product_facts']}`",
        f"- public URLs SHA-256: `{public_urls_sha256}`",
        f"- commercial revision: `{commercial['commercial_revision']}`",
        f"- commercial contract SHA-256: `{commercial['contract_sha256']}`",
        f"- copy catalog: `{copy_catalog['catalog_version']}` / `{copy_catalog_sha256}`",
        f"- marketing governance: `{marketing_governance['revision']}` / `{marketing_governance['contract_sha256']}`",
        f"- legal launch ready: `{str(bool(commercial['legal']['launch_ready'])).lower()}`",
        f"- campaign launch state: `{marketing_governance['default_campaign_launch_state']}`",
        "",
        "## Authority map",
        "",
        "| Family | Canonical owner | Active-client rule |",
        "| --- | --- | --- |",
        "| Product, trial, reward, scope, and legal paths | `shared/product-facts.json` | Generated seed and typed Dart projection may be consumed at runtime. |",
        "| Public destinations | `shared/public-urls.json` | Generated URLs may be consumed at runtime. Availability still requires separate live evidence. |",
        "| Base plans, prices, promo results, legal state, and capacity | `shared/commercial-contract.json` plus server responses | The client pins the revision and digest. It must render server values and must not calculate authoritative prices or eligibility. |",
        "| Platform copy catalog | `copy/catalog.ru.json` through `shared/copy.ts` | Platform consumers use the catalog. The client receives the `app.*` baseline below for reconciliation, not a bulk runtime import. |",
        "| Public claims and campaign channels | `shared/contracts/marketing/marketing-governance.v1.json` | This governs public acquisition copy. It does not approve client copy or unblock a campaign. |",
        "| Client operational and recovery copy | `POKROV-app/packages/app_shell/` plus client copy tests | Client-owned wording may vary by state, but it must not contradict the pinned platform facts or invent price, promo, availability, signing, or launch claims. |",
        "",
        "## Catalog namespace coverage",
        "",
        "| Namespace | Entries | Public entries |",
        "| --- | ---: | ---: |",
    ]
    for family, counts in sorted(family_counts.items()):
        lines.append(f"| `{family}` | {counts['entries']} | {counts['public']} |")

    lines.extend(
        [
            "",
            "## Active-client catalog baseline",
            "",
            "These `app.*` entries are review baselines. They are not a replacement for state-specific client wording.",
            "",
            "| Key | Russian baseline | Tone |",
            "| --- | --- | --- |",
        ]
    )
    for key, raw in app_items:
        lines.append(
            f"| `{key}` | {_markdown_cell(raw.get('ru'))} | `{_markdown_cell(raw.get('tone'))}` |"
        )

    lines.extend(
        [
            "",
            "The active-client seed pins every platform owner listed above. `validate-seed.ps1` runs the platform synchronizer with `--check`, so digest, generated-document, typed-projection, hardcoded-product-fact, and runtime-consumer drift fails closed without rewriting files.",
            "",
            "Repository consistency is local evidence only. It does not prove legal approval, campaign authorization, deployed copy, public URL availability, provider prices, signing, store publication, or an exact release candidate.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_pokrov_app_product_fact_consumers(pokrov_app_root: Path) -> None:
    source_root = pokrov_app_root / "packages" / "app_shell" / "lib"
    production_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(source_root.rglob("*.dart"))
        if path.name != "platform_product_facts.g.dart"
    )
    product = _read_json("product-facts.json")
    telegram_days = int(product["telegram_reward"]["days"])
    trial_days = int(product["trial"]["days"])
    forbidden = (
        f"Telegram +{telegram_days}",
        f"+{telegram_days} дней за Telegram",
        f"startsWith('{trial_days} '",
    )
    found = [literal for literal in forbidden if literal in production_source]
    if found:
        raise SystemExit(
            "hardcoded platform product facts in POKROV-app production Dart: "
            + ", ".join(found)
        )

    hardcoded_prices = sorted(
        set(
            match.group(0)
            for match in re.finditer(
                r"(?i)(?:\b\d[\d _]*\s*(?:₽|руб\.?|RUB)\b|₽\s*\d)",
                production_source,
            )
        )
    )
    if hardcoded_prices:
        raise SystemExit(
            "hardcoded client price facts in POKROV-app production Dart: "
            + ", ".join(hardcoded_prices)
        )

    copy_source = (
        source_root / "src" / "shared" / "platform_product_copy.dart"
    ).read_text(encoding="utf-8")
    profile_source = (
        source_root / "src" / "features" / "profile" / "profile_surface.dart"
    ).read_text(encoding="utf-8")
    seed_source = (
        source_root / "src" / "seed" / "seed_context.dart"
    ).read_text(encoding="utf-8")
    subscription_source = (
        source_root / "app_first_runtime_bootstrap.dart"
    ).read_text(encoding="utf-8")
    required_copy_tokens = (
        "PlatformProductFacts.trialDays",
        "PlatformProductFacts.telegramRewardDays",
    )
    required_profile_tokens = (
        "PlatformProductFacts.offerUrl",
        "PlatformProductFacts.privacyUrl",
        "PlatformProductFacts.githubReleasesUrl",
        "plan.price",
    )
    required_seed_tokens = (
        "PlatformProductFacts.trialDays",
        "PlatformProductFacts.telegramRewardDays",
        "PlatformProductFacts.publicReleaseTargets",
        "PlatformProductFacts.readinessOnlyTargets",
    )
    required_subscription_tokens = (
        "price: _clientText(json['price'])",
    )
    missing = [
        token
        for tokens, source in (
            (required_copy_tokens, copy_source),
            (required_profile_tokens, profile_source),
            (required_seed_tokens, seed_source),
            (required_subscription_tokens, subscription_source),
        )
        for token in tokens
        if token not in source
    ]
    if missing:
        raise SystemExit(
            "missing generated platform product-fact consumers: " + ", ".join(missing)
        )


def _render_json_target(path: Path, updates: dict[str, Any]) -> str:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    merged = _merge_dict(existing, updates)
    return json.dumps(merged, ensure_ascii=False, indent=2) + "\n"


def _write_or_check(path: Path, expected: str, *, check: bool) -> None:
    if check:
        if (
            not path.exists()
            or path.read_text(encoding="utf-8").replace("\r\n", "\n") != expected
        ):
            raise SystemExit(f"shared fact projection drift: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8")


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
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify exact generated projections without writing files.",
    )
    args = parser.parse_args()

    product = _read_json("product-facts.json")
    public_urls = _read_json("public-urls.json")
    public_urls_sha256 = _shared_sha256("public-urls.json")
    commercial = _read_json("commercial-contract.json")
    copy_catalog = _read_object(COPY_CATALOG_PATH)
    marketing_governance = _read_object(MARKETING_GOVERNANCE_PATH)
    copy_catalog_sha256 = _canonical_text_sha256(COPY_CATALOG_PATH)
    if marketing_governance.get("copy_catalog_sha256") != copy_catalog_sha256:
        raise SystemExit(
            "marketing governance copy-catalog digest does not match copy/catalog.ru.json"
        )

    if args.target_lane in {"pokrov-app", "both"}:
        pokrov_app_root = Path(args.pokrov_app_root)
        targets = {
            "product_contract": pokrov_app_root
            / "config"
            / "product-contract.seed.json",
            "runtime_profile": pokrov_app_root / "config" / "runtime-profile.seed.json",
            "platform_matrix": pokrov_app_root / "config" / "platform-matrix.seed.json",
        }
        for key, updates in build_pokrov_app_updates(
            product,
            public_urls,
            commercial,
            copy_catalog,
            marketing_governance,
            public_urls_sha256,
            copy_catalog_sha256,
        ).items():
            _write_or_check(
                targets[key],
                _render_json_target(targets[key], updates),
                check=args.check,
            )
        runtime_dart = (
            pokrov_app_root
            / "packages"
            / "app_shell"
            / "lib"
            / "src"
            / "seed"
            / "platform_product_facts.g.dart"
        )
        _write_or_check(
            runtime_dart,
            build_pokrov_app_product_facts_dart(
                product, public_urls, commercial, public_urls_sha256
            ),
            check=args.check,
        )
        copy_contract_document = (
            pokrov_app_root / "docs" / "generated" / "platform-copy-contract.md"
        )
        _write_or_check(
            copy_contract_document,
            build_pokrov_app_copy_contract_document(
                commercial,
                copy_catalog,
                marketing_governance,
                public_urls_sha256,
                copy_catalog_sha256,
            ),
            check=args.check,
        )
        validate_pokrov_app_product_fact_consumers(pokrov_app_root)

    if args.target_lane in {"bridge", "both"}:
        _write_or_check(
            Path(args.bridge_target),
            build_bridge_dart(product, public_urls),
            check=args.check,
        )


if __name__ == "__main__":
    main()
