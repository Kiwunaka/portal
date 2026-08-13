from __future__ import annotations

import importlib
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

NOW = datetime(2026, 7, 12, 12, 0, 0)


@pytest.fixture(autouse=True)
def _enable_legacy_free_tier(monkeypatch):
    monkeypatch.setenv("FREE_TIER_ENABLED", "true")


def _session(tmp_path: Path):
    import economy_service
    from models import Base

    importlib.reload(economy_service)

    engine = create_engine(f"sqlite:///{(tmp_path / 'economy-bonus.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _seed_account(session, *, suffix: int, expiry_days: int = 5, paid: bool = False):
    from models import Account, User

    account_id = str(uuid.uuid4())
    tg_id = 7_000_000 + suffix
    account = Account(
        id=account_id,
        status="active",
        created_source="app_first",
        created_at=NOW,
        updated_at=NOW,
    )
    user = User(
        tg_id=tg_id,
        account_id=account_id,
        username=f"bonus-{suffix}",
        uuid=str(uuid.uuid4()),
        email=f"bonus-{suffix}@example.test",
        sub_type="PAID" if paid else "FREE",
        current_plan_code="1_month" if paid else "trial",
        expiry_at=NOW + timedelta(days=expiry_days),
        is_active=True,
        trial_used=not paid,
        tos_accepted=True,
        created_at=NOW,
    )
    session.add_all([account, user])
    session.flush()
    return account, user


def test_channel_grant_is_account_deduped_and_adds_five_days(tmp_path: Path) -> None:
    from economy_service import grant_channel_bonus
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    account, app_user = _seed_account(session, suffix=1)
    bot_projection = type(app_user)(
        tg_id=8_000_001,
        account_id=account.id,
        username="linked-bot",
        uuid=str(uuid.uuid4()),
        email="linked-bot@example.test",
        sub_type="FREE",
        current_plan_code="trial",
        expiry_at=app_user.expiry_at,
        is_active=True,
        trial_used=True,
        tos_accepted=True,
        created_at=NOW,
    )
    session.add(bot_projection)
    session.flush()

    first = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=app_user.tg_id,
        telegram_id=8_000_001,
        now=NOW,
    )
    replay = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=bot_projection.tg_id,
        telegram_id=8_000_001,
        now=NOW + timedelta(minutes=5),
    )

    assert replay.id == first.id
    assert first.idempotency_key == f"channel-grant:v2:{account.id}"
    assert first.duration_days == 5
    assert first.starts_at == NOW
    assert first.expires_at == NOW + timedelta(days=5)
    assert session.query(EntitlementGrant).filter_by(source="telegram_channel").count() == 1
    assert {row.expiry_at for row in (app_user, bot_projection)} == {NOW + timedelta(days=5)}
    session.close()
    engine.dispose()


def test_grandfathered_channel_backfill_preserves_issued_ten_days(tmp_path: Path) -> None:
    from economy_service import backfill_grandfathered_channel_grant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=2, expiry_days=23)
    user.channel_bonus_claimed_at = NOW - timedelta(days=2)
    user.channel_bonus_active = True
    user.channel_bonus_expires_at = NOW + timedelta(days=8)
    before_expiry = user.expiry_at

    grant = backfill_grandfathered_channel_grant(session, user=user, now=NOW)
    replay = backfill_grandfathered_channel_grant(session, user=user, now=NOW + timedelta(days=1))

    assert grant is not None
    assert replay is not None and replay.id == grant.id
    assert grant.idempotency_key == f"channel-grant:v1-grandfathered:{account.id}"
    assert grant.duration_days == 10
    assert grant.source == "telegram_channel_grandfathered"
    assert grant.starts_at == user.channel_bonus_expires_at - timedelta(days=10)
    assert grant.expires_at == user.channel_bonus_expires_at
    assert user.expiry_at == before_expiry
    session.close()
    engine.dispose()


def test_legacy_pre_first_payment_trial_channel_friend_cap_is_exactly_fifteen_days(tmp_path: Path) -> None:
    from economy_service import (
        activate_reserved_trial,
        grant_channel_bonus,
        grant_referred_friend_bonus,
        record_connection_evidence,
        reserve_trial,
    )
    from models import AccountDevice

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=3, expiry_days=7)
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=account.id,
        install_id="cap-install",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(device)
    session.flush()
    reserve_trial(session, account_id=account.id, device_id=device.id, now=NOW)
    evidence = record_connection_evidence(
        session,
        account_id=account.id,
        device_id=device.id,
        node_id=3,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="cap:observer:3",
    )
    activate_reserved_trial(session, account_id=account.id, evidence=evidence)

    channel = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW,
    )
    friend = grant_referred_friend_bonus(
        session,
        account_id=account.id,
        evidence=evidence,
        now=NOW,
        allow_legacy_migration=True,
    )

    assert channel.duration_days == 5
    assert friend.duration_days == 5
    assert user.expiry_at == NOW + timedelta(days=15)
    assert sum(grant.duration_days or 0 for grant in (channel, friend)) == 10
    session.close()
    engine.dispose()


def test_channel_loss_waits_24h_and_reverses_only_unused_channel_time(tmp_path: Path) -> None:
    from economy_service import begin_channel_loss_grace, grant_channel_bonus, reverse_due_channel_grants

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=4)
    grant = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW,
    )
    grace = begin_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=6))

    early = reverse_due_channel_grants(session, now=grace + timedelta(hours=23, minutes=59))
    due = reverse_due_channel_grants(session, now=grace + timedelta(hours=24))

    assert early == {"reversed": 0, "waiting": 1}
    assert due == {"reversed": 1, "waiting": 0}
    assert grant.status == "reversed"
    assert grant.reversal_reason == "channel_membership_lost"
    assert grant.reversed_at == grace + timedelta(hours=24)
    assert user.expiry_at == NOW + timedelta(days=7)
    assert user.channel_bonus_active is False
    assert user.channel_bonus_revoked_at == grace + timedelta(hours=24)
    session.close()
    engine.dispose()


def test_early_channel_loss_never_reverses_the_trial_baseline(tmp_path: Path) -> None:
    from economy_service import begin_channel_loss_grace, grant_channel_bonus, reverse_due_channel_grants

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=6)
    _seed_typed_trial(session, account_id=account.id, tg_id=user.tg_id)
    grant = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW,
    )
    begin_channel_loss_grace(session, account_id=account.id, now=NOW)

    result = reverse_due_channel_grants(session, now=NOW + timedelta(hours=24))

    assert result == {"reversed": 1, "waiting": 0}
    assert grant.duration_days == 5
    assert user.expiry_at == NOW + timedelta(days=5)
    session.close()
    engine.dispose()


def test_channel_rejoin_cancels_grace_and_paid_unrelated_access_survives(tmp_path: Path) -> None:
    from economy_service import (
        begin_channel_loss_grace,
        cancel_channel_loss_grace,
        grant_channel_bonus,
        reverse_due_channel_grants,
    )
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=5, expiry_days=50, paid=True)
    unrelated = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account.id,
        idempotency_key=f"paid:v1:{account.id}",
        source="payment",
        status="active",
        grant_kind="paid_access",
        plan_code="1_month",
        starts_at=NOW,
        expires_at=NOW + timedelta(days=50),
        duration_days=50,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(unrelated)
    channel = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW,
    )
    begin_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=41))
    assert cancel_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=41, hours=1)) is True
    assert channel.status == "active"

    begin_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=41, hours=2))
    result = reverse_due_channel_grants(session, now=NOW + timedelta(days=42, hours=2))

    assert result == {"reversed": 1, "waiting": 0}
    assert user.sub_type == "PAID"
    assert user.current_plan_code == "1_month"
    assert user.expiry_at == NOW + timedelta(days=50)
    assert unrelated.status == "active"
    assert unrelated.expires_at == NOW + timedelta(days=50)
    session.close()
    engine.dispose()


def test_referral_relationship_rejects_self_and_cycles(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship

    engine, session = _session(tmp_path)
    account_a, _ = _seed_account(session, suffix=10)
    account_b, _ = _seed_account(session, suffix=11)
    account_c, _ = _seed_account(session, suffix=12)

    first = create_referral_relationship(
        session,
        referred_account_id=account_b.id,
        referrer_account_id=account_a.id,
        source="bot_code",
        now=NOW,
    )
    replay = create_referral_relationship(
        session,
        referred_account_id=account_b.id,
        referrer_account_id=account_a.id,
        source="app_projection",
        now=NOW + timedelta(minutes=1),
    )
    create_referral_relationship(
        session,
        referred_account_id=account_c.id,
        referrer_account_id=account_b.id,
        source="bot_code",
        now=NOW,
    )

    assert replay.id == first.id
    with __import__("pytest").raises(ValueError, match="self_referral"):
        create_referral_relationship(
            session,
            referred_account_id=account_a.id,
            referrer_account_id=account_a.id,
            source="bot_code",
            now=NOW,
        )
    with __import__("pytest").raises(ValueError, match="referral_cycle"):
        create_referral_relationship(
            session,
            referred_account_id=account_a.id,
            referrer_account_id=account_c.id,
            source="bot_code",
            now=NOW,
        )
    session.close()
    engine.dispose()


def test_invitee_reward_is_disabled_even_with_canonical_connection_evidence(tmp_path: Path) -> None:
    from economy_service import (
        activate_referred_friend_reward,
        create_referral_relationship,
        record_connection_evidence,
    )
    from models import AccountDevice, EntitlementGrant

    engine, session = _session(tmp_path)
    referrer, _ = _seed_account(session, suffix=13, paid=True)
    referred, user = _seed_account(session, suffix=14)
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=referred.id,
        install_id="friend-evidence-install",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(device)
    session.flush()
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )

    with __import__("pytest").raises(ValueError, match="referral_invitee_bonus_disabled"):
        activate_referred_friend_reward(session, account_id=referred.id, evidence=None, now=NOW)
    evidence = record_connection_evidence(
        session,
        account_id=referred.id,
        device_id=device.id,
        node_id=14,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="friend:observer:14",
    )
    with __import__("pytest").raises(ValueError, match="referral_invitee_bonus_disabled"):
        activate_referred_friend_reward(session, account_id=referred.id, evidence=evidence, now=NOW)

    assert user.expiry_at == NOW + timedelta(days=5)
    assert session.query(EntitlementGrant).filter_by(source="referral_friend").count() == 0
    session.close()
    engine.dispose()


def test_recording_server_evidence_does_not_release_invitee_reward(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship, record_connection_evidence
    from models import AccountDevice, EntitlementGrant

    engine, session = _session(tmp_path)
    referrer, _ = _seed_account(session, suffix=19, paid=True)
    referred, _ = _seed_account(session, suffix=20)
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=referred.id,
        install_id="auto-friend-evidence",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(device)
    session.flush()
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )

    evidence = record_connection_evidence(
        session,
        account_id=referred.id,
        device_id=device.id,
        node_id=20,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="friend:auto:20",
    )
    replay = record_connection_evidence(
        session,
        account_id=referred.id,
        device_id=device.id,
        node_id=20,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="friend:auto:20",
    )

    assert replay.id == evidence.id
    assert session.query(EntitlementGrant).filter_by(source="referral_friend").count() == 0
    session.close()
    engine.dispose()


def test_trial_activation_grants_only_the_five_day_trial(tmp_path: Path) -> None:
    from economy_service import (
        activate_reserved_trial,
        create_referral_relationship,
        record_connection_evidence,
        reserve_trial,
    )
    from models import AccountDevice, EntitlementGrant

    engine, session = _session(tmp_path)
    referrer, _ = _seed_account(session, suffix=21, paid=True)
    referred, user = _seed_account(session, suffix=22)
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=referred.id,
        install_id="trial-friend-order",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(device)
    session.flush()
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )
    reserve_trial(session, account_id=referred.id, device_id=device.id, now=NOW)
    evidence = record_connection_evidence(
        session,
        account_id=referred.id,
        device_id=device.id,
        node_id=22,
        evidence_kind="observer_connection",
        observed_at=NOW + timedelta(hours=1),
        evidence_key="trial-friend:observer:22",
    )

    activation = activate_reserved_trial(session, account_id=referred.id, evidence=evidence)

    assert activation.activated_now is True
    assert user.expiry_at == evidence.observed_at + timedelta(days=5)
    assert session.query(EntitlementGrant).filter_by(source="referral_friend").count() == 0
    session.close()
    engine.dispose()


def test_referrer_reward_waits_full_72_hours_and_payment_replays_converge(tmp_path: Path) -> None:
    from economy_service import (
        create_referral_relationship,
        queue_first_payment_referrer_reward,
        release_due_referrer_rewards,
    )
    from models import EntitlementGrant, ReferralTransition

    engine, session = _session(tmp_path)
    referrer, referrer_user = _seed_account(session, suffix=15, paid=True, expiry_days=20)
    referred, referred_user = _seed_account(session, suffix=16)
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )

    hold = queue_first_payment_referrer_reward(
        session,
        referred_account_id=referred.id,
        payment_key="lavatop:order-16",
        paid_at=NOW,
    )
    replay = queue_first_payment_referrer_reward(
        session,
        referred_account_id=referred.id,
        payment_key="lavatop:order-16",
        paid_at=NOW + timedelta(minutes=2),
    )
    referred_user.first_purchase_done = True

    before = release_due_referrer_rewards(session, now=NOW + timedelta(hours=71, minutes=59))
    at_due = release_due_referrer_rewards(session, now=NOW + timedelta(hours=72))
    worker_replay = release_due_referrer_rewards(session, now=NOW + timedelta(hours=80))

    assert replay.id == hold.id
    assert hold.hold_until == NOW + timedelta(hours=72)
    assert before == {"released": 0, "waiting": 1, "rejected": 0}
    assert at_due == {"released": 1, "waiting": 0, "rejected": 0}
    assert worker_replay == {"released": 0, "waiting": 0, "rejected": 0}
    assert referrer_user.expiry_at == NOW + timedelta(days=30)
    reward = session.query(EntitlementGrant).filter_by(source="referral_referrer").one()
    assert reward.idempotency_key == f"referral-referrer:v1:{referred.id}"
    assert reward.duration_days == 10
    assert session.query(ReferralTransition).filter_by(transition_kind="referrer_reward_released").count() == 1
    session.close()
    engine.dispose()


def _seed_typed_trial(session, *, account_id: str, tg_id: int, starts_at: datetime = NOW):
    from models import EntitlementGrant

    grant = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account_id,
        legacy_tg_id=tg_id,
        idempotency_key=f"typed-trial:{account_id}",
        source="premium_trial",
        status="active",
        grant_kind="premium_trial",
        plan_code="trial",
        starts_at=starts_at,
        expires_at=starts_at + timedelta(days=5),
        activated_at=starts_at,
        duration_days=5,
        provider="internal_economy",
        created_at=starts_at,
        updated_at=starts_at,
    )
    session.add(grant)
    session.flush()
    return grant


def test_channel_then_payment_reversal_rebuild_preserves_full_purchase_and_continuity(tmp_path: Path) -> None:
    from economy_service import (
        begin_channel_loss_grace,
        grant_channel_bonus,
        record_successful_payment_grant,
        reverse_due_channel_grants,
    )
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=30)
    _seed_typed_trial(session, account_id=account.id, tg_id=user.tg_id)
    channel = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW,
    )
    payment = record_successful_payment_grant(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        provider="lavatop",
        order_id="channel-first-order",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW + timedelta(days=1),
    )
    begin_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=6))

    result = reverse_due_channel_grants(session, now=NOW + timedelta(days=7))

    paid_grant = session.query(EntitlementGrant).filter_by(id=payment.grant.id).one()
    assert result == {"reversed": 1, "waiting": 0}
    assert channel.status == "reversed"
    assert payment.is_first_payment is True
    assert paid_grant.duration_days == 30
    assert paid_grant.starts_at == NOW + timedelta(days=7)
    assert paid_grant.expires_at == NOW + timedelta(days=37)
    assert user.expiry_at == NOW + timedelta(days=37)
    assert user.sub_type == "PAID"
    assert user.is_active is True
    session.close()
    engine.dispose()


def test_payment_then_channel_reversal_keeps_paid_projection_and_partial_consumption(tmp_path: Path) -> None:
    from economy_service import (
        begin_channel_loss_grace,
        grant_channel_bonus,
        record_successful_payment_grant,
        reverse_due_channel_grants,
    )

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=31, expiry_days=0)
    user.expiry_at = NOW
    payment = record_successful_payment_grant(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        provider="freekassa",
        order_id="payment-first-order",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW,
    )
    channel = grant_channel_bonus(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id,
        now=NOW + timedelta(days=2),
    )
    begin_channel_loss_grace(session, account_id=account.id, now=NOW + timedelta(days=3))

    result = reverse_due_channel_grants(session, now=NOW + timedelta(days=4))

    assert result == {"reversed": 1, "waiting": 0}
    assert channel.status == "reversed"
    assert payment.grant.duration_days == 30
    assert payment.grant.expires_at == NOW + timedelta(days=30)
    assert user.expiry_at == NOW + timedelta(days=30)
    assert user.sub_type == "PAID"
    assert user.current_plan_code == "1_month"
    session.close()
    engine.dispose()


def test_canonical_payment_fact_is_first_once_across_linked_projections(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship, record_successful_payment_grant
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    referrer, _ = _seed_account(session, suffix=32, paid=True)
    referred, app_user = _seed_account(session, suffix=33, expiry_days=0)
    bot_user = type(app_user)(
        tg_id=8_000_033,
        account_id=referred.id,
        username="payment-bot-projection",
        uuid=str(uuid.uuid4()),
        email="payment-bot-projection@example.test",
        sub_type="FREE",
        expiry_at=NOW,
        is_active=False,
        first_purchase_done=False,
        created_at=NOW,
    )
    session.add(bot_user)
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )

    first = record_successful_payment_grant(
        session,
        account_id=referred.id,
        legacy_tg_id=app_user.tg_id,
        provider="lavatop",
        order_id="canonical-first",
        plan_code="start_99",
        duration_days=30,
        paid_at=NOW,
    )
    replay = record_successful_payment_grant(
        session,
        account_id=referred.id,
        legacy_tg_id=bot_user.tg_id,
        provider="lavatop",
        order_id="canonical-first",
        plan_code="start_99",
        duration_days=30,
        paid_at=NOW + timedelta(minutes=1),
    )
    renewal = record_successful_payment_grant(
        session,
        account_id=referred.id,
        legacy_tg_id=bot_user.tg_id,
        provider="lavatop",
        order_id="canonical-renewal",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW + timedelta(days=1),
    )

    assert first.is_first_payment is True
    assert replay.is_first_payment is True
    assert replay.grant.id == first.grant.id
    assert renewal.is_first_payment is False
    assert session.query(EntitlementGrant).filter_by(source="provider_payment").count() == 2
    assert {app_user.first_purchase_done, bot_user.first_purchase_done} == {True}
    assert app_user.expiry_at == bot_user.expiry_at == NOW + timedelta(days=60)
    relationship = first.relationship
    assert relationship is not None
    assert relationship.first_payment_key == "lavatop:canonical-first"
    assert relationship.hold_until == NOW + timedelta(hours=72)
    session.close()
    engine.dispose()


def test_provider_order_replay_cannot_move_fulfillment_to_another_account(tmp_path: Path) -> None:
    from economy_service import record_successful_payment_grant

    engine, session = _session(tmp_path)
    first_account, first_user = _seed_account(session, suffix=36, expiry_days=0)
    other_account, other_user = _seed_account(session, suffix=37, expiry_days=0)
    result = record_successful_payment_grant(
        session,
        account_id=first_account.id,
        legacy_tg_id=first_user.tg_id,
        provider="lavatop",
        order_id="non-transferable-order",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW,
    )

    with __import__("pytest").raises(ValueError, match="payment_account_mismatch"):
        record_successful_payment_grant(
            session,
            account_id=other_account.id,
            legacy_tg_id=other_user.tg_id,
            provider="lavatop",
            order_id="non-transferable-order",
            plan_code="1_month",
            duration_days=30,
            paid_at=NOW + timedelta(minutes=1),
        )

    assert result.grant.account_id == first_account.id
    assert first_user.expiry_at == NOW + timedelta(days=30)
    assert other_user.expiry_at == NOW
    session.close()
    engine.dispose()


def test_legacy_friend_bonus_promotes_free_policy_preserves_paid_and_downgrades_after_expiry(tmp_path: Path) -> None:
    from economy_service import grant_referred_friend_bonus, rebuild_account_entitlement_projection, record_connection_evidence
    from models import AccessKey, AccountDevice

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=34, expiry_days=0)
    user.expiry_at = NOW
    key = AccessKey(
        tg_id=user.tg_id,
        key_uuid=str(uuid.uuid4()),
        panel_email="bonus-policy@example.test",
        node_code="NL-free",
        pool_code="free_pool",
        state="active",
        source="test",
        is_primary=True,
        created_at=NOW,
        updated_at=NOW,
    )
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=account.id,
        install_id="bonus-policy-install",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add_all([key, device])
    evidence = record_connection_evidence(
        session,
        account_id=account.id,
        device_id=device.id,
        node_id=34,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="bonus-policy:34",
    )

    grant_referred_friend_bonus(
        session,
        account_id=account.id,
        evidence=evidence,
        now=NOW,
        allow_legacy_migration=True,
    )

    assert user.sub_type == "BONUS"
    assert user.current_plan_code == "referral_friend"
    assert key.pool_code == "premium_pool"
    rebuild_account_entitlement_projection(session, account_id=account.id, now=NOW + timedelta(days=6))
    assert user.sub_type == "FREE"
    assert user.current_plan_code == "free_monthly"
    assert key.pool_code == "free_pool"
    session.close()
    engine.dispose()


def test_legacy_friend_bonus_keeps_paid_policy_then_transitions_bonus_to_free(tmp_path: Path) -> None:
    from economy_service import grant_referred_friend_bonus, rebuild_account_entitlement_projection, record_connection_evidence
    from models import AccessKey, AccountDevice

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=35, expiry_days=5, paid=True)
    key = AccessKey(
        tg_id=user.tg_id,
        key_uuid=str(uuid.uuid4()),
        panel_email="paid-bonus-policy@example.test",
        node_code="NL-free",
        pool_code="free_pool",
        state="active",
        source="test",
        is_primary=True,
        created_at=NOW,
        updated_at=NOW,
    )
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=account.id,
        install_id="paid-bonus-policy-install",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add_all([key, device])
    evidence = record_connection_evidence(
        session,
        account_id=account.id,
        device_id=device.id,
        node_id=35,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="paid-bonus-policy:35",
    )

    grant_referred_friend_bonus(
        session,
        account_id=account.id,
        evidence=evidence,
        now=NOW,
        allow_legacy_migration=True,
    )
    assert user.sub_type == "PAID"
    assert key.pool_code == "premium_pool"

    rebuild_account_entitlement_projection(session, account_id=account.id, now=NOW + timedelta(days=6))
    assert user.sub_type == "BONUS"
    assert user.current_plan_code == "referral_friend"
    assert key.pool_code == "premium_pool"

    rebuild_account_entitlement_projection(session, account_id=account.id, now=NOW + timedelta(days=11))
    assert user.sub_type == "FREE"
    assert user.current_plan_code == "free_monthly"
    assert key.pool_code == "free_pool"
    session.close()
    engine.dispose()


def test_non_payment_authority_cannot_queue_referrer_reward(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship, queue_first_payment_referrer_reward

    engine, session = _session(tmp_path)
    referrer, _ = _seed_account(session, suffix=17, paid=True)
    referred, _ = _seed_account(session, suffix=18)
    create_referral_relationship(
        session,
        referred_account_id=referred.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        now=NOW,
    )

    for payment_key in ("clicked_connect", "connected_ok", "admin_gift:18", "renewal:18"):
        with __import__("pytest").raises(ValueError, match="first_payment"):
            queue_first_payment_referrer_reward(
                session,
                referred_account_id=referred.id,
                payment_key=payment_key,
                paid_at=NOW,
            )
    session.close()
    engine.dispose()


def test_free_cycle_expiry_never_extends_provider_payment_or_bonus(tmp_path: Path) -> None:
    from economy_service import grant_channel_bonus, grant_referred_friend_bonus, record_connection_evidence, record_successful_payment_grant
    from models import AccountDevice

    engine, session = _session(tmp_path)
    paid_account, paid_user = _seed_account(session, suffix=40, expiry_days=25)
    paid_user.current_plan_code = "free_monthly"
    paid_user.free_cycle_next_reset_at = NOW + timedelta(days=25)
    payment = record_successful_payment_grant(
        session,
        account_id=paid_account.id,
        legacy_tg_id=paid_user.tg_id,
        provider="lavatop",
        order_id="free-boundary-payment",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW,
    )
    assert payment.grant.starts_at == NOW
    assert payment.grant.expires_at == NOW + timedelta(days=30)
    assert paid_user.expiry_at == NOW + timedelta(days=30)

    channel_account, channel_user = _seed_account(session, suffix=41, expiry_days=25)
    channel_user.current_plan_code = "free_monthly"
    channel_user.free_cycle_next_reset_at = NOW + timedelta(days=25)
    channel = grant_channel_bonus(
        session,
        account_id=channel_account.id,
        legacy_tg_id=channel_user.tg_id,
        telegram_id=channel_user.tg_id,
        now=NOW,
    )
    assert channel.starts_at == NOW
    assert channel.expires_at == NOW + timedelta(days=5)
    assert channel_user.expiry_at == NOW + timedelta(days=5)

    friend_account, friend_user = _seed_account(session, suffix=42, expiry_days=25)
    friend_user.current_plan_code = "free_monthly"
    friend_user.free_cycle_next_reset_at = NOW + timedelta(days=25)
    device = AccountDevice(
        id=str(uuid.uuid4()),
        account_id=friend_account.id,
        install_id="free-boundary-friend",
        state="active",
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(device)
    evidence = record_connection_evidence(
        session,
        account_id=friend_account.id,
        device_id=device.id,
        node_id=42,
        evidence_kind="observer_connection",
        observed_at=NOW,
        evidence_key="free-boundary-friend:42",
    )
    friend = grant_referred_friend_bonus(
        session,
        account_id=friend_account.id,
        evidence=evidence,
        now=NOW,
        allow_legacy_migration=True,
    )
    assert friend.starts_at == NOW
    assert friend.expires_at == NOW + timedelta(days=5)
    assert friend_user.expiry_at == NOW + timedelta(days=5)
    session.close()
    engine.dispose()


def test_mixed_projection_and_channel_reversal_use_only_explicit_premium_contributions(tmp_path: Path) -> None:
    from economy_service import rebuild_account_entitlement_projection, reverse_due_channel_grants
    from models import AccessKey, EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=43, expiry_days=25, paid=True)
    user.free_cycle_next_reset_at = NOW + timedelta(days=25)
    key = AccessKey(
        tg_id=user.tg_id,
        key_uuid=str(uuid.uuid4()),
        panel_email="mixed-boundary@example.test",
        node_code="NL-free",
        pool_code="free_pool",
        state="active",
        source="test",
        is_primary=True,
        created_at=NOW,
        updated_at=NOW,
    )
    free_snapshot = EntitlementGrant(
        id=str(uuid.uuid4()),
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        idempotency_key="mixed-free-snapshot",
        source="legacy_snapshot",
        status="active",
        grant_kind="access_snapshot",
        plan_code="free_monthly",
        starts_at=NOW,
        expires_at=NOW + timedelta(days=25),
        duration_days=25,
        metadata_json='{"sub_type":"FREE"}',
        created_at=NOW,
        updated_at=NOW,
    )
    paid = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="mixed-paid", source="provider_payment", status="active",
        grant_kind="paid_access", plan_code="1_month", starts_at=NOW,
        expires_at=NOW + timedelta(days=10), activated_at=NOW, duration_days=10,
        provider="lavatop", external_order_id="mixed-paid", created_at=NOW, updated_at=NOW,
    )
    trial = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="mixed-trial", source="premium_trial", status="active",
        grant_kind="premium_trial", plan_code="trial", starts_at=NOW + timedelta(days=10),
        expires_at=NOW + timedelta(days=15), activated_at=NOW, duration_days=5,
        provider="internal_economy", created_at=NOW, updated_at=NOW,
    )
    channel = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="mixed-channel", source="telegram_channel", status="grace",
        grant_kind="premium_bonus", plan_code="channel_bonus", starts_at=NOW + timedelta(days=15),
        expires_at=NOW + timedelta(days=20), activated_at=NOW, duration_days=5,
        provider="telegram_membership", metadata_json=f'{{"grace_until":"{NOW.isoformat()}"}}',
        created_at=NOW, updated_at=NOW,
    )
    session.add_all([key, free_snapshot, paid, trial, channel])
    session.flush()

    assert reverse_due_channel_grants(session, now=NOW) == {"reversed": 1, "waiting": 0}
    assert user.expiry_at == NOW + timedelta(days=15)
    assert user.sub_type == "PAID"
    assert key.pool_code == "premium_pool"

    rebuild_account_entitlement_projection(session, account_id=account.id, now=NOW + timedelta(days=11))
    assert user.expiry_at == NOW + timedelta(days=15)
    assert user.sub_type == "BONUS"
    assert user.current_plan_code == "trial"
    assert key.pool_code == "premium_pool"

    rebuild_account_entitlement_projection(session, account_id=account.id, now=NOW + timedelta(days=16))
    assert user.expiry_at == NOW + timedelta(days=25)
    assert user.sub_type == "FREE"
    assert user.current_plan_code == "free_monthly"
    assert key.pool_code == "free_pool"
    session.close()
    engine.dispose()


def test_pre_first_payment_cap_ignores_free_snapshot_duration(tmp_path: Path) -> None:
    from economy_service import grant_channel_bonus, grant_referred_friend_bonus, record_connection_evidence
    from models import AccountDevice, EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=44, expiry_days=25)
    user.current_plan_code = "free_monthly"
    free_snapshot = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="cap-free-snapshot", source="legacy_snapshot", status="active",
        grant_kind="access_snapshot", plan_code="free_monthly", starts_at=NOW,
        expires_at=NOW + timedelta(days=25), duration_days=25,
        metadata_json='{"sub_type":"FREE"}', created_at=NOW, updated_at=NOW,
    )
    trial = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="cap-explicit-trial", source="premium_trial", status="active",
        grant_kind="premium_trial", plan_code="trial", starts_at=NOW,
        expires_at=NOW + timedelta(days=5), activated_at=NOW, duration_days=5,
        provider="internal_economy", created_at=NOW, updated_at=NOW,
    )
    device = AccountDevice(
        id=str(uuid.uuid4()), account_id=account.id, install_id="cap-free-snapshot",
        state="active", first_seen_at=NOW, last_seen_at=NOW, created_at=NOW, updated_at=NOW,
    )
    session.add_all([free_snapshot, trial, device])
    session.flush()
    evidence = record_connection_evidence(
        session, account_id=account.id, device_id=device.id, node_id=44,
        evidence_kind="observer_connection", observed_at=NOW, evidence_key="cap-free-snapshot:44",
    )
    channel = grant_channel_bonus(
        session, account_id=account.id, legacy_tg_id=user.tg_id,
        telegram_id=user.tg_id, now=NOW,
    )
    friend = grant_referred_friend_bonus(
        session,
        account_id=account.id,
        evidence=evidence,
        now=NOW,
        allow_legacy_migration=True,
    )

    assert channel.duration_days == friend.duration_days == 5
    premium_acquisition = session.query(EntitlementGrant).filter(
        EntitlementGrant.account_id == account.id,
        EntitlementGrant.source.in_(["premium_trial", "telegram_channel", "referral_friend"]),
    ).all()
    assert sum(int(row.duration_days or 0) for row in premium_acquisition) == 15
    assert user.expiry_at == NOW + timedelta(days=15)
    session.close()
    engine.dispose()


def test_legacy_bonus_snapshot_is_premium_baseline_for_new_payment(tmp_path: Path) -> None:
    from economy_service import record_successful_payment_grant
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=45, expiry_days=5)
    user.sub_type = "BONUS"
    user.current_plan_code = "legacy_bonus"
    snapshot = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="legacy-bonus-baseline", source="legacy_snapshot", status="active",
        grant_kind="access_snapshot", plan_code="legacy_bonus", starts_at=NOW - timedelta(days=2),
        expires_at=NOW + timedelta(days=5), duration_days=7,
        metadata_json='{"sub_type":"BONUS"}', created_at=NOW, updated_at=NOW,
    )
    session.add(snapshot)
    session.flush()

    payment = record_successful_payment_grant(
        session,
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        provider="lavatop",
        order_id="legacy-bonus-payment",
        plan_code="1_month",
        duration_days=30,
        paid_at=NOW,
    )

    assert payment.grant.starts_at == NOW + timedelta(days=5)
    assert payment.grant.expires_at == NOW + timedelta(days=35)
    assert user.expiry_at == NOW + timedelta(days=35)
    session.close()
    engine.dispose()


def test_legacy_paid_snapshot_is_preserved_without_double_applying_backfilled_payment(tmp_path: Path) -> None:
    from economy_service import _provider_payment_key, record_successful_payment_grant
    from models import EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=46, expiry_days=20, paid=True)
    snapshot = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="legacy-paid-baseline", source="legacy_snapshot", status="active",
        grant_kind="access_snapshot", plan_code="1_month", starts_at=NOW - timedelta(days=10),
        expires_at=NOW + timedelta(days=20), duration_days=30,
        metadata_json='{"sub_type":"PAID"}', created_at=NOW, updated_at=NOW,
    )
    fact = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key=_provider_payment_key("lavatop", "legacy-paid-replay"), source="provider_payment",
        status="recorded", grant_kind="payment_fact", plan_code="1_month",
        activated_at=NOW - timedelta(days=10), duration_days=0, provider="lavatop",
        external_order_id="legacy-paid-replay",
        metadata_json='{"is_first_payment":true,"projection_already_applied":true}',
        created_at=NOW - timedelta(days=10), updated_at=NOW,
    )
    session.add_all([snapshot, fact])
    session.flush()

    replay = record_successful_payment_grant(
        session, account_id=account.id, legacy_tg_id=user.tg_id,
        provider="lavatop", order_id="legacy-paid-replay", plan_code="1_month",
        duration_days=30, paid_at=NOW,
    )

    assert replay.grant.grant_kind == "payment_fact"
    assert user.expiry_at == NOW + timedelta(days=20)
    assert user.sub_type == "PAID"
    session.close()
    engine.dispose()


def test_future_legacy_free_snapshot_is_only_fallback_after_bonus_reversal(tmp_path: Path) -> None:
    from economy_service import reverse_due_channel_grants
    from models import AccessKey, EntitlementGrant

    engine, session = _session(tmp_path)
    account, user = _seed_account(session, suffix=47, expiry_days=25)
    user.current_plan_code = "free_monthly"
    user.free_cycle_next_reset_at = None
    key = AccessKey(
        tg_id=user.tg_id, key_uuid=str(uuid.uuid4()), panel_email="legacy-free-fallback@example.test",
        node_code="NL-free", pool_code="premium_pool", state="active", source="test",
        is_primary=True, created_at=NOW, updated_at=NOW,
    )
    free_snapshot = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="legacy-free-fallback", source="legacy_snapshot", status="active",
        grant_kind="access_snapshot", plan_code="free_monthly", starts_at=NOW,
        expires_at=NOW + timedelta(days=25), duration_days=25,
        metadata_json='{"sub_type":"FREE"}', created_at=NOW, updated_at=NOW,
    )
    channel = EntitlementGrant(
        id=str(uuid.uuid4()), account_id=account.id, legacy_tg_id=user.tg_id,
        idempotency_key="legacy-free-channel", source="telegram_channel", status="grace",
        grant_kind="premium_bonus", plan_code="channel_bonus", starts_at=NOW,
        expires_at=NOW + timedelta(days=5), activated_at=NOW, duration_days=5,
        provider="telegram_membership", metadata_json=f'{{"grace_until":"{NOW.isoformat()}"}}',
        created_at=NOW, updated_at=NOW,
    )
    session.add_all([key, free_snapshot, channel])
    session.flush()

    assert reverse_due_channel_grants(session, now=NOW) == {"reversed": 1, "waiting": 0}
    assert user.expiry_at == NOW + timedelta(days=25)
    assert user.sub_type == "FREE"
    assert user.current_plan_code == "free_monthly"
    assert key.pool_code == "free_pool"
    session.close()
    engine.dispose()
