from __future__ import annotations

import importlib
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

models = importlib.import_module("models")
economy = importlib.import_module("economy_service")
outbox = importlib.import_module("payment_entitlement_outbox")
migrations = importlib.import_module("migrations")
NOW = datetime(2026, 8, 21, 16, 0, 0)


@pytest.fixture()
def database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'payment-outbox.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _seed_account(factory, *, tg_id: int = 6101) -> tuple[str, datetime]:
    account_id = str(uuid.uuid4())
    original_expiry = NOW + timedelta(days=3)
    with factory() as session:
        session.add(
            models.Account(
                id=account_id,
                status="active",
                created_source="test",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            models.User(
                tg_id=tg_id,
                account_id=account_id,
                username=f"outbox_{tg_id}",
                uuid=str(uuid.uuid4()),
                email=f"user_{tg_id}",
                sub_type="FREE",
                current_plan_code="free_monthly",
                expiry_at=original_expiry,
                is_active=True,
                tos_accepted=True,
                created_at=NOW,
            )
        )
        session.commit()
    return account_id, original_expiry


def _grant(
    factory, *, account_id: str, tg_id: int = 6101, order_id: str = "order-outbox-1"
):
    with factory() as session:
        result = economy.record_successful_payment_grant(
            session,
            account_id=account_id,
            legacy_tg_id=tg_id,
            provider="lavatop",
            order_id=order_id,
            plan_code="1_month",
            duration_days=30,
            paid_at=NOW,
        )
        session.commit()
        return str(result.grant.id)


def test_grant_and_outbox_share_one_transaction_and_rollback_together(database) -> None:
    _engine, factory = database
    account_id, original_expiry = _seed_account(factory)

    with factory() as session:
        economy.record_successful_payment_grant(
            session,
            account_id=account_id,
            legacy_tg_id=6101,
            provider="lavatop",
            order_id="rollback-order",
            plan_code="1_month",
            duration_days=30,
            paid_at=NOW,
        )
        assert session.query(models.PaymentEntitlementOutbox).count() == 1
        session.rollback()

    with factory() as session:
        assert session.query(models.PaymentEntitlementOutbox).count() == 0
        assert session.query(models.EntitlementGrant).count() == 0
        user = session.query(models.User).filter_by(tg_id=6101).one()
        assert user.expiry_at == original_expiry
        assert user.sub_type == "FREE"


def test_callback_replay_converges_to_one_grant_and_one_outbox_event(database) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    grant_id = _grant(factory, account_id=account_id)

    replay_grant_id = _grant(factory, account_id=account_id)
    assert replay_grant_id == grant_id
    with factory() as session:
        assert (
            session.query(models.EntitlementGrant)
            .filter_by(source="provider_payment")
            .count()
            == 1
        )
        row = session.query(models.PaymentEntitlementOutbox).one()
        payload = json.loads(row.payload_json)
        assert row.aggregate_id == grant_id
        assert row.status == "pending"
        assert payload["grant_id"] == grant_id
        assert payload["order_id"] == "order-outbox-1"
        assert set(payload) == outbox._PAYLOAD_KEYS


def test_worker_dispatch_is_idempotent_and_enqueues_one_payment_sync(database) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    grant_id = _grant(factory, account_id=account_id)

    first = outbox.run_payment_entitlement_outbox_once(factory, now=NOW)
    second = outbox.run_payment_entitlement_outbox_once(
        factory, now=NOW + timedelta(minutes=1)
    )

    assert first == {
        "backfilled": 0,
        "backfill_rejected": 0,
        "recovered": 0,
        "claimed": 1,
        "delivered": 1,
        "retryable": 0,
        "dead_letter": 0,
        "claim_lost": 0,
    }
    assert second["claimed"] == 0
    with factory() as session:
        row = session.query(models.PaymentEntitlementOutbox).one()
        job = session.query(models.NodeProvisioningJob).one()
        assert row.status == "delivered"
        assert row.attempts == 1
        assert job.job_type == "payment_entitlement_sync"
        assert job.entitlement_grant_id == grant_id
        assert job.account_id == account_id


def test_worker_backfills_preexisting_active_provider_grant(database) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    grant_id = str(uuid.uuid4())
    with factory() as session:
        session.add(
            models.EntitlementGrant(
                id=grant_id,
                account_id=account_id,
                legacy_tg_id=6101,
                idempotency_key="lavatop:preexisting-outbox-order",
                source="provider_payment",
                status="active",
                grant_kind="paid_access",
                plan_code="1_month",
                starts_at=NOW,
                expires_at=NOW + timedelta(days=30),
                activated_at=NOW,
                duration_days=30,
                provider="lavatop",
                external_order_id="preexisting-outbox-order",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()

    counters = outbox.run_payment_entitlement_outbox_once(factory, now=NOW)
    assert counters["backfilled"] == 1
    assert counters["delivered"] == 1
    with factory() as session:
        assert session.query(models.PaymentEntitlementOutbox).count() == 1
        job = session.query(models.NodeProvisioningJob).one()
        assert job.entitlement_grant_id == grant_id


def test_worker_rolls_back_partial_dispatch_then_retries_to_dead_letter(
    database,
) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    _grant(factory, account_id=account_id)

    def failing_dispatch(session, payload):
        session.add(
            models.NodeProvisioningJob(
                account_id=account_id,
                entitlement_grant_id=str(payload["grant_id"]),
                job_type="payment_entitlement_sync",
                status="queued",
                idempotency_key="must-rollback",
                next_run_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.flush()
        raise RuntimeError("RAW-DISPATCH-SECRET")

    first = outbox.run_payment_entitlement_outbox_once(
        factory,
        now=NOW,
        max_attempts=2,
        dispatcher=failing_dispatch,
    )
    second = outbox.run_payment_entitlement_outbox_once(
        factory,
        now=NOW + timedelta(seconds=3),
        max_attempts=2,
        dispatcher=failing_dispatch,
    )

    assert first["retryable"] == 1
    assert second["dead_letter"] == 1
    with factory() as session:
        row = session.query(models.PaymentEntitlementOutbox).one()
        assert row.status == "dead_letter"
        assert row.attempts == 2
        assert row.last_error_code == "outbox_dispatch_failed"
        assert row.terminal_reason == "outbox_dispatch_failed"
        assert "RAW-DISPATCH-SECRET" not in str(row.last_error_code)
        assert session.query(models.NodeProvisioningJob).count() == 0


def test_stale_claim_is_recovered_and_dispatched_once(database) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    _grant(factory, account_id=account_id)
    with factory() as session:
        row = session.query(models.PaymentEntitlementOutbox).one()
        row.status = "processing"
        row.attempts = 1
        row.claim_token = "stale-token"
        row.claimed_at = NOW - timedelta(minutes=10)
        session.commit()

    counters = outbox.run_payment_entitlement_outbox_once(
        factory,
        now=NOW,
        stale_after_seconds=60,
    )
    assert counters["recovered"] == 1
    assert counters["delivered"] == 1
    with factory() as session:
        row = session.query(models.PaymentEntitlementOutbox).one()
        assert row.status == "delivered"
        assert row.attempts == 2
        assert session.query(models.NodeProvisioningJob).count() == 1


def test_malformed_payload_dead_letters_without_access_or_provisioning_mutation(
    database,
) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    _grant(factory, account_id=account_id)
    with factory() as session:
        user = session.query(models.User).filter_by(tg_id=6101).one()
        expiry_after_grant = user.expiry_at
        row = session.query(models.PaymentEntitlementOutbox).one()
        row.payload_json = '{"schema_version":1,"raw":"SECRET"}'
        session.commit()

    counters = outbox.run_payment_entitlement_outbox_once(factory, now=NOW)
    assert counters["dead_letter"] == 1
    with factory() as session:
        user = session.query(models.User).filter_by(tg_id=6101).one()
        row = session.query(models.PaymentEntitlementOutbox).one()
        assert user.expiry_at == expiry_after_grant
        assert row.status == "dead_letter"
        assert row.terminal_reason == "outbox_payload_invalid"
        assert session.query(models.NodeProvisioningJob).count() == 0


def test_health_projection_is_integer_only(database) -> None:
    _engine, factory = database
    account_id, _ = _seed_account(factory)
    _grant(factory, account_id=account_id)
    with factory() as session:
        health = outbox.payment_entitlement_outbox_health(
            session, now=NOW + timedelta(seconds=9)
        )
    assert health == {
        "pending": 1,
        "processing": 0,
        "delivered": 0,
        "dead_letter": 0,
        "oldest_open_age_seconds": 9,
    }
    assert all(type(value) is int for value in health.values())


def test_outbox_migration_is_rerunnable_and_indexed(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'migration.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    migrations.run_migrations(engine)

    inspector = inspect(engine)
    assert "payment_entitlement_outbox" in inspector.get_table_names()
    index_names = {
        row["name"] for row in inspector.get_indexes("payment_entitlement_outbox")
    }
    assert {
        "ix_payment_entitlement_outbox_status_next_id",
        "uq_payment_entitlement_outbox_idempotency",
    } <= index_names
    engine.dispose()
