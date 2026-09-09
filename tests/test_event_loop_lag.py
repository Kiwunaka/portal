from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))
from event_loop_lag import EventLoopLagMonitor


def test_blocked_loop_is_observed_and_close_stops_collection() -> None:
    async def scenario() -> None:
        monitor = EventLoopLagMonitor(interval_seconds=0.005)
        monitor.start()
        first = monitor.snapshot()
        assert first["status"] == "warming_up"
        assert first["samples"] == 0
        assert first["last_lag_ms"] is first["max_lag_ms"] is None
        try:
            async with asyncio.timeout(2):
                while monitor.snapshot()["samples"] == 0:
                    await asyncio.sleep(0.001)
            before = monitor.snapshot()
            # A deliberate synchronous stall in this test loop must be visible.
            time.sleep(0.06)
            await asyncio.sleep(0.01)
            observed = monitor.snapshot()
            assert observed["status"] == "collecting"
            assert observed["samples"] > before["samples"]
            assert observed["lag_total_ms"] - before["lag_total_ms"] >= 40
        finally:
            await monitor.close()
        stopped = monitor.snapshot()
        assert stopped["status"] == "stopped"
        await asyncio.sleep(0.02)
        assert monitor.snapshot() == stopped

    asyncio.run(scenario())
