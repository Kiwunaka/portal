from __future__ import annotations

import sys
from pathlib import Path


def _load_profile_module():
    repo_root = Path(__file__).resolve().parents[1]
    portal_dir = str(repo_root / "portal_bot")
    if portal_dir not in sys.path:
        sys.path.insert(0, portal_dir)
    import telegram_profile

    return telegram_profile


def test_profile_spec_fits_telegram_bot_api_limits() -> None:
    profile = _load_profile_module()

    assert len(profile.BOT_PROFILE_NAME) <= profile.BOT_PROFILE_NAME_LIMIT
    assert len(profile.BOT_PROFILE_SHORT_DESCRIPTION) <= profile.BOT_PROFILE_SHORT_DESCRIPTION_LIMIT
    assert len(profile.BOT_PROFILE_DESCRIPTION) <= profile.BOT_PROFILE_DESCRIPTION_LIMIT
    assert profile.validate_profile_spec() == []


def test_profile_copy_contains_required_pokrov_surface_facts() -> None:
    profile = _load_profile_module()
    copy = "\n".join(profile.expected_profile_payload().values())

    for fragment in (
        "POKROV VPN",
        "Android",
        "Windows",
        "5 дней",
        "без карты",
        "@pokrov_supportbot",
        "@pokrov_feedbackbot",
        "@pokrov_vpn",
    ):
        assert fragment in copy


def test_public_commands_and_menu_are_the_shared_source_of_truth() -> None:
    profile = _load_profile_module()

    assert profile.expected_public_command_names() == ["start", "cabinet", "support", "help", "promo", "redeem"]
    assert profile.expected_webapp_menu_button_payload() == {
        "type": "web_app",
        "text": "POKROV",
        "web_app": {"url": "https://app.pokrov.space/"},
    }
