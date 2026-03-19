from scripts.remote_switch_bot_tokens import apply_bot_switch


def test_apply_bot_switch_updates_main_and_helpbot_env() -> None:
    original = "\n".join(
        [
            "BOT_TOKEN=old-main-token",
            "BOT_USERNAME=swazist_bot",
            "SUPPORT_USERNAME=swazist_bot",
            "SUPPORT_BOT_USERNAME=swazist_bot",
            "PUBLIC_CHANNEL=old_channel",
            "",
        ]
    )

    updated = apply_bot_switch(
        original,
        new_bot_token="new-main-token",
        new_bot_username="portal_service_bot",
        migration_target_url="https://t.me/portal_service_bot",
        public_channel="portal_privacy",
        profile_update_hours=6,
        help_bot_token="new-help-token",
        support_username="portal_privacy_helpbot",
    )

    assert "BOT_TOKEN=new-main-token" in updated
    assert "BOT_USERNAME=portal_service_bot" in updated
    assert "BOT_MIGRATION_TARGET_URL=https://t.me/portal_service_bot" in updated
    assert "PUBLIC_CHANNEL=portal_privacy" in updated
    assert "PROFILE_UPDATE_INTERVAL_HOURS=6" in updated
    assert "HELP_BOT_TOKEN=new-help-token" in updated
    assert "SUPPORT_USERNAME=portal_privacy_helpbot" in updated
    assert "SUPPORT_BOT_USERNAME=portal_privacy_helpbot" in updated
    assert "LEGACY_BOT_TOKEN=old-main-token" in updated
