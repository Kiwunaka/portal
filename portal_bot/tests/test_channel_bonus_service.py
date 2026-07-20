from __future__ import annotations

import asyncio
import importlib
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError


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
        "account_foundation_service",
        "channel_bonus_service",
        "config",
        "db",
        "migrations",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "economy_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
        "public_urls",
        "shared_surface_facts",
    ]:
        monkeypatch.delitem(sys.modules, name, raising=False)

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
        assert payload["bonus_days"] == 5
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
        assert payload["premium_days"] == 5
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


def test_api_and_bot_projections_converge_on_one_account_grant(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    from models import Account, EntitlementGrant

    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)

    try:
        account = Account(
            id="33333333-3333-3333-3333-333333333333",
            status="active",
            created_source="app_first",
            created_at=now,
            updated_at=now,
        )
        app_user = api.User(
            tg_id=9000000000003,
            account_id=account.id,
            username="app_projection",
            uuid="33333333-3333-3333-3333-333333333334",
            email="APP_9000000000003",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + api.timedelta(days=5),
            is_active=True,
            tos_accepted=True,
            is_app_user=True,
            linked_telegram_id=777003,
        )
        bot_user = api.User(
            tg_id=777003,
            account_id=account.id,
            username="bot_projection",
            uuid="33333333-3333-3333-3333-333333333335",
            email="BOT_777003",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + api.timedelta(days=5),
            is_active=True,
            tos_accepted=True,
        )
        session.add_all([account, app_user, bot_user])
        session.commit()

        checked_ids: list[int] = []

        async def fake_is_member(_channel_username: str, telegram_id: int):
            checked_ids.append(telegram_id)
            return True, "member"

        async def fake_sync(_user):
            return True

        monkeypatch.setattr(service, "award_points", lambda **_kwargs: 100)
        first = asyncio.run(
            service.claim_channel_bonus(
                s=session,
                user=app_user,
                tg_id=int(app_user.tg_id),
                public_channel="pokrov_vpn",
                bonus_days=10,
                opening_bonus_campaign_key="opening_premium_14d",
                subscriber_campaign_key="channel_subscriber_v1",
                points_expiry_days=90,
                is_channel_member=fake_is_member,
                sync_user_after_paid_bonus=fake_sync,
            )
        )
        replay = asyncio.run(
            service.claim_channel_bonus(
                s=session,
                user=bot_user,
                tg_id=int(bot_user.tg_id),
                public_channel="pokrov_vpn",
                bonus_days=10,
                opening_bonus_campaign_key="opening_premium_14d",
                subscriber_campaign_key="channel_subscriber_v1",
                points_expiry_days=90,
                is_channel_member=fake_is_member,
                sync_user_after_paid_bonus=fake_sync,
            )
        )

        assert first["premium_days"] == 5
        assert replay["premium_days"] == 5
        assert replay["already_claimed"] is True
        assert checked_ids == [777003]
        assert session.query(EntitlementGrant).filter_by(source="telegram_channel").count() == 1
        assert app_user.expiry_at == bot_user.expiry_at
    finally:
        session.close()


def test_concurrent_channel_claim_uniqueness_conflict_returns_canonical_grant(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    from models import Account, EntitlementGrant

    session = api.SessionLocal()
    now = datetime(2026, 7, 12, 12, 0, 0)
    try:
        account = Account(
            id=str(uuid.uuid4()),
            status="active",
            created_source="test",
            created_at=now,
            updated_at=now,
        )
        user = api.User(
            tg_id=9000000000099,
            account_id=account.id,
            username="channel-race",
            uuid=str(uuid.uuid4()),
            email="channel-race@example.test",
            sub_type="FREE",
            current_plan_code="trial",
            created_at=now,
            expiry_at=now + timedelta(days=5),
            is_active=True,
            tos_accepted=True,
            linked_telegram_id=777099,
        )
        canonical = EntitlementGrant(
            id=str(uuid.uuid4()),
            account_id=account.id,
            legacy_tg_id=user.tg_id,
            idempotency_key=f"channel-grant:v2:{account.id}",
            source="telegram_channel",
            status="active",
            grant_kind="premium_bonus",
            plan_code="channel_bonus",
            starts_at=now + timedelta(days=5),
            expires_at=now + timedelta(days=10),
            activated_at=now,
            duration_days=5,
            provider="telegram_membership",
            created_at=now,
            updated_at=now,
        )
        session.add_all([account, user, canonical])
        session.commit()

        lookups = iter([None, canonical])
        monkeypatch.setattr(service, "_channel_grant_for_account", lambda *_args, **_kwargs: next(lookups))
        monkeypatch.setattr(
            service,
            "grant_channel_bonus",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                IntegrityError("INSERT entitlement_grants", {}, Exception("unique"))
            ),
        )

        async def member(_channel: str, _tg_id: int):
            return True, "member"

        payload = asyncio.run(
            service.claim_channel_bonus(
                s=session,
                user=user,
                tg_id=user.tg_id,
                public_channel="pokrov_vpn",
                bonus_days=5,
                opening_bonus_campaign_key="opening_premium_14d",
                subscriber_campaign_key="channel_subscriber_v1",
                points_expiry_days=90,
                is_channel_member=member,
            )
        )

        assert payload["ok"] is True
        assert payload["already_claimed"] is True
        assert payload["premium_days"] == 5
        assert session.query(EntitlementGrant).filter_by(account_id=account.id).count() == 1
    finally:
        session.close()
