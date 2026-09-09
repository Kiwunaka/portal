"""Real two-connection outbox checks on the existing disposable loopback DB."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from sqlalchemy import event

from test_public_checkout_postgres import pg_checkout  # noqa: F401


def test_stale_recovery_cannot_steal_an_inflight_dispatch(pg_checkout):
    _api, engine, sessions = pg_checkout
    import economy_service
    import models
    import payment_entitlement_outbox as outbox

    now = datetime(2026, 9, 6, 0, 0, 0)
    account_id = str(uuid.uuid4())
    with sessions.begin() as session:
        session.add(models.Account(id=account_id, status="active", created_source="test"))
        session.add(models.User(
            tg_id=6101, account_id=account_id, uuid=str(uuid.uuid4()),
            username="outbox_fixture", email="outbox@example.test",
            sub_type="FREE", is_active=True, tos_accepted=True,
        ))
        session.flush()
        grant = economy_service.record_successful_payment_grant(
            session, account_id=account_id, legacy_tg_id=6101,
            provider="lavatop", order_id="pg-outbox-fixture", plan_code="1_month",
            duration_days=30, paid_at=now,
        ).grant
        grant_id = str(grant.id)
    claim = outbox._claim_one(sessions, now=now)
    assert claim is not None
    later = now + timedelta(minutes=10)
    entered = threading.Event()
    release = threading.Event()
    backend_pids = set()

    def observe(connection, _cursor, statement, _parameters, _context, _many):
        if "payment_entitlement_outbox" in statement:
            backend_pids.add(connection.connection.driver_connection.get_backend_pid())

    def paused_dispatch(session, payload):
        entered.set()
        assert release.wait(timeout=10), "Dispatch barrier was not released"
        outbox.dispatch_to_provisioning_queue(session, payload, now=later)

    event.listen(engine, "before_cursor_execute", observe)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            delivery = pool.submit(
                outbox._dispatch_one, sessions, claim=claim, now=later,
                dispatcher=paused_dispatch,
            )
            try:
                assert entered.wait(timeout=10), "Dispatch did not start"
                recovery = outbox._recover_stale(
                    sessions, now=later, stale_after_seconds=60, max_attempts=5, limit=20,
                )
            finally:
                release.set()
            assert delivery.result(timeout=15) == "delivered"
    finally:
        event.remove(engine, "before_cursor_execute", observe)

    assert len(backend_pids) == 2, "Two PostgreSQL connections must participate"
    assert recovery == {"recovered": 0, "dead_letter": 0}
    with sessions() as session:
        row = session.get(models.PaymentEntitlementOutbox, claim.row_id)
        assert row.status == "delivered"
        assert row.attempts == 1
        assert row.claim_token is None
        job = session.query(models.NodeProvisioningJob).one()
        assert job.entitlement_grant_id == grant_id
        assert session.query(models.EntitlementGrant).filter_by(
            source="provider_payment", external_order_id="pg-outbox-fixture",
        ).count() == 1
