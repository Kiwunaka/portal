from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"

if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def test_shared_surface_fact_loaders_expose_canonical_product_and_url_truth():
    shared_surface_facts = importlib.import_module("shared_surface_facts")

    product = shared_surface_facts.get_product_facts()
    urls = shared_surface_facts.get_public_urls()
    design = shared_surface_facts.get_design_tokens()

    assert product["brands"]["platform"] == "POKROV"
    assert product["brands"]["client"] == "POKROV"
    assert product["trial"]["days"] == 5
    assert product["telegram_reward"]["days"] == 5
    assert product["telegram_reward"]["grandfathered_days"] == 10
    assert product["platform_scope"]["public"] == ["android", "windows"]
    assert product["network_defaults"]["routing_mode_default"] == "all_except_ru"
    assert product["network_defaults"]["transport_profile_default"] == "legacy_reality_fallback"
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


def test_public_url_helpers_use_shared_public_url_defaults(monkeypatch):
    monkeypatch.delenv("PUBLIC_CONNECT_URL", raising=False)
    monkeypatch.delenv("PUBLIC_CONNECT_DOMAIN", raising=False)

    shared_surface_facts = importlib.import_module("shared_surface_facts")
    public_urls = importlib.import_module("public_urls")

    shared_surface_facts.clear_shared_surface_fact_caches()

    assert public_urls.public_connect_base_url() == "https://connect.pokrov.space"
    assert public_urls.public_connect_host() == "connect.pokrov.space"
    token = "abc123_secure_token"
    assert public_urls.build_subscription_url(token) == f"https://connect.pokrov.space/s8Kx2mP7qR4wT/{token}"


def test_subscription_url_builder_fails_closed_for_missing_or_numeric_credentials():
    public_urls = importlib.import_module("public_urls")

    assert public_urls.build_subscription_url("") == ""
    assert public_urls.build_subscription_url("   ") == ""
    assert public_urls.build_subscription_url(1001) == ""
    assert public_urls.build_subscription_url("1001") == ""


def test_numeric_subscription_compatibility_is_deny_by_default():
    api_source = (PORTAL_BOT_DIR / "api.py").read_text(encoding="utf-8")
    check_links_source = (REPO_ROOT / "scripts" / "check-links.py").read_text(encoding="utf-8")

    assert (
        'SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=False)'
        in api_source
    )
    assert (
        'SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED = env_bool("SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED", default=False)'
        in check_links_source
    )


def test_telegram_login_hash_uses_constant_time_comparison():
    api_source = (PORTAL_BOT_DIR / "api.py").read_text(encoding="utf-8")

    assert "calculated_hash != check_hash" not in api_source
    assert "hmac.compare_digest(calculated_hash, check_hash)" in api_source


def test_sync_shared_surface_facts_builds_pokrov_app_seed_updates_from_shared_truth():
    module_path = REPO_ROOT / "scripts" / "sync_shared_surface_facts.py"
    spec = importlib.util.spec_from_file_location("sync_shared_surface_facts", module_path)
    assert spec is not None and spec.loader is not None
    sync_shared_surface_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_shared_surface_facts)
    product = sync_shared_surface_facts._read_json("product-facts.json")
    public_urls = sync_shared_surface_facts._read_json("public-urls.json")

    updates = sync_shared_surface_facts.build_pokrov_app_updates(product, public_urls)

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
    assert updates["runtime_profile"]["official_surfaces"]["api"] == "https://api.pokrov.space/"
    assert updates["runtime_profile"]["official_surfaces"]["checkout"] == "https://pay.pokrov.space/checkout/"
    assert updates["platform_matrix"]["public_release_targets"] == ["android", "windows"]
    assert updates["platform_matrix"]["readiness_only_targets"] == ["ios", "macos"]
