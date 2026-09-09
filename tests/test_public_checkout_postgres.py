"""Opt-in checkout concurrency gate on a named disposable loopback PostgreSQL."""

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import test_api_payments_callbacks as api_fixtures


@pytest.fixture
def pg_checkout(monkeypatch):
    configured = os.environ.get("POKROV_TEST_POSTGRES_URL")
    if not configured:
        pytest.skip("POKROV_TEST_POSTGRES_URL is required for real PostgreSQL proof")
    url = make_url(configured)
    assert url.get_backend_name() == "postgresql"
    assert url.host in {"127.0.0.1", "localhost"}
    assert url.database == "r12_checkout_rehearsal"
    fixture = api_fixtures.ApiPaymentCallbacksTests()
    fixture.setUp()
    admin = create_engine(url, hide_parameters=True)
    schema = "checkout_" + uuid.uuid4().hex
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url, hide_parameters=True,
        connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=15000 -ctimezone=UTC"},
    )
    from models import Base
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(fixture.api, "SessionLocal", sessions)
    try:
        yield fixture.api, engine, sessions
    finally:
        engine.dispose()
        admin.dispose()
        fixture.tearDown()
        fixture.doCleanups()


@pytest.mark.parametrize("identity", ["intent", "quote"])
@pytest.mark.parametrize("provider_result", ["success", "timeout", "late_paid"])
def test_two_http_requests_create_one_postgres_order(pg_checkout, monkeypatch, identity, provider_result):
    api, engine, sessions = pg_checkout
    from models import ExternalOrder
    payload = {
        "provider": "lavatop", "plan_code": "1_month", "currency": "RUB",
        "buyer_email": "concurrency@pokrov.test", "payment_method": "card",
    }
    if identity == "quote":
        preview = TestClient(api.app).post("/api/public/offers/preview", json={
            "plan_code": "1_month", "buyer_email": payload["buyer_email"],
        })
        assert preview.status_code == 200
        assert preview.json()["valid"]
        payload["offer_token"] = preview.json()["offer_token"]
    else:
        payload["intent_id"] = str(uuid.uuid4())

    barrier = threading.Barrier(2)
    recovered = threading.Event()
    backend_pids = set()
    guard = threading.Lock()
    provider_calls = []

    def before_lock(connection, _cursor, statement, _parameters, _context, _many):
        if "SELECT pg_advisory_xact_lock(:key)" not in statement and "SELECT pg_advisory_xact_lock(%(key)s)" not in statement:
            return
        with guard:
            backend_pids.add(connection.connection.driver_connection.get_backend_pid())
        barrier.wait(timeout=10)

    event.listen(engine, "before_cursor_execute", before_lock)

    async def provider(**kwargs):
        provider_calls.append(kwargs["order_id"])
        assert recovered.wait(timeout=10), "Retry did not return while provider I/O was outstanding"
        if provider_result == "timeout":
            raise TimeoutError("synthetic provider timeout after local commit")
        if provider_result == "late_paid":
            # Model the terminal order update from a verified callback transaction.
            # This tests checkout completion, not payment fulfillment authority.
            with sessions.begin() as session:
                session.query(ExternalOrder).filter_by(order_id=kwargs["order_id"]).one().status = "paid"
        return {"payment_url": "https://checkout.invalid/synthetic", "remote": {"id": "synthetic"}}

    monkeypatch.setattr(api, "create_rub_payment", provider)

    def submit():
        try:
            response = TestClient(api.app).post("/api/payments/orders/create-public", json=payload)
        except TimeoutError:
            assert provider_result == "timeout"
            return None
        assert response.status_code == 200
        body = response.json()
        if body["payment_url"] is None:
            recovered.set()
        return body

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit) for _ in range(2)]
            results = [future.result(timeout=25) for future in futures]
    finally:
        event.remove(engine, "before_cursor_execute", before_lock)

    assert len(backend_pids) == 2, "The test must use two PostgreSQL connections"
    assert len(provider_calls) == 1
    assert recovered.is_set()
    with sessions() as session:
        orders = session.query(ExternalOrder).all()
        assert len(orders) == 1
        assert orders[0].order_id == provider_calls[0]
        assert orders[0].status == {"success": "pending", "timeout": "created", "late_paid": "paid"}[provider_result]
    for result in filter(None, results):
        assert result["order_id"] == provider_calls[0]

    retry = TestClient(api.app).post("/api/payments/orders/create-public", json=payload)
    assert retry.status_code == 200
    assert retry.json()["order_id"] == provider_calls[0]
    assert len(provider_calls) == 1
    changed = TestClient(api.app).post("/api/payments/orders/create-public", json={**payload, "payment_method": "sbp"})
    assert changed.status_code == 409
    assert len(provider_calls) == 1


@pytest.mark.parametrize("same_reservation", [True, False])
def test_postgres_commercial_reservation_serializes_order_and_quota(pg_checkout, monkeypatch, same_reservation):
    import importlib
    from datetime import datetime, timezone
    import test_commercial_order_service

    # Reuse the existing synthetic campaign/lineage fixture against this test's
    # PostgreSQL models; ApiPaymentCallbacksTests owns module isolation.
    commercial = importlib.reload(test_commercial_order_service)
    monkeypatch.setattr(commercial, "NOW", datetime.now(timezone.utc))
    original_preview = commercial.offer_service.preview_commercial_offer

    def checked_preview(*args, **kwargs):
        result = original_preview(*args, **kwargs)
        assert result["valid"], {k: result.get(k) for k in ("reason", "reason_code", "error")}
        return result

    monkeypatch.setattr(commercial.offer_service, "preview_commercial_offer", checked_preview)
    _, engine, sessions = pg_checkout
    with sessions() as session:
        first = commercial._seed(session)
        first_preview = commercial._preview(session, first)
        payloads = [(first_preview["offer_token"], first["tg_id"])]
        if same_reservation:
            payloads *= 2
        else:
            second = commercial._seed(session, tg_id=1002, suffix="e")
            payloads.append((commercial._preview(session, second)["offer_token"], second["tg_id"]))
            first["offer"].paid_cap = 1
            session.commit()

    barrier = threading.Barrier(2)
    backend_pids = set()
    guard = threading.Lock()

    def before_first_row_lock(connection, _cursor, statement, _parameters, _context, _many):
        if "FOR UPDATE" not in statement:
            return
        pid = connection.connection.driver_connection.get_backend_pid()
        with guard:
            if pid in backend_pids:
                return
            backend_pids.add(pid)
        barrier.wait(timeout=10)

    def bind(index):
        token, tg_id = payloads[index]
        with sessions() as session:
            try:
                binding = commercial._bind(session, token, tg_id=tg_id, candidate=f"pg_race_{index}")
                if not binding["order_preexisting"]:
                    commercial._persist_order(session, binding, tg_id=tg_id)
                session.commit()
                return binding
            except commercial.order_service.CommercialOrderBindingError as exc:
                session.rollback()
                assert not same_reservation
                assert str(exc) == "commercial_quota_reached"
                return None

    event.listen(engine, "before_cursor_execute", before_first_row_lock)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(bind, index) for index in range(2)]
            results = [future.result(timeout=25) for future in futures]
    finally:
        event.remove(engine, "before_cursor_execute", before_first_row_lock)

    assert len(backend_pids) == 2
    with sessions() as session:
        orders = session.query(commercial.ExternalOrder).all()
        assert len(orders) == 1
        assert session.query(commercial.CommercialReservation).filter_by(status="bound").count() == 1
        assert {result["order_id"] for result in results if result} == {orders[0].order_id}
    assert sum(result is not None for result in results) == (2 if same_reservation else 1)
