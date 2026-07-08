import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "docs" / "developer" / "pokrov-canonical-feature-tracker.csv"


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8", errors="replace")


def _assert_contains(text: str, snippets: tuple[str, ...], *, context: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"{context} missing snippets: {missing}"


def _telegram_rows() -> list[dict[str, str]]:
    with TRACKER.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [row for row in rows if row["source_tracker"].endswith("pokrov-telegram-bot-user-stories.xlsx")]


def test_all_telegram_story_rows_keep_live_source_references() -> None:
    rows = _telegram_rows()
    assert len(rows) == 57

    for row in rows:
        evidence_refs = re.findall(r"portal_bot/[A-Za-z0-9_./-]+\.py", row["code_evidence"])
        assert evidence_refs, f"{row['canonical_id']} has no code evidence"
        for evidence_ref in evidence_refs:
            relative_path = evidence_ref.split(":", 1)[0]
            path = ROOT / relative_path
            assert relative_path.startswith("portal_bot/"), f"{row['canonical_id']} points outside portal_bot: {relative_path}"
            assert path.exists(), f"{row['canonical_id']} source ref is stale: {relative_path}"


def test_main_bot_public_and_admin_story_triggers_remain_present() -> None:
    bot = _read("portal_bot/bot.py")

    _assert_contains(
        bot,
        (
            "OPENING_PREMIUM_CAMPAIGN_KEY",
            "sync_telegram_identity",
            "generate_referral_code",
            "get_or_create_referral_code",
            "set_referrer_by_code",
            "noop",
            "accept_tos",
            "show_key",
            "share_access",
            "panic_menu",
            "panic_execute",
            "show_instruction",
            "confused_help",
            "menu_bonuses",
            "menu_more",
            "review_start",
            "show_referral",
            "show_wheel",
            "do_wheel_spin",
            "pay_rub",
            "buy_trial",
            "network_status",
            "network_status_scan",
            "handle_text_input",
            "activate_promo_code_for_user",
            "create_gift_card",
        ),
        context="main bot public triggers",
    )
    _assert_contains(
        bot,
        (
            "admin_manual_menu",
            "admin_manual_create",
            "admin_reviews",
            "admin_nodes",
            "admin_bcast",
            "_campaign_lookup",
            "admin_start_links",
            "admin_start_create",
            "admin_start_edit",
            "admin_mass",
            "admin_sync",
            "admin_health",
            "admin_wheel",
            "wheel_weights",
            "mass_sync_nodes",
            "mass_addgb_active",
        ),
        context="main bot admin fallback triggers",
    )


def test_support_feedback_and_legacy_bot_story_triggers_remain_present() -> None:
    helpbot = _read("portal_bot/helpbot.py")
    feedbackbot = _read("portal_bot/feedbackbot.py")
    legacy = _read("portal_bot/legacy_redirect_bot.py")

    _assert_contains(
        helpbot,
        (
            "hb_ticket_new",
            "hb_ticket_my",
            "hb_ticket_view_",
            "hb_ticket_reply_",
            "hb_ticket_close_",
            "hb_ticket_reopen_",
            "hb_admin_queue",
            "hb_aiq_",
            "capture_ticket_attachment",
            "capture_ticket_reply",
            "_configure_support_bot_commands",
            "SUPPORT_AI_CONFIG",
        ),
        context="support bot triggers",
    )
    _assert_contains(
        feedbackbot,
        (
            "fb_new",
            "fb_back_home",
            "fb_admin_queue",
            "fb_review_",
            "fb_feature_",
            "fb_delete_",
            "pending_feedback",
            "upsert_feedback_entry",
            "publish_feedback_entry",
            "delete_feedback_entry",
        ),
        context="feedback bot triggers",
    )
    _assert_contains(
        legacy,
        (
            "TARGET_URL",
            "https://t.me/pokrov_vpnbot",
            "_redirect_text",
            "_redirect_kb",
            "CommandStart",
            "any_callback",
            "any_text",
        ),
        context="legacy redirect bot",
    )


def test_main_bot_profile_growth_contracts_remain_present() -> None:
    bot = _read("portal_bot/bot.py")
    profile = _read("portal_bot/telegram_profile.py")
    checker = _read("scripts/brain_telegram_bot_profile_check.py")

    _assert_contains(
        bot,
        (
            "expected_public_command_payload",
            "TELEGRAM_PROFILE_WEBAPP_MENU_TEXT",
            "_track_bot_entry",
            "bot_entry_opened",
            "_classify_start_arg_for_analytics",
        ),
        context="main bot profile and analytics hooks",
    )
    _assert_contains(
        profile,
        (
            "BOT_PROFILE_NAME",
            "POKROV VPN",
            "BOT_PROFILE_SHORT_DESCRIPTION",
            "BOT_PROFILE_DESCRIPTION",
            "expected_webapp_menu_button_payload",
            "validate_profile_spec",
        ),
        context="telegram profile source of truth",
    )
    _assert_contains(
        checker,
        (
            "getMyName",
            "getMyShortDescription",
            "getMyDescription",
            "setMyName",
            "setMyShortDescription",
            "setMyDescription",
            "telegram_similar_bots_manual",
            "MANUAL_OWNER_TEST",
        ),
        context="telegram profile drift checker",
    )
