from __future__ import annotations

import asyncio
import json
import sys
import threading
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from payment_db_runtime import (  # noqa: E402
    payment_db_runtime_snapshot,
    reset_payment_db_runtime_for_tests,
    run_payment_db_use_case,
    run_session_transaction,
)


def test_slow_payment_db_use_case_does_not_block_event_loop() -> None:
    reset_payment_db_runtime_for_tests()
    started = threading.Event()
    release = threading.Event()
    main_thread = threading.get_ident()

    def slow_use_case() -> int:
        started.set()
        assert release.wait(timeout=2)
        return threading.get_ident()

    async def run() -> None:
        task = asyncio.create_task(
            run_payment_db_use_case("order_prepare", slow_use_case)
        )
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.001)
        assert started.is_set()
        assert (
            await asyncio.wait_for(
                asyncio.sleep(0, result="event_loop_live"), timeout=0.1
            )
            == "event_loop_live"
        )
        release.set()
        worker_thread = await task
        assert worker_thread != main_thread

    asyncio.run(run())
    snapshot = payment_db_runtime_snapshot()
    assert snapshot["started"] == 1
    assert snapshot["completed"] == 1
    assert snapshot["failed"] == 0
    assert snapshot["active"] == 0


class _FakeSession:
    def __init__(self) -> None:
        self.staged = False
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.thread_ids: list[int] = []

    def commit(self) -> None:
        self.thread_ids.append(threading.get_ident())
        self.committed = True

    def rollback(self) -> None:
        self.thread_ids.append(threading.get_ident())
        self.staged = False
        self.rolled_back = True

    def close(self) -> None:
        self.thread_ids.append(threading.get_ident())
        self.closed = True


def test_session_transaction_rolls_back_and_closes_in_worker_thread() -> None:
    reset_payment_db_runtime_for_tests()
    session = _FakeSession()
    main_thread = threading.get_ident()

    def use_case(current: _FakeSession) -> None:
        current.thread_ids.append(threading.get_ident())
        current.staged = True
        raise RuntimeError("closed-test-error")

    async def run() -> None:
        with pytest.raises(RuntimeError, match="closed-test-error"):
            await run_payment_db_use_case(
                "order_record_checkout",
                run_session_transaction,
                lambda: session,
                use_case,
            )

    asyncio.run(run())
    assert session.staged is False
    assert session.committed is False
    assert session.rolled_back is True
    assert session.closed is True
    assert session.thread_ids
    assert len(set(session.thread_ids)) == 1
    assert session.thread_ids[0] != main_thread
    snapshot = payment_db_runtime_snapshot()
    assert snapshot["started"] == 1
    assert snapshot["failed"] == 1
    assert snapshot["completed"] == 0
    assert snapshot["active"] == 0


def test_payment_db_metrics_are_integer_only_and_fixed_shape() -> None:
    reset_payment_db_runtime_for_tests()
    snapshot = payment_db_runtime_snapshot()

    assert set(snapshot) == {
        "active",
        "max_active",
        "started",
        "completed",
        "failed",
        "queue_wait_total_ms",
        "queue_wait_max_ms",
        "duration_total_ms",
        "duration_max_ms",
    }
    assert all(type(value) is int for value in snapshot.values())
    serialized = json.dumps(snapshot)
    assert "sql" not in serialized.lower()
    assert "parameter" not in serialized.lower()


def test_payment_async_paths_have_no_inline_session_or_orm_across_await() -> None:
    api_source = (PORTAL_ROOT / "api.py").read_text(encoding="utf-8")
    client_source = (PORTAL_ROOT / "api_client_routes.py").read_text(encoding="utf-8")
    payment_route_source = (PORTAL_ROOT / "api_payment_routes.py").read_text(
        encoding="utf-8"
    )
    callback_source = (PORTAL_ROOT / "payment_callback_application.py").read_text(
        encoding="utf-8"
    )
    callback_wrapper = api_source.split("async def _handle_payment_callback", 1)[
        1
    ].split("async def _freekassa_api_request", 1)[0]
    callback = callback_source.split("async def handle_payment_callback", 1)[1]
    paid_sync = api_source.split("async def _sync_user_after_paid_purchase", 1)[
        1
    ].split("def _ticket_status_title", 1)[0]
    order_create = client_source.split("async def _rub_create_order_internal", 1)[
        1
    ].split('@app.get("/api/public/promo-media', 1)[0]
    start99 = payment_route_source.split("async def start99_eligibility", 1)[1].split(
        '@app.post("/api/payments/freekassa/orders/create"', 1
    )[0]

    assert "SessionLocal(" not in callback_wrapper
    assert "SessionLocal(" not in callback
    assert "SessionLocal(" not in paid_sync
    assert "SessionLocal(" not in order_create
    assert "SessionLocal(" not in start99
    assert "await _sync_user_after_paid_bonus(user)" not in paid_sync
    assert "handle_payment_callback(" in callback_wrapper
    assert "run_payment_db_use_case" in callback
    assert "run_payment_db_use_case" in order_create
    assert "run_payment_db_use_case" in start99
