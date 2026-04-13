from __future__ import annotations

import asyncio
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api_and_service(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")

    for name in [
        "api",
        "channel_bonus_service",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
        "public_urls",
        "shared_surface_facts",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")
    service = importlib.import_module("channel_bonus_service")
    return api, service


def test_channel_subscriber_status_reports_link_required_and_claim_state(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)

    try:
        user = api.User(
            tg_id=9000000000001,
            username="app_000001",
            uuid="11111111-1111-1111-1111-111111111111",
            email="APP_9000000000001",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + api.timedelta(days=5),
            is_active=True,
            tos_accepted=True,
            is_app_user=True,
            app_install_id="install-bonus-status",
            app_device_name="Pixel Fold",
            linked_telegram_id=777001,
            linked_telegram_username="linked_member",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        async def fake_is_channel_member(channel_username: str, tg_id: int):
            assert channel_username == "pokrov_vpn"
            return True, "member"

        payload = asyncio.run(
            service.build_channel_subscriber_check_response(
                user=user,
                channel_username="pokrov_vpn",
                bonus_days=10,
                is_channel_member=fake_is_channel_member,
            )
        )

        assert payload["ok"] is True
        assert payload["subscriber"] is True
        assert payload["reason"] == "member"
        assert payload["claim_required"] is True
        assert payload["bonus_days"] == 10
        assert payload["already_claimed"] is False
    finally:
        session.close()


def test_claim_channel_bonus_updates_user_and_returns_public_shape(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)

    try:
        user = api.User(
            tg_id=9000000000002,
            username="app_000002",
            uuid="22222222-2222-2222-2222-222222222222",
            email="APP_9000000000002",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + api.timedelta(days=5),
            is_active=True,
            tos_accepted=True,
            is_app_user=True,
            app_install_id="install-bonus-claim",
            app_device_name="Pixel Fold",
            linked_telegram_id=777001,
            linked_telegram_username="linked_member",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        async def fake_is_channel_member(channel_username: str, tg_id: int):
            assert channel_username == "pokrov_vpn"
            assert tg_id == 777001
            return True, "member"

        async def fake_sync_user_after_paid_bonus(user_row):
            return True

        monkeypatch.setattr(service, "_is_channel_member", fake_is_channel_member)
        monkeypatch.setattr(service, "_sync_user_after_paid_bonus", fake_sync_user_after_paid_bonus)
        monkeypatch.setattr(service, "award_points", lambda **kwargs: 100)

        payload = asyncio.run(
            service.claim_channel_bonus(
                s=session,
                user=user,
                tg_id=int(user.tg_id),
                public_channel="pokrov_vpn",
                bonus_days=10,
                opening_bonus_campaign_key="opening_premium_14d",
                subscriber_campaign_key="channel_subscriber_v1",
                points_expiry_days=90,
            )
        )

        session.refresh(user)

        assert payload["ok"] is True
        assert payload["already_claimed"] is False
        assert payload["premium_days"] == 10
        assert payload["channel"] == "pokrov_vpn"
        assert payload["sync_ok"] is True
        assert payload["points_granted"] == 100
        assert payload["linked_telegram_id"] == 777001
        assert payload["linked_telegram_username"] == "linked_member"
        assert user.sub_type == "BONUS"
        assert user.current_plan_code == "channel_bonus"
        assert user.channel_bonus_claimed_at is not None
    finally:
        session.close()
