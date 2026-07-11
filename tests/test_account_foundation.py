from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, event, text
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
    RecoveryCode,
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
        tables["entitlement_grants"].c.keys()
    )
    assert {
        "raw_ip",
        "raw_ip_expires_at",
        "ip_full_hmac",
        "ip_prefix_hmac",
        "hmac_version",
    } <= set(tables["antiabuse_events"].c.keys())


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
    assert session.query(EntitlementGrant).filter_by(account_id=account_id).count() == 2
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
    assert session.query(EntitlementGrant).filter_by(account_id=canonical_account_id).count() == 2

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
