from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

from starlette.concurrency import run_in_threadpool


T = TypeVar("T")
_USE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_metrics_lock = threading.Lock()
_metrics = {
    "active": 0,
    "max_active": 0,
    "started": 0,
    "completed": 0,
    "failed": 0,
    "queue_wait_total_ms": 0,
    "queue_wait_max_ms": 0,
    "duration_total_ms": 0,
    "duration_max_ms": 0,
}


def payment_db_runtime_snapshot() -> dict[str, int]:
    with _metrics_lock:
        return {key: int(value) for key, value in _metrics.items()}


def _record_start(*, queue_wait_ms: int) -> None:
    with _metrics_lock:
        _metrics["active"] += 1
        _metrics["max_active"] = max(_metrics["max_active"], _metrics["active"])
        _metrics["started"] += 1
        _metrics["queue_wait_total_ms"] += max(0, int(queue_wait_ms))
        _metrics["queue_wait_max_ms"] = max(
            _metrics["queue_wait_max_ms"], max(0, int(queue_wait_ms))
        )


def _record_finish(*, duration_ms: int, failed: bool) -> None:
    with _metrics_lock:
        _metrics["active"] = max(0, _metrics["active"] - 1)
        _metrics["failed" if failed else "completed"] += 1
        _metrics["duration_total_ms"] += max(0, int(duration_ms))
        _metrics["duration_max_ms"] = max(
            _metrics["duration_max_ms"], max(0, int(duration_ms))
        )


async def run_payment_db_use_case(
    name: str,
    function: Callable[..., T],
    /,
    *args: Any,
    **kwargs: Any,
) -> T:
    use_case = str(name or "").strip().lower()
    if not _USE_CASE_RE.fullmatch(use_case):
        raise ValueError("payment_db_use_case_invalid")
    queued_at = time.perf_counter()

    def invoke() -> T:
        started_at = time.perf_counter()
        _record_start(queue_wait_ms=int((started_at - queued_at) * 1000))
        failed = False
        try:
            return function(*args, **kwargs)
        except BaseException:
            failed = True
            raise
        finally:
            _record_finish(
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                failed=failed,
            )

    return await run_in_threadpool(invoke)


def run_session_transaction(
    session_factory: Callable[[], Any],
    use_case: Callable[[Any], T],
    *,
    commit: bool = True,
) -> T:
    session = session_factory()
    try:
        result = use_case(session)
        if commit:
            session.commit()
        return result
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def reset_payment_db_runtime_for_tests() -> None:
    with _metrics_lock:
        for key in _metrics:
            _metrics[key] = 0
