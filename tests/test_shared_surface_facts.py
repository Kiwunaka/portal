from __future__ import annotations

import importlib
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
    assert product["brands"]["client"] == "POKROV VPN"
    assert product["trial"]["days"] == 5
    assert product["telegram_reward"]["days"] == 10
    assert product["platform_scope"]["public"] == ["android", "windows"]

    assert urls["surfaces"]["marketing"] == "https://pokrov.space/"
    assert urls["surfaces"]["webapp"] == "https://app.pokrov.space/"
    assert urls["surfaces"]["api"] == "https://api.pokrov.space/"
    assert urls["surfaces"]["connect"] == "https://connect.pokrov.space/"
    assert urls["surfaces"]["checkout"] == "https://pay.pokrov.space/checkout/"
    assert urls["telegram"]["channel_username"] == "@pokrov_vpn"

    assert design["theme"]["name"] == "quiet-core-luminous-edge"
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
    assert public_urls.build_subscription_url("abc123") == "https://connect.pokrov.space/s8Kx2mP7qR4wT/abc123"
