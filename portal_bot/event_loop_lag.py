from __future__ import annotations

import asyncio
import contextlib
import logging
import math


logger = logging.getLogger(__name__)


class EventLoopLagMonitor:
    """One lifespan-owned timer; retain scalar observations, never requests."""

    def __init__(self, *, interval_seconds: float = 1.0) -> None:
        if not math.isfinite(interval_seconds) or interval_seconds <= 0:
            raise ValueError("event_loop_lag_interval_invalid")
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._status = "not_started"
        self._samples = 0
        self._last_ms: int | None = None
        self._max_ms: int | None = None
        self._total_ms = 0

    def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="api-event-loop-lag")
        self._status = "warming_up"

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._status != "failed":
            self._status = "stopped"

    def snapshot(self) -> dict[str, int | str | None]:
        return {
            "status": self._status,
            "interval_ms": int(self._interval * 1000),
            "samples": self._samples,
            "last_lag_ms": self._last_ms,
            "max_lag_ms": self._max_ms,
            "lag_total_ms": self._total_ms,
        }

    async def _run(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            while True:
                due = loop.time() + self._interval
                await asyncio.sleep(self._interval)
                lag_ms = max(0, int((loop.time() - due) * 1000))
                self._samples += 1
                self._last_ms = lag_ms
                self._max_ms = max(self._max_ms or 0, lag_ms)
                self._total_ms += lag_ms
                self._status = "collecting"
        except Exception:
            self._status = "failed"
            logger.warning("event_loop_lag_monitor_failed")
