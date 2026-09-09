from __future__ import annotations

import threading
import time

from sqlalchemy.pool import QueuePool
from sqlalchemy.util.queue import Empty, Queue


class _ObservedPoolQueue(Queue):
    def __init__(self, maxsize=0, use_lifo=False):
        super().__init__(maxsize, use_lifo=use_lifo)
        self._metrics_lock = threading.Lock()
        self._metrics = {
            "attempts": 0,
            "waiting": 0,
            "max_waiting": 0,
            "timeouts": 0,
            "wait_total_ms": 0,
            "wait_max_ms": 0,
        }

    def wait_snapshot(self) -> dict[str, int]:
        with self._metrics_lock:
            return dict(self._metrics)

    def get(self, block=True, timeout=None):
        if not block:
            return super().get(block, timeout)
        started = time.perf_counter()
        timed_out = False
        with self._metrics_lock:
            self._metrics["attempts"] += 1
            self._metrics["waiting"] += 1
            self._metrics["max_waiting"] = max(
                self._metrics["max_waiting"], self._metrics["waiting"]
            )
        try:
            return super().get(block, timeout)
        except Empty:
            timed_out = True
            raise
        finally:
            elapsed = int((time.perf_counter() - started) * 1000)
            with self._metrics_lock:
                self._metrics["waiting"] -= 1
                self._metrics["timeouts"] += int(timed_out)
                self._metrics["wait_total_ms"] += elapsed
                self._metrics["wait_max_ms"] = max(self._metrics["wait_max_ms"], elapsed)


class ObservedQueuePool(QueuePool):
    # SQLAlchemy 2.0.46's queue-class hook keeps creation, pre-ping and SQL
    # outside the timer. The saturation/timeout test covers this internal hook.
    _queue_class = _ObservedPoolQueue

    def wait_snapshot(self) -> dict[str, int]:
        return self._pool.wait_snapshot()
