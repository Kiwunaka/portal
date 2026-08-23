from __future__ import annotations

import hashlib
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"

if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def test_shared_surface_fact_loaders_expose_canonical_product_and_url_truth():
    shared_surface_facts = importlib.import_module("shared_surface_facts")

    product = shared_surface_facts.get_product_facts()
    urls = shared_surface_facts.get_public_urls()
    design = shared_surface_facts.get_design_tokens()
    commercial = shared_surface_facts.get_commercial_contract()

    assert product["brands"]["platform"] == "POKROV"
    assert product["brands"]["client"] == "POKROV"
    assert product["trial"]["days"] == 5
    assert product["telegram_reward"]["days"] == 5
    assert product["telegram_reward"]["grandfathered_days"] == 10
    assert product["platform_scope"]["public"] == ["android", "windows"]
    assert product["network_defaults"]["routing_mode_default"] == "all_except_ru"
    assert (
        product["network_defaults"]["transport_profile_default"]
        == "legacy_reality_fallback"
    )
    assert product["network_defaults"]["dns_policy_default"] == "ru_direct_split"
    assert product["versions"]["ruleset_version"]
    assert product["versions"]["package_catalog_version"]
    assert product["versions"]["client_transport_baseline"] == "legacy_reality_fallback"
    assert product["versions"]["support_recovery_order"] == ["app", "web", "telegram"]

    assert urls["surfaces"]["marketing"] == "https://pokrov.space/"
    assert urls["surfaces"]["webapp"] == "https://app.pokrov.space/"
    assert urls["surfaces"]["api"] == "https://api.pokrov.space/"
    assert urls["surfaces"]["connect"] == "https://connect.pokrov.space/"
    assert urls["surfaces"]["checkout"] == "https://pay.pokrov.space/checkout/"
    assert urls["telegram"]["channel_username"] == "@pokrov_vpn"

    assert design["theme"]["name"] == "pokrov-clear"
    assert design["glass"]["content_planes"] == "solid"
    assert design["motion"]["reduced_motion_fallback"] == "fade-only"

    assert commercial["commercial_revision"] == "2026-08-21.1"
    assert commercial["price_authority"] == "server_commercial_contract"
    assert commercial["capacity_policy"]["limit_units"] == 300
    assert commercial["legal"]["launch_ready"] is False


def test_public_url_helpers_use_shared_public_url_defaults(monkeypatch):
    monkeypatch.delenv("PUBLIC_CONNECT_URL", raising=False)
    monkeypatch.delenv("PUBLIC_CONNECT_DOMAIN", raising=False)

    shared_surface_facts = importlib.import_module("shared_surface_facts")
    public_urls = importlib.import_module("public_urls")

    shared_surface_facts.clear_shared_surface_fact_caches()

    assert public_urls.public_connect_base_url() == "https://connect.pokrov.space"
    assert public_urls.public_connect_host() == "connect.pokrov.space"
    token = "abc123_secure_token"
    assert (
        public_urls.build_subscription_url(token)
        == f"https://connect.pokrov.space/s8Kx2mP7qR4wT/{token}"
    )


def test_subscription_url_builder_fails_closed_for_missing_or_numeric_credentials():
    public_urls = importlib.import_module("public_urls")

    assert public_urls.build_subscription_url("") == ""
    assert public_urls.build_subscription_url("   ") == ""
    assert public_urls.build_subscription_url(1001) == ""
    assert public_urls.build_subscription_url("1001") == ""


def test_numeric_subscription_compatibility_is_deny_by_default():
    api_source = (PORTAL_BOT_DIR / "api.py").read_text(encoding="utf-8")
    check_links_source = (REPO_ROOT / "scripts" / "check-links.py").read_text(
        encoding="utf-8"
    )

    assert (
        'SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=False)'
        in api_source
    )
    assert (
        'SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=False)'
        in check_links_source
    )
    assert (
        'api_admin_file = REPO_ROOT / "portal_bot" / "api_admin_routes.py"'
        in check_links_source
    )


def test_telegram_login_hash_uses_constant_time_comparison():
    api_source = (PORTAL_BOT_DIR / "api.py").read_text(encoding="utf-8")

    assert "calculated_hash != check_hash" not in api_source
    assert "hmac.compare_digest(calculated_hash, check_hash)" in api_source


def test_sync_shared_surface_facts_builds_pokrov_app_seed_updates_from_shared_truth():
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)
    product = sync_shared_surface_facts._read_json("product-facts.json")
    public_urls = sync_shared_surface_facts._read_json("public-urls.json")
    public_urls_sha256 = sync_shared_surface_facts._shared_sha256("public-urls.json")

    commercial = sync_shared_surface_facts._read_json("commercial-contract.json")

    updates = sync_shared_surface_facts.build_pokrov_app_updates(
        product, public_urls, commercial, public_urls_sha256
    )

    assert updates["product_contract"]["brand"] == "POKROV"
    assert updates["product_contract"]["public_product_line"] == "POKROV"
    assert updates["product_contract"]["client_strategy"] == "consumer-first"
    assert updates["product_contract"]["identity_model"] == "app-first"
    assert updates["product_contract"]["default_runtime_core"] == "sing-box"
    assert updates["product_contract"]["advanced_fallback_core"] == "xray"
    assert updates["product_contract"]["trial_days"] == 5
    assert updates["product_contract"]["telegram_bonus_days"] == 5
    assert updates["product_contract"]["public_scope"] == ["android", "windows"]
    assert updates["product_contract"]["readiness_only_scope"] == ["ios", "macos"]
    assert (
        updates["runtime_profile"]["official_surfaces"]["api"]
        == "https://api.pokrov.space/"
    )
    assert (
        updates["runtime_profile"]["official_surfaces"]["checkout"]
        == "https://pay.pokrov.space/checkout/"
    )
    assert updates["platform_matrix"]["public_release_targets"] == [
        "android",
        "windows",
    ]
    assert updates["platform_matrix"]["readiness_only_targets"] == ["ios", "macos"]
    authority = updates["product_contract"]["platform_authority"]
    assert authority["commercial_revision"] == commercial["commercial_revision"]
    assert (
        authority["product_facts_sha256"]
        == commercial["source_sha256"]["product_facts"]
    )
    assert authority["public_urls_contract"] == "shared/public-urls.json"
    assert authority["public_urls_sha256"] == public_urls_sha256
    assert (
        authority["tariff_catalog_sha256"]
        == commercial["source_sha256"]["tariff_catalog"]
    )
    assert authority["commercial_contract_sha256"] == commercial["contract_sha256"]

    dart = sync_shared_surface_facts.build_pokrov_app_product_facts_dart(
        product, public_urls, commercial, public_urls_sha256
    )
    assert f"static const trialDays = {product['trial']['days']};" in dart
    assert (
        f"static const telegramRewardDays = {product['telegram_reward']['days']};"
        in dart
    )
    assert (
        f"static const referralReferrerDays = {product['referral_reward']['referrer_days']};"
        in dart
    )
    assert "ClientPlatform.android" in dart
    assert "ClientPlatform.macos" in dart
    assert commercial["contract_sha256"] in dart
    assert public_urls_sha256 in dart
    assert f"static const offerUrl = '{public_urls['legal']['offer']}';" in dart
    assert f"static const privacyUrl = '{public_urls['legal']['privacy']}';" in dart
    assert public_urls["releases"]["github_releases"] in dart


def test_shared_surface_fact_hash_is_stable_across_line_endings(tmp_path):
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts_hash", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)

    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    canonical = b'{"surface":"https://pokrov.space/"}\n'
    lf_path.write_bytes(canonical)
    crlf_path.write_bytes(canonical.replace(b"\n", b"\r\n"))

    expected = hashlib.sha256(canonical).hexdigest()
    assert sync_shared_surface_facts._canonical_text_sha256(lf_path) == expected
    assert sync_shared_surface_facts._canonical_text_sha256(crlf_path) == expected


def test_backend_trial_and_reward_constants_bind_shared_product_facts():
    shared_surface_facts = importlib.import_module("shared_surface_facts")
    economy_service = importlib.import_module("economy_service")
    product = shared_surface_facts.get_product_facts()

    assert economy_service.TRIAL_DURATION_DAYS == product["trial"]["days"]
    assert economy_service.TRIAL_RESERVATION_DAYS == product["trial"]["days"]
    assert economy_service.CHANNEL_GRANT_DAYS == product["telegram_reward"]["days"]
    assert (
        economy_service.GRANDFATHERED_CHANNEL_GRANT_DAYS
        == product["telegram_reward"]["grandfathered_days"]
    )
    assert economy_service.FRIEND_GRANT_DAYS == product["referral_reward"][
        "friend_days"
    ]
    assert economy_service.REFERRER_GRANT_DAYS == product["referral_reward"][
        "referrer_days"
    ]
    assert economy_service.REFERRER_HOLD_HOURS == product["referral_reward"][
        "referrer_hold_hours"
    ]

    api_source = (PORTAL_BOT_DIR / "api.py").read_text(encoding="utf-8")
    bot_source = (PORTAL_BOT_DIR / "bot.py").read_text(encoding="utf-8")
    user_handler_source = (PORTAL_BOT_DIR / "bot_user_handlers.py").read_text(
        encoding="utf-8"
    )
    worker_source = (PORTAL_BOT_DIR / "worker.py").read_text(encoding="utf-8")
    assert 'APP_TRIAL_DEFAULT_DAYS = int(_PRODUCT_FACTS["trial"]["days"])' in api_source
    assert (
        'CHANNEL_PREMIUM_DAYS = int(_PRODUCT_FACTS["telegram_reward"]["days"])'
        in api_source
    )
    assert 'REFERRAL_BONUS_DAYS = int(_BOT_REFERRAL_REWARD_FACTS["referrer_days"])' in bot_source
    assert "REFERRAL_FRIEND_DAYS" in user_handler_source
    assert "REFERRAL_HOLD_HOURS" in user_handler_source
    assert "REFERRAL_BONUS_DAYS =" not in worker_source


def test_shared_surface_fact_consumer_audit_rejects_hardcoded_client_facts(tmp_path):
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts_consumers", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)

    source_root = tmp_path / "packages" / "app_shell" / "lib"
    copy_path = source_root / "src" / "shared" / "platform_product_copy.dart"
    profile_path = source_root / "src" / "features" / "profile" / "profile_surface.dart"
    copy_path.parent.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True)
    copy_path.write_text(
        "PlatformProductFacts.trialDays\n"
        "PlatformProductFacts.telegramRewardDays\n"
        "Telegram +5 дней\n",
        encoding="utf-8",
    )
    profile_path.write_text(
        "PlatformProductFacts.offerUrl\n"
        "PlatformProductFacts.privacyUrl\n"
        "PlatformProductFacts.githubReleasesUrl\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="hardcoded platform product facts"):
        sync_shared_surface_facts.validate_pokrov_app_product_fact_consumers(tmp_path)


def _write_valid_client_product_fact_consumers(root: Path) -> Path:
    source_root = root / "packages" / "app_shell" / "lib"
    paths = {
        "copy": source_root / "src" / "shared" / "platform_product_copy.dart",
        "profile": source_root
        / "src"
        / "features"
        / "profile"
        / "profile_surface.dart",
        "seed": source_root / "src" / "seed" / "seed_context.dart",
        "subscription": source_root / "app_first_runtime_bootstrap.dart",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["copy"].write_text(
        "PlatformProductFacts.trialDays\n"
        "PlatformProductFacts.telegramRewardDays\n",
        encoding="utf-8",
    )
    paths["profile"].write_text(
        "PlatformProductFacts.offerUrl\n"
        "PlatformProductFacts.privacyUrl\n"
        "PlatformProductFacts.githubReleasesUrl\n"
        "plan.price\n",
        encoding="utf-8",
    )
    paths["seed"].write_text(
        "PlatformProductFacts.trialDays\n"
        "PlatformProductFacts.telegramRewardDays\n"
        "PlatformProductFacts.publicReleaseTargets\n"
        "PlatformProductFacts.readinessOnlyTargets\n",
        encoding="utf-8",
    )
    paths["subscription"].write_text(
        "price: _clientText(json['price'])\n",
        encoding="utf-8",
    )
    return source_root


def test_shared_surface_fact_consumer_audit_rejects_hardcoded_client_price(tmp_path):
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts_price_consumers", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)
    source_root = _write_valid_client_product_fact_consumers(tmp_path)
    (source_root / "price.dart").write_text(
        "const localPrice = '299 RUB';\n", encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="hardcoded client price facts"):
        sync_shared_surface_facts.validate_pokrov_app_product_fact_consumers(tmp_path)


def test_shared_surface_fact_consumer_audit_requires_device_scope_projection(tmp_path):
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts_device_consumers", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)
    source_root = _write_valid_client_product_fact_consumers(tmp_path)
    seed_path = source_root / "src" / "seed" / "seed_context.dart"
    seed_path.write_text(
        seed_path.read_text(encoding="utf-8").replace(
            "PlatformProductFacts.publicReleaseTargets\n", ""
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        SystemExit, match="missing generated platform product-fact consumers"
    ):
        sync_shared_surface_facts.validate_pokrov_app_product_fact_consumers(tmp_path)


def test_shared_surface_fact_check_rejects_drift_without_rewriting(tmp_path):
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location(
        "sync_shared_surface_facts_check", module_path
    )
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)

    target = tmp_path / "projection.json"
    target.write_text("stale\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="shared fact projection drift"):
        sync_shared_surface_facts._write_or_check(
            target, '{"expected":true}\n', check=True
        )

    assert target.read_text(encoding="utf-8") == "stale\n"
