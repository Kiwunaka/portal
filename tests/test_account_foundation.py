from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


import account_foundation_service as account_foundation_module  # noqa: E402
import migrations as migrations_module  # noqa: E402
from account_foundation_service import (  # noqa: E402
    ACCOUNT_FOUNDATION_BACKFILL_KEY,
    _acquire_postgres_advisory_lock,
    _merge_duplicate_identity_state,
    _move_account_owned_rows,
    backfill_account_foundation,
    ensure_user_account_foundation,
    run_account_foundation_backfill_once,
)
from migrations import run_migrations  # noqa: E402
from models import (  # noqa: E402
    Account,
    AccountDevice,
    AccountIdentity,
    AccountMergeReview,
    AntiAbuseAction,
    AntiAbuseCase,
    AntiAbuseEvent,
    AppSetting,
    AuthSession,
    Base,
    EntitlementGrant,
    ExternalOrder,
    NodeProvisioningJob,
    ReferralRelationship,
    ReferralTransition,
    RecoveryCode,
    RewardAccountState,
    User,
    WebEmailIdentity,
)


def _session_for(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'account-foundation.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _record_projection_lock_events(session, monkeypatch) -> list[tuple[object, ...]]:
    events: list[tuple[object, ...]] = []

    def _capture_row_lock(orm_execute_state) -> None:
        statement = orm_execute_state.statement
        if getattr(statement, "_for_update_arg", None) is not None:
            events.append(("rows", str(statement)))

    def _capture_advisory_lock(_session, lock_key: str, *, shared: bool = False) -> None:
        events.append(("lock", str(lock_key), bool(shared)))

    event.listen(session, "do_orm_execute", _capture_row_lock)
    monkeypatch.setattr(
        account_foundation_module,
        "_acquire_postgres_advisory_lock",
        _capture_advisory_lock,
    )
    return events


def test_account_foundation_collected_modules_match_runtime_modules() -> None:
    import economy_service as economy_module
    import models as models_module

    assert models_module.Account is Account
    assert models_module.User is User
    assert models_module.EntitlementGrant is EntitlementGrant
    assert sys.modules["account_foundation_service"] is account_foundation_module
    assert economy_module.User is User
    assert economy_module.EntitlementGrant is EntitlementGrant


def _user(
    tg_id: int,
    *,
    now: datetime,
    app_install_id: str | None = None,
    linked_telegram_id: int | None = None,
    plan: str = "trial",
    expiry_days: int = 5,
) -> User:
    return User(
        tg_id=tg_id,
        username=f"user_{tg_id}",
        uuid=f"00000000-0000-0000-0000-{tg_id:012d}",
        email=f"USER_{tg_id}@telegram.local",
        sub_type="PAID" if plan == "paid" else "FREE",
        current_plan_code=plan,
        created_at=now,
        expiry_at=now + timedelta(days=expiry_days),
        is_active=True,
        trial_used=True,
        first_purchase_done=plan == "paid",
        is_app_user=app_install_id is not None,
        app_install_id=app_install_id,
        app_device_name="Test device" if app_install_id else None,
        app_platform="windows" if app_install_id else None,
        app_os_version="11" if app_install_id else None,
        app_version="1.0.0-beta" if app_install_id else None,
        app_locale="ru" if app_install_id else None,
        app_timezone="Europe/Moscow" if app_install_id else None,
        app_last_seen_at=now if app_install_id else None,
        route_mode="all_traffic" if app_install_id else None,
        linked_telegram_id=linked_telegram_id,
        linked_telegram_linked_at=now if linked_telegram_id else None,
    )


def test_account_foundation_models_cover_release_contract() -> None:
    tables = Base.metadata.tables

    for table_name in (
        "accounts",
        "account_identities",
        "account_devices",
        "auth_sessions",
        "recovery_codes",
        "entitlement_grants",
        "account_entitlement_grants",
        "antiabuse_events",
        "antiabuse_cases",
        "antiabuse_actions",
        "account_merge_reviews",
    ):
        assert table_name in tables

    assert "account_id" in tables["users"].c
    assert {"refresh_token_hash", "refresh_family_id", "reuse_detected_at", "revoked_at"} <= set(
        tables["auth_sessions"].c.keys()
    )
    assert {"code_hmac", "code_hint", "status", "used_at"} <= set(tables["recovery_codes"].c.keys())
    assert {"idempotency_key", "source", "status", "expires_at", "reversed_at"} <= set(
        tables["account_entitlement_grants"].c.keys()
    )
    assert {
        "raw_ip",
        "raw_ip_expires_at",
        "ip_full_hmac",
        "ip_prefix_hmac",
        "hmac_version",
    } <= set(tables["antiabuse_events"].c.keys())


def test_legacy_entitlement_table_is_preserved_beside_account_ledger(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-entitlements.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE entitlement_grants ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "tg_id BIGINT NOT NULL, "
                "activation_key_code VARCHAR(64) NOT NULL, "
                "plan_code VARCHAR(32) NOT NULL, "
                "source VARCHAR(32), "
                "duration_days INTEGER NOT NULL, "
                "granted_from DATETIME NOT NULL, "
                "granted_until DATETIME NOT NULL, "
                "meta_json TEXT, "
                "created_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO entitlement_grants "
                "(tg_id, activation_key_code, plan_code, source, duration_days, "
                "granted_from, granted_until, created_at) "
                "VALUES (42, 'legacy-key', 'legacy-paid', 'legacy', 30, "
                "'2026-06-01 00:00:00', '2026-07-01 00:00:00', '2026-06-01 00:00:00')"
            )
        )

    Base.metadata.create_all(engine)
    run_migrations(engine)

    inspector = inspect(engine)
    assert inspector.has_table("entitlement_grants")
    assert inspector.has_table("account_entitlement_grants")
    assert {column["name"] for column in inspector.get_columns("entitlement_grants")} == {
        "id",
        "tg_id",
        "activation_key_code",
        "plan_code",
        "source",
        "duration_days",
        "granted_from",
        "granted_until",
        "meta_json",
        "created_at",
    }
    assert {"account_id", "idempotency_key", "grant_kind", "status"} <= {
        column["name"] for column in inspector.get_columns("account_entitlement_grants")
    }
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM entitlement_grants")).scalar_one() == 1
    engine.dispose()


def _trial_grant(
    *,
    grant_id: str,
    account_id: str,
    status: str,
    now: datetime,
    activated_at: datetime | None = None,
) -> EntitlementGrant:
    effective_activation = activated_at
    if status == "expired" and effective_activation is None:
        effective_activation = now - timedelta(days=10)
    return EntitlementGrant(
        id=grant_id,
        account_id=account_id,
        idempotency_key=f"trial:{grant_id}",
        source="premium_trial",
        status=status,
        grant_kind="premium_trial",
        plan_code="trial",
        reserved_at=now,
        reservation_expires_at=now + timedelta(days=7),
        activated_at=effective_activation,
        starts_at=effective_activation,
        expires_at=effective_activation + timedelta(days=5) if effective_activation else None,
        duration_days=5,
        created_at=now,
        updated_at=now,
    )


def test_account_merge_keeps_strongest_reward_state_and_requeues_running_job(
    tmp_path: Path,
) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 20, 12, 0, 0)
    merge_now = now + timedelta(hours=1)
    target = Account(
        id="reward-merge-target",
        status="active",
        created_source="test",
        created_at=now,
        updated_at=now,
    )
    source = Account(
        id="reward-merge-source",
        status="active",
        created_source="test",
        created_at=now,
        updated_at=now,
    )
    target_grant = EntitlementGrant(
        id="reward-target-wheel-grant",
        account_id=target.id,
        idempotency_key="reward-wheel:v1:merge-target",
        source="bonus_wheel",
        status="active",
        grant_kind="premium_bonus",
        duration_days=1,
        starts_at=now,
        expires_at=now + timedelta(days=1),
        created_at=now,
        updated_at=now,
    )
    source_grant = EntitlementGrant(
        id="reward-source-wheel-grant",
        account_id=source.id,
        idempotency_key="reward-wheel:v1:merge-source",
        source="bonus_wheel",
        status="active",
        grant_kind="premium_bonus",
        duration_days=7,
        starts_at=now,
        expires_at=now + timedelta(days=7),
        created_at=now,
        updated_at=now,
    )
    target_state = RewardAccountState(
        account_id=target.id,
        wheel_last_spin_at=now - timedelta(days=4),
        wheel_last_grant_id=target_grant.id,
        calendar_last_check_date=date(2026, 7, 19),
        calendar_cycle_started_on=date(2026, 7, 13),
        calendar_cycle_day=7,
        calendar_first_checkin_at=now - timedelta(days=40),
        calendar_streak_7_unlocked_at=now - timedelta(days=5),
        created_at=now - timedelta(days=40),
        updated_at=now,
    )
    source_state = RewardAccountState(
        account_id=source.id,
        wheel_last_spin_at=now - timedelta(days=2),
        wheel_last_grant_id=source_grant.id,
        calendar_last_check_date=date(2026, 7, 19),
        calendar_cycle_started_on=date(2026, 7, 6),
        calendar_cycle_day=14,
        calendar_first_checkin_at=now - timedelta(days=20),
        calendar_streak_7_unlocked_at=now - timedelta(days=10),
        created_at=now - timedelta(days=20),
        updated_at=now,
    )
    reward_job = NodeProvisioningJob(
        account_id=source.id,
        entitlement_grant_id=source_grant.id,
        job_type="reward_entitlement_sync",
        status="running",
        idempotency_key=f"reward-entitlement-sync:v1:{source_grant.id}",
        attempts=2,
        locked_at=now,
        lock_token="stale-source-worker",
        created_at=now,
        updated_at=now,
    )
    session.add_all(
        [
            target,
            source,
            target_grant,
            source_grant,
            target_state,
            source_state,
            reward_job,
        ]
    )
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=merge_now,
    )
    session.flush()
    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=merge_now + timedelta(hours=1),
    )
    session.flush()

    state = session.get(RewardAccountState, target.id)
    assert state is not None
    assert session.get(RewardAccountState, source.id) is None
    assert state.wheel_last_spin_at == source_state.wheel_last_spin_at
    assert state.wheel_last_grant_id == source_grant.id
    assert state.calendar_last_check_date == date(2026, 7, 19)
    assert state.calendar_cycle_started_on == date(2026, 7, 6)
    assert state.calendar_cycle_day == 14
    assert state.calendar_first_checkin_at == now - timedelta(days=40)
    assert state.calendar_streak_7_unlocked_at == now - timedelta(days=10)

    job = session.query(NodeProvisioningJob).filter_by(entitlement_grant_id=source_grant.id).one()
    assert job.account_id == target.id
    assert job.status == "queued"
    assert job.attempts == 2
    assert job.locked_at is None
    assert job.lock_token is None
    assert job.next_run_at == merge_now
    assert job.idempotency_key == f"reward-entitlement-sync:v1:{source_grant.id}"
    session.expire(source_grant)
    assert source_grant.account_id == target.id

    session.close()
    engine.dispose()


def test_account_merge_reconciles_duplicate_trial_authority_and_is_rerunnable(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="target-account", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="source-account", status="active", created_source="test", created_at=now, updated_at=now)
    target_reserved = _trial_grant(grant_id="target-reserved", account_id=target.id, status="reserved", now=now)
    source_active = _trial_grant(
        grant_id="source-active",
        account_id=source.id,
        status="active",
        now=now + timedelta(hours=1),
        activated_at=now + timedelta(hours=2),
    )
    session.add_all([target, source, target_reserved, source_active])
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=3),
    )
    session.flush()
    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=4),
    )
    session.flush()

    canonical = session.query(EntitlementGrant).filter_by(account_id=target.id, source="premium_trial").all()
    assert [grant.id for grant in canonical] == ["source-active"]
    session.refresh(target_reserved)
    assert target_reserved.status == "superseded"
    assert target_reserved.source == "premium_trial_superseded"
    assert target_reserved.reversed_at == now + timedelta(hours=3)
    assert target_reserved.reversal_reason == "account_merge_duplicate"
    assert "source-active" in str(target_reserved.metadata_json)

    second_target = Account(id="target-active-account", status="active", created_source="test", created_at=now, updated_at=now)
    second_source = Account(id="source-reserved-account", status="active", created_source="test", created_at=now, updated_at=now)
    target_active = _trial_grant(
        grant_id="target-active",
        account_id=second_target.id,
        status="active",
        now=now,
        activated_at=now + timedelta(minutes=30),
    )
    source_reserved = _trial_grant(
        grant_id="source-reserved",
        account_id=second_source.id,
        status="reserved",
        now=now + timedelta(hours=1),
    )
    session.add_all([second_target, second_source, target_active, source_reserved])
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=second_source.id,
        target_account_id=second_target.id,
        now=now + timedelta(hours=2),
    )
    session.flush()

    canonical = session.query(EntitlementGrant).filter_by(
        account_id=second_target.id,
        source="premium_trial",
    ).all()
    assert [grant.id for grant in canonical] == ["target-active"]
    session.refresh(source_reserved)
    assert source_reserved.status == "superseded"
    session.close()
    engine.dispose()


def test_account_merge_moves_referral_authority_and_grandfather_backfill_is_idempotent(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="merge-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="merge-source", status="active", created_source="test", created_at=now, updated_at=now)
    referrer = Account(id="merge-referrer", status="active", created_source="test", created_at=now, updated_at=now)
    user = _user(7001, now=now)
    user.account_id = source.id
    user.channel_bonus_claimed_at = now - timedelta(days=2)
    user.channel_bonus_active = True
    user.channel_bonus_expires_at = now + timedelta(days=8)
    relationship = ReferralRelationship(
        id="relationship-merge",
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        status="linked",
        review_status="clear",
        created_at=now,
        updated_at=now,
    )
    transition = ReferralTransition(
        id="transition-merge",
        relationship_id=relationship.id,
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        transition_key="transition:merge",
        transition_kind="relationship_linked",
        status="linked",
        occurred_at=now,
        created_at=now,
    )
    session.add_all([target, source, referrer, user, relationship, transition])
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=1),
    )
    user.account_id = target.id
    session.flush()
    first = ensure_user_account_foundation(session, user, now=now + timedelta(hours=2))
    session.flush()
    second = ensure_user_account_foundation(session, user, now=now + timedelta(hours=3))
    session.flush()

    session.refresh(relationship)
    session.refresh(transition)
    assert relationship.referred_account_id == target.id
    assert transition.referred_account_id == target.id
    grandfathered = session.query(EntitlementGrant).filter_by(source="telegram_channel_grandfathered").all()
    assert len(grandfathered) == 1
    assert grandfathered[0].duration_days == 10
    assert grandfathered[0].account_id == target.id
    assert first.grants_created >= 1
    assert second.grants_created == 0
    session.close()
    engine.dispose()


def test_account_merge_dedupes_channel_and_same_referrer_authority(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="dedupe-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="dedupe-source", status="active", created_source="test", created_at=now, updated_at=now)
    referrer = Account(id="dedupe-referrer", status="active", created_source="test", created_at=now, updated_at=now)
    target_relationship = ReferralRelationship(
        id="dedupe-rel-target",
        referred_account_id=target.id,
        referrer_account_id=referrer.id,
        source="app_projection",
        status="linked",
        review_status="clear",
        created_at=now,
        updated_at=now,
    )
    source_relationship = ReferralRelationship(
        id="dedupe-rel-source",
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        status="linked",
        review_status="clear",
        created_at=now + timedelta(minutes=1),
        updated_at=now + timedelta(minutes=1),
    )
    target_grant = EntitlementGrant(
        id="dedupe-channel-target",
        account_id=target.id,
        idempotency_key=f"channel-grant:v2:{target.id}",
        source="telegram_channel",
        status="active",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=now,
        expires_at=now + timedelta(days=5),
        duration_days=5,
        created_at=now,
        updated_at=now,
    )
    source_grant = EntitlementGrant(
        id="dedupe-channel-source",
        account_id=source.id,
        idempotency_key=f"channel-grant:v1-grandfathered:{source.id}",
        source="telegram_channel_grandfathered",
        status="active",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=now,
        expires_at=now + timedelta(days=10),
        duration_days=10,
        created_at=now,
        updated_at=now,
    )
    transition = ReferralTransition(
        id="dedupe-transition-source",
        relationship_id=source_relationship.id,
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        transition_key="dedupe-transition-source",
        transition_kind="relationship_linked",
        status="linked",
        occurred_at=now,
        created_at=now,
    )
    session.add_all(
        [target, source, referrer, target_relationship, source_relationship, target_grant, source_grant, transition]
    )
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=1),
    )
    session.flush()
    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=2),
    )
    session.flush()

    relationships = session.query(ReferralRelationship).filter_by(referred_account_id=target.id).all()
    retained_source = session.query(ReferralRelationship).filter_by(id=source_relationship.id).one()
    channel_grants = (
        session.query(EntitlementGrant)
        .filter(
            EntitlementGrant.account_id == target.id,
            EntitlementGrant.source.in_(["telegram_channel", "telegram_channel_grandfathered"]),
        )
        .all()
    )
    session.refresh(transition)
    assert len(relationships) == 1
    assert relationships[0].referrer_account_id == referrer.id
    assert retained_source.referred_account_id == source.id
    assert retained_source.referrer_account_id == referrer.id
    assert retained_source.status == "superseded"
    assert retained_source.review_status == "review"
    assert transition.relationship_id == retained_source.id
    assert transition.referred_account_id == source.id
    assert len(channel_grants) == 1
    assert channel_grants[0].duration_days == 10
    assert channel_grants[0].source == "telegram_channel_grandfathered"
    session.close()
    engine.dispose()


def test_account_merge_prefers_active_channel_over_revoked_grandfathered_grant(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="channel-rank-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="channel-rank-source", status="active", created_source="test", created_at=now, updated_at=now)
    active = EntitlementGrant(
        id="channel-rank-active",
        account_id=target.id,
        idempotency_key=f"channel-grant:v2:{target.id}",
        source="telegram_channel",
        status="active",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=now,
        expires_at=now + timedelta(days=5),
        duration_days=5,
        created_at=now,
        updated_at=now,
    )
    revoked = EntitlementGrant(
        id="channel-rank-revoked",
        account_id=source.id,
        idempotency_key=f"channel-grant:v1-grandfathered:{source.id}",
        source="telegram_channel_grandfathered",
        status="reversed",
        grant_kind="premium_bonus",
        plan_code="channel_bonus",
        starts_at=now,
        expires_at=now + timedelta(days=10),
        duration_days=10,
        reversed_at=now + timedelta(hours=1),
        reversal_reason="channel_membership_lost",
        created_at=now,
        updated_at=now + timedelta(hours=1),
    )
    session.add_all([target, source, active, revoked])
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=2),
    )
    session.flush()

    session.refresh(active)
    session.refresh(revoked)
    assert active.account_id == target.id
    assert active.source == "telegram_channel"
    assert active.status == "active"
    assert revoked.source == "telegram_channel_superseded"
    assert revoked.status == "superseded"
    session.close()
    engine.dispose()


def test_account_merge_dedupes_friend_and_referrer_grants_and_repairs_pointers(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="reward-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="reward-source", status="active", created_source="test", created_at=now, updated_at=now)
    referrer = Account(id="reward-referrer", status="active", created_source="test", created_at=now, updated_at=now)
    referrer_user = _user(7044, now=now, plan="trial", expiry_days=30)
    referrer_user.account_id = referrer.id
    referrer_user.sub_type = "BONUS"
    referrer_user.current_plan_code = "referral_referrer"
    target_relationship = ReferralRelationship(
        id="reward-rel-target",
        referred_account_id=target.id,
        referrer_account_id=referrer.id,
        source="app_projection",
        status="rewarded",
        review_status="clear",
        friend_grant_id="friend-target",
        referrer_grant_id="referrer-target",
        created_at=now,
        updated_at=now,
    )
    source_relationship = ReferralRelationship(
        id="reward-rel-source",
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        status="rewarded",
        review_status="clear",
        friend_grant_id="friend-source",
        referrer_grant_id="referrer-source",
        created_at=now + timedelta(minutes=1),
        updated_at=now + timedelta(minutes=1),
    )

    def grant(
        *,
        grant_id: str,
        account_id: str,
        key: str,
        source_name: str,
        days: int,
        starts_after_days: int = 0,
    ) -> EntitlementGrant:
        starts_at = now + timedelta(days=starts_after_days)
        return EntitlementGrant(
            id=grant_id,
            account_id=account_id,
            idempotency_key=key,
            source=source_name,
            status="active",
            grant_kind="premium_bonus",
            plan_code=source_name,
            starts_at=starts_at,
            expires_at=starts_at + timedelta(days=days),
            duration_days=days,
            created_at=now,
            updated_at=now,
        )

    rows = [
        grant(grant_id="friend-target", account_id=target.id, key=f"referral-friend:v1:{target.id}", source_name="referral_friend", days=5),
        grant(grant_id="friend-source", account_id=source.id, key=f"referral-friend:v1:{source.id}", source_name="referral_friend", days=5, starts_after_days=5),
        grant(grant_id="referrer-target", account_id=referrer.id, key=f"referral-referrer:v1:{target.id}", source_name="referral_referrer", days=15),
        grant(grant_id="referrer-source", account_id=referrer.id, key=f"referral-referrer:v1:{source.id}", source_name="referral_referrer", days=15, starts_after_days=15),
    ]
    session.add_all([target, source, referrer, referrer_user, target_relationship, source_relationship, *rows])
    session.flush()

    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=1),
    )
    session.flush()

    canonical = session.query(ReferralRelationship).filter_by(referred_account_id=target.id).one()
    friend_active = session.query(EntitlementGrant).filter_by(source="referral_friend", status="active").all()
    referrer_active = session.query(EntitlementGrant).filter_by(source="referral_referrer", status="active").all()
    assert len(friend_active) == 1
    assert len(referrer_active) == 1
    assert canonical.friend_grant_id == friend_active[0].id
    assert canonical.referrer_grant_id == referrer_active[0].id
    assert friend_active[0].idempotency_key == f"referral-friend:v1:{target.id}"
    assert referrer_active[0].idempotency_key == f"referral-referrer:v1:{target.id}"
    assert session.query(EntitlementGrant).filter_by(source="referral_friend_superseded", status="superseded").count() == 1
    assert session.query(EntitlementGrant).filter_by(source="referral_referrer_superseded", status="superseded").count() == 1
    assert referrer_user.expiry_at == now + timedelta(hours=1, days=15)
    session.close()
    engine.dispose()


def test_grandfathered_channel_backfill_splits_snapshot_before_reversal(tmp_path: Path) -> None:
    from economy_service import begin_channel_loss_grace, reverse_due_channel_grants

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    user = _user(7099, now=now, plan="trial", expiry_days=7)
    user.sub_type = "BONUS"
    user.current_plan_code = "channel_bonus"
    user.channel_bonus_claimed_at = now - timedelta(days=3)
    user.channel_bonus_active = True
    user.channel_bonus_expires_at = now + timedelta(days=7)
    session.add(user)
    session.flush()

    ensure_user_account_foundation(session, user, now=now)
    session.flush()
    snapshot = session.query(EntitlementGrant).filter_by(source="legacy_snapshot").one()
    channel = session.query(EntitlementGrant).filter_by(source="telegram_channel_grandfathered").one()
    assert snapshot.expires_at == channel.starts_at
    assert '"telegram_channel_grandfathered"' in str(snapshot.metadata_json)

    begin_channel_loss_grace(session, account_id=str(user.account_id), now=now)
    reversal_at = now + timedelta(hours=24)
    result = reverse_due_channel_grants(session, now=reversal_at)

    assert result == {"reversed": 1, "waiting": 0}
    assert channel.status == "reversed"
    assert user.expiry_at == reversal_at
    assert user.expiry_at != user.channel_bonus_expires_at
    session.close()
    engine.dispose()


def test_account_merge_reconciles_full_referral_field_and_transition_matrix_idempotently(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="matrix-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="matrix-source", status="active", created_source="test", created_at=now, updated_at=now)
    referrer = Account(id="matrix-referrer", status="active", created_source="test", created_at=now, updated_at=now)
    target_relationship = ReferralRelationship(
        id="matrix-target-rel",
        referred_account_id=target.id,
        referrer_account_id=referrer.id,
        source="app_projection",
        status="linked",
        review_status="clear",
        friend_evidence_id="friend-evidence",
        friend_grant_id="friend-grant",
        friend_granted_at=now + timedelta(hours=1),
        created_at=now,
        updated_at=now + timedelta(hours=1),
    )
    source_relationship = ReferralRelationship(
        id="matrix-source-rel",
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        source="bot_code",
        status="rewarded",
        review_status="wait",
        first_payment_key="lavatop:matrix-first",
        first_payment_at=now + timedelta(hours=2),
        hold_until=now + timedelta(hours=74),
        referrer_grant_id="referrer-grant",
        referrer_granted_at=now + timedelta(hours=75),
        created_at=now + timedelta(minutes=1),
        updated_at=now + timedelta(hours=75),
    )
    target_transition = ReferralTransition(
        id="matrix-target-transition",
        relationship_id=target_relationship.id,
        referred_account_id=target.id,
        referrer_account_id=referrer.id,
        transition_key=f"referral-first-payment:v1:{target.id}",
        transition_kind="first_payment_held",
        status="holding",
        occurred_at=now + timedelta(hours=2),
        created_at=now + timedelta(hours=2),
    )
    source_transition = ReferralTransition(
        id="matrix-source-transition",
        relationship_id=source_relationship.id,
        referred_account_id=source.id,
        referrer_account_id=referrer.id,
        transition_key=f"referral-first-payment:v1:{source.id}",
        transition_kind="referrer_reward_released",
        status="released",
        occurred_at=now + timedelta(hours=75),
        created_at=now + timedelta(hours=75),
    )
    session.add_all([target, source, referrer, target_relationship, source_relationship, target_transition, source_transition])
    session.flush()

    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(days=4))
    session.flush()
    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(days=5))
    session.flush()

    relationship = session.query(ReferralRelationship).filter_by(referred_account_id=target.id).one()
    transitions = session.query(ReferralTransition).filter_by(relationship_id=relationship.id).order_by(ReferralTransition.id).all()
    source_transitions = session.query(ReferralTransition).filter_by(relationship_id=source_relationship.id).all()
    assert relationship.friend_evidence_id == "friend-evidence"
    assert relationship.friend_grant_id == "friend-grant"
    assert relationship.first_payment_key == "lavatop:matrix-first"
    assert relationship.hold_until == now + timedelta(hours=74)
    assert relationship.referrer_grant_id == "referrer-grant"
    assert relationship.referrer_granted_at == now + timedelta(hours=75)
    assert relationship.status == "rewarded"
    assert relationship.review_status == "wait"
    assert len(transitions) == 1
    assert transitions[0].id == target_transition.id
    assert len(source_transitions) == 3
    assert source_transition in source_transitions
    assert all(row.referred_account_id == source.id for row in source_transitions)
    assert session.query(ReferralRelationship).filter_by(id=source_relationship.id, status="superseded").count() == 1
    session.close()
    engine.dispose()


def test_account_merge_removes_self_referral_and_breaks_new_cycle(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="graph-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="graph-source", status="active", created_source="test", created_at=now, updated_at=now)
    child = Account(id="graph-child", status="active", created_source="test", created_at=now, updated_at=now)
    self_after_merge = ReferralRelationship(
        id="graph-self",
        referred_account_id=target.id,
        referrer_account_id=source.id,
        source="bot_code",
        status="linked",
        review_status="clear",
        created_at=now,
        updated_at=now,
    )
    child_to_source = ReferralRelationship(
        id="graph-child-rel",
        referred_account_id=child.id,
        referrer_account_id=source.id,
        source="bot_code",
        status="linked",
        review_status="clear",
        created_at=now,
        updated_at=now,
    )
    source_to_child = ReferralRelationship(
        id="graph-source-rel",
        referred_account_id=source.id,
        referrer_account_id=child.id,
        source="bot_code",
        status="linked",
        review_status="clear",
        created_at=now,
        updated_at=now,
    )
    transitions = [
        ReferralTransition(
            id=f"{relationship.id}-transition",
            relationship_id=relationship.id,
            referred_account_id=relationship.referred_account_id,
            referrer_account_id=relationship.referrer_account_id,
            transition_key=f"{relationship.id}:linked",
            transition_kind="relationship_linked",
            status="linked",
            occurred_at=now,
            created_at=now,
        )
        for relationship in (self_after_merge, child_to_source, source_to_child)
    ]
    session.add_all([target, source, child, self_after_merge, child_to_source, source_to_child, *transitions])
    session.flush()

    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(hours=1))
    session.flush()

    rows = session.query(ReferralRelationship).all()
    assert {row.id for row in rows} == {"graph-self", "graph-child-rel", "graph-source-rel"}
    terminal = {row.id for row in rows if row.status in {"superseded", "rejected"}}
    assert terminal
    active_rows = [row for row in rows if row.status not in {"superseded", "rejected"}]
    assert all(row.referred_account_id != row.referrer_account_id for row in active_rows)
    parents = {row.referred_account_id: row.referrer_account_id for row in active_rows}
    for start in parents:
        seen: set[str] = set()
        cursor = start
        while cursor in parents:
            assert cursor not in seen
            seen.add(cursor)
            cursor = parents[cursor]
    orphan_count = (
        session.query(ReferralTransition)
        .outerjoin(ReferralRelationship, ReferralTransition.relationship_id == ReferralRelationship.id)
        .filter(ReferralRelationship.id.is_(None))
        .count()
    )
    assert orphan_count == 0
    _move_account_owned_rows(
        session,
        source_account_id=source.id,
        target_account_id=target.id,
        now=now + timedelta(hours=2),
    )
    session.flush()
    assert session.query(ReferralRelationship).count() == 3
    assert session.query(ReferralTransition).count() >= 3
    session.close()
    engine.dispose()


def test_account_merge_conflicting_referrers_keeps_strongest_and_snapshots_loser(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="conflict-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="conflict-source", status="active", created_source="test", created_at=now, updated_at=now)
    target_referrer = Account(id="conflict-ref-a", status="active", created_source="test", created_at=now, updated_at=now)
    source_referrer = Account(id="conflict-ref-b", status="active", created_source="test", created_at=now, updated_at=now)
    target_relationship = ReferralRelationship(
        id="conflict-target-rel",
        referred_account_id=target.id,
        referrer_account_id=target_referrer.id,
        source="app_projection",
        status="holding",
        review_status="clear",
        first_payment_key="lavatop:target-payment",
        first_payment_at=now,
        hold_until=now + timedelta(hours=72),
        created_at=now,
        updated_at=now,
    )
    source_relationship = ReferralRelationship(
        id="conflict-source-rel",
        referred_account_id=source.id,
        referrer_account_id=source_referrer.id,
        source="bot_code",
        status="rewarded",
        review_status="reject",
        friend_grant_id="source-friend-grant",
        referrer_grant_id="source-referrer-grant",
        referrer_granted_at=now + timedelta(days=4),
        created_at=now,
        updated_at=now + timedelta(days=4),
    )
    session.add_all([target, source, target_referrer, source_referrer, target_relationship, source_relationship])
    session.flush()

    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(days=5))
    session.flush()
    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(days=6))
    session.flush()

    relationship = session.query(ReferralRelationship).filter_by(referred_account_id=target.id).one()
    snapshot = session.query(ReferralTransition).filter_by(transition_kind="relationship_merge_superseded").one()
    reviews = session.query(AccountMergeReview).filter_by(reason_code="referral_merge_conflict").all()
    assert relationship.referrer_account_id == source_referrer.id
    assert relationship.status == "rewarded"
    assert relationship.review_status == "reject"
    assert relationship.friend_grant_id == "source-friend-grant"
    assert relationship.referrer_grant_id == "source-referrer-grant"
    assert snapshot.relationship_id == source_relationship.id
    assert "lavatop:target-payment" in str(snapshot.metadata_json)
    assert len(reviews) == 1
    session.close()
    engine.dispose()


def test_flag_only_legacy_purchase_creates_review_marker_not_payment_authority(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship, record_successful_payment_grant

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    referrer = _user(8100, now=now, plan="paid", expiry_days=30)
    historical_gift = _user(8101, now=now, plan="paid", expiry_days=30)
    historical_gift.referrer_id = referrer.tg_id
    session.add_all([referrer, historical_gift])
    session.commit()

    first = backfill_account_foundation(session, now=now)
    session.commit()
    second = backfill_account_foundation(session, now=now + timedelta(hours=1))
    session.commit()
    session.refresh(referrer)
    session.refresh(historical_gift)

    assert session.query(EntitlementGrant).filter_by(
        account_id=historical_gift.account_id, source="provider_payment"
    ).count() == 0
    marker = session.query(EntitlementGrant).filter_by(
        account_id=historical_gift.account_id, source="legacy_first_purchase_marker"
    ).one()
    assert marker.status == "manual_review"
    assert marker.grant_kind == "audit_marker"
    assert second.grants_created == 0

    create_referral_relationship(
        session,
        referred_account_id=str(historical_gift.account_id),
        referrer_account_id=str(referrer.account_id),
        source="legacy_projection_test",
        now=now + timedelta(hours=2),
    )
    payment = record_successful_payment_grant(
        session,
        account_id=str(historical_gift.account_id),
        legacy_tg_id=historical_gift.tg_id,
        provider="lavatop",
        order_id="gift-flag-real-first",
        plan_code="1_month",
        duration_days=30,
        paid_at=now + timedelta(hours=2),
    )
    assert payment.is_first_payment is True
    assert payment.relationship is not None
    assert payment.relationship.status == "holding"
    assert payment.relationship.first_payment_key == "lavatop:gift-flag-real-first"
    assert first.grants_created >= 2
    session.close()
    engine.dispose()


def test_corroborated_historical_paid_order_backfills_one_account_payment_fact_for_linked_users(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    telegram = _user(8200, now=now, plan="paid", expiry_days=30)
    app = _user(
        9_000_000_008_200,
        now=now,
        app_install_id="historical-paid-linked",
        linked_telegram_id=telegram.tg_id,
        plan="trial",
    )
    order = ExternalOrder(
        order_id="historical-provider-order",
        tg_id=telegram.tg_id,
        provider="freekassa",
        plan_code="1_month",
        amount=249,
        currency="RUB",
        status="paid",
        created_at=now - timedelta(days=10),
        paid_at=now - timedelta(days=10),
    )
    session.add_all([telegram, app, order])
    session.commit()

    first = backfill_account_foundation(session, now=now)
    session.commit()
    second = backfill_account_foundation(session, now=now + timedelta(hours=1))
    session.commit()
    session.refresh(telegram)
    session.refresh(app)

    assert telegram.account_id == app.account_id
    facts = session.query(EntitlementGrant).filter_by(
        account_id=telegram.account_id, source="provider_payment"
    ).all()
    assert len(facts) == 1
    assert facts[0].provider == "freekassa"
    assert facts[0].external_order_id == "historical-provider-order"
    assert facts[0].status == "recorded"
    assert '"corroborated":true' in str(facts[0].metadata_json)
    assert session.query(EntitlementGrant).filter_by(
        account_id=telegram.account_id, source="legacy_first_purchase_marker"
    ).count() == 0
    assert second.grants_created == 0
    assert first.grants_created >= 3
    session.close()
    engine.dispose()


def test_fulfilled_historical_payment_backfill_then_callback_replay_does_not_append_days(tmp_path: Path) -> None:
    from economy_service import record_successful_payment_grant

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    user = _user(8300, now=now - timedelta(days=20), plan="paid", expiry_days=50)
    expected_expiry = user.expiry_at
    order = ExternalOrder(
        order_id="fulfilled-historical-order",
        tg_id=user.tg_id,
        provider="lavatop",
        plan_code="1_month",
        amount=249,
        currency="RUB",
        status="paid",
        meta_json='{"fulfillment":{"status":"account_extended"}}',
        created_at=now - timedelta(days=10),
        paid_at=now - timedelta(days=10),
    )
    session.add_all([user, order])
    session.commit()
    backfill_account_foundation(session, now=now)
    session.commit()
    session.refresh(user)
    fact = session.query(EntitlementGrant).filter_by(source="provider_payment").one()
    assert '"projection_already_applied":true' in str(fact.metadata_json)

    replay = record_successful_payment_grant(
        session,
        account_id=str(user.account_id),
        legacy_tg_id=user.tg_id,
        provider="lavatop",
        order_id=order.order_id,
        plan_code="1_month",
        duration_days=30,
        paid_at=order.paid_at,
    )

    assert replay.grant.id == fact.id
    assert user.expiry_at == expected_expiry
    assert replay.grant.duration_days == 0
    session.close()
    engine.dispose()


def test_pending_provider_order_after_legacy_gift_is_not_marked_projection_applied(tmp_path: Path) -> None:
    from economy_service import record_successful_payment_grant

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    user = _user(8302, now=now, plan="paid", expiry_days=20)
    gift_expiry = user.expiry_at
    order = ExternalOrder(
        order_id="gift-then-pending-provider-order",
        tg_id=user.tg_id,
        provider="lavatop",
        plan_code="1_month",
        amount=249,
        currency="RUB",
        status="paid",
        meta_json='{"fulfillment":{"mode":"account_extend","status":"pending_payment"}}',
        created_at=now,
        paid_at=now,
    )
    session.add_all([user, order])
    session.commit()
    backfill_account_foundation(session, now=now)
    session.commit()
    fact = session.query(EntitlementGrant).filter_by(source="provider_payment").one()
    assert '"projection_already_applied":false' in str(fact.metadata_json)

    payment = record_successful_payment_grant(
        session, account_id=str(user.account_id), legacy_tg_id=user.tg_id,
        provider="lavatop", order_id=order.order_id, plan_code="1_month",
        duration_days=30, paid_at=now,
    )

    assert payment.grant.grant_kind == "paid_access"
    assert payment.grant.starts_at == gift_expiry
    assert user.expiry_at == gift_expiry + timedelta(days=30)
    session.close()
    engine.dispose()


def test_ambiguous_historical_paid_stars_attempt_remains_review_safe_and_repairable(tmp_path: Path) -> None:
    from models import PayAttempt

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    user = _user(8303, now=now - timedelta(days=40), plan="paid", expiry_days=20)
    attempt = PayAttempt(
        tg_id=user.tg_id,
        source="bot",
        plan_code="1_month",
        amount_stars=299,
        currency="XTR",
        status="paid",
        invoice_payload="portal_1_month_8303_buy_a99",
        started_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=10),
        paid_at=now - timedelta(days=10),
    )
    session.add_all([user, attempt])
    session.commit()

    backfill_account_foundation(session, now=now)
    session.commit()
    backfill_account_foundation(session, now=now + timedelta(hours=1))
    session.commit()

    self_authority = session.query(EntitlementGrant).filter_by(
        account_id=user.account_id,
        source="provider_payment",
    ).all()
    markers = session.query(EntitlementGrant).filter_by(
        account_id=user.account_id,
        source="legacy_stars_payment_marker",
    ).all()
    assert self_authority == []
    assert len(markers) == 1
    assert markers[0].status == "manual_review"
    assert markers[0].grant_kind == "audit_marker"
    assert '"projection_already_applied":false' in str(markers[0].metadata_json)
    session.close()
    engine.dispose()


def test_callback_fact_survives_backfill_rerun_and_out_of_order_history_normalizes_first(tmp_path: Path) -> None:
    from economy_service import record_successful_payment_grant

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    user = _user(8301, now=now, plan="trial", expiry_days=0)
    user.first_purchase_done = False
    session.add(user)
    session.commit()
    ensure_user_account_foundation(session, user, now=now)
    session.flush()
    callback = record_successful_payment_grant(
        session,
        account_id=str(user.account_id),
        legacy_tg_id=user.tg_id,
        provider="lavatop",
        order_id="z-callback-first",
        plan_code="1_month",
        duration_days=30,
        paid_at=now,
    )
    session.add_all(
        [
            ExternalOrder(
                order_id="z-callback-first", tg_id=user.tg_id, provider="lavatop",
                plan_code="1_month", amount=249, currency="RUB", status="paid",
                created_at=now, paid_at=now,
            ),
            ExternalOrder(
                order_id="a-earlier-history", tg_id=user.tg_id, provider="freekassa",
                plan_code="1_month", amount=249, currency="RUB", status="paid",
                created_at=now - timedelta(days=2), paid_at=now - timedelta(days=2),
            ),
        ]
    )
    session.commit()
    expiry_after_callback = user.expiry_at

    backfill_account_foundation(session, now=now + timedelta(hours=1))
    session.commit()
    backfill_account_foundation(session, now=now + timedelta(hours=2))
    session.commit()

    facts = session.query(EntitlementGrant).filter_by(account_id=user.account_id, source="provider_payment").all()
    first = [row for row in facts if '"is_first_payment":true' in str(row.metadata_json)]
    assert len(facts) == 2
    assert len(first) == 1
    assert first[0].external_order_id == "a-earlier-history"
    assert user.expiry_at == expiry_after_callback
    assert callback.grant.grant_kind == "paid_access"
    session.close()
    engine.dispose()


def test_merge_two_paid_histories_normalizes_earliest_fact_and_existing_hold_idempotently(tmp_path: Path) -> None:
    from economy_service import create_referral_relationship, record_successful_payment_grant

    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    target = Account(id="payment-merge-target", status="active", created_source="test", created_at=now, updated_at=now)
    source = Account(id="payment-merge-source", status="active", created_source="test", created_at=now, updated_at=now)
    referrer = Account(id="payment-merge-referrer", status="active", created_source="test", created_at=now, updated_at=now)
    target_user = _user(8400, now=now, plan="trial", expiry_days=0)
    target_user.account_id = target.id
    source_user = _user(8401, now=now, plan="trial", expiry_days=0)
    source_user.account_id = source.id
    session.add_all([target, source, referrer, target_user, source_user])
    session.flush()
    relationship = create_referral_relationship(
        session,
        referred_account_id=target.id,
        referrer_account_id=referrer.id,
        source="test",
        now=now - timedelta(days=1),
    )
    later = record_successful_payment_grant(
        session, account_id=target.id, legacy_tg_id=target_user.tg_id,
        provider="lavatop", order_id="later-order", plan_code="1_month",
        duration_days=30, paid_at=now,
    )
    earlier = record_successful_payment_grant(
        session, account_id=source.id, legacy_tg_id=source_user.tg_id,
        provider="freekassa", order_id="earlier-order", plan_code="1_month",
        duration_days=30, paid_at=now - timedelta(days=3),
    )
    session.flush()
    assert later.is_first_payment is True and earlier.is_first_payment is True

    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(hours=1))
    session.flush()
    _move_account_owned_rows(session, source_account_id=source.id, target_account_id=target.id, now=now + timedelta(hours=2))
    session.flush()

    facts = session.query(EntitlementGrant).filter_by(account_id=target.id, source="provider_payment").all()
    first = [row for row in facts if '"is_first_payment":true' in str(row.metadata_json)]
    assert len(first) == 1
    assert first[0].external_order_id == "earlier-order"
    assert relationship.first_payment_key == "freekassa:earlier-order"
    assert relationship.first_payment_at == now - timedelta(days=3)
    assert relationship.hold_until == now - timedelta(days=3) + timedelta(hours=72)
    before_status = relationship.status
    replay = record_successful_payment_grant(
        session, account_id=target.id, legacy_tg_id=target_user.tg_id,
        provider="lavatop", order_id="later-order", plan_code="1_month",
        duration_days=30, paid_at=now + timedelta(hours=3),
    )
    assert replay.is_first_payment is False
    assert relationship.status == before_status
    assert relationship.first_payment_key == "freekassa:earlier-order"
    session.close()
    engine.dispose()


def test_account_merge_reconciles_every_trial_status_in_unique_source_set(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 12, 10, 0, 0)
    scenarios = (
        ("active-expired", "active", "expired", "active-expired-target"),
        ("reserved-expired", "reserved", "expired", "reserved-expired-target"),
        ("expired-expired", "expired", "expired", "expired-expired-target"),
        ("reversed-superseded", "reversed", "superseded", "reversed-superseded-target"),
    )

    for index, (label, target_status, source_status, expected_winner) in enumerate(scenarios):
        target_account_id = f"{label}-target-account"
        source_account_id = f"{label}-source-account"
        target = Account(
            id=target_account_id,
            status="active",
            created_source="test",
            created_at=now,
            updated_at=now,
        )
        source = Account(
            id=source_account_id,
            status="active",
            created_source="test",
            created_at=now,
            updated_at=now,
        )
        target_grant = _trial_grant(
            grant_id=f"{label}-target",
            account_id=target_account_id,
            status=target_status,
            now=now + timedelta(hours=index),
            activated_at=now - timedelta(days=10) if target_status in {"active", "expired"} else None,
        )
        source_grant = _trial_grant(
            grant_id=f"{label}-source",
            account_id=source_account_id,
            status=source_status,
            now=now + timedelta(hours=index + 1),
            activated_at=now - timedelta(days=9) if source_status == "expired" else None,
        )
        session.add_all([target, source, target_grant, source_grant])
        session.flush()

        _move_account_owned_rows(
            session,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            now=now + timedelta(days=1),
        )
        session.flush()
        _move_account_owned_rows(
            session,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            now=now + timedelta(days=2),
        )
        session.flush()

        canonical = session.query(EntitlementGrant).filter_by(
            account_id=target_account_id,
            source="premium_trial",
        ).all()
        assert [grant.id for grant in canonical] == [expected_winner]
        loser = source_grant if expected_winner == target_grant.id else target_grant
        session.refresh(loser)
        assert loser.source == "premium_trial_superseded"
        assert loser.status == "superseded"
        assert loser.reversal_reason == "account_merge_duplicate"
        assert expected_winner in str(loser.metadata_json)

    session.close()
    engine.dispose()


def test_backfill_is_idempotent_and_merges_explicit_telegram_link(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    direct_telegram = _user(1001, now=now, plan="paid", expiry_days=30)
    app_user = _user(
        9_000_000_000_001,
        now=now,
        app_install_id="install-linked-telegram",
        linked_telegram_id=1001,
    )
    session.add_all([direct_telegram, app_user])
    session.flush()
    session.add(
        WebEmailIdentity(
            email="Owner@Example.test",
            email_norm="owner@example.test",
            password_hash="unused-migration-hash",
            linked_tg_id=app_user.tg_id,
            is_verified=True,
            verified_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    first = backfill_account_foundation(session)
    session.commit()
    second = backfill_account_foundation(session)
    session.commit()

    session.refresh(direct_telegram)
    session.refresh(app_user)
    assert direct_telegram.account_id
    assert app_user.account_id == direct_telegram.account_id
    assert first.users_seen == 2
    assert second.accounts_created == 0
    assert second.identities_created == 0
    assert second.devices_created == 0
    assert second.grants_created == 0

    account_id = str(app_user.account_id)
    assert session.query(Account).filter(Account.id == account_id, Account.status == "active").count() == 1
    assert session.query(AccountIdentity).filter(AccountIdentity.account_id == account_id).count() == 4
    assert (
        session.query(AccountIdentity)
        .filter(
            AccountIdentity.account_id == account_id,
            AccountIdentity.kind == "telegram",
            AccountIdentity.subject_norm == "1001",
        )
        .count()
        == 1
    )
    assert (
        session.query(AccountIdentity)
        .filter(
            AccountIdentity.account_id == account_id,
            AccountIdentity.kind == "email",
            AccountIdentity.subject_norm == "owner@example.test",
        )
        .count()
        == 1
    )
    device = session.query(AccountDevice).filter_by(install_id="install-linked-telegram").one()
    assert device.account_id == account_id
    assert device.route_mode == "all_traffic"
    assert session.query(EntitlementGrant).filter_by(account_id=account_id).count() == 3
    marker = session.query(EntitlementGrant).filter_by(
        account_id=account_id, source="legacy_first_purchase_marker"
    ).one()
    assert marker.status == "manual_review"
    assert marker.grant_kind == "audit_marker"
    assert session.query(AccountMergeReview).count() == 0

    session.close()
    engine.dispose()


def test_late_explicit_link_absorbs_previous_account_without_losing_grants(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    direct_telegram = _user(2001, now=now, plan="paid", expiry_days=90)
    app_user = _user(
        9_000_000_000_002,
        now=now,
        app_install_id="install-linked-later",
    )
    session.add_all([direct_telegram, app_user])
    session.commit()

    backfill_account_foundation(session)
    session.commit()
    session.refresh(direct_telegram)
    session.refresh(app_user)
    expected_target_id = str(direct_telegram.account_id)
    blocked_source_id = str(app_user.account_id)
    old_account_ids = {expected_target_id, blocked_source_id}
    assert len(old_account_ids) == 2

    blocked_source = session.query(Account).filter_by(id=blocked_source_id).one()
    blocked_source.status = "blocked"
    blocked_source.auth_epoch = 4
    session.commit()

    app_user.linked_telegram_id = direct_telegram.tg_id
    app_user.linked_telegram_linked_at = now + timedelta(hours=1)
    session.commit()
    report = backfill_account_foundation(session)
    session.commit()
    session.refresh(direct_telegram)
    session.refresh(app_user)

    canonical_account_id = str(direct_telegram.account_id)
    assert canonical_account_id == expected_target_id
    assert app_user.account_id == canonical_account_id
    assert report.accounts_merged == 1
    absorbed_id = (old_account_ids - {canonical_account_id}).pop()
    absorbed = session.query(Account).filter_by(id=absorbed_id).one()
    assert absorbed.status == "merged"
    assert absorbed.merged_into_account_id == canonical_account_id
    canonical_account = session.query(Account).filter_by(id=canonical_account_id).one()
    assert canonical_account.status == "blocked"
    assert canonical_account.auth_epoch == 4
    assert session.query(EntitlementGrant).filter_by(account_id=canonical_account_id).count() == 3
    assert session.query(EntitlementGrant).filter_by(
        account_id=canonical_account_id, source="legacy_first_purchase_marker"
    ).count() == 1

    session.close()
    engine.dispose()


def test_duplicate_identity_merge_preserves_verified_and_disabled_state() -> None:
    now = datetime(2026, 7, 10, 15, 0, 0)
    verified_at = now - timedelta(days=2)
    disabled_at = now - timedelta(days=1)
    target = AccountIdentity(
        account_id="target",
        kind="email",
        provider="email",
        subject_norm="owner@example.test",
        created_at=now,
        updated_at=now,
    )
    source = AccountIdentity(
        account_id="source",
        kind="email",
        provider="email",
        subject_norm="owner@example.test",
        verified_at=verified_at,
        disabled_at=disabled_at,
        created_at=now,
        updated_at=now,
    )

    _merge_duplicate_identity_state(target, source, now=now)

    assert target.verified_at == verified_at
    assert target.disabled_at == disabled_at
    assert target.updated_at == now


def test_startup_backfill_uses_completed_marker_instead_of_rescanning_users(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    session.add(_user(5001, now=now))
    session.commit()

    first = run_account_foundation_backfill_once(session, now=now)
    session.commit()
    second = run_account_foundation_backfill_once(session, now=now + timedelta(minutes=1))
    session.commit()

    assert first.users_seen == 1
    assert second.users_seen == 0
    marker = session.query(AppSetting).filter_by(key=ACCOUNT_FOUNDATION_BACKFILL_KEY).one()
    assert '"status":"complete"' in str(marker.value_json)
    assert '"version":1' in str(marker.value_json)

    session.close()
    engine.dispose()


def test_startup_marker_repairs_a_late_legacy_user_without_account(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    first_user = _user(5101, now=now)
    session.add(first_user)
    session.commit()
    run_account_foundation_backfill_once(session, now=now)
    session.commit()

    late_user = _user(5102, now=now + timedelta(minutes=1))
    session.add(late_user)
    session.commit()
    assert late_user.account_id is None

    repair = run_account_foundation_backfill_once(session, now=now + timedelta(minutes=2))
    session.commit()
    session.refresh(late_user)

    assert repair.users_seen == 2
    assert late_user.account_id

    session.close()
    engine.dispose()


def test_startup_backfill_locks_rows_users_then_one_exclusive_global(
    tmp_path: Path,
    monkeypatch,
) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    session.add(_user(5201, now=now))
    session.commit()
    events = _record_projection_lock_events(session, monkeypatch)

    run_account_foundation_backfill_once(session, now=now)

    assert events[0] == ("lock", "pokrov_account_foundation_startup_v1", False)
    assert events[1][0] == "rows"
    assert "ORDER BY users.tg_id ASC" in str(events[1][1])
    assert "FOR UPDATE" in str(events[1][1])
    assert events[2:] == [
        ("lock", "pokrov_account_foundation_user:5201", False),
        ("lock", "pokrov_account_foundation_backfill", False),
    ]

    session.rollback()
    session.close()
    engine.dispose()


def test_postgres_projection_lock_uses_parameterized_transaction_lock() -> None:
    class _Dialect:
        name = "postgresql"

    class _Bind:
        dialect = _Dialect()

    class _Session:
        def __init__(self) -> None:
            self.calls: list[tuple[object, dict[str, str]]] = []

        def get_bind(self):
            return _Bind()

        def execute(self, statement, params):
            self.calls.append((statement, params))

    session = _Session()
    _acquire_postgres_advisory_lock(session, "pokrov_account_foundation_user:5001")
    _acquire_postgres_advisory_lock(
        session,
        "pokrov_account_foundation_backfill",
        shared=True,
    )

    assert len(session.calls) == 2
    exclusive_statement, exclusive_params = session.calls[0]
    shared_statement, shared_params = session.calls[1]
    assert "pg_advisory_xact_lock(" in str(exclusive_statement)
    assert ":lock_key" in str(exclusive_statement)
    assert exclusive_params == {"lock_key": "pokrov_account_foundation_user:5001"}
    assert "pg_advisory_xact_lock_shared(" in str(shared_statement)
    assert shared_params == {"lock_key": "pokrov_account_foundation_backfill"}


def test_full_backfill_locks_rows_ordered_users_then_one_exclusive_global(
    tmp_path: Path,
    monkeypatch,
) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    session.add_all([_user(5302, now=now), _user(5301, now=now)])
    session.commit()
    events = _record_projection_lock_events(session, monkeypatch)

    backfill_account_foundation(session, now=now)

    assert events[0][0] == "rows"
    assert "ORDER BY users.tg_id ASC" in str(events[0][1])
    assert "FOR UPDATE" in str(events[0][1])
    assert events[1:] == [
        ("lock", "pokrov_account_foundation_user:5301", False),
        ("lock", "pokrov_account_foundation_user:5302", False),
        ("lock", "pokrov_account_foundation_backfill", False),
    ]

    session.rollback()
    session.close()
    engine.dispose()


def test_dirty_linked_component_is_row_locked_before_autoflush(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    direct_telegram = _user(5351, now=now)
    app_user = _user(
        9_000_000_000_535,
        now=now,
        app_install_id="install-dirty-component-535",
        linked_telegram_id=5351,
    )
    session.add_all([direct_telegram, app_user])
    session.commit()

    events: list[str] = []

    def _capture_flush(*_args) -> None:
        events.append("flush")

    def _capture_row_lock(orm_execute_state) -> None:
        if getattr(orm_execute_state.statement, "_for_update_arg", None) is not None:
            events.append("rows")

    event.listen(session, "before_flush", _capture_flush)
    event.listen(session, "do_orm_execute", _capture_row_lock)
    app_user.app_device_name = "Dirty before component lock"

    ensure_user_account_foundation(session, app_user, now=now)

    assert events[0] == "rows"
    assert "flush" in events

    session.rollback()
    session.close()
    engine.dispose()


def test_pending_direct_telegram_arrival_joins_reverse_component_after_persisted_locks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    app_user = _user(
        9_000_000_000_536,
        now=now,
        app_install_id="install-pending-reverse-arrival-536",
        linked_telegram_id=5361,
    )
    session.add(app_user)
    session.commit()
    ensure_user_account_foundation(session, app_user, now=now)
    session.commit()
    session.refresh(app_user)
    app_account_id = str(app_user.account_id)

    events = _record_projection_lock_events(session, monkeypatch)

    def _capture_flush(*_args) -> None:
        events.append(("flush",))

    event.listen(session, "before_flush", _capture_flush)
    direct_telegram = _user(5361, now=now + timedelta(minutes=1))
    session.add(direct_telegram)

    report = ensure_user_account_foundation(
        session,
        direct_telegram,
        now=now + timedelta(minutes=1),
    )

    assert report.users_seen == 2
    assert str(direct_telegram.account_id) == app_account_id
    assert str(app_user.account_id) == app_account_id
    first_flush_index = events.index(("flush",))
    assert events[0][0] == "rows"
    assert "ORDER BY users.tg_id ASC" in str(events[0][1])
    assert "FOR UPDATE" in str(events[0][1])
    assert events[1:first_flush_index] == [
        ("lock", "pokrov_account_foundation_user:5361", False),
        ("lock", "pokrov_account_foundation_user:9000000000536", False),
        ("lock", "pokrov_account_foundation_backfill", False),
    ]

    session.rollback()
    session.close()
    engine.dispose()


def test_direct_telegram_arrival_converges_existing_reverse_link_only(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    app_user = _user(
        9_000_000_000_531,
        now=now,
        app_install_id="install-reverse-arrival-531",
        linked_telegram_id=5301,
    )
    unrelated = _user(5399, now=now)
    session.add_all([app_user, unrelated])
    session.commit()

    ensure_user_account_foundation(session, app_user, now=now)
    session.commit()
    session.refresh(app_user)
    app_account_id = str(app_user.account_id)

    direct_telegram = _user(5301, now=now + timedelta(minutes=1))
    session.add(direct_telegram)
    session.commit()
    report = ensure_user_account_foundation(
        session,
        direct_telegram,
        now=now + timedelta(minutes=1),
    )
    session.commit()
    session.refresh(app_user)
    session.refresh(direct_telegram)
    session.refresh(unrelated)

    assert report.users_seen == 2
    assert str(direct_telegram.account_id) == app_account_id
    assert str(app_user.account_id) == app_account_id
    assert unrelated.account_id is None
    assert session.query(AccountMergeReview).count() == 0

    session.close()
    engine.dispose()


def test_runtime_link_sync_projects_only_the_explicit_component(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    direct_telegram = _user(6001, now=now)
    app_user = _user(
        9_000_000_000_601,
        now=now,
        app_install_id="install-runtime-component",
        linked_telegram_id=6001,
    )
    unrelated = _user(7001, now=now)
    session.add_all([direct_telegram, app_user, unrelated])
    session.add(
        WebEmailIdentity(
            email="unrelated@example.test",
            email_norm="unrelated@example.test",
            password_hash="unused-runtime-component-hash",
            linked_tg_id=unrelated.tg_id,
            is_verified=True,
            verified_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    report = ensure_user_account_foundation(session, app_user, now=now)
    session.commit()
    session.refresh(direct_telegram)
    session.refresh(app_user)
    session.refresh(unrelated)

    assert report.users_seen == 2
    assert direct_telegram.account_id == app_user.account_id
    assert unrelated.account_id is None
    assert session.query(AccountMergeReview).count() == 0
    assert session.query(AccountIdentity).filter_by(subject_norm="unrelated@example.test").count() == 0

    session.close()
    engine.dispose()


def test_runtime_sync_handles_existing_transitive_component_in_numeric_order(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    first = _user(
        9_000_000_000_801,
        now=now,
        app_install_id="install-existing-chain-801",
        linked_telegram_id=8002,
    )
    middle = _user(8002, now=now, linked_telegram_id=7003)
    last = _user(7003, now=now)
    session.add_all([first, middle, last])
    session.commit()

    report = ensure_user_account_foundation(session, first, now=now)
    session.commit()
    session.refresh(first)
    session.refresh(middle)
    session.refresh(last)

    assert report.users_seen == 3
    assert first.account_id == middle.account_id == last.account_id

    session.close()
    engine.dispose()


def test_postgres_schema_bootstrap_lock_precedes_create_all(monkeypatch) -> None:
    import db as db_module

    calls: list[str] = []

    class _Dialect:
        name = "postgresql"

    class _Connection:
        def execute(self, statement):
            calls.append(str(statement))

    connection = _Connection()

    class _Begin:
        def __enter__(self):
            return connection

        def __exit__(self, exc_type, exc, traceback):
            return False

    class _Engine:
        dialect = _Dialect()

        def begin(self):
            return _Begin()

    monkeypatch.setattr(db_module, "engine", _Engine())
    monkeypatch.setattr(
        db_module.Base.metadata,
        "create_all",
        lambda bind: calls.append("create_all") if bind is connection else calls.append("wrong_bind"),
    )

    db_module._create_schema()

    assert len(calls) == 2
    assert "pg_advisory_xact_lock" in calls[0]
    assert "pokrov_schema_bootstrap" in calls[0]
    assert calls[1] == "create_all"


def test_postgres_create_all_and_migrations_share_one_bootstrap_lock(monkeypatch) -> None:
    import db as db_module

    schema_calls: list[str] = []

    class _Dialect:
        name = "postgresql"

    class _SchemaConnection:
        def execute(self, statement):
            schema_calls.append(str(statement))

    schema_connection = _SchemaConnection()

    class _SchemaBegin:
        def __enter__(self):
            return schema_connection

        def __exit__(self, exc_type, exc, traceback):
            return False

    class _SchemaEngine:
        dialect = _Dialect()

        def begin(self):
            return _SchemaBegin()

    monkeypatch.setattr(db_module, "engine", _SchemaEngine())
    monkeypatch.setattr(db_module.Base.metadata, "create_all", lambda bind: None)
    db_module._create_schema()

    migration_calls: list[str] = []

    class _StopMigrationProbe(Exception):
        pass

    class _MigrationConnection:
        def execute(self, statement, *_args, **_kwargs):
            migration_calls.append(str(statement))
            if len(migration_calls) > 1:
                raise _StopMigrationProbe
            return None

    migration_connection = _MigrationConnection()

    class _MigrationBegin:
        def __enter__(self):
            return migration_connection

        def __exit__(self, exc_type, exc, traceback):
            return False

    class _MigrationEngine:
        dialect = _Dialect()

        def begin(self):
            return _MigrationBegin()

    try:
        migrations_module._run_postgres_migrations(_MigrationEngine())
    except _StopMigrationProbe:
        pass
    else:
        raise AssertionError("migration probe did not stop after its advisory lock")

    assert "pokrov_schema_bootstrap" in schema_calls[0]
    assert "pokrov_schema_bootstrap" in migration_calls[0]


def test_backfill_never_clears_operator_blocked_account_status(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    user = _user(3001, now=now, plan="paid", expiry_days=30)
    session.add(user)
    session.commit()

    backfill_account_foundation(session)
    session.commit()
    session.refresh(user)
    account = session.query(Account).filter_by(id=str(user.account_id)).one()
    account.status = "blocked"
    session.commit()

    backfill_account_foundation(session)
    session.commit()
    session.refresh(account)

    assert account.status == "blocked"
    assert account.merged_into_account_id is None

    session.close()
    engine.dispose()


def test_conflicting_verified_identity_is_queued_for_review(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    now = datetime(2026, 7, 10, 12, 0, 0)
    user = _user(4001, now=now, plan="paid", expiry_days=30)
    session.add(user)
    session.commit()
    backfill_account_foundation(session)
    session.commit()
    session.refresh(user)

    conflicting_account_id = "11111111-1111-4111-8111-111111111111"
    session.add(
        Account(
            id=conflicting_account_id,
            status="active",
            created_source="test-conflict",
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        AccountIdentity(
            account_id=conflicting_account_id,
            kind="email",
            provider="email",
            subject_norm="conflict@example.test",
            verified_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        WebEmailIdentity(
            email="conflict@example.test",
            email_norm="conflict@example.test",
            password_hash="unused-migration-hash",
            linked_tg_id=user.tg_id,
            is_verified=True,
            verified_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    report = backfill_account_foundation(session)
    session.commit()

    review = session.query(AccountMergeReview).one()
    assert report.reviews_created == 1
    assert review.reason_code == "identity_account_conflict"
    assert review.account_id == user.account_id
    assert review.conflicting_account_id == conflicting_account_id
    identity = session.query(AccountIdentity).filter_by(subject_norm="conflict@example.test").one()
    assert identity.account_id == conflicting_account_id

    second = backfill_account_foundation(session)
    session.commit()
    assert second.reviews_created == 0
    assert session.query(AccountMergeReview).count() == 1

    session.close()
    engine.dispose()


def test_legacy_sqlite_users_table_receives_account_id_column(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-schema.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                  tg_id BIGINT PRIMARY KEY,
                  username VARCHAR(100),
                  uuid VARCHAR(36),
                  email VARCHAR(100),
                  sub_type VARCHAR(50),
                  created_at DATETIME,
                  expiry_at DATETIME,
                  is_active BOOLEAN,
                  stars_paid INTEGER DEFAULT 0,
                  total_gb INTEGER DEFAULT 0,
                  referrer_id BIGINT,
                  referral_count INTEGER DEFAULT 0
                )
                """
            )
        )
    Base.metadata.create_all(engine)

    run_migrations(engine)

    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(users)")).fetchall()
        assert "account_id" in {str(row[1]) for row in columns}

    engine.dispose()


def test_security_foundation_tables_start_empty(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)

    assert session.query(AuthSession).count() == 0
    assert session.query(RecoveryCode).count() == 0
    assert session.query(AntiAbuseEvent).count() == 0
    assert session.query(AntiAbuseCase).count() == 0
    assert session.query(AntiAbuseAction).count() == 0

    session.close()
    engine.dispose()
